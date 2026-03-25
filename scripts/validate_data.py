import json
import os
import re
import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description='Validate catalog data and generate quality report.')
parser.add_argument('--input', type=str, default="public/data/catalog.json", help='Path to catalog JSON')
parser.add_argument('--output', type=str, default="docs/data_quality_report.md", help='Path to output report')
parser.add_argument('--write-notes', action='store_true', help='Write quality notes to Google Sheet cells')
parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json",
                    help='Path to Google Sheets credentials (only used with --write-notes)')
parser.add_argument('--excel', type=str, default="docs/data_catalog.xlsx",
                    help='Path to Excel file (for row mapping with --write-notes)')
args = parser.parse_args()

# Known country names (from generate_insights_data.py ISO mapping)
KNOWN_COUNTRIES = {
    'Kenya', 'India', 'South Africa', 'Ghana', 'Rwanda', 'Uganda', 'Indonesia',
    'Nigeria', 'Tanzania', 'Ecuador', 'DRC', 'Congo', 'Benin', 'Colombia',
    "Cote d'Ivoire", 'Ivory Coast', 'Angola', 'Mozambique', 'Zambia', 'Niger',
    'Togo', 'Cameroon', 'Madagascar', 'Pakistan', 'Malawi', 'Ethiopia',
    'Senegal', 'Mali', 'Burkina Faso', 'Bangladesh', 'Nepal', 'Sri Lanka',
    'Myanmar', 'Thailand', 'Vietnam', 'Cambodia', 'Laos', 'Philippines',
    'Malaysia', 'Peru', 'Bolivia', 'Brazil', 'Argentina', 'Chile', 'Mexico',
    'Guatemala', 'Honduras', 'Nicaragua', 'Costa Rica', 'Panama',
    'Democratic Republic of Congo',
}

# Column names in the Google Sheet / Excel
COL_LICENSE = 'License'
COL_ORGS = 'Organizations Involved'
COL_DESCRIPTION = 'Description - What can be done with this? What is this about?'
COL_DATA_CHARS = 'Data - Key Characteristics'
COL_HOW_TO_USE = 'Deep Dive - How can you concretely work with this and build on this?'


def validate_catalog(catalog_path):
    """Run all validation checks and return structured issues."""
    with open(catalog_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    projects = data.get('projects', [])
    issues = {
        'low_score': [],
        'license': [],
        'org_person_names': [],
        'country': [],
        'short_description': [],
        'missing_links': [],
    }

    for p in projects:
        pid = p.get('id', '?')
        title = p.get('title', pid)
        score = p.get('quality_score', 0)

        # Low score
        if score < 50:
            missing = []
            if not p.get('description', '').strip():
                missing.append('description')
            if not p.get('data_characteristics', '').strip():
                missing.append('data_characteristics')
            if not p.get('how_to_use', '').strip():
                missing.append('how_to_use')
            if not p.get('license', '').strip():
                missing.append('license')
            if not p.get('sdgs'):
                missing.append('SDGs')
            if not p.get('data_types'):
                missing.append('data_types')
            if not p.get('dataset_links') and not p.get('usecase_links') and not p.get('has_access_note'):
                missing.append('links')
            issues['low_score'].append({
                'title': title, 'id': pid, 'score': score, 'missing': missing
            })

        # License: flag non-empty values that look like raw URLs or unusual strings
        lic = p.get('license', '')
        if lic and (lic.startswith('http') or lic.startswith('\n')):
            issues['license'].append({'title': title, 'id': pid, 'value': lic})

        # Organization field: flag entries with email addresses (likely person not org)
        orgs = p.get('organizations', '')
        if orgs and re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', orgs, re.I):
            issues['org_person_names'].append({'title': title, 'id': pid, 'value': orgs})

        # Country issues: unknown country names
        for country in p.get('countries', []):
            if country not in KNOWN_COUNTRIES:
                issues['country'].append({'title': title, 'id': pid, 'value': country})

        # Short description
        desc = p.get('description', '')
        if desc.strip() and len(desc.strip()) < 50:
            issues['short_description'].append({
                'title': title, 'id': pid, 'length': len(desc.strip())
            })

    return projects, issues


def print_console_summary(projects, issues):
    """Print a concise summary to console during build."""
    scores = [p.get('quality_score', 0) for p in projects]
    avg = sum(scores) / len(scores) if scores else 0

    print(f"\n{'='*60}")
    print(f"DATA QUALITY REPORT")
    print(f"{'='*60}")
    print(f"  {len(projects)} projects evaluated")
    print(f"  Average quality score: {avg:.0f}/100")
    print(f"  Score range: {min(scores)}-{max(scores)}")

    if issues['low_score']:
        print(f"\n  {len(issues['low_score'])} projects below score 50 (need attention):")
        for item in sorted(issues['low_score'], key=lambda x: x['score']):
            missing_str = ', '.join(item['missing']) if item['missing'] else 'various fields sparse'
            print(f"    [{item['score']:3d}] {item['title'][:60]} -- missing: {missing_str}")

    if issues['license']:
        print(f"\n  {len(issues['license'])} license values still look like raw URLs:")
        for item in issues['license']:
            print(f"    {item['title'][:50]}: {item['value'][:60]}")

    if issues['org_person_names']:
        print(f"\n  {len(issues['org_person_names'])} org fields contain email addresses (likely person not org):")
        for item in issues['org_person_names']:
            snippet = item['value'][:80].replace('\n', ' | ')
            print(f"    {item['title'][:50]}: {snippet}...")

    if issues['country']:
        unique_countries = set(item['value'] for item in issues['country'])
        print(f"\n  {len(unique_countries)} unrecognized country name(s): {', '.join(sorted(unique_countries))}")

    if issues['short_description']:
        print(f"\n  {len(issues['short_description'])} projects with very short descriptions (<50 chars)")

    print(f"{'='*60}\n")


def write_report(projects, issues, output_path):
    """Write a persistent markdown quality report."""
    scores = [p.get('quality_score', 0) for p in projects]
    avg = sum(scores) / len(scores) if scores else 0
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    lines = [
        f"# Data Quality Report",
        f"Generated: {now}",
        "",
        "## Summary",
        f"- **{len(projects)}** projects evaluated",
        f"- **Average score: {avg:.0f}/100** (range {min(scores)}-{max(scores)})",
        f"- **{len(issues['low_score'])}** projects below 50/100 (need attention)",
        f"- **{len(issues['license'])}** license values need review",
        f"- **{len(issues['org_person_names'])}** organization fields contain email addresses",
        f"- **{len(set(i['value'] for i in issues['country']))}** unrecognized country names",
        "",
    ]

    if issues['low_score']:
        lines.append("## Projects Needing Attention (score < 50)")
        lines.append("")
        lines.append("| Project | Score | Missing Fields |")
        lines.append("|---|---|---|")
        for item in sorted(issues['low_score'], key=lambda x: x['score']):
            missing = ', '.join(item['missing']) if item['missing'] else '-'
            lines.append(f"| {item['title'][:60]} | {item['score']} | {missing} |")
        lines.append("")

    if issues['license']:
        lines.append("## License Values Needing Review")
        lines.append("")
        lines.append("| Project | Current Value |")
        lines.append("|---|---|")
        for item in issues['license']:
            val = item['value'].replace('|', '\\|').replace('\n', ' ')[:80]
            lines.append(f"| {item['title'][:60]} | `{val}` |")
        lines.append("")

    if issues['org_person_names']:
        lines.append("## Organization Fields with Email Addresses")
        lines.append("")
        lines.append("These entries may contain person names instead of organization names.")
        lines.append("")
        lines.append("| Project | Value (excerpt) |")
        lines.append("|---|---|")
        for item in issues['org_person_names']:
            val = item['value'].replace('|', '\\|').replace('\n', ' | ')[:100]
            lines.append(f"| {item['title'][:60]} | {val} |")
        lines.append("")

    if issues['country']:
        unique = sorted(set(item['value'] for item in issues['country']))
        lines.append("## Unrecognized Country Names")
        lines.append("")
        lines.append("These country names are not in the known list and will not appear on the map.")
        lines.append("")
        for c in unique:
            affected = [item['title'] for item in issues['country'] if item['value'] == c]
            lines.append(f"- **{c}** (used by: {', '.join(t[:40] for t in affected)})")
        lines.append("")

    if issues['short_description']:
        lines.append("## Very Short Descriptions (<50 characters)")
        lines.append("")
        lines.append("| Project | Length |")
        lines.append("|---|---|")
        for item in issues['short_description']:
            lines.append(f"| {item['title'][:60]} | {item['length']} chars |")
        lines.append("")

    lines.append("## Score Distribution")
    lines.append("")
    brackets = [(90, 100), (70, 89), (50, 69), (30, 49), (0, 29)]
    for lo, hi in brackets:
        count = sum(1 for s in scores if lo <= s <= hi)
        bar = '#' * count
        lines.append(f"- **{lo}-{hi}**: {count} projects {bar}")
    lines.append("")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Quality report written to {output_path}")


def build_row_notes(excel_path):
    """Read Excel and build per-row quality notes keyed by Excel row index.

    Returns dict: {row_index: {column_name: note_text}}
    Row indices are 0-based (matching df.iterrows), and map to sheet row = idx + 3
    (1-indexed + header row + explanation row).
    """
    import pandas as pd
    from utils import resolve_project_id

    df = pd.read_excel(excel_path)
    row_notes = {}

    for idx, row in df.iterrows():
        notes = {}

        # License check
        lic = row.get(COL_LICENSE, '')
        if isinstance(lic, str) and lic.strip():
            lower = lic.strip().lower()
            if lower.startswith('http'):
                notes[COL_LICENSE] = (
                    "Consider using a short license name instead of a URL.\n"
                    "Standard formats: CC-BY 4.0, CC0 1.0, MIT, Apache 2.0"
                )

        # Organization check: email in org field
        orgs = row.get(COL_ORGS, '')
        if isinstance(orgs, str) and re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', orgs, re.I):
            notes[COL_ORGS] = (
                "This field should list organization names, not contact persons.\n"
                "Consider moving personal contact info to the Point of Contact column."
            )

        # Description check
        desc = row.get(COL_DESCRIPTION, '')
        if not isinstance(desc, str) or not desc.strip() or (isinstance(desc, float)):
            notes[COL_DESCRIPTION] = (
                "A description helps users understand what this project offers.\n"
                "Aim for 2-3 sentences explaining the purpose and potential uses."
            )
        elif len(str(desc).strip()) < 50:
            notes[COL_DESCRIPTION] = (
                "This description is very short. Consider expanding it to 2-3 sentences\n"
                "to help users understand what this project offers."
            )

        # Data characteristics check
        data_chars = row.get(COL_DATA_CHARS, '')
        if not isinstance(data_chars, str) or not data_chars.strip() or (isinstance(data_chars, float)):
            notes[COL_DATA_CHARS] = (
                "Adding data characteristics helps users evaluate if this dataset\n"
                "fits their needs (e.g., format, size, coverage, annotation details)."
            )

        # How-to-use check
        how_to = row.get(COL_HOW_TO_USE, '')
        if not isinstance(how_to, str) or not how_to.strip() or (isinstance(how_to, float)):
            notes[COL_HOW_TO_USE] = (
                "A how-to-use section helps users get started with this resource.\n"
                "Describe concrete steps for working with the data or model."
            )

        if notes:
            row_notes[idx] = notes

    return row_notes


def write_notes_to_sheet(row_notes, credentials_path):
    """Write quality feedback as cell notes to the Google Sheet using batch API."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(credentials)

    spreadsheet_id = "18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c"
    gid = 756053104

    spreadsheet = client.open_by_key(spreadsheet_id)
    sheet = spreadsheet.get_worksheet_by_id(gid)
    headers = sheet.row_values(1)

    # Map column names to column indices (1-based for gspread)
    col_indices = {}
    for i, h in enumerate(headers):
        col_indices[h] = i + 1  # gspread uses 1-based indexing

    # Also try fuzzy matching for column names that may differ slightly
    from thefuzz import fuzz
    target_cols = [COL_LICENSE, COL_ORGS, COL_DESCRIPTION, COL_DATA_CHARS, COL_HOW_TO_USE]
    for target in target_cols:
        if target not in col_indices:
            best_score = 0
            best_header = None
            for h in headers:
                score = fuzz.token_sort_ratio(target, h)
                if score > best_score:
                    best_score = score
                    best_header = h
            if best_score >= 70 and best_header:
                col_indices[target] = col_indices[best_header]
                print(f"  Fuzzy-matched column '{target}' -> '{best_header}' (score: {best_score})")

    # First, batch-clear any previous auto-check notes so we start clean.
    # Then batch-write all new notes in one API call.
    # This avoids per-cell get_note + update_note (which hits rate limits).

    note_prefix = "[Auto-check] "

    # Read all existing notes in one call (returns list-of-lists)
    existing_notes_grid = []
    try:
        existing_notes_grid = sheet.get_notes(default_empty_value='')
    except Exception:
        pass  # If get_notes fails, proceed without checking existing

    def get_existing_note(sheet_row, col_idx):
        """Look up an existing note from the grid (1-based row/col)."""
        r = sheet_row - 1  # convert to 0-based
        c = col_idx - 1
        if r < len(existing_notes_grid) and c < len(existing_notes_grid[r]):
            return existing_notes_grid[r][c]
        return ''

    # Build batch notes dict: {cell_A1_notation: note_text}
    batch_notes = {}
    for row_idx, notes in row_notes.items():
        sheet_row = row_idx + 3  # +1 for 1-indexing, +1 for header, +1 for explanation row
        for col_name, note_text in notes.items():
            col_idx = col_indices.get(col_name)
            if col_idx is None:
                continue
            cell = gspread.utils.rowcol_to_a1(sheet_row, col_idx)
            full_note = note_prefix + note_text

            # If cell has an existing note that is NOT auto-check, preserve it
            existing = get_existing_note(sheet_row, col_idx)
            if existing and note_prefix not in existing:
                full_note = existing + "\n\n" + full_note

            batch_notes[cell] = full_note

    if not batch_notes:
        print("  No notes to write.")
        return

    # Write all notes in one batch API call
    try:
        sheet.update_notes(batch_notes)
        print(f"  Wrote {len(batch_notes)} quality notes to Google Sheet (batch)")
    except Exception as e:
        print(f"  Error writing batch notes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found. Run generate_catalog_data.py first.")
        exit(1)

    projects, issues = validate_catalog(args.input)
    print_console_summary(projects, issues)
    write_report(projects, issues, args.output)

    if args.write_notes:
        if not os.path.exists(args.credentials):
            print(f"Error: Credentials file '{args.credentials}' not found. Cannot write notes to sheet.")
            exit(1)
        if not os.path.exists(args.excel):
            print(f"Error: Excel file '{args.excel}' not found. Cannot map rows for notes.")
            exit(1)

        print("Writing quality notes to Google Sheet...")
        try:
            row_notes = build_row_notes(args.excel)
            if row_notes:
                write_notes_to_sheet(row_notes, args.credentials)
            else:
                print("  No quality issues found to write back.")
        except Exception as e:
            print(f"  Warning: Could not write notes to Google Sheet: {e}")
            import traceback
            traceback.print_exc()

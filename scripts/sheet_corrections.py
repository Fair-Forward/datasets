"""Correct the master Google Sheet where the sources themselves say otherwise.

The weekly health check reads each project's GitHub repositories, Hugging Face datasets, models and
spaces, and Zenodo records (public/data/health.json). Where those sources contradict the Sheet, or
fill a gap in it, this script corrects the Sheet, so the catalogue shows what the sources declare:

- License: the licence the project's data declares at its source. A dataset's licence (a Zenodo
  record counts as data unless it is filed as software) wins over a model's, and a model's over
  code's. A licence that only code declares fills an empty cell but never replaces one, because a
  project's code and data licences can legitimately differ. Several different licences in the
  deciding group, a custom licence, or a linked asset that could not be read leave the cell alone.
- Links: a repository renamed on GitHub or Hugging Face gets its new address, and a link to an
  older version of a Zenodo record becomes the record's all-versions DOI, which always opens the
  latest version. A new address is used only once it answers.

Each changed cell gets a "[Source check]" paragraph in its note with the previous value; the
Sheet's version history keeps every earlier state. A cell whose note contains [Keep] is never
changed, and neither are protected cells or formulas. A run that would change more than
MAX_CHANGES cells writes nothing and fails, since a jump like that points at a fault, not at the
sources. Without --apply it only reports.

Usage:
    python scripts/sheet_corrections.py                  # report what would change
    python scripts/sheet_corrections.py --apply          # write it to the Sheet
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

import requests

from generate_catalog_data import KNOWN_LICENSE_VALUES, normalize_license
from sheet_notes import is_pinned, merge_note
from text_parsing import license_label, spdx_for
from utils import DEFAULT_CREDENTIALS_PATH

HEALTH_PATH = os.path.join('public', 'data', 'health.json')
SCHEMA_VERSION = 2
NOTE_PREFIX = '[Source check]'
MAX_CHANGES = 30
PIN_HINT = 'To keep your own value in this cell, write Keep in square brackets in this note.'
USER_AGENT = 'FairForwardCatalog-SheetCorrections/1.0 (+https://fair-forward.github.io/datasets/)'

# The exact Sheet headers (case and spacing aside) of the cells this script reads and writes. A
# writer does not guess: a renamed header stops the run before anything is written.
COLUMNS = {
    'id': ('Project ID',),
    'dataset': ('Access to the dataset [link]', 'Dataset Link', 'Dataset URL'),
    'model': ('Access to AI Model /Software / AI System [link]',
              'Access to AI Model, Software, AI Application [link]', 'Model/Use-Case Links'),
    'license': ('License', 'Usage Rights'),
}
COLUMN_LABELS = {'dataset': 'Dataset link', 'model': 'Model link', 'license': 'License'}
LINK_COLUMNS = ('dataset', 'model')

# Whose licence speaks for the project's data, first to last.
TIERS = ('dataset', 'model', 'code')
PLATFORM_NAMES = {'github': 'GitHub', 'huggingface': 'Hugging Face', 'zenodo': 'Zenodo'}
NOUNS = {'datasets': 'dataset', 'models': 'model', 'spaces': 'space'}

# The catalogue's spelling of each SPDX id it knows, e.g. 'CC-BY-4.0' -> 'CC-BY 4.0'.
SPDX_TO_CATALOGUE = {spdx_for(value): value for value in sorted(KNOWN_LICENSE_VALUES) if spdx_for(value)}

# Characters that continue a link, so a match followed by one is part of a longer link.
_LINK_CONTINUES = re.compile(r'[A-Za-z0-9\-_~/%#?=&+@]')
_DOI_URL = re.compile(r'https?://(?:dx\.)?doi\.org/(10\.\S+)$', re.I)


def recognised_license(text):
    """The catalogue's spelling of a License cell: '' when empty, None when the cell holds text that
    is not one licence the catalogue knows, which is left for a person to read."""
    text = (text or '').strip()
    if not text:
        return ''
    value = normalize_license(text)
    if value in KNOWN_LICENSE_VALUES:
        return value
    return SPDX_TO_CATALOGUE.get(spdx_for(license_label(text)))


def asset_tier(asset):
    platform = asset.get('platform')
    if platform == 'github':
        return 'code'
    if platform == 'huggingface':
        return {'datasets': 'dataset', 'models': 'model', 'spaces': 'code'}.get(asset.get('kind'))
    if platform == 'zenodo':
        # Uploaders often file a dataset as a publication (ui_39), so only software counts as code.
        return 'code' if asset.get('resource_type') == 'software' else 'dataset'
    return None


def asset_noun(asset):
    if asset.get('platform') == 'github':
        return 'repository'
    if asset.get('platform') == 'zenodo':
        return 'record'
    return NOUNS.get(asset.get('kind'), 'asset')


def decide_license(assets):
    """What the sources declare for the project's data: {value, spdx, tier, declaring, group} when
    one licence settles it, otherwise {reason}, which is None when there is nothing to report."""
    if not assets:
        return {'reason': None}
    if any(a.get('status') != 'measured' or asset_tier(a) is None for a in assets):
        return {'reason': 'not every linked asset could be read'}
    for tier in TIERS:
        group = [a for a in assets if asset_tier(a) == tier]
        declared = [(a, item) for a in group for item in a.get('license') or [] if item.get('status') != 'none']
        if not declared:
            continue
        if any(item.get('status') != 'detected' or not item.get('spdx') for _, item in declared):
            return {'tier': tier, 'reason': f'a custom or unrecognised licence at the source ({tier})'}
        ids = sorted({item['spdx'] for _, item in declared})
        if len(ids) > 1:
            return {'tier': tier, 'reason': f'several licences at the source: {", ".join(ids)}'}
        value = SPDX_TO_CATALOGUE.get(ids[0])
        if value is None:
            return {'tier': tier, 'reason': f'{ids[0]} has no spelling in the catalogue yet'}
        declaring = list({id(a): a for a, _ in declared}.values())
        return {'value': value, 'spdx': ids[0], 'tier': tier, 'declaring': declaring, 'group': group}
    return {'reason': None}


def _plural(noun, n):
    if n == 1:
        return noun
    return noun[:-1] + 'ies' if noun.endswith('y') else noun + 's'


def describe_source(decision):
    """'the dataset on Hugging Face declares CC-BY-4.0', '2 datasets on Hugging Face declare ...'."""
    declaring, spdx = decision['declaring'], decision['spdx']
    groups = Counter((asset_noun(a), PLATFORM_NAMES.get(a.get('platform'), a.get('platform')))
                     for a in declaring)
    if len(declaring) == 1:
        (noun, platform), = groups
        text = f'the {noun} on {platform} declares {spdx}'
    else:
        parts = [f'{n} {_plural(noun, n)} on {platform}' for (noun, platform), n in sorted(groups.items())]
        text = f'{" and ".join(parts)} declare {spdx}'
    rest = len(decision['group']) - len(declaring)
    if rest:
        text += f', and {rest} more declare{"s" if rest == 1 else ""} none'
    return text


def renamed_url(url, old_id, new_id):
    """url with a renamed owner/name replaced, or None when the link does not carry it as a whole
    path (a DOI, for one, keeps working without a change)."""
    match = re.search(r'(?<=/)' + re.escape(old_id) + r'(?=$|[/?#])', url, re.I)
    if not match:
        return None
    return url[:match.start()] + new_id + url[match.end():]


def replace_link(text, old, new):
    """text with every whole occurrence of the link old replaced by new, and how many there were. A
    longer link that starts with old (old/tree/main, old-extra) is a different link and stays."""
    out, i, count = [], 0, 0
    while True:
        j = text.find(old, i)
        if j < 0:
            break
        end = j + len(old)
        nxt, after = text[end:end + 1], text[end + 1:end + 2]
        whole = not _LINK_CONTINUES.match(nxt) and not (nxt == '.' and after.isalnum())
        out.append(text[i:j])
        out.append(new if whole else old)
        count += whole
        i = end
    out.append(text[i:])
    return ''.join(out), count


def link_targets(oss):
    """[(old url, new url, why)] for measured assets the Sheet links under an outdated address."""
    targets = []
    for asset in oss.get('assets') or []:
        url = asset.get('url')
        if asset.get('status') != 'measured' or not url:
            continue
        platform = asset.get('platform')
        if platform in ('github', 'huggingface') and asset.get('renamed_from') and asset.get('id'):
            new = renamed_url(url, asset['renamed_from'], asset['id'])
            if new and new != url:
                targets.append((url, new, f'Replaced {url} with {new}; the {asset_noun(asset)} was renamed '
                                          f'on {PLATFORM_NAMES[platform]}.'))
        elif platform == 'zenodo' and asset.get('linked_is_latest') is False and asset.get('concept_id'):
            new = f"https://doi.org/10.5281/zenodo.{asset['concept_id']}"
            if new.lower() != url.lower():
                targets.append((url, new, f'Replaced {url}, an older version of the Zenodo record, with {new}, '
                                          f'which always opens the latest version.'))
    return targets


def verify_link(url, session=None, timeout=30):
    """True when a new address answers. A DOI is checked at the DOI registry, so a slow repository
    behind it cannot hold up a correction."""
    session = session or requests
    doi = _DOI_URL.match(url)
    try:
        if doi:
            response = session.get(f'https://doi.org/api/handles/{doi.group(1)}', timeout=timeout)
            return response.status_code == 200 and (response.json() or {}).get('responseCode') == 1
        response = session.get(url, timeout=timeout, allow_redirects=True, headers={'User-Agent': USER_AGENT})
        return response.status_code < 400
    except (requests.RequestException, ValueError):
        return False


def a1(row, col):
    """A1 notation of a zero-based cell."""
    letters, col = '', col + 1
    while col:
        col, rest = divmod(col - 1, 26)
        letters = chr(65 + rest) + letters
    return f'{letters}{row + 1}'


def _normal(header):
    return ' '.join(str(header).split()).lower()


def find_columns(header):
    """Zero-based column of each COLUMNS entry; ValueError naming any that is missing."""
    index = {}
    for i, name in enumerate(header):
        index.setdefault(_normal(name), i)
    found, missing = {}, []
    for key, names in COLUMNS.items():
        col = next((index[_normal(n)] for n in names if _normal(n) in index), None)
        if col is None:
            missing.append(names[0])
        else:
            found[key] = col
    if missing:
        raise ValueError(f'no column headed {" or ".join(repr(m) for m in missing)} in the Sheet')
    return found


def _cell(grid, r, c):
    if r < len(grid) and c < len(grid[r]):
        return grid[r][c] or ''
    return ''


def _protected(r, c, ranges):
    def inside(value, start, end):
        return (start is None or value >= start) and (end is None or value < end)
    return any(inside(r, r0, r1) and inside(c, c0, c1) for r0, r1, c0, c1 in ranges)


def _natural(pid):
    digits = re.search(r'\d+', pid)
    return (int(digits.group()) if digits else -1, pid)


class _Sheet:
    def __init__(self, grid, notes, formulas, protected):
        self.grid, self.notes, self.formulas, self.protected = grid, notes, formulas, protected

    def value(self, r, c):
        return _cell(self.grid, r, c)

    def note(self, r, c):
        return _cell(self.notes, r, c)

    def blocked(self, r, c):
        """Why this cell must not be written, or None."""
        if _protected(r, c, self.protected):
            return 'protected in the Sheet'
        if _cell(self.formulas, r, c).startswith('='):
            return 'the cell holds a formula'
        if is_pinned(self.note(r, c)):
            return 'pinned with [Keep]'
        return None


def _change(pid, r, c, column, old, new, kind, sentence, display, sheet, today):
    paragraph = f'{NOTE_PREFIX} {today}: {sentence} {PIN_HINT}'
    return {'pid': pid, 'row': r, 'col': c, 'cell': a1(r, c), 'column': column, 'old': old, 'new': new,
            'kind': kind, 'display': display, 'note': merge_note(sheet.note(r, c), NOTE_PREFIX, paragraph)}


def _license_plan(pid, oss, r, cols, sheet, today):
    if oss.get('status') not in ('measured', 'carried_forward'):
        return None, None  # a source could not be read this week
    decision = decide_license(oss.get('assets') or [])
    c = cols['license']
    if 'value' not in decision:
        reason = decision.get('reason')
        return None, ({'pid': pid, 'what': 'License', 'reason': reason} if reason else None)
    old = sheet.value(r, c).strip()
    current, value, source = recognised_license(old), decision['value'], describe_source(decision)
    if current == value:
        return None, None
    if old and decision['tier'] == 'code':
        return None, {'pid': pid, 'what': 'License',
                      'reason': f'only code declares {decision["spdx"]}, and code and data licences can differ, '
                                f'so the Sheet keeps "{old}"'}
    if old and current is None:
        return None, {'pid': pid, 'what': 'License',
                      'reason': f'the cell holds "{old}", not one licence the catalogue knows; {source}'}
    blocked = sheet.blocked(r, c)
    if blocked:
        return None, {'pid': pid, 'what': 'License', 'reason': blocked}
    kind = 'overwrite' if old else 'fill'
    sentence = f'Was "{old}"; {source}.' if old else f'Was empty; {source}.'
    return _change(pid, r, c, 'license', old, value, kind, sentence, [(old, value, source)], sheet, today), None


def _link_plan(pid, oss, r, cols, sheet, verify, today):
    targets = link_targets(oss)
    if not targets:
        return [], []
    texts = {key: sheet.value(r, cols[key]) for key in LINK_COLUMNS}
    changes, skipped = [], []
    edits = {key: [] for key in LINK_COLUMNS}
    for old, new, sentence in targets:
        holders = [key for key in LINK_COLUMNS if replace_link(texts[key], old, new)[1]]
        if not holders:
            if not any(replace_link(texts[key], new, new)[1] for key in LINK_COLUMNS):
                skipped.append({'pid': pid, 'what': old, 'reason': 'not found in the Sheet as linked'})
            continue  # already corrected
        if not verify(new):
            skipped.append({'pid': pid, 'what': old, 'reason': f'the new address {new} did not answer'})
            continue
        for key in holders:
            edits[key].append((old, new, sentence))
    for key in LINK_COLUMNS:
        if not edits[key]:
            continue
        c = cols[key]
        blocked = sheet.blocked(r, c)
        if blocked:
            skipped.append({'pid': pid, 'what': COLUMN_LABELS[key], 'reason': blocked})
            continue
        text = texts[key]
        for old, new, _ in edits[key]:
            text, _ = replace_link(text, old, new)
        sentence = ' '.join(s for _, _, s in edits[key])
        display = [(old, new, 'older Zenodo version' if 'older version' in s else 'renamed')
                   for old, new, s in edits[key]]
        changes.append(_change(pid, r, c, key, texts[key], text, 'link', sentence, display, sheet, today))
    return changes, skipped


def plan(health, grid, notes, formulas, protected, verify, today):
    """The cells to change, and what was left alone with the reason. Raises ValueError when the
    Sheet lacks a column this script relies on."""
    if not grid:
        raise ValueError('the Sheet is empty')
    cols = find_columns(grid[0])
    sheet = _Sheet(grid, notes, formulas, protected)
    rows = {}
    for r in range(1, len(grid)):
        pid = sheet.value(r, cols['id']).strip()
        # A row with nothing but its Project ID is a placeholder, not a project.
        if pid and any(str(v).strip() for c, v in enumerate(grid[r]) if c != cols['id']):
            rows.setdefault(pid, []).append(r)
    changes, skipped = [], []
    for pid in sorted(health.get('entries') or {}, key=_natural):
        oss = ((health['entries'][pid] or {}).get('oss')) or {}
        if oss.get('status') not in ('measured', 'partial', 'carried_forward'):
            continue
        found = rows.get(pid) or []
        if len(found) != 1:
            reason = 'not in the Sheet' if not found else f'the Project ID is in several rows ({len(found)})'
            skipped.append({'pid': pid, 'what': 'row', 'reason': reason})
            continue
        r = found[0]
        change, skip = _license_plan(pid, oss, r, cols, sheet, today)
        changes.extend([change] if change else [])
        skipped.extend([skip] if skip else [])
        link_changes, link_skips = _link_plan(pid, oss, r, cols, sheet, verify, today)
        changes.extend(link_changes)
        skipped.extend(link_skips)
    return changes, skipped


def apply_changes(worksheet, changes):
    """Write the values as typed (no formula or number parsing), then the notes."""
    worksheet.batch_update([{'range': c['cell'], 'values': [[c['new']]]} for c in changes], raw=True)
    worksheet.update_notes({c['cell']: c['note'] for c in changes})


def _md(text):
    return str(text).replace('|', '\\|').replace('\n', ' ') if text else '(empty)'


def render_summary(health, changes, skipped, applied, capped, max_changes):
    count = f'{len(changes)} cell{"" if len(changes) == 1 else "s"}'
    if capped:
        status = (f'{count} would change, more than the limit of {max_changes}, so nothing was written. '
                  f'Check the health data before raising the limit.')
    elif applied:
        status = f'{count} changed in the master Sheet.'
    else:
        status = f'{count} would change (report only, nothing written).'
    lines = ['## Sheet corrections from the sources', '',
             f'Health data of {health.get("generated_at", "?")}. {status}', '']
    if changes:
        lines += ['| Project | Cell | Was | Now | Why |', '|---|---|---|---|---|']
        for c in changes:
            for old, new, why in c['display']:
                lines.append(f'| {c["pid"]} | {COLUMN_LABELS[c["column"]]} ({c["cell"]}) | {_md(old)} | {_md(new)} '
                             f'| {_md(why)} |')
        lines.append('')
    if skipped:
        lines.append(f'Left unchanged ({len(skipped)}):')
        lines += [f'- {s["pid"]}, {s["what"]}: {s["reason"]}' for s in skipped]
        lines.append('')
    return '\n'.join(lines)


def _open_sheet(credentials):
    """The worksheet, its values, formulas and notes, and its protected ranges (zero-based,
    end-exclusive row and column bounds; None is unbounded)."""
    from utils import get_gsheet_client
    _client, spreadsheet, worksheet = get_gsheet_client(credentials)
    grid = worksheet.get_all_values()
    formulas = worksheet.get_all_values(value_render_option='FORMULA')
    notes = worksheet.get_notes(default_empty_value='')
    protected = []
    for item in spreadsheet.list_protected_ranges(worksheet.id):
        rng = item.get('range') or {}
        protected.append((rng.get('startRowIndex'), rng.get('endRowIndex'),
                          rng.get('startColumnIndex'), rng.get('endColumnIndex')))
    return worksheet, grid, notes, formulas, protected


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Correct the master Sheet from what the sources declare.')
    parser.add_argument('--health', default=HEALTH_PATH)
    parser.add_argument('--credentials', default=DEFAULT_CREDENTIALS_PATH)
    parser.add_argument('--apply', action='store_true', help='write the corrections (default: report only)')
    parser.add_argument('--max-changes', type=int, default=MAX_CHANGES)
    parser.add_argument('--summary', help='also write the report as Markdown to this file')
    return parser.parse_args(argv)


def main(argv=None, open_sheet=None, verify=None, today=None):
    args = parse_args(argv)
    with open(args.health, encoding='utf-8') as f:
        health = json.load(f)
    if health.get('schema_version') != SCHEMA_VERSION:
        print(f'{args.health} is not schema version {SCHEMA_VERSION}; nothing written.')
        return 2
    today = today or datetime.now(timezone.utc).date().isoformat()
    worksheet, grid, notes, formulas, protected = (open_sheet or _open_sheet)(args.credentials)
    try:
        changes, skipped = plan(health, grid, notes, formulas, protected, verify or verify_link, today)
    except ValueError as err:
        print(f'Stopped before writing anything: {err}.')
        return 2
    capped = len(changes) > args.max_changes
    applied = bool(args.apply and changes and not capped)
    if applied:
        apply_changes(worksheet, changes)
    summary = render_summary(health, changes, skipped, applied, capped, args.max_changes)
    print(summary)
    if args.summary:
        with open(args.summary, 'w', encoding='utf-8') as f:
            f.write(summary)
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a', encoding='utf-8') as f:
            f.write(f'written={len(changes) if applied else 0}\n')
    return 3 if capped else 0


if __name__ == '__main__':
    sys.exit(main())

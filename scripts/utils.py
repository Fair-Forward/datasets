import os
import re
import pandas as pd

PROJECTS_DIR = os.path.join("public", "projects")

# Google Sheet configuration (single source of truth)
GOOGLE_SHEET_ID = "18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c"
GOOGLE_SHEET_GID = 756053104
DEFAULT_CREDENTIALS_PATH = "data_sources/google_sheets_api/service_account_JN.json"

# Country name to ISO Alpha-2 code mapping (canonical list for all scripts)
COUNTRY_ISO_MAP = {
    'Kenya': 'KE', 'India': 'IN', 'South Africa': 'ZA', 'Ghana': 'GH',
    'Rwanda': 'RW', 'Uganda': 'UG', 'Indonesia': 'ID', 'Nigeria': 'NG',
    'Tanzania': 'TZ', 'Ecuador': 'EC', 'DRC': 'CD', 'Congo': 'CG',
    'Democratic Republic of the Congo': 'CD', 'Democratic Republic of Congo': 'CD',
    'Benin': 'BJ', 'Colombia': 'CO',
    "Cote d'Ivoire": 'CI', 'Ivory Coast': 'CI', 'Angola': 'AO',
    'Mozambique': 'MZ', 'Zambia': 'ZM', 'Niger': 'NE', 'Togo': 'TG',
    'Cameroon': 'CM', 'Madagascar': 'MG', 'Pakistan': 'PK', 'Malawi': 'MW',
    'Ethiopia': 'ET', 'Senegal': 'SN', 'Mali': 'ML', 'Burkina Faso': 'BF',
    'Bangladesh': 'BD', 'Nepal': 'NP', 'Sri Lanka': 'LK', 'Myanmar': 'MM',
    'Thailand': 'TH', 'Vietnam': 'VN', 'Cambodia': 'KH', 'Laos': 'LA',
    'Philippines': 'PH', 'Malaysia': 'MY', 'Peru': 'PE', 'Bolivia': 'BO',
    'Brazil': 'BR', 'Argentina': 'AR', 'Chile': 'CL', 'Mexico': 'MX',
    'Guatemala': 'GT', 'Honduras': 'HN', 'Nicaragua': 'NI', 'Costa Rica': 'CR',
    'Panama': 'PA',
}
KNOWN_COUNTRIES = set(COUNTRY_ISO_MAP.keys())


def get_gsheet_client(credentials_path=None):
    """Authenticate with Google Sheets and return (client, spreadsheet, sheet)."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    creds_path = credentials_path or DEFAULT_CREDENTIALS_PATH
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    sheet = spreadsheet.get_worksheet_by_id(GOOGLE_SHEET_GID)
    return client, spreadsheet, sheet

# Access-note rows: only these openings in Dataset / Use-Case link cells (case-insensitive).
ACCESS_NOTE_PREFIX_PENDING = "dataset/use-case has not been published yet."
ACCESS_NOTE_PREFIX_UNAVAILABLE = "there is no dataset/use-case available."


def normalize_sheet_link_cell(value):
    """Strip and normalize Dataset Link / Model Use-Case cell values."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if not isinstance(value, str):
        return str(value).strip()
    return value.strip()


_DANGEROUS_SCHEMES = ('javascript:', 'data:', 'vbscript:', 'file:')


def _is_safe_url(url):
    """Reject URLs with dangerous schemes (XSS prevention)."""
    lower = url.lower().strip()
    return not any(lower.startswith(s) for s in _DANGEROUS_SCHEMES)


def _clean_url(url):
    """Strip trailing punctuation that is sentence-ending, not part of the URL."""
    return url.rstrip('.;,')


def extract_http_links(text):
    """
    Extract http(s) links only (for Dataset Link / Model/Use-Case columns).
    Returns list of dicts: {'name': str, 'url': str}.
    """
    if not text or (isinstance(text, float) and pd.isna(text)) or not isinstance(text, str):
        return []

    urls = []
    markdown_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    for name, url in re.findall(markdown_pattern, text):
        url = _clean_url(url.strip())
        if url.startswith("http") and _is_safe_url(url):
            urls.append({"name": name.strip(), "url": url})

    url_pattern = r"https?://[^\s,;)\]>]+"
    for url in re.findall(url_pattern, text):
        url = _clean_url(url.strip())
        if url not in [u["url"] for u in urls]:
            urls.append({"name": "Link", "url": url})

    return urls


def extract_links_allow_site_paths(text):
    """
    Extract http(s) links and markdown targets that are site-relative (start with /).
    Used for additional resources and hosted PDFs under public/projects/...
    """
    if not text or (isinstance(text, float) and pd.isna(text)) or not isinstance(text, str):
        return []

    urls = []
    markdown_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    for name, url in re.findall(markdown_pattern, text):
        url = _clean_url(url.strip())
        if (url.startswith("http") or url.startswith("/")) and _is_safe_url(url):
            urls.append({"name": name.strip(), "url": url})

    url_pattern = r"https?://[^\s,;)\]>]+"
    for url in re.findall(url_pattern, text):
        url = _clean_url(url.strip())
        if url not in [u["url"] for u in urls]:
            urls.append({"name": "Link", "url": url})

    return urls


def link_columns_match_access_prefixes(dataset_text, usecase_text):
    """True if either link cell starts with the pending or unavailable prefix."""
    d = normalize_sheet_link_cell(dataset_text).lower()
    u = normalize_sheet_link_cell(usecase_text).lower()
    p = ACCESS_NOTE_PREFIX_PENDING
    q = ACCESS_NOTE_PREFIX_UNAVAILABLE
    return (bool(d) and (d.startswith(p) or d.startswith(q))) or (
        bool(u) and (u.startswith(p) or u.startswith(q))
    )


def classify_access_note_prefix_kind(dataset_text, usecase_text):
    """
    'pending' if either cell starts with pending prefix (wins over unavailable).
    'unavailable' if either starts with unavailable prefix and neither pending.
    None if neither prefix matches.
    """
    d = normalize_sheet_link_cell(dataset_text).lower()
    u = normalize_sheet_link_cell(usecase_text).lower()
    p = ACCESS_NOTE_PREFIX_PENDING
    q = ACCESS_NOTE_PREFIX_UNAVAILABLE
    if d.startswith(p) or u.startswith(p):
        return "pending"
    if d.startswith(q) or u.startswith(q):
        return "unavailable"
    return None


def merge_access_note_link_columns(dataset_text, usecase_text):
    """Join non-empty link-column text (dataset first, then use-case)."""
    parts = []
    d = normalize_sheet_link_cell(dataset_text)
    u = normalize_sheet_link_cell(usecase_text)
    if d:
        parts.append(d)
    if u:
        parts.append(u)
    return "\n\n".join(parts)


def documents_dir_has_files(project_id):
    """True if public/projects/<id>/documents/ exists and contains at least one non-hidden file."""
    if not project_id:
        return False
    doc_dir = os.path.join(PROJECTS_DIR, project_id, "documents")
    if not os.path.isdir(doc_dir):
        return False
    try:
        for _root, _dirs, files in os.walk(doc_dir):
            for f in files:
                if f and not f.startswith("."):
                    return True
    except OSError:
        pass
    return False


def row_included_for_catalog_or_insights(row, row_idx=None):
    """
    Match catalog inclusion: http link(s), or strict access prefixes, or documents/
    with files (after resolve).
    """
    dataset_link_text = row.get("Dataset Link", "")
    usecase_link_text = row.get("Model/Use-Case Links", "")

    normalized_project_id, _src, error_msg = resolve_project_id(
        row, row_idx=row_idx
    )

    if extract_http_links(dataset_link_text) or extract_http_links(usecase_link_text):
        return True
    if link_columns_match_access_prefixes(dataset_link_text, usecase_link_text):
        return True
    if not error_msg and normalized_project_id and documents_dir_has_files(
        normalized_project_id
    ):
        return True
    return False


def normalize_for_directory(text, max_words=6, max_length=50):
    """
    Normalize text for use as a directory name.
    Truncates long titles to keep directory names manageable.
    
    Args:
        text: Text to normalize
        max_words: Maximum number of words to use (default: 6)
        max_length: Maximum length of normalized string (default: 50)
    """
    if not text or (isinstance(text, float) and pd.isna(text)) or not isinstance(text, str):
        return ""
    
    # Truncate to first N words if text is very long
    words = text.split()
    if len(words) > max_words:
        text = ' '.join(words[:max_words])
    
    # Convert to lowercase, replace spaces with underscores, remove special characters
    normalized = re.sub(r'[^a-z0-9_]', '', text.lower().replace(' ', '_'))
    
    # Truncate to max_length if still too long
    if len(normalized) > max_length:
        normalized = normalized[:max_length]
    
    return normalized

def resolve_project_id(row, projects_dir=PROJECTS_DIR, row_idx=None):
    """
    Resolve project ID with smart fallback logic:
    1. Try Project ID from column (if exists and directory exists)
    2. Try Dataset Speaking Titles
    3. Try Use Case Speaking Title
    4. Try OnSite Name
    5. Try Project ID as final fallback
    
    Returns: (normalized_id, source, error_message)
    """
    project_id = row.get('Project ID', '')
    dataset_speaking_title = row.get('Dataset Speaking Titles', '')
    usecase_speaking_title = row.get('Use Case Speaking Title', '')
    onsite_name = row.get('OnSite Name', '')
    
    # Check if projects directory exists
    if not os.path.exists(projects_dir):
        os.makedirs(projects_dir, exist_ok=True)
    
    existing_dirs = set(os.listdir(projects_dir)) if os.path.exists(projects_dir) else set()
    
    # Priority 1: Project ID (if exists and directory exists)
    if project_id and not pd.isna(project_id):
        normalized_id = normalize_for_directory(str(project_id))
        if normalized_id and normalized_id in existing_dirs:
            return (normalized_id, "Project ID (existing directory)", None)
    
    # Priority 2: Dataset Speaking Titles
    if dataset_speaking_title and not pd.isna(dataset_speaking_title):
        normalized_id = normalize_for_directory(str(dataset_speaking_title))
        if normalized_id:
            if normalized_id in existing_dirs:
                # Directory exists - use it (title-based names are more reliable)
                # Warn if Project ID doesn't match (potential mismatch)
                if project_id and not pd.isna(project_id):
                    existing_normalized = normalize_for_directory(str(project_id))
                    if existing_normalized != normalized_id:
                        print(f"WARNING Row {row_idx}: Directory '{normalized_id}' exists but Project ID '{project_id}' would create '{existing_normalized}'. Using existing directory.")
                return (normalized_id, "Dataset Speaking Titles (existing)", None)
            # New directory - check for potential collision with Project ID
            if project_id and not pd.isna(project_id):
                existing_normalized = normalize_for_directory(str(project_id))
                if existing_normalized and existing_normalized in existing_dirs and existing_normalized != normalized_id:
                    error_msg = f"Row {row_idx}: Collision detected! Title generates '{normalized_id}' but Project ID '{project_id}' points to existing directory '{existing_normalized}'. Please resolve manually."
                    return (None, None, error_msg)
            return (normalized_id, "Dataset Speaking Titles", None)
    
    # Priority 3: Use Case Speaking Title
    if usecase_speaking_title and not pd.isna(usecase_speaking_title):
        normalized_id = normalize_for_directory(str(usecase_speaking_title))
        if normalized_id:
            if normalized_id in existing_dirs:
                # Directory exists - use it
                if project_id and not pd.isna(project_id):
                    existing_normalized = normalize_for_directory(str(project_id))
                    if existing_normalized != normalized_id:
                        print(f"WARNING Row {row_idx}: Directory '{normalized_id}' exists but Project ID '{project_id}' would create '{existing_normalized}'. Using existing directory.")
                return (normalized_id, "Use Case Speaking Title (existing)", None)
            # New directory - check for potential collision
            if project_id and not pd.isna(project_id):
                existing_normalized = normalize_for_directory(str(project_id))
                if existing_normalized and existing_normalized in existing_dirs and existing_normalized != normalized_id:
                    error_msg = f"Row {row_idx}: Collision detected! Title generates '{normalized_id}' but Project ID '{project_id}' points to existing directory '{existing_normalized}'. Please resolve manually."
                    return (None, None, error_msg)
            return (normalized_id, "Use Case Speaking Title", None)
    
    # Priority 4: OnSite Name
    if onsite_name and not pd.isna(onsite_name):
        normalized_id = normalize_for_directory(str(onsite_name))
        if normalized_id:
            if normalized_id in existing_dirs:
                # Directory exists - use it
                if project_id and not pd.isna(project_id):
                    existing_normalized = normalize_for_directory(str(project_id))
                    if existing_normalized != normalized_id:
                        print(f"WARNING Row {row_idx}: Directory '{normalized_id}' exists but Project ID '{project_id}' would create '{existing_normalized}'. Using existing directory.")
                return (normalized_id, "OnSite Name (existing)", None)
            # New directory - check for potential collision
            if project_id and not pd.isna(project_id):
                existing_normalized = normalize_for_directory(str(project_id))
                if existing_normalized and existing_normalized in existing_dirs and existing_normalized != normalized_id:
                    error_msg = f"Row {row_idx}: Collision detected! Title generates '{normalized_id}' but Project ID '{project_id}' points to existing directory '{existing_normalized}'. Please resolve manually."
                    return (None, None, error_msg)
            return (normalized_id, "OnSite Name", None)
    
    # Priority 5: Project ID as final fallback (even if directory doesn't exist)
    if project_id and not pd.isna(project_id):
        normalized_id = normalize_for_directory(str(project_id))
        if normalized_id:
            return (normalized_id, "Project ID (fallback)", None)
    
    # No valid ID found
    error_msg = f"Row {row_idx}: No valid title or Project ID found. Please provide at least one of: Dataset Speaking Titles, Use Case Speaking Title, OnSite Name, or Project ID."
    return (None, None, error_msg)

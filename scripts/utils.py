import re
import pandas as pd

def normalize_for_directory(text):
    if not text or (isinstance(text, float) and pd.isna(text)) or not isinstance(text, str):
        return ""
    # Convert to lowercase, replace spaces with underscores, remove special characters
    normalized = re.sub(r'[^a-z0-9_]', '', text.lower().replace(' ', '_'))
    return normalized

def is_valid_http_url(value):
    """Check if value is a valid http(s) URL. More permissive - just checks for http/https scheme and basic domain."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    text = str(value).strip()
    if not text:
        return False
    # Simple check: starts with http:// or https:// and has at least one dot after scheme
    if text.startswith(('http://', 'https://')):
        scheme_removed = text[text.find('://') + 3:]
        if '.' in scheme_removed and len(scheme_removed.split('/')[0]) > 0:
            return True
    return False

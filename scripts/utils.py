import re
import pandas as pd
import os

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

def resolve_project_id(row, projects_dir="docs/public/projects", row_idx=None):
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

import pandas as pd
import json
import os
import re
import shutil
import argparse
from utils import (
    normalize_for_directory,
    resolve_project_id,
    PROJECTS_DIR,
    normalize_sheet_link_cell,
    extract_http_links,
    extract_links_allow_site_paths,
    classify_access_note_prefix_kind,
    merge_access_note_link_columns,
    documents_dir_has_files,
)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate catalog JSON from Excel file.')
parser.add_argument('--input', type=str, default="docs/data_catalog.xlsx", help='Path to the input Excel file')
parser.add_argument('--output', type=str, default="public/data/catalog.json", help='Path to the output JSON file')
args = parser.parse_args()


# License normalization: map inconsistent values to canonical short names
LICENSE_NORMALIZATION = {
    'https://creativecommons.org/licenses/by/4.0/': 'CC-BY 4.0',
    'cc-by': 'CC-BY 4.0',
    'cc-by 4.0': 'CC-BY 4.0',
    'cc-by-sa': 'CC-BY-SA 4.0',
    'cc-0': 'CC0 1.0',
    'cc0': 'CC0 1.0',
    'cc-o': 'CC0 1.0',
    'apache 2.0': 'Apache 2.0',
    'apache license 2.0': 'Apache 2.0',
    'mit license': 'MIT',
    'mit': 'MIT',
    'https://www.gnu.org/licenses/agpl-3.0.html': 'AGPL 3.0',
    'https://opendatacommons.org/licenses/dbcl/1-0/': 'ODbL 1.0',
    'permissive': 'Permissive',
    'by-nc-sa-fs': 'BY-NC-SA-FS',
}

KNOWN_LICENSE_VALUES = set(LICENSE_NORMALIZATION.values())


def normalize_license(raw_license):
    """Normalize license strings to canonical short names."""
    if not raw_license or not isinstance(raw_license, str):
        return ''
    cleaned = raw_license.strip()
    if not cleaned or cleaned == 'nan':
        return ''
    # Strip leading whitespace/newlines (some entries have "\n\nhttps://...")
    cleaned = cleaned.strip()
    lookup = cleaned.lower().strip()
    return LICENSE_NORMALIZATION.get(lookup, cleaned)


def clean_str(value):
    """Clean a string value: strip whitespace, replace literal 'nan' with empty."""
    if not isinstance(value, str):
        return ''
    s = value.strip()
    if s == 'nan':
        return ''
    return s


def clean_country_list(country_text):
    """Split country text into clean list, handling slash-separated region qualifiers."""
    if not country_text or not isinstance(country_text, str):
        return []
    parts = re.split(r',|\s+and\s+|;', country_text)
    countries = []
    for part in parts:
        country = part.strip()
        if not country:
            continue
        # Split "Benin/West Africa" -> take the country name (first part)
        if '/' in country:
            country = country.split('/')[0].strip()
        if country:
            countries.append(country)
    return countries


def _content_length_score(text, thresholds):
    """Graduated score based on content length.

    thresholds: list of (min_chars, points) tuples, cumulative.
    Returns sum of points for all thresholds where len(text) >= min_chars.
    """
    if not text or not isinstance(text, str):
        return 0
    length = len(text.strip())
    if length == 0:
        return 0
    return sum(pts for min_chars, pts in thresholds if length >= min_chars)


def compute_quality_score(project):
    """Compute a 0-100 quality score based on field completeness and depth."""
    score = 0

    # title: 5 points
    if project.get('title') and project['title'].strip():
        score += 5

    # description: 15 points (graduated by length)
    score += _content_length_score(
        project.get('description', ''), [(1, 5), (100, 5), (300, 5)])

    # links: 10 points (at least one dataset/usecase link, or has access note)
    if project.get('dataset_links') or project.get('usecase_links'):
        score += 10
    elif project.get('has_access_note'):
        score += 10

    # data_characteristics: 15 points (graduated by length)
    score += _content_length_score(
        project.get('data_characteristics', ''), [(1, 3), (100, 5), (300, 7)])

    # model_characteristics: 10 points (graduated by length)
    score += _content_length_score(
        project.get('model_characteristics', ''), [(1, 2), (100, 3), (300, 5)])

    # how_to_use: 15 points (graduated by length)
    score += _content_length_score(
        project.get('how_to_use', ''), [(1, 3), (100, 5), (300, 7)])

    # license: 8 points
    if project.get('license') and project['license'].strip():
        score += 8

    # sdgs: 5 points
    if project.get('sdgs'):
        score += 5

    # countries: 5 points
    if project.get('countries'):
        score += 5

    # data_types: 4 points
    if project.get('data_types'):
        score += 4

    # organizations: 4 points
    if project.get('organizations') and project['organizations'].strip():
        score += 4

    # maturity_tags: 5 points
    if project.get('maturity_tags'):
        score += 5

    return min(score, 100)


# Define the maturity funnel stages in order of progression (matching MaturityChart.jsx)
MATURITY_STAGES = [
    {'key': 'dataset', 'label': 'Datasets', 'patterns': ['dataset']},
    {'key': 'model', 'label': 'Models', 'patterns': ['model']},
    {'key': 'pilot', 'label': 'Pilots', 'patterns': ['pilot']},
    {'key': 'usecase', 'label': 'Use Cases', 'patterns': ['use-case', 'use case', 'usecase']},
    {'key': 'business', 'label': 'Business Model', 'patterns': ['business model', 'business-model', 'scaled']}
]


def parse_maturity_tags(maturity_string):
    """Parse maturity string and return list of maturity stage keys the project has reached."""
    if not maturity_string or not isinstance(maturity_string, str):
        return []
    
    normalized = maturity_string.lower().strip()
    reached_stages = []
    
    # Check each stage - if any pattern matches, this project has reached that stage
    for stage in MATURITY_STAGES:
        for pattern in stage['patterns']:
            if pattern in normalized:
                reached_stages.append(stage['key'])
                break  # Found this stage, move to next
    
    return reached_stages


def get_project_image(project_id):
    """Find the first image in the project's images directory."""
    images_dir = os.path.join(PROJECTS_DIR, project_id, "images")
    
    if os.path.exists(images_dir) and os.path.isdir(images_dir):
        image_files = [f for f in os.listdir(images_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        if image_files:
            return f"/projects/{project_id}/images/{image_files[0]}"
    
    return None


def get_hosted_documents(project_id):
    """
    List files under public/projects/<id>/documents/ for access-note projects.
    Returns [{'name': str, 'url': str}, ...] with site-relative URLs.
    """
    documents_dir = os.path.join(PROJECTS_DIR, project_id, "documents")
    if not os.path.isdir(documents_dir):
        return []

    items = []
    for root, _dirs, files in os.walk(documents_dir):
        files = sorted(f for f in files if f and not f.startswith("."))
        for filename in files:
            full_path = os.path.join(root, filename)
            if not os.path.isfile(full_path):
                continue
            rel = os.path.relpath(full_path, os.path.join(PROJECTS_DIR, project_id))
            rel_posix = rel.replace(os.sep, "/")
            url_path = f"/projects/{project_id}/{rel_posix}"
            display = filename.rsplit(".", 1)[0].replace("_", " ").strip() or filename
            items.append({"name": display, "url": url_path})

    items.sort(key=lambda x: x["url"].lower())
    return items


def migrate_project_directories_if_needed():
    """Rename title-based project dirs to stable ui_X names if needed."""
    try:
        df = pd.read_excel(args.input)
    except Exception:
        return
    if not os.path.isdir(PROJECTS_DIR):
        return
    existing_dirs = set(os.listdir(PROJECTS_DIR))
    for _, row in df.iterrows():
        project_id = row.get('Project ID', '')
        if pd.isna(project_id) or not str(project_id).strip():
            continue
        target = normalize_for_directory(str(project_id))
        if not target or target in existing_dirs:
            continue
        for col in ['Dataset Speaking Titles', 'Use Case Speaking Title', 'OnSite Name']:
            val = row.get(col, '')
            if val and not pd.isna(val):
                old = normalize_for_directory(str(val))
                if old and old in existing_dirs:
                    old_path = os.path.join(PROJECTS_DIR, old)
                    new_path = os.path.join(PROJECTS_DIR, target)
                    shutil.move(old_path, new_path)
                    existing_dirs.discard(old)
                    existing_dirs.add(target)
                    print(f"Migrated directory: '{old}' -> '{target}'")
                    break


def generate_catalog_json():
    """Generate catalog JSON from Excel file."""
    migrate_project_directories_if_needed()

    try:
        df = pd.read_excel(args.input)
        print(f"Successfully loaded data from {args.input}")
        print(f"DataFrame columns: {list(df.columns)}")
        
        # Clean text columns
        text_columns = ['Description - What can be done with this? What is this about?', 
                       'Data - Key Characteristics', 'Model/Use-Case - Key Characteristics', 
                       'Deep Dive - How can you concretely work with this and build on this?',
                       'Domain/SDG', 'Data Type', 'License', 'Country Team']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
        
        # Calculate statistics
        dataset_count = 0
        usecase_count = 0
        valid_countries = set()
        project_ids = set()
        projects = []
        
        # Collect unique values for filters
        all_sdgs = set()
        all_data_types = set()
        all_countries = set()
        
        for index, row in df.iterrows():
            dataset_link_text = row.get('Dataset Link', '')
            usecase_link_text = row.get('Model/Use-Case Links', '')

            dataset_urls = extract_http_links(dataset_link_text)
            usecase_urls = extract_http_links(usecase_link_text)

            has_dataset_link = len(dataset_urls) > 0
            has_usecase_link = len(usecase_urls) > 0

            # Resolve project ID before access-note / exclusion rules
            normalized_project_id, id_source, error_msg = resolve_project_id(row, row_idx=index)
            if error_msg or not normalized_project_id:
                print(f"Row {index}: Skipping - {error_msg}")
                continue

            access_note_kind = None
            access_note_markdown = None

            if not has_dataset_link and not has_usecase_link:
                prefix_kind = classify_access_note_prefix_kind(
                    dataset_link_text, usecase_link_text
                )
                if prefix_kind is not None:
                    access_note_kind = prefix_kind
                elif documents_dir_has_files(normalized_project_id):
                    access_note_kind = "documents"
                else:
                    continue
                merged_note = merge_access_note_link_columns(
                    dataset_link_text, usecase_link_text
                ).strip()
                access_note_markdown = merged_note if merged_note else None

            # Count only real http(s) links
            dataset_count += len(dataset_urls)
            usecase_count += len(usecase_urls)

            project_ids.add(normalized_project_id)
            
            # Count countries
            country_text = row.get('Country Team', '')
            if isinstance(country_text, str) and not pd.isna(country_text):
                parts = re.split(r',|\s+and\s+|;', country_text)
                for part in parts:
                    country = part.strip()
                    if country:
                        valid_countries.add(country)
                        all_countries.add(country)
            
            # Get display title
            onsite_name = row.get('OnSite Name', '')
            dataset_title = row.get('Dataset Speaking Titles', '')
            usecase_title = row.get('Use Case Speaking Title', '')
            
            if has_usecase_link and usecase_title and not pd.isna(usecase_title):
                title = usecase_title
            elif has_dataset_link and dataset_title and not pd.isna(dataset_title):
                title = dataset_title
            elif usecase_title and not pd.isna(usecase_title):
                title = usecase_title
            elif dataset_title and not pd.isna(dataset_title):
                title = dataset_title
            elif onsite_name and not pd.isna(onsite_name):
                title = onsite_name
            else:
                title = f"Project {normalized_project_id}"
            
            # Extract SDGs
            domain = row.get('Domain/SDG', '')
            sdgs = []
            if isinstance(domain, str):
                # Extract SDG numbers
                sdg_matches = re.findall(r'SDG\s*(\d+)', domain, re.IGNORECASE)
                for num in sdg_matches:
                    sdg_num = int(num)
                    if 1 <= sdg_num <= 17:
                        sdg_label = f"SDG {sdg_num}"
                        sdgs.append(sdg_label)
                        all_sdgs.add(sdg_label)
            
            # Extract data types
            data_type_text = row.get('Data Type', '')
            data_types = []
            if isinstance(data_type_text, str) and data_type_text:
                types = re.split(r'[,;]', data_type_text)
                data_types = [t.strip() for t in types if t.strip()]
                all_data_types.update(data_types)
            
            # Get project image
            image = get_project_image(normalized_project_id)
            
            # Check for Lacuna dataset
            lacuna_dataset = row.get('Lacuna Dataset', '')
            is_lacuna = isinstance(lacuna_dataset, str) and not pd.isna(lacuna_dataset) and \
                       lacuna_dataset.strip().lower() in ['yes', 'y', 'true', '1']
            
            # Parse maturity tags
            maturity_string = str(row.get('Maturity / Readiness for replication or scaling [INTERNAL]', ''))
            maturity_tags = parse_maturity_tags(maturity_string)
            
            # Parse additional resources column
            additional_resources_raw = row.get('Link to additional Resources (Paper, Publications, etc)', '')
            additional_resources = []
            if isinstance(additional_resources_raw, str) and not pd.isna(additional_resources_raw) and additional_resources_raw.strip():
                resource_text = additional_resources_raw.strip()
                # Extract any URLs from the text
                resource_urls = extract_links_allow_site_paths(resource_text)
                if resource_urls:
                    for ru in resource_urls:
                        label = ru['name']
                        # If label is just "Link", derive a nicer one from the URL
                        if label == 'Link' and ru['url']:
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(ru['url'])
                                if parsed.scheme in ('http', 'https'):
                                    domain = parsed.netloc.replace('www.', '')
                                    path = parsed.path.strip('/').split('/')
                                    slug = path[-1] if path and path[-1] else ''
                                    slug = slug.replace('-', ' ').replace('_', ' ')
                                    if slug and len(slug) > 3:
                                        label = f"{slug.title()} ({domain})"
                                    else:
                                        label = domain or 'Link'
                                elif ru['url'].startswith('/'):
                                    path = ru['url'].strip('/').split('/')
                                    slug = path[-1] if path and path[-1] else ''
                                    slug = slug.replace('-', ' ').replace('_', ' ')
                                    label = slug.title() if slug else 'Link'
                                else:
                                    label = 'Link'
                            except Exception:
                                label = 'Link'
                        additional_resources.append({'name': label, 'url': ru['url']})
                # Only include entries that have a valid URL (skip plain text notes for now)

            has_access_note = access_note_kind is not None
            hosted_documents = (
                get_hosted_documents(normalized_project_id) if has_access_note else []
            )

            # Compute URL slug (stable ID + cosmetic title hint)
            title_slug = normalize_for_directory(str(title))
            slug = f"{normalized_project_id}-{title_slug}" if title_slug else normalized_project_id

            # Compute aliases for backward-compatible URL resolution
            aliases = set()
            for alias_col in ['Dataset Speaking Titles', 'Use Case Speaking Title', 'OnSite Name']:
                alias_val = row.get(alias_col, '')
                if alias_val and not pd.isna(alias_val):
                    candidate = normalize_for_directory(str(alias_val))
                    if candidate and candidate != normalized_project_id:
                        aliases.add(candidate)

            # Create project object with normalized fields
            project = {
                'id': normalized_project_id,
                'slug': slug,
                'aliases': sorted(aliases),
                'title': str(title),
                'description': clean_str(str(row.get('Description - What can be done with this? What is this about?', ''))),
                'dataset_links': dataset_urls,
                'usecase_links': usecase_urls,
                'access_note_kind': access_note_kind,
                'access_note_markdown': access_note_markdown,
                'has_access_note': has_access_note,
                'hosted_documents': hosted_documents,
                'sdgs': sdgs,
                'data_types': data_types,
                'countries': clean_country_list(country_text),
                'license': normalize_license(str(row.get('License', ''))),
                'contact': clean_str(str(row.get('Point of Contact/Communities', ''))),
                'organizations': clean_str(str(row.get('Organizations Involved', ''))),
                'editor': clean_str(str(row.get('Authors', ''))),
                'is_lacuna': is_lacuna,
                'has_dataset': has_dataset_link,
                'has_usecase': has_usecase_link,
                'image': image,
                'data_characteristics': clean_str(str(row.get('Data - Key Characteristics', ''))),
                'model_characteristics': clean_str(str(row.get('Model/Use-Case - Key Characteristics', ''))),
                'how_to_use': clean_str(str(row.get('Deep Dive - How can you concretely work with this and build on this?', ''))),
                'maturity': maturity_string,
                'maturity_tags': maturity_tags,
                'additional_resources': additional_resources
            }

            # Compute and attach quality score
            project['quality_score'] = compute_quality_score(project)

            projects.append(project)
        
        # Calculate final counts
        project_count = len(project_ids)
        country_count = len(valid_countries)
        access_note_project_count = sum(1 for p in projects if p.get('has_access_note'))

        # Build alias lookup map: old_title_id -> stable_id
        alias_map = {}
        for p in projects:
            for alias in p.get('aliases', []):
                if alias in alias_map and alias_map[alias] != p['id']:
                    print(f"WARNING: Alias collision - '{alias}' maps to both '{alias_map[alias]}' and '{p['id']}'. Last one wins.")
                alias_map[alias] = p['id']

        # Create catalog data structure
        catalog_data = {
            'projects': projects,
            'aliases': alias_map,
            'stats': {
                'total_projects': project_count,
                'total_datasets': dataset_count,
                'total_usecases': usecase_count,
                'total_access_note_projects': access_note_project_count,
                'total_countries': country_count
            },
            'filters': {
                'sdgs': sorted(list(all_sdgs), key=lambda x: int(re.search(r'\d+', x).group())),
                'data_types': sorted(list(all_data_types)),
                'countries': sorted(list(all_countries)),
                'maturity_stages': [stage['key'] for stage in MATURITY_STAGES]
            }
        }
        
        # Write JSON file
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(catalog_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully generated {args.output}")
        print(f"  - {project_count} projects")
        print(f"  - {dataset_count} datasets")
        print(f"  - {usecase_count} use cases")
        print(f"  - {access_note_project_count} info / no public link projects")
        print(f"  - {country_count} countries")
        print(f"  - {len(all_sdgs)} SDGs")
        print(f"  - {len(all_data_types)} data types")
        
        return catalog_data
        
    except Exception as e:
        print(f"Error generating catalog: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = generate_catalog_json()
    if result:
        # Return project count for use by other scripts
        print(f"\nProject count: {result['stats']['total_projects']}")


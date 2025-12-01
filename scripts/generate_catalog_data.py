import pandas as pd
import json
import os
import re
import argparse
from utils import normalize_for_directory, is_valid_http_url, resolve_project_id

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate catalog JSON from Excel file.')
parser.add_argument('--input', type=str, default="docs/data_catalog.xlsx", help='Path to the input Excel file')
parser.add_argument('--output', type=str, default="public/data/catalog.json", help='Path to the output JSON file')
args = parser.parse_args()


def extract_urls(text):
    """Extract URLs from text."""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    urls = []
    # Pattern for markdown links [text](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    markdown_matches = re.findall(markdown_pattern, text)
    for name, url in markdown_matches:
        url = url.strip()
        if url.startswith('http'):
            urls.append({'name': name.strip(), 'url': url})
    
    # Pattern for plain URLs
    url_pattern = r'https?://[^\s,)\]>]+'
    plain_matches = re.findall(url_pattern, text)
    for url in plain_matches:
        url = url.strip()
        if url not in [u['url'] for u in urls]:
            urls.append({'name': 'Link', 'url': url})
    
    return urls


def has_valid_url(text):
    """Check if text contains at least one valid URL."""
    return len(extract_urls(text)) > 0


def get_project_image(project_id):
    """Find the first image in the project's images directory."""
    images_dir = os.path.join("docs/public/projects", project_id, "images")
    
    if os.path.exists(images_dir) and os.path.isdir(images_dir):
        image_files = [f for f in os.listdir(images_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        if image_files:
            return f"./public/projects/{project_id}/images/{image_files[0]}"
    
    return None


def generate_catalog_json():
    """Generate catalog JSON from Excel file."""
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
            # Check for valid links
            dataset_link_text = row.get('Dataset Link', '')
            usecase_link_text = row.get('Model/Use-Case Links', '')
            
            dataset_urls = extract_urls(dataset_link_text)
            usecase_urls = extract_urls(usecase_link_text)
            
            has_dataset_link = len(dataset_urls) > 0
            has_usecase_link = len(usecase_urls) > 0
            
            # Skip rows without valid links
            if not has_dataset_link and not has_usecase_link:
                continue
            
            # Count links
            if has_dataset_link:
                dataset_count += len(dataset_urls)
            if has_usecase_link:
                usecase_count += len(usecase_urls)
            
            # Resolve project ID
            normalized_project_id, id_source, error_msg = resolve_project_id(row, row_idx=index)
            if error_msg or not normalized_project_id:
                print(f"Row {index}: Skipping - {error_msg}")
                continue
            
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
            
            # Create project object
            project = {
                'id': normalized_project_id,
                'title': str(title),
                'description': str(row.get('Description - What can be done with this? What is this about?', '')),
                'dataset_links': dataset_urls,
                'usecase_links': usecase_urls,
                'sdgs': sdgs,
                'data_types': data_types,
                'countries': [c.strip() for c in re.split(r',|\s+and\s+|;', country_text) if c.strip()] if country_text else [],
                'license': str(row.get('License', '')),
                'contact': str(row.get('Point of Contact/Communities', '')),
                'organizations': str(row.get('Organizations Involved', '')),
                'authors': str(row.get('Authors', '')),
                'is_lacuna': is_lacuna,
                'has_dataset': has_dataset_link,
                'has_usecase': has_usecase_link,
                'image': image,
                'data_characteristics': str(row.get('Data - Key Characteristics', '')),
                'model_characteristics': str(row.get('Model/Use-Case - Key Characteristics', '')),
                'how_to_use': str(row.get('Deep Dive - How can you concretely work with this and build on this?', '')),
                'maturity': str(row.get('Maturity / Readiness for replication or scaling [INTERNAL]', ''))
            }
            
            projects.append(project)
        
        # Calculate final counts
        project_count = len(project_ids)
        country_count = len(valid_countries)
        
        # Create catalog data structure
        catalog_data = {
            'projects': projects,
            'stats': {
                'total_projects': project_count,
                'total_datasets': dataset_count,
                'total_usecases': usecase_count,
                'total_countries': country_count
            },
            'filters': {
                'sdgs': sorted(list(all_sdgs), key=lambda x: int(re.search(r'\d+', x).group())),
                'data_types': sorted(list(all_data_types)),
                'countries': sorted(list(all_countries))
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


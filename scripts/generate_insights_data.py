import argparse
import pandas as pd
import json
import re
from collections import Counter
from utils import resolve_project_id

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate insights data JSON from data catalog.')
parser.add_argument('--input', type=str, default="docs/data_catalog.xlsx", help='Path to the input Excel file')
parser.add_argument('--output', type=str, default="public/data/insights.json", help='Path to the output JSON file')
parser.add_argument('--project-count', type=int, help='Total project count from catalog page')
args = parser.parse_args()


def extract_urls(text):
    """Extract URLs from text."""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    urls = []
    # Pattern for markdown links [text](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    markdown_matches = re.findall(markdown_pattern, text)
    for _, url in markdown_matches:
        url = url.strip()
        if url.startswith('http'):
            urls.append(url)
    
    # Pattern for plain URLs
    url_pattern = r'https?://[^\s,)\]>]+'
    plain_matches = re.findall(url_pattern, text)
    for url in plain_matches:
        url = url.strip()
        if url not in urls:
            urls.append(url)
    
    return urls


def analyze_data(excel_path):
    """Analyze the Excel data and extract insights."""
    try:
        df = pd.read_excel(excel_path)
        print(f"Loaded {len(df)} rows from {excel_path}")
        
        # Country name to ISO Alpha-2 code mapping
        country_iso_map = {
            'Kenya': 'KE', 'India': 'IN', 'South Africa': 'ZA', 'Ghana': 'GH',
            'Rwanda': 'RW', 'Uganda': 'UG', 'Indonesia': 'ID', 'Nigeria': 'NG',
            'Tanzania': 'TZ', 'Ecuador': 'EC', 'DRC': 'CD', 'Congo': 'CG',
            'Democratic Republic of the Congo': 'CD', 'Benin': 'BJ', 'Colombia': 'CO',
            "Cote d'Ivoire": 'CI', 'Ivory Coast': 'CI', 'Angola': 'AO',
            'Mozambique': 'MZ', 'Zambia': 'ZM', 'Niger': 'NE', 'Togo': 'TG',
            'Cameroon': 'CM', 'Madagascar': 'MG', 'Pakistan': 'PK', 'Malawi': 'MW',
            'Ethiopia': 'ET', 'Senegal': 'SN', 'Mali': 'ML', 'Burkina Faso': 'BF',
            'Bangladesh': 'BD', 'Nepal': 'NP', 'Sri Lanka': 'LK', 'Myanmar': 'MM',
            'Thailand': 'TH', 'Vietnam': 'VN', 'Cambodia': 'KH', 'Laos': 'LA',
            'Philippines': 'PH', 'Malaysia': 'MY', 'Peru': 'PE', 'Bolivia': 'BO',
            'Brazil': 'BR', 'Argentina': 'AR', 'Chile': 'CL', 'Mexico': 'MX',
            'Guatemala': 'GT', 'Honduras': 'HN', 'Nicaragua': 'NI', 'Costa Rica': 'CR',
            'Panama': 'PA'
        }
        
        # Extract country distribution - ONLY from projects with valid links
        country_counts = Counter()
        country_sdgs = {}  # Track SDGs per country
        country_data_types = {}  # Track data types per country
        project_ids = set()
        sdg_counts = Counter()  # Global SDG counts
        
        for index, row in df.iterrows():
            # Only count rows with valid dataset OR use case links
            dataset_link_text = row.get('Dataset Link', '')
            usecase_link_text = row.get('Model/Use-Case Links', '')
            
            has_dataset_link = len(extract_urls(dataset_link_text)) > 0
            has_usecase_link = len(extract_urls(usecase_link_text)) > 0
            
            # Skip rows without valid links
            if not has_dataset_link and not has_usecase_link:
                continue
            
            # Count this project
            normalized_project_id, id_source, error_msg = resolve_project_id(row, row_idx=index)
            if normalized_project_id and not error_msg:
                project_ids.add(normalized_project_id)
            
            # Extract SDGs for this row
            domain = row.get('Domain/SDG', '')
            row_sdgs = []
            if isinstance(domain, str):
                sdg_matches = re.findall(r'SDG\s*(\d+)', domain, re.IGNORECASE)
                for num in sdg_matches:
                    sdg_num = int(num)
                    if 1 <= sdg_num <= 17:
                        sdg_label = f"SDG {sdg_num}"
                        row_sdgs.append(sdg_label)
                        sdg_counts[sdg_label] += 1
            
            # Extract data types for this row
            data_type_text = row.get('Data Type', '')
            row_data_types = []
            if isinstance(data_type_text, str) and data_type_text:
                types = re.split(r'[,;]', data_type_text)
                row_data_types = [t.strip() for t in types if t.strip()]
            
            # Extract countries
            country_text = row.get('Country Team', '')
            if isinstance(country_text, str) and not pd.isna(country_text):
                # Split by common delimiters
                parts = re.split(r',|\s+and\s+|;|/', country_text)
                for part in parts:
                    country = part.strip()
                    # Clean up common variations
                    country = re.sub(r'\(.*?\)', '', country).strip()
                    country = country.replace('Republic of', '').strip()
                    country = country.replace('Democratic Republic of', '').strip()
                    
                    # Skip generic entries
                    if country and len(country) > 1 and country not in ['Global', 'Regional']:
                        country_counts[country] += 1
                        # Track SDGs for this country
                        if country not in country_sdgs:
                            country_sdgs[country] = set()
                        country_sdgs[country].update(row_sdgs)
                        # Track data types for this country
                        if country not in country_data_types:
                            country_data_types[country] = set()
                        country_data_types[country].update(row_data_types)
        
        # Prepare data for map visualization with ISO codes
        map_data = {}
        for country, count in country_counts.items():
            iso_code = country_iso_map.get(country)
            if iso_code:
                sdgs = sorted(list(country_sdgs.get(country, [])), 
                             key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
                data_types = sorted(list(country_data_types.get(country, [])))
                map_data[iso_code] = {
                    'name': country,
                    'projects': count,
                    'iso2': iso_code,
                    'sdgs': sdgs,
                    'data_types': data_types
                }
        
        # Calculate summary stats
        total_projects = len(project_ids)
        total_countries = len(country_counts)
        
        # Sort SDG counts for display
        sorted_sdgs = sorted(sdg_counts.items(), 
                            key=lambda x: int(re.search(r'\d+', x[0]).group()) if re.search(r'\d+', x[0]) else 0)
        
        return {
            'total_projects': total_projects,
            'total_countries': total_countries,
            'map_data': map_data,
            'sdg_distribution': dict(sorted_sdgs)
        }
        
    except Exception as e:
        print(f"Error analyzing data: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_insights_json():
    """Generate insights JSON file."""
    
    # Analyze the data
    insights = analyze_data(args.input)
    if not insights:
        print("Failed to analyze data, exiting.")
        return
    
    # Use project count from catalog if provided
    if args.project_count:
        insights['total_projects'] = args.project_count
    
    # Write JSON file
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    
    print(f"Generated insights data at {args.output}")
    print(f"  - {insights['total_projects']} projects")
    print(f"  - {insights['total_countries']} countries covered")


if __name__ == "__main__":
    generate_insights_json()


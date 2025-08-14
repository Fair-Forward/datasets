import pandas as pd
import html
import os
import re
import colorsys
import argparse
import datetime
from urllib.parse import urlparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate HTML catalog from Excel file.')
parser.add_argument('--input', type=str, default="docs/data_catalog.xlsx", help='Path to the input Excel file')
parser.add_argument('--output', type=str, default="docs/index.html", help='Path to the output HTML file')
args = parser.parse_args()

# Load the dataset
DATA_CATALOG = args.input
HTML_OUTPUT = args.output

# Function to convert markdown links to HTML
def convert_markdown_links_to_html(text):
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # First, normalize whitespace around commas
    text = re.sub(r'\s*,\s*', ', ', text)
    
    # Split by commas but keep the commas
    parts = re.split(r'(,\s*)', text)
    result = []
    
    for part in parts:
        # If this part is just a comma and whitespace, add it as is
        if re.match(r'^,\s*$', part):
            result.append(part)
            continue
            
        # Trim whitespace
        part = part.strip()
        if not part:
            continue
            
        # Handle the format: "Name (URL)" - common in the Point of Contact field
        url_match = re.search(r'([^(]+)\s*\((https?://[^)]+)\)', part)
        if url_match:
            display_name = url_match.group(1).strip()
            link_url = url_match.group(2).strip()
            result.append(f'<a href="{link_url}" target="_blank">{display_name}</a>')
            continue
            
        # Handle email addresses: "Name (email@example.com)"
        email_match = re.search(r'([^(]+)\s*\(([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\)', part)
        if email_match:
            display_name = email_match.group(1).strip()
            email = email_match.group(2).strip()
            result.append(f'<a href="mailto:{email}">{display_name}</a>')
            continue
            
        # Handle markdown links: [Name](URL)
        markdown_match = re.search(r'\[(.*?)\]\((.*?)\)', part)
        if markdown_match:
            display_name = markdown_match.group(1).strip()
            link_url = markdown_match.group(2).strip()
            result.append(f'<a href="{link_url}" target="_blank">{display_name}</a>')
            continue
            
        # If no patterns match, keep the original text
        result.append(part)
    
    # Join all parts back together
    return ''.join(result)

# Function to normalize label text for CSS class names
def normalize_label(text):
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Convert to lowercase, replace spaces with hyphens, remove special characters
    normalized = re.sub(r'[^a-z0-9\-]', '', text.lower().replace(' ', '-'))
    return normalized

# Function to normalize a string for use as a directory name
def normalize_for_directory(text):
    if not text or pd.isna(text) or not isinstance(text, str):
        return ""
    # Convert to lowercase, replace spaces with underscores, remove special characters
    normalized = re.sub(r'[^a-z0-9_]', '', text.lower().replace(' ', '_'))
    return normalized

# Function to create HTML for labels
def create_label_html(text, label_type):
    if pd.isna(text) or not isinstance(text, str) or text.strip() == "":
        return ""
    
    # Split by commas or semicolons
    labels = re.split(r'[,;]', text)
    html_labels = []
    
    for label in labels:
        label = label.strip()
        if label:
            normalized = normalize_label(label)
            if normalized:
                html_labels.append(f'<span class="tag label-{normalized}" data-filter="{label}">{label}</span>')
    
    return "".join(html_labels)

# Function to get unique categories for generating CSS and filters
def get_unique_categories(df):
    domains = set()
    data_types = set()
    statuses = set()
    regions = set() # This will store unique regions from *valid* rows
    lacuna_datasets = set() # This will store Lacuna Fund datasets
    
    # Iterate through DataFrame rows to check for valid links
    for index, row in df.iterrows():
        # Check for valid links
        has_dataset_link = isinstance(row.get('Dataset Link'), str) and not pd.isna(row.get('Dataset Link'))
        has_usecase_link = isinstance(row.get('Model/Use-Case Links'), str) and not pd.isna(row.get('Model/Use-Case Links'))
        is_valid_row = has_dataset_link or has_usecase_link

        # Process Domains (only if row is valid - optional, based on user need)
        # If you want Domains/Data Types/Statuses filters to also only show
        # categories from active projects, apply the is_valid_row check here too.
        domain_col = 'Domain/SDG'
        if domain_col in df.columns:
            domain_text = row.get(domain_col)
            if isinstance(domain_text, str) and not pd.isna(domain_text):
                if is_valid_row: # <<< Filter domains to only show from valid projects
                    for domain in re.split(r'[,;]', domain_text):
                        domain = domain.strip()
                        if domain:
                            domains.add(domain)
        
        # Process Data Types (only if row is valid - optional)
        data_type_col = 'Data Type'
        if data_type_col in df.columns:
            type_text = row.get(data_type_col)
            if isinstance(type_text, str) and not pd.isna(type_text):
                if is_valid_row: # <<< Filter data types to only show from valid projects
                    for data_type in re.split(r'[,;]', type_text):
                        data_type = data_type.strip()
                        if data_type:
                            data_types.add(data_type)
        
        # Process Statuses (only if row is valid - optional)
        status_col = 'Use Case Pipeline Status'
        if status_col in df.columns:
            status_text = row.get(status_col)
            if isinstance(status_text, str) and not pd.isna(status_text):
                if is_valid_row: # <<< Filter statuses to only show from valid projects
                    for status in re.split(r'[,;]', status_text):
                        status = status.strip()
                        if status:
                            statuses.add(status)
        
        # --- Process Regions (ONLY if row is valid) ---
        region_col = 'Country Team'
        if region_col in df.columns and is_valid_row: # Apply the check here
            region_text = row.get(region_col)
            if isinstance(region_text, str) and not pd.isna(region_text):
                for region in re.split(r'[,;]', region_text):
                    region = region.strip()
                    if region:
                        regions.add(region)
        
        # --- Process Lacuna Dataset (ONLY if row is valid) ---
        lacuna_col = 'Lacuna Dataset'
        if lacuna_col in df.columns and is_valid_row:
            lacuna_text = row.get(lacuna_col)
            if isinstance(lacuna_text, str) and not pd.isna(lacuna_text):
                lacuna_text = lacuna_text.strip().lower()
                if lacuna_text in ['yes', 'y', 'true', '1']:
                    lacuna_datasets.add('Yes')
    
    return list(domains), list(data_types), list(statuses), list(regions), list(lacuna_datasets)

# Function to generate CSS for labels
def generate_label_css(domains, data_types, statuses):
    css = ""
    
    # Generate a color palette with enough colors for all categories
    total_categories = len(domains) + len(data_types) + len(statuses)
    colors = generate_color_palette(total_categories)
    color_index = 0
    
    # Generate CSS for domains
    for domain in domains:
        normalized = normalize_label(domain)
        if normalized:
            hue = colors[color_index]
            # Create styles for both label- and domain- prefixes
            css += f"""
.label-{normalized} {{
    background-color: {get_pastel_color(hue)};
    color: #2d3748;
}}

.domain-{normalized} {{
    background-color: {get_pastel_color(hue)};
    color: #2d3748;
}}
"""
            color_index += 1
    
    # Generate CSS for data types
    for data_type in data_types:
        normalized = normalize_label(data_type)
        if normalized:
            hue = colors[color_index]
            css += f"""
.label-{normalized} {{
    background-color: {get_pastel_color(hue)};
    color: #2d3748;
}}
"""
            color_index += 1
    
    # Generate CSS for statuses
    for status in statuses:
        normalized = normalize_label(status)
        if normalized:
            hue = colors[color_index]
            css += f"""
.label-{normalized} {{
    background-color: {get_pastel_color(hue)};
    color: #2d3748;
}}
"""
            color_index += 1
    
    return css

# Function to generate a pastel color from a hue value
def get_pastel_color(hue):
    # Convert HSL to RGB with moderate lightness and saturation for more visible but still minimalistic colors
    r, g, b = colorsys.hls_to_rgb(hue, 0.85, 0.25)
    # Convert to hex
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

# Function to generate evenly spaced colors
def generate_color_palette(n):
    return [i/n for i in range(n)]

def generate_card_html(row, idx):
    # --- Extract card data ---
    project_id = row.get('Project ID', '') # Get Project ID
    onsite_name = row.get('OnSite Name', '')
    dataset_speaking_title = row.get('Dataset Speaking Titles', '')
    usecase_speaking_title = row.get('Use Case Speaking Title', '')
    description = row.get('Description - What can be done with this? What is this about?', '')
    dataset_link = row.get('Dataset Link', '')
    model_links = row.get('Model/Use-Case Links', '')
    domain = row.get('Domain/SDG', '')
    status = row.get('Use Case Pipeline Status', '')
    data_type = row.get('Data Type', '')
    contact = row.get('Point of Contact/Communities', '')
    region = row.get('Country Team', '')
    # --- Extract new columns ---
    organizations = row.get('Organizations Involved', '')
    authors = row.get('Authors', '')
    lacuna_dataset = row.get('Lacuna Dataset', '')
    # --- End Extract new columns ---
    
    # --- Basic Checks ---
    # Skip if Project ID is missing (shouldn't happen if build script requires it, but good check)
    if not project_id or pd.isna(project_id):
        print(f"Warning: Skipping card generation for row {idx} due to missing Project ID.")
        return "" # Return empty string to skip card
        
    # Normalize the Project ID once
    normalized_project_id = normalize_for_directory(str(project_id))
    if not normalized_project_id:
        print(f"Warning: Skipping card generation for row {idx} due to invalid Project ID '{project_id}'.")
        return ""

    # Determine if row has dataset and/or use case
    has_dataset = isinstance(dataset_link, str) and not pd.isna(dataset_link)
    has_usecase = isinstance(model_links, str) and not pd.isna(model_links)
    
    # --- Determine Display Title --- 
    # Select the appropriate title based on content type and speaking titles (for display)
    if has_usecase and usecase_speaking_title and not pd.isna(usecase_speaking_title):
        title = usecase_speaking_title
    elif has_dataset and dataset_speaking_title and not pd.isna(dataset_speaking_title):
        title = dataset_speaking_title
    elif onsite_name and not pd.isna(onsite_name):
        title = onsite_name
    else:
        title = f"Project {project_id}" # Fallback display title

    # --- Card Classes --- 
    card_classes = ["card"]
    if has_dataset:
        card_classes.append("has-dataset")
    if has_usecase:
        card_classes.append("has-usecase")
    
    # Add Lacuna Fund class if applicable
    has_lacuna = isinstance(lacuna_dataset, str) and not pd.isna(lacuna_dataset) and lacuna_dataset.strip().lower() in ['yes', 'y', 'true', '1']
    if has_lacuna:
        card_classes.append("has-lacuna")
    
    card_class = " ".join(card_classes)
    
    # --- Image Handling (Using Project ID) ---
    card_image = '<div class="card-image"></div>' # Default: no image div
    project_image_path = None
    images_dir = os.path.join("docs/public/projects", normalized_project_id, "images")

    # Check if the images directory exists and contains any images
    if os.path.exists(images_dir):
        image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        
        if image_files: # Only proceed if images are found
            # Sort image files to prioritize real images over placeholder images
            real_images = [f for f in image_files if not f.startswith('placeholder_')]
            placeholder_images = [f for f in image_files if f.startswith('placeholder_')]
            
            chosen_image_file = None
            if real_images:
                chosen_image_file = real_images[0] # Use the first real image
            elif placeholder_images:
                chosen_image_file = placeholder_images[0] # Use the first placeholder image
            
            if chosen_image_file:
                 # Construct the relative path for the HTML src attribute
                project_image_path = f"public/projects/{normalized_project_id}/images/{chosen_image_file}"
                # Escape path for CSS background-image style
                # Fixed: ensure proper escaping for CSS url()
                escaped_image_path = project_image_path.replace("\\", "/").replace("'", "\\'").replace("\"", "\\\"") 
                card_image = f'<div class="card-image has-image" style="background-image: url(\'{escaped_image_path}\');"></div>'

    # --- Domain Badges --- 
    # (No changes needed here)
    domain_badges = ""
    domain_list = []
    if domain and not pd.isna(domain):
        domain_badges_html = []
        for d in re.split(r'[,;]', str(domain)):
            d = d.strip()
            if d:
                domain_list.append(d)
                normalized = normalize_label(d)
                domain_badges_html.append(f'<div class="domain-badge domain-{normalized}">{d}</div>')
        
        if domain_badges_html:
            domain_badges = f'<div class="domain-badges">{"".join(domain_badges_html)}</div>'
    
    # --- Meta Items (Region, Contact) ---
    meta_items = []
    # Region
    if region and not pd.isna(region):
        clean_region = re.sub(r'\s+', ' ', str(region).strip())
        meta_items.append(f'<div class="meta-item"><i class="fas fa-map-marker-alt"></i> {html.escape(clean_region)}</div>')
    
    # Contact
    if contact and not pd.isna(contact):
        contact_html = convert_markdown_links_to_html(contact)
        meta_items.append(f'<div class="meta-item"><i class="fas fa-user"></i> {contact_html}</div>')
        
    # --- REMOVE Authors and Organizations from visible meta items ---
    # if authors and not pd.isna(authors):
    #     authors_html = convert_markdown_links_to_html(str(authors))
    #     meta_items.append(f'<div class="meta-item"><i class="fas fa-pen-alt"></i> {authors_html}</div>')
    # if organizations and not pd.isna(organizations):
    #     organizations_html = convert_markdown_links_to_html(str(organizations))
    #     meta_items.append(f'<div class="meta-item"><i class="fas fa-building"></i> {organizations_html}</div>')
        
    # --- Combine Remaining Meta Items ---
    meta_html = ""
    if meta_items:
        meta_html = f'<div class="meta">{"".join(meta_items)}</div>'
    
    # --- Process Authors and Organizations for Data Attributes ---
    authors_data_attr = ""
    if authors and not pd.isna(authors):
        # Process potential links/markdown within the authors string
        authors_data_attr = html.escape(convert_markdown_links_to_html(str(authors)), quote=True)
        
    organizations_data_attr = ""
    if organizations and not pd.isna(organizations):
        # Process potential links/markdown within the organizations string
        organizations_data_attr = html.escape(convert_markdown_links_to_html(str(organizations)), quote=True)

    # --- Data Type Chips --- 
    # (No changes needed here)
    data_type_chips = []
    if data_type and not pd.isna(data_type):
        for dt in re.split(r'[,;]', str(data_type)):
            dt = dt.strip()
            if dt:
                normalized = normalize_label(dt)
                # Choose icon based on data type
                icon = "fa-database"  # default icon
                if normalized == "images":
                    icon = "fa-image"
                elif normalized == "audio":
                    icon = "fa-volume-up"
                elif normalized == "text":
                    icon = "fa-file-alt"
                elif normalized == "geospatial":
                    icon = "fa-map"
                elif normalized == "tabular":
                    icon = "fa-table"
                elif normalized == "video":
                    icon = "fa-video"
                
                data_type_chips.append(f'<span class="data-type-chip label-{normalized}" data-filter="{dt}"><i class="fas {icon}"></i> {dt}</span>')
    
    data_type_html = ""
    if data_type_chips:
        data_type_html = f'<div class="data-type-chips">{"".join(data_type_chips)}</div>'
    
    # --- Tags for Filtering (Hidden) --- 
    # (No changes needed here)
    tags = []
    # Add domain tags for filtering (hidden)
    for d in domain_list:
        normalized = normalize_label(d)
        tags.append(f'<span class="tag label-{normalized}" data-filter="{d}" style="display:none;">{d}</span>')
    
    # Add data type tags for filtering (hidden)
    if data_type and not pd.isna(data_type):
        for dt in re.split(r'[,;]', str(data_type)):
            dt = dt.strip()
            if dt:
                normalized = normalize_label(dt)
                tags.append(f'<span class="tag label-{normalized}" data-filter="{dt}" style="display:none;">{dt}</span>')
    
    tags_html = ""
    if tags:
        tags_html = f'<div class="tags">{"".join(tags)}</div>'
    
    # --- Description --- 
    # (No changes needed here)
    description_html = ""
    if description and not pd.isna(description):
        description_html = f'''
            <div class="card-description">
                <div class="description-text collapsed">{html.escape(str(description))}</div>
                <div class="details-link"><i class="fas fa-arrow-right"></i><span>See Details</span></div>
            </div>
        '''
    
    # --- Hidden Links (Dataset/Use Case Buttons) ---
    hidden_links = []
    # Process Dataset Links
    if has_dataset and dataset_link:
        # --- Revised splitting logic ---
        processed_link_string = str(dataset_link).replace(',', ';') # Replace commas with semicolons
        dataset_link_entries = [s.strip() for s in processed_link_string.split(';') if s.strip()]
        # --- End revised splitting logic ---
        is_single_dataset = len(dataset_link_entries) == 1
        for i, link_entry in enumerate(dataset_link_entries):
            link_url = link_entry
            # Adjust default link name based on count
            link_name = "Dataset" if is_single_dataset else f"Dataset {i+1}"

            # Check for "Name (URL)" format
            name_url_match = re.search(r'([^(]+)\s*\((https?://[^)]+)\)', link_entry)
            if name_url_match:
                link_name = name_url_match.group(1).strip()
                link_url = name_url_match.group(2).strip()
            # Check for Markdown link: [Name](URL)
            else:
                md_match = re.search(r'\[(.*?)\]\((.*?)\)', link_entry)
                if md_match:
                    link_name = md_match.group(1).strip()
                    link_url = md_match.group(2).strip()
                # else: it's a bare URL, link_url is already set, link_name is default
            
            # Check for email (should ideally not be a primary dataset link, but handle)
            email_match = re.search(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', link_url, re.IGNORECASE)
            if email_match:
                 # For mailto, link_name might be better derived if not explicitly given
                if link_name == f"Dataset {i+1}": # if still default
                    name_part_of_email_match = re.search(r'([^(]+)\s*\(([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\)', link_entry)
                    if name_part_of_email_match: link_name = name_part_of_email_match.group(1).strip() 
                    else: link_name = f"Email Contact {i+1}"
                link_url = f"mailto:{email_match.group(1)}"
            
            escaped_link_name = html.escape(link_name)
            # Ensure this append is INSIDE the loop for each link_entry
            hidden_links.append(f'<a href="{link_url}" target="_blank" class="btn btn-primary hidden-link" data-link-type="dataset" data-link-name="{escaped_link_name}" style="display:none;">View {escaped_link_name}</a>')

    # Process Use Case Links (similarly)
    if has_usecase and model_links:
        # --- Revised splitting logic ---
        processed_model_link_string = str(model_links).replace(',', ';')
        usecase_link_entries = [s.strip() for s in processed_model_link_string.split(';') if s.strip()]
        # --- End revised splitting logic ---
        is_single_usecase = len(usecase_link_entries) == 1
        for i, link_entry in enumerate(usecase_link_entries):
            link_url = link_entry
            # Adjust default link name based on count
            link_name = "Use Case" if is_single_usecase else f"Use Case {i+1}"

            name_url_match = re.search(r'([^(]+)\s*\((https?://[^)]+)\)', link_entry)
            if name_url_match:
                link_name = name_url_match.group(1).strip()
                link_url = name_url_match.group(2).strip()
            else:
                md_match = re.search(r'\[(.*?)\]\((.*?)\)', link_entry)
                if md_match:
                    link_name = md_match.group(1).strip()
                    link_url = md_match.group(2).strip()

            email_match = re.search(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', link_url, re.IGNORECASE)
            if email_match:
                if link_name == f"Use Case {i+1}":
                    name_part_of_email_match = re.search(r'([^(]+)\s*\(([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\)', link_entry)
                    if name_part_of_email_match: link_name = name_part_of_email_match.group(1).strip()
                    else: link_name = f"Email Contact {i+1}"
                link_url = f"mailto:{email_match.group(1)}"

            escaped_link_name = html.escape(link_name)
            # Ensure this append is INSIDE the loop for each link_entry
            hidden_links.append(f'<a href="{link_url}" target="_blank" class="btn btn-secondary hidden-link" data-link-type="usecase" data-link-name="{escaped_link_name}" style="display:none;">View {escaped_link_name}</a>')
    
    hidden_links_html = ""
    if hidden_links:
        hidden_links_html = f'<div class="hidden-links" style="display:none;">{"".join(hidden_links)}</div>'
    
    # --- Footer Links (Data Type Chips, License) --- 
    # (No changes needed here)
    footer_links = []
    
    # Add data type chips to the footer if they exist
    if data_type_chips:
        footer_links.append(f'<div class="data-type-chips footer-chips">{"".join(data_type_chips)}</div>')
    
    # --- Process License Tag with Link Handling ---
    license_text = row.get('License', '')
    license_html = '' # Initialize
    
    if license_text and not pd.isna(license_text) and str(license_text).strip():
        text_content = str(license_text).strip()
        link_name = None
        link_url = None
        
        # 1. Check for Markdown link: [Name](URL)
        md_match = re.search(r'\[(.*?)\]\((.*?)\)', text_content)
        if md_match:
            link_name = md_match.group(1).strip()
            link_url = md_match.group(2).strip()
            
        # 2. Check for Name (URL) format
        elif '(' in text_content and ')' in text_content and 'http' in text_content:
             name_url_match = re.search(r'([^(]+)\s*\((https?://[^)]+)\)', text_content)
             if name_url_match:
                 link_name = name_url_match.group(1).strip()
                 link_url = name_url_match.group(2).strip()

        # 3. Check for bare URL
        elif text_content.startswith('http://') or text_content.startswith('https://'):
            url_match = re.search(r'(https?://\S+)', text_content)
            if url_match:
                link_url = url_match.group(1)
                link_name = None # Initialize link_name here

                try:
                    parsed_url = urlparse(link_url)
                    path = parsed_url.path.strip('/') # Get path e.g., 'licenses/agpl-3.0.html'
                    
                    # --- START: Specific Creative Commons URL Handling ---
                    is_cc_url = "creativecommons.org" in parsed_url.netloc and path.startswith("licenses/")
                    if is_cc_url:
                        path_parts = [part for part in path.split('/') if part] # e.g., ['licenses', 'by', '4.0']
                        if len(path_parts) >= 3 and path_parts[0] == 'licenses':
                            version = path_parts[-1]
                            components = path_parts[1:-1]
                            if version and components:
                                link_name = f"cc-{'-'.join(components)}-{version}" # e.g., cc-by-4.0
                    # --- END: Specific Creative Commons URL Handling ---
                    
                    # --- START: Specific Open Data Commons URL Handling ---
                    # Check if already handled by CC or if it's an ODC URL
                    elif not link_name and "opendatacommons.org" in parsed_url.netloc and path.startswith("licenses/"):
                        path_parts = [part for part in path.split('/') if part] # e.g., ['licenses', 'dbcl', '1-0']
                        if len(path_parts) >= 3 and path_parts[0] == 'licenses':
                            version = path_parts[-1]
                            # Assume the part before version is the license abbreviation
                            license_abbr = path_parts[-2]
                            if version and license_abbr:
                                link_name = f"{license_abbr}-{version}" # e.g., dbcl-1-0
                    # --- END: Specific Open Data Commons URL Handling ---

                    # --- General Path/Filename Extraction (if not handled by specific cases) ---
                    if not link_name and path:
                        filename = os.path.basename(path) # Get e.g., 'agpl-3.0.html' or '4.0'
                        name_part, _ = os.path.splitext(filename) # Get e.g., 'agpl-3.0' or '4.0'
                        if name_part:
                            link_name = name_part

                    # Fallback to domain name if no name extracted yet
                    if not link_name:
                        link_name = parsed_url.netloc or "License Link" # Use domain or default

                except Exception as e:
                    # If any error occurs during parsing, fall back safely
                    print(f"Warning: Could not parse license URL '{link_url}' effectively: {e}")
                    # Attempt fallback to domain name again, just in case
                    try:
                         parsed_url_fallback = urlparse(link_url)
                         link_name = parsed_url_fallback.netloc or "License Link"
                    except:
                         link_name = "License Link" # Absolute fallback

        # 4. If URL found, create link, otherwise use plain text
        if link_url and link_name:
            # Escape name for safety, URL is used directly in href
            escaped_name = html.escape(link_name)
            license_html = f'<div class="license-tag"><i class="fas fa-copyright"></i> <a href="{link_url}" target="_blank">{escaped_name}</a></div>'
        else:
            # No link found or extracted, display plain text
            escaped_license = html.escape(text_content)
            license_html = f'<div class="license-tag"><i class="fas fa-copyright"></i> {escaped_license}</div>'
            
    else:
        # Use the default placeholder if license is empty or invalid
        license_html = f'<div class="license-tag"><i class="fas fa-copyright"></i> cc-by-4.0 </div>'

    # Add the generated or default license HTML to footer links
    footer_links.append(license_html)
    
    footer_html = f'<div class="card-footer">{"".join(footer_links)}</div>'
    
    # --- Construct the complete card --- 
    # Add data-authors and data-organizations attributes
    card_html = f'''
    <div class="{card_class}" \
         data-title="{html.escape(str(title))}" \
         data-region="{html.escape(str(region))}" \
         data-id="{idx}" \
         data-project-id="{normalized_project_id}" \
         data-authors="{authors_data_attr}" \
         data-organizations="{organizations_data_attr}" \
         data-lacuna="{str(has_lacuna).lower()}">
        {card_image}
        <div class="card-header">
            {domain_badges}
            <h3>{html.escape(str(title))}</h3>
            {meta_html}
        </div>
        <div class="card-body">
            {description_html}
            {tags_html}
            {hidden_links_html}
        </div>
        {footer_html}
    </div>
    '''
    
    return card_html

def generate_filter_html(domains, data_types, regions, lacuna_datasets):
    domain_options = '\n'.join([f'<option value="{domain}">{domain}</option>' for domain in sorted(domains)])
    data_type_options = '\n'.join([f'<option value="{data_type}">{data_type}</option>' for data_type in sorted(data_types)])
    region_options = '\n'.join([f'<option value="{region}">{region}</option>' for region in sorted(regions)])
    lacuna_options = '\n'.join([f'<option value="{lacuna}">{lacuna}</option>' for lacuna in sorted(lacuna_datasets)])
    
    filter_html = f'''
    <div class="filters">
        <div class="filters-content">
            <div class="filter-group">
                <div class="search-box">
                    <i class="fas fa-search"></i>
                    <input type="text" id="searchInput" placeholder="Search datasets and use-cases..." autocomplete="off">
                </div>
            </div>
            <div class="filter-group">
                <span class="filter-label">View:</span>
                <select id="viewFilter">
                    <option value="all">All Items</option>
                    <option value="datasets">Datasets Only</option>
                    <option value="usecases">Use Cases Only</option>
                    <option value="lacuna">Lacuna Fund</option>
                </select>
            </div>
            <div class="filter-group">
                <span class="filter-label">Domain:</span>
                <select id="domainFilter">
                    <option value="all">All Domains</option>
                    {domain_options}
                </select>
            </div>
            <div class="filter-group">
                <span class="filter-label">Data Type:</span>
                <select id="dataTypeFilter">
                    <option value="all">All Data Types</option>
                    {data_type_options}
                </select>
            </div>
            <div class="filter-group">
                <span class="filter-label">Region:</span>
                <select id="regionFilter">
                    <option value="all">All Regions</option>
                    {region_options}
                </select>
            </div>
        </div>
    </div>
    '''
    
    return filter_html

def generate_js_code():
    return '''
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Get filter elements
            const searchInput = document.getElementById('searchInput');
            const viewFilter = document.getElementById('viewFilter');
            const domainFilter = document.getElementById('domainFilter');
            const dataTypeFilter = document.getElementById('dataTypeFilter');
            const regionFilter = document.getElementById('regionFilter');
            const emptyState = document.getElementById('emptyState');
            const cards = document.querySelectorAll('.card');
            
            // Initialize variables for current filter state
            let searchTerm = '';
            let currentView = 'all';
            let selectedDomain = 'all';
            let selectedDataType = 'all';
            let selectedRegion = 'all';
            let selectedItemId = null;
            
            // === THEME TOGGLE FUNCTIONALITY ===
            // To add a new theme:
            // 1. Add theme variables to CSS :root section (e.g., --newtheme-primary: #color)
            // 2. Add theme override section in CSS (e.g., [data-theme="newtheme"] { --primary: var(--newtheme-primary); })
            // 3. Add theme to this themes object with name and icon
            // 4. Update the theme cycling logic in the click handler below
            const themes = {
                'classic': { name: 'Classic', icon: 'fas fa-moon' },
                'solarized': { name: 'Solarized', icon: 'fas fa-sun' }
            };
            
            let currentTheme = localStorage.getItem('theme') || 'classic';
            const themeToggle = document.getElementById('theme-toggle');
            const themeName = document.getElementById('theme-name');
            
            // Apply saved theme on page load
            function applyTheme(theme) {
                if (theme === 'solarized') {
                    document.documentElement.setAttribute('data-theme', 'solarized');
                } else {
                    document.documentElement.removeAttribute('data-theme');
                }
                
                // Update button text and icon
                if (themeName && themeToggle) {
                    themeName.textContent = themes[theme].name;
                    const icon = themeToggle.querySelector('i');
                    if (icon) {
                        icon.className = themes[theme].icon;
                    }
                }
                
                currentTheme = theme;
                localStorage.setItem('theme', theme);
            }
            
            // Initialize theme
            applyTheme(currentTheme);
            
            // Theme toggle event listener
            if (themeToggle) {
                themeToggle.addEventListener('click', function() {
                    // Cycle through themes
                    const themeKeys = Object.keys(themes);
                    const currentIndex = themeKeys.indexOf(currentTheme);
                    const nextIndex = (currentIndex + 1) % themeKeys.length;
                    const nextTheme = themeKeys[nextIndex];
                    applyTheme(nextTheme);
                });
            }
            
            // Function to parse URL parameters
            function getUrlParams() {
                const params = new URLSearchParams(window.location.search);
                return {
                    search: params.get('search') || '',
                    view: params.get('view') || 'all',
                    domain: params.get('domain') || 'all',
                    dataType: params.get('dataType') || 'all',
                    region: params.get('region') || 'all',
                    item: params.get('item') || null
                };
            }
            
            // Function to update URL with current filters
            function updateUrl(openPanel = false) {
                const params = new URLSearchParams();
                
                // Only add parameters that are not default values
                if (searchTerm) params.set('search', searchTerm);
                if (currentView !== 'all') params.set('view', currentView);
                if (selectedDomain !== 'all') params.set('domain', selectedDomain);
                if (selectedDataType !== 'all') params.set('dataType', selectedDataType);
                if (selectedRegion !== 'all') params.set('region', selectedRegion);
                if (selectedItemId && openPanel) params.set('item', selectedItemId);
                
                // Update URL without reloading the page
                const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
                window.history.pushState({ path: newUrl }, '', newUrl);
            }
            
            // Function to reset item ID in URL
            function resetItemInUrl() {
                selectedItemId = null;
                updateUrl(false);
            }
            
            // Function to apply filters from URL parameters
            function applyUrlParams() {
                const params = getUrlParams();
                
                // Set filter values from URL parameters
                searchTerm = params.search;
                currentView = params.view;
                selectedDomain = params.domain;
                selectedDataType = params.dataType;
                selectedRegion = params.region;
                selectedItemId = params.item;
                
                // Update UI to match URL parameters
                if (searchTerm) searchInput.value = searchTerm;
                if (currentView) viewFilter.value = currentView;
                if (selectedDomain) domainFilter.value = selectedDomain;
                if (selectedDataType) dataTypeFilter.value = selectedDataType;
                if (selectedRegion) regionFilter.value = selectedRegion;
                
                // Apply filters
                applyFilters();
                
                // Open detail panel if item is specified
                if (selectedItemId) {
                    const card = document.querySelector(`.card[data-id="${selectedItemId}"]`);
                    if (card) {
                        const title = card.getAttribute('data-title');
                        setTimeout(() => {
                            openDetailPanel(title, selectedItemId);
                        }, 300); // Small delay to ensure filters are applied first
                    }
                }
            }
            
            // Add event listeners for filters
            searchInput.addEventListener('input', function() {
                searchTerm = this.value.toLowerCase();
                applyFilters();
                updateUrl();
            });
            
            viewFilter.addEventListener('change', function() {
                currentView = this.value;
                applyFilters();
                updateUrl();
            });
            
            domainFilter.addEventListener('change', function() {
                selectedDomain = this.value;
                applyFilters();
                updateUrl();
            });
            
            dataTypeFilter.addEventListener('change', function() {
                selectedDataType = this.value;
                applyFilters();
                updateUrl();
            });
            
            regionFilter.addEventListener('change', function() {
                selectedRegion = this.value;
                applyFilters();
                updateUrl();
            });
            
            // Set up details links to open the side panel
            const detailsLinks = document.querySelectorAll('.details-link');
            detailsLinks.forEach(link => {
                // Check if the text is long enough to need a details link
                const descriptionText = link.previousElementSibling;
                const needsDetailsLink = descriptionText && (descriptionText.scrollHeight > descriptionText.clientHeight || descriptionText.textContent.length > 300);
                
                if (needsDetailsLink) {
                    link.addEventListener('click', function(e) {
                        e.stopPropagation(); // Prevent the card-description click event from firing
                        const card = this.closest('.card');
                        const title = card.getAttribute('data-title');
                        const id = card.getAttribute('data-id');
                        selectedItemId = id;
                        openDetailPanel(title, id);
                        updateUrl(true); // Update URL with item ID
                    });
                } else {
                    // Hide the details link if not needed
                    if (link) {
                        link.style.display = 'none';
                    }
                }
            });
            
            // Make card-description and card-footer areas clickable
            document.querySelectorAll('.card-description, .card-footer').forEach(element => {
                element.addEventListener('click', function(e) {
                    // Don't trigger if clicking on a link or button inside
                    if (e.target.closest('a') || e.target.closest('button')) {
                        return;
                    }
                    
                    const card = this.closest('.card');
                    const title = card.getAttribute('data-title');
                    const id = card.getAttribute('data-id');
                    selectedItemId = id;
                    openDetailPanel(title, id);
                    updateUrl(true); // Update URL with item ID
                });
            });
            
            // Add event listeners for closing the detail panel
            const closeDetailPanel = document.getElementById('closeDetailPanel');
            const panelOverlay = document.getElementById('panelOverlay');
            const detailPanel = document.getElementById('detailPanel');
            
            if (closeDetailPanel) {
                closeDetailPanel.addEventListener('click', function() {
                    detailPanel.classList.remove('open');
                    panelOverlay.classList.remove('active');
                    document.body.style.overflow = '';
                    resetItemInUrl(); // Reset item ID in URL
                });
            }
            
            if (panelOverlay) {
                panelOverlay.addEventListener('click', function() {
                    detailPanel.classList.remove('open');
                    panelOverlay.classList.remove('active');
                    document.body.style.overflow = '';
                    resetItemInUrl(); // Reset item ID in URL
                });
            }
            
            // Function to apply all filters
            function applyFilters() {
                let visibleCards = 0;
                
                cards.forEach(card => {
                    // Check if card matches the view filter
                    let viewMatch = true;
                    if (currentView === 'datasets') {
                        viewMatch = card.classList.contains('has-dataset');
                    } else if (currentView === 'usecases') {
                        viewMatch = card.classList.contains('has-usecase');
                    } else if (currentView === 'lacuna') {
                        viewMatch = card.classList.contains('has-lacuna');
                    }
                    
                    // Check if card matches the search term
                    let searchMatch = !searchTerm || card.textContent.toLowerCase().includes(searchTerm);
                    
                    // Check if card matches the domain filter
                    let domainMatch = selectedDomain === 'all';
                    if (!domainMatch) {
                        // Look for tags with the selected domain
                        const domainTags = card.querySelectorAll(`.tag[data-filter="${selectedDomain}"]`);
                        domainMatch = domainTags.length > 0;
                        
                        // Also check domain badges
                        if (!domainMatch) {
                            const domainBadges = card.querySelectorAll('.domain-badge');
                            domainBadges.forEach(badge => {
                                if (badge.textContent === selectedDomain) {
                                    domainMatch = true;
                                }
                            });
                        }
                    }
                    
                    // Check if card matches the data type filter
                    let dataTypeMatch = selectedDataType === 'all' || 
                                    card.querySelector(`.tag[data-filter="${selectedDataType}"]`) !== null;
                    
                    // Check if card matches the region filter
                    let regionMatch = selectedRegion === 'all';
                    if (!regionMatch) {
                        const cardRegion = card.getAttribute('data-region');
                        regionMatch = cardRegion && cardRegion.includes(selectedRegion);
                    }
                    
                    // Card is visible only if it matches all filters
                    if (viewMatch && searchMatch && domainMatch && dataTypeMatch && regionMatch) {
                        card.classList.remove('filtered-out');
                        visibleCards++;
                    } else {
                        card.classList.add('filtered-out');
                    }
                });
                
                // Toggle empty state message
                emptyState.classList.toggle('visible', visibleCards === 0);
            }
            
            // Apply URL parameters on page load
            applyUrlParams();
            
            // Handle browser back/forward navigation
            window.addEventListener('popstate', function() {
                applyUrlParams();
            });

            // --- Start: Count-up Animation --- 
            function animateValue(id, start, end, duration) {
                const element = document.getElementById(id);
                if (!element) return;
                let startTimestamp = null;
                const step = (timestamp) => {
                    if (!startTimestamp) startTimestamp = timestamp;
                    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                    const currentValue = Math.floor(progress * (end - start) + start);
                    element.textContent = currentValue;
                    if (progress < 1) {
                        window.requestAnimationFrame(step);
                    }
                };
                window.requestAnimationFrame(step);
            }

            // Animate the stat values
            const datasetCounter = document.getElementById('stat-datasets');
            const usecaseCounter = document.getElementById('stat-usecases');
            const countryCounter = document.getElementById('stat-countries');

            if (datasetCounter) {
                animateValue('stat-datasets', 0, parseInt(datasetCounter.getAttribute('data-target') || '0', 10), 1500);
            }
            if (usecaseCounter) {
                animateValue('stat-usecases', 0, parseInt(usecaseCounter.getAttribute('data-target') || '0', 10), 1500);
            }
            if (countryCounter) {
                animateValue('stat-countries', 0, parseInt(countryCounter.getAttribute('data-target') || '0', 10), 1500);
            }
            // --- End: Count-up Animation --- 

            // --- Start: Fair Sharing Modal --- 
            const fairSharingLink = document.getElementById('fair-sharing-link');
            const fairSharingModal = document.getElementById('fair-sharing-modal');
            const fairSharingCloseBtn = document.getElementById('fair-sharing-close');

            if (fairSharingLink && fairSharingModal) {
                fairSharingLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    fairSharingModal.classList.add('visible');
                });
            }
            if (fairSharingCloseBtn && fairSharingModal) {
                fairSharingCloseBtn.addEventListener('click', () => {
                    fairSharingModal.classList.remove('visible');
                });
            }
            if (fairSharingModal) {
                // Close modal if clicking on the background overlay
                fairSharingModal.addEventListener('click', (e) => {
                    if (e.target === fairSharingModal) { // Check if the click is directly on the container
                        fairSharingModal.classList.remove('visible');
                    }
                });
            }
            // --- End: Fair Sharing Modal --- 

            // --- Start: About Website Modal --- 
            const aboutWebsiteLink = document.getElementById('about-website-link');
            const aboutWebsiteModal = document.getElementById('about-website-modal');
            const aboutWebsiteCloseBtn = document.getElementById('about-website-close');

            if (aboutWebsiteLink && aboutWebsiteModal) {
                aboutWebsiteLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    aboutWebsiteModal.classList.add('visible');
                });
            }
            if (aboutWebsiteCloseBtn && aboutWebsiteModal) {
                aboutWebsiteCloseBtn.addEventListener('click', () => {
                    aboutWebsiteModal.classList.remove('visible');
                });
            }
            if (aboutWebsiteModal) {
                // Close modal if clicking on the background overlay
                aboutWebsiteModal.addEventListener('click', (e) => {
                    if (e.target === aboutWebsiteModal) { // Check if the click is directly on the container
                        aboutWebsiteModal.classList.remove('visible');
                    }
                });
            }
            // --- End: About Website Modal --- 
        });
    </script>
    '''

def generate_detail_panel_html():
    return '''
    <!-- Slide-in Panel for Detailed Information -->
    <div id="detailPanel" class="detail-panel">
        <div class="detail-panel-header">
            <button id="closeDetailPanel" class="close-panel-btn">
                <i class="fas fa-times"></i>
            </button>
            <h2 id="detailPanelTitle">Dataset Details</h2>
        </div>
        <div class="detail-panel-content">
            <div id="detailPanelLoader" class="panel-loader">
                <div class="loader-spinner"></div>
                <p>Loading details...</p>
            </div>
            <div id="detailPanelData" class="panel-data">
                <!-- Content will be dynamically populated -->
            </div>
        </div>
    </div>
    
    <!-- Overlay for when panel is open -->
    <div id="panelOverlay" class="panel-overlay"></div>
    '''

# Main execution
try:
    # Read Excel File
    df = pd.read_excel(DATA_CATALOG)
    print(f"Successfully loaded data from {DATA_CATALOG}")
    
    # Debug column names
    print("DataFrame columns:", list(df.columns))
    
    # Clean and process data
    # Replace NaN with empty strings for text fields
    text_columns = ['Description - What can be done with this? What is this about?', 'Data - Key Characteristics', 
                    'Model/Use-Case - Key Characteristics', 'Deep Dive - How can you concretely work with this and build on this?',
                    'Region/Country', 'Domain/SDG', 'Data Type', 'License']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna('')
    
    # Count the statistics for the header - REVISED for multiple links
    # dataset_count = sum(df['Dataset Link'].notna())
    # usecase_count = sum(df['Model/Use-Case Links'].notna())
    dataset_count = 0
    usecase_count = 0
    valid_countries = set()

    for index, row in df.iterrows():
        # Count individual dataset links
        dataset_link_text = row.get('Dataset Link', '')
        has_dataset_link = False
        if isinstance(dataset_link_text, str) and not pd.isna(dataset_link_text):
            processed_link_string = str(dataset_link_text).replace(',', ';')
            dataset_link_entries = [s.strip() for s in processed_link_string.split(';') if s.strip()]
            if dataset_link_entries:
                dataset_count += len(dataset_link_entries)
                has_dataset_link = True
        
        # Count individual use case links
        usecase_link_text = row.get('Model/Use-Case Links', '')
        has_usecase_link = False
        if isinstance(usecase_link_text, str) and not pd.isna(usecase_link_text):
            processed_model_link_string = str(usecase_link_text).replace(',', ';')
            usecase_link_entries = [s.strip() for s in processed_model_link_string.split(';') if s.strip()]
            if usecase_link_entries:
                usecase_count += len(usecase_link_entries)
                has_usecase_link = True
        
        # Count unique countries ONLY from rows with at least one valid link
        if has_dataset_link or has_usecase_link:
            country_text = row.get('Country Team')
            if isinstance(country_text, str) and not pd.isna(country_text):
                parts = re.split(r',|\s+and\s+|;', country_text)
                for part in parts:
                    country = part.strip()
                    if country:
                        valid_countries.add(country)
    
    # The final count is the number of unique countries found in valid rows
    country_count = len(valid_countries)
    
    # Get unique categories for filter and CSS generation
    # Note: get_unique_categories might need similar filtering if its results
    # should only reflect active projects, but for now, we only adjust the count.
    domains, data_types, statuses, regions, lacuna_datasets = get_unique_categories(df)
    
    # Generate CSS for labels
    label_css = generate_label_css(domains, data_types, statuses)
    
    # --- Define Static CSS --- 
    # Moved static CSS rules out of the main f-string to avoid syntax errors
    static_css = r'''
        :root {
            /* === THEME SYSTEM === */
            /* To add a new theme, follow this pattern:
               1. Define theme-specific variables (e.g., --newtheme-primary: #color)
               2. Add a [data-theme="newtheme"] selector with variable overrides
               3. Update the JavaScript themes object and cycling logic */
            
            /* Solarized Light Theme (Default) */
            --solarized-base03: #002b36;
            --solarized-base02: #073642;
            --solarized-base01: #586e75;
            --solarized-base00: #657b83;
            --solarized-base0: #839496;
            --solarized-base1: #93a1a1;
            --solarized-base2: #eee8d5;
            --solarized-base3: #fdf6e3;
            --solarized-yellow: #b58900;
            --solarized-orange: #cb4b16;
            --solarized-red: #dc322f;
            --solarized-magenta: #d33682;
            --solarized-violet: #6c71c4;
            --solarized-blue: #268bd2;
            --solarized-cyan: #2aa198;
            --solarized-green: #859900;
            --solarized-light-bg: #fefcf5;
            --solarized-card-bg: #f5f2ea;

            /* Classic Blue Theme */
            --classic-primary: #3b5998;
            --classic-primary-light: #4c70ba;
            --classic-secondary: #5b7fb9;
            --classic-light: #f9fafb;
            --classic-dark: #1a202c;
            --classic-gray: #64748b;
            --classic-border: #e2e8f0;
            --classic-background: #f8fafc;
            --classic-card-bg: #f5f8fc;
            --classic-text: #1e293b;
            --classic-text-light: #64748b;
            --classic-shadow: rgba(0, 0, 0, 0.04);
            --classic-shadow-hover: rgba(0, 0, 0, 0.08);
            --classic-title-color: #2c4a7c;
            --classic-btn-text: #ffffff;

            /* Active Theme Variables (Default: Classic) */
            --primary: var(--classic-primary);
            --primary-light: var(--classic-primary-light);
            --background: var(--classic-background);
            --card-background: #ffffff;
            --text: var(--classic-text);
            --text-light: var(--classic-text-light);
            --border: var(--classic-border);
            --shadow: var(--classic-shadow);
            --shadow-hover: var(--classic-shadow-hover);
            --title-color: var(--classic-title-color);
            --btn-text: var(--classic-btn-text);
            --yellow: #d97706;
        }

        /* Solarized Theme Override */
        [data-theme="solarized"] {
            --primary: var(--solarized-blue);
            --primary-light: var(--solarized-cyan);
            --background: var(--solarized-card-bg);
            --card-background: var(--solarized-light-bg);
            --text: var(--solarized-base00);
            --text-light: var(--solarized-base01);
            --border: rgba(147, 161, 161, 0.3);
            --shadow: rgba(0, 0, 0, 0.02);
            --shadow-hover: rgba(0, 0, 0, 0.04);
            --title-color: var(--solarized-base02);
            --btn-text: var(--solarized-light-bg);
            --yellow: var(--solarized-yellow);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        
        html {
            /* Set a smaller base font size to scale everything down */
            font-size: 14px;
        }
        
        body {
            background-color: var(--background);
            color: var(--text);
            line-height: 1.7;
            font-size: 1rem; /* Use relative units based on html font-size */
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        header {
            background-color: var(--background); /* Simplified to single background color */
            padding: 0 0 3.5rem; /* Increased bottom padding from 2rem to 3.5rem */
            position: relative;
            overflow: hidden;
            border-bottom: 1px solid var(--border);
            box-shadow: 0 2px 10px var(--shadow);
        }

        /* Top navigation area that will contain both the logos and the about link */
        .top-nav-container {
            background-color: var(--card-background); /* Use card background for subtle contrast */
            padding: 0;
            width: 100%;
            box-shadow: 0 1px 4px var(--shadow);
            margin-bottom: 2rem; /* Reverted back to 2rem from 3rem */
        }

        .top-nav-area {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 3rem; /* Reverted back to 0.75rem from 1.25rem */
            max-width: 1100px;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 0; /* Removed bottom margin */
            position: relative;
            z-index: 2;
        }
        
        .top-nav-links { /* Add this new rule */
            display: flex;
            align-items: center;
            gap: 0.75rem; /* Adjust this value for desired spacing */
        }
        
        .about-link {
            color: var(--text);
            font-size: 0.9rem;
            text-decoration: none;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            transition: background-color 0.2s;
        }

        .about-link:hover {
            background-color: rgba(0, 0, 0, 0.05);
        }
        
        /* Theme Toggle Button */
        .theme-toggle {
            background: var(--card-background);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            color: var(--text);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            white-space: nowrap;
            box-shadow: 0 1px 3px var(--shadow);
        }
        
        .theme-toggle:hover {
            background: var(--background);
            border-color: var(--primary-light);
            transform: translateY(-1px);
            box-shadow: 0 2px 6px var(--shadow-hover);
        }
        
        .theme-toggle i {
            font-size: 0.75rem;
            opacity: 0.8;
        }
        
        .header-content {
            display: flex;
            flex-direction: column;
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 3rem;
            position: relative;
            z-index: 1;
        }

        .header-main {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 3rem; /* Increased from 2rem to 3rem for more space between text and stats */
        }
        
        .header-logos {
            display: flex;
            gap: 1.75rem; /* Reverted back to 1.75rem from 2.25rem */
            align-items: center;
        }
        
        .header-logo {
            height: 45px; /* Reverted back to 45px from 52px */
            width: auto;
            transition: opacity 0.2s;
            filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.05));
            vertical-align: middle; /* Better vertical alignment */
        }
        
        .header-logo:hover {
            opacity: 0.9;
        }
        
        .header-text {
            padding-right: 1rem;
            max-width: 62%;
        }
        
        .header-text h1 {
            margin-bottom: 0.75rem;
            font-size: 2.5rem;
            font-weight: 400;
            color: var(--title-color);
            line-height: 1.2;
            position: relative;
            letter-spacing: -0.015em;
        }
        
        .subtitle {
            font-size: 1.15rem;
            color: var(--text-light);
            max-width: 800px;
            font-weight: 300;
            line-height: 1.5;
            margin-top: 1rem;
            letter-spacing: 0.01em;
            margin-bottom: 1.25rem;
        }
        
        .header-learn-more {
            display: inline-flex;
            align-items: center;
            font-size: 0.9rem;
            color: var(--primary);
            text-decoration: none;
            margin-top: 0.25rem;
            transition: all 0.2s ease;
        }
        
        .header-learn-more:hover {
            opacity: 0.85;
            text-decoration: underline;
        }
        
        .header-learn-more i {
            display: none;
        }
        
        .filters {
            background-color: var(--card-background); /* Use card background for subtle contrast */
            padding: 1.25rem 0; /* Reduced from 1.5rem */
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 10;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            box-shadow: 0 4px 10px var(--shadow-hover);
            margin-top: -0.75rem;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        }
        
        .filters-content {
            max-width: 1100px; /* Reduced from 1200px to match container */
            margin: 0 auto;
            padding: 0 3rem; /* Increased from 2rem to match container */
            display: flex;
            flex-wrap: wrap;
            gap: 1.25rem; /* Reduced from 1.5rem */
            justify-content: center;
            align-items: center;
        }
        
        .filter-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .filter-label {
            font-weight: 500;
            font-size: 0.875rem;
            color: var(--text-light);
        }
        
        select, input {
            padding: 0.5rem 0.875rem; /* Reduced from 0.625rem 1rem */
            border-radius: 0.5rem;
            border: 1px solid var(--border);
            min-width: 160px; /* Reduced from 180px */
            background-color: var(--card-background); /* Match filter bar background */
            font-size: 0.875rem;
            color: var(--text);
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px var(--shadow);
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: var(--primary-light);
            box-shadow: 0 0 0 3px rgba(38, 139, 210, 0.1); /* Using blue for focus, alpha adjusted */
        }
        
        .search-box {
            display: flex;
            align-items: center;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 0.5rem 0.875rem; /* Reduced from 0.625rem 1rem */
            min-width: 280px; /* Reduced from 300px */
            background-color: var(--card-background); /* Match filter bar background */
            box-shadow: 0 1px 2px var(--shadow);
            transition: all 0.2s ease;
        }
        
        .search-box:focus-within {
            border-color: var(--primary-light);
            box-shadow: 0 0 0 3px rgba(38, 139, 210, 0.1); /* Using blue for focus, alpha adjusted */
        }
        
        .search-box input {
            border: none;
            flex-grow: 1;
            min-width: 0;
            padding: 0;
            box-shadow: none;
        }
        
        .search-box input:focus {
            box-shadow: none;
        }
        
        .search-box i {
            color: var(--gray);
            margin-right: 0.75rem;
        }
        
        .container {
            max-width: 1100px; /* Reduced from 1200px for a more narrow layout */
            margin: 2.5rem auto;
            padding: 0 3rem; /* Increased from 2rem for more side spacing */
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); /* Reduced from 280px */
            gap: 1.5rem; /* Increased from 1.25rem for more spacing between cards */
        }
        
        .card {
            background: var(--card-background); /* Use card background for subtle contrast */
            border-radius: 0.75rem;
            overflow: hidden;
            box-shadow: 0 4px 10px var(--shadow-hover); /* Use theme shadow */
            transition: transform 0.3s, box-shadow 0.3s, border-color 0.3s;
            display: flex;
            flex-direction: column;
            height: 100%;
            position: relative;
            /* Set a default transparent border to prevent layout shifts */
            border: 1px solid transparent;
        }
        
        .card:hover {
            transform: translateY(-5px); /* More lift */
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08); /* Lighter shadow on hover */
            /* Apply blue border color on hover */
            border-color: var(--primary-light);
        }
        
        .card-description, .card-footer {
            cursor: pointer;
        }
        
        .card-image {
            height: 130px; /* Increased from 120px for less square proportions */
            background-color: var(--background); /* Use main background as placeholder */
            background-image: linear-gradient(135deg, var(--card-background) 0%, var(--background) 100%); /* Simple two-tone gradient */
            background-size: cover;
            background-position: center;
            position: relative;
            overflow: hidden;
        }
        
        .card-image.has-image {
            background-image: none; /* Correct: remove placeholder if actual image is set inline */
        }
        
        .card-image.has-image::after { /* This is the overlay gradient on top of the image */
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                to bottom,
                rgba(254, 252, 245, 0) 0%,   /* --light-bg (card background) with alpha */
                rgba(254, 252, 245, 0) 50%,  /* --light-bg (card background) with alpha */
                rgba(254, 252, 245, 0.3) 75%,/* --light-bg (card background) with alpha */
                rgba(254, 252, 245, 0.8) 90%,/* --light-bg (card background) with alpha */
                rgba(254, 252, 245, 1) 100%  /* --light-bg (card background) full */
            );
            z-index: 1;
        }
        
        .card-image.has-image::before { /* This is for the fallback background if image fails, beneath actual image */
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--card-background) 0%, var(--background) 100%); /* Simple two-tone fallback */
            z-index: -1;
        }
        
        .card-header {
            padding: 1.25rem 1.25rem 0.5rem; /* Increased horizontal padding */
        }
        
        .card-body {
            padding: 0 1.25rem 0.75rem; /* Increased horizontal padding */
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        
        .domain-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            position: absolute;
            top: 1rem;
            right: 1rem;
            z-index: 1;
        }
        
        .domain-badge {
            display: inline-block;
            background-color: var(--primary); /* Using primary accent */
            color: var(--btn-text); /* Text on primary accent */
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.7rem;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(38, 139, 210, 0.15); /* Using blue for shadow, alpha adjusted */
        }
        
        .data-type-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            margin-top: 0.25rem;
        }
        
        .data-type-chip {
            font-size: 0.7rem;
            font-weight: 400;
            padding: 0.2rem 0.5rem;
            border-radius: 1rem;
            background-color: var(--background); /* Use main background */
            color: var(--text-light);
            display: inline-flex;
            align-items: center;
            border: 1px solid var(--border); /* Use theme border */
        }
        
        .data-type-chip i {
            margin-right: 0.25rem;
            font-size: 0.65rem;
            opacity: 0.7;
        }
        
        .card h3 {
            font-size: 1rem; /* Reduced from 1.125rem */
            margin-bottom: 0.5rem;
            color: var(--title-color);
            line-height: 1.3;
            font-weight: 600;
        }
        
        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .meta-item {
            font-size: 0.75rem;
            color: var(--gray);
            display: flex;
            align-items: center;
        }
        
        .meta-item i {
            margin-right: 0.25rem;
        }
        
        .card-description {
            margin-bottom: 0.75rem;
            flex-grow: 1;
        }
        
        .description-text {
            color: var(--text-light);
            font-size: 0.9375rem;
            line-height: 1.6;
            overflow: hidden;
            position: relative;
        }
        
        .description-text.collapsed {
            max-height: 4.8em; /* Show 3 lines of text */
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        }
        
        .details-link {
            color: var(--primary);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            margin-top: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.375rem;
            transition: all 0.2s ease;
        }
        
        .details-link i {
            font-size: 0.75rem;
            transition: transform 0.2s ease;
        }
        
        .details-link:hover {
            color: var(--primary-light);
        }
        
        .details-link:hover i {
            transform: translateX(3px);
        }
        
        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.8125rem;
            color: var(--text-light);
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 0.375rem;
        }
        
        .meta-item a {
            color: var(--primary);
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .meta-item a:hover {
            color: var(--secondary);
            text-decoration: underline;
        }
        
        .tags {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1.5rem;
        }
        
        .tag {
            background-color: rgba(38, 139, 210, 0.08); /* blue with alpha */
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            color: var(--primary);
            transition: all 0.2s;
            font-weight: 500;
        }
        
        .tag:hover {
            background-color: rgba(38, 139, 210, 0.12); /* blue with alpha, slightly darker */
            transform: translateY(-2px);
        }
        
        .card-footer {
            border-top: 1px solid var(--border);
            padding: 0.625rem 1.25rem; /* Increased horizontal padding */
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.5rem;
            background-color: var(--background); /* Use main background for footer */
            flex-wrap: wrap;
        }
        
        .footer-chips {
            margin-right: auto;
            margin-bottom: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
        }
        
        .footer-chips .data-type-chip {
            font-size: 0.7rem;
            padding: 0.2rem 0.5rem;
            margin-bottom: 0;
        }
        
        .license-tag {
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 0.375rem;
            background-color: rgba(181, 137, 0, 0.1); /* yellow with alpha */
            color: var(--yellow); /* yellow */
            display: flex;
            align-items: center;
            gap: 0.25rem;
            margin-left: auto;
            border: 1px solid rgba(181, 137, 0, 0.2); /* yellow with alpha */
            transition: all 0.2s ease;
        }
        
        .license-tag:hover {
            background-color: rgba(181, 137, 0, 0.15); /* yellow with alpha, slightly darker */
            transform: translateY(-2px);
        }
        
        .license-tag i {
            font-size: 0.7rem;
            opacity: 0.8;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.25rem;
            padding: 0.375rem 0.625rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.2s;
            cursor: pointer;
            border: none;
            white-space: nowrap;
            min-width: 0;
            flex-shrink: 0;
        }
        
        .btn i {
            font-size: 0.75rem;
        }
        
        .btn-view-details {
            background-color: var(--card-background);  /* Use card background */
            color: var(--text-light);
            border: 1px solid var(--border);  /* Use theme border */
            margin-left: auto;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        @media (max-width: 768px) {
            .filters-content {
                flex-direction: column;
                align-items: flex-start;
                padding: 0 1.5rem;
                gap: 1rem;
            }
            
            .header-content {
                padding: 0 1.5rem;
            }
            
            .top-nav-area {
                flex-direction: column;
                align-items: flex-start;
                padding: 0.5rem 1.5rem; /* Reverted back to 0.5rem from 0.75rem */
                gap: 0.75rem;
            }
            
            .top-nav-links {
                align-self: flex-end;
                margin-top: -2rem; /* Position next to logos */
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            
            .top-nav-container {
                margin-bottom: 1.5rem; /* Reverted back to 1.5rem from 2rem */
            }
            
            .theme-toggle {
                padding: 0.3rem 0.6rem;
                font-size: 0.75rem;
                gap: 0.3rem;
            }
            

            
            .header-logos {
                flex-wrap: wrap;
                gap: 1.25rem;
                justify-content: flex-start;
            }
            
            .header-logo {
                height: 38px; /* Adjusted for mobile but still larger than before */
            }
            
            .header-main {
                flex-direction: column;
            }
            
            .header-text {
                padding-right: 0;
                max-width: 100%;
            }
            
            h1 {
                font-size: 2.2rem;
                margin-bottom: 0.75rem;
            }
            
            .subtitle {
                font-size: 1.05rem;
                margin-top: 0.9rem;
                margin-bottom: 1.1rem;
            }
            
            .header-stats {
                margin-top: 1.75rem;
                width: 100%;
                min-width: initial;
            }
            
            .stats-row {
                flex-direction: row;
                justify-content: center;
                gap: 0.9rem;
            }
            
            .stat-item {
                flex-direction: column;
                text-align: center;
            }
            
            .stat-value {
                font-size: 1.5rem;
                line-height: 1.1;
            }
            
            .stat-label {
                font-size: 0.85rem;
                margin-top: 0.1rem;
            }
            
            header {
                padding: 0.75rem 0 1.75rem;
            }
            
            .filters {
                margin-top: -0.75rem;
            }
        }
        
        /* {label_css} Will be appended here */
        
        footer {
            background-color: var(--background);
            color: var(--text-light);
            padding: 4rem 0;
            text-align: center;
            border-top: 1px solid var(--border);
        }
        
        .footer-content {
            max-width: 1100px; /* Reduced from 1200px to match container */
            margin: 0 auto;
            padding: 0 3rem; /* Increased from 2rem to match container */
        }
        
        footer p {
            font-size: 0.9375rem;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .btn-primary {
            background-color: var(--primary);
            color: var(--btn-text);
            box-shadow: 0 2px 4px rgba(38, 139, 210, 0.15); /* blue with alpha */
        }
        
        .btn-primary:hover {
            background-color: var(--primary-light);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(38, 139, 210, 0.2); /* blue with alpha */
        }
        
        .btn-secondary {
            background-color: rgba(38, 139, 210, 0.08); /* blue with alpha */
            color: var(--primary);
        }
        
        .btn-secondary:hover {
            background-color: rgba(38, 139, 210, 0.12); /* blue with alpha, slightly darker */
            transform: translateY(-2px);
        }
        
        .btn-view-details:hover {
            background-color: var(--background);  /* Use main background on hover */
            color: var(--primary);  /* Use primary color for text */
            transform: translateY(-2px);
        }
        
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            background-color: var(--card-background); /* Use card background */
            border-radius: 1rem;
            border: 1px solid var(--border);
            display: none;
            margin: 2rem auto;
            max-width: 600px;
        }
        
        .empty-state.visible {
            display: block;
        }
        
        .empty-state h3 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--text);
            font-weight: 600;
        }
        
        .empty-state p {
            color: var(--text-light);
            font-size: 1.0625rem;
            line-height: 1.6;
        }
        
        .card.filtered-out {
            display: none;
        }
        

        
        /* Side panel styles are now in enhanced_side_panel.css */
        
        /* Stats panel styling */
        .header-stats {
            display: flex;
            flex-direction: column;
            min-width: 180px;
            justify-content: center;
            align-self: center;
        }
        
        .stats-row {
            display: flex;
            justify-content: space-between;
            gap: 1.2rem;
            margin-bottom: 1rem;
        }
        
        .stats-bottom {
            display: flex;
            justify-content: center;
        }
        
        .stat-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        
        .stat-text {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .stat-value {
            font-size: 1.75rem;
            font-weight: 500;
            color: var(--title-color);
            line-height: 1.1;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: var(--text-light);
            margin-top: 0.15rem;
        }

        /* Modal Styles */
        .modal-container {
            display: none; /* Hidden by default */
            position: fixed;
            z-index: 1050;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent black background */
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .modal-container.visible {
            display: flex;
            opacity: 1;
        }
        .modal-content {
            position: relative;
            background-color: var(--background); /* Use main background */
            padding: 2.5rem;
            border-radius: 0.75rem;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            animation: fadeInModal 0.3s ease-out;
        }
        .modal-close {
            position: absolute;
            top: 0.75rem;
            right: 1rem;
            font-size: 1.75rem;
            font-weight: bold;
            color: #aaa;
            background: none;
            border: none;
            cursor: pointer;
            line-height: 1;
        }
        .modal-close:hover,
        .modal-close:focus {
            color: #333;
            text-decoration: none;
        }
        .modal-content h2 {
            margin-top: 0;
            margin-bottom: 1.5rem;
            color: var(--title-color);
            font-weight: 600;
            font-size: 1.25rem;
        }
        .modal-content p {
            margin-bottom: 0;
            color: var(--text);
            line-height: 1.6;
        }
        @keyframes fadeInModal {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Style for links within license tags */
        .license-tag a {
            color: inherit; /* Inherit text color from parent */
            text-decoration: none; /* Remove underline */
        }
        .license-tag a:hover {
            text-decoration: underline; /* Add underline on hover */
        }
    ''' # End of static_css definition

    # --- Combine Static and Dynamic CSS ---
    final_css = static_css + "\n\n/* === Generated Label CSS === */\n" + label_css

    # Create a completely new HTML file from scratch
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fair Forward - Open Data & Use Cases</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <!-- Add enhanced side panel CSS -->
    <link rel="stylesheet" href="enhanced_side_panel.css">
    <!-- Add syntax highlighting for code blocks -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <script>
        // Initialize syntax highlighting when the page loads
        document.addEventListener('DOMContentLoaded', function() {{
            hljs.highlightAll();
            
            // Re-run highlighting when content is dynamically added
            const observer = new MutationObserver(function(mutations) {{
                mutations.forEach(function(mutation) {{
                    if (mutation.addedNodes.length) {{
                        hljs.highlightAll();
                    }}
                }});
            }});
            
            // Start observing the document body for changes
            observer.observe(document.body, {{ childList: true, subtree: true }});
        }});
    </script>
    <style>
        {final_css} /* Inject the combined CSS here */
    </style>
</head>
<body>
    <header>
        <div class="top-nav-container">
            <div class="top-nav-area">
                <div class="header-logos">
                    <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank" title="Fair Forward Initiative">
                        <img src="img/ff_official.png" alt="Fair Forward Logo" class="header-logo">
                    </a>
                    <a href="https://www.bmz-digital.global/en/" target="_blank" title="Digital Global">
                        <img src="img/digital_global_official.png" alt="Digital Global Logo" class="header-logo">
                    </a>
                    <a href="https://www.bmz.de/en" target="_blank" title="Federal Ministry for Economic Cooperation and Development">
                        <img src="img/ministry_official.png" alt="BMZ Logo" class="header-logo">
                    </a>
                    <a href="https://www.giz.de/en/html/index.html" target="_blank" title="Deutsche Gesellschaft für Internationale Zusammenarbeit">
                        <img src="img/giz_official.png" alt="GIZ Logo" class="header-logo">
                    </a>
                </div>
                <div class="top-nav-links"> <!-- Add this wrapper div -->
                    <button id="theme-toggle" class="theme-toggle" title="Switch theme">
                        <i class="fas fa-moon"></i>
                        <span id="theme-name">Classic</span>
                    </button>
                    <a href="#" id="fair-sharing-link" class="about-link">Info on Fair Sharing</a>
                    <a href="#" id="about-website-link" class="about-link">About the website</a> <!-- Added ID -->
                </div> <!-- Close the wrapper div -->
            </div>
        </div>
        <div class="header-content">
            <div class="header-main">
                <div class="header-text">
                    <h1>Fair Forward - Open Data & Use Cases</h1>
                    <p class="subtitle">Exploring datasets and solutions for global challenges across agriculture, language technology, climate action, energy, and more.</p>
                    <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank" class="header-learn-more">
                        [Learn more about Fair Forward]
                    </a>
                </div>
                <div class="header-stats">
                    <div class="stats-row">
                        <div class="stat-item">
                            <div class="stat-text">
                                <div class="stat-value" id="stat-datasets" data-target="{dataset_count}">0</div>
                                <div class="stat-label">Datasets</div>
                            </div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-text">
                                <div class="stat-value" id="stat-usecases" data-target="{usecase_count}">0</div>
                                <div class="stat-label">Use Cases</div>
                            </div>
                        </div>
                    </div>
                    <div class="stats-bottom">
                        <div class="stat-item">
                            <div class="stat-text">
                                <div class="stat-value" id="stat-countries" data-target="{country_count}">0</div>
                                <div class="stat-label">Countries</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </header>
    
    {generate_filter_html(domains, data_types, regions, lacuna_datasets)}
    
    <div class="container">
        <div class="grid" id="dataGrid">
'''
    
    # Generate cards for each row in the dataframe
    for idx, row in df.iterrows():
        # Skip rows without dataset or use case links
        dataset_link = row.get('Dataset Link', '')
        model_links = row.get('Model/Use-Case Links', '')
        has_dataset = isinstance(dataset_link, str) and not pd.isna(dataset_link)
        has_usecase = isinstance(model_links, str) and not pd.isna(model_links)
        
        if not has_dataset and not has_usecase:
            continue
        
        html_template += generate_card_html(row, idx)
    
    # Add the empty state and detail panel
    html_template += f'''
        </div>
        
        <div id="emptyState" class="empty-state">
            <h3>No matching items found</h3>
            <p>Try adjusting your filters or search term to find what you're looking for.</p>
        </div>
        
        {generate_detail_panel_html()}
    </div>
    
    <footer>
        <div class="footer-content">
            <p>&copy; {datetime.datetime.now().year} Fair Forward - Artificial Intelligence for All | A project by GIZ</p>
            <p style="margin-top: 1rem; font-size: 0.875rem;"><a href="https://github.com/Fair-Forward/datasets" target="_blank" style="color: var(--primary); text-decoration: none;">Contribute to the Source Code on GitHub <i class="fab fa-github"></i></a></p>
            <p style="margin-top: 0.5rem; font-size: 0.875rem;">For technical questions/feedback <a href="https://github.com/Fair-Forward/datasets/issues" target="_blank" style="color: var(--primary);">open an issue on Github</a> or contact <a href="mailto:jonas.nothnagel@gmail.com" style="color: var(--primary);">Jonas Nothnagel</a>.</p>
            <p style="margin-top: 0.5rem; font-size: 0.875rem;"><a href="analytics.html" style="color: var(--primary);">View Analytics Dashboard</a></p>
        </div>
    </footer>
    
    {generate_js_code()}
    
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Add enhanced side panel JavaScript -->
    <script src="enhanced_side_panel.js"></script>
    <!-- Add analytics tracking -->
    <script src="umami-analytics.js"></script>

    <!-- Fair Sharing Modal HTML -->
    <div id="fair-sharing-modal" class="modal-container">
        <div class="modal-content">
            <button id="fair-sharing-close" class="modal-close">&times;</button>
            <h2>Fair Sharing & Digital Public Goods</h2>
            <p>
                Adhere to fair contributing: "This is a global digital public good under open-source licenses as named under "licenses" - Please consider fair sharing and giving back to communities in an appropriate way."
            </p>
        </div>
    </div>

    <!-- About Website Modal HTML -->
    <div id="about-website-modal" class="modal-container">
        <div class="modal-content">
            <button id="about-website-close" class="modal-close">&times;</button>
            <h2>About This Website</h2>
            <p>
                Welcome to our organization's data and use-case catalog. Below is a list of datasets and use-cases that have been collected throughout our programme Fair Forward. This website aims to function as an open-sourced community place to link to our partners work and provide clear information on how the datasets and use-cases can be replicated and worked with. All listed datasets and use-cases are openly available as digital public goods.
            </p>
            <p>
                Please adhere to fair contributing: "This is a global digital public good under open-source licenses as named under "licenses" - Please consider fair sharing and giving back to communities in an appropriate way."
            </p>
        </div>
    </div>

</body>
</html>
'''
    
    # Write the HTML to the output file
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Successfully generated {HTML_OUTPUT}")

    # After you've processed your data and before writing the HTML output
    # Create frontend directory if it doesn't exist
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(HTML_OUTPUT)), 'frontend')
    os.makedirs(frontend_dir, exist_ok=True)

    # Export data as JSON for React frontend
    json_output = os.path.join(frontend_dir, 'data.json')
    df.to_json(json_output, orient='records')
    print(f"Successfully generated {json_output}")

except Exception as e:
    print(f"Error generating catalog: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1) 
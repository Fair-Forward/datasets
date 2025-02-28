import pandas as pd
import html
import os
import re
import colorsys
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate HTML catalog from Excel file.')
parser.add_argument('--input', type=str, default="docs/data_catalog.xlsx", help='Path to the input Excel file')
parser.add_argument('--output', type=str, default="docs/index.html", help='Path to the output HTML file')
parser.add_argument('--template', type=str, default="docs/new_index.html", help='Path to the HTML template file')
parser.add_argument('--google-sheet', action='store_true', help='Use Google Sheet as data source')
args = parser.parse_args()

# Load the dataset
DATA_CATALOG = args.input
HTML_OUTPUT = args.output
HTML_TEMPLATE = args.template

# Read Excel File or Google Sheet
if args.google_sheet:
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # Setup credentials
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'data_sources/google_sheets_api/service_account_JN.json', scope)
        client = gspread.authorize(credentials)
        
        # Extract correct spreadsheet ID and gid from full URL
        full_url = "https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456"
        spreadsheet_id = full_url.split('/d/')[1].split('/')[0]
        gid = 756053104
        
        # Connect to sheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.get_worksheet_by_id(int(gid))
        print(f"Successfully connected to sheet: {sheet.title}")
        
        # Get all values
        all_values = sheet.get_all_values()
        headers = all_values[0]
        
        # Create unique headers if necessary
        unique_headers = []
        header_count = {}
        
        for header in headers:
            if header in header_count:
                header_count[header] += 1
                unique_headers.append(f"{header}_{header_count[header]}")
            else:
                header_count[header] = 1
                unique_headers.append(header)
        
        # Create DataFrame
        data = all_values[1:]
        df = pd.DataFrame(data, columns=unique_headers)
        
    except Exception as e:
        print(f"Error connecting to Google Sheet: {e}")
        print("Falling back to Excel file...")
        df = pd.read_excel(DATA_CATALOG)
else:
    df = pd.read_excel(DATA_CATALOG)

# Print column names for debugging
print("Column names in the Excel file:", df.columns.tolist())

# Function to convert markdown links to HTML
def convert_markdown_links_to_html(text):
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Convert markdown links [text](url) to HTML <a href="url">text</a>
    pattern = r'\[(.*?)\]\((.*?)\)'
    html_text = re.sub(pattern, r'<a href="\2" target="_blank">\1</a>', text)
    
    # If no markdown links but contains a URL, make it clickable
    if html_text == text and ('http://' in text or 'https://' in text):
        url_pattern = r'(https?://[^\s]+)'
        html_text = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
    
    return html_text

# Function to normalize label text for CSS class names
def normalize_label(text):
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Convert to lowercase, replace spaces with hyphens, remove special characters
    normalized = re.sub(r'[^a-z0-9\-]', '', text.lower().replace(' ', '-'))
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

# Function to get unique categories for generating CSS
def get_unique_categories(df):
    domains = set()
    data_types = set()
    statuses = set()
    
    # Extract domains
    domain_col = 'Domain/SDG'
    if domain_col in df.columns:
        for domain_text in df[domain_col].dropna():
            if isinstance(domain_text, str):
                for domain in re.split(r'[,;]', domain_text):
                    domain = domain.strip()
                    if domain:
                        domains.add(domain)
    
    # Extract data types
    data_type_col = 'Data Type'
    if data_type_col in df.columns:
        for type_text in df[data_type_col].dropna():
            if isinstance(type_text, str):
                for data_type in re.split(r'[,;]', type_text):
                    data_type = data_type.strip()
                    if data_type:
                        data_types.add(data_type)
    
    # Extract statuses
    status_col = 'Use Case Pipeline Status'
    if status_col in df.columns:
        for status_text in df[status_col].dropna():
            if isinstance(status_text, str):
                for status in re.split(r'[,;]', status_text):
                    status = status.strip()
                    if status:
                        statuses.add(status)
    
    return list(domains), list(data_types), list(statuses)

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
            css += f"""
.label-{normalized} {{
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
    # Convert HSL to RGB with high lightness for pastel
    r, g, b = colorsys.hls_to_rgb(hue, 0.9, 0.3)
    # Convert to hex
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

# Function to generate evenly spaced colors
def generate_color_palette(n):
    return [i/n for i in range(n)]

# Get unique categories
domains, data_types, statuses = get_unique_categories(df)

# Generate card HTML for each dataset
cards = []
for idx, row in df.iterrows():
    # Determine if row has dataset and/or use case
    has_dataset = isinstance(row.get('Dataset Link'), str) and not pd.isna(row.get('Dataset Link'))
    has_usecase = isinstance(row.get('Model/Use-Case Links'), str) and not pd.isna(row.get('Model/Use-Case Links'))
    
    # Skip rows with no dataset or use case
    if not has_dataset and not has_usecase:
        continue
    
    # Set card classes based on what it contains
    card_classes = ["card"]
    if has_dataset:
        card_classes.append("has-dataset")
    if has_usecase:
        card_classes.append("has-usecase")
    
    card_class = " ".join(card_classes)
    
    # Get data for the card
    project_title = html.escape(str(row['OnSite Name'])) if not pd.isna(row['OnSite Name']) else ""
    data_type_tags = create_label_html(row.get('Data Type', ''), 'data-type')
    domain_tags = create_label_html(row.get('Domain/SDG', ''), 'domain')
    region = html.escape(str(row.get('Country Team', ''))) if not pd.isna(row.get('Country Team', '')) else ""
    author = convert_markdown_links_to_html(row.get('Point of Contact/Communities', ''))
    dataset_link = row.get('Dataset Link', '') if not pd.isna(row.get('Dataset Link', '')) else ""
    usecase_link = row.get('Model/Use-Case Links', '') if not pd.isna(row.get('Model/Use-Case Links', '')) else ""
    description = html.escape(str(row.get('Description - What can be done with this? What is this about?', ''))) if not pd.isna(row.get('Description - What can be done with this? What is this about?', '')) else ""
    
    # Get the first domain for the badge
    domain_badge = ""
    if 'Domain/SDG' in row and not pd.isna(row['Domain/SDG']):
        domains_list = [d.strip() for d in str(row['Domain/SDG']).split(',')]
        if domains_list and domains_list[0]:
            domain_badge = f'<div class="domain-badge">{domains_list[0]}</div>'
    
    # Create buttons for dataset and use case links
    buttons = []
    if dataset_link:
        buttons.append(f'<a href="{dataset_link}" target="_blank" class="btn btn-primary"><i class="fas fa-database"></i> Dataset</a>')
    if usecase_link:
        buttons.append(f'<a href="{usecase_link}" target="_blank" class="btn btn-secondary"><i class="fas fa-project-diagram"></i> Use Case</a>')
    
    # Set card image based on project
    card_image_class = "card-image"
    card_image_style = ""
    
    # For the first card (CADI AI Project), use the cashew image
    if idx == 0 and "CADI AI Project" in project_title:
        card_image_class += " has-image"
        card_image_style = ' style="background-image: url(\'img/cashew_karaagro.png\');"'
    
    # Create the card HTML
    card_html = f"""
    <div class="{card_class}" data-title="{project_title}" data-region="{region}">
        <div class="{card_image_class}"{card_image_style}></div>
        <div class="card-header">
            {domain_badge}
            <h3>{project_title}</h3>
            <div class="meta">
                {f'<div class="meta-item"><i class="fas fa-map-marker-alt"></i> {region}</div>' if region else ''}
                {f'<div class="meta-item"><i class="fas fa-user"></i> {author}</div>' if author else ''}
            </div>
        </div>
        <div class="card-body">
            <p>{description}</p>
            <div class="tags">
                {data_type_tags}
                {domain_tags}
            </div>
        </div>
        {f'<div class="card-footer">{" ".join(buttons)}</div>' if buttons else ''}
    </div>
    """
    cards.append(card_html)

# Combine all cards in a grid layout
grid_html = f"""
<div class="grid" id="dataGrid">
    {"".join(cards)}
</div>
"""

# Generate dynamic CSS for labels
dynamic_css = generate_label_css(domains, data_types, statuses)

# Generate domain options for the filter
domain_options = "\n".join([f'<option value="{domain}">{domain}</option>' for domain in sorted(domains)])

# Generate data type options for the filter
data_type_options = "\n".join([f'<option value="{data_type}">{data_type}</option>' for data_type in sorted(data_types)])

# Generate region options for the filter
regions = sorted(set([r for r in df['Country Team'].dropna() if isinstance(r, str)]))
region_options = "\n".join([f'<option value="{region}">{region}</option>' for region in regions])

# Read the HTML template
try:
    with open(HTML_TEMPLATE, "r") as file:
        template_html = file.read()
except Exception as e:
    print(f"Error reading template file: {e}")
    template_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Data Catalog</title>
        <style>
            /* Dynamic CSS will be inserted here */
            {dynamic_css}
        </style>
    </head>
    <body>
        <div class="grid">
            {grid_html}
        </div>
    </body>
    </html>
    """

# Replace the table content with the grid content
output_html = template_html.replace("<!-- Table content will be populated dynamically -->", grid_html)

# Add dynamic CSS
output_html = output_html.replace("/* Dynamic CSS for labels will be inserted here */", dynamic_css)

# Add domain options to the domain filter
output_html = output_html.replace("<!-- Domain options will be populated dynamically -->", domain_options)

# Add data type options to the data type filter
output_html = output_html.replace("<!-- Data Type options will be populated dynamically -->", data_type_options)

# Add region options to the region filter
output_html = output_html.replace("<!-- Region options will be populated dynamically -->", region_options)

# Write the output HTML
try:
    with open(HTML_OUTPUT, "w") as file:
        file.write(output_html)
    print(f"HTML file generated successfully: {HTML_OUTPUT}")
except Exception as e:
    print(f"Error writing HTML file: {e}") 
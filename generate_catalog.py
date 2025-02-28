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
parser.add_argument('--google-sheet', action='store_true', help='Use Google Sheet as data source')
args = parser.parse_args()

# Load the dataset
DATA_CATALOG = args.input
HTML_OUTPUT = args.output

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
                header_count[header] = 0
                unique_headers.append(header)
        
        # Get all data with unique headers
        data = sheet.get_all_records(expected_headers=unique_headers)
        df = pd.DataFrame(data)
        print(f"Data shape: {df.shape}")
        
    except Exception as e:
        print(f"Error reading Google Sheet: {str(e)}")
        exit(1)
else:
    try:
        df = pd.read_excel(DATA_CATALOG)
    except FileNotFoundError:
        print(f"Error: {DATA_CATALOG} not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        exit(1)

# Define the columns we want to display
# These are the columns from the new database structure
display_columns = [
    'Dataset Speaking Titles',
    'Use Case Speaking Title',
    'Country Team',
    'Description - What can be done with this? What is this about?',
    'Dataset Link',
    'Model/Use-Case Links',
    'Domain/SDG',
    'Data Type',
    'Point of Contact/Communities'
]

# Filter to only include columns that exist in the dataframe
display_columns = [col for col in display_columns if col in df.columns]

# Apply the column selection
df = df[display_columns]

# Rename columns for display
column_display_names = {
    'Dataset Speaking Titles': 'Dataset',
    'Use Case Speaking Title': 'Use Case',
    'Country Team': 'Country/Region',
    'Description - What can be done with this? What is this about?': 'Description',
    'Dataset Link': 'Dataset Link',
    'Model/Use-Case Links': 'Use Case Link',
    'Domain/SDG': 'Domain/SDG',
    'Data Type': 'Data Type',
    'Point of Contact/Communities': 'Contact'
}

def normalize_label(text):
    """Convert text to lowercase and remove special characters."""
    if pd.isna(text):
        return ""
    base = text.lower().strip()
    # Extract the main type from parentheses if present
    if "(" in base:
        base = base.split("(")[0].strip()
    # Replace both slash and space with empty string to ensure consistent normalization
    return re.sub(r'[^a-z0-9]', '', base)

def create_label_html(text, category):
    """Create HTML for a label."""
    if pd.isna(text):
        return ""
    normalized = normalize_label(text)
    return f'<span class="label label-{normalized}" data-filter="{text}">{text}</span>'

# Define columns that need special hyperlink formatting
link_columns = {
    "Dataset Link": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Dataset</a>' if pd.notna(x) else "N/A",
    "Model/Use-Case Links": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Use Case</a>' if pd.notna(x) else "N/A"
}

def convert_markdown_links_to_html(text):
    if not text or not isinstance(text, str):
        return text
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    return re.sub(link_pattern, r'<a href="\2" target="_blank" class="minimal-link">\1</a>', text)

def create_description_html(text):
    """Create HTML for description with expandable text."""
    if pd.isna(text):
        return "N/A"
    
    # Convert markdown links in the full text
    full_text = convert_markdown_links_to_html(str(text))
    
    return f"""
        <div class="description-wrapper">
            <div class="description-content">{full_text}</div>
            <span class="toggle-description">Read more</span>
        </div>
    """

def get_pastel_color(hue):
    """Generate a pale, understated pastel color given a hue value."""
    # Convert to HSL color space and create a pale color
    # Lightness 0.9 (instead of 0.95) for slightly less whiteness
    # Saturation 0.35 (instead of 0.25) for slightly more color while keeping it understated
    rgb = colorsys.hls_to_rgb(hue, 0.9, 0.45)
    # Convert RGB values to hex
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

def generate_color_palette(n):
    """Generate n evenly spaced pastel colors."""
    return [get_pastel_color(i/n) for i in range(n)]

def get_unique_categories(df):
    """Extract all unique categories from Domain/SDG, Data Type, and Status columns."""
    domains = set()
    data_types = set()
    statuses = set()
    
    # Extract domains
    if 'Domain/SDG' in df.columns:
        domain_col = df["Domain/SDG"].dropna()
        for items in domain_col:
            domains.update([item.strip() for item in str(items).split(",")])
    
    # Extract data types
    if 'Data Type' in df.columns:
        type_col = df["Data Type"].dropna()
        for items in type_col:
            data_types.update([item.strip() for item in str(items).split(",")])
    
    # Extract statuses
    if 'Use Case Pipeline Status' in df.columns:
        status_col = df["Use Case Pipeline Status"].dropna()
        for items in status_col:
            statuses.update([item.strip() for item in str(items).split(",")])
    
    # Sort the lists to ensure consistent color assignment
    return sorted(list(domains)), sorted(list(data_types)), sorted(list(statuses))

def generate_label_css(domains, data_types, statuses):
    """Generate CSS for all labels."""
    all_categories = domains + data_types + statuses
    colors = generate_color_palette(len(all_categories))
    
    css = []
    # Base label styles (moved from static CSS)
    css.append("""
.label {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    font-size: 0.8125rem;
    font-weight: 500;
    border-radius: 6px;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    line-height: 1;
    white-space: nowrap;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: all 0.2s ease;
}

.label:hover {
    transform: translateY(-1px);
    opacity: 0.9;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.label.active {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
    transform: translateY(-1px);
    opacity: 1;
}""")
    
    # Generate specific label styles
    for category, color in zip(all_categories, colors):
        normalized = normalize_label(category)
        css.append(f"""
.label-{normalized} {{
    background-color: {color};
    color: #2d3748;
}}""")
    
    return "\n".join(css)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Catalog</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <!-- Bootstrap for styling -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.1.3/css/bootstrap.min.css">
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
    /* Dynamic label styles */
    {dynamic_css}
    </style>
</head>
<body>
    <header>
        <div class="container d-flex align-items-center justify-content-between">
            <div class="header-text">
                <h1 class="mb-3">Technical Portfolio</h1>
                <p class="text-muted">An overview of datasets and use cases funded by Fair Forward</p>
            </div>
            <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank">
                <img src="img/fair_forward.png" alt="Fair Forward Logo" class="header-logo mx-3">
            </a>
        </div>
    </header>

    <div class="container my-4">
        <!-- Enhanced Filter Section -->
        <div class="filter-section mb-4 p-3 bg-white rounded shadow-sm">
            <h5 class="mb-3 fw-bold">Explore Our Global Data Repository</h5>
            
            <div class="row g-3 mb-3">
                <!-- Search Box -->
                <div class="col-md-6">
                    <div class="input-group">
                        <input type="text" id="searchInput" class="form-control" placeholder="Search for datasets, countries, or domains...">
                        <button class="btn btn-primary" type="button" id="searchButton">
                            <i class="fas fa-search"></i> Search
                        </button>
                    </div>
                </div>
                
                <!-- Domain Filter -->
                <div class="col-md-3">
                    <select class="form-select" id="domainFilter">
                        <option value="all">All Domains</option>
                        <!-- Will be populated dynamically -->
                    </select>
                </div>
                
                <!-- Region Filter -->
                <div class="col-md-3">
                    <select class="form-select" id="regionFilter">
                        <option value="all">All Regions</option>
                        <!-- Will be populated dynamically -->
                    </select>
                </div>
            </div>
            
            <div class="row g-3">
                <!-- Sort By -->
                <div class="col-md-3">
                    <select class="form-select" id="sortBy">
                        <option value="default">Recently Updated</option>
                        <option value="name-asc">Name (A-Z)</option>
                        <option value="name-desc">Name (Z-A)</option>
                        <option value="country-asc">Country (A-Z)</option>
                    </select>
                </div>
                
                <!-- View Type Buttons -->
                <div class="col-md-9">
                    <div class="filter-controls">
                        <div class="btn-group" role="group" aria-label="View filters">
                            <button type="button" class="btn btn-outline-primary active" data-view="all">All</button>
                            <button type="button" class="btn btn-outline-primary" data-view="datasets">Datasets</button>
                            <button type="button" class="btn btn-outline-primary" data-view="usecases">Use Cases</button>
                        </div>
                        
                        <button id="advancedFilters" class="btn btn-outline-secondary ms-2">
                            <i class="fas fa-sliders"></i> Advanced Filters
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="table-responsive">
            {table}
        </div>
        <div class="empty-state">No matching items found. Try changing your filters.</div>
    </div>

    <footer class="bg-light py-3 mt-4">
        <div class="container">
            <p class="mb-0 text-muted">&copy; 2024 Fair Forward</p>
        </div>
    </footer>

    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Filter functionality for labels
        const labels = document.querySelectorAll('.label');
        const tableRows = document.querySelectorAll('.custom-table tbody tr');
        const emptyState = document.querySelector('.empty-state');
        let activeFilter = null;

        // View filter buttons
        const viewButtons = document.querySelectorAll('.filter-controls button[data-view]');
        let currentView = 'all';
        
        // Column visibility based on view
        const datasetCells = document.querySelectorAll('.dataset-column');
        const usecaseCells = document.querySelectorAll('.usecase-column');
        
        // New filter elements
        const searchInput = document.getElementById('searchInput');
        const searchButton = document.getElementById('searchButton');
        const domainFilter = document.getElementById('domainFilter');
        const regionFilter = document.getElementById('regionFilter');
        const sortBySelect = document.getElementById('sortBy');
        
        // Populate domain filter
        const domains = new Set();
        document.querySelectorAll('.label').forEach(label => {{
            if (label.dataset.filter) {{
                domains.add(label.dataset.filter);
            }}
        }});
        
        domains.forEach(domain => {{
            const option = document.createElement('option');
            option.value = domain;
            option.textContent = domain;
            domainFilter.appendChild(option);
        }});
        
        // Populate region filter
        const regions = new Set();
        document.querySelectorAll('.custom-table tbody tr').forEach(row => {{
            const regionCell = row.querySelector('td:nth-child(3)');
            if (regionCell && regionCell.textContent.trim() !== 'N/A') {{
                regions.add(regionCell.textContent.trim());
            }}
        }});
        
        Array.from(regions).sort().forEach(region => {{
            const option = document.createElement('option');
            option.value = region;
            option.textContent = region;
            regionFilter.appendChild(option);
        }});
        
        // Function to update column visibility based on view
        function updateColumnVisibility() {{
            if (currentView === 'datasets') {{
                // Show only dataset column
                datasetCells.forEach(cell => {{
                    cell.classList.remove('hidden');
                    // If it's a header cell, make it the first column
                    if (cell.tagName === 'TH') {{
                        cell.style.width = '20%';
                        cell.textContent = 'Dataset';
                    }}
                }});
                
                // Hide usecase column
                usecaseCells.forEach(cell => cell.classList.add('hidden'));
            }} else if (currentView === 'usecases') {{
                // Hide dataset column
                datasetCells.forEach(cell => cell.classList.add('hidden'));
                
                // Show only usecase column
                usecaseCells.forEach(cell => {{
                    cell.classList.remove('hidden');
                    // If it's a header cell, make it the first column
                    if (cell.tagName === 'TH') {{
                        cell.style.width = '20%';
                        cell.textContent = 'Use Case';
                    }}
                }});
            }} else {{
                // Show both columns
                datasetCells.forEach(cell => {{
                    cell.classList.remove('hidden');
                    if (cell.tagName === 'TH') {{
                        cell.textContent = 'Dataset';
                    }}
                }});
                
                usecaseCells.forEach(cell => {{
                    cell.classList.remove('hidden');
                    if (cell.tagName === 'TH') {{
                        cell.textContent = 'Use Case';
                    }}
                }});
            }}
        }}

        // Function to apply all filters
        function applyFilters() {{
            let visibleRows = 0;
            const searchTerm = searchInput.value.toLowerCase();
            const selectedDomain = domainFilter.value;
            const selectedRegion = regionFilter.value;
            
            tableRows.forEach(row => {{
                // First check if row should be visible based on view filter
                let viewMatch = true;
                
                if (currentView === 'datasets') {{
                    viewMatch = row.classList.contains('has-dataset');
                }} else if (currentView === 'usecases') {{
                    viewMatch = row.classList.contains('has-usecase');
                }}
                
                // Check if row matches the label filter
                let labelMatch = !activeFilter || row.textContent.includes(activeFilter);
                
                // Check if row matches the search term
                let searchMatch = !searchTerm || row.textContent.toLowerCase().includes(searchTerm);
                
                // Check if row matches the domain filter
                let domainMatch = selectedDomain === 'all' || 
                                 (row.querySelector('[data-filter="' + selectedDomain + '"]') !== null);
                
                // Check if row matches the region filter
                const regionCell = row.querySelector('td:nth-child(3)');
                let regionMatch = selectedRegion === 'all' || 
                                 (regionCell && regionCell.textContent.trim() === selectedRegion);
                
                // Row is visible only if it matches all filters
                if (viewMatch && labelMatch && searchMatch && domainMatch && regionMatch) {{
                    row.classList.remove('filtered-out');
                    visibleRows++;
                }} else {{
                    row.classList.add('filtered-out');
                }}
            }});
            
            // Update column visibility based on current view
            updateColumnVisibility();
            
            // Toggle empty state message
            emptyState.classList.toggle('visible', visibleRows === 0);
        }}
        
        // Function to sort table rows
        function sortTable(sortBy) {{
            const tbody = document.querySelector('.custom-table tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {{
                if (sortBy === 'name-asc') {{
                    const aName = a.querySelector('td:nth-child(1), td:nth-child(2)').textContent.trim();
                    const bName = b.querySelector('td:nth-child(1), td:nth-child(2)').textContent.trim();
                    return aName.localeCompare(bName);
                }} else if (sortBy === 'name-desc') {{
                    const aName = a.querySelector('td:nth-child(1), td:nth-child(2)').textContent.trim();
                    const bName = b.querySelector('td:nth-child(1), td:nth-child(2)').textContent.trim();
                    return bName.localeCompare(aName);
                }} else if (sortBy === 'country-asc') {{
                    const aCountry = a.querySelector('td:nth-child(3)').textContent.trim();
                    const bCountry = b.querySelector('td:nth-child(3)').textContent.trim();
                    return aCountry.localeCompare(bCountry);
                }}
                
                // Default sorting (keep original order)
                return 0;
            }});
            
            // Remove all rows
            rows.forEach(row => row.remove());
            
            // Add sorted rows back
            rows.forEach(row => tbody.appendChild(row));
        }}

        // Set up label filter click handlers
        labels.forEach(label => {{
            label.addEventListener('click', () => {{
                const filterValue = label.dataset.filter;
                
                // If clicking the same filter again, remove it
                if (label.classList.contains('active')) {{
                    label.classList.remove('active');
                    activeFilter = null;
                }} else {{
                    // Remove active class from all labels
                    labels.forEach(l => l.classList.remove('active'));
                    label.classList.add('active');
                    activeFilter = filterValue;
                }}
                
                applyFilters();
            }});
        }});
        
        // Set up view filter button click handlers
        viewButtons.forEach(button => {{
            button.addEventListener('click', () => {{
                // Update active button
                viewButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update current view
                currentView = button.dataset.view;
                
                applyFilters();
            }});
        }});
        
        // Set up search functionality
        searchButton.addEventListener('click', applyFilters);
        searchInput.addEventListener('keyup', function(event) {{
            if (event.key === 'Enter') {{
                applyFilters();
            }}
        }});
        
        // Set up domain filter
        domainFilter.addEventListener('change', applyFilters);
        
        // Set up region filter
        regionFilter.addEventListener('change', applyFilters);
        
        // Set up sorting
        sortBySelect.addEventListener('change', function() {{
            sortTable(this.value);
        }});
        
        // Advanced filters button (placeholder)
        document.getElementById('advancedFilters').addEventListener('click', function() {{
            alert('Advanced filters functionality would be implemented here.');
        }});

        // Description toggle functionality
        document.querySelectorAll('.toggle-description').forEach(toggle => {{
            toggle.addEventListener('click', function() {{
                const content = this.previousElementSibling;
                const isExpanded = content.classList.contains('expanded');
                
                content.classList.toggle('expanded');
                this.textContent = isExpanded ? 'Read more' : 'Show less';
            }});
        }});
        
        // Initialize column visibility
        updateColumnVisibility();
    }});
    </script>
</body>
</html>
"""

# Generate the table header
header_html = "<tr>"
for col in display_columns:
    display_name = column_display_names.get(col, col)
    
    # Set appropriate classes for the columns
    if col == 'Dataset Speaking Titles':
        header_class = 'dataset-column'
    elif col == 'Use Case Speaking Title':
        header_class = 'usecase-column'
    elif col == 'Description - What can be done with this? What is this about?':
        header_class = 'description-column'
    else:
        header_class = 'standard-column'
    
    header_html += f"<th class='{header_class}'>{display_name}</th>"
header_html += "</tr>"

# Update the table generation code
rows = []
for _, row in df.iterrows():
    # Determine if this row has a dataset or use case or both
    has_dataset = pd.notna(row.get('Dataset Link', '')) and row.get('Dataset Link', '') != ''
    has_usecase = pd.notna(row.get('Model/Use-Case Links', '')) and row.get('Model/Use-Case Links', '') != ''
    
    row_classes = []
    if has_dataset:
        row_classes.append('has-dataset')
    if has_usecase:
        row_classes.append('has-usecase')
    
    row_class_attr = f" class='{' '.join(row_classes)}'" if row_classes else ""
    
    row_data = []
    for col in display_columns:
        cell_value = row[col]
        
        # Set appropriate classes for the cells
        if col == 'Dataset Speaking Titles':
            cell_class = 'dataset-column'
            cell_content = str(cell_value) if pd.notna(cell_value) else "N/A"
            cell_content = convert_markdown_links_to_html(cell_content)
            row_data.append(f"<td class='{cell_class}'>{cell_content}</td>")
        elif col == 'Use Case Speaking Title':
            cell_class = 'usecase-column'
            cell_content = str(cell_value) if pd.notna(cell_value) else "N/A"
            cell_content = convert_markdown_links_to_html(cell_content)
            row_data.append(f"<td class='{cell_class}'>{cell_content}</td>")
        elif col == "Description - What can be done with this? What is this about?":
            description_html = create_description_html(cell_value)
            row_data.append(f"<td class='description-column'>{description_html}</td>")
        elif col in link_columns:
            link_html = link_columns[col](cell_value)
            row_data.append(f"<td class='standard-column'>{link_html}</td>")
        elif col == "Domain/SDG":
            labels = str(cell_value).split(", ") if pd.notna(cell_value) else []
            label_html = " ".join([create_label_html(label, "domain") for label in labels])
            row_data.append(f"<td class='standard-column'>{label_html}</td>")
        elif col == "Data Type":
            types = str(cell_value).split(", ") if pd.notna(cell_value) else []
            type_html = " ".join([create_label_html(dtype, "datatype") for dtype in types])
            row_data.append(f"<td class='standard-column'>{type_html}</td>")
        else:
            cell_content = str(cell_value) if pd.notna(cell_value) else "N/A"
            cell_content = convert_markdown_links_to_html(cell_content)
            row_data.append(f"<td class='standard-column'>{cell_content}</td>")
    rows.append(f"<tr{row_class_attr}>{''.join(row_data)}</tr>")

# Construct the table without Bootstrap classes
table_html = f"<table class='custom-table'><thead>{header_html}</thead><tbody>{''.join(rows)}</tbody></table>"

# Get unique categories and generate CSS
domains, data_types, statuses = get_unique_categories(df)
dynamic_css = generate_label_css(domains, data_types, statuses)

# Add additional CSS for the new view filters and column visibility
dynamic_css += """
.filter-controls {
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
}

.btn-group .btn {
    border-radius: 0.375rem;
    margin-right: 0.5rem;
}

.btn-group .btn.active {
    background-color: #4a5568;
    color: white;
    border-color: #4a5568;
}

/* New filter section styling */
.filter-section {
    border-radius: 8px;
    border: 1px solid rgba(0, 0, 0, 0.05);
}

.filter-section h5 {
    color: #2d3748;
    font-size: 1.1rem;
}

.filter-section .form-control,
.filter-section .form-select,
.filter-section .btn {
    font-size: 0.9rem;
    border-radius: 6px;
}

.filter-section .form-control:focus,
.filter-section .form-select:focus {
    box-shadow: 0 0 0 0.2rem rgba(66, 153, 225, 0.25);
    border-color: #4299e1;
}

.filter-section .btn-primary {
    background-color: #4299e1;
    border-color: #4299e1;
}

.filter-section .btn-primary:hover {
    background-color: #3182ce;
    border-color: #3182ce;
}

.filter-section .btn-outline-secondary {
    color: #4a5568;
    border-color: #e2e8f0;
}

.filter-section .btn-outline-secondary:hover {
    background-color: #f7fafc;
    color: #2d3748;
}

tr.has-dataset.has-usecase {
    /* Rows with both dataset and use case */
    background-color: rgba(245, 243, 255, 0.3); /* Light purple background for rows with both */
}

tr.has-dataset:not(.has-usecase) {
    /* Rows with only dataset */
    background-color: rgba(236, 246, 255, 0.3); /* Light blue background for dataset rows */
}

tr.has-usecase:not(.has-dataset) {
    /* Rows with only use case */
    background-color: rgba(240, 247, 235, 0.3); /* Light green background for use case rows */
}

/* Column visibility classes */
.hidden {
    display: none !important;
}

/* Make dataset and usecase columns the same width */
.dataset-column, .usecase-column {
    width: 20%;
    font-weight: 500;
}

/* Add visual indicators for row types */
tr.has-dataset:not(.has-usecase) td.dataset-column::before {
    content: "📊 ";
    opacity: 0.7;
}

tr.has-usecase:not(.has-dataset) td.usecase-column::before {
    content: "🔍 ";
    opacity: 0.7;
}

tr.has-dataset.has-usecase td.dataset-column::before,
tr.has-dataset.has-usecase td.usecase-column::before {
    content: "🔗 ";
    opacity: 0.7;
}
"""

# Create the complete HTML with dynamic CSS
output_html = HTML_TEMPLATE.format(table=table_html, dynamic_css=dynamic_css)

try:
    with open(HTML_OUTPUT, "w") as file:
        file.write(output_html)
    print("HTML file generated successfully.")
except Exception as e:
    print(f"Error writing HTML file: {e}")

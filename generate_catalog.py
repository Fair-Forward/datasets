import pandas as pd
import html
import os
import re
import colorsys
import argparse
import datetime

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
    
    # Convert markdown links [text](url) to HTML <a href="url">text</a>
    pattern = r'\[(.*?)\]\((.*?)\)'
    html_text = re.sub(pattern, r'<a href="\2" target="_blank">\1</a>', text)
    
    # If no markdown links but contains a URL, make it clickable
    if html_text == text and ('http://' in text or 'https://' in text):
        # This pattern matches URLs that aren't already in HTML tags
        url_pattern = r'(https?://[^\s<>]+)(?![^<]*>|[^<>]*</)'
        html_text = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
    
    return html_text

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

# Function to get unique categories for generating CSS
def get_unique_categories(df):
    domains = set()
    data_types = set()
    statuses = set()
    regions = set()
    
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
    
    # Extract regions
    region_col = 'Country Team'
    if region_col in df.columns:
        for region_text in df[region_col].dropna():
            if isinstance(region_text, str):
                for region in re.split(r'[,;]', region_text):
                    region = region.strip()
                    if region:
                        regions.add(region)
    
    return list(domains), list(data_types), list(statuses), list(regions)

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
    # Extract card data
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
    
    # Determine if row has dataset and/or use case
    has_dataset = isinstance(dataset_link, str) and not pd.isna(dataset_link)
    has_usecase = isinstance(model_links, str) and not pd.isna(model_links)
    
    # Select the appropriate title based on content type and speaking titles
    if has_usecase and usecase_speaking_title and not pd.isna(usecase_speaking_title):
        title = usecase_speaking_title
    elif has_dataset and dataset_speaking_title and not pd.isna(dataset_speaking_title):
        title = dataset_speaking_title
    else:
        title = onsite_name
    
    # Generate all possible directory names from different titles
    possible_titles = []
    if onsite_name and not pd.isna(onsite_name):
        possible_titles.append(onsite_name)
    if dataset_speaking_title and not pd.isna(dataset_speaking_title):
        possible_titles.append(dataset_speaking_title)
    if usecase_speaking_title and not pd.isna(usecase_speaking_title):
        possible_titles.append(usecase_speaking_title)
    
    # Generate normalized directory names for each title
    dir_names = [normalize_for_directory(t) for t in possible_titles]
    # Remove duplicates and empty strings
    dir_names = list(set(filter(None, dir_names)))
    
    # Use the first directory name that exists, or the first one if none exist
    dir_name = None
    for d in dir_names:
        if os.path.exists(os.path.join("docs/public/projects", d)):
            dir_name = d
            break
    if not dir_name and dir_names:
        dir_name = dir_names[0]
    
    # Card classes based on what it contains
    card_classes = ["card"]
    if has_dataset:
        card_classes.append("has-dataset")
    if has_usecase:
        card_classes.append("has-usecase")
    
    card_class = " ".join(card_classes)
    
    # Check for project-specific image
    card_image = '<div class="card-image"></div>'
    
    # First check in the project directory
    project_image_path = None
    if dir_name:
        images_dir = f"docs/public/projects/{dir_name}/images"
        
        # Check if the images directory exists and contains any images
        if os.path.exists(images_dir):
            # Look for any image file in the directory
            image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            if image_files:
                project_image_path = f"public/projects/{dir_name}/images/{image_files[0]}"
    
    # Set the image if found
    if project_image_path:
        card_image = f'<div class="card-image has-image" style="background-image: url(\'{project_image_path}\');"></div>'
    
    # Create domain badges
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
    
    # Create meta items
    meta_items = []
    if region and not pd.isna(region):
        # Clean up region text by removing extra spaces and normalizing
        clean_region = re.sub(r'\s+', ' ', str(region).strip())
        meta_items.append(f'<div class="meta-item"><i class="fas fa-map-marker-alt"></i> {html.escape(clean_region)}</div>')
    
    if contact and not pd.isna(contact):
        # Process contact information with markdown links
        contact_html = convert_markdown_links_to_html(contact)
        meta_items.append(f'<div class="meta-item"><i class="fas fa-user"></i> {contact_html}</div>')
    
    meta_html = ""
    if meta_items:
        meta_html = f'<div class="meta">{"".join(meta_items)}</div>'
    
    # Create data type chips with different icons based on type
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
    
    # Create tags for filtering (hidden)
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
    
    # Create description
    description_html = ""
    if description and not pd.isna(description):
        description_html = f'''
            <div class="card-description">
                <div class="description-text collapsed">{html.escape(str(description))}</div>
                <div class="read-more-btn">Read more</div>
            </div>
        '''
    
    # Create footer with links
    footer_links = []
    if has_dataset:
        footer_links.append(f'<a href="{dataset_link}" target="_blank" class="btn btn-primary"><i class="fas fa-database"></i> Dataset</a>')
    
    if has_usecase:
        footer_links.append(f'<a href="{model_links}" target="_blank" class="btn btn-secondary"><i class="fas fa-lightbulb"></i> Use Case</a>')
    
    footer_links.append('<button class="btn btn-view-details"><i class="fas fa-info-circle"></i> How to use it</button>')
    
    footer_html = f'<div class="card-footer">{"".join(footer_links)}</div>'
    
    # Store all possible directory names as a data attribute for JavaScript to use
    dir_names_json = html.escape(str(dir_names))
    
    # Construct the complete card
    card_html = f'''
    <div class="{card_class}" data-title="{html.escape(str(title))}" data-region="{html.escape(str(region))}" data-id="{idx}" data-dir-names="{dir_names_json}">
        {card_image}
        <div class="card-header">
            {domain_badges}
            <h3>{html.escape(str(title))}</h3>
            {meta_html}
        </div>
        <div class="card-body">
            {description_html}
            {data_type_html}
            {tags_html}
        </div>
        {footer_html}
    </div>
    '''
    
    return card_html

def generate_filter_html(domains, data_types, regions):
    domain_options = '\n'.join([f'<option value="{domain}">{domain}</option>' for domain in sorted(domains)])
    data_type_options = '\n'.join([f'<option value="{data_type}">{data_type}</option>' for data_type in sorted(data_types)])
    region_options = '\n'.join([f'<option value="{region}">{region}</option>' for region in sorted(regions)])
    
    filter_html = f'''
    <div class="filters">
        <div class="filters-content">
            <div class="filter-group">
                <div class="search-box">
                    <i class="fas fa-search"></i>
                    <input type="text" id="searchInput" placeholder="Search datasets and use-cases...">
                </div>
            </div>
            <div class="filter-group">
                <span class="filter-label">View:</span>
                <select id="viewFilter">
                    <option value="all">All Items</option>
                    <option value="datasets">Datasets Only</option>
                    <option value="usecases">Use Cases Only</option>
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
            <div class="filter-group share-filter-group">
                <button id="shareViewBtn" class="btn-share-view" title="Copy link to share this filtered view">
                    <i class="fas fa-share-alt"></i> Share this view
                </button>
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
            
            // Set up read more buttons
            const descriptionTexts = document.querySelectorAll('.description-text');
            descriptionTexts.forEach(text => {
                // Check if the text is long enough to need a read more button
                const needsReadMore = text.scrollHeight > text.clientHeight || text.textContent.length > 300;
                
                if (needsReadMore) {
                    const readMoreBtn = text.nextElementSibling;
                    if (readMoreBtn && readMoreBtn.classList.contains('read-more-btn')) {
                        readMoreBtn.addEventListener('click', function() {
                            text.classList.toggle('collapsed');
                            text.classList.toggle('expanded');
                            this.textContent = text.classList.contains('expanded') ? 'Read less' : 'Read more';
                        });
                    }
                } else {
                    // Hide the read more button if not needed
                    const readMoreBtn = text.nextElementSibling;
                    if (readMoreBtn && readMoreBtn.classList.contains('read-more-btn')) {
                        readMoreBtn.style.display = 'none';
                    }
                }
            });
            
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
            
            // Add event listeners for detail panel
            document.querySelectorAll('.btn-view-details').forEach(btn => {
                btn.addEventListener('click', function() {
                    const card = this.closest('.card');
                    const title = card.getAttribute('data-title');
                    const id = card.getAttribute('data-id');
                    selectedItemId = id;
                    openDetailPanel(title, id);
                    updateUrl(true); // Update URL with item ID
                });
            });
            
            // Apply URL parameters on page load
            applyUrlParams();
            
            // Handle browser back/forward navigation
            window.addEventListener('popstate', function() {
                applyUrlParams();
            });
            
            // Share view button functionality
            const shareViewBtn = document.getElementById('shareViewBtn');
            if (shareViewBtn) {
                shareViewBtn.addEventListener('click', function() {
                    // Copy current URL to clipboard
                    navigator.clipboard.writeText(window.location.href).then(() => {
                        // Show success feedback
                        const originalHTML = this.innerHTML;
                        this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                        this.classList.add('copied');
                        
                        // Reset after 2 seconds
                        setTimeout(() => {
                            this.innerHTML = originalHTML;
                            this.classList.remove('copied');
                        }, 2000);
                    }).catch(err => {
                        console.error('Failed to copy URL: ', err);
                    });
                });
            }
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
    
    # Get unique categories for filter and CSS generation
    domains, data_types, statuses, regions = get_unique_categories(df)
    
    # Generate CSS for labels
    label_css = generate_label_css(domains, data_types, statuses)
    
    # Create a completely new HTML file from scratch
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data & Use Cases Catalog</title>
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
        :root {{
            /* Claude.ai inspired color palette with Fair Forward influence */
            --primary: #3b5998;
            --primary-light: #4c70ba;
            --secondary: #5b7fb9;
            --light: #f9fafb;
            --dark: #1a202c;
            --gray: #64748b;
            --border: #e2e8f0;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --shadow: rgba(0, 0, 0, 0.04);
            --shadow-hover: rgba(0, 0, 0, 0.08);
            --title-color: #1e3a6e;
            --btn-text: #ffffff;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }}
        
        body {{
            background-color: var(--background);
            color: var(--text);
            line-height: 1.7;
            font-size: 16px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        header {{
            background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
            padding: 80px 0 60px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.03);
            text-align: center;
            position: relative;
        }}
        
        .header-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .header-text {{
            text-align: left;
            flex: 1;
        }}
        
        .header-logos {{
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-left: 2rem;
        }}
        
        .header-logo {{
            height: 70px;
            width: auto;
            opacity: 0.95;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.05));
        }}
        
        .header-logo:hover {{
            opacity: 1;
            transform: translateY(-2px);
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
            color: var(--title-color);
            letter-spacing: -0.02em;
            line-height: 1.2;
        }}
        
        .subtitle {{
            font-size: 1.125rem;
            color: var(--gray);
            max-width: 800px;
            line-height: 1.6;
            font-weight: 400;
        }}
        
        .filters {{
            background-color: var(--card-bg);
            padding: 1.5rem 0;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 10;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }}
        
        .filters-content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            justify-content: center;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .filter-label {{
            font-weight: 500;
            font-size: 0.875rem;
            color: var(--text-light);
        }}
        
        select, input {{
            padding: 0.625rem 1rem;
            border-radius: 0.5rem;
            border: 1px solid var(--border);
            min-width: 180px;
            background-color: white;
            font-size: 0.875rem;
            color: var(--text);
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px var(--shadow);
        }}
        
        select:focus, input:focus {{
            outline: none;
            border-color: var(--primary-light);
            box-shadow: 0 0 0 3px rgba(142, 68, 173, 0.1);
        }}
        
        .search-box {{
            display: flex;
            align-items: center;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 0.625rem 1rem;
            min-width: 300px;
            background-color: white;
            box-shadow: 0 1px 2px var(--shadow);
            transition: all 0.2s ease;
        }}
        
        .search-box:focus-within {{
            border-color: var(--primary-light);
            box-shadow: 0 0 0 3px rgba(142, 68, 173, 0.1);
        }}
        
        .search-box input {{
            border: none;
            flex-grow: 1;
            min-width: 0;
            padding: 0;
            box-shadow: none;
        }}
        
        .search-box input:focus {{
            box-shadow: none;
        }}
        
        .search-box i {{
            color: var(--gray);
            margin-right: 0.75rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 3rem auto;
            padding: 0 2rem;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        
        .card {{
            background-color: var(--card-bg);
            border-radius: 0.75rem;
            overflow: hidden;
            box-shadow: 0 3px 5px var(--shadow);
            transition: transform 0.3s, box-shadow 0.3s;
            display: flex;
            flex-direction: column;
            height: 100%;
            position: relative;
            border: 1px solid rgba(0, 0, 0, 0.02);
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 15px var(--shadow-hover);
        }}
        
        .card-image {{
            height: 140px;
            background-color: #f8fafc;
            background-image: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
            background-size: cover;
            background-position: center;
            position: relative;
        }}
        
        .card-image.has-image {{
            background-image: none;
        }}
        
        .card-header {{
            padding: 1.25rem 1.25rem 0.5rem;
        }}
        
        .card-body {{
            padding: 0 1.25rem 0.75rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .domain-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            position: absolute;
            top: 1rem;
            right: 1rem;
            z-index: 1;
        }}
        
        .domain-badge {{
            display: inline-block;
            background-color: var(--primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.7rem;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(59, 89, 152, 0.15);
        }}
        
        .data-type-chips {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            margin-top: 0.25rem;
        }}
        
        .data-type-chip {{
            font-size: 0.7rem;
            font-weight: 400;
            padding: 0.2rem 0.5rem;
            border-radius: 1rem;
            background-color: rgba(0, 0, 0, 0.05);
            color: var(--gray);
            display: inline-flex;
            align-items: center;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }}
        
        .data-type-chip i {{
            margin-right: 0.25rem;
            font-size: 0.65rem;
            opacity: 0.7;
        }}
        
        .card h3 {{
            font-size: 1.125rem;
            margin-bottom: 0.5rem;
            color: var(--title-color);
            line-height: 1.3;
            font-weight: 600;
        }}
        
        .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }}
        
        .meta-item {{
            font-size: 0.75rem;
            color: var(--gray);
            display: flex;
            align-items: center;
        }}
        
        .meta-item i {{
            margin-right: 0.25rem;
        }}
        
        .card-description {{
            margin-bottom: 0.75rem;
            flex-grow: 1;
        }}
        
        .description-text {{
            color: var(--text-light);
            font-size: 0.9375rem;
            line-height: 1.6;
            overflow: hidden;
            position: relative;
        }}
        
        .description-text.collapsed {{
            max-height: 4.8em; /* Show 3 lines of text */
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        }}
        
        .read-more-btn {{
            color: var(--primary);
            font-size: 0.8125rem;
            font-weight: 500;
            cursor: pointer;
            margin-top: 0.25rem;
            display: inline-block;
            transition: color 0.2s;
        }}
        
        .read-more-btn:hover {{
            color: var(--secondary);
            text-decoration: underline;
        }}
        
        .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.8125rem;
            color: var(--text-light);
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.375rem;
        }}
        
        .meta-item a {{
            color: var(--primary);
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .meta-item a:hover {{
            color: var(--secondary);
            text-decoration: underline;
        }}
        
        .tags {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1.5rem;
        }}
        
        .tag {{
            background-color: rgba(142, 68, 173, 0.08);
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            color: var(--primary);
            transition: all 0.2s;
            font-weight: 500;
        }}
        
        .tag:hover {{
            background-color: rgba(142, 68, 173, 0.12);
            transform: translateY(-2px);
        }}
        
        .card-footer {{
            border-top: 1px solid var(--border);
            padding: 0.75rem 1.25rem;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.5rem;
            background-color: rgba(0,0,0,0.01);
        }}
        
        .btn {{
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
        }}
        
        .btn i {{
            font-size: 0.75rem;
        }}
        
        .btn-view-details {{
            background-color: #fff0f0;  /* Light red background */
            color: var(--text-light);
            border: 1px solid #ffdddd;  /* Light red border */
            margin-left: auto;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }}
        
        @media (max-width: 768px) {{
            .filters-content {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .search-box {{
                min-width: 100%;
            }}
            
            .share-filter-group {{
                margin-left: 0;
                margin-top: 1rem;
            }}
            
            .btn-share-view {{
                width: 100%;
                justify-content: center;
            }}
            
            .grid {{
                grid-template-columns: 1fr;
            }}
            
            .card-footer {{
                flex-wrap: nowrap;
                justify-content: space-between;
            }}
            
            .btn {{
                font-size: 0.7rem;
                padding: 0.375rem 0.5rem;
            }}
            
            .btn-view-details {{
                margin-left: 0.25rem;
                order: 0;
            }}
        }}
        
        {label_css}
        
        footer {{
            background-color: var(--light);
            color: var(--text-light);
            padding: 4rem 0;
            text-align: center;
            border-top: 1px solid var(--border);
        }}
        
        .footer-content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        footer p {{
            font-size: 0.9375rem;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .btn-primary {{
            background-color: var(--primary);
            color: var(--btn-text);
            box-shadow: 0 2px 4px rgba(59, 89, 152, 0.15);
        }}
        
        .btn-primary:hover {{
            background-color: var(--primary-light);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(59, 89, 152, 0.2);
        }}
        
        .btn-secondary {{
            background-color: rgba(59, 89, 152, 0.08);
            color: var(--primary);
        }}
        
        .btn-secondary:hover {{
            background-color: rgba(59, 89, 152, 0.12);
            transform: translateY(-2px);
        }}
        
        .btn-view-details:hover {{
            background-color: #ffe0e0;  /* Slightly darker red on hover */
            color: #d63031;  /* Darker red text on hover */
            transform: translateY(-2px);
        }}
        
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            background-color: rgba(255, 255, 255, 0.5);
            border-radius: 1rem;
            border: 1px solid var(--border);
            display: none;
            margin: 2rem auto;
            max-width: 600px;
        }}
        
        .empty-state.visible {{
            display: block;
        }}
        
        .empty-state h3 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--text);
            font-weight: 600;
        }}
        
        .empty-state p {{
            color: var(--text-light);
            font-size: 1.0625rem;
            line-height: 1.6;
        }}
        
        .card.filtered-out {{
            display: none;
        }}
        
        /* Side panel styles are now in enhanced_side_panel.css */
        
        .share-filter-group {{
            margin-left: auto;
        }}
        
        .btn-share-view {{
            background-color: #f0f9ff;
            color: #3b82f6;
            border: 1px solid #bfdbfe;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.2s ease;
        }}
        
        .btn-share-view:hover {{
            background-color: #e0f2fe;
            transform: translateY(-2px);
        }}
        
        .btn-share-view.copied {{
            background-color: #ecfdf5;
            color: #10b981;
            border-color: #a7f3d0;
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="header-text">
                <h1>Data & Use Cases Catalog</h1>
                <p class="subtitle">Exploring datasets and solutions for global challenges across agriculture, language technology, climate action, energy, and more. Browse our collection of datasets and use cases for AI applications for sustainable development.</p>
            </div>
            <div class="header-logos">
                <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank">
                    <img src="img/fair_forward.png" alt="Fair Forward Logo" class="header-logo">
                </a>
                <a href="https://www.bmz-digital.global/en/" target="_blank">
                    <img src="img/digital_global.png" alt="Digital Global Logo" class="header-logo">
                </a>
            </div>
        </div>
    </header>
    
    {generate_filter_html(domains, data_types, regions)}
    
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
        </div>
    </footer>
    
    {generate_js_code()}
    
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Add enhanced side panel JavaScript -->
    <script src="enhanced_side_panel.js"></script>
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
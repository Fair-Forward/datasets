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
    title = row.get('OnSite Name', '')
    description = row.get('Description - What can be done with this? What is this about?', '')
    dataset_link = row.get('Dataset Link', '')
    model_links = row.get('Model/Use-Case Links', '')
    domain = row.get('Domain/SDG', '')
    status = row.get('Use Case Pipeline Status', '')
    data_type = row.get('Data Type', '')
    contact = row.get('Point of Contact/Communities', '')
    region = row.get('Country Team', '')
    
    # Normalize title for directory name
    dir_name = normalize_for_directory(title)
    
    # Determine if row has dataset and/or use case
    has_dataset = isinstance(dataset_link, str) and not pd.isna(dataset_link)
    has_usecase = isinstance(model_links, str) and not pd.isna(model_links)
    
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
    
    # We're removing the Dataset and Use-Case tags, so we'll skip adding status tags
    
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
    
    # Construct the complete card
    card_html = f'''
    <div class="{card_class}" data-title="{html.escape(str(title))}" data-region="{html.escape(str(region))}" data-id="{idx}">
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
            
            // Add event listeners for filters
            searchInput.addEventListener('input', function() {
                searchTerm = this.value.toLowerCase();
                applyFilters();
            });
            
            viewFilter.addEventListener('change', function() {
                currentView = this.value;
                applyFilters();
            });
            
            domainFilter.addEventListener('change', function() {
                selectedDomain = this.value;
                applyFilters();
            });
            
            dataTypeFilter.addEventListener('change', function() {
                selectedDataType = this.value;
                applyFilters();
            });
            
            regionFilter.addEventListener('change', function() {
                selectedRegion = this.value;
                applyFilters();
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
            
            // Initial filter application
            applyFilters();
            
            // Detail Panel Functionality
            const detailPanel = document.getElementById('detailPanel');
            const panelOverlay = document.getElementById('panelOverlay');
            const closeDetailPanel = document.getElementById('closeDetailPanel');
            const detailPanelTitle = document.getElementById('detailPanelTitle');
            const detailPanelLoader = document.getElementById('detailPanelLoader');
            const detailPanelData = document.getElementById('detailPanelData');
            
            // Add event listeners for detail panel
            document.querySelectorAll('.btn-view-details').forEach(btn => {
                btn.addEventListener('click', function() {
                    const card = this.closest('.card');
                    const title = card.getAttribute('data-title');
                    const id = card.getAttribute('data-id');
                    openDetailPanel(title, id);
                });
            });
            
            if (closeDetailPanel) {
                closeDetailPanel.addEventListener('click', function() {
                    detailPanel.classList.remove('open');
                    panelOverlay.classList.remove('active');
                    document.body.style.overflow = '';
                });
            }
            
            if (panelOverlay) {
                panelOverlay.addEventListener('click', function() {
                    detailPanel.classList.remove('open');
                    panelOverlay.classList.remove('active');
                    document.body.style.overflow = '';
                });
            }
            
            // Function to open the detail panel
            function openDetailPanel(title, itemId) {
                const detailPanel = document.getElementById('detailPanel');
                const detailPanelTitle = document.getElementById('detailPanelTitle');
                const detailPanelLoader = document.getElementById('detailPanelLoader');
                const detailPanelData = document.getElementById('detailPanelData');
                const panelOverlay = document.getElementById('panelOverlay');
                
                if (!detailPanel || !detailPanelTitle || !detailPanelLoader || !detailPanelData || !panelOverlay) {
                    console.error('Could not find required panel elements');
                    return;
                }
                
                // Set title and show panel
                detailPanelTitle.textContent = title;
                detailPanel.classList.add('open');
                panelOverlay.classList.add('active');
                document.body.style.overflow = 'hidden';
                
                // Show loader and hide content
                detailPanelLoader.style.display = 'flex';
                detailPanelData.classList.remove('active');
                detailPanelData.style.display = 'none';
                
                // Load the details
                loadItemDetails(itemId);
            }
            
            // Simple markdown parser
            function parseMarkdown(markdown) {
                if (!markdown) return '';
                
                // Replace headers
                let html = markdown
                    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                    .replace(/^# (.*$)/gim, '<h1>$1</h1>');
                
                // Replace links
                html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank">$1</a>');
                
                // Replace images
                html = html.replace(/!\[([^\]]+)\]\(([^)]+)\)/gim, '<img src="$2" alt="$1" style="max-width:100%;">');
                
                // Replace bold text
                html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
                
                // Replace italic text
                html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');
                
                // Replace code blocks
                html = html.replace(/```([^`]+)```/gim, '<pre><code>$1</code></pre>');
                
                // Replace inline code
                html = html.replace(/`([^`]+)`/gim, '<code>$1</code>');
                
                // Replace lists
                html = html.replace(/^\s*\*\s(.*$)/gim, '<li>$1</li>');
                html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
                
                // Replace paragraphs (must be done last)
                html = html.replace(/^(?!<[a-z])(.*$)/gim, '<p>$1</p>');
                
                // Fix nested lists and paragraphs
                html = html.replace(/<\/ul>\s*<ul>/gim, '');
                html = html.replace(/<\/p>\s*<p>/gim, '</p><p>');
                
                return html;
            }
            
            // Function to load item details
            function loadItemDetails(itemId) {
                const card = document.querySelector(`.card[data-id="${itemId}"]`);
                if (!card) return;
                
                const title = card.getAttribute('data-title');
                const tags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);
                const region = card.getAttribute('data-region');
                
                // Normalize title for directory name - match the Python normalization
                const dirName = title.toLowerCase().replace(/ /g, '_').replace(/[^a-z0-9_]/g, '');
                console.log('Loading details for:', dirName);
                
                // Show loading state
                const detailPanelLoader = document.getElementById('detailPanelLoader');
                const detailPanelData = document.getElementById('detailPanelData');
                
                if (detailPanelLoader && detailPanelData) {
                    detailPanelLoader.style.display = 'flex';
                    detailPanelData.style.display = 'none';
                }
                
                // Prepare to fetch all markdown files
                const filesToFetch = [
                    { path: `./public/projects/${dirName}/docs/description.md`, section: 'Description' },
                    { path: `./public/projects/${dirName}/docs/data_characteristics.md`, section: 'Data Characteristics' },
                    { path: `./public/projects/${dirName}/docs/model_characteristics.md`, section: 'Model Characteristics' },
                    { path: `./public/projects/${dirName}/docs/how_to_use.md`, section: 'How to Use It' }
                ];
                
                // Initialize content sections
                let contentSections = {
                    'Description': '',
                    'Data Characteristics': '',
                    'Model Characteristics': '',
                    'How to Use It': ''
                };
                
                // Create a counter to track when all fetches are complete
                let fetchesCompleted = 0;
                
                // Function to update the UI when all fetches are complete
                function updateDetailPanel() {
                    console.log('Updating panel with sections:', contentSections);
                    let detailContent = '';
                    
                    // Add each section that has content
                    for (const [section, content] of Object.entries(contentSections)) {
                        if (content) {
                            detailContent += `
                                <div class="detail-section">
                                    <h3>${section}</h3>
                                    <div class="documentation-content">${content}</div>
                                </div>
                            `;
                        }
                    }
                    
                    // Add tags section
                    detailContent += `
                        <div class="detail-section">
                            <h3>Tags</h3>
                            <div class="tags">
                                ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                            </div>
                        </div>
                    `;
                    
                    // Add region section if available
                    if (region) {
                        detailContent += `
                            <div class="detail-section">
                                <h3>Region</h3>
                                <p>${region}</p>
                            </div>
                        `;
                    }
                    
                    // Update the detail panel content
                    const detailPanelData = document.getElementById('detailPanelData');
                    const detailPanelLoader = document.getElementById('detailPanelLoader');
                    
                    if (detailPanelData && detailPanelLoader) {
                        detailPanelData.innerHTML = detailContent;
                        detailPanelLoader.style.display = 'none';
                        detailPanelData.classList.add('active');
                        detailPanelData.style.display = 'block';
                    } else {
                        console.error('Could not find detail panel elements');
                    }
                }
                
                // Fetch each file
                filesToFetch.forEach(file => {
                    console.log('Fetching:', file.path);
                    fetch(file.path)
                        .then(response => {
                            console.log('Response for', file.path, ':', response.status);
                            if (response.ok) {
                                return response.text();
                            } else {
                                console.log('File not found:', file.path);
                                return null;
                            }
                        })
                        .then(content => {
                            if (content) {
                                console.log('Content loaded for', file.section);
                                // Parse markdown content
                                contentSections[file.section] = parseMarkdown(content);
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching', file.path, ':', error);
                        })
                        .finally(() => {
                            fetchesCompleted++;
                            console.log('Fetches completed:', fetchesCompleted, 'of', filesToFetch.length);
                            if (fetchesCompleted === filesToFetch.length) {
                                updateDetailPanel();
                            }
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
    <style>
        :root {{
            --primary: #1a365d;
            --primary-light: #2d5a88;
            --secondary: #4a5568;
            --light: #f8f9fa;
            --dark: #2d3748;
            --gray: #4a5568;
            --border: #e2e8f0;
            --background: #f8f9fa;
            --card-bg: #ffffff;
            --text: #2d3748;
            --text-light: #4a5568;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }}
        
        body {{
            background-color: var(--background);
            color: var(--dark);
            line-height: 1.7;
        }}
        
        header {{
            background: linear-gradient(135deg, #ffffff 0%, #f0f4f8 100%);
            padding: 60px 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
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
        
        .header-logo {{
            height: 70px;
            width: auto;
            opacity: 0.95;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
            margin-left: 2rem;
        }}
        
        .header-logo:hover {{
            opacity: 1;
            transform: translateY(-2px);
        }}
        
        h1 {{
            font-size: 2.25rem;
            margin-bottom: 0.75rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }}
        
        .subtitle {{
            font-size: 1rem;
            color: var(--gray);
            max-width: 800px;
            line-height: 1.5;
        }}
        
        .filters {{
            background-color: white;
            padding: 1.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 1px solid var(--border);
            width: 100%;
        }}
        
        .filters-content {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 1rem;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            margin-right: 1.5rem;
        }}
        
        .filter-label {{
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--gray);
            margin-right: 0.5rem;
        }}
        
        select {{
            padding: 0.5rem 2rem 0.5rem 0.75rem;
            border: 1px solid var(--border);
            border-radius: 0.375rem;
            background-color: white;
            font-size: 0.875rem;
            color: var(--dark);
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%234a5568' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 0.5rem center;
            cursor: pointer;
        }}
        
        .search-box {{
            position: relative;
            flex-grow: 1;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 0.5rem 0.75rem 0.5rem 2.25rem;
            border: 1px solid var(--border);
            border-radius: 0.375rem;
            font-size: 0.875rem;
            color: var(--dark);
        }}
        
        .search-box i {{
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--gray);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .card {{
            background-color: var(--card-bg);
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            border: 1px solid var(--border);
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 15px rgba(0,0,0,0.05);
        }}
        
        .card-image {{
            height: 140px;
            background-color: #f0f4f8;
            position: relative;
            overflow: hidden;
        }}
        
        .card-image.has-image {{
            background-size: cover;
            background-position: center;
        }}
        
        .card-header {{
            padding: 1.25rem 1.25rem 0.75rem;
            position: relative;
        }}
        
        .domain-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }}
        
        .domain-badge {{
            font-size: 0.75rem;
            font-weight: 500;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }}
        
        .data-type-chips {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
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
            font-weight: 600;
            margin-bottom: 0.5rem;
            line-height: 1.4;
            color: var(--dark);
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
        
        .card-body {{
            padding: 0 1.25rem 1.25rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .card-description {{
            margin-bottom: 1rem;
        }}
        
        .description-text {{
            font-size: 0.875rem;
            color: var(--text-light);
            overflow: hidden;
            position: relative;
        }}
        
        .description-text.collapsed {{
            max-height: 4.5rem;
            text-overflow: ellipsis;
        }}
        
        .read-more-btn {{
            font-size: 0.75rem;
            color: var(--primary);
            cursor: pointer;
            margin-top: 0.25rem;
            font-weight: 500;
            display: inline-block;
        }}
        
        .read-more-btn:hover {{
            text-decoration: underline;
        }}
        
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: auto;
        }}
        
        .tag {{
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            background-color: #f0f4f8;
            color: var(--gray);
        }}
        
        .card-footer {{
            padding: 1rem;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 0.5rem;
            flex-wrap: nowrap;
            justify-content: space-between;
        }}
        
        .btn {{
            padding: 0.4rem 0.6rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            border: none;
            white-space: nowrap;
            flex: 1;
            min-width: 0;
        }}
        
        .btn i {{
            margin-right: 0.25rem;
            font-size: 0.75rem;
        }}
        
        .btn-primary {{
            background-color: var(--primary);
            color: white;
        }}
        
        .btn-primary:hover {{
            background-color: var(--primary-light);
        }}
        
        .btn-secondary {{
            background-color: #e2e8f0;
            color: var(--dark);
        }}
        
        .btn-secondary:hover {{
            background-color: #cbd5e0;
        }}
        
        .btn-view-details {{
            background-color: white;
            color: var(--gray);
            border: 1px solid var(--border);
        }}
        
        .btn-view-details:hover {{
            background-color: #f8f9fa;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 3rem 1rem;
            background-color: white;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            border: 1px solid var(--border);
            display: none;
        }}
        
        .empty-state.visible {{
            display: block;
        }}
        
        .empty-state h3 {{
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
            color: var(--dark);
        }}
        
        .empty-state p {{
            color: var(--gray);
        }}
        
        .card.filtered-out {{
            display: none;
        }}
        
        .detail-panel {{
            position: fixed;
            top: 0;
            right: -800px;
            width: 800px;
            max-width: 90vw;
            height: 100vh;
            background-color: var(--card-bg);
            box-shadow: -5px 0 25px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .detail-panel.open {{
            right: 0;
        }}
        
        .detail-panel-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .detail-panel-header h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
        }}
        
        .close-panel-btn {{
            background: none;
            border: none;
            cursor: pointer;
            color: var(--gray);
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            transition: all 0.2s;
        }}
        
        .close-panel-btn:hover {{
            background-color: #f0f4f8;
            color: var(--dark);
        }}
        
        .detail-panel-content {{
            padding: 2rem;
            overflow-y: auto;
            flex-grow: 1;
            line-height: 1.6;
        }}
        
        .panel-loader {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--gray);
        }}
        
        .loader-spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin-bottom: 1rem;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .panel-data {{
            display: none;
        }}
        
        .panel-data.active {{
            display: block;
        }}
        
        .detail-section {{
            margin-bottom: 2.5rem;
        }}
        
        .detail-section h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--dark);
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }}
        
        .panel-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0,0,0,0.5);
            z-index: 99;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease-in-out;
        }}
        
        .panel-overlay.active {{
            opacity: 1;
            pointer-events: all;
        }}
        
        footer {{
            background-color: #f8f9fa;
            padding: 2rem 0;
            border-top: 1px solid var(--border);
            text-align: center;
            margin-top: 2rem;
        }}
        
        footer p {{
            color: var(--gray);
            font-size: 0.875rem;
        }}
        
        .code-sample {{
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            overflow-x: auto;
            font-family: monospace;
            font-size: 0.85rem;
            color: #333;
            border: 1px solid #e2e8f0;
        }}
        
        .documentation-content {{
            line-height: 1.7;
            font-size: 1rem;
            color: var(--text);
        }}
        
        .documentation-content h1,
        .documentation-content h2,
        .documentation-content h3,
        .documentation-content h4 {{
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
            color: var(--dark);
        }}
        
        .documentation-content h1 {{
            font-size: 1.75rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }}
        
        .documentation-content h2 {{
            font-size: 1.5rem;
        }}
        
        .documentation-content h3 {{
            font-size: 1.25rem;
        }}
        
        .documentation-content h4 {{
            font-size: 1.1rem;
        }}
        
        .documentation-content p {{
            margin-bottom: 1.25rem;
        }}
        
        .documentation-content ul,
        .documentation-content ol {{
            margin-bottom: 1.25rem;
            padding-left: 1.75rem;
        }}
        
        .documentation-content li {{
            margin-bottom: 0.5rem;
        }}
        
        .documentation-content pre {{
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1.25rem;
            overflow-x: auto;
            margin: 1.5rem 0;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            border: 1px solid #e2e8f0;
        }}
        
        .documentation-content code {{
            background-color: #f1f1f1;
            padding: 0.2rem 0.4rem;
            border-radius: 0.25rem;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            color: #476582;
        }}
        
        .documentation-content a {{
            color: #3182ce;
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .documentation-content a:hover {{
            color: #2c5282;
            text-decoration: underline;
        }}
        
        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .detail-panel {{
                width: 100vw;
                max-width: 100vw;
            }}
        }}
        
        {label_css}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="header-text">
                <h1>Data & Use Cases Catalog</h1>
                <p class="subtitle">Exploring data-driven solutions for global challenges across agriculture, langauge technology, climate action, energy, and more. Browse our collection of datasets and use cases for AI applications for sustainable development.</p>
            </div>
            <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank">
                <img src="img/fair_forward.png" alt="Fair Forward Logo" class="header-logo">
            </a>
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
        <p>&copy; {datetime.datetime.now().year} Fair Forward - Artificial Intelligence for All</p>
    </footer>
    
    {generate_js_code()}
    
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
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
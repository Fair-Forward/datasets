import pandas as pd
import html
import os
import re
import markdown
from pathlib import Path

# Load the dataset
DATA_CATALOG = "docs/data_catalog.xlsx"
HTML_OUTPUT = "docs/index.html"

def read_markdown_file(filepath):
    """Read and convert markdown file to HTML."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Convert markdown to HTML
            html_content = markdown.markdown(content)
            return html_content
    except Exception as e:
        print(f"Warning: Could not read markdown file {filepath}: {e}")
        return None

# Read Excel File
try:
    df = pd.read_excel(DATA_CATALOG)
except FileNotFoundError:
    print(f"Error: {DATA_CATALOG} not found.")
    exit(1)
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit(1)

def normalize_label(text):
    """Convert text to lowercase and remove special characters."""
    if pd.isna(text):
        return ""
    base = text.lower().strip()
    # Extract the main type from parentheses if present
    if "(" in base:
        base = base.split("(")[0].strip()
    return base.replace(" ", "").replace(",", "").replace(".", "")

def create_label_html(text, category):
    """Create HTML for a label."""
    if pd.isna(text):
        return ""
    normalized = normalize_label(text)
    return f'<span class="label label-{normalized}">{text}</span>'

# Define columns that need special hyperlink formatting
link_columns = {
    "Link to Dataset": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Link</a>' if pd.notna(x) else "N/A",
    "Documentation": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Details</a>' if pd.notna(x) else "N/A",
    "Use-Case": lambda x: create_use_case_link(x) if pd.notna(x) else "N/A"
}

def create_use_case_link(filepath):
    """Create a link with preview for use-case markdown files."""
    if not isinstance(filepath, str):
        return "N/A"
    
    # Read the markdown content
    content = read_markdown_file(filepath)
    if content:
        preview_id = f"preview-{hash(filepath)}"
        return f'''
            <div class="use-case-container">
                <a href="{filepath}" target="_blank" class="minimal-link use-case-link" 
                   data-preview-id="{preview_id}">Use-Case</a>
                <div class="preview-popup" id="{preview_id}">
                    <div class="preview-content markdown-body">
                        {content}
                    </div>
                </div>
            </div>
        '''
    return f'<a href="{filepath}" target="_blank" class="minimal-link">Use-Case</a>'

def convert_markdown_links_to_html(text):
    if not text or not isinstance(text, str):
        return text
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    return re.sub(link_pattern, r'<a href="\2" target="_blank" class="minimal-link">\1</a>', text)

def get_unique_labels(df, column):
    """Get unique labels from a column that may contain multiple comma-separated values."""
    if column not in df.columns:
        return []
    labels = set()
    for value in df[column].dropna():
        if isinstance(value, str):
            for label in value.split(", "):
                labels.add(label.strip())
    return sorted(list(labels))

# Get unique values for filters
data_types = get_unique_labels(df, "Data Type")
domains = get_unique_labels(df, "SDG/Domain")

# Create filter controls HTML
def create_filter_controls():
    datatype_labels = "".join([create_label_html(dtype, "datatype") for dtype in data_types])
    domain_labels = "".join([create_label_html(domain, "domain") for domain in domains])
    
    return """
<div class="filter-controls">
    <div class="filter-section">
        <div class="filter-title">Filter by Data Type</div>
        <div class="filter-group" data-filter-group="datatype">
            {datatype_labels}
        </div>
    </div>
    <div class="filter-section">
        <div class="filter-title">Filter by Domain</div>
        <div class="filter-group" data-filter-group="domain">
            {domain_labels}
        </div>
    </div>
    <button class="reset-filters" onclick="resetFilters()">Reset Filters</button>
</div>
<div class="empty-state">No matching datasets found. Try adjusting your filters.</div>
""".format(datatype_labels=datatype_labels, domain_labels=domain_labels)

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
    <!-- GitHub Markdown CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css">
</head>
<body>
    <header>
        <div class="container d-flex align-items-center justify-content-between">
            <div class="header-text">
                <h1 class="mb-3">Data Catalog</h1>
                <p class="text-muted">An overview of datasets and resources funded by Fair Forward</p>
            </div>
            <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank">
                <img src="img/fair_forward.png" alt="Fair Forward Logo" class="header-logo mx-3">
            </a>
        </div>
    </header>

    <div class="container my-5">
        {filters}
        {table}
    </div>

    <footer class="bg-light py-4 mt-5">
        <div class="container">
            <p class="mb-0 text-muted">&copy; 2024 Fair Forward</p>
        </div>
    </footer>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Preview functionality
        const useCase = document.querySelectorAll('.use-case-link');
        useCase.forEach(link => {
            const previewId = link.getAttribute('data-preview-id');
            const preview = document.getElementById(previewId);
            if (!preview) return;  // Skip if preview element doesn't exist
            let timeout;

            link.addEventListener('mouseenter', () => {
                timeout = setTimeout(() => {
                    preview.style.display = 'block';
                    const linkRect = link.getBoundingClientRect();
                    const previewRect = preview.getBoundingClientRect();
                    
                    if (linkRect.right + previewRect.width > window.innerWidth) {
                        preview.style.left = 'auto';
                        preview.style.right = '0';
                    } else {
                        preview.style.left = '0';
                        preview.style.right = 'auto';
                    }
                }, 200);
            });

            link.addEventListener('mouseleave', () => {
                clearTimeout(timeout);
                setTimeout(() => {
                    if (!preview.matches(':hover')) {
                        preview.style.display = 'none';
                    }
                }, 100);
            });

            preview.addEventListener('mouseleave', () => {
                preview.style.display = 'none';
            });
        });

        // Filtering functionality
        const filterLabels = document.querySelectorAll('.filter-label');
        const tableRows = document.querySelectorAll('table tbody tr');
        const emptyState = document.querySelector('.empty-state');
        let activeFilters = {
            datatype: new Set(),
            domain: new Set()
        };

        filterLabels.forEach(label => {
            label.addEventListener('click', () => {
                const filterGroup = label.closest('[data-filter-group]').dataset.filterGroup;
                const filterValue = label.textContent.trim();

                if (label.classList.contains('active')) {
                    label.classList.remove('active');
                    activeFilters[filterGroup].delete(filterValue);
                } else {
                    label.classList.add('active');
                    activeFilters[filterGroup].add(filterValue);
                }

                applyFilters();
            });
        });

        function applyFilters() {
            let visibleRows = 0;

            tableRows.forEach(row => {
                const datatypes = row.querySelector('[data-types]')?.dataset.types.split(',') || [];
                const domains = row.querySelector('[data-domains]')?.dataset.domains.split(',') || [];

                const matchesDataType = activeFilters.datatype.size === 0 || 
                    [...activeFilters.datatype].some(filter => datatypes.includes(filter));
                const matchesDomain = activeFilters.domain.size === 0 || 
                    [...activeFilters.domain].some(filter => domains.includes(filter));

                if (matchesDataType && matchesDomain) {
                    row.classList.remove('filtered-out');
                    visibleRows++;
                } else {
                    row.classList.add('filtered-out');
                }
            });

            emptyState.classList.toggle('visible', visibleRows === 0);
        }

        window.resetFilters = function() {
            filterLabels.forEach(label => label.classList.remove('active'));
            activeFilters.datatype.clear();
            activeFilters.domain.clear();
            applyFilters();
        };
    });
    </script>
</body>
</html>
"""

# Generate the table header
header_html = "<tr>" + "".join(
    [
        f"<th class='project-title' title='{html.escape(col)}'>{html.escape(col)}</th>" if col == "Project Title" 
        else f"<th class='standard-column' title='{html.escape(col)}'>{html.escape(col)}</th>"
        for col in df.columns
    ]
) + "</tr>"

rows = []
for _, row in df.iterrows():
    row_data = []
    for col in df.columns:
        cell_value = row[col]
        if col in link_columns:
            link_html = link_columns[col](cell_value)
            row_data.append(f"<td class='standard-column' title='{html.escape(str(cell_value))}'>{link_html}</td>")
        elif col == "SDG/Domain":
            labels = str(cell_value).split(", ") if pd.notna(cell_value) else []
            label_html = " ".join([create_label_html(label, "domain") for label in labels])
            row_data.append(
                f"<td class='standard-column' title='{html.escape(str(cell_value))}' data-domains='{",".join(labels)}'>{label_html}</td>"
            )
        elif col == "Data Type":
            types = str(cell_value).split(", ") if pd.notna(cell_value) else []
            type_html = " ".join([create_label_html(dtype, "datatype") for dtype in types])
            row_data.append(
                f"<td class='standard-column' title='{html.escape(str(cell_value))}' data-types='{",".join(types)}'>{type_html}</td>"
            )
        else:
            cell_content = str(cell_value) if pd.notna(cell_value) else "N/A"
            cell_content = convert_markdown_links_to_html(cell_content)
            if col == "Project Title":
                row_data.append(
                    f"<td class='project-title' title='{html.escape(cell_content, quote=True)}'>{cell_content}</td>"
                )
            else:
                row_data.append(f"<td class='standard-column' title='{html.escape(cell_content, quote=True)}'>{cell_content}</td>")
    rows.append(f"<tr>{''.join(row_data)}</tr>")

# Construct the table
table_html = f"<table class='table table-hover custom-table'><thead>{header_html}</thead><tbody>{''.join(rows)}</tbody></table>"

# Create the complete HTML
filter_controls_html = create_filter_controls()
output_html = HTML_TEMPLATE.format(filters=filter_controls_html, table=table_html)

try:
    with open(HTML_OUTPUT, "w") as file:
        file.write(output_html)
    print("HTML file generated successfully.")
except Exception as e:
    print(f"Error writing HTML file: {e}")

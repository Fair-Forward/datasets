import pandas as pd
import html
import os
import re

# Load the dataset
DATA_CATALOG = "docs/data_catalog.xlsx"
HTML_OUTPUT = "docs/index.html"

# Read Excel File
try:
    df = pd.read_excel(DATA_CATALOG)
except FileNotFoundError:
    print(f"Error: {DATA_CATALOG} not found.")
    exit(1)
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit(1)

# Specify columns to exclude
excluded_columns = [
    'Documentation', 
    'Use-Case',
]

# Keep all columns except excluded ones
display_columns = [col for col in df.columns if col not in excluded_columns]

# Apply the column selection
df = df[display_columns]

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
    return f'<span class="label label-{normalized}" data-filter="{text}">{text}</span>'

# Define columns that need special hyperlink formatting
link_columns = {
    "Link to Dataset": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Link</a>' if pd.notna(x) else "N/A",
    "Documentation": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Details</a>' if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Use-Case</a>' if pd.notna(x) else "N/A"
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
        {table}
        <div class="empty-state">No matching datasets found. Click any label again to remove the filter.</div>
    </div>

    <footer class="bg-light py-4 mt-5">
        <div class="container">
            <p class="mb-0 text-muted">&copy; 2024 Fair Forward</p>
        </div>
    </footer>

    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Filter functionality
        const labels = document.querySelectorAll('.label');
        const tableRows = document.querySelectorAll('.custom-table tbody tr');
        const emptyState = document.querySelector('.empty-state');
        let activeFilter = null;

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

                // Apply the filter
                let visibleRows = 0;
                tableRows.forEach(row => {{
                    if (!activeFilter) {{
                        row.classList.remove('filtered-out');
                        visibleRows++;
                    }} else {{
                        const hasMatch = row.textContent.includes(activeFilter);
                        if (hasMatch) {{
                            row.classList.remove('filtered-out');
                            visibleRows++;
                        }} else {{
                            row.classList.add('filtered-out');
                        }}
                    }}
                }});

                // Toggle empty state message
                emptyState.classList.toggle('visible', visibleRows === 0);
            }});
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
    }});
    </script>
</body>
</html>
"""

# Generate the table header
header_html = "<tr>"
for col in df.columns:
    header_class = 'project-title' if col == 'Project Title' else 'description-column' if col == 'Description and How to Use it' else 'standard-column'
    header_html += f"<th class='{header_class}'>{col}</th>"
header_html += "</tr>"

# Update the table generation code
rows = []
for _, row in df.iterrows():
    row_data = []
    for col in df.columns:
        cell_value = row[col]
        if col == "Description and How to Use it":
            description_html = create_description_html(cell_value)
            row_data.append(f"<td class='description-column'>{description_html}</td>")
        elif col in link_columns:
            link_html = link_columns[col](cell_value)
            row_data.append(f"<td class='standard-column'>{link_html}</td>")
        elif col == "SDG/Domain":
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
            cell_class = 'project-title' if col == 'Project Title' else 'standard-column'
            row_data.append(f"<td class='{cell_class}'>{cell_content}</td>")
    rows.append(f"<tr>{''.join(row_data)}</tr>")

# Construct the table without Bootstrap classes
table_html = f"<table class='custom-table'><thead>{header_html}</thead><tbody>{''.join(rows)}</tbody></table>"

# Create the complete HTML
output_html = HTML_TEMPLATE.format(table=table_html)

try:
    with open(HTML_OUTPUT, "w") as file:
        file.write(output_html)
    print("HTML file generated successfully.")
except Exception as e:
    print(f"Error writing HTML file: {e}")

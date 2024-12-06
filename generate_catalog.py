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

# Define columns that need special hyperlink formatting (already existing logic)
link_columns = {
    "Link to Dataset": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Link</a>' if pd.notna(x) else "N/A",
    "Documentation": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Details</a>' if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f'<a href="{x}" target="_blank" class="minimal-link">Use-Case</a>' if pd.notna(x) else "N/A"
}

# Function to convert markdown links to HTML links
def convert_markdown_links_to_html(text):
    if not text or not isinstance(text, str):
        return text
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    # Replace markdown links with HTML anchor tags
    return re.sub(link_pattern, r'<a href="\2" target="_blank" class="minimal-link">\1</a>', text)

# HTML Template referencing the external CSS file
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Catalog</title>
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
            <div class="header-logo-container">
                <img src="img/fair_forward.png" alt="Fair Forward Logo" class="header-logo">
            </div>
        </div>
    </header>

    <div class="container my-5">
        {table}
    </div>

    <footer class="bg-light py-4 mt-5">
        <div class="container">
            <p class="mb-0 text-muted">&copy; 2024 Fair Forward</p>
        </div>
    </footer>
</body>
</html>
"""

# Generate table header
header_html = "<tr>" + "".join(
    [
        f"<th class='project-title' title='{html.escape(col)}'>{html.escape(col)}</th>"
        if col == "Project Title" else f"<th class='standard-column' title='{html.escape(col)}'>{html.escape(col)}</th>"
        for col in df.columns
    ]
) + "</tr>"

# Convert DataFrame to HTML table with formatted links
rows = []
for index, row in df.iterrows():
    row_data = []
    for col in df.columns:
        cell_value = row[col]
        if col in link_columns:
            # For known link columns
            link_html = link_columns[col](cell_value)
            row_data.append(f"<td class='standard-column' title='{html.escape(str(cell_value))}'>{link_html}</td>")
        else:
            # For other columns, convert markdown links if present
            cell_content = str(cell_value) if pd.notna(cell_value) else "N/A"
            cell_content = convert_markdown_links_to_html(cell_content)
            # Escape only non-HTML parts if needed. Since we've added <a> tags,
            # we should not re-escape the entire cell_content or we lose anchor tags.
            # Just ensure that no malicious HTML is inserted. If you're confident that the Excel 
            # does not contain malicious HTML, you can trust after conversion.
            
            # Project Title gets a special class
            if col == "Project Title":
                row_data.append(f"<td class='project-title' title='{html.escape(cell_content, quote=True)}'>{cell_content}</td>")
            else:
                row_data.append(f"<td class='standard-column' title='{html.escape(cell_content, quote=True)}'>{cell_content}</td>")
    rows.append(f"<tr>{''.join(row_data)}</tr>")

# Construct complete table HTML
table_html = f"<table class='table table-hover custom-table'><thead>{header_html}</thead><tbody>{''.join(rows)}</tbody></table>"

# Insert the HTML table into the template
output_html = HTML_TEMPLATE.format(table=table_html)

# Write to the HTML file
try:
    with open(HTML_OUTPUT, "w") as file:
        file.write(output_html)
    print("HTML file generated successfully.")
except Exception as e:
    print(f"Error writing HTML file: {e}")

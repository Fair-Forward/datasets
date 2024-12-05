import pandas as pd
import html
import os

# Load the dataset
DATA_CATALOG = "docs/data_catalog.xlsx"
HTML_OUTPUT = "docs/index.md"

# Read Excel File
df = pd.read_excel(DATA_CATALOG)

# Define columns that need special hyperlink formatting
link_columns = {
    "Link to Dataset": lambda x: f"<a href=\"{x}\" target=\"_blank\">Link</a>" if pd.notna(x) else "N/A",
    "Documentation": lambda x: f"<a href=\"{x}\" target=\"_blank\">Details</a>" if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f"<a href=\"{x}\" target=\"_blank\">Use-Case</a>" if pd.notna(x) else "N/A"
}

# Create a mapping to add padding to certain column headers
column_mapping = {col: col + ("&nbsp;" * 30 if col == "Description" else "") for col in df.columns}

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="styles.css">
    <title>Data Catalog</title>
    <!-- Link to Bootstrap for styling -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <!-- Optional: Link to Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
</head>
<body>
    <header class="bg-primary text-white p-4 mb-4">
        <div class="container">
            <h1>Data Catalog</h1>
            <p>An overview of datasets and resources funded by Fair Forward</p>
        </div>
    </header>

    <div class="container">
        {table}
    </div>

    <footer class="bg-secondary text-white p-4 mt-4">
        <div class="container text-center">
            <p>&copy; 2024 Fair Forward</p>
        </div>
    </footer>

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Convert DataFrame to HTML table with formatted links
rows = []
for _, row in df.iterrows():
    row_data = []
    for col in df.columns:
        # Check if the column needs special hyperlink formatting
        if col in link_columns:
            row_data.append(link_columns[col](row[col]))
        else:
            row_data.append(str(row[col]) if pd.notna(row[col]) else "N/A")
    rows.append(f"<tr>{''.join([f'<td>{html.escape(cell)}</td>' for cell in row_data])}</tr>")

# Generate table header
header_html = "<tr>" + "".join([f"<th>{html.escape(column_mapping[col])}</th>" for col in df.columns]) + "</tr>"

# Construct complete table HTML
table_html = f"<table class='table table-striped table-bordered table-hover'><thead>{header_html}</thead><tbody>{''.join(rows)}</tbody></table>"

# Insert the HTML table into the template
output_html = HTML_TEMPLATE.format(table=table_html)

# Write to the markdown file
with open(HTML_OUTPUT, "w") as file:
    file.write(output_html)

print("HTML file generated successfully.")

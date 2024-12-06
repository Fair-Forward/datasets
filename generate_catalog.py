import pandas as pd
import html
import os

# Load the dataset
DATA_CATALOG = "docs/data_catalog.xlsx"
HTML_OUTPUT = "docs/index.html"

# Read Excel File
df = pd.read_excel(DATA_CATALOG)

# Define columns that need special hyperlink formatting
link_columns = {
    "Link to Dataset": lambda x: f"<a href=\"{x}\" target=\"_blank\" class=\"minimal-link\">Link</a>" if pd.notna(x) else "N/A",
    "Documentation": lambda x: f"<a href=\"{x}\" target=\"_blank\" class=\"minimal-link\">Details</a>" if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f"<a href=\"{x}\" target=\"_blank\" class=\"minimal-link\">Use-Case</a>" if pd.notna(x) else "N/A"
}

# HTML Template referencing the external CSS file
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
    <!-- Link to Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
</head>
<body>
    <header>
        <h1>Data Catalog</h1>
        <p>An overview of datasets and resources funded by Fair Forward</p>
    </header>

    <div class="container my-5">
        {table}
    </div>

    <footer class="text-center p-4">
        <p>&copy; 2024 Fair Forward</p>
    </footer>

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Generate table header with an "Action" column
header_html = "<tr>" + "".join(
    [f"<th class='project-title'>{html.escape(col)}</th>" if col == "Project Title" else f"<th>{html.escape(col)}</th>" for col in df.columns]
) + "<th>Action</th></tr>"

# Convert DataFrame to HTML table with formatted links and interactive elements
rows = []
for index, row in df.iterrows():
    row_data = []
    for col in df.columns:
        # Check if the column needs special hyperlink formatting
        if col in link_columns:
            cell_content = link_columns[col](row[col])
        else:
            cell_content = str(row[col]) if pd.notna(row[col]) else "N/A"
        # Add class to "Project Title" column cells
        if col == "Project Title":
            row_data.append(f"<td class='project-title'>{cell_content}</td>")
        else:
            row_data.append(f"<td>{cell_content}</td>")
    # Add action icons
    row_data.append(
        "<td><div class='action-icons'>"
        "<i class='fas fa-edit'></i>"
        "<i class='fas fa-trash-alt'></i>"
        "</div></td>"
    )
    rows.append(f"<tr>{''.join(row_data)}</tr>")

# Construct complete table HTML
table_html = f"<table class='table table-hover table-bordered'><thead>{header_html}</thead><tbody>{''.join(rows)}</tbody></table>"

# Insert the HTML table into the template
output_html = HTML_TEMPLATE.format(table=table_html)

# Write to the HTML file
with open(HTML_OUTPUT, "w") as file:
    file.write(output_html)

print("HTML file generated successfully.")

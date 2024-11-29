import pandas as pd

# Load the Excel file
excel_file = "data_catalog.xlsx"
df = pd.read_excel(excel_file)

# Define columns that need special hyperlink formatting
link_columns = {
    "Link": lambda x: f'<a href="{x}" target="_blank">Link</a>' if pd.notna(x) else "N/A",
    "Documentation": lambda x: f'<a href="{x}" target="_blank">Details</a>' if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f'<a href="{x}" target="_blank">Use-Case</a>' if pd.notna(x) else "N/A"
}

# Open the HTML file for writing
output_file = "data_catalog.html"
with open(output_file, "w") as f:
    # Write the opening HTML structure
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <title>Data Catalog</title>
</head>
<body>
    <h1>Data Catalog</h1>
    <p>Welcome to our organization's data catalog. Below is a list of datasets collected as part of our Fair Forward programme.</p>
    <table id="dataCatalog" class="display">
        <thead>
            <tr>
    """)

    # Write the table headers dynamically based on column names
    for column in df.columns:
        f.write(f"<th>{column}</th>")
    f.write("</tr></thead><tbody>\n")

    # Write each row of the DataFrame as a table row
    for _, row in df.iterrows():
        f.write("<tr>")
        for col in df.columns:
            value = row[col]
            # Apply hyperlink formatting for specific columns
            if col in link_columns:
                f.write(f"<td>{link_columns[col](value)}</td>")
            else:
                f.write(f"<td>{value if pd.notna(value) else 'N/A'}</td>")
        f.write("</tr>\n")

    # Close the table and HTML structure
    f.write("""
        </tbody>
    </table>
    <script>
        $(document).ready(function () {
            $('#dataCatalog').DataTable({
                paging: true,
                searching: true,
                ordering: true,
                pageLength: 10
            });
        });
    </script>
</body>
</html>
    """)

print(f"HTML table generated and saved to {output_file}")

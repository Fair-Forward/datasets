import pandas as pd
import html 

# Load the Excel file
excel_file = "docs/data_catalog.xlsx"
df = pd.read_excel(excel_file)

# Define columns that need special hyperlink formatting
link_columns = {
    "Link to Dataset": lambda x: f"[Link]({x})" if pd.notna(x) else "N/A",
    "Documentation": lambda x: f"[Details]({x})" if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f"[Use-Case]({x})" if pd.notna(x) else "N/A"
}

# Create a mapping to add padding to certain column headers
column_mapping = {col: col + ("&nbsp;" * 30 if col == "Description" else "") for col in df.columns}

# Open the Markdown file for writing
output_file = "docs/index.md"
with open(output_file, "w") as f:
    # if styling options shall be added - add html snippets here:
    #f.write('<link rel="stylesheet" href="assets/css/style.css">')

    # Write the header for the Markdown file
    f.write("\n# Data Catalog\n\n")
    f.write("Welcome to our organization's data catalog. Below is a list of datasets that have been collected throughout our programme Fair Forward.\n\n")

    # Write the Markdown table header dynamically based on modified column names
    f.write("| " + " | ".join(column_mapping[col] for col in df.columns) + " |\n")
    f.write("|" + " | ".join(["-" * len(html.unescape(col)) for col in column_mapping.values()]) + "|\n")


    # Write each row
    for _, row in df.iterrows():
        row_data = []
        for col in df.columns:
            # Check if the column needs special hyperlink formatting
            if col in link_columns:
                row_data.append(link_columns[col](row[col]))
            else:
                row_data.append(str(row[col]) if pd.notna(row[col]) else "N/A")
        # Write the row to the Markdown file
        f.write("| " + " | ".join(row_data) + " |\n")

print(f"Markdown table generated and saved to {output_file}")

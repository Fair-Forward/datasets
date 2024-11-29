import pandas as pd

# Load the Excel file
excel_file = "data_catalog.xlsx"
df = pd.read_excel(excel_file)

# Open the Markdown file for writing
output_file = "index.md"
with open(output_file, "w") as f:
    # Write the header for the Markdown file
    f.write("# Data Catalog\n\n")
    f.write("Welcome to our organization's data catalog. Below is a list of datasets that have been collected throughout our programme Fair Forward.\n\n")

    # Write the Markdown table header
    f.write("| Dataset Name | Year | Description | Dataset Link | Documentation | Use-Case |\n")
    f.write("|--------------|------|-------------|--------------|---------------|----------|\n")

    # Write each row from the Excel file into the Markdown table
    for _, row in df.iterrows():
        f.write(f"| {row['Dataset Name']} | {row['Year']} | {row['Description']} | ")
        f.write(f"[Dataset Link]({row['Link']}) | ")
        f.write(f"[Documentatino]({row['Documentation']}) | ")
        f.write(f"[Use-Case One Pager]({row['Use-Case']}) |\n")

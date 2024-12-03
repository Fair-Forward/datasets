import pandas as pd
import html

# Load the Excel file
excel_file = "data_catalog.xlsx"
df = pd.read_excel(excel_file)

# Define columns that need special hyperlink formatting
link_columns = {
    "Link to Dataset": lambda x: f"[Link]({x})" if pd.notna(x) else "N/A",
    "Documentation": lambda x: f"[Details]({x})" if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f"[Use-Case]({x})" if pd.notna(x) else "N/A"
}

# Open the Markdown file for writing
output_file = "index.md"
with open(output_file, "w") as f:
    # Optional: add HTML styling or CSS links if needed
    f.write('<link rel="stylesheet" href="assets/css/style.css">\n')

    # Write the header for the Markdown file
    f.write("\n# Data Catalog\n\n")
    f.write("Welcome to our organization's data catalog. Below is a list of datasets that have been collected throughout our programme Fair Forward.\n\n")

    # Write the Markdown table header dynamically based on column names
    f.write("| " + " | ".join(df.columns) + " |\n")
    f.write("|" + " | ".join(["-" * len(col) for col in df.columns]) + "|\n")

    # Write each row
    for _, row in df.iterrows():
        row_data = []
        for col in df.columns:
            # Check if the column needs special hyperlink formatting
            if col in link_columns:
                row_data.append(link_columns[col](row[col]))
            elif col == "Description":
                # Option 1: Bullet Points for Description with improved handling
                if pd.notna(row[col]):
                    description_text = html.escape(str(row[col]))
                    # Replace line breaks and ensure description is inline
                    description_text = description_text.replace("\n", " ").replace("\r", " ").replace("  ", " ")
                    bullet_points = "<ul>"
                    for sentence in description_text.split('. '):
                        if sentence.strip():
                            bullet_points += f"<li>{sentence.strip()}</li>"
                    bullet_points += "</ul>"
                    # Ensure the entire description is wrapped in a single line
                    row_data.append(bullet_points.replace("\n", "").replace("\r", ""))
                else:
                    row_data.append("N/A")
            else:
                row_data.append(html.escape(str(row[col])) if pd.notna(row[col]) else "N/A")

        # Write the row to the Markdown file
        f.write("| " + " | ".join(row_data) + " |\n")

print(f"Markdown table generated and saved to {output_file}")

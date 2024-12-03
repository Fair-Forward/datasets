import pandas as pd
import html

# Load the Excel file
excel_file = "data_catalog.xlsx"
df = pd.read_excel(excel_file)

# Define columns that need special hyperlink formatting
link_columns = {
    "Link": lambda x: f"[Link]({x})" if pd.notna(x) else "N/A",
    "Documentation": lambda x: f"[Details]({x})" if pd.notna(x) else "N/A",
    "Use-Case": lambda x: f"[Use-Case]({x})" if pd.notna(x) else "N/A"
}

# Open the Markdown file for writing
output_file = "index.md"
with open(output_file, "w") as f:
    # Optional: add HTML styling or CSS links if needed
    # f.write('<link rel="stylesheet" href="assets/css/style.css">\n')

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

                # Option 1: Bullet Points
                # if pd.notna(row[col]):
                #     bullet_points = "<ul>"
                #     for sentence in str(row[col]).split('. '):
                #         if sentence.strip():
                #             bullet_points += f"<li>{sentence.strip()}</li>"
                #     bullet_points += "</ul>"
                #     row_data.append(bullet_points)

                # Option 2: Tooltip (comment out bullet points if using tooltips)
                if pd.notna(row[col]):
                    tooltip_text = html.escape(str(row[col]).replace("\n", " "))  # Replace line breaks with space
                    tooltip = f'<span title="{tooltip_text}">Hover for details</span>'
                    row_data.append(tooltip)

                else:
                    row_data.append("N/A")
            else:
                row_data.append(str(row[col]) if pd.notna(row[col]) else "N/A")

        # Write the row to the Markdown file
        f.write("| " + " | ".join(row_data) + " |\n")

print(f"Markdown table generated and saved to {output_file}")

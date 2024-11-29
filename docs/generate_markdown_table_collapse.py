import pandas as pd

# Load the Excel file
excel_file = "data_catalog.xlsx"
df = pd.read_excel(excel_file)

# Open the Markdown file for writing
output_file = "index.md"
with open(output_file, "w") as f:
    # Write the header for the Markdown file

    f.write('<link rel="stylesheet" href="assets/css/style.css">')
    f.write("\n# Data Catalog\n\n")
    f.write("Welcome to our organization's data catalog. Below is a list of datasets with expandable documentation for more details.\n\n")

    # Start the collapsible dataset table
    f.write("<div class='dataset-list'>\n")
    for _, row in df.iterrows():
        # Extract dataset details
        dataset_name = row["Dataset Name"]
        year = row["Year"]
        description = row["Description"]
        dataset_link = row["Link"] if pd.notna(row["Link"]) else "N/A"
        documentation = row["Documentation"] if pd.notna(row["Documentation"]) else "N/A"

        # Write each dataset as a collapsible section
        f.write(f"""
<div class="dataset-item">
    <div class="dataset-header">
        <h3>{dataset_name} ({year})</h3>
        <button class="toggle-btn" onclick="toggleContent(this)">▼</button>
    </div>
    <div class="dataset-content" style="display: none;">
        <p><strong>Description:</strong> {description}</p>
        <p><strong>Dataset Link:</strong> <a href="{dataset_link}" target="_blank">{dataset_link}</a></p>
        <p><strong>Documentation:</strong> {documentation}</p>
    </div>
</div>
""")
    f.write("</div>\n")

    # Add the JavaScript toggle functionality
    f.write("""
<script>
function toggleContent(button) {
    const content = button.parentElement.nextElementSibling;
    if (content.style.display === "none") {
        content.style.display = "block";
        button.textContent = "▲";
    } else {
        content.style.display = "none";
        button.textContent = "▼";
    }
}
</script>
    """)

print(f"Markdown file with collapsible elements generated and saved to {output_file}")

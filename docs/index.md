<link rel="stylesheet" href="assets/css/style.css">
# Data Catalog

Welcome to our organization's data catalog. Below is a list of datasets with expandable documentation for more details.

<div class='dataset-list'>

<div class="dataset-item">
    <div class="dataset-header">
        <h3>Crop Analyses: AI for Telangana Agriculture (2022-2024 )</h3>
        <button class="toggle-btn" onclick="toggleContent(this)">▼</button>
    </div>
    <div class="dataset-content" style="display: none;">
        <p><strong>Description:</strong> AI-based crop type map and replication kit</p>
        <p><strong>Dataset Link:</strong> <a href="https://dataexplorer.ts.adex.org.in/dataset/1da21f2b-87f6-4641-81bd-ed6bcd461303" target="_blank">https://dataexplorer.ts.adex.org.in/dataset/1da21f2b-87f6-4641-81bd-ed6bcd461303</a></p>
        <p><strong>Documentation:</strong> datasets-documentation/telangana_crop_data_documentation.md</p>
    </div>
</div>
</div>

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
    
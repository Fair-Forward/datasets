# Data Catalog

Welcome to our organization's data catalog. Below is a list of datasets that have been collected throughout our programme Fair Forward.

You can access the catalog here: [Data Catalog!](https://fair-forward.github.io/datasets/)

> **Note:** This data catalog is currently a prototype and is not yet fully developed. It is intended to showcase the concept and functionality, but may undergo significant changes in the future.

## How to Contribute Data

Want to add your dataset or AI use case to this catalog? Great!

1.  **Access the Source:** The data for this catalog lives in this [Google Sheet](https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456).
2.  **Add Your Project:** Add a new row to the sheet and fill in the details for your project. Please follow the format of existing entries and use the second row as a guide for the expected content in each column.
3.  **Update the Website:** Once you've added your information to the Google Sheet, the website needs to be rebuilt to include it. Please contact one of the repository maintainers or follow the "Update via GitHub Actions" steps above (if you have write access) to trigger an update.

## How to Update the Catalog

The content of this catalog is primarily sourced from a [Google Sheet](https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456). Changes made to the sheet (e.g., adding a new project, updating details) need to be reflected on the website.

There are two main ways to update the website:

1.  **Local Update (for Developers):**
    *   Ensure you have the prerequisites installed (see Development section).
    *   Run the build script locally: `python build_from_google_sheets.py`
    *   This fetches the latest data, generates `docs/index.html`, updates `docs/data_catalog.xlsx`, and creates project files.
    *   Commit and push all changed files (including `index.html`, `.xlsx`, backups, and any new files in `docs/public/projects/`) to the `main` branch.

2.  **Update via GitHub Actions (for Non-Developers with Repo Access):**
    *   This method allows updating the website directly from GitHub without running code locally.
    *   Go to the repository's **Actions** tab on GitHub.
    *   In the left sidebar, click on the "**Manually Update Website from Google Sheets**" workflow.
    *   Above the list of workflow runs, click the "**Run workflow**" dropdown button.
    *   Ensure the "Branch: `main`" is selected.
    *   Click the green "**Run workflow**" button.
    *   The workflow will fetch the latest data from the Google Sheet, rebuild the website, and automatically commit the changes to the `main` branch. The live website will be updated shortly after the workflow completes successfully.


## Development

This repository contains the code for generating a static website that displays a catalog of datasets and use cases. The website is built from data stored in an Excel file or fetched from a Google Spreadsheet. The repository includes both a static HTML generator and a React frontend.

### Prerequisites

- Python 3.6+
- Required packages for main functionality: `pandas`, `openpyxl`, `gspread`, `oauth2client`
- Required packages for placeholder images: `requests`, `python-dotenv`
- Node.js and npm (for React frontend)

You can install the required Python packages with:

```bash
pip install pandas openpyxl gspread oauth2client
pip install -r placeholder_images_requirements.txt
```

### Building the Website

#### From Local Excel File

To build the website from the local Excel file:

```bash
python generate_catalog.py
```

This will read the data from `docs/data_catalog.xlsx` and generate the website in `docs/index.html`. It will also export the data as JSON for the React frontend to `frontend/data.json`.

#### From Google Spreadsheet

To fetch data from Google Spreadsheet and build the website:

```bash
python build_from_google_sheets.py
```

This will:
1. Fetch data from the Google Spreadsheet
2. Save it to `docs/data_catalog.xlsx`
3. Build the website from the Excel file

### Placeholder Images

The repository includes a script to automatically download placeholder images for projects that don't have images yet:

```bash
python download_placeholder_images.py
```

This script:
- Scans all project directories in the data catalog
- Extracts relevant keywords from project metadata
- Searches for images using the Pexels API
- Downloads images and saves them with a "placeholder_" prefix
- Creates metadata files with attribution information

You need a Pexels API key to use this feature. You can set it up in two ways:
- Create a `.env` file with `PEXELS_API_KEY=your_api_key_here`
- Pass the API key as a command-line argument: `python download_placeholder_images.py --api-key YOUR_API_KEY`

For more details, see [placeholder_images_README.md](placeholder_images_README.md).

### React Frontend

The repository also includes a React frontend in the `frontend/` directory. To run the frontend:

```bash
cd frontend
npm install
npm run dev
```

The React app uses the data from `frontend/data.json`, which is generated by the `generate_catalog.py` script.

### Configuration

#### Google Sheets API Credentials

To use the Google Sheets API, you need to set up credentials:

1. Create a service account in the Google Cloud Console
2. Download the JSON key file
3. Save it as `data_sources/google_sheets_api/service_account.json`

#### Command Line Arguments

The `generate_catalog.py` script accepts the following arguments:

- `--input`: Path to the input Excel file (default: `docs/data_catalog.xlsx`)
- `--output`: Path to the output HTML file (default: `docs/index.html`)

The `build_from_google_sheets.py` script accepts the following arguments:

- `--output`: Path to save the Excel file (default: `docs/data_catalog.xlsx`)
- `--credentials`: Path to the Google Sheets API credentials file (default: `data_sources/google_sheets_api/service_account_JN.json`)
- `--backup`: Create a backup of the existing Excel file
- `--skip-fetch`: Skip fetching data from Google Sheets and just build the website

The `download_placeholder_images.py` script accepts these arguments:

- `--api-key`: Pexels API key (can also be set in `.env` file)
- `--limit`: Maximum number of projects to process
- `--force`: Force download even if images already exist
- `--min-width`: Minimum image width
- `--min-height`: Minimum image height
- `--data-file`: Path to data catalog Excel file

### Project Structure

- `generate_catalog.py`: Main script for generating the HTML catalog from Excel data
- `build_from_google_sheets.py`: Script for fetching data from Google Sheets and building the website
- `download_placeholder_images.py`: Script for downloading placeholder images for projects
- `placeholder_images_README.md`: Documentation for the placeholder image feature
- `docs/`: Directory containing the generated website and assets
  - `data_catalog.xlsx`: Excel file containing the dataset information
  - `index.html`: Generated HTML file for the website
  - `enhanced_side_panel.js` and `enhanced_side_panel.css`: Styling and functionality for the side panel
  - `public/projects/`: Directory containing project-specific data and images
- `frontend/`: Directory containing the React frontend
  - `src/`: React source code
  - `data.json`: Data exported from the Excel file for the React app
- `data_sources/`: Directory containing scripts and credentials for data sources

### GitHub Actions

This repository uses GitHub Actions:

- `.github/workflows/update_from_google_sheets.yml`: **Manually triggered** workflow to fetch data from Google Sheets, build the website (`docs/index.html`), and commit changes to the `main` branch.
- `.github/workflows/monthly_backup.yml`: **Automatically triggered** workflow (1st of the month) to create a raw CSV backup of the Google Sheet data.

### Features

The data catalog includes the following features:

- Modern UI with a clean, responsive layout
- Filtering by domain, data type, and region
- Search functionality for finding specific datasets or use cases
- Visual distinction between domains and data types
- Detailed information for each dataset and use case
- Links to external resources for datasets and use cases
- Enhanced side panel for displaying detailed project information
- Automatic placeholder images for projects without custom images
- React frontend for a more interactive user experience

### Contributing (Code)

If you would like to contribute *code changes* to this project, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request

Please ensure that your code follows the existing style and includes appropriate documentation.

## License

This project is licensed under the terms of the LICENSE file included in the repository.
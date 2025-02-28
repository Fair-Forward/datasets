# Data Catalog

Welcome to our organization's data catalog. Below is a list of datasets that have been collected throughout our programme Fair Forward.

You can access the catalog here: [Data Catalog!](https://fair-forward.github.io/datasets/)

## Development

This repository contains the code for generating a static website that displays a catalog of datasets. The website is built from data stored in an Excel file or fetched from a Google Spreadsheet.

### Prerequisites

- Python 3.6+
- Required packages: `pandas`, `openpyxl`, `gspread`, `oauth2client`

You can install the required packages with:

```bash
pip install pandas openpyxl gspread oauth2client
```

### Building the Website

#### From Local Excel File

To build the website from the local Excel file:

```bash
python generate_catalog.py
```

This will read the data from `docs/data_catalog.xlsx` and generate the website in `docs/index.html`.

#### From Google Spreadsheet

To fetch data from Google Spreadsheet and build the website:

```bash
python build_from_google_sheets.py
```

This will:
1. Fetch data from the Google Spreadsheet
2. Save it to `docs/data_catalog.xlsx`
3. Build the website from the Excel file

You can also run these steps separately:

```bash
# Fetch data from Google Spreadsheet
python fetch_google_sheet.py

# Build the website from the Excel file
python generate_catalog.py
```

### Configuration

#### Google Sheets API Credentials

To use the Google Sheets API, you need to set up credentials:

1. Create a service account in the Google Cloud Console
2. Download the JSON key file
3. Save it as `data_sources/google_sheets_api/service_account_JN.json`

#### Command Line Arguments

Both `fetch_google_sheet.py` and `build_from_google_sheets.py` accept the following arguments:

- `--output`: Path to save the Excel file (default: `docs/data_catalog.xlsx`)
- `--credentials`: Path to the Google Sheets API credentials file (default: `data_sources/google_sheets_api/service_account_JN.json`)
- `--no-backup`: Do not create a backup of the existing Excel file

`build_from_google_sheets.py` also accepts:

- `--skip-fetch`: Skip fetching data from Google Sheets and just build the website

### GitHub Actions

This repository uses GitHub Actions to automatically build and deploy the website:

- `.github/workflows/update_markdown.yml`: Builds the website from the local Excel file when changes are pushed
- `.github/workflows/update_from_google_sheets.yml`: Fetches data from Google Sheets and builds the website on a schedule

### Branch Strategy

- `main`: The main branch that contains the production website
- `feature/new-dataset`: A branch for testing the new Google Sheets integration
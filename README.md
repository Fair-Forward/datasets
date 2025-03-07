# Data Catalog

Welcome to our organization's data catalog. Below is a list of datasets that have been collected throughout our programme Fair Forward.

You can access the catalog here: [Data Catalog!](https://fair-forward.github.io/datasets/)

> **Note:** This data catalog is currently a prototype and is not yet fully developed. It is intended to showcase the concept and functionality, but may undergo significant changes in the future.

## Development

This repository contains the code for generating a static website that displays a catalog of datasets and use cases. The website is built from data stored in an Excel file or fetched from a Google Spreadsheet.

### Prerequisites

- Python 3.6+
- Required packages: `pandas`, `openpyxl`, `gspread`, `oauth2client`, `colorsys`

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

### Project Structure

- `generate_catalog.py`: Main script for generating the HTML catalog from Excel data
- `build_from_google_sheets.py`: Script for fetching data from Google Sheets and building the website
- `docs/`: Directory containing the generated website and assets
  - `data_catalog.xlsx`: Excel file containing the dataset information
  - `index.html`: Generated HTML file for the website
  - `img/`: Directory containing images for the datasets
- `data_sources/`: Directory containing scripts and credentials for data sources

### GitHub Actions

This repository uses GitHub Actions to automatically build and deploy the website:

- `.github/workflows/update_markdown.yml`: Builds the website from the local Excel file when changes are pushed
- `.github/workflows/update_from_google_sheets.yml`: Fetches data from Google Sheets and builds the website on a schedule

### Features

The data catalog includes the following features:

- Modern UI with a clean, responsive layout
- Filtering by domain, data type, and region
- Search functionality for finding specific datasets or use cases
- Visual distinction between domains and data types
- Detailed information for each dataset and use case
- Links to external resources for datasets and use cases

### Contributing

If you would like to contribute to this project, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request

Please ensure that your code follows the existing style and includes appropriate documentation.
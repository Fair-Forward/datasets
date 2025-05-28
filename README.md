# Data Catalog

Welcome to our organization's data and use-case catalog. Below is a list of datasets and use-cases that have been collected throughout our programme Fair Forward. 

You can access the live website here: [Data Catalog!](https://fair-forward.github.io/datasets/)

> **Note:** This data catalog is currently a prototype and is not yet fully developed. It is intended to showcase the concept and functionality, but may undergo significant changes in the future.

## How to Contribute Data

Want to add your dataset or AI use case to this catalog? Great!

1.  **Access the Source:** The data for this catalog lives in this [Google Sheet](https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456).
2.  **Add Your Project:** Add a new row to the sheet and fill in the details for your project. Please follow the format of existing entries and use the second row as a guide for the expected content in each column.
3.  **Update the Website:** Once you've added your information to the Google Sheet, the website needs to be rebuilt to include it. Please contact one of the repository maintainers or follow the "Update via GitHub Actions" steps below (if you have write access) to trigger an update.

## How to Update the Catalog

The content of this catalog is primarily sourced from the Google Sheet mentioned above. Changes made there need to be reflected on the website.

There are two main ways to update the website:

1.  **Local Update (for Developers):**
    *   Ensure you have the prerequisites installed (see Development section).
    *   Run the main build script locally: `python scripts/build_from_google_sheets.py`
    *   This single script fetches the latest data, applies necessary processing (like fuzzy column matching), saves the intermediate `docs/data_catalog.xlsx`, creates/updates project markdown files in `docs/public/projects/`, generates the final `docs/index.html`, and saves a daily backup CSV to `data_sources/google_sheets_backup/`.
    *   Optionally, run `python scripts/download_placeholder_images.py` if new projects need placeholder images (requires Pexels API key setup).
    *   Commit and push all changed files (including `index.html`, `.xlsx`, backups, and any new/modified files in `docs/public/projects/`) to the `main` branch.

2.  **Update via GitHub Actions (for Non-Developers with Repo Access):**
    *   This method allows updating the website directly from GitHub without running code locally.
    *   Go to the repository's **Actions** tab on GitHub.
    *   In the left sidebar, click on the "**Manually Update Website from Google Sheets**" workflow.
    *   Above the list of workflow runs, click the "**Run workflow**" dropdown button.
    *   Ensure the "Branch: `main`" is selected.
    *   Click the green "**Run workflow**" button.
    *   The workflow will perform the same steps as running `scripts/build_from_google_sheets.py` locally, fetching the latest data, rebuilding the website, and automatically committing the changes to the `main` branch. The live website will be updated shortly after the workflow completes successfully. (Note: This action does not currently run the placeholder image download script).

## Analytics System

This repository includes a comprehensive open-source analytics system for tracking user interactions with the data catalog. The analytics system is privacy-focused and designed to provide insights into how users engage with datasets and use cases.

### Analytics Features

- **Privacy-Focused Tracking**: Designed with user privacy in mind, compatible with GDPR and other privacy regulations
- **Comprehensive Event Tracking**: Tracks page views, card clicks, search terms, filter usage, and external link clicks
- **Interactive Dashboard**: Visual analytics dashboard with charts showing usage patterns and trends
- **Sample Data Generation**: Ability to generate sample data for testing and demonstration purposes
- **Local Storage**: Events are stored locally for reliability and can be batch-sent to analytics services
- **Umami Integration**: Ready for integration with Umami Analytics or other privacy-focused analytics platforms

### Analytics Components

1. **Frontend Tracking** (`docs/umami-analytics.js`): JavaScript class that tracks user interactions
2. **Data Collection** (`data_sources/analytics/collect_analytics.py`): Aggregates analytics data from multiple sources
3. **Dashboard Generation** (`data_sources/analytics/analytics_dashboard.py`): Creates interactive HTML dashboard
4. **Configuration** (`data_sources/analytics/analytics_config.json`): Centralized analytics settings
5. **Automated Updates** (`.github/workflows/analytics_update.yml`): Daily scheduled data collection and dashboard updates

### Viewing Analytics

The analytics dashboard is available at `/analytics.html` on the website. It provides:
- Overview statistics (total events, unique sessions, popular datasets)
- Interactive charts showing trends over time
- Breakdown by event types, domains, and regions
- Search term analysis and filter usage patterns

### Analytics Status

**Current Status**: The analytics tracking script is temporarily disabled to prevent conflicts with the main website functionality. The analytics system is fully implemented and ready to be re-enabled once event listener conflicts are resolved.

To view sample analytics data, visit the dashboard at `http://localhost:8000/analytics.html` when running the local server.

## Development

This repository contains the code for generating a static website data catalog.

### Prerequisites

- Python 3.7+ (due to `thefuzz` dependency)
- Required Python packages are listed in `requirements.txt`.
- Node.js and npm (Optional: only needed for the React frontend development)

Install Python packages with:
```bash
pip install -r requirements.txt
```

### Building the Website Locally

The primary script handles fetching data and building the site:
```bash
python scripts/build_from_google_sheets.py
```
This script:
1. Fetches data from the Google Spreadsheet.
2. Performs fuzzy matching on column headers.
3. Saves the processed data to `docs/data_catalog.xlsx`.
4. Creates/updates markdown documentation files in `docs/public/projects/*/docs/`.
5. Creates/updates project image folders in `docs/public/projects/*/images/`.
6. Saves a daily raw backup to `data_sources/google_sheets_backup/`.
7. Runs `scripts/generate_catalog.py` internally to build `docs/index.html`.

If you only want to regenerate the HTML from the existing `docs/data_catalog.xlsx` without fetching from Google Sheets, you can run:
```bash
python scripts/generate_catalog.py
```

### Analytics Development

To work with the analytics system:

1. **Generate Sample Data:**
   ```bash
   python data_sources/analytics/collect_analytics.py --sample
   ```

2. **Create Analytics Dashboard:**
   ```bash
   python data_sources/analytics/analytics_dashboard.py
   ```

3. **Test Analytics Locally:**
   - Start local server: `cd docs && python -m http.server 8000`
   - Visit `http://localhost:8000/analytics.html` to view the dashboard
   - Visit `http://localhost:8000` to test the main website

### Placeholder Images

To download placeholder images for projects lacking them:
```bash
python scripts/download_placeholder_images.py
```
This requires a Pexels API key. Set it up via:
- A `.env` file in the root directory: `PEXELS_API_KEY=your_api_key_here`
- Command-line argument: `--api-key YOUR_API_KEY`

(Note: The `scripts/download_placeholder_images.py` script uses `requirements.txt` for its dependencies.)

### React Frontend (Experimental)

The `frontend/` directory contains an experimental React frontend. It uses data from `frontend/data.json`, generated by `scripts/generate_catalog.py`.

To run:
```bash
cd frontend
npm install
npm run dev
```

### Configuration

#### Google Sheets API Credentials

1. Create a Google Cloud service account.
2. Download its JSON key file.
3. Save it as `data_sources/google_sheets_api/service_account_JN.json` (or match the path used in scripts/workflows).
4. Ensure this file is listed in `.gitignore` and **never commit it**.

#### Pexels API Key

Needed for `scripts/download_placeholder_images.py`. Set via `.env` file or `--api-key` argument.

#### Analytics Configuration

Analytics settings can be configured in `data_sources/analytics/analytics_config.json`:
- Enable/disable different types of tracking
- Set privacy options
- Configure data retention periods
- Customize dashboard appearance

### Project Structure

```
├── data_sources/
│   ├── analytics/                    # Analytics system files
│   │   ├── collect_analytics.py      # Data collection script
│   │   ├── analytics_dashboard.py    # Dashboard generation
│   │   ├── analytics_config.json     # Analytics configuration
│   │   ├── analytics_data.json       # Collected analytics data
│   │   └── ANALYTICS_README.md       # Analytics documentation
│   ├── google_sheets_api/            # Google Sheets API credentials
│   │   └── service_account_JN.json   # Service account file (ignored by git)
│   └── google_sheets_backup/         # Daily and monthly raw CSV backups
├── scripts/                          # Build and utility scripts
│   ├── build_from_google_sheets.py   # Main build script
│   ├── generate_catalog.py           # HTML catalog generator
│   ├── download_placeholder_images.py # Image download utility
│   ├── backup_google_sheet.py        # Backup utility
│   └── placeholder_images_README.md  # Image documentation
├── docs/                             # Generated website files
│   ├── data_catalog.xlsx             # Processed data from Google Sheets
│   ├── index.html                    # Main website (GitHub Pages)
│   ├── analytics.html                # Analytics dashboard
│   ├── umami-analytics.js             # Analytics tracking script
│   ├── enhanced_side_panel.js         # Side panel functionality
│   ├── enhanced_side_panel.css        # Side panel styles
│   └── public/projects/              # Project-specific files
├── frontend/                         # Experimental React frontend
├── .github/workflows/                # GitHub Actions
│   ├── update_from_google_sheets.yml # Manual website update
│   ├── monthly_backup.yml            # Monthly backup automation
│   └── analytics_update.yml          # Daily analytics collection
└── requirements.txt                  # Python dependencies
```

### GitHub Actions

- `.github/workflows/update_from_google_sheets.yml`: **Manually triggered** workflow to run `scripts/build_from_google_sheets.py` and commit results to `main`.
- `.github/workflows/monthly_backup.yml`: **Automatically triggered** workflow (1st of month) to run `scripts/backup_google_sheet.py` and commit the monthly raw CSV backup.
- `.github/workflows/analytics_update.yml`: **Daily triggered** workflow to collect analytics data and update the dashboard.

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
- **Privacy-focused analytics system** with interactive dashboard
- **Real-time usage tracking** and insights
- **Automated data collection** and reporting

### Contributing (Code)

If you would like to contribute *code changes* to this project, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/YourFeature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/YourFeature`)
6. Create a new Pull Request

Please ensure that your code follows the existing style and includes appropriate documentation.

## License

This project is licensed under the terms of the LICENSE file included in the repository.
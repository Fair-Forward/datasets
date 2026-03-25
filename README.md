# Fair Forward Data Catalog

Live site: **https://fair-forward.github.io/datasets/**

An open catalog of datasets and AI use cases for international development, maintained by the [FAIR Forward](https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/) initiative.

---

## Update the website (no coding required)

If you've added or edited data in the [Google Sheet](https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=756053104#gid=756053104), you can publish your changes to the live site in a few clicks:

1. Go to the repository on GitHub: [Fair-Forward/datasets](https://github.com/Fair-Forward/datasets)
2. Click the **Actions** tab at the top
3. In the left sidebar, click **"Manually Update Website from Google Sheets"**
4. Click the **"Run workflow"** button (top right of the workflow list)
5. Make sure the branch is set to **main**, then click the green **"Run workflow"** button
6. Wait 1-2 minutes. The workflow will:
   - Fetch the latest data from the Google Sheet
   - Run data quality checks and write feedback notes into the sheet
   - Rebuild the website
   - Deploy to GitHub Pages
7. Once the green checkmark appears, the live site is updated

> **Tip:** After the build, check the Google Sheet for cells with small black triangles in the corner. Hover over them to see quality feedback (e.g., missing descriptions, license format suggestions).

---

## How the data works

### Source of truth

All project data lives in the [Google Sheet](https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=756053104#gid=756053104). Anyone with edit access can add or update entries. The build pipeline fetches this data, validates it, and generates the website.

### What makes a project appear in the catalog

A row appears on the website when **any** of these are true:
- The **Dataset Link** or **Model/Use-Case Links** column contains an `http(s)` URL
- Either link column starts with `"Dataset/Use-Case has not been published yet."` or `"There is no Dataset/Use-Case available."`
- The project folder at `public/projects/<id>/documents/` contains at least one file

### Data quality checks

The build automatically scores each project (0-100) based on how complete its information is. Projects with richer documentation appear higher in the catalog. The scoring considers: title, description, links, data characteristics, how-to-use guidance, license, SDGs, countries, data types, and images.

Quality feedback is written back to the Google Sheet as cell notes (small black triangle in the cell corner, visible on hover). These notes suggest improvements like adding missing descriptions or using standard license formats.

### Uploading PDFs or documents

Place files in `public/projects/<project_id>/documents/`. These will appear as download buttons on the project's detail page.

---

## Local development

### Prerequisites

- Python 3.x
- Node.js (for Vite / React)
- Google Sheets service account JSON (for full sync)

### Setup

```bash
# Create Python environment
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
npm install
```

Create a local `.env` file (gitignored):
```
GOOGLE_APPLICATION_CREDENTIALS=./data_sources/google_sheets_api/service_account_JN.json
```
Place your service account JSON at that path. Never commit it.

### Build commands

```bash
# Full pipeline: fetch Google Sheet -> validate -> build website
python scripts/build_and_sync.py

# Rebuild from existing Excel (no Google Sheets fetch)
python scripts/build.py

# Just regenerate JSON from Excel
python scripts/generate_catalog_data.py

# Run data quality validation only
python scripts/validate_data.py

# Dev server with hot reload
npm run dev
```

### Scripts overview

| Script | Purpose |
|---|---|
| `scripts/build_and_sync.py` | Full pipeline: fetch sheet, create project dirs, validate, build site |
| `scripts/build.py` | Rebuild from existing `docs/data_catalog.xlsx` (no fetch) |
| `scripts/generate_catalog_data.py` | Excel -> `public/data/catalog.json` |
| `scripts/generate_insights_data.py` | Excel -> `public/data/insights.json` |
| `scripts/validate_data.py` | Run quality checks, generate report, optionally write notes to sheet |

---

## Deployment

The `docs/` folder is the static build output. GitHub Pages serves directly from `docs/` on the `main` branch. Any push to `main` that changes `docs/` will update the live site.

---

## Contributing

PRs welcome. Follow existing code style and keep secrets out of git.

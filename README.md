# Data Catalog

Live: https://fair-forward.github.io/datasets/

## Quick start (local)
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Front-end dev server (Vite):
```bash
npm install      # one-time per clone (or after deleting node_modules)
npm run dev      # starts Vite (uses node_modules/.bin/vite)
```

Create a local `.env` (gitignored):
```
GOOGLE_APPLICATION_CREDENTIALS=./data_sources/google_sheets_api/service_account_JN.json
PEXELS_API_KEY=your_pexels_key   # optional, for placeholder images
```
Place your service account JSON at that path (do not commit it).

Build end-to-end from Google Sheets:
```bash
python scripts/build_from_google_sheets.py
```
Rebuild from existing `docs/data_catalog.xlsx` (no Sheets fetch):
```bash
python scripts/build.py
```

## Contribute data
1. Add or update rows in the source Google Sheet: https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456  
2. Run the build locally (above) or trigger the GitHub Action “Manually Update Website from Google Sheets” on branch `main`.

### No public dataset/use-case link yet (Info)
If both link columns have no `http(s)` URL, a row is listed only when **one** of these holds:

- Either cell **starts with** `Dataset/Use-Case has not been published yet.` (coming soon), or  
- Either cell **starts with** `There is no Dataset/Use-Case available.` (not public), or  
- `public/projects/<project_id>/documents/` contains at least one file (then column text is optional; download buttons still appear).

Other no-link notes without those prefixes are **omitted** from the catalog. If either column has a real `http(s)` URL, the project is a normal dataset/use-case entry.

### PDFs per project
Put files in `public/projects/<project_id>/documents/`. You can still link the same files from **Link to additional Resources**. Sheet builds try to move `documents/` when a project folder is renamed or merged.

## Secrets & safety
- Service account keys stay local (ignored by git). Never commit JSON keys.
- If a key was ever committed, rotate it in Google Cloud and update your local `.env` path.
- Pexels API key is only needed for `scripts/download_placeholder_images.py`.

## Scripts
- `scripts/build_from_google_sheets.py` — fetch Sheet, generate markdown/JSON, run Vite build to `docs/`.
- `scripts/build.py` — regenerate JSON + Vite build from existing `docs/data_catalog.xlsx`.
- `scripts/download_placeholder_images.py` — optional placeholders (needs `PEXELS_API_KEY`).

## Deploy
`docs/` is the static output (Vite). GitHub Pages serves from `docs/`. Running the build scripts updates it. The GitHub Action “Manually Update Website from Google Sheets” can do this without local setup.

## Contributing (code)
PRs welcome; follow existing style and keep secrets out of git.
 

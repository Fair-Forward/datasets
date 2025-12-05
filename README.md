# Data Catalog

Live: https://fair-forward.github.io/datasets/

## Quick start (local)
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
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
 

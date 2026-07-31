# Fair Forward Data Catalog

Live site: **https://fair-forward.github.io/datasets/**

An open catalog of datasets and AI use cases for international development, maintained by the [FAIR Forward](https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/) initiative.

---

## Update the website (no coding required)

If you've added or edited data in the [Google Sheet](https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=756053104#gid=756053104), you can publish your changes to the live site without any coding.

### External partners (no GitHub account needed)

Use the trigger page: **https://fair-forward.github.io/datasets/trigger.html**

Click **"Update Website Now"** and wait 1-2 minutes. You can monitor progress via the link on that page.

### Team members (GitHub account)

1. Go to the repository on GitHub: [Fair-Forward/datasets](https://github.com/Fair-Forward/datasets)
2. Click the **Actions** tab at the top
3. In the left sidebar, click **"Manually Update Website from Google Sheets"**
4. Click the **"Run workflow"** button (top right of the workflow list)
5. Make sure the branch is set to **main**, then click the green **"Run workflow"** button
6. Wait 1-2 minutes for the build to complete

Either way, the workflow will:
- Fetch the latest data from the Google Sheet
- Run data quality checks and write feedback notes into the sheet
- Rebuild the website and deploy to GitHub Pages

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

The build automatically scores each project (0-100) based on how complete its information is — title, description, links, data and model characteristics, how-to-use guidance, license, SDGs, countries, data types, and maturity. Cards are then ordered by this documentation score, nudged by the weekly health signal: projects with recent activity or many downloads/stars rank a little higher, and entries whose links no longer resolve rank lower. Documentation completeness stays the main driver, and projects without GitHub/Hugging Face activity data are never penalised for lacking it. See `docs/health-thresholds.md` for the exact methodology.

Quality feedback is written back to the Google Sheet as cell notes (small black triangle in the cell corner, visible on hover). These notes suggest improvements like adding missing descriptions or using standard license formats.

### Uploading PDFs or documents

Place files in `public/projects/<project_id>/documents/`. These will appear as download buttons on the project's detail page.

---

## API

The catalog is also published as JSON, so other catalogs and tools can list these projects alongside their own. The files are static, so there is no key to request and no rate limit.

The same information is on the website at **[fair-forward.github.io/datasets/api/](https://fair-forward.github.io/datasets/api/)**, linked from the header. That page is generated from the data, so its counts are always current.

```bash
curl https://fair-forward.github.io/datasets/api/v1/index.json
```

| Endpoint | Contents |
|---|---|
| [`api/v1/index.json`](https://fair-forward.github.io/datasets/api/v1/index.json) | Counts, licenses, vocabularies, and the notes below |
| [`api/v1/catalog.json`](https://fair-forward.github.io/datasets/api/v1/catalog.json) | Every published project |
| [`api/v1/datasets.json`](https://fair-forward.github.io/datasets/api/v1/datasets.json) | Projects that publish a dataset |
| [`api/v1/usecases.json`](https://fair-forward.github.io/datasets/api/v1/usecases.json) | Projects that publish a use case |

Every endpoint returns the same envelope: `api_version`, `license`, `count`, `vocabularies`, `version`, and `projects`. Start with `index.json`; it describes the rest.

### Licenses

Two different things are licensed here, and it matters which one you mean.

The catalog metadata is **CC0 1.0**. You can republish these records freely, with or without attribution. Every response says so under `license`.

The linked assets are not ours. Each record's `license` field describes the dataset or model we point at. It is `null` for about half the projects. That means no license has been recorded, not that the asset is unlicensed and not that it is free to reuse.

### Identifiers

Store `id`, for example `ui_6`. It comes from the Project ID column in the sheet and survives title edits. `canonical_url` contains a title-derived slug that changes when the title does, and `aliases` lists identifiers a project used to be reachable by.

### Filtering

Records carry the same vocabularies the website filters on: `sdgs`, `data_types`, `countries` (with ISO codes), and `maturity.tags`. Maturity stages are cumulative, so a project that reached a use case also carries `pilot`:

```python
pilot_plus = [p for p in data["projects"]
              if {"pilot", "usecase", "business"} & set(p["maturity"]["tags"])]
```

### Keeping in sync

There are no per-record dates, because the sheet does not record any. Instead every response carries a `version` content hash: fetch again and compare it to see whether anything changed. HTTP `Last-Modified` and `ETag` date the file. The catalog is rebuilt when someone triggers it, not on a schedule.

### Before you reuse the data

- A project is listed only while it has a working link or an access note, so records can appear and disappear. A missing id is not a retraction.
- Fields under `content` carry `provenance: "curated"` or `"auto-enriched"`. Auto-enriched text was drafted from the linked resources and is not a verified claim by the project team.
- `contact` usually holds a personal email address. It is published so people can reach a project team about their work. Please do not use it for bulk collection or unrelated outreach.

### Example

```python
import urllib.request, json

url = "https://fair-forward.github.io/datasets/api/v1/usecases.json"
data = json.load(urllib.request.urlopen(url))

for p in data["projects"]:
    license = p["license"]["name"] if p["license"] else "not recorded"
    countries = ", ".join(c["name"] for c in p["countries"]) or "not listed"
    print(f'{p["title"]}\n  {countries} | {license}\n  {p["canonical_url"]}')
```

---

## Related catalogs

Other funders and initiatives run repositories that overlap with this one. [ECOSYSTEM.md](ECOSYSTEM.md) lists them, along with whether each can be read by a machine, as the starting point for exchanging entries instead of duplicating them.

---

## Traffic, and links you share

GitHub Pages reports nothing about who visits, so the site carries [Umami](https://umami.is),
an open-source analytics tool hosted in the EU. It sets no cookies, which is why there is no
consent banner; [the privacy page](https://fair-forward.github.io/datasets/privacy/) says
plainly what it does record.

**The dashboard is public: [cloud.umami.is/share/My5RtFnm08TzktG6](https://cloud.umami.is/share/My5RtFnm08TzktG6)**

No account, no login, nothing to ask anyone for. It carries the aggregate views (overview,
period comparison, breakdowns by page, referrer and location, and UTM campaigns) and also
the per-session rows, which list a visit's city, browser, OS, device and the pages it
viewed. Anyone the link reaches can see all of that, so treat it as published.

Local `npm run dev` and `npm run preview` traffic is excluded via `data-domains`, so the
numbers are real visitors rather than our own testing.

### Tag links before you post them

LinkedIn's in-app browser often strips the referrer, and what survives arrives as an
anonymous `lnkd.in` bucket. A post you cannot distinguish from every other post tells you
nothing, so add campaign parameters to any link you publish:

```
https://fair-forward.github.io/datasets/?utm_source=linkedin&utm_medium=social&utm_campaign=kenya-datasets-launch
```

| Parameter | Use |
|---|---|
| `utm_source` | Where the link is posted: `linkedin`, `newsletter`, `bmz-blog`, `partner-site` |
| `utm_medium` | How it travels: `social`, `email`, `blog` |
| `utm_campaign` | One slug per post, reused nowhere else, e.g. `kenya-datasets-launch` |

Keep one campaign slug per post even when the same post goes to several places. Then
`utm_source` separates the channels and `utm_campaign` still totals the post.

### Any of these URLs is safe to share

The homepage, `/insights/`, `/api/` and every `/projects/<slug>/` page are real files, so
they keep their referrer and their `utm_*` parameters. Deep links to anything else fall
through `404.html`, which redirects to the homepage and loses both, and the visit lands as
untracked direct traffic.

### One-time setup

Analytics is dormant until a real Umami Website ID replaces the placeholder in three
places: `UMAMI_WEBSITE_ID` in `scripts/utils.py`, `index.html`, and
`public/privacy/index.html`. `scripts/check_head_parity.py` reports which state the site
is in on every build.

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
| `scripts/generate_api.py` | `catalog.json` -> `public/api/` (the public API and its guide page) |
| `scripts/generate_seo_pages.py` | Per-project pages, `/insights/`, `sitemap.xml`, `robots.txt` |
| `scripts/text_parsing.py` | Shared link/license/organization parsing (no CLI) |
| `scripts/check_parity.py` | Verify `text_parsing.py` still matches its JavaScript twin |
| `scripts/check_head_parity.py` | Verify every page head carries the same CSP and analytics tag |
| `scripts/validate_data.py` | Run quality checks, generate report, optionally write notes to sheet |

---

## Deployment

The `docs/` folder is the static build output. GitHub Pages serves directly from `docs/` on the `main` branch. Any push to `main` that changes `docs/` will update the live site.

---

## Contributing

PRs welcome. Follow existing code style and keep secrets out of git.

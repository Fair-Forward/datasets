#!/usr/bin/env python3
"""
Generate the public read-only API under public/api/v1/.

public/data/catalog.json is the SPA's own payload: its shape follows whatever the
interface needs, and it carries internal editorial fields. This emits a separate,
documented contract for external consumers, so the two can evolve independently --
partners mirror these records into their own repositories, where a renamed field is
a breaking change in a way it never is for our own frontend.

What the contract guarantees, and why each choice was made:

  * `id` is the identifier. It comes from the sheet's authored Project ID column
    and survives title edits; `slug` does not, so it is not published here.
  * Editorial judgements about partners' work (quality_score, editor, is_lacuna)
    are omitted. They carry our own framing, which does not survive being mirrored
    into someone else's catalogue stripped of context.
  * Machine-generated text is labelled `provenance: "auto-enriched"` rather than
    passed off as curated, so a consumer can choose not to present it as our claim.
  * A missing license is null. It means no license was recorded -- not that the
    asset is unlicensed, and not that it is free to reuse.
  * Metadata is CC0: this file states it, because a partner cannot lawfully
    republish records whose terms are undeclared. That licence covers our
    description of an asset, never the asset itself.

Output is deterministic (depends only on catalog.json), so re-running without data
changes produces byte-identical files and no git churn. Freshness is therefore not
stamped into the payload as a build timestamp: `version` is a content hash, which
answers "has anything changed?" more precisely than a clock, and GitHub Pages'
own Last-Modified/ETag headers date the file.

Vite copies public/api/ into docs/ during `npm run build`; build.py runs this before
that step, so no Vite or workflow configuration is involved.
"""

import argparse
import hashlib
import json
import os
from string import Template

from utils import (COUNTRY_ISO_MAP, SITE_BASE, AUTO_ENRICHED_PREFIX, CSP, FONT_HREF,
                   is_auto_enriched)
from text_parsing import license_parts, org_section_parts, parse_organizations

API_VERSION = "1.0"
CATALOG_PATH = os.path.join("public", "data", "catalog.json")
API_DIR = os.path.join("public", "api")
OUTPUT_DIR = os.path.join(API_DIR, "v1")

# The metadata licence: what a consumer may do with these records. Distinct from
# each record's `license`, which describes the third-party asset we point at and
# which Fair Forward does not own.
METADATA_LICENSE = {
    "spdx": "CC0-1.0",
    "url": "https://creativecommons.org/publicdomain/zero/1.0/",
    "note": (
        "Covers the catalogue metadata in this file: you may republish these records "
        "freely, with or without attribution. It does NOT cover the linked assets. "
        "Each record's `license` field describes the terms of the asset itself, which "
        "Fair Forward does not own; a null value means no license has been recorded, "
        "not that the asset is unlicensed or free to reuse."
    ),
}


# The human page sits at /api/, one level under the site root, directly above the
# JSON it documents at /api/v1/. Numbers in the copy are substituted from the data
# rather than typed, so the page cannot drift from what the endpoints actually return.
DOCS_PAGE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="How to read the FAIR Forward catalog as JSON: endpoints, licenses, identifiers and filtering.">
<meta http-equiv="Content-Security-Policy" content="$csp">
<link rel="canonical" href="${base}api/">
<title>API - FAIR Forward Data Catalog</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="$font_href" rel="stylesheet">
<style>
  :root {
    --canvas: #f6f7f7; --card: #ffffff; --surface: #f4f6f6;
    --primary: #0c815a; --gold: #c08a3e;
    --ink: #141a1f; --ink-2: #48505a; --ink-muted: #5f6873; --ink-faint: #9aa2ac;
    --border: #e3e6e8; --border-light: #eef0f1;
    --shadow: 0 1px 2px rgba(20,26,31,.04), 0 1px 12px rgba(20,26,31,.03);
    --sans: 'Hanken Grotesk', system-ui, -apple-system, sans-serif;
    --mono: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
    --measure: 68ch;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--canvas); color: var(--ink); font-family: var(--sans);
    font-size: 15px; line-height: 1.65; -webkit-font-smoothing: antialiased; }
  .masthead { border-bottom: 1px solid var(--border-light); background: var(--card); }
  .masthead-in { max-width: 82ch; margin: 0 auto; padding: .85rem 1.5rem;
    display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
  .masthead img { height: 26px; width: auto; display: block; }
  .back { font-size: .8125rem; font-weight: 600; color: var(--primary); text-decoration: none; }
  .back:hover { text-decoration: underline; }
  .wrap { max-width: 82ch; margin: 0 auto; padding: 3rem 1.5rem 5rem; }
  .stack { display: flex; flex-direction: column; gap: 2.75rem; }
  .prose { max-width: var(--measure); }
  .eyebrow { font-size: .8125rem; font-weight: 600; letter-spacing: .09em;
    text-transform: uppercase; color: var(--ink-faint); margin: 0 0 .6rem; }
  h1 { font-size: 2.1rem; font-weight: 700; letter-spacing: -.02em; line-height: 1.15;
    text-wrap: balance; margin: 0 0 .75rem; }
  .standfirst { font-size: 1.0625rem; color: var(--ink-2); margin: 0; max-width: var(--measure); }
  h2 { font-size: 1.1875rem; font-weight: 600; letter-spacing: -.01em; text-wrap: balance; margin: 0 0 .5rem; }
  h3 { font-size: .9375rem; font-weight: 600; margin: 0 0 .3rem; }
  p { color: var(--ink-2); margin: 0 0 .75rem; }
  p:last-child { margin-bottom: 0; }
  strong { color: var(--ink); font-weight: 600; }
  a { color: var(--primary); text-underline-offset: 2px; }
  a:focus-visible { outline: 2px solid var(--primary); outline-offset: 3px; border-radius: 3px; }
  section { display: flex; flex-direction: column; gap: .85rem; }
  hr { height: 1px; background: var(--border-light); border: 0; margin: 0; }
  code { font-family: var(--mono); font-size: .855em; background: var(--surface);
    border: 1px solid var(--border-light); border-radius: 4px; padding: .1em .35em; }
  pre { font-family: var(--mono); font-size: .8125rem; line-height: 1.7; background: var(--card);
    border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.15rem;
    overflow-x: auto; box-shadow: var(--shadow); margin: 0; }
  pre code { background: none; border: 0; padding: 0; font-size: inherit; }
  .c-key { color: var(--primary); } .c-com { color: var(--ink-faint); font-style: italic; }
  .c-str { color: var(--gold); }
  .endpoint { display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; background: var(--card);
    border: 1px solid var(--border); border-radius: 8px; padding: .85rem 1.1rem; box-shadow: var(--shadow); }
  .method { font-family: var(--mono); font-size: .7rem; font-weight: 600; letter-spacing: .06em;
    color: var(--primary); border: 1px solid var(--primary); border-radius: 3px; padding: .1rem .4rem; }
  .endpoint a { font-family: var(--mono); font-size: .8125rem; word-break: break-all; color: var(--ink); }
  .scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; box-shadow: var(--shadow); }
  table { border-collapse: collapse; width: 100%; background: var(--card); font-size: .8125rem; }
  th, td { text-align: left; padding: .6rem .85rem; border-bottom: 1px solid var(--border-light); vertical-align: top; }
  th { font-size: .7rem; text-transform: uppercase; letter-spacing: .07em; color: var(--ink-faint);
    font-weight: 600; white-space: nowrap; background: var(--surface); }
  tr:last-child td { border-bottom: 0; }
  td:first-child { font-family: var(--mono); font-size: .8125rem; color: var(--ink); white-space: nowrap; }
  td.note { color: var(--ink-muted); }
  td.num { font-variant-numeric: tabular-nums; white-space: nowrap; }
  .notes { display: flex; flex-direction: column; max-width: var(--measure); }
  .note-item { padding: 1rem 0; border-top: 1px solid var(--border-light);
    display: flex; flex-direction: column; gap: .15rem; }
  .note-item:first-child { border-top: 0; padding-top: .25rem; }
  footer { color: var(--ink-faint); font-size: .8125rem; max-width: var(--measure); }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
</head>
<body>
<div class="masthead"><div class="masthead-in">
  <a href="../" aria-label="FAIR Forward catalog home"><img src="../img/ff_official.png" alt="FAIR Forward"></a>
  <a class="back" href="../">Back to the catalog</a>
</div></div>

<div class="wrap"><div class="stack">

  <header class="prose">
    <p class="eyebrow">For developers</p>
    <h1>Catalog API</h1>
    <p class="standfirst">The catalog is also published as JSON, so other catalogs and tools can list
    these projects alongside their own. The files are static, so there is no key to request and no rate limit.</p>
  </header>

  <section>
    <div class="endpoint">
      <span class="method">GET</span>
      <a href="v1/index.json">${base}api/v1/index.json</a>
    </div>
    <p class="prose"><code>index.json</code> describes the rest: counts, licenses, vocabularies and the
    notes below. Every endpoint returns the same envelope, with the records under <code>projects</code>.</p>
    <div class="scroll"><table>
      <thead><tr><th>Endpoint</th><th>Contents</th><th>Records</th></tr></thead>
      <tbody>
        <tr><td><a href="v1/catalog.json">v1/catalog.json</a></td><td class="note">Every published project</td><td class="num">$total_projects</td></tr>
        <tr><td><a href="v1/datasets.json">v1/datasets.json</a></td><td class="note">Projects that publish a dataset</td><td class="num">$total_datasets</td></tr>
        <tr><td><a href="v1/usecases.json">v1/usecases.json</a></td><td class="note">Projects that publish a use case</td><td class="num">$total_usecases</td></tr>
      </tbody>
    </table></div>
  </section>

  <hr>

  <section>
    <h2>Licenses</h2>
    <div class="prose">
      <p>Two different things are licensed here, and it matters which one you mean.</p>
      <p>The catalog metadata is <strong>CC0 1.0</strong>. You can republish these records freely, with or
      without attribution. Every response says so under <code>license</code>.</p>
      <p>The linked assets are not ours. Each record's <code>license</code> field describes the dataset or
      model we point at. It is <code>null</code> for $unlicensed of $total_projects projects. That means no
      license has been recorded, not that the asset is unlicensed and not that it is free to reuse.</p>
    </div>
  </section>

  <hr>

  <section>
    <h2>Identifiers</h2>
    <p class="prose">Store <code>id</code>, for example <code>ui_6</code>. It comes from the Project ID
    column in the sheet and survives title edits. <code>canonical_url</code> contains a title-derived slug
    that changes when the title does, and <code>aliases</code> lists identifiers a project used to be
    reachable by.</p>
  </section>

  <hr>

  <section>
    <h2>Filtering</h2>
    <p class="prose">Records carry the same vocabularies the website filters on: <code>sdgs</code>
    ($n_sdgs), <code>data_types</code> ($n_data_types), <code>countries</code> with ISO codes ($n_countries),
    and <code>maturity.tags</code>. Maturity stages are cumulative, so a project that reached a use case
    also carries <code>pilot</code>:</p>
    <pre><code><span class="c-com"># $pilot_plus of $total_projects projects have reached pilot or beyond</span>
<span class="c-key">import</span> urllib.request, json

url = <span class="c-str">"${base}api/v1/catalog.json"</span>
data = json.load(urllib.request.urlopen(url))

pilot_plus = [p <span class="c-key">for</span> p <span class="c-key">in</span> data[<span class="c-str">"projects"</span>]
              <span class="c-key">if</span> {<span class="c-str">"pilot"</span>, <span class="c-str">"usecase"</span>, <span class="c-str">"business"</span>} &amp; <span class="c-key">set</span>(p[<span class="c-str">"maturity"</span>][<span class="c-str">"tags"</span>])]</code></pre>
    <div class="scroll"><table>
      <thead><tr><th>Field</th><th>Type</th><th>Recorded</th><th>Notes</th></tr></thead>
      <tbody>
        <tr><td>id</td><td>string</td><td class="num">$total_projects</td><td class="note">Stable. Store this one.</td></tr>
        <tr><td>title</td><td>string</td><td class="num">$cov_title</td><td class="note">Plain text.</td></tr>
        <tr><td>description</td><td>string</td><td class="num">$cov_description</td><td class="note">Prose, no markup.</td></tr>
        <tr><td>organizations</td><td>roles</td><td class="num">$cov_orgs</td><td class="note">provided_by, catalyzed_by, financed_by. Each has text and links.</td></tr>
        <tr><td>countries[]</td><td>name, iso2</td><td class="num">$cov_countries</td><td class="note">ISO 3166-1 alpha-2. Join on iso2, not name.</td></tr>
        <tr><td>regions[]</td><td>string[]</td><td class="num">$cov_regions</td><td class="note">Values with no country code, such as "West Africa".</td></tr>
        <tr><td>sdgs[]</td><td>string[]</td><td class="num">$cov_sdgs</td><td class="note">The closest thing we record to a sector.</td></tr>
        <tr><td>data_types[]</td><td>string[]</td><td class="num">$cov_data_types</td><td class="note">Such as Voice or Geospatial/Remote Sensing.</td></tr>
        <tr><td>maturity.tags[]</td><td>string[]</td><td class="num">$cov_maturity</td><td class="note">Cumulative stages, as above.</td></tr>
        <tr><td>links</td><td>label, url</td><td class="num">$cov_links</td><td class="note">Grouped as dataset, usecase, additional, documents.</td></tr>
        <tr><td>canonical_url</td><td>string</td><td class="num">$total_projects</td><td class="note">The project's page here. A good place to link back to.</td></tr>
        <tr><td>license</td><td>name, spdx, url</td><td class="num">$cov_license</td><td class="note">Often null. See above.</td></tr>
        <tr><td>content</td><td>text, provenance</td><td class="num">$cov_content</td><td class="note">Check provenance before showing it.</td></tr>
        <tr><td>contact</td><td>string</td><td class="num">$cov_contact</td><td class="note">Free text, usually an email address.</td></tr>
        <tr><td>image</td><td>string</td><td class="num">$cov_image</td><td class="note">Absolute URL. Some are stock placeholders.</td></tr>
      </tbody>
    </table></div>
  </section>

  <hr>

  <section>
    <h2>Keeping in sync</h2>
    <p class="prose">There are no per-record dates, because the sheet does not record any. Instead every
    response carries a <code>version</code> content hash: fetch again and compare it to see whether anything
    changed. HTTP <code>Last-Modified</code> and <code>ETag</code> date the file. The catalog is rebuilt when
    someone triggers it, not on a schedule, so checking daily is ample.</p>
  </section>

  <hr>

  <section>
    <h2>Before you reuse the data</h2>
    <div class="notes">
      <div class="note-item">
        <h3>A null license is not permission</h3>
        <p>$unlicensed of $total_projects projects have no license recorded. That means nobody has
        established the terms, not that the asset is free to reuse. Please show it as unknown rather than
        filling in a default.</p>
      </div>
      <div class="note-item">
        <h3>Some text is machine-drafted</h3>
        <p>Fields under <code>content</code> carry <code>provenance: "curated"</code> or
        <code>"auto-enriched"</code>. Auto-enriched text was drafted from the linked resources and is not a
        verified claim by the project team.</p>
      </div>
      <div class="note-item">
        <h3>A project can appear and disappear</h3>
        <p>A project is listed only while it has a working link or an access note. A missing id is not a
        retraction, so please do not treat it as a delete.</p>
      </div>
      <div class="note-item">
        <h3>Contact holds personal email addresses</h3>
        <p>Published so people can reach a project team about their work. Please do not use it for bulk
        collection or unrelated outreach, and let us know before republishing it.</p>
      </div>
    </div>
  </section>

  <hr>

  <footer>
    <p>Fair Forward, Artificial Intelligence for All. A project by GIZ. Catalog metadata is CC0 1.0.</p>
    <p>Questions, or a field you need that is not here?
    <a href="https://github.com/Fair-Forward/datasets/issues/new">Open an issue on GitHub</a>.</p>
  </footer>

</div></div>
</body>
</html>
""")


def absolute_url(path):
    """Turn a site-relative path from catalog.json into a URL a consumer can fetch."""
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    return SITE_BASE + path.lstrip("/")


def content_field(text):
    """Return {text, provenance} for a prose field, or None when empty.

    The auto-enrichment marker is lifted out of the prose into a flag: inline, it
    is noise every consumer would have to strip; as a field, it is a fact about the
    text that a consumer can act on.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return None
    if is_auto_enriched(text):
        stripped = text.lstrip()[len(AUTO_ENRICHED_PREFIX):].lstrip()
        if not stripped:
            return None
        return {"text": stripped, "provenance": "auto-enriched"}
    return {"text": text.strip(), "provenance": "curated"}


def split_places(names):
    """Split catalog `countries` into ISO-coded countries and uncoded regions.

    The column mixes granularities ("Kenya" alongside "West Africa" and "Global"),
    which a consumer cannot resolve from the strings alone. COUNTRY_ISO_MAP decides:
    anything it codes is a country, anything left over is published as a region
    rather than silently dropped or passed off as a country.
    """
    countries, regions = [], []
    for name in names:
        iso2 = COUNTRY_ISO_MAP.get(name)
        if iso2:
            countries.append({"name": name, "iso2": iso2})
        else:
            regions.append(name)
    return countries, regions


def build_organizations(project):
    """Credit the makers as structured roles rather than a prose blob.

    The source cell reads "Powered by / Provided by: X\\nCatalyzed by: Y". A cell
    with no role labels is published under `unattributed` rather than being
    guessed into a role we cannot verify.
    """
    roles = parse_organizations(project.get("organizations"))
    if not roles:
        return None
    if "raw" in roles:
        parts = org_section_parts(roles["raw"])
        return {"unattributed": parts} if parts else None
    parsed = {key: org_section_parts(value) for key, value in roles.items()}
    return parsed if any(parsed.values()) else None


def build_links(project):
    """Group a project's links by role, with absolute URLs and real labels."""
    def group(items):
        return [
            {"label": item.get("name") or "Link", "url": absolute_url(item["url"])}
            for item in items or []
            if item.get("url")
        ]

    return {
        "dataset": group(project.get("dataset_links")),
        "usecase": group(project.get("usecase_links")),
        "additional": group(project.get("additional_resources")),
        "documents": group(project.get("hosted_documents")),
    }


def build_record(project):
    """Reshape one catalog project into a published API record."""
    countries, regions = split_places(project.get("countries") or [])

    kind = []
    if project.get("has_dataset"):
        kind.append("dataset")
    if project.get("has_usecase"):
        kind.append("usecase")

    access_note = None
    if project.get("has_access_note"):
        access_note = {
            "kind": project.get("access_note_kind"),
            "markdown": project.get("access_note_markdown"),
        }

    content = {
        key: content_field(project.get(key))
        for key in ("data_characteristics", "model_characteristics", "how_to_use")
    }

    return {
        "id": project["id"],
        # The slug churns when a title is edited; the canonical URL is built from the
        # current one so a consumer always has a link that resolves, while `id`
        # remains the thing to store.
        "canonical_url": SITE_BASE + "projects/" + project["slug"] + "/",
        "aliases": project.get("aliases") or [],
        "title": (project.get("title") or "").strip(),
        "description": (project.get("description") or "").strip() or None,
        "kind": kind,
        "countries": countries,
        "regions": regions,
        "sdgs": project.get("sdgs") or [],
        "data_types": project.get("data_types") or [],
        "maturity": {
            "stage": (project.get("maturity") or "").strip() or None,
            "tags": project.get("maturity_tags") or [],
        },
        "license": license_parts(project.get("license")),
        "organizations": build_organizations(project),
        "contact": (project.get("contact") or "").strip() or None,
        "access_note": access_note,
        "links": build_links(project),
        "content": content,
        "image": absolute_url(project.get("image")),
    }


def build_vocabularies(records, catalog):
    """Publish the closed sets a consumer can filter on, derived from what shipped.

    Countries are listed by name, not collapsed by code: the source spells some
    countries more than one way ("DRC" and "Democratic Republic of Congo"), so
    every name a record can actually carry has to appear here for name matching to
    work. Consumers that want one entry per country should group on iso2.
    """
    countries = set()
    regions = set()
    for record in records:
        for country in record["countries"]:
            countries.add((country["name"], country["iso2"]))
        regions.update(record["regions"])
    return {
        "sdgs": catalog["filters"]["sdgs"],
        "data_types": catalog["filters"]["data_types"],
        "countries": [
            {"name": name, "iso2": iso2} for name, iso2 in sorted(countries)
        ],
        "regions": sorted(regions),
        "maturity_stages": catalog["filters"]["maturity_stages"],
    }


def envelope(records, catalog, vocabularies, description):
    """Wrap records in the shared envelope every endpoint returns."""
    body = {
        "api_version": API_VERSION,
        "description": description,
        "source": SITE_BASE,
        "documentation": SITE_BASE + "api/v1/index.json",
        "license": METADATA_LICENSE,
        "count": len(records),
        "vocabularies": vocabularies,
        "projects": records,
    }
    # Hash the payload as it will be served, minus the version line itself, so the
    # value changes when and only when the content does.
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    return {**body, "version": digest}


def write_docs_page(records, vocabularies, path):
    """Render the human-readable API page from the records themselves.

    Every count in the copy is derived here rather than typed, so the page cannot
    claim coverage the endpoints do not have.
    """
    total = len(records)

    def recorded(predicate):
        return sum(1 for r in records if predicate(r))

    fields = {
        "cov_title": recorded(lambda r: r["title"]),
        "cov_description": recorded(lambda r: r["description"]),
        "cov_orgs": recorded(lambda r: r["organizations"]),
        "cov_countries": recorded(lambda r: r["countries"]),
        "cov_regions": recorded(lambda r: r["regions"]),
        "cov_sdgs": recorded(lambda r: r["sdgs"]),
        "cov_data_types": recorded(lambda r: r["data_types"]),
        "cov_maturity": recorded(lambda r: r["maturity"]["tags"]),
        "cov_links": recorded(lambda r: any(r["links"].values())),
        "cov_license": recorded(lambda r: r["license"]),
        "cov_content": recorded(lambda r: any(r["content"].values())),
        "cov_contact": recorded(lambda r: r["contact"]),
        "cov_image": recorded(lambda r: r["image"]),
    }

    page = DOCS_PAGE.substitute(
        base=SITE_BASE,
        csp=CSP,
        font_href=FONT_HREF,
        total_projects=total,
        total_datasets=recorded(lambda r: "dataset" in r["kind"]),
        total_usecases=recorded(lambda r: "usecase" in r["kind"]),
        unlicensed=total - fields["cov_license"],
        pilot_plus=recorded(
            lambda r: {"pilot", "usecase", "business"} & set(r["maturity"]["tags"])
        ),
        n_sdgs=len(vocabularies["sdgs"]),
        n_data_types=len(vocabularies["data_types"]),
        n_countries=len(vocabularies["countries"]),
        **fields,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def generate_api(catalog_path=CATALOG_PATH, output_dir=OUTPUT_DIR):
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    records = [build_record(p) for p in catalog["projects"]]
    vocabularies = build_vocabularies(records, catalog)

    datasets = [r for r in records if "dataset" in r["kind"]]
    usecases = [r for r in records if "usecase" in r["kind"]]

    os.makedirs(output_dir, exist_ok=True)

    endpoints = {
        "catalog.json": (records, "Every published project."),
        "datasets.json": (datasets, "Projects that publish a dataset."),
        "usecases.json": (usecases, "Projects that publish a use case."),
    }
    for filename, (subset, description) in endpoints.items():
        write_json(
            os.path.join(output_dir, filename),
            envelope(subset, catalog, vocabularies, description),
        )

    index = {
        "api_version": API_VERSION,
        "name": "Fair Forward Data Catalog API",
        "description": (
            "Open datasets, models and AI use cases for international development, "
            "built by local partners."
        ),
        "source": SITE_BASE,
        "license": METADATA_LICENSE,
        "endpoints": [
            {
                "url": SITE_BASE + "api/v1/" + filename,
                "description": description,
                "count": len(subset),
            }
            for filename, (subset, description) in endpoints.items()
        ],
        "counts": {
            "projects": len(records),
            "datasets": len(datasets),
            "usecases": len(usecases),
        },
        "vocabularies": vocabularies,
        "identifiers": (
            "`id` is stable: it is authored in the source sheet and survives title "
            "edits. Store it. `canonical_url` contains a title-derived slug that "
            "changes when the title does; `aliases` lists identifiers a project was "
            "previously reachable by."
        ),
        "freshness": (
            "There are no per-record dates: the source carries none, so incremental "
            "sync is not possible. `version` is a content hash -- re-fetch and compare "
            "it to detect any change. HTTP Last-Modified and ETag date the file. The "
            "catalogue is rebuilt manually, not on a schedule."
        ),
        "caveats": [
            "Membership is derived from link presence, not authored: a project is "
            "published only while it has a working link or an access note, so records "
            "can appear and disappear. Absence is not a retraction.",
            "`license` is null for roughly half of projects, meaning no license was "
            "recorded. Do not infer permission from a null.",
            "`content` fields marked provenance: \"auto-enriched\" were machine-drafted "
            "from the linked resources, not written or verified by the project team.",
            "`contact` is free text and usually contains a personal email address. It "
            "is published so users can reach the project team about their work; please "
            "do not use it for bulk collection or unrelated outreach.",
        ],
    }
    write_json(os.path.join(output_dir, "index.json"), index)

    # The human page lives one level up, directly above the JSON it documents.
    docs_page = os.path.join(os.path.dirname(output_dir.rstrip(os.sep)), "index.html")
    write_docs_page(records, vocabularies, docs_page)

    print(f"Successfully generated {output_dir}/")
    print(f"  - {docs_page} (human-readable guide)")
    print(f"  - index.json     ({len(records)} projects, {len(datasets)} datasets, "
          f"{len(usecases)} use cases)")
    for filename, (subset, _description) in endpoints.items():
        print(f"  - {filename:<14} ({len(subset)} records)")
    licensed = sum(1 for r in records if r["license"])
    print(f"  - {licensed}/{len(records)} records carry a license")
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the public API JSON.")
    parser.add_argument("--input", default=CATALOG_PATH, help="Path to catalog.json")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    cli_args = parser.parse_args()
    generate_api(cli_args.input, cli_args.output_dir)

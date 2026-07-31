#!/usr/bin/env python3
"""
Generate per-project static HTML pages for SEO, plus sitemap.xml and robots.txt.

The catalogue is a client-rendered SPA: docs/index.html ships an empty #root and
all project text is drawn by JavaScript at runtime, so crawlers see no project
content and there are no per-project URLs. This script emits one static page per
project at docs/projects/<slug>/index.html, each with the project's real title,
description and text baked into the served HTML plus per-page meta/canonical tags.

Each page also loads the same app bundle; when the browser runs it, the SPA boots
at /datasets/projects/<slug>/ (via the /projects/:slug route in src/App.jsx) and
opens that project in place inside the full interactive catalogue.

The same trick gives /insights a real file. Without one it falls through to
docs/404.html, whose location.replace() to the site root costs the visit its referrer
and its ?utm_* query before analytics can read them -- so a shared insights link would
report as untracked direct traffic. Every URL worth sharing is now a served document.

Output is deterministic (depends only on catalog.json), so re-running without data
changes produces byte-identical files and no git churn.

Run AFTER `npm run build` (needs docs/assets/index.{js,css}); build.py invokes it.
"""

import html
import json
import os
from string import Template

from utils import SITE_BASE, SITE_NAME, CSP, ANALYTICS, FONT_HREF

DEFAULT_OG_IMAGE = SITE_BASE + "img/fair_forward.png"
CATALOG_PATH = os.path.join("public", "data", "catalog.json")
DOCS_DIR = "docs"



MATURITY_LABELS = {
    "dataset": "Dataset", "model": "Model", "pilot": "Pilot",
    "usecase": "Use case", "business": "Business",
}

# Pages live at docs/projects/<slug>/index.html (two levels below docs/), so
# site-root-relative assets are reached with a ../../ prefix. This matches Vite's
# base:'./' convention and works both in `npm run preview` and on the deployed subpath.
PREFIX = "../../"

PAGE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="$description">
    <meta property="og:title" content="$og_title">
    <meta property="og:description" content="$description">
    <meta property="og:type" content="article">
    <meta property="og:url" content="$canonical">
    <meta property="og:image" content="$og_image">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="$og_title">
    <meta name="twitter:description" content="$description">
    <meta name="twitter:image" content="$og_image">
    <meta http-equiv="Content-Security-Policy" content="$csp">
    $analytics
    <link rel="canonical" href="$canonical">
    <title>$title_tag</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" crossorigin href="../../assets/index.css">
    <style>
      .seo-fallback{max-width:820px;margin:0 auto;padding:2rem 1.25rem;font-family:'Public Sans',system-ui,-apple-system,sans-serif;color:#1a2b3c;line-height:1.6}
      .seo-fallback a{color:#1565c0}
      .seo-fallback .seo-home{font-size:.9rem;font-weight:600;text-decoration:none}
      .seo-fallback h1{font-size:1.9rem;line-height:1.25;margin:1rem 0 .75rem}
      .seo-fallback h2{font-size:1.15rem;margin:2rem 0 .5rem}
      .seo-fallback .seo-meta{color:#5a6b7c;font-size:.95rem;margin:0 0 1.5rem}
      .seo-fallback img{max-width:100%;height:auto;border-radius:8px;margin:1rem 0}
      .seo-fallback ul{padding-left:1.2rem;margin:.25rem 0}
    </style>
</head>
<body>
    <div id="root">
$body
    </div>
    <script type="module" crossorigin src="../../assets/index.js"></script>
</body>
</html>
""")

# docs/insights/index.html sits one level below docs/, hence ../ rather than ../../.
# The fallback body is deliberately thin: the charts are drawn from insights.json at
# runtime and there is no static text to bake in, so it only has to describe the page
# for crawlers and give a no-JS reader a way back to the catalogue.
INSIGHTS_PAGE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="$description">
    <meta property="og:title" content="$og_title">
    <meta property="og:description" content="$description">
    <meta property="og:type" content="website">
    <meta property="og:url" content="$canonical">
    <meta property="og:image" content="$og_image">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="$og_title">
    <meta name="twitter:description" content="$description">
    <meta name="twitter:image" content="$og_image">
    <meta http-equiv="Content-Security-Policy" content="$csp">
    $analytics
    <link rel="canonical" href="$canonical">
    <title>$og_title</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="$font_href" rel="stylesheet">
    <link rel="stylesheet" crossorigin href="../assets/index.css">
    <style>
      .seo-fallback{max-width:820px;margin:0 auto;padding:2rem 1.25rem;font-family:'Hanken Grotesk',system-ui,-apple-system,sans-serif;color:#141a1f;line-height:1.6}
      .seo-fallback a{color:#0c815a}
      .seo-fallback h1{font-size:1.9rem;line-height:1.25;margin:1rem 0 .75rem}
    </style>
</head>
<body>
    <div id="root">
      <main class="seo-fallback">
        <a href="../">FAIR Forward - Open Data &amp; AI Use Cases</a>
        <h1>Insights &amp; Visualisations</h1>
        <p>Where the $count projects in the FAIR Forward catalogue are based, how they
        progress from data to deployment, and which Sustainable Development Goals they
        address.</p>
        <p><a href="../">Browse the full FAIR Forward catalogue</a></p>
      </main>
    </div>
    <script type="module" crossorigin src="../assets/index.js"></script>
</body>
</html>
""")


def esc(value):
    """HTML-escape text/attribute values (quotes included)."""
    return html.escape("" if value is None else str(value))


def meta_description(text):
    """Single-line, whitespace-collapsed description trimmed to ~160 chars."""
    collapsed = " ".join(str(text or "").split())
    if len(collapsed) > 160:
        collapsed = collapsed[:157].rstrip() + "..."
    return esc(collapsed)


def rel_asset(site_root_path):
    """Turn a site-root-relative path ('/projects/ui_28/images/x.png') into a
    page-relative path ('../../projects/ui_28/images/x.png')."""
    return PREFIX + str(site_root_path or "").lstrip("/")


def abs_url(site_root_path):
    """Absolute URL for a site-root-relative path."""
    return SITE_BASE.rstrip("/") + "/" + str(site_root_path or "").lstrip("/")


def render_prose(text):
    """Escape free text and preserve paragraph/line breaks as HTML."""
    text = str(text or "").strip()
    if not text:
        return ""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    return "\n".join("<p>" + esc(b).replace("\n", "<br>") + "</p>" for b in blocks)


def render_links(links, heading):
    """Render a {name,url} list as a section with real anchors; skip if empty."""
    items = [l for l in (links or []) if isinstance(l, dict) and l.get("url")]
    if not items:
        return ""
    lis = "".join(
        '<li><a href="{}" rel="noopener noreferrer">{}</a></li>'.format(
            esc(l["url"]), esc(l.get("name") or l["url"]))
        for l in items
    )
    return "<section><h2>{}</h2><ul>{}</ul></section>".format(esc(heading), lis)


def render_section(text, heading):
    prose = render_prose(text)
    if not prose:
        return ""
    return "<section><h2>{}</h2>{}</section>".format(esc(heading), prose)


def build_meta_line(project):
    parts = []
    countries = project.get("countries") or []
    if countries:
        parts.append(("Country: " if len(countries) == 1 else "Countries: ") + ", ".join(countries))
    if project.get("sdgs"):
        parts.append(", ".join(project["sdgs"]))
    if project.get("data_types"):
        parts.append("Data: " + ", ".join(project["data_types"]))
    if project.get("license"):
        parts.append("License: " + project["license"])
    tags = project.get("maturity_tags") or []
    if tags:
        parts.append("Maturity: " + " > ".join(MATURITY_LABELS.get(t, t) for t in tags))
    return esc(" | ".join(parts))


def build_body(project):
    title = project.get("title") or project.get("id")
    image = project.get("image")
    parts = ['      <main class="seo-fallback">']
    parts.append('        <a class="seo-home" href="../../">FAIR Forward - Open Data &amp; AI Use Cases</a>')
    parts.append("        <h1>{}</h1>".format(esc(title)))
    meta_line = build_meta_line(project)
    if meta_line:
        parts.append('        <p class="seo-meta">{}</p>'.format(meta_line))
    if image:
        parts.append('        <img src="{}" alt="{}">'.format(esc(rel_asset(image)), esc(title)))
    if project.get("description"):
        parts.append(render_prose(project["description"]))
    parts.append(render_section(project.get("data_characteristics"), "Data characteristics"))
    parts.append(render_section(project.get("model_characteristics"), "Model characteristics"))
    parts.append(render_section(project.get("how_to_use"), "How to use"))
    parts.append(render_links(project.get("dataset_links"), "Datasets"))
    parts.append(render_links(project.get("usecase_links"), "Use cases"))
    parts.append(render_links(project.get("hosted_documents"), "Documents"))
    parts.append(render_links(project.get("additional_resources"), "Additional resources"))
    # About block (organizations / authors / contact) -- names people may search for.
    about = []
    if project.get("organizations"):
        about.append(render_prose(project["organizations"]))
    if project.get("editor"):
        about.append("<p>Authors: {}</p>".format(esc(project["editor"])))
    if project.get("contact"):
        about.append("<p>Contact: {}</p>".format(esc(project["contact"])))
    if any(about):
        parts.append("<section><h2>About</h2>{}</section>".format("".join(a for a in about if a)))
    parts.append('        <p><a href="../../">Browse the full FAIR Forward catalogue</a></p>')
    parts.append("      </main>")
    return "\n".join(p for p in parts if p)


def build_page(project):
    title = project.get("title") or project.get("id")
    slug = project.get("slug") or project.get("id")
    canonical = SITE_BASE + "projects/" + slug + "/"
    og_image = abs_url(project["image"]) if project.get("image") else DEFAULT_OG_IMAGE
    og_title = esc("{} - {}".format(title, SITE_NAME))
    return PAGE.substitute(
        description=meta_description(project.get("description") or title),
        og_title=og_title,
        title_tag=og_title,
        canonical=esc(canonical),
        og_image=esc(og_image),
        csp=esc(CSP),
        analytics=ANALYTICS,
        body=build_body(project),
    )


def build_insights_page(project_count):
    return INSIGHTS_PAGE.substitute(
        description=meta_description(
            "Where the {} projects in the FAIR Forward catalogue are based, how they "
            "progress from data to deployment, and which Sustainable Development Goals "
            "they address.".format(project_count)),
        og_title=esc("Insights & Visualisations - " + SITE_NAME),
        canonical=esc(SITE_BASE + "insights/"),
        og_image=esc(DEFAULT_OG_IMAGE),
        csp=esc(CSP),
        analytics=ANALYTICS,
        font_href=esc(FONT_HREF),
        count=project_count,
    )


def build_sitemap(slugs):
    # lastmod is intentionally omitted to keep output deterministic (no date churn).
    # Only URLs that return HTTP 200 are listed: the homepage, /insights/ (written just
    # below) and the project pages that were actually written (the caller passes their
    # slugs).
    urls = [SITE_BASE, SITE_BASE + "insights/"]
    urls += [SITE_BASE + "projects/" + slug + "/" for slug in slugs]
    body = "\n".join("  <url><loc>{}</loc></url>".format(esc(u)) for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + body + "\n</urlset>\n")


def build_robots():
    return ("User-agent: *\nAllow: /\nSitemap: " + SITE_BASE + "sitemap.xml\n")


def main():
    print("\n" + "=" * 60)
    print("  Generating SEO pages (per-project HTML + sitemap)")
    print("=" * 60)

    if not os.path.exists(CATALOG_PATH):
        print("ERROR: {} not found; run generate_catalog_data.py first.".format(CATALOG_PATH))
        return 1
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    projects = catalog.get("projects") or []
    written_slugs = []
    failed = 0
    for project in projects:
        slug = project.get("slug") or project.get("id")
        if not slug:
            print("  Skipping project with no slug/id: {}".format(project.get("title")))
            failed += 1
            continue
        try:
            out_dir = os.path.join(DOCS_DIR, "projects", slug)
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(build_page(project))
            written_slugs.append(slug)
        except Exception as exc:  # one bad project must not break the whole build
            print("  Failed to generate page for {}: {}".format(slug, exc))
            failed += 1

    # A real file for /insights, so shared links to it keep their referrer and ?utm_*
    # instead of being laundered through the 404 redirect shim.
    insights_dir = os.path.join(DOCS_DIR, "insights")
    os.makedirs(insights_dir, exist_ok=True)
    with open(os.path.join(insights_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_insights_page(len(projects)))

    # Sitemap lists only the pages actually written, so every <loc> returns HTTP 200.
    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(written_slugs))
    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(build_robots())

    print("Wrote {} project pages ({} failed), insights page, sitemap.xml ({} urls), "
          "robots.txt".format(len(written_slugs), failed, len(written_slugs) + 2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

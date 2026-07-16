#!/usr/bin/env python3
"""
Verify scripts/text_parsing.py still agrees with its JavaScript twin.

Link labels used to be derived in the browser by labelFromUrl() in
src/utils/parsing.js. They are now derived at build time in Python and baked into
catalog.json and the public API, but the JavaScript copy survives because the
detail panel's markdown renderer still shortens bare URLs with it. Two
implementations of one rule will drift, and drift here changes what readers see
and what partners mirror -- so this diffs them over every URL in the catalog plus
the edge cases the live data does not happen to cover.

Usage:
    python scripts/check_parity.py          # exits non-zero on any mismatch

Requires node. Skips (exit 0) when node is unavailable, so it never blocks a
build on a machine that only has Python.
"""

import json
import os
import shutil
import subprocess
import sys

from text_parsing import label_from_url, license_label, first_url

CATALOG_PATH = os.path.join("public", "data", "catalog.json")
PARSING_JS = os.path.abspath(os.path.join("src", "utils", "parsing.js"))

# Shapes the catalog may not contain today but the rules must still agree on.
# The malformed ones matter as much as the tidy ones: Python's urlparse accepts hosts
# and ports that the frontend's new URL() rejects, and unquote swallows escapes that
# decodeURIComponent throws on, so each of these caught a real divergence.
EXTRA_URLS = [
    "https://huggingface.co/roymukund/X/tree/main",
    "https://github.com/org/repo.git",
    "https://example.com/a/very/long/segment-name-that-exceeds-thirty-four-chars",
    "https://example.com/50%off",            # malformed percent-escape
    "https://example.com/%E4%B8%AD%E6%96%87",  # non-ascii
    "https://example.com/",
    "https://www.doi.org/10.1234/abc",
    "https://example.com/path/(parens)",
    "https://example.com/download/raw/main",  # all-noise path
    "https://example.com:99999/a",           # port out of range
    "https://exa mple.com/a",                # space in host
    "https://ex%mple.com/a",                 # malformed escape in host
    "https:///path",                         # empty authority
    "http://[not-a-host]/x",                 # unparseable host
    "https://",
    "ftp://example.com/x",
    "not a url",
    "",
]
EXTRA_LICENSES = ["4.0", "1.0", "", "CC-BY 4.0", "https://example.com/",
                  "https://creativecommons.org/licenses/by/4.0/",
                  "Name (X)\nhttps://example.com/licenses/some-license",
                  "https://example.com/50%off",      # malformed escape in the segment
                  "https://example.com/%E4%B8%AD",   # non-ascii segment
                  "https://ex%mple.com/",            # malformed escape in the host
                  "https:///path"]

NODE_SCRIPT = """
import {{ readFileSync }} from 'fs'
import {{ labelFromUrl, licenseLabel, firstUrl }} from '{parsing_js}'
const {{ urls, licenses }} = JSON.parse(readFileSync(0, 'utf8'))
process.stdout.write(JSON.stringify({{
  labelFromUrl: urls.map(labelFromUrl),
  licenseLabel: licenses.map(licenseLabel),
  firstUrl: licenses.map(firstUrl),
}}))
"""


def collect_inputs(catalog):
    """Every URL and license string the catalog can put through these rules."""
    urls, licenses = set(EXTRA_URLS), set(EXTRA_LICENSES)
    for project in catalog["projects"]:
        for key in ("dataset_links", "usecase_links", "additional_resources",
                    "hosted_documents"):
            for link in project.get(key) or []:
                if link.get("url"):
                    urls.add(link["url"])
        if isinstance(project.get("license"), str):
            licenses.add(project["license"])
    return sorted(urls), sorted(licenses)


def main():
    if not shutil.which("node"):
        print("check_parity: node not found, skipping")
        return 0
    if not os.path.exists(CATALOG_PATH):
        print(f"check_parity: {CATALOG_PATH} not found, run generate_catalog_data.py first")
        return 1

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    urls, licenses = collect_inputs(catalog)

    result = subprocess.run(
        ["node", "--input-type=module", "-e",
         NODE_SCRIPT.format(parsing_js=PARSING_JS)],
        input=json.dumps({"urls": urls, "licenses": licenses}),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("check_parity: node failed:\n" + result.stderr.strip())
        return 1

    js = json.loads(result.stdout)
    cases = [
        ("labelFromUrl", label_from_url, urls, js["labelFromUrl"]),
        ("licenseLabel", license_label, licenses, js["licenseLabel"]),
        ("firstUrl", first_url, licenses, js["firstUrl"]),
    ]

    mismatches = 0
    for name, py_fn, inputs, expected in cases:
        bad = [(i, e, py_fn(i)) for i, e in zip(inputs, expected) if py_fn(i) != e]
        print(f"  {'OK  ' if not bad else 'FAIL'} {name}: "
              f"{len(inputs) - len(bad)}/{len(inputs)} match")
        for value, want, got in bad[:10]:
            print(f"       input: {value!r}\n         js: {want!r}\n         py: {got!r}")
        mismatches += len(bad)

    if mismatches:
        print(f"\ncheck_parity: {mismatches} mismatch(es). scripts/text_parsing.py and "
              f"src/utils/parsing.js must agree -- they label the same links.")
        return 1
    print("\ncheck_parity: python and javascript agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())

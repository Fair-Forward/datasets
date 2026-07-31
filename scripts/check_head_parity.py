#!/usr/bin/env python3
"""
Verify every page head carries the same CSP and the same analytics tag.

Five surfaces serve HTML and each one owns its own <head>: index.html (hand-written,
Vite copies it to docs/), the per-project SEO pages and /insights (generate_seo_pages.py),
the API guide (generate_api.py), and the privacy page (hand-written under public/).
The generated three import CSP and ANALYTICS from utils.py; the two hand-written ones
cannot, so they hold literal copies.

Drift here is silent and expensive in both directions. A stale CSP blocks the analytics
script on some pages only, which looks exactly like "those pages get no traffic". A
missing analytics tag undercounts without erroring anywhere. Neither shows up in a build
log, so this asserts it instead.

Usage:
    python scripts/check_head_parity.py     # exits non-zero on any drift

Checks docs/ when it has been built, and skips those checks otherwise, so it is safe to
run before the first build.
"""

import glob
import html
import os
import re
import sys

from utils import CSP, ANALYTICS, UMAMI_WEBSITE_ID

PLACEHOLDER_ID = "PASTE-WEBSITE-ID-FROM-UMAMI-DASHBOARD"

INDEX_HTML = "index.html"
PRIVACY_HTML = os.path.join("public", "privacy", "index.html")
DOCS_DIR = "docs"

CSP_META = re.compile(
    r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]*)"\s*/?>')


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_csp(path, source, failures):
    """The CSP meta in `source` must decode to exactly utils.CSP.

    Generated pages substitute html.escape(CSP), the hand-written ones hold it raw, so
    both are unescaped before comparing rather than matched as two separate literals.
    """
    found = CSP_META.search(source)
    if not found:
        failures.append("{}: no Content-Security-Policy meta tag".format(path))
        return
    actual = html.unescape(found.group(1))
    if actual != CSP:
        failures.append(
            "{}: CSP differs from utils.CSP\n       utils.py: {}\n       {}: {}".format(
                path, CSP, path, actual))


def check_analytics(path, source, failures):
    """The analytics tag must be present verbatim, so the website ID cannot drift."""
    if ANALYTICS not in source:
        failures.append("{}: analytics tag missing or altered\n       expected: {}".format(
            path, ANALYTICS))


def main():
    failures = []

    # Hand-written heads. These are the ones that go stale, because nothing forces them
    # to be edited when utils.py is.
    for path in (INDEX_HTML, PRIVACY_HTML):
        if not os.path.exists(path):
            failures.append("{}: missing".format(path))
            continue
        source = read(path)
        check_csp(path, source, failures)
        check_analytics(path, source, failures)

    # Generated heads, checked in their built form so the assertion covers what actually
    # ships rather than what the templates intend.
    generated = [os.path.join(DOCS_DIR, "index.html"),
                 os.path.join(DOCS_DIR, "insights", "index.html"),
                 os.path.join(DOCS_DIR, "api", "index.html"),
                 os.path.join(DOCS_DIR, "privacy", "index.html")]
    project_pages = sorted(glob.glob(os.path.join(DOCS_DIR, "projects", "*", "index.html")))
    generated += project_pages

    built = [p for p in generated if os.path.exists(p)]
    if not built:
        print("check_head_parity: docs/ not built yet, checked source files only")
    else:
        missing = [p for p in generated if not os.path.exists(p)]
        for path in missing:
            failures.append("{}: missing (run npm run build && python scripts/build.py)".format(path))
        for path in built:
            source = read(path)
            check_csp(path, source, failures)
            check_analytics(path, source, failures)
        print("  Checked {} built pages ({} project pages)".format(
            len(built), len(project_pages)))

    if failures:
        print("\ncheck_head_parity: {} problem(s)".format(len(failures)))
        for failure in failures:
            print("  FAIL {}".format(failure))
        print("\nEvery page head must carry the same CSP and analytics tag. Update "
              "scripts/utils.py and the literal copies in {} and {} together.".format(
                  INDEX_HTML, PRIVACY_HTML))
        return 1

    if UMAMI_WEBSITE_ID == PLACEHOLDER_ID:
        # Not a failure: the heads agree, the site just is not collecting yet. Loud,
        # because a placeholder ID looks identical to a working install from the outside.
        print("\ncheck_head_parity: heads agree, but analytics is NOT LIVE -- "
              "UMAMI_WEBSITE_ID is still the placeholder.")
        print("  Paste the Website ID from the Umami dashboard into:")
        print("    scripts/utils.py  (UMAMI_WEBSITE_ID)")
        print("    {}".format(INDEX_HTML))
        print("    {}".format(PRIVACY_HTML))
        return 0

    print("\ncheck_head_parity: every head carries the same CSP and analytics tag")
    return 0


if __name__ == "__main__":
    sys.exit(main())

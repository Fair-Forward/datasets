"""Compute a per-entry sustainability / health signal for the catalog.

For every catalog entry this checks the in-scope links (dataset links + use-case/model/app
links) and produces a two-part signal:

  availability  -- the one signal comparable across all hosts: does any link resolve?
                   "available" / "unavailable" (with the specific dead links listed).
  context       -- an optional, platform-specific maintenance hint, shown only where the host
                   exposes it: "recently_updated" / "stable_archive" / "no_recent_updates".

The design is deliberately platform-aware. Reachability is the universal baseline. Recency is
read only from GitHub (last push) and Hugging Face (last modified) where those hosts are linked.
Archival platforms (Zenodo, Harvard Dataverse) are intentionally frozen and permanently citable,
so they are surfaced as a positive "stable_archive", never penalised for being old.

Network/API failures degrade gracefully: a failed enrichment call is skipped for that link, and
the entry still gets its availability plus whatever context is derivable.

Output: public/data/health.json and docs/data/health.json (the same dual-location pattern
catalog.json uses), so the live site picks up the signal without an app rebuild.
"""
import json
import math
import os
import re
import argparse
from datetime import datetime, timezone

from utils import check_urls

parser = argparse.ArgumentParser(description='Compute per-entry health/sustainability signals.')
parser.add_argument('--input', type=str, default='public/data/catalog.json',
                    help='Path to catalog JSON')
parser.add_argument('--outputs', type=str, nargs='+',
                    default=['public/data/health.json', 'docs/data/health.json'],
                    help='Output paths for health.json (written to each)')
parser.add_argument('--timestamp', type=str, default=os.environ.get('RUN_TIMESTAMP', ''),
                    help='Run date (YYYY-MM-DD); defaults to today (UTC)')
args = parser.parse_args()

# Thresholds (days). Kept in sync with docs/health-thresholds.md.
RECENT_DAYS = 365        # < 12 months -> recently_updated
STALE_DAYS = 547         # > 18 months -> no_recent_updates (12-18 month band stays untagged)

# Activity scoring (feeds the catalog ranking). Documented in docs/health-thresholds.md.
ACTIVITY_ZERO_DAYS = 730   # recency decays to 0 at ~2 years since the last activity
ARCHIVE_RECENCY = 0.6      # stable archives: durable & citable -- positive, but not "fresh"
POP_LOG_FULL = 4           # 10^4 (=10,000) downloads/stars saturates popularity at 1.0

# Statuses that mean "the resource exists but blocks automated or unauthenticated requests".
# A human reaches these fine in a browser, so we must NOT claim the link is unavailable --
# doing so would put a false statement on the site (the catalog's data-quality bar is strict).
_ACCESS_RESTRICTED = {401, 403, 405, 406, 409, 429}
# Hosts that routinely return misleading 404s to non-browser clients (bot protection); a 404
# from these is treated as "exists" rather than "gone".
_UNRELIABLE_404_HOSTS = ('kaggle.com',)

GITHUB_API = 'https://api.github.com/repos/{owner}/{repo}'
HF_API = 'https://huggingface.co/api/{kind}/{repo_id}'

# GitHub path segments that are not user/repo pairs.
_GITHUB_RESERVED = {
    'orgs', 'about', 'features', 'marketplace', 'sponsors', 'topics', 'collections',
    'settings', 'notifications', 'explore', 'pulls', 'issues', 'search', 'apps',
}


def run_date():
    """Resolve the run date string (YYYY-MM-DD)."""
    if args.timestamp:
        return args.timestamp[:10]
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def in_scope_urls(entry):
    """Collect http(s) URLs from dataset_links + usecase_links (the model/app/demo links)."""
    urls = []
    for link in (entry.get('dataset_links', []) + entry.get('usecase_links', [])):
        url = (link.get('url') or '').strip()
        if url.startswith('http'):
            urls.append(url)
    # Preserve order, drop duplicates.
    return list(dict.fromkeys(urls))


def parse_github(url):
    """Return (owner, repo) for a github.com repository URL, else None."""
    m = re.match(r'https?://github\.com/([^/\s?#]+)/([^/\s?#]+)', url, re.I)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2).removesuffix('.git')
    if owner.lower() in _GITHUB_RESERVED:
        return None
    return owner, repo


def parse_hf(url):
    """Return (kind, repo_id) for a huggingface.co model/dataset/space URL, else None.

    kind is one of 'models' | 'datasets' | 'spaces' (matching the HF API namespace).
    """
    m = re.match(r'https?://huggingface\.co/(.+)', url, re.I)
    if not m:
        return None
    parts = [p for p in m.group(1).split('?')[0].split('#')[0].strip('/').split('/') if p]
    if not parts:
        return None
    kind = 'models'
    if parts[0] == 'datasets':
        kind, parts = 'datasets', parts[1:]
    elif parts[0] == 'spaces':
        kind, parts = 'spaces', parts[1:]
    if len(parts) < 2:
        # A single segment is an org/user page, not a specific asset -- no stats to read.
        return None
    return kind, f'{parts[0]}/{parts[1]}'


def is_archive_url(url):
    """True for DOI archive hosts (Zenodo, Harvard Dataverse) -- stable & citable by design."""
    low = url.lower()
    return (
        'zenodo.org/record' in low
        or 'zenodo.org/doi' in low
        or 'doi.org/10.5281/zenodo' in low
        or 'dataverse.harvard.edu' in low
    )


def is_reachable(url, result):
    """Conservative reachability: only a genuine, unambiguous failure counts as unreachable.

    Access-restricted statuses (auth/bot blocks) and known-unreliable 404 hosts are treated as
    reachable, because the resource almost certainly works in a real browser. Genuine failures --
    404/410 on reliable hosts, 5xx, and connection/timeout/DNS errors -- count as unreachable.
    """
    if result is None:
        return True  # never checked -> do not assert a failure
    if result.get('ok'):
        return True
    status = result.get('status')
    if status in _ACCESS_RESTRICTED:
        return True
    if status == 404 and any(host in url.lower() for host in _UNRELIABLE_404_HOSTS):
        return True
    return False


def days_since(iso_date):
    """Whole days between an ISO datetime/date string and now (UTC). None if unparseable."""
    if not iso_date:
        return None
    try:
        text = iso_date.replace('Z', '+00:00')
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except ValueError:
        return None


def fetch_github(owner, repo, cache):
    """Fetch {pushed_at, archived, days_since_commit} for a repo, cached. None on failure."""
    import requests
    key = f'{owner}/{repo}'
    if key in cache:
        return cache[key]

    headers = {'Accept': 'application/vnd.github+json',
               'User-Agent': 'FairForward-DataCatalog/1.0'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    result = None
    try:
        resp = requests.get(GITHUB_API.format(owner=owner, repo=repo),
                            headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            pushed_at = data.get('pushed_at')
            result = {
                'repo': key,
                'pushed_at': pushed_at,
                'archived': bool(data.get('archived')),
                'days_since_commit': days_since(pushed_at),
                'stars': data.get('stargazers_count'),
            }
    except (requests.exceptions.RequestException, ValueError):
        result = None

    cache[key] = result
    return result


def fetch_hf(kind, repo_id, cache):
    """Fetch {downloads, likes, last_modified} for an HF asset, cached. None on failure."""
    import requests
    key = f'{kind}/{repo_id}'
    if key in cache:
        return cache[key]

    headers = {'User-Agent': 'FairForward-DataCatalog/1.0'}
    result = None
    try:
        resp = requests.get(HF_API.format(kind=kind, repo_id=repo_id),
                            headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            last_modified = data.get('lastModified')
            result = {
                'id': repo_id,
                'kind': kind,
                'downloads': data.get('downloads'),
                'likes': data.get('likes'),
                'last_modified': last_modified,
                'days_since_modified': days_since(last_modified),
            }
    except (requests.exceptions.RequestException, ValueError):
        result = None

    cache[key] = result
    return result


def compute_context(has_archive, github, hf):
    """Derive the optional context tag. Archive takes precedence over recency."""
    if has_archive:
        return 'stable_archive'

    # Most recent activity across any GitHub/HF source we could read.
    recency_days = []
    if github:
        if github.get('archived'):
            return 'no_recent_updates'
        if github.get('days_since_commit') is not None:
            recency_days.append(github['days_since_commit'])
    if hf and hf.get('days_since_modified') is not None:
        recency_days.append(hf['days_since_modified'])

    if not recency_days:
        return None
    freshest = min(recency_days)
    if freshest < RECENT_DAYS:
        return 'recently_updated'
    if freshest > STALE_DAYS:
        return 'no_recent_updates'
    return None  # 12-18 month band: no nagging.


def _recency_component(context, github, hf):
    """0-1 recency signal, or None when no host exposes activity. Archives score a fixed mid value."""
    if context == 'stable_archive':
        return ARCHIVE_RECENCY
    if github and github.get('archived'):
        return 0.0
    days = [d for d in (
        github.get('days_since_commit') if github else None,
        hf.get('days_since_modified') if hf else None,
    ) if d is not None]
    if not days:
        return None
    return max(0.0, min(1.0, 1 - min(days) / ACTIVITY_ZERO_DAYS))


def _popularity_component(github, hf):
    """0-1 popularity from HF downloads / GitHub stars (log-scaled), or None if neither exists."""
    metrics = []
    if hf and isinstance(hf.get('downloads'), int):
        metrics.append(hf['downloads'])
    if github and isinstance(github.get('stars'), int):
        metrics.append(github['stars'])
    if not metrics:
        return None
    return max(0.0, min(1.0, math.log10(max(metrics) + 1) / POP_LOG_FULL))


def compute_activity(context, github, hf):
    """0-100 activity score from recency + popularity, or None when the entry exposes no signal.

    Recency is weighted above popularity because more hosts expose it. Returns None (not 0) when
    there is nothing to measure, so the ranking stays neutral for non-GitHub/HF entries instead of
    penalising them for their host. See docs/health-thresholds.md.
    """
    recency = _recency_component(context, github, hf)
    popularity = _popularity_component(github, hf)
    parts = []
    if recency is not None:
        parts.append((recency, 0.6))
    if popularity is not None:
        parts.append((popularity, 0.4))
    if not parts:
        return None
    total_weight = sum(w for _, w in parts)
    return round(100 * sum(value * w for value, w in parts) / total_weight)


def build_entry_health(entry, link_results, checked_at, gh_cache, hf_cache):
    """Assemble the health record for one catalog entry, or None if it has no in-scope links."""
    urls = in_scope_urls(entry)
    if not urls:
        return None

    reachable = [u for u in urls if is_reachable(u, link_results.get(u))]
    broken_links = [u for u in urls if u not in reachable]
    availability = 'available' if reachable else 'unavailable'

    has_archive = any(is_archive_url(u) for u in urls)

    # Enrichment: take the first GitHub/HF asset we can resolve among the entry's links.
    github = None
    hf = None
    for url in urls:
        if github is None:
            gh = parse_github(url)
            if gh:
                github = fetch_github(gh[0], gh[1], gh_cache)
        if hf is None:
            parsed = parse_hf(url)
            if parsed:
                hf = fetch_hf(parsed[0], parsed[1], hf_cache)

    context = compute_context(has_archive, github, hf)

    return {
        'availability': availability,
        'checked_at': checked_at,
        'context': context,
        'activity_score': compute_activity(context, github, hf),
        'link_count': len(urls),
        'broken_links': broken_links,
        'github': github,
        'hf': hf,
    }


def main():
    if not os.path.exists(args.input):
        print(f'Error: {args.input} not found. Run generate_catalog_data.py first.')
        raise SystemExit(1)

    with open(args.input, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    projects = catalog.get('projects', [])
    checked_at = run_date()

    # One batched reachability pass across every in-scope URL in the catalog.
    all_urls = []
    for p in projects:
        all_urls.extend(in_scope_urls(p))
    print(f'Checking reachability of {len(set(all_urls))} unique links...')
    link_results = check_urls(all_urls)

    gh_cache, hf_cache = {}, {}
    entries = {}
    for p in projects:
        pid = p.get('id')
        if not pid:
            continue
        record = build_entry_health(p, link_results, checked_at, gh_cache, hf_cache)
        if record:
            entries[pid] = record

    available = sum(1 for r in entries.values() if r['availability'] == 'available')
    print(f'  {len(entries)} entries with links | {available} available, '
          f'{len(entries) - available} unavailable')

    output = {'generated_at': checked_at, 'entries': entries}
    for path in args.outputs:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f'  Wrote {path}')


if __name__ == '__main__':
    main()

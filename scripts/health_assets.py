"""Which catalogue links are open assets, and which of those the health check can measure.

A project's dataset and use-case links are classified by host. GitHub repositories, Hugging Face
models, datasets and spaces, and Zenodo records are measured (see chaoss_metrics.py). GitLab,
Kaggle, Harvard Dataverse, figshare, other DOIs and organisation pages are open hosts we do not
measure yet; everything else is a website. DOIs are followed where the prefix names the platform.
"""
import re
from collections import Counter
from urllib.parse import unquote, urlparse

# Every host except a plain website: a repository, model, dataset or record someone can reuse.
OPEN_HOSTS = frozenset({
    'github', 'github_org', 'gitlab', 'huggingface', 'huggingface_org', 'zenodo', 'dataverse',
    'kaggle', 'figshare', 'doi_other',
})
MEASURED_PLATFORMS = ('github', 'huggingface', 'zenodo')

# GitHub path segments that are not user/repo pairs.
_GITHUB_RESERVED = {
    'orgs', 'about', 'features', 'marketplace', 'sponsors', 'topics', 'collections',
    'settings', 'notifications', 'explore', 'pulls', 'issues', 'search', 'apps',
}


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
    m = re.match(r'https?://(?:www\.)?github\.com/([^/\s?#]+)/([^/\s?#]+)', url, re.I)
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
    m = re.match(r'https?://(?:www\.)?(?:huggingface\.co|hf\.co)/(.+)', url, re.I)
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


def _info(host, platform=None, id_=None, kind=None, doi=None):
    return {'host': host, 'platform': platform, 'id': id_, 'kind': kind, 'doi': doi}


def _classify_doi(doi):
    low = doi.lower()
    zenodo = re.match(r'10\.5281/zenodo\.(\d+)$', low)
    if zenodo:
        return _info('zenodo', 'zenodo', zenodo.group(1), doi=doi)
    if low.startswith('10.57967/hf/'):
        # A Hugging Face DOI names the repository only through the DOI resolver.
        return _info('huggingface', 'huggingface', doi=doi)
    if low.startswith('10.7910/dvn'):
        return _info('dataverse', doi=doi)
    return _info('doi_other', doi=doi)


def classify_url(url):
    """{host, platform, id, kind, doi} for one link. platform is set only for measured hosts."""
    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower().removeprefix('www.')
    segments = [s for s in parsed.path.split('/') if s]

    if netloc in ('doi.org', 'dx.doi.org'):
        return _classify_doi(unquote(parsed.path.lstrip('/')))
    if netloc == 'github.com':
        repo = parse_github(url)
        if repo:
            return _info('github', 'github', f'{repo[0]}/{repo[1]}')
        if len(segments) == 1 and segments[0].lower() not in _GITHUB_RESERVED:
            return _info('github_org')
        return _info('website')
    if netloc in ('huggingface.co', 'hf.co'):
        asset = parse_hf(url)
        if asset:
            return _info('huggingface', 'huggingface', asset[1], asset[0])
        return _info('huggingface_org') if segments else _info('website')
    if netloc == 'zenodo.org':
        record = re.search(r'/records?/(\d+)', parsed.path) or re.search(r'zenodo\.(\d+)', parsed.path)
        if record:
            return _info('zenodo', 'zenodo', record.group(1))
        return _info('website')
    if netloc == 'gitlab.com' and segments:
        return _info('gitlab')
    if netloc == 'kaggle.com' and segments:
        return _info('kaggle')
    if netloc == 'dataverse.harvard.edu':
        return _info('dataverse')
    if (netloc == 'figshare.com' or netloc.endswith('.figshare.com')) and 'account' not in segments:
        return _info('figshare')
    return _info('website')


def _asset_key(info):
    if info['platform'] == 'github':
        return 'github:' + info['id'].lower()
    if info['platform'] == 'huggingface':
        if info['id'] is None:
            return 'doi:' + info['doi'].lower()
        return f"huggingface:{info['kind']}/{info['id']}".lower()
    return 'zenodo:' + info['id']


def discover_assets(entry):
    """The measurable assets among an entry's in-scope links, once each, in link order."""
    assets, seen = [], set()
    for url in in_scope_urls(entry):
        info = classify_url(url)
        if info['platform'] not in MEASURED_PLATFORMS:
            continue
        key = _asset_key(info)
        if key in seen:
            continue
        seen.add(key)
        assets.append({'key': key, 'platform': info['platform'], 'id': info['id'],
                       'kind': info['kind'], 'url': url, 'doi': info['doi']})
    return assets


def host_counts(entry):
    """{host: number of in-scope links}, sorted by host for stable output."""
    counts = Counter(classify_url(url)['host'] for url in in_scope_urls(entry))
    return dict(sorted(counts.items()))

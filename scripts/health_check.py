"""Compute the per-entry health signal for the catalog, including open-source health facts.

For every catalog entry this checks the in-scope links (dataset links + use-case/model/app links)
and produces:

  availability  -- the one signal comparable across all hosts: does any link resolve?
                   "available" / "unavailable" (with the specific dead links listed).
  context       -- an optional status tag where a host exposes it: "recently_updated" /
                   "stable_archive" / "no_recent_updates".
  oss           -- open-source health facts for every GitHub repository, Hugging Face model,
                   dataset or space and Zenodo record the entry links, following CHAOSS metric
                   definitions (chaoss_metrics.py). Facts, never scores; gaps are named.
  compare       -- the yes/no facts the Insights page and the private report count, decided here
                   once so both apply the same policy.

Reachability is the universal baseline. Archival platforms (Zenodo, Harvard Dataverse) are frozen
and permanently citable, so they are surfaced as a positive "stable_archive", never penalised. A
source that cannot be reached this week keeps its previous measurement, with its own date, for up
to chaoss_metrics.CARRY_FORWARD_MAX_DAYS.

Output: public/data/health.json and docs/data/health.json (the same dual-location pattern
catalog.json uses), so the live site picks up the signal without an app rebuild. The whole file is
public: counts and dates only, never names, usernames or email addresses. validate_health() checks
that before anything is written. See docs/health-thresholds.md.
"""
import argparse
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import chaoss_metrics as cm
from health_assets import OPEN_HOSTS, discover_assets, host_counts, in_scope_urls, is_archive_url
from health_sources import (TRANSIENT, ApiClient, SourceError, fetch_github_repo, fetch_hf_asset,
                            fetch_zenodo_record, resolve_doi)

SCHEMA_VERSION = 2
DEFAULT_OUTPUTS = ('public/data/health.json', 'docs/data/health.json')
METHOD_PAGE = 'https://fair-forward.github.io/datasets/open-source-health/'
USER_AGENT = 'FairForward-DataCatalog/1.0 (+https://fair-forward.github.io/datasets/)'

# Projects whose partners asked us to leave out the open-source health facts (CHAOSS recommends
# offering an opt-out). Their links are still checked. Note who asked and when beside the id.
OPT_OUT_IDS = frozenset()

OSS_STATUSES = frozenset({'measured', 'partial', 'carried_forward', 'unreadable', 'opted_out'})

# Statuses that mean "the resource exists but blocks automated or unauthenticated requests".
# A human reaches these fine in a browser, so we must NOT claim the link is unavailable --
# doing so would put a false statement on the site (the catalog's data-quality bar is strict).
_ACCESS_RESTRICTED = {401, 403, 405, 406, 409, 429}
# Hosts that routinely return misleading 404s to non-browser clients (bot protection); a 404
# from these is treated as "exists" rather than "gone".
_UNRELIABLE_404_HOSTS = ('kaggle.com',)

# Keys that would carry a person's identity. None may appear anywhere in the written file.
_IDENTITY_KEYS = frozenset({'login', 'logins', 'email', 'emails', 'name', 'names', 'author',
                            'authors', 'user', 'users'})
_PLATFORMS = ('github', 'huggingface', 'zenodo')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Compute per-entry health signals and open-source health facts.')
    parser.add_argument('--input', default='public/data/catalog.json', help='Path to catalog JSON')
    parser.add_argument('--outputs', nargs='+', default=None,
                        help='Output paths for health.json (written to each)')
    parser.add_argument('--timestamp', default=os.environ.get('RUN_TIMESTAMP', ''),
                        help='Run date (YYYY-MM-DD); defaults to today (UTC)')
    parser.add_argument('--previous', default=None,
                        help='Previous health.json whose measurements may be carried forward '
                             '(default: the first output)')
    parser.add_argument('--only', default='',
                        help='Comma-separated project ids to check (debugging; needs --outputs)')
    parser.add_argument('--summary', default='',
                        help='Also write a Markdown run summary here (the weekly PR body)')
    parser.add_argument('--github-budget', type=int, default=800,
                        help='Most GitHub API requests to make (GITHUB_TOKEN allows 1,000 per hour '
                             'per repository)')
    args = parser.parse_args(argv)
    if args.only and args.outputs is None:
        parser.error('--only writes a partial file; pass --outputs explicitly')
    if args.outputs is None:
        args.outputs = list(DEFAULT_OUTPUTS)
    if args.previous is None:
        args.previous = args.outputs[0]
    return args


def run_date_from(timestamp):
    """Resolve the run date string (YYYY-MM-DD)."""
    if timestamp:
        return timestamp[:10]
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


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


def load_previous(path):
    """Entries of an earlier health.json, or {} when there is none to carry forward from."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get('entries') or {}
    except (OSError, ValueError, AttributeError):
        return {}


def make_clients(github_budget):
    github_headers = {'Accept': 'application/vnd.github+json', 'User-Agent': USER_AGENT,
                      'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        github_headers['Authorization'] = f'Bearer {token}'
    return {
        'github': ApiClient('GitHub', github_headers, budget=github_budget),
        'huggingface': ApiClient('Hugging Face', {'User-Agent': USER_AGENT}, budget=400, min_interval=0.25),
        'zenodo': ApiClient('Zenodo', {'User-Agent': USER_AGENT, 'Accept': 'application/json'},
                            budget=60, min_interval=0.5),
        'doi': ApiClient('doi.org', {'User-Agent': USER_AGENT}, budget=20),
    }


def fetch_asset(asset, clients, window):
    if asset['platform'] == 'github':
        owner, repo = asset['id'].split('/', 1)
        return fetch_github_repo(clients['github'], owner, repo, window)
    if asset['platform'] == 'huggingface':
        return fetch_hf_asset(clients['huggingface'], asset['kind'], asset['id'], window)
    return fetch_zenodo_record(clients['zenodo'], asset['id'], window)


def _resolve(asset, client, cache):
    """A Hugging Face DOI asset with its repository filled in, or (asset, error)."""
    doi = asset['doi']
    if doi not in cache:
        try:
            cache[doi] = resolve_doi(client, doi)
        except SourceError as err:
            cache[doi] = err
    found = cache[doi]
    if isinstance(found, SourceError):
        return asset, found
    if not found or found.get('platform') != asset['platform'] or not found.get('id'):
        return asset, SourceError('unavailable', detail='the DOI does not name a repository')
    key = f"huggingface:{found['kind']}/{found['id']}".lower()
    return {'key': key, 'platform': 'huggingface', 'id': found['id'], 'kind': found['kind'],
            'url': asset['url'], 'doi': doi, 'resolved_from': doi}, None


def collect(projects, clients, window):
    """Discover each project's assets, resolve DOIs, and fetch every asset once.

    Returns ({project id: [asset]}, {asset key: fetcher result or SourceError}).
    """
    assets_by_project, observations, dois = {}, {}, {}
    for project in projects:
        unique = {}
        for asset in discover_assets(project):
            if asset['id'] is None and asset['doi']:
                asset, error = _resolve(asset, clients['doi'], dois)
                if error is not None:
                    observations[asset['key']] = error
            unique.setdefault(asset['key'], asset)  # a DOI can name a repository also linked directly
        assets_by_project[project['id']] = list(unique.values())

    for assets in assets_by_project.values():
        for asset in assets:
            if asset['key'] in observations:
                continue
            try:
                observations[asset['key']] = fetch_asset(asset, clients, window)
            except SourceError as err:
                observations[asset['key']] = err
                print(f"  not measured: {asset['platform']} {asset['id'] or asset['doi']} ({err.kind})")
    return assets_by_project, observations


def _sum(records, field):
    values = [r.get(field) for r in records if isinstance(r.get(field), int) and not isinstance(r.get(field), bool)]
    return sum(values) if values else None


def _releases(records, in_window, total, latest):
    dates = [r.get(latest) for r in records if r.get(latest)]
    return {'in_window': _sum(records, in_window) or 0, 'total': _sum(records, total) or 0,
            'latest_at': max(dates) if dates else None}


def _unique_concepts(records):
    """One Zenodo record per concept: its download and view counts already cover all versions."""
    by_concept = {}
    for record in records:
        concept = record.get('concept_id') or record['id']
        kept = by_concept.get(concept)
        if kept is None or (record.get('versions_total') or 0) > (kept.get('versions_total') or 0):
            by_concept[concept] = record
    return list(by_concept.values())


def _licenses(records):
    groups = {}
    for record in records:
        for license_ in record.get('license') or []:
            key = (license_['status'], license_['spdx'] or license_['raw'])
            if key in groups:
                groups[key]['assets'] += 1
            else:
                groups[key] = dict(license_, assets=1)
    return list(groups.values())


def _people_gap_reason(measured, people_buckets):
    if all(r['platform'] == 'zenodo' for r in measured):
        return 'archive_record'
    asset_reasons = {gap.get('reason') for r in measured for gap in r.get('gaps') or []}
    if 'gated' in asset_reasons:
        return 'gated'
    if 'empty_repository' in asset_reasons:
        return 'empty_repository'
    if people_buckets:
        return 'no_human_commits'
    return 'unreadable'


def summarise_entry(assets, observations, run_date):
    """The public open-source health block for one project: per-platform facts, named gaps, and
    one record per linked asset. People are combined per platform (one person counts once across a
    project's repositories) and never summed across platforms."""
    start, end = cm.window_bounds(run_date)
    records, measured, buckets = [], [], {}
    response_items, outside_prs = [], []
    failed = unreadable = 0
    for asset in assets:
        observation = observations.get(asset['key'])
        base = {'key': asset['key'], 'platform': asset['platform'], 'url': asset['url']}
        if not isinstance(observation, dict):
            transient = observation is None or observation.kind in TRANSIENT
            failed += transient
            unreadable += not transient
            records.append({**base, 'id': asset['id'], 'status': 'failed' if transient else 'unavailable'})
            continue
        record = {**base, **observation['record'], 'status': 'measured'}
        if asset.get('resolved_from'):
            record['resolved_from'] = asset['resolved_from']
        records.append(record)
        measured.append(record)
        if observation.get('people'):
            bucket = buckets.setdefault(record['platform'], {'all_time': {}, 'active': {}, 'assets': 0,
                                                             'fork_history': False})
            bucket['assets'] += 1
            bucket['fork_history'] = bucket['fork_history'] or bool(record.get('fork_of'))
            for key, count in observation['people']['all_time'].items():
                bucket['all_time'][key] = bucket['all_time'].get(key, 0) + count
            for key, count in observation['people']['active'].items():
                bucket['active'][key] = bucket['active'].get(key, 0) + count
        response_items.extend(observation.get('response_items') or [])
        outside_prs.extend(observation.get('outside_prs') or [])

    by = {platform: [r for r in measured if r['platform'] == platform] for platform in _PLATFORMS}
    by['zenodo'] = _unique_concepts(by['zenodo'])

    people = {}
    for platform in ('github', 'huggingface'):
        bucket = buckets.get(platform)
        if bucket:
            summary = cm.merge_people(bucket['all_time'], bucket['active'])
            if summary['total']:
                people[platform] = dict(summary, assets=bucket['assets'], fork_history=bucket['fork_history'])

    dated = [(r['last_change_at'], r['platform'], bool(r.get('archived'))) for r in measured if r.get('last_change_at')]
    live = [d for d in dated if not d[2]]
    pick = max(live or dated) if dated else None

    releases = {}
    if by['github']:
        releases['github'] = _releases(by['github'], 'releases_in_window', 'releases_total', 'latest_release_at')
    if by['zenodo']:
        releases['zenodo'] = _releases(by['zenodo'], 'versions_in_window', 'versions_total', 'last_change_at')

    reuse = {}
    if by['github']:
        reuse['github'] = {'forks': _sum(by['github'], 'forks'), 'stars': _sum(by['github'], 'stars')}
    if by['huggingface']:
        reuse['huggingface'] = {'downloads_30d': _sum(by['huggingface'], 'downloads_30d'),
                                'downloads_all_time': _sum(by['huggingface'], 'downloads_all_time'),
                                'likes': _sum(by['huggingface'], 'likes')}
    if by['zenodo']:
        reuse['zenodo'] = {'downloads': _sum(by['zenodo'], 'downloads_all_time'),
                           'views': _sum(by['zenodo'], 'views_all_time')}

    licenses = {platform: _licenses(by[platform]) for platform in _PLATFORMS if by[platform]}

    gaps, first_response, change_requests = [], None, None
    if by['github']:
        first_response, gap = cm.first_response_summary(response_items, end)
        gaps.extend([gap] if gap else [])
        change_requests, gap = cm.closure_summary(outside_prs)
        gaps.extend([gap] if gap else [])
    elif measured:
        gaps += [{'metric': 'first_response', 'reason': 'github_only'},
                 {'metric': 'change_request_closure', 'reason': 'github_only'}]
    if measured and not releases:
        gaps.append({'metric': 'releases', 'reason': 'no_releases_on_platform'})
    if measured and not people:
        reason = _people_gap_reason(measured, buckets)
        gaps += [{'metric': 'contributors', 'reason': reason}, {'metric': 'absence_factor', 'reason': reason}]
    for record in measured:
        for gap in record.get('gaps') or []:
            covered = people and gap.get('metric') in ('contributors', 'absence_factor')
            if not covered and gap not in gaps:
                gaps.append(gap)

    return {
        'status': 'partial' if failed else ('measured' if measured else 'unreadable'),
        'measured_at': run_date,
        'window': {'start': start.date().isoformat(), 'end': (end - timedelta(days=1)).date().isoformat()},
        'scope': {'github': len(by['github']), 'huggingface': len(by['huggingface']),
                  'zenodo': len(by['zenodo']), 'unreadable': unreadable, 'failed': failed},
        'last_change': {'at': pick[0], 'platform': pick[1], 'archived': pick[2]} if pick else None,
        'people': people,
        'releases': releases,
        'reuse': reuse,
        'license': licenses,
        'first_response': first_response,
        'change_requests': change_requests,
        'gaps': gaps,
        'assets': records,
    }


def carry_forward(fresh, previous, run_date):
    """Keep last week's block when this week's could not read every source.

    Only a block measured within CARRY_FORWARD_MAX_DAYS and covering the same assets is kept, with
    its own measured_at. A person counted across two repositories cannot be re-combined from stored
    counts, so the whole block is kept or replaced, never mixed.
    """
    if not fresh or fresh.get('status') != 'partial' or not previous:
        return fresh
    if previous.get('status') not in ('measured', 'carried_forward'):
        return fresh
    age = cm.days_between(previous.get('measured_at'), run_date)
    if age is None or age > cm.CARRY_FORWARD_MAX_DAYS:
        return fresh
    same_assets = sorted(a['key'] for a in previous.get('assets') or []) == \
        sorted(a['key'] for a in fresh.get('assets') or [])
    return dict(previous, status='carried_forward') if same_assets else fresh


def compare_flags(hosts, oss):
    """Yes/no facts for counting across projects: never shown per project, never named.

    changed_12m leaves out projects measured only through archive records (stable by design);
    several_contributors leaves out projects without commit history to count people from.
    """
    flags = {'open_asset': any(host in OPEN_HOSTS for host in hosts), 'measured': False,
             'changed_12m': None, 'several_contributors': None}
    if not oss or oss.get('status') not in ('measured', 'partial', 'carried_forward'):
        return flags
    measured = [a for a in oss.get('assets') or [] if a.get('status') == 'measured']
    if not measured:
        return flags
    flags['measured'] = True
    if oss.get('last_change') and any(a['platform'] != 'zenodo' for a in measured):
        flags['changed_12m'] = oss['last_change']['at'] >= oss['window']['start']
    totals = [p['total'] for p in (oss.get('people') or {}).values() if p.get('total')]
    if totals:
        flags['several_contributors'] = max(totals) >= 2
    return flags


def _activity_inputs(oss):
    dated, popularity = [], []
    for record in (oss or {}).get('assets') or []:
        if record.get('status') != 'measured':
            continue
        if record.get('last_change_at'):
            dated.append({'at': record['last_change_at'], 'archived': bool(record.get('archived'))})
        for field in ('stars', 'downloads_30d'):
            if isinstance(record.get(field), int):
                popularity.append(record[field])
    return dated, popularity


def build_entry(project, link_results, assets, observations, previous_entry, run_date):
    """The health record for one catalog entry, or None if it has no in-scope links."""
    urls = in_scope_urls(project)
    if not urls:
        return None
    reachable = [u for u in urls if is_reachable(u, link_results.get(u))]
    hosts = host_counts(project)
    if project.get('id') in OPT_OUT_IDS:
        oss = {'status': 'opted_out'}
    elif assets:
        oss = carry_forward(summarise_entry(assets, observations, run_date),
                            (previous_entry or {}).get('oss'), run_date)
    else:
        oss = None
    dated, popularity = _activity_inputs(oss)
    context = cm.compute_context(any(is_archive_url(u) for u in urls), dated, run_date)
    return {
        'availability': 'available' if reachable else 'unavailable',
        'checked_at': run_date,
        'context': context,
        'activity_score': cm.compute_activity(context, dated, popularity, run_date),
        'link_count': len(urls),
        'broken_links': [u for u in urls if u not in reachable],
        'hosts': hosts,
        'compare': compare_flags(hosts, oss),
        'oss': oss,
    }


def validate_health(doc):
    """Raise ValueError unless the document is safe to publish: the expected schema, consistent
    counts, no dates after the run, and nothing that identifies a person."""
    problems = []
    if doc.get('schema_version') != SCHEMA_VERSION:
        problems.append(f'schema_version must be {SCHEMA_VERSION}')
    run = cm.parse_ts(doc.get('generated_at'))
    if run is None:
        problems.append('generated_at is not a date')
    for pid, entry in (doc.get('entries') or {}).items():
        if entry.get('availability') not in ('available', 'unavailable'):
            problems.append(f'{pid}: availability')
        oss = entry.get('oss')
        if oss is not None and oss.get('status') not in OSS_STATUSES:
            problems.append(f'{pid}: unknown oss status')
        for platform, counts in ((oss or {}).get('people') or {}).items():
            total = counts.get('total') or 0
            if (counts.get('active') or 0) > total or (counts.get('absence_factor') or 0) > total:
                problems.append(f'{pid}: inconsistent {platform} people counts')

    def walk(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).lower() in _IDENTITY_KEYS:
                    problems.append(f'{path}.{key}: identity field')
                walk(child, f'{path}.{key}')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f'{path}[{index}]')
        elif isinstance(value, bool) or value is None:
            return
        elif isinstance(value, (int, float)):
            if value < 0:
                problems.append(f'{path}: negative number')
        elif isinstance(value, str):
            if '@' in value and not value.startswith(('http://', 'https://')):
                problems.append(f'{path}: looks like an email address')
            if run is not None and path.endswith(('_at', '.at')):
                moment = cm.parse_ts(value)
                if moment is not None and moment.date() > run.date():
                    problems.append(f'{path}: date after the run')

    walk(doc.get('entries') or {}, 'entries')
    if problems:
        raise ValueError('health.json failed validation:\n  ' + '\n  '.join(problems[:25]))


def should_abort(stats):
    """Refuse to write when most sources failed and some project would lose its measurement."""
    attempted = stats.get('attempted') or 0
    return attempted > 0 and (stats.get('transient') or 0) * 2 > attempted and (stats.get('degraded') or 0) > 0


def method_block():
    return {'page': METHOD_PAGE, 'window_days': cm.WINDOW_DAYS, 'min_outside_items': cm.MIN_OUTSIDE_ITEMS,
            'min_outside_change_requests': cm.MIN_OUTSIDE_CHANGE_REQUESTS, 'min_group': cm.MIN_GROUP,
            'absence_share': cm.ABSENCE_SHARE}


def render_summary(doc, stats):
    """A Markdown run summary for the weekly PR. Counts and public asset ids only."""
    entries = doc.get('entries') or {}
    available = sum(1 for e in entries.values() if e.get('availability') == 'available')
    statuses = Counter((e.get('oss') or {}).get('status') for e in entries.values() if e.get('oss'))
    assets, not_measured = Counter(), []
    for pid, entry in entries.items():
        for asset in (entry.get('oss') or {}).get('assets') or []:
            if asset.get('status') == 'measured':
                assets[asset['platform']] += 1
            else:
                not_measured.append(f"{pid}: {asset['platform']} {asset.get('id') or asset['key']} ({asset['status']})")
    requests_line = ', '.join(f"{host} {used} of {stats.get('budgets', {}).get(host, '?')}"
                              for host, used in (stats.get('requests') or {}).items())
    lines = [
        f"## Weekly health check {doc.get('generated_at')}",
        '',
        f'- Links: {len(entries)} projects checked, {available} available, {len(entries) - available} unavailable',
        f"- Open-source health, following CHAOSS metric definitions: {statuses['measured']} measured, "
        f"{statuses['partial']} partial, {statuses['carried_forward']} carried forward, "
        f"{statuses['unreadable']} unreadable, {statuses['opted_out']} opted out",
        f"- Asset links measured: GitHub {assets['github']}, Hugging Face {assets['huggingface']}, "
        f"Zenodo {assets['zenodo']}",
        f'- API requests: {requests_line}',
        f'- Method: {METHOD_PAGE}',
    ]
    if not_measured:
        lines += ['', '<details><summary>Asset links not measured this week</summary>', '']
        lines += [f'- {line}' for line in not_measured] + ['', '</details>']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    args = parse_args(argv)
    if not os.path.exists(args.input):
        print(f'Error: {args.input} not found. Run generate_catalog_data.py first.')
        raise SystemExit(1)

    with open(args.input, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    projects = [p for p in catalog.get('projects', []) if p.get('id')]
    if args.only:
        wanted = {pid.strip() for pid in args.only.split(',') if pid.strip()}
        projects = [p for p in projects if p['id'] in wanted]
    checked_at = run_date_from(args.timestamp)
    previous = load_previous(args.previous)

    # Imported here: utils pulls in pandas, which the unit tests do not need.
    from utils import check_urls

    # One batched reachability pass across every in-scope URL in the catalog.
    all_urls = [url for p in projects for url in in_scope_urls(p)]
    print(f'Checking reachability of {len(set(all_urls))} unique links...')
    link_results = check_urls(all_urls)

    print('Reading open-source activity (CHAOSS metric definitions)...')
    clients = make_clients(args.github_budget)
    assets_by_project, observations = collect(projects, clients, cm.window_bounds(checked_at))

    entries = {}
    for p in projects:
        entry = build_entry(p, link_results, assets_by_project.get(p['id'], []), observations,
                            previous.get(p['id']), checked_at)
        if entry:
            entries[p['id']] = entry

    output = {'schema_version': SCHEMA_VERSION, 'generated_at': checked_at, 'method': method_block(),
              'entries': entries}
    try:
        validate_health(output)
    except ValueError as err:
        print(f'Error: {err}')
        raise SystemExit(1)

    errors = [o for o in observations.values() if isinstance(o, SourceError)]
    stats = {
        'attempted': len(observations),
        'transient': sum(1 for e in errors if e.kind in TRANSIENT),
        'degraded': sum(1 for e in entries.values() if (e.get('oss') or {}).get('status') == 'partial'),
        'carried': sum(1 for e in entries.values() if (e.get('oss') or {}).get('status') == 'carried_forward'),
        'requests': {c.name: c.used for c in clients.values()},
        'budgets': {c.name: c.budget for c in clients.values()},
    }
    if should_abort(stats):
        print(f"Error: {stats['transient']} of {stats['attempted']} sources failed and "
              f"{stats['degraded']} projects would lose their measurement; not writing.")
        raise SystemExit(1)

    available = sum(1 for r in entries.values() if r['availability'] == 'available')
    measured = sum(1 for r in entries.values() if r['compare']['measured'])
    print(f'  {len(entries)} entries with links | {available} available, '
          f'{len(entries) - available} unavailable | {measured} with open-source health facts')
    print('  API requests: ' + ', '.join(f'{name} {used}' for name, used in stats['requests'].items()))

    for path in args.outputs:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f'  Wrote {path}')
    if args.summary:
        with open(args.summary, 'w', encoding='utf-8') as f:
            f.write(render_summary(output, stats))
        print(f'  Wrote {args.summary}')


if __name__ == '__main__':
    main()

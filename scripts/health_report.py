"""Private comparison report for the open-source health facts. Never published.

CHAOSS advises against comparing projects with each other, so the public site shows each project's
own facts and compares SDGs only without names. This report is the named comparison the team uses
to see patterns and fix links: coverage and upkeep by SDG, how far the CHAOSS Starter Project Health
model can be computed, one row per project, and data-quality flags a maintainer can act on. A CSV
keyed by "Project ID" can be joined in (for example an assessment kept elsewhere); its categorical
columns are cross-tabulated against the measured facts.

Output, in --out (which must lie outside this repository): index.html (self-contained, noindex),
projects.csv, by_sdg.csv and flags.csv. The catalogue's contact field is never read.

Usage:
  python scripts/health_report.py --out ~/reports/open-source-health [--join assessment.csv]
"""
import argparse
import csv
import html
import json
import os
import re
import statistics
from collections import Counter
from pathlib import Path

import chaoss_metrics as cm
from health_assets import discover_assets
from text_parsing import license_parts

REPO_ROOT = Path(__file__).resolve().parents[1]
JOIN_KEY = 'Project ID'
MAX_CATEGORIES = 6
_INTERNAL = ('sdg_list', 'platform_set', 'flag_details')


def ensure_outside_repo(path):
    """The resolved output directory, or ValueError when it lies inside this repository."""
    resolved = Path(path).expanduser().resolve()
    # Compare existing ancestors as files, so another letter case on a case-insensitive disk
    # cannot slip past.
    for candidate in (resolved, *resolved.parents):
        if candidate == REPO_ROOT or (candidate.exists() and os.path.samefile(candidate, REPO_ROOT)):
            raise ValueError(f'{resolved} is inside the repository; the report is private, write it elsewhere')
    return resolved


def _source_licenses(oss):
    found = []
    for items in (oss.get('license') or {}).values():
        for item in items:
            if item.get('status') == 'detected' and item.get('spdx') and item['spdx'] not in found:
                found.append(item['spdx'])
    return found


def _license_flags(project, oss):
    source = _source_licenses(oss)
    if not source:
        return []
    parts = license_parts(project.get('license') or '')
    if parts is None:
        return [('license_missing', f"the catalogue records no licence; the source declares {', '.join(source)}")]
    catalogue = parts.get('spdx') or cm.SPDX_CANONICAL.get(re.sub(r'\s+', '-', (parts.get('name') or '').strip()).lower())
    if catalogue and catalogue.lower() in {s.lower() for s in source}:
        return []
    shown = parts.get('name') or project.get('license')
    return [('license_differs', f"catalogue: {shown}; source declares {', '.join(source)} "
                                f"(code and data licences can legitimately differ)")]


def quality_flags(project, entry):
    """[(kind, detail)] for link and record problems a maintainer can fix in the Sheet."""
    flags = []
    oss = (entry or {}).get('oss') or {}
    for asset in oss.get('assets') or []:
        ident = asset.get('id') or asset.get('key')
        if asset.get('status') == 'unavailable':
            flags.append(('unreadable', f"{asset['platform']} {ident} could not be read (private, removed or blocked)"))
        elif asset.get('status') == 'failed':
            flags.append(('failed', f"{asset['platform']} {ident} could not be reached this run"))
        if asset.get('renamed_from'):
            flags.append(('renamed', f"linked as {asset['renamed_from']}, now {asset['id']}"))
        if asset.get('fork'):
            original = asset.get('fork_of') or 'a repository under a personal account'
            flags.append(('fork_linked', f"{asset['id']} is a fork of {original}"))
        if asset.get('archived'):
            flags.append(('archived', f"{asset['id']} is archived by its maintainers"))
        if asset.get('linked_is_latest') is False:
            flags.append(('superseded_version', f"Zenodo record {asset['id']} is an older version; "
                                                f"the latest is {asset.get('latest_id') or 'unknown'}"))
        if asset.get('gated'):
            flags.append(('gated', f"{asset['id']} is gated ({asset['gated']})"))
        if asset.get('resolved_from'):
            flags.append(('doi_resolved', f"DOI {asset['resolved_from']} resolves to {asset['id']}"))
    hosts = (entry or {}).get('hosts') or {}
    org_links = (hosts.get('github_org') or 0) + (hosts.get('huggingface_org') or 0)
    if org_links:
        flags.append(('org_page', f'{org_links} link(s) to an organisation page rather than a repository'))
    flags += _license_flags(project, oss)

    links = [(link.get('url') or '').strip() for link in project.get('dataset_links', []) + project.get('usecase_links', [])]
    links = [url for url in links if url]
    for url in sorted({url for url in links if links.count(url) > 1}):
        flags.append(('duplicate_link', f'{url} is listed more than once'))
    in_scope = {asset['key'] for asset in discover_assets(project)}
    additional = {'dataset_links': project.get('additional_resources', []), 'usecase_links': []}
    for asset in discover_assets(additional):
        if asset['key'] not in in_scope:
            flags.append(('additional_only', f"{asset['platform']} {asset['id'] or asset['doi']} is listed only "
                                             f"under additional resources, so it is not measured"))
    return flags


def _files(github_assets, name):
    profiled = [a for a in github_assets if a.get('files')]
    if not profiled:
        return None
    return f"{sum(1 for a in profiled if a['files'].get(name))} of {len(profiled)}"


def project_rows(catalog, health, joined):
    """One row per catalogue project with its measured facts, flags and joined columns."""
    entries = (health or {}).get('entries') or {}
    run = (health or {}).get('generated_at')
    rows = []
    for project in catalog.get('projects', []):
        pid = project.get('id')
        if not pid:
            continue
        entry = entries.get(pid) or {}
        oss = entry.get('oss') or {}
        compare = entry.get('compare') or {}
        people = oss.get('people') or {}
        github, hf = people.get('github') or {}, people.get('huggingface') or {}
        releases, reuse = oss.get('releases') or {}, oss.get('reuse') or {}
        measured_assets = [a for a in oss.get('assets') or [] if a.get('status') == 'measured']
        github_assets = [a for a in measured_assets if a.get('platform') == 'github']
        platforms = sorted({a['platform'] for a in measured_assets})
        change_requests = oss.get('change_requests')
        last_change = oss.get('last_change') or {}
        flags = quality_flags(project, entry)
        row = {
            'id': pid,
            'title': ' '.join((project.get('title') or '').split()),
            'sdgs': ', '.join(project.get('sdgs') or []),
            'status': oss.get('status') or ('no measurable asset' if entry else 'no links checked'),
            'open_asset': bool(compare.get('open_asset')),
            'measured': bool(compare.get('measured')),
            'changed_12m': compare.get('changed_12m'),
            'several_contributors': compare.get('several_contributors'),
            'hosts': ', '.join(f'{host} {n}' for host, n in (entry.get('hosts') or {}).items()),
            'platforms': ', '.join(platforms),
            'measured_at': oss.get('measured_at'),
            'last_change': last_change.get('at'),
            'last_change_platform': last_change.get('platform'),
            'days_since_change': cm.days_between(last_change.get('at'), run) if run and last_change else None,
            'contributors_github': github.get('total'),
            'active_github': github.get('active'),
            'absence_factor_github': github.get('absence_factor'),
            'contributors_hf': hf.get('total'),
            'active_hf': hf.get('active'),
            'absence_factor_hf': hf.get('absence_factor'),
            'releases_12m': sum(r.get('in_window') or 0 for r in releases.values()) if releases else None,
            'releases_total': sum(r.get('total') or 0 for r in releases.values()) if releases else None,
            'forks': (reuse.get('github') or {}).get('forks'),
            'stars': (reuse.get('github') or {}).get('stars'),
            'hf_downloads_30d': (reuse.get('huggingface') or {}).get('downloads_30d'),
            'hf_downloads_all_time': (reuse.get('huggingface') or {}).get('downloads_all_time'),
            'hf_likes': (reuse.get('huggingface') or {}).get('likes'),
            'zenodo_downloads': (reuse.get('zenodo') or {}).get('downloads'),
            'zenodo_views': (reuse.get('zenodo') or {}).get('views'),
            'license_catalogue': (project.get('license') or '').strip(),
            'license_source': ', '.join(_source_licenses(oss)),
            'outside_items_12m': sum(a.get('outside_items') or 0 for a in github_assets) if github_assets else None,
            'first_response_median_hours': (oss.get('first_response') or {}).get('median_hours'),
            'change_requests': (f"{change_requests['closed']} of {change_requests['opened']} closed"
                                if change_requests else None),
            'readme': _files(github_assets, 'readme'),
            'contributing': _files(github_assets, 'contributing'),
            'code_of_conduct': _files(github_assets, 'code_of_conduct'),
            'gaps': '; '.join(f"{g['metric']} ({g['reason']})" for g in oss.get('gaps') or []),
            'flags': '; '.join(kind for kind, _ in flags),
            'sdg_list': list(project.get('sdgs') or []),
            'platform_set': set(platforms),
            'flag_details': flags,
        }
        for key, value in ((joined or {}).get(pid) or {}).items():
            if key not in row:
                row[key] = value
        rows.append(row)
    return rows


def _fraction(group, key):
    known = [r[key] for r in group if r[key] is not None]
    return f'{sum(1 for v in known if v)} of {len(known)}' if known else ''


def _bucket(value, edges, labels):
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def _median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else ''


def group_stats(group, **label):
    """Counts for one group of rows (an SDG, or a joined category)."""
    measured = [r for r in group if r['measured']]
    changes = Counter(_bucket(r['days_since_change'], (cm.RECENT_DAYS, cm.STALE_DAYS + 1),
                              ('under 12 months', '12 to 18 months', 'over 18 months'))
                      for r in measured if r['days_since_change'] is not None)
    contributors = Counter(_bucket(max(v for v in (r['contributors_github'], r['contributors_hf']) if v is not None),
                                   (2, 5), ('1', '2 to 4', '5 or more'))
                           for r in measured if r['contributors_github'] is not None or r['contributors_hf'] is not None)
    absence = Counter(_bucket(r['absence_factor_github'] if r['absence_factor_github'] is not None else r['absence_factor_hf'],
                              (2, 3), ('1', '2', '3 or more'))
                      for r in measured if r['absence_factor_github'] is not None or r['absence_factor_hf'] is not None)
    stats = dict(label)
    stats.update({
        'projects': len(group),
        'open_asset': sum(1 for r in group if r['open_asset']),
        'measured': len(measured),
        'github': sum(1 for r in measured if 'github' in r['platform_set']),
        'huggingface': sum(1 for r in measured if 'huggingface' in r['platform_set']),
        'zenodo': sum(1 for r in measured if 'zenodo' in r['platform_set']),
        'changed_12m': _fraction(group, 'changed_12m'),
        'several_contributors': _fraction(group, 'several_contributors'),
        'last_change_under_12_months': changes['under 12 months'],
        'last_change_12_to_18_months': changes['12 to 18 months'],
        'last_change_over_18_months': changes['over 18 months'],
        'contributors_1': contributors['1'],
        'contributors_2_to_4': contributors['2 to 4'],
        'contributors_5_or_more': contributors['5 or more'],
        'absence_factor_1': absence['1'],
        'absence_factor_2': absence['2'],
        'absence_factor_3_or_more': absence['3 or more'],
        'released_in_12_months': sum(1 for r in measured if r['releases_12m']),
        'license_detected_at_source': sum(1 for r in measured if r['license_source']),
        'with_outside_items': sum(1 for r in measured if r['outside_items_12m']),
        'median_hf_downloads_all_time': _median(r['hf_downloads_all_time'] for r in measured),
        'median_github_forks': _median(r['forks'] for r in measured),
    })
    return stats


def _sdg_number(sdg):
    match = re.search(r'\d+', sdg)
    return int(match.group()) if match else 99


def sdg_table(rows):
    """One row per SDG, ordered by number of projects. Projects count under every SDG they address."""
    counts = Counter(sdg for row in rows for sdg in row['sdg_list'])
    order = sorted(counts, key=lambda sdg: (-counts[sdg], _sdg_number(sdg)))
    return [group_stats([r for r in rows if sdg in r['sdg_list']], sdg=sdg) for sdg in order]


def starter_fill_rates(rows):
    """How many projects the four Starter Project Health metrics can be computed for."""
    measured = [r for r in rows if r['measured']]
    on_github = [r for r in measured if 'github' in r['platform_set']]
    return [
        {'metric': 'Time to First Response', 'eligible': len(on_github),
         'computable': sum(1 for r in on_github if r['first_response_median_hours'] is not None),
         'note': f'needs {cm.MIN_OUTSIDE_ITEMS} or more outside issues or pull requests in 12 months'},
        {'metric': 'Change Request Closure Ratio', 'eligible': len(on_github),
         'computable': sum(1 for r in on_github if r['change_requests']),
         'note': f'needs {cm.MIN_OUTSIDE_CHANGE_REQUESTS} or more outside pull requests in 12 months'},
        {'metric': 'Contributor Absence Factor', 'eligible': len(measured),
         'computable': sum(1 for r in measured if r['absence_factor_github'] is not None or r['absence_factor_hf'] is not None),
         'note': 'needs a readable commit history on GitHub or Hugging Face'},
        {'metric': 'Release Frequency', 'eligible': len(measured),
         'computable': sum(1 for r in measured if r['releases_total'] is not None),
         'note': 'GitHub releases or Zenodo versions; Hugging Face has no releases'},
    ]


def crosstabs(rows, columns):
    """{column: {value: counts}} for joined categorical columns."""
    tables = {}
    for column in columns:
        values = sorted({r.get(column) for r in rows if r.get(column)})
        table = {}
        for value in values:
            group = [r for r in rows if r.get(column) == value]
            table[value] = {
                'projects': len(group),
                'open_asset': sum(1 for r in group if r['open_asset']),
                'measured': sum(1 for r in group if r['measured']),
                'changed_12m': sum(1 for r in group if r['changed_12m']),
                'several_contributors': sum(1 for r in group if r['several_contributors']),
                'with_outside_items': sum(1 for r in group if r['outside_items_12m']),
            }
        tables[column] = table
    return tables


def load_join(path, key=JOIN_KEY):
    """({project id: {column: value}}, [categorical columns]) from a CSV keyed by `key`."""
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if key not in (reader.fieldnames or []):
            raise ValueError(f'{path} has no "{key}" column')
        rows = {}
        for row in reader:
            pid = (row.get(key) or '').strip()
            if pid:
                rows[pid] = {k.strip(): ' '.join((v or '').split()) for k, v in row.items() if k and k != key}
        columns = [c.strip() for c in reader.fieldnames if c and c != key]
    categorical = []
    for column in columns:
        values = [r[column] for r in rows.values() if r.get(column)]
        distinct = set(values)
        if values and len(distinct) <= MAX_CATEGORIES and len(distinct) < len(values):
            categorical.append(column)
    return rows, categorical


def _public_row(row):
    return {k: (', '.join(sorted(v)) if isinstance(v, set) else v) for k, v in row.items() if k not in _INTERNAL}


def _write_csv(path, rows):
    fields = []
    for row in rows:
        fields += [key for key in row if key not in fields]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _cell(value):
    if value is None or value == '':
        return '<td class="empty"></td>'
    if isinstance(value, bool):
        return f'<td>{"yes" if value else "no"}</td>'
    if isinstance(value, int):
        return f'<td class="num">{value:,}</td>'
    if isinstance(value, float):
        return f'<td class="num">{value:,.1f}</td>'
    return f'<td>{html.escape(str(value))}</td>'


def _table(headers, rows):
    head = ''.join(f'<th>{html.escape(h)}</th>' for h, _ in headers)
    body = ''.join('<tr>' + ''.join(_cell(row.get(key)) for _, key in headers) + '</tr>' for row in rows)
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


_STYLE = """
:root { --ink: #10173e; --ink-3: #5c6278; --hair: #e0e3eb; --paper-2: #f4f6fa; }
body { margin: 0; padding: 2rem 1rem 4rem; font: 15px/1.5 system-ui, -apple-system, 'Segoe UI', sans-serif;
       color: var(--ink); background: #fff; }
main { max-width: 1200px; margin: 0 auto; }
h1 { font-size: 1.75rem; margin: .25rem 0 .5rem; } h2 { font-size: 1.2rem; margin: 2.5rem 0 .5rem; }
.label { color: var(--ink-3); font-weight: 600; margin: 0; } .note { color: var(--ink-3); max-width: 70ch; }
ul.glance { padding-left: 1.1rem; } ul.glance li { margin: .2rem 0; }
.scroll { overflow-x: auto; border-top: 1px solid var(--hair); }
table { border-collapse: collapse; font-size: 13px; min-width: 100%; }
th, td { text-align: left; padding: .35rem .6rem; border-bottom: 1px solid var(--hair); vertical-align: top; }
th { background: var(--paper-2); font-weight: 600; white-space: nowrap; }
td.num { text-align: right; font-variant-numeric: tabular-nums; } td.empty { background: #fcfcfd; }
a { color: var(--ink); }
"""


def _glance(rows):
    measured = [r for r in rows if r['measured']]
    on_github = [r for r in measured if 'github' in r['platform_set']]
    with_history = [r for r in measured if r['absence_factor_github'] is not None or r['absence_factor_hf'] is not None]
    single = sum(1 for r in with_history
                 if (r['absence_factor_github'] if r['absence_factor_github'] is not None else r['absence_factor_hf']) == 1)
    outside = sum(r['outside_items_12m'] or 0 for r in on_github)
    hf_all = sum(r['hf_downloads_all_time'] or 0 for r in measured)
    hf_30 = sum(r['hf_downloads_30d'] or 0 for r in measured)
    zen = sum(r['zenodo_downloads'] or 0 for r in measured)
    items = [
        f"{len(rows)} projects in the catalogue; {sum(1 for r in rows if r['open_asset'])} link an open repository, model or record; "
        f"{len(measured)} have open-source health facts (GitHub {sum(1 for r in measured if 'github' in r['platform_set'])}, "
        f"Hugging Face {sum(1 for r in measured if 'huggingface' in r['platform_set'])}, "
        f"Zenodo {sum(1 for r in measured if 'zenodo' in r['platform_set'])}).",
        f"Changed in the last 12 months: {_fraction(rows, 'changed_12m') or 'none measured'} (archive records left out).",
        f"More than one contributor: {_fraction(rows, 'several_contributors') or 'none measured'}.",
        f"Half of all commits came from one person (absence factor 1): {single} of {len(with_history)} projects with a commit history.",
        f"Outside issues and pull requests in the last 12 months: {outside} across {len(on_github)} projects on GitHub.",
        f"Hugging Face downloads: {hf_all:,} all time, {hf_30:,} in the last 30 days (as counted by Hugging Face). "
        f"Zenodo downloads, all versions: {zen:,}.",
    ]
    return '<ul class="glance">' + ''.join(f'<li>{html.escape(item)}</li>' for item in items) + '</ul>'


def render_html(rows, sdg, fill, tabs, flags, health, joined_columns=()):
    measured_at = (health or {}).get('generated_at') or 'unknown'
    method = (health or {}).get('method') or {}
    sdg_headers = [('SDG', 'sdg'), ('Projects', 'projects'), ('Open asset', 'open_asset'), ('Measured', 'measured'),
                   ('GitHub', 'github'), ('Hugging Face', 'huggingface'), ('Zenodo', 'zenodo'),
                   ('Changed in 12 months', 'changed_12m'), ('More than one contributor', 'several_contributors'),
                   ('Absence factor 1', 'absence_factor_1'), ('Absence factor 2', 'absence_factor_2'),
                   ('Absence factor 3+', 'absence_factor_3_or_more'),
                   ('Released in 12 months', 'released_in_12_months'), ('License at source', 'license_detected_at_source'),
                   ('With outside items', 'with_outside_items'), ('Median HF downloads', 'median_hf_downloads_all_time')]
    project_headers = [('ID', 'id'), ('Title', 'title'), ('SDGs', 'sdgs'), ('Status', 'status'), ('Platforms', 'platforms'),
                       ('Last change', 'last_change'), ('Contributors (GH)', 'contributors_github'),
                       ('Active (GH)', 'active_github'), ('Absence factor (GH)', 'absence_factor_github'),
                       ('Contributors (HF)', 'contributors_hf'), ('Absence factor (HF)', 'absence_factor_hf'),
                       ('Releases 12m', 'releases_12m'), ('Forks', 'forks'), ('Stars', 'stars'),
                       ('HF downloads all time', 'hf_downloads_all_time'), ('Zenodo downloads', 'zenodo_downloads'),
                       ('Outside items 12m', 'outside_items_12m'), ('License (catalogue)', 'license_catalogue'),
                       ('License (source)', 'license_source'), ('Contributing guide', 'contributing'),
                       ('Flags', 'flags')]
    project_headers += [(c, c) for c in joined_columns]
    sections = [
        f'<p class="label">Private. Not for publication or sharing outside the team.</p>',
        f'<h1>Open-source health of the catalogue\'s projects</h1>',
        f'<p class="note">Measured {html.escape(measured_at)} from public GitHub, Hugging Face and Zenodo data, '
        f'following <a href="{cm.CHAOSS_HOME}">CHAOSS</a> metric definitions over a {method.get("window_days", cm.WINDOW_DAYS)}-day window. '
        f'CHAOSS advises against comparing projects with each other; the public catalogue therefore shows each '
        f'project\'s own facts and compares SDGs without names. Read this comparison with each project\'s goals in mind: '
        f'a finished dataset that no longer changes can be complete.</p>',
        '<h2>At a glance</h2>', _glance(rows),
        '<h2>Coverage and upkeep by SDG</h2>',
        '<p class="note">Projects can address several goals and count under each. "n of m" counts only projects '
        'where the fact applies (archive records are left out of "changed").</p>',
        _table(sdg_headers, sdg),
        f'<h2>CHAOSS <a href="{cm.STARTER_MODEL_URL}">Starter Project Health</a>: what can be computed</h2>',
        _table([('Metric', 'metric'), ('Computable', 'computable'), ('Eligible projects', 'eligible'), ('Needs', 'note')], fill),
    ]
    for column, table in tabs.items():
        sections += [f'<h2>Joined: {html.escape(column)}</h2>',
                     _table([(column, 'value'), ('Projects', 'projects'), ('Open asset', 'open_asset'),
                             ('Measured', 'measured'), ('Changed in 12 months', 'changed_12m'),
                             ('More than one contributor', 'several_contributors'),
                             ('With outside items', 'with_outside_items')],
                            [dict(counts, value=value) for value, counts in table.items()])]
    sections += ['<h2>Data-quality flags</h2>',
                 '<p class="note">Link and record issues to fix in the Sheet. Licence differences need a judgement: '
                 'a code licence and a data licence can both be right.</p>',
                 _table([('ID', 'id'), ('Title', 'title'), ('Flag', 'flag'), ('Detail', 'detail')],
                        [{'id': a, 'title': b, 'flag': c, 'detail': d} for a, b, c, d in flags]),
                 '<h2>Projects</h2>', _table(project_headers, rows)]
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex, nofollow">'
            '<title>Open-source health: private comparison</title>'
            f'<style>{_STYLE}</style></head><body><main>' + '\n'.join(sections) + '</main></body></html>\n')


def write_report(out, catalog, health, joined, categorical):
    """Write index.html and the CSV files into `out` (outside the repository). Returns the path."""
    out = ensure_outside_repo(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = project_rows(catalog, health, joined)
    sdg = sdg_table(rows)
    fill = starter_fill_rates(rows)
    tabs = crosstabs(rows, categorical)
    flags = [(r['id'], r['title'], kind, detail) for r in rows for kind, detail in r['flag_details']]
    _write_csv(out / 'projects.csv', [_public_row(r) for r in rows])
    _write_csv(out / 'by_sdg.csv', sdg)
    _write_csv(out / 'flags.csv', [{'id': a, 'title': b, 'flag': c, 'detail': d} for a, b, c, d in flags])
    joined_columns = list(dict.fromkeys(key for values in (joined or {}).values() for key in values))
    (out / 'index.html').write_text(render_html(rows, sdg, fill, tabs, flags, health, joined_columns), encoding='utf-8')
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description='Write the private open-source health comparison (never published).')
    parser.add_argument('--out', required=True, help='Directory to write to; must lie outside this repository')
    parser.add_argument('--health', default='public/data/health.json', help='health.json (schema_version 2)')
    parser.add_argument('--catalog', default='public/data/catalog.json', help='catalog.json')
    parser.add_argument('--join', default='', help=f'Optional CSV keyed by "{JOIN_KEY}" to join and cross-tabulate')
    args = parser.parse_args(argv)
    try:
        ensure_outside_repo(args.out)
    except ValueError as err:
        parser.error(str(err))
    with open(args.health, encoding='utf-8') as f:
        health = json.load(f)
    if health.get('schema_version') != 2:
        parser.error(f'{args.health} is not a schema_version 2 health.json; run health_check.py first')
    with open(args.catalog, encoding='utf-8') as f:
        catalog = json.load(f)
    joined, categorical = load_join(args.join) if args.join else ({}, [])
    if args.join:
        try:
            ensure_outside_repo(args.join)
        except ValueError:
            print('Warning: the joined file lies inside the repository; keep private data out of git.')
    out = write_report(args.out, catalog, health, joined, categorical)
    print(f'Wrote {out / "index.html"}, projects.csv, by_sdg.csv and flags.csv')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Compare the current live catalog.json (docs/) against the newly generated one (public/)
to detect suspicious changes before deployment.

Exit codes:
  0 - changes look normal
  1 - suspicious changes detected (e.g. >5% projects removed)

Outputs a markdown change summary to stdout.
"""

import json
import os
import sys

# Threshold: flag if more than this fraction of projects are removed
REMOVAL_THRESHOLD = 0.05  # 5%

OLD_PATH = os.path.join('docs', 'data', 'catalog.json')
NEW_PATH = os.path.join('public', 'data', 'catalog.json')


def load_catalog(path):
    """Load catalog.json and return a dict keyed by project id."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {p['id']: p for p in data.get('projects', [])}


def summarize_link_changes(old_project, new_project):
    """Return a short description of link changes, or None."""
    old_ds = set(link['url'] for link in old_project.get('dataset_links', []))
    new_ds = set(link['url'] for link in new_project.get('dataset_links', []))
    old_uc = set(link['url'] for link in old_project.get('usecase_links', []))
    new_uc = set(link['url'] for link in new_project.get('usecase_links', []))

    changes = []
    added_ds = new_ds - old_ds
    removed_ds = old_ds - new_ds
    added_uc = new_uc - old_uc
    removed_uc = old_uc - new_uc

    if added_ds:
        changes.append(f"{len(added_ds)} dataset link(s) added")
    if removed_ds:
        changes.append(f"{len(removed_ds)} dataset link(s) removed")
    if added_uc:
        changes.append(f"{len(added_uc)} use-case link(s) added")
    if removed_uc:
        changes.append(f"{len(removed_uc)} use-case link(s) removed")

    return ', '.join(changes) if changes else None


def diff_catalogs(old_catalog, new_catalog):
    """Compare two catalogs and return a structured diff."""
    old_ids = set(old_catalog.keys())
    new_ids = set(new_catalog.keys())

    added_ids = new_ids - old_ids
    removed_ids = old_ids - new_ids
    common_ids = old_ids & new_ids

    # Detect changes in common projects
    title_changes = []
    link_changes = []
    for pid in sorted(common_ids):
        old_p = old_catalog[pid]
        new_p = new_catalog[pid]

        if old_p.get('title') != new_p.get('title'):
            title_changes.append((pid, old_p.get('title', ''), new_p.get('title', '')))

        link_summary = summarize_link_changes(old_p, new_p)
        if link_summary:
            link_changes.append((new_p.get('title', pid), link_summary))

    return {
        'old_count': len(old_catalog),
        'new_count': len(new_catalog),
        'added': [(pid, new_catalog[pid].get('title', pid)) for pid in sorted(added_ids)],
        'removed': [(pid, old_catalog[pid].get('title', pid)) for pid in sorted(removed_ids)],
        'title_changes': title_changes,
        'link_changes': link_changes,
    }


def format_summary(diff):
    """Format the diff as a markdown summary."""
    old_n = diff['old_count']
    new_n = diff['new_count']
    delta = new_n - old_n

    lines = ['## Sheet Update Summary', '']

    if old_n == 0:
        lines.append(f'**Projects**: {new_n} (first build, no previous data)')
    else:
        pct = (delta / old_n * 100) if old_n else 0
        sign = '+' if delta >= 0 else ''
        lines.append(f'**Projects**: {old_n} -> {new_n} ({sign}{delta}, {sign}{pct:.1f}%)')

    lines.append('')

    if diff['added']:
        lines.append(f'### Added ({len(diff["added"])})')
        for _pid, title in diff['added']:
            lines.append(f'- {title}')
        lines.append('')

    if diff['removed']:
        lines.append(f'### Removed ({len(diff["removed"])})')
        for _pid, title in diff['removed']:
            lines.append(f'- {title}')
        lines.append('')

    if diff['title_changes']:
        lines.append(f'### Title changes ({len(diff["title_changes"])})')
        for _pid, old_title, new_title in diff['title_changes']:
            lines.append(f'- "{old_title}" -> "{new_title}"')
        lines.append('')

    if diff['link_changes']:
        lines.append(f'### Link changes ({len(diff["link_changes"])})')
        for title, summary in diff['link_changes']:
            lines.append(f'- "{title}": {summary}')
        lines.append('')

    if not diff['added'] and not diff['removed'] and not diff['title_changes'] and not diff['link_changes']:
        lines.append('No project-level changes detected.')
        lines.append('')

    return '\n'.join(lines)


def check_suspicious(diff):
    """Return True if changes exceed safety thresholds."""
    old_n = diff['old_count']
    if old_n == 0:
        return False  # First build, nothing to compare

    removed_count = len(diff['removed'])
    removal_fraction = removed_count / old_n

    if removal_fraction > REMOVAL_THRESHOLD:
        return True

    return False


def main():
    old_catalog = load_catalog(OLD_PATH)
    new_catalog = load_catalog(NEW_PATH)

    diff = diff_catalogs(old_catalog, new_catalog)
    summary = format_summary(diff)
    suspicious = check_suspicious(diff)

    print(summary)

    if suspicious:
        removed_pct = len(diff['removed']) / diff['old_count'] * 100
        print(f'**FLAGGED**: {len(diff["removed"])} projects removed '
              f'({removed_pct:.1f}% of {diff["old_count"]}), '
              f'exceeds {REMOVAL_THRESHOLD*100:.0f}% threshold.')
        print('This PR requires manual review before merging.')
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()

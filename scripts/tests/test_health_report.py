"""Tests for health_report: the private comparison report (never published)."""
import csv
import os
import tempfile
import unittest
from pathlib import Path

import health_report as hr

REPO = Path(__file__).resolve().parents[2]


def entry(measured=True, changed=True, several=True, assets=(), people=None, releases=None, reuse=None,
          license_=None, gaps=(), hosts=None, first_response=None, change_requests=None):
    oss = None
    if measured:
        oss = {'status': 'measured', 'measured_at': '2026-10-05', 'window': {'start': '2025-10-06', 'end': '2026-10-05'},
               'scope': {}, 'last_change': {'at': '2026-08-02', 'platform': 'github', 'archived': False},
               'people': people if people is not None else {'github': {'total': 5, 'active': 2, 'absence_factor': 2, 'assets': 1, 'fork_history': False}},
               'releases': releases if releases is not None else {'github': {'in_window': 0, 'total': 0, 'latest_at': None}},
               'reuse': reuse if reuse is not None else {'github': {'forks': 1, 'stars': 1}},
               'license': license_ if license_ is not None else {'github': [{'status': 'detected', 'spdx': 'MIT', 'raw': 'MIT', 'assets': 1}]},
               'first_response': first_response, 'change_requests': change_requests,
               'gaps': list(gaps) or [{'metric': 'first_response', 'reason': 'too_few_items', 'count': 0}],
               'assets': list(assets) or [{'key': 'github:o/r', 'platform': 'github', 'id': 'o/r', 'status': 'measured',
                                            'outside_items': 0, 'files': {'readme': True, 'contributing': False, 'code_of_conduct': False}}]}
    return {'availability': 'available', 'checked_at': '2026-10-05', 'context': None, 'activity_score': None,
            'link_count': 1, 'broken_links': [], 'hosts': hosts or ({'github': 1} if measured else {'website': 1}),
            'compare': {'open_asset': measured or 'kaggle' in (hosts or {}), 'measured': measured,
                        'changed_12m': changed if measured else None, 'several_contributors': several if measured else None},
            'oss': oss}


def project(pid, title, sdgs, license_='', contact='', dataset=(), additional=()):
    return {'id': pid, 'title': title, 'sdgs': list(sdgs), 'license': license_, 'contact': contact,
            'dataset_links': [{'name': '', 'url': u} for u in dataset], 'usecase_links': [],
            'additional_resources': [{'name': '', 'url': u} for u in additional]}


class SafetyTests(unittest.TestCase):
    def test_refuses_to_write_inside_the_repository(self):
        with self.assertRaises(ValueError):
            hr.ensure_outside_repo(REPO / 'reports')
        with self.assertRaises(ValueError):
            hr.ensure_outside_repo(REPO)

    @unittest.skipUnless(Path(str(REPO).swapcase()).exists(), 'needs a case-insensitive file system')
    def test_refuses_the_repository_under_another_letter_case(self):
        with self.assertRaises(ValueError):
            hr.ensure_outside_repo(Path(str(REPO).swapcase()) / 'reports')

    def test_accepts_a_directory_elsewhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(hr.ensure_outside_repo(Path(tmp) / 'out'), (Path(tmp) / 'out').resolve())


class FlagTests(unittest.TestCase):
    def test_names_the_link_problems_a_maintainer_can_fix(self):
        assets = [
            {'key': 'github:a/old', 'platform': 'github', 'id': 'a/new', 'status': 'measured', 'renamed_from': 'a/old',
             'fork': True, 'fork_of': 'up/new', 'archived': True},
            {'key': 'github:a/private', 'platform': 'github', 'id': 'a/private', 'status': 'unavailable'},
            {'key': 'zenodo:1', 'platform': 'zenodo', 'id': '1', 'status': 'measured', 'linked_is_latest': False, 'latest_id': '2'},
            {'key': 'huggingface:datasets/h/d', 'platform': 'huggingface', 'id': 'h/d', 'status': 'measured', 'gated': 'auto',
             'resolved_from': '10.57967/hf/1'},
        ]
        e = entry(assets=assets, hosts={'github': 2, 'github_org': 1, 'zenodo': 1, 'huggingface': 1},
                  license_={'github': [{'status': 'detected', 'spdx': 'MIT', 'raw': 'MIT', 'assets': 1}]})
        p = project('ui_1', 'One', ['SDG 2'], license_='CC-BY 4.0',
                    dataset=['https://github.com/a/old', 'https://github.com/a/old'],
                    additional=['https://huggingface.co/datasets/x/y'])
        kinds = [kind for kind, _ in hr.quality_flags(p, e)]
        for expected in ('renamed', 'fork_linked', 'archived', 'unreadable', 'superseded_version', 'gated',
                         'doi_resolved', 'org_page', 'license_differs', 'duplicate_link', 'additional_only'):
            self.assertIn(expected, kinds)

    def test_a_licence_missing_from_the_catalogue_is_flagged(self):
        e = entry(license_={'zenodo': [{'status': 'detected', 'spdx': 'CC-BY-4.0', 'raw': 'cc-by-4.0', 'assets': 1}]})
        flags = dict(hr.quality_flags(project('ui_2', 'Two', ['SDG 2']), e))
        self.assertIn('CC-BY-4.0', flags['license_missing'])

    def test_a_matching_licence_is_not_flagged(self):
        e = entry(license_={'github': [{'status': 'detected', 'spdx': 'CC-BY-4.0', 'raw': 'CC-BY-4.0', 'assets': 1}]})
        kinds = [k for k, _ in hr.quality_flags(project('ui_3', 'Three', ['SDG 2'], license_='CC-BY 4.0'), e)]
        self.assertNotIn('license_differs', kinds)
        self.assertNotIn('license_missing', kinds)


class TableTests(unittest.TestCase):
    def rows(self):
        catalog = {'projects': [
            project('ui_1', 'One', ['SDG 2', 'SDG 13']),
            project('ui_2', 'Two', ['SDG 2']),
            project('ui_3', 'Three', ['SDG 13']),
            project('ui_4', 'Four', ['SDG 11'])]}
        health = {'generated_at': '2026-10-05', 'entries': {
            'ui_1': entry(changed=True, several=True),
            'ui_2': entry(changed=False, several=False,
                          people={'github': {'total': 1, 'active': 0, 'absence_factor': 1, 'assets': 1, 'fork_history': False}}),
            'ui_3': entry(measured=False, hosts={'kaggle': 1}),
            'ui_4': entry(measured=False)}}
        joined = {'ui_1': {'Potential Community': 'Yes'}, 'ui_2': {'Potential Community': 'No'},
                  'ui_3': {'Potential Community': 'Yes'}}
        return hr.project_rows(catalog, health, joined)

    def test_counts_each_sdg_a_project_addresses(self):
        table = {row['sdg']: row for row in hr.sdg_table(self.rows())}
        self.assertEqual((table['SDG 2']['projects'], table['SDG 2']['measured'], table['SDG 2']['changed_12m']), (2, 2, '1 of 2'))
        self.assertEqual((table['SDG 13']['projects'], table['SDG 13']['open_asset'], table['SDG 13']['measured']), (2, 2, 1))
        self.assertEqual(table['SDG 11']['open_asset'], 0)
        self.assertEqual([row['sdg'] for row in hr.sdg_table(self.rows())][:2], ['SDG 2', 'SDG 13'])

    def test_starter_model_fill_rates(self):
        rates = {row['metric']: row for row in hr.starter_fill_rates(self.rows())}
        self.assertEqual((rates['Time to First Response']['computable'], rates['Time to First Response']['eligible']), (0, 2))
        self.assertEqual((rates['Contributor Absence Factor']['computable'], rates['Contributor Absence Factor']['eligible']), (2, 2))

    def test_crosstab_of_a_joined_category(self):
        tables = hr.crosstabs(self.rows(), ['Potential Community'])
        yes = tables['Potential Community']['Yes']
        self.assertEqual((yes['projects'], yes['measured'], yes['changed_12m'], yes['several_contributors']), (2, 1, 1, 1))

    def test_rows_carry_joined_columns_and_no_contact_data(self):
        catalog = {'projects': [project('ui_1', 'One', ['SDG 2'], contact='Jane <jane@example.org>')]}
        rows = hr.project_rows(catalog, {'generated_at': '2026-10-05', 'entries': {'ui_1': entry()}},
                               {'ui_1': {'Potential Community': 'Yes'}})
        self.assertEqual(rows[0]['Potential Community'], 'Yes')
        self.assertNotIn('jane@example.org', repr(rows))


class JoinTests(unittest.TestCase):
    def test_reads_rows_by_project_id_and_finds_categorical_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'join.csv'
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Project ID', 'Title', 'Potential Community', 'Reason'])
                for n, value in enumerate(['Yes', 'No', 'Check', 'Yes', 'No', 'Yes', 'Check']):
                    writer.writerow([f'ui_{n}', f'Title {n}', value, f'Because {n}'])
            rows, categorical = hr.load_join(path)
        self.assertEqual(rows['ui_2']['Potential Community'], 'Check')
        self.assertEqual(categorical, ['Potential Community'])


class WriteTests(unittest.TestCase):
    def test_writes_a_self_contained_noindex_report(self):
        catalog = {'projects': [project('ui_1', 'Tom & <Jerry>', ['SDG 2'])]}
        health = {'generated_at': '2026-10-05', 'entries': {'ui_1': entry()}}
        with tempfile.TemporaryDirectory() as tmp:
            out = hr.write_report(Path(tmp) / 'report', catalog, health, {}, [])
            html = (out / 'index.html').read_text(encoding='utf-8')
            self.assertIn('noindex', html)
            self.assertIn('Tom &amp; &lt;Jerry&gt;', html)
            self.assertNotIn('—', html)
            for name in ('projects.csv', 'by_sdg.csv', 'flags.csv'):
                self.assertTrue((out / name).exists(), name)


if __name__ == '__main__':
    unittest.main()

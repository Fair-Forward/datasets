"""Tests for health_check: per-project open-source health blocks, carry-forward and validation.

Observations are built by hand in the shape the fetchers return, so no test touches the network.
Logins and emails are invented and must never reach the output.
"""
import json
import unittest
from pathlib import Path
from unittest import mock

import chaoss_metrics as cm
import health_check as hc
from health_sources import SourceError

RUN = '2026-10-05'
UI80_ALL_TIME = {'u:a': 198, 'u:b': 187, 'u:c': 30, 'u:d': 12, 'e:x@example.org': 7}


def gh_obs(repo_id, last='2026-08-02', all_time=None, active=None, archived=False, fork_of=None, fork=False, forks=1,
           stars=1, lic=None, rel_in=0, rel_total=0, latest_rel=None, response_items=(), outside_prs=()):
    all_time = dict(UI80_ALL_TIME) if all_time is None else all_time
    active = {'u:a': 5, 'u:b': 2} if active is None else active
    people = cm.merge_people(all_time, active)
    record = {'platform': 'github', 'id': repo_id, 'renamed_from': None, 'fork': bool(fork_of) or fork,
              'fork_of': fork_of, 'archived': archived,
              'forks': forks, 'stars': stars, 'license': cm.normalise_licenses(lic, 'github'),
              'last_change_at': last, 'gaps': [], 'contributors_total': people['total'],
              'contributors_active': people['active'], 'absence_factor': people['absence_factor'],
              'releases_in_window': rel_in, 'releases_total': rel_total, 'latest_release_at': latest_rel,
              'outside_items': len(response_items), 'outside_change_requests': len(outside_prs),
              'files': {'readme': True, 'contributing': False, 'code_of_conduct': False}}
    return {'record': record, 'people': {'all_time': all_time, 'active': active},
            'response_items': list(response_items), 'outside_prs': list(outside_prs)}


def hf_obs(repo_id, kind='datasets', last='2026-07-30', gated=False, d30=64, dall=2155, likes=3, lic='cc-by-4.0'):
    record = {'platform': 'huggingface', 'kind': kind, 'id': repo_id, 'renamed_from': None, 'gated': gated,
              'last_change_at': last, 'created_at': '2023-05-17', 'likes': likes, 'downloads_30d': d30,
              'downloads_all_time': dall, 'license': cm.normalise_licenses(lic, 'huggingface'),
              'contributors_total': None, 'contributors_active': None, 'absence_factor': None,
              'discussions': None, 'gaps': []}
    people = None
    if gated:
        record['gaps'] = [{'metric': 'contributors', 'reason': 'gated'}]
    else:
        people = {'all_time': {'u:a': 3, 'u:b': 1}, 'active': {'u:a': 1}}
        record.update({'contributors_total': 2, 'contributors_active': 1, 'absence_factor': 1})
    return {'record': record, 'people': people, 'response_items': [], 'outside_prs': []}


def zen_obs(record_id, concept='100', versions=2, in_window=1, last='2026-07-29', downloads=387, views=2358):
    record = {'platform': 'zenodo', 'id': record_id, 'concept_id': concept, 'linked_is_latest': True,
              'latest_id': record_id, 'versions_total': versions, 'versions_in_window': in_window,
              'last_change_at': last, 'downloads_all_time': downloads, 'views_all_time': views,
              'license': cm.normalise_licenses('cc-by-4.0', 'zenodo'), 'resource_type': 'dataset',
              'access_right': 'open', 'gaps': []}
    return {'record': record, 'people': None, 'response_items': [], 'outside_prs': []}


def asset(key, platform, id_, kind=None):
    return {'key': key, 'platform': platform, 'id': id_, 'kind': kind, 'url': f'https://example.org/{id_}', 'doi': None}


SOLAR = asset('github:marconi-lab/solar_irradiation', 'github', 'Marconi-Lab/Solar_irradiation')
PORTAL = asset('github:marconi-lab/irradiation_portal', 'github', 'Marconi-Lab/Irradiation_Portal')


def ui80_observations():
    return {SOLAR['key']: gh_obs('Marconi-Lab/SolarIrradiation'), PORTAL['key']: SourceError('unavailable', 404)}


class SummariseTests(unittest.TestCase):
    def test_the_approved_mockup_project(self):
        oss = hc.summarise_entry([SOLAR, PORTAL], ui80_observations(), RUN)
        self.assertEqual(oss['status'], 'measured')
        self.assertEqual(oss['measured_at'], RUN)
        self.assertEqual(oss['window'], {'start': '2025-10-06', 'end': '2026-10-05'})
        self.assertEqual(oss['scope'], {'github': 1, 'huggingface': 0, 'zenodo': 0, 'unreadable': 1, 'failed': 0})
        self.assertEqual(oss['last_change'], {'at': '2026-08-02', 'platform': 'github', 'archived': False})
        self.assertEqual(oss['people'], {'github': {'total': 5, 'active': 2, 'absence_factor': 2, 'assets': 1,
                                                    'fork_history': False}})
        self.assertEqual(oss['releases'], {'github': {'in_window': 0, 'total': 0, 'latest_at': None}})
        self.assertEqual(oss['reuse'], {'github': {'forks': 1, 'stars': 1}})
        self.assertEqual(oss['license'], {'github': [{'status': 'none', 'spdx': None, 'raw': None, 'assets': 1}]})
        self.assertIsNone(oss['first_response'])
        self.assertIsNone(oss['change_requests'])
        self.assertIn({'metric': 'first_response', 'reason': 'too_few_items', 'count': 0}, oss['gaps'])
        self.assertIn({'metric': 'change_request_closure', 'reason': 'too_few_items', 'count': 0}, oss['gaps'])
        self.assertEqual([a['status'] for a in oss['assets']], ['measured', 'unavailable'])

    def test_the_block_holds_no_identities(self):
        text = json.dumps(hc.summarise_entry([SOLAR, PORTAL], ui80_observations(), RUN))
        self.assertNotIn('@', text.replace('https://', ''))
        self.assertNotIn('u:a', text)

    def test_counts_a_person_once_across_repositories(self):
        one = asset('github:o/one', 'github', 'o/one')
        two = asset('github:o/two', 'github', 'o/two')
        observations = {one['key']: gh_obs('o/one', all_time={'u:a': 10, 'u:b': 1}, active={'u:a': 1}),
                        two['key']: gh_obs('o/two', all_time={'u:a': 5, 'u:c': 20}, active={'u:c': 2})}
        people = hc.summarise_entry([one, two], observations, RUN)['people']['github']
        self.assertEqual((people['total'], people['active'], people['absence_factor'], people['assets']), (3, 2, 1, 2))

    def test_the_last_change_counts_archived_repositories_too(self):
        live = asset('github:o/live', 'github', 'o/live')
        old = asset('github:o/old', 'github', 'o/old')
        observations = {live['key']: gh_obs('o/live', last='2023-04-06'),
                        old['key']: gh_obs('o/old', last='2024-05-24', archived=True)}
        self.assertEqual(hc.summarise_entry([live, old], observations, RUN)['last_change'],
                         {'at': '2024-05-24', 'platform': 'github', 'archived': False})
        only_old = hc.summarise_entry([old], {old['key']: observations[old['key']]}, RUN)
        self.assertEqual(only_old['last_change'], {'at': '2024-05-24', 'platform': 'github', 'archived': True})

    def test_a_fork_marks_its_history_even_when_the_original_is_unnamed(self):
        one = asset('github:o/fork', 'github', 'o/fork')
        oss = hc.summarise_entry([one], {one['key']: gh_obs('o/fork', fork=True)}, RUN)
        self.assertTrue(oss['people']['github']['fork_history'])

    def test_pools_reply_times_across_repositories_before_the_minimum(self):
        one = asset('github:o/one', 'github', 'o/one')
        two = asset('github:o/two', 'github', 'o/two')
        created = cm.parse_ts('2026-09-01T00:00:00Z')
        replied = cm.parse_ts('2026-09-01T02:00:00Z')
        items = [{'created_at': created, 'first_reply_at': replied}] * 3
        observations = {one['key']: gh_obs('o/one', response_items=items), two['key']: gh_obs('o/two', response_items=items)}
        oss = hc.summarise_entry([one, two], observations, RUN)
        self.assertEqual(oss['first_response'], {'items': 6, 'answered': 6, 'median_hours': 2.0,
                                                 'median_is_lower_bound': False})

    def test_hugging_face_only_names_the_gaps_its_platform_cannot_fill(self):
        ds = asset('huggingface:datasets/o/ds', 'huggingface', 'o/ds', 'datasets')
        oss = hc.summarise_entry([ds], {ds['key']: hf_obs('o/ds')}, RUN)
        self.assertEqual(oss['reuse'], {'huggingface': {'downloads_30d': 64, 'downloads_all_time': 2155, 'likes': 3}})
        for gap in ({'metric': 'releases', 'reason': 'no_releases_on_platform'},
                    {'metric': 'first_response', 'reason': 'github_only'},
                    {'metric': 'change_request_closure', 'reason': 'github_only'}):
            self.assertIn(gap, oss['gaps'])
        self.assertEqual(oss['people']['huggingface']['total'], 2)

    def test_a_gated_dataset_names_the_people_gap(self):
        ds = asset('huggingface:datasets/o/ds', 'huggingface', 'o/ds', 'datasets')
        oss = hc.summarise_entry([ds], {ds['key']: hf_obs('o/ds', gated='auto')}, RUN)
        self.assertEqual(oss['people'], {})
        self.assertIn({'metric': 'contributors', 'reason': 'gated'}, oss['gaps'])
        self.assertIn({'metric': 'absence_factor', 'reason': 'gated'}, oss['gaps'])

    def test_a_zenodo_record_has_versions_and_reuse_but_no_people(self):
        rec = asset('zenodo:111', 'zenodo', '111')
        oss = hc.summarise_entry([rec], {rec['key']: zen_obs('111')}, RUN)
        self.assertEqual(oss['releases'], {'zenodo': {'in_window': 1, 'total': 2, 'latest_at': '2026-07-29'}})
        self.assertEqual(oss['reuse'], {'zenodo': {'downloads': 387, 'views': 2358}})
        self.assertIn({'metric': 'contributors', 'reason': 'archive_record'}, oss['gaps'])

    def test_two_versions_of_one_zenodo_concept_count_once(self):
        old, new = asset('zenodo:111', 'zenodo', '111'), asset('zenodo:222', 'zenodo', '222')
        observations = {old['key']: zen_obs('111'), new['key']: zen_obs('222')}
        oss = hc.summarise_entry([old, new], observations, RUN)
        self.assertEqual(oss['reuse']['zenodo'], {'downloads': 387, 'views': 2358})
        self.assertEqual(oss['releases']['zenodo']['total'], 2)

    def test_a_transient_failure_makes_the_block_partial(self):
        observations = {SOLAR['key']: gh_obs('Marconi-Lab/SolarIrradiation'), PORTAL['key']: SourceError('failed', 502)}
        oss = hc.summarise_entry([SOLAR, PORTAL], observations, RUN)
        self.assertEqual((oss['status'], oss['scope']['failed']), ('partial', 1))

    def test_nothing_readable_is_unreadable(self):
        oss = hc.summarise_entry([PORTAL], {PORTAL['key']: SourceError('unavailable', 404)}, RUN)
        self.assertEqual(oss['status'], 'unreadable')


class CarryForwardTests(unittest.TestCase):
    def previous(self, measured_at='2026-09-28'):
        oss = hc.summarise_entry([SOLAR, PORTAL], ui80_observations(), measured_at)
        return oss

    def partial(self):
        observations = {SOLAR['key']: SourceError('rate_limited', 403), PORTAL['key']: SourceError('unavailable', 404)}
        return hc.summarise_entry([SOLAR, PORTAL], observations, RUN)

    def test_keeps_a_recent_measurement_with_its_own_date(self):
        carried = hc.carry_forward(self.partial(), self.previous('2026-09-28'), RUN)
        self.assertEqual((carried['status'], carried['measured_at']), ('carried_forward', '2026-09-28'))
        self.assertEqual(carried['people']['github']['total'], 5)

    def test_does_not_keep_a_measurement_older_than_four_weeks(self):
        self.assertEqual(hc.carry_forward(self.partial(), self.previous('2026-08-31'), RUN)['status'], 'partial')

    def test_does_not_keep_a_measurement_of_different_links(self):
        previous = hc.summarise_entry([SOLAR], {SOLAR['key']: gh_obs('x')}, '2026-09-28')
        self.assertEqual(hc.carry_forward(self.partial(), previous, RUN)['status'], 'partial')

    def test_keeps_a_measurement_when_doi_org_fails_this_run(self):
        doi = '10.57967/HF/6491'
        linked = {'key': 'doi:' + doi.lower(), 'platform': 'huggingface', 'id': None, 'kind': None,
                  'url': f'https://doi.org/{doi}', 'doi': doi}
        resolved = dict(linked, key='huggingface:datasets/org/ds', id='org/ds', kind='datasets', resolved_from=doi)
        previous = hc.summarise_entry([SOLAR, resolved], {SOLAR['key']: gh_obs('Marconi-Lab/SolarIrradiation'),
                                                           resolved['key']: hf_obs('org/ds')}, '2026-09-28')
        fresh = hc.summarise_entry([SOLAR, linked], {SOLAR['key']: gh_obs('Marconi-Lab/SolarIrradiation'),
                                                      linked['key']: SourceError('failed', 502)}, RUN)
        self.assertEqual(hc.carry_forward(fresh, previous, RUN)['status'], 'carried_forward')

    def test_a_complete_measurement_replaces_the_previous_one(self):
        fresh = hc.summarise_entry([SOLAR, PORTAL], ui80_observations(), RUN)
        self.assertEqual(hc.carry_forward(fresh, self.previous(), RUN)['measured_at'], RUN)


class CompareTests(unittest.TestCase):
    def test_websites_only(self):
        self.assertEqual(hc.compare_flags({'website': 2}, None),
                         {'open_asset': False, 'measured': False, 'changed_12m': None, 'several_contributors': None})

    def test_an_open_host_we_do_not_measure(self):
        flags = hc.compare_flags({'kaggle': 1}, None)
        self.assertEqual((flags['open_asset'], flags['measured']), (True, False))

    def test_the_mockup_project(self):
        oss = hc.summarise_entry([SOLAR, PORTAL], ui80_observations(), RUN)
        self.assertEqual(hc.compare_flags({'github': 2}, oss),
                         {'open_asset': True, 'measured': True, 'changed_12m': True, 'several_contributors': True})

    def test_an_archived_repository_unchanged_for_years(self):
        old = asset('github:o/old', 'github', 'o/old')
        oss = hc.summarise_entry([old], {old['key']: gh_obs('o/old', last='2024-10-14', archived=True,
                                                            all_time={'u:a': 4}, active={})}, RUN)
        flags = hc.compare_flags({'github': 1}, oss)
        self.assertEqual((flags['changed_12m'], flags['several_contributors']), (False, False))

    def test_archive_records_are_left_out_of_changed(self):
        rec = asset('zenodo:111', 'zenodo', '111')
        oss = hc.summarise_entry([rec], {rec['key']: zen_obs('111')}, RUN)
        flags = hc.compare_flags({'zenodo': 1}, oss)
        self.assertEqual((flags['measured'], flags['changed_12m'], flags['several_contributors']), (True, None, None))


def project(pid='ui_80', urls=('https://github.com/Marconi-Lab/Solar_irradiation',
                               'https://github.com/Marconi-Lab/Irradiation_Portal')):
    return {'id': pid, 'dataset_links': [{'name': '', 'url': u} for u in urls], 'usecase_links': []}


class BuildEntryTests(unittest.TestCase):
    def test_builds_the_public_entry(self):
        results = {'https://github.com/Marconi-Lab/Irradiation_Portal': {'ok': False, 'status': 404}}
        entry = hc.build_entry(project(), results, [SOLAR, PORTAL], ui80_observations(), None, RUN)
        self.assertEqual(entry['availability'], 'available')
        self.assertEqual(entry['broken_links'], ['https://github.com/Marconi-Lab/Irradiation_Portal'])
        self.assertEqual(entry['hosts'], {'github': 2})
        self.assertEqual((entry['context'], entry['activity_score']), ('recently_updated', 58))
        self.assertTrue(entry['compare']['measured'])

    def test_projects_without_links_get_no_entry(self):
        self.assertIsNone(hc.build_entry(project(urls=()), {}, [], {}, None, RUN))

    def test_partners_can_opt_out(self):
        with mock.patch.object(hc, 'OPT_OUT_IDS', frozenset({'ui_80'})):
            entry = hc.build_entry(project(), {}, [SOLAR, PORTAL], ui80_observations(), None, RUN)
        self.assertEqual(entry['oss'], {'status': 'opted_out'})
        self.assertFalse(entry['compare']['measured'])


def document(entry):
    return {'schema_version': 2, 'generated_at': RUN, 'method': {}, 'entries': {'ui_80': entry}}


class ValidateTests(unittest.TestCase):
    def good(self):
        return hc.build_entry(project(), {}, [SOLAR, PORTAL], ui80_observations(), None, RUN)

    def test_accepts_a_measured_document(self):
        hc.validate_health(document(self.good()))

    def test_rejects_anything_that_looks_like_an_email(self):
        entry = self.good()
        entry['oss']['assets'][0]['note'] = 'contact jane@example.org'
        with self.assertRaises(ValueError):
            hc.validate_health(document(entry))

    def test_rejects_identity_keys(self):
        entry = self.good()
        entry['oss']['assets'][0]['login'] = 'jane'
        with self.assertRaises(ValueError):
            hc.validate_health(document(entry))

    def test_rejects_impossible_counts(self):
        entry = self.good()
        entry['oss']['people']['github']['active'] = 9
        with self.assertRaises(ValueError):
            hc.validate_health(document(entry))
        entry = self.good()
        entry['oss']['reuse']['github']['forks'] = -1
        with self.assertRaises(ValueError):
            hc.validate_health(document(entry))

    def test_rejects_dates_after_the_run(self):
        entry = self.good()
        entry['oss']['last_change']['at'] = '2026-12-01'
        with self.assertRaises(ValueError):
            hc.validate_health(document(entry))


class RunTests(unittest.TestCase):
    def test_aborts_when_most_sources_fail_and_projects_would_degrade(self):
        self.assertTrue(hc.should_abort({'attempted': 10, 'transient': 6, 'degraded': 1}))
        self.assertFalse(hc.should_abort({'attempted': 10, 'transient': 6, 'degraded': 0}))
        self.assertFalse(hc.should_abort({'attempted': 10, 'transient': 2, 'degraded': 2}))
        self.assertFalse(hc.should_abort({'attempted': 0, 'transient': 0, 'degraded': 0}))

    def test_only_requires_explicit_outputs(self):
        with self.assertRaises(SystemExit), mock.patch('sys.stderr'):
            hc.parse_args(['--only', 'ui_80'])
        args = hc.parse_args(['--only', 'ui_80', '--outputs', '/tmp/x.json'])
        self.assertEqual((args.outputs, args.previous), (['/tmp/x.json'], '/tmp/x.json'))

    def test_defaults_write_both_copies_and_carry_from_the_public_one(self):
        args = hc.parse_args([])
        self.assertEqual(args.outputs, ['public/data/health.json', 'docs/data/health.json'])
        self.assertEqual(args.previous, 'public/data/health.json')

    def test_the_run_summary_names_no_people(self):
        doc = document(hc.build_entry(project(), {}, [SOLAR, PORTAL], ui80_observations(), None, RUN))
        text = hc.render_summary(doc, {'attempted': 2, 'transient': 0, 'degraded': 0, 'carried': 0,
                                       'requests': {'GitHub': 9}, 'budgets': {'GitHub': 800}})
        self.assertIn('Weekly health check', text)
        self.assertNotIn('@', text)


class MethodTests(unittest.TestCase):
    def test_the_method_link_points_at_a_document_the_repository_publishes(self):
        # Until the methodology page ships, health.json links the methodology document itself.
        prefix = 'https://github.com/Fair-Forward/datasets/blob/main/'
        self.assertTrue(hc.METHOD_PAGE.startswith(prefix), hc.METHOD_PAGE)
        document = Path(__file__).resolve().parents[2] / hc.METHOD_PAGE[len(prefix):]
        self.assertTrue(document.exists(), document)


if __name__ == '__main__':
    unittest.main()

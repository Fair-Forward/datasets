"""Tests for chaoss_metrics: the pure CHAOSS metric maths behind the open-source health signal."""
import unittest
from datetime import datetime, timezone

import chaoss_metrics as cm

NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


def item(created, reply=None):
    return {'created_at': cm.parse_ts(created), 'first_reply_at': cm.parse_ts(reply) if reply else None}


class ParseTsTests(unittest.TestCase):
    def test_parses_z_suffix_as_utc(self):
        self.assertEqual(cm.parse_ts('2026-08-02T08:54:46Z'),
                         datetime(2026, 8, 2, 8, 54, 46, tzinfo=timezone.utc))

    def test_converts_offsets_to_utc(self):
        self.assertEqual(cm.parse_ts('2026-08-02T10:54:46+02:00'),
                         datetime(2026, 8, 2, 8, 54, 46, tzinfo=timezone.utc))

    def test_reads_a_bare_date_as_midnight_utc(self):
        self.assertEqual(cm.parse_ts('2026-10-05'), datetime(2026, 10, 5, tzinfo=timezone.utc))

    def test_returns_none_for_empty_or_unparseable_values(self):
        for value in (None, '', 'not a date', 42):
            self.assertIsNone(cm.parse_ts(value))


class WindowTests(unittest.TestCase):
    def test_window_covers_365_days_ending_with_the_run_day(self):
        start, end = cm.window_bounds('2026-10-08')
        self.assertEqual(end, datetime(2026, 10, 9, tzinfo=timezone.utc))
        self.assertEqual(start, datetime(2025, 10, 9, tzinfo=timezone.utc))

    def test_counts_calendar_days_between_a_timestamp_and_the_run_date(self):
        self.assertEqual(cm.days_between('2026-08-17T12:26:01Z', '2026-10-05'), 49)
        self.assertIsNone(cm.days_between(None, '2026-10-05'))


class BotTests(unittest.TestCase):
    def test_recognises_bot_accounts(self):
        self.assertTrue(cm.is_bot(login='dependabot[bot]'))
        self.assertTrue(cm.is_bot(login='someone', user_type='Bot'))
        self.assertTrue(cm.is_bot(login='SFconvertbot'))
        self.assertTrue(cm.is_bot(email='49699333+dependabot[bot]@users.noreply.github.com'))
        self.assertTrue(cm.is_bot(name='github-actions[bot]'))
        self.assertTrue(cm.is_bot(name='parquet-converter'))

    def test_does_not_flag_people_whose_names_contain_bot(self):
        self.assertFalse(cm.is_bot(login='abbott'))
        self.assertFalse(cm.is_bot(login='robotics-lab'))
        self.assertFalse(cm.is_bot(name='Talbot'))
        self.assertFalse(cm.is_bot())


class IdentityTests(unittest.TestCase):
    def test_prefers_the_login(self):
        self.assertEqual(cm.identity_key(login='Jane', email='jane@example.org'), 'u:jane')

    def test_maps_github_noreply_addresses_to_the_login(self):
        self.assertEqual(cm.identity_key(email='123+Jane@users.noreply.github.com'), 'u:jane')
        self.assertEqual(cm.identity_key(email='jane@users.noreply.github.com'), 'u:jane')

    def test_falls_back_to_email_then_name(self):
        self.assertEqual(cm.identity_key(email='Jane@Example.org'), 'e:jane@example.org')
        self.assertEqual(cm.identity_key(name=' Jane Doe '), 'n:jane doe')
        self.assertIsNone(cm.identity_key())


class PeopleTests(unittest.TestCase):
    def test_absence_factor_is_the_smallest_group_making_half_the_commits(self):
        self.assertEqual(cm.absence_factor([198, 187, 30, 12, 7]), 2)
        self.assertEqual(cm.absence_factor([5, 5]), 1)
        self.assertEqual(cm.absence_factor([3, 3, 3]), 2)
        self.assertEqual(cm.absence_factor([10]), 1)
        self.assertEqual(cm.absence_factor([1, 7, 1, 1]), 1)

    def test_absence_factor_is_none_when_nobody_contributed(self):
        self.assertIsNone(cm.absence_factor([]))
        self.assertIsNone(cm.absence_factor([0, 0]))

    def test_merge_people_adds_window_authors_missing_from_all_time_counts(self):
        self.assertEqual(cm.merge_people({'u:a': 10, 'u:b': 2}, {'u:a': 3, 'u:c': 1}),
                         {'total': 3, 'active': 2, 'absence_factor': 1})

    def test_merge_people_with_nobody(self):
        self.assertEqual(cm.merge_people({}, {}), {'total': 0, 'active': 0, 'absence_factor': None})


class FirstResponseTests(unittest.TestCase):
    def test_names_a_gap_below_the_minimum(self):
        summary, gap = cm.first_response_summary([item('2026-09-01'), item('2026-09-02')], NOW, minimum=5)
        self.assertIsNone(summary)
        self.assertEqual(gap, {'metric': 'first_response', 'reason': 'too_few_items', 'count': 2})

    def test_reports_the_lower_median_reply_time_in_hours(self):
        items = [item('2026-09-01T00:00:00Z', '2026-09-01T02:00:00Z'),
                 item('2026-09-02T00:00:00Z', '2026-09-03T00:00:00Z'),
                 item('2026-09-03T00:00:00Z', '2026-09-03T05:00:00Z'),
                 item('2026-09-04T00:00:00Z', '2026-09-06T00:00:00Z'),
                 item('2026-09-05T00:00:00Z', '2026-09-05T01:00:00Z'),
                 item('2026-09-06T00:00:00Z', '2026-09-06T03:00:00Z')]
        summary, gap = cm.first_response_summary(items, NOW, minimum=5)
        self.assertIsNone(gap)
        self.assertEqual(summary, {'items': 6, 'answered': 6, 'median_hours': 3.0,
                                   'median_is_lower_bound': False})

    def test_unanswered_items_count_their_age_as_a_lower_bound(self):
        items = [item('2026-10-01T00:00:00Z')] * 3 + [item('2026-09-01T00:00:00Z', '2026-09-01T01:00:00Z')] * 2
        summary, _ = cm.first_response_summary(items, NOW, minimum=5)
        self.assertEqual(summary['median_hours'], 192.0)
        self.assertTrue(summary['median_is_lower_bound'])
        self.assertEqual(summary['answered'], 2)

    def test_median_stays_exact_when_unanswered_items_are_slower_anyway(self):
        items = [item('2026-09-01T00:00:00Z', '2026-09-01T01:00:00Z')] * 4 + [item('2026-01-01T00:00:00Z')]
        summary, _ = cm.first_response_summary(items, NOW, minimum=5)
        self.assertEqual(summary['median_hours'], 1.0)
        self.assertFalse(summary['median_is_lower_bound'])


class ClosureTests(unittest.TestCase):
    def test_counts_opened_and_closed_outside_pull_requests(self):
        prs = ([{'created_at': NOW, 'closed_at': NOW}] * 4) + ([{'created_at': NOW, 'closed_at': None}] * 2)
        self.assertEqual(cm.closure_summary(prs, minimum=5), ({'opened': 6, 'closed': 4}, None))

    def test_names_a_gap_below_the_minimum(self):
        prs = [{'created_at': NOW, 'closed_at': None}] * 2
        self.assertEqual(cm.closure_summary(prs, minimum=5),
                         (None, {'metric': 'change_request_closure', 'reason': 'too_few_items', 'count': 2}))


class ReleaseTests(unittest.TestCase):
    def test_counts_releases_inside_the_window(self):
        start, end = cm.window_bounds('2026-10-08')
        dates = [cm.parse_ts('2025-10-09'), cm.parse_ts('2026-10-08T23:00:00Z'), cm.parse_ts('2025-10-08T23:59:59Z')]
        self.assertEqual(cm.release_summary(dates, start, end),
                         {'in_window': 2, 'total': 3, 'latest_at': '2026-10-08'})

    def test_no_releases(self):
        start, end = cm.window_bounds('2026-10-08')
        self.assertEqual(cm.release_summary([], start, end), {'in_window': 0, 'total': 0, 'latest_at': None})


class LicenseTests(unittest.TestCase):
    def test_github_spdx_ids(self):
        self.assertEqual(cm.normalise_licenses('MIT', 'github'), [{'status': 'detected', 'spdx': 'MIT', 'raw': 'MIT'}])
        self.assertEqual(cm.normalise_licenses('NOASSERTION', 'github'),
                         [{'status': 'unrecognised', 'spdx': None, 'raw': 'NOASSERTION'}])
        self.assertEqual(cm.normalise_licenses(None, 'github'), [{'status': 'none', 'spdx': None, 'raw': None}])

    def test_hugging_face_ids_are_mapped_to_spdx_case(self):
        self.assertEqual(cm.normalise_licenses('cc-by-4.0', 'huggingface'),
                         [{'status': 'detected', 'spdx': 'CC-BY-4.0', 'raw': 'cc-by-4.0'}])
        self.assertEqual([x['spdx'] for x in cm.normalise_licenses(['mit', 'apache-2.0'], 'huggingface')],
                         ['MIT', 'Apache-2.0'])

    def test_unknown_or_custom_licences_are_other(self):
        self.assertEqual(cm.normalise_licenses('other', 'huggingface'), [{'status': 'other', 'spdx': None, 'raw': 'other'}])
        self.assertEqual(cm.normalise_licenses('openrail', 'huggingface'),
                         [{'status': 'other', 'spdx': None, 'raw': 'openrail'}])

    def test_zenodo_ids_and_empty_values(self):
        self.assertEqual(cm.normalise_licenses('cc-by-4.0', 'zenodo')[0]['spdx'], 'CC-BY-4.0')
        self.assertEqual(cm.normalise_licenses([], 'huggingface'), [{'status': 'none', 'spdx': None, 'raw': None}])


class ContextTests(unittest.TestCase):
    def test_archive_records_take_precedence(self):
        self.assertEqual(cm.compute_context(True, [{'at': '2026-10-01', 'archived': False}], '2026-10-05'),
                         'stable_archive')

    def test_recent_change_is_recently_updated(self):
        self.assertEqual(cm.compute_context(False, [{'at': '2026-08-02', 'archived': False}], '2026-10-05'),
                         'recently_updated')

    def test_uses_the_last_change_not_the_last_push(self):
        # spot-the-crop-challenge: pushed Oct 2022, last default-branch commit Jan 2022.
        self.assertEqual(cm.compute_context(False, [{'at': '2022-01-19', 'archived': False}], '2026-10-05'),
                         'no_recent_updates')

    def test_twelve_to_eighteen_months_stays_untagged(self):
        self.assertIsNone(cm.compute_context(False, [{'at': '2025-09-01', 'archived': False}], '2026-10-05'))

    def test_a_fresh_asset_outweighs_an_archived_repository(self):
        dated = [{'at': '2024-10-14', 'archived': True}, {'at': '2026-08-16', 'archived': False}]
        self.assertEqual(cm.compute_context(False, dated, '2026-10-05'), 'recently_updated')

    def test_archived_only_is_no_recent_updates(self):
        self.assertEqual(cm.compute_context(False, [{'at': '2026-09-01', 'archived': True}], '2026-10-05'),
                         'no_recent_updates')

    def test_nothing_dated_gives_no_tag(self):
        self.assertIsNone(cm.compute_context(False, [], '2026-10-05'))


class ActivityTests(unittest.TestCase):
    def test_formula_is_unchanged(self):
        self.assertEqual(cm.compute_activity('recently_updated', [{'at': '2026-08-17', 'archived': False}], [1],
                                             '2026-10-05'), 59)

    def test_stable_archive_uses_the_fixed_recency(self):
        self.assertEqual(cm.compute_activity('stable_archive', [], [], '2026-10-05'), 60)

    def test_archived_only_scores_zero_recency(self):
        self.assertEqual(cm.compute_activity('no_recent_updates', [{'at': '2026-09-01', 'archived': True}], [],
                                             '2026-10-05'), 0)

    def test_popularity_alone(self):
        self.assertEqual(cm.compute_activity(None, [], [10000], '2026-10-05'), 100)

    def test_none_without_any_signal(self):
        self.assertIsNone(cm.compute_activity(None, [], [], '2026-10-05'))


class MetricListTests(unittest.TestCase):
    def test_starter_project_health_metrics_are_flagged(self):
        starter = {m['chaoss'] for m in cm.CHAOSS_METRICS if m['starter']}
        self.assertEqual(starter, {'Time to First Response', 'Change Request Closure Ratio',
                                   'Contributor Absence Factor', 'Release Frequency'})

    def test_every_metric_links_its_chaoss_citation_url(self):
        for metric in cm.CHAOSS_METRICS:
            self.assertRegex(metric['url'], r'^https://chaoss\.community/\?p=\d+$')
            self.assertNotIn('—', metric['label'])


if __name__ == '__main__':
    unittest.main()

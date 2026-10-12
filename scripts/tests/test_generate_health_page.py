"""Tests for generate_health_page: the CHAOSS methodology page."""
import os
import re
import unittest

import chaoss_metrics as cm
import generate_health_page as gp
from utils import ANALYTICS, CSP

WORKFLOW = "on:\n  schedule:\n    - cron: '0 9 * * 1'   # 09:00 UTC every Monday\n"
RANKING = "export const ACTIVITY_WEIGHT = 40\nexport const UNAVAILABLE_PENALTY = 20\n"
WORD_BUDGET = 490  # the page was about 1,350 words; it stays a short reference (about 480)


def visible(page):
    """The text a reader sees: no head, no tags, whitespace collapsed."""
    return ' '.join(re.sub(r'<[^>]+>', ' ', page.split('<body>', 1)[1]).split())


RANKING_JS = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'utils', 'ranking.js')


def project(pid, *urls):
    return {'id': pid, 'dataset_links': [{'name': '', 'url': u} for u in urls], 'usecase_links': []}


CATALOG = {'projects': [
    project('ui_1', 'https://github.com/o/repo', 'https://huggingface.co/datasets/o/ds'),
    project('ui_2', 'https://zenodo.org/records/1'),
    project('ui_3', 'https://www.kaggle.com/datasets/o/k'),
    project('ui_4', 'https://example.org/site'),
]}


class CoverageTests(unittest.TestCase):
    def test_counts_projects_and_distinct_assets_per_platform(self):
        self.assertEqual(gp.coverage(CATALOG), {'projects': 4, 'measurable': 2, 'github': 1, 'huggingface': 1,
                                                'zenodo': 1, 'other_open': 1, 'other_hosts': {'kaggle': 1}})

    def test_counts_the_hosts_of_projects_we_do_not_measure(self):
        catalog = {'projects': CATALOG['projects'] + [
            project('ui_5', 'https://huggingface.co/some-org', 'https://example.org/site'),
            project('ui_6', 'https://www.kaggle.com/datasets/o/k2', 'https://gitlab.com/o/r'),
        ]}
        self.assertEqual(gp.coverage(catalog)['other_hosts'], {'kaggle': 2, 'huggingface_org': 1, 'gitlab': 1})

    def test_names_every_host_we_do_not_measure(self):
        unmeasured = set(gp.OPEN_HOSTS) - set(gp.MEASURED_PLATFORMS)
        self.assertEqual(unmeasured - set(gp.UNMEASURED_HOST_NAMES) - set(gp.ORG_PAGE_HOSTS), set())


class PageTests(unittest.TestCase):
    def page(self, catalog=CATALOG, ranking=RANKING):
        # Whitespace collapsed as a browser renders it, so a phrase may wrap in the template.
        return ' '.join(gp.render_page(catalog, WORKFLOW, ranking).split())

    def test_names_every_chaoss_metric_with_its_citation_link(self):
        page = self.page()
        for metric in cm.CHAOSS_METRICS:
            self.assertIn(metric['chaoss'], page)
            self.assertIn(metric['url'], page)
        self.assertIn('which does not review or endorse this catalogue', page)

    def test_states_the_thresholds_the_collector_applies(self):
        page = self.page()
        self.assertIn(f'at least {cm.MIN_OUTSIDE_ITEMS} outside issues and pull requests', page)
        self.assertIn(f'up to {cm.CARRY_FORWARD_MAX_DAYS} days', page)
        self.assertIn(cm.SCHEDULE_TEXT, page)
        self.assertIn(f'an SDG with at least {cm.MIN_GROUP} measured projects', page)
        self.assertIn('pull requests from the last 12 months', page)
        self.assertIn(f'the {cm.WINDOW_DAYS} days up to the day of measurement', page)
        self.assertIn(f'at least {round(cm.ABSENCE_SHARE * 100)}% of all commits', page)

    def test_states_the_ranking_boost_plainly(self):
        page = self.page()
        self.assertNotIn('we do not rank projects', page)
        self.assertNotIn('small boost', page)
        self.assertIn('adds up to 40 points', page)

    def test_reads_the_ranking_weights_from_the_ranking_code(self):
        page = self.page(ranking='export const ACTIVITY_WEIGHT = 25\nexport const UNAVAILABLE_PENALTY = 7\n')
        self.assertIn('adds up to 25 points', page)
        self.assertIn('loses 7 points', page)

    def test_refuses_a_ranking_it_cannot_read(self):
        with self.assertRaises(ValueError):
            self.page(ranking='export const ACTIVITY_WEIGHT = 40\n')

    def test_reads_the_real_ranking_file(self):
        with open(RANKING_JS, encoding='utf-8') as f:
            weights = gp.ranking_weights(f.read())
        self.assertEqual(set(weights), {'ACTIVITY_WEIGHT', 'UNAVAILABLE_PENALTY'})

    def test_says_bots_are_left_out_of_people_not_of_everything(self):
        page = self.page()
        self.assertIn('Bots are left out of people counts, response times, pull request closure', page)
        self.assertNotIn('every count', page)

    def test_privacy_promise_is_about_contributors(self):
        self.assertIn("never contributors' names, usernames or email addresses", self.page())

    def test_a_project_can_keep_its_previous_measurement(self):
        self.assertIn(f'can keep its previous measurement for up to {cm.CARRY_FORWARD_MAX_DAYS} days', self.page())

    def test_describes_zenodo_views(self):
        self.assertIn('views on Zenodo', self.page())

    def test_speaks_without_we(self):
        self.assertIsNone(re.search(r"\b(we|our|us)\b", visible(self.page()), re.I))

    def test_has_no_slogans(self):
        text = visible(self.page())
        for slogan in ('facts, not scores', 'not scores', 'not that something is wrong'):
            self.assertNotIn(slogan, text)

    def test_stays_a_short_reference(self):
        self.assertLessEqual(len(visible(self.page()).split()), WORD_BUDGET)

    def test_names_the_hosts_and_pages_we_do_not_measure_yet(self):
        catalog = {'projects': CATALOG['projects'] + [
            project('ui_5', 'https://huggingface.co/some-org'),
            project('ui_6', 'https://www.kaggle.com/datasets/o/k2'),
        ]}
        self.assertIn('3 more projects link only to pages not measured yet: Kaggle and organisation '
                      'pages on Hugging Face.', self.page(catalog))

    def test_substitutes_coverage_from_the_catalogue(self):
        self.assertIn('2 of 4 projects', self.page())

    def test_says_which_links_are_read(self):
        self.assertIn('2 of 4 projects link measured assets in their dataset or use-case links', self.page())

    def test_carries_the_shared_head(self):
        page = self.page()
        self.assertIn(CSP, page)
        self.assertIn(ANALYTICS, page)
        self.assertIn('<link rel="canonical" href="https://fair-forward.github.io/datasets/chaoss/">', page)
        self.assertIn('<h1>How the CHAOSS metrics are measured</h1>', page)
        self.assertIn('<title>How the CHAOSS metrics are measured - FAIR Forward Data Catalog</title>', page)
        self.assertIn('Community Health Analytics in Open Source Software', page)

    def test_is_deterministic_and_has_no_em_dash(self):
        self.assertEqual(self.page(), self.page())
        self.assertNotIn('—', self.page())

    def test_refuses_a_schedule_the_workflow_does_not_run(self):
        with self.assertRaises(ValueError):
            gp.render_page(CATALOG, "on:\n  schedule:\n    - cron: '0 6 * * 3'\n", RANKING)


    def test_refuses_a_second_schedule_the_page_does_not_state(self):
        with self.assertRaises(ValueError):
            gp.render_page(CATALOG, WORKFLOW + "    - cron: '0 6 * * 3'\n", RANKING)

if __name__ == '__main__':
    unittest.main()

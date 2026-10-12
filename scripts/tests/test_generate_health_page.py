"""Tests for generate_health_page: the CHAOSS methodology page."""
import os
import unittest
import unittest.mock

import chaoss_metrics as cm
import generate_health_page as gp
from utils import ANALYTICS, CSP

WORKFLOW = "on:\n  schedule:\n    - cron: '0 9 * * 1'   # 09:00 UTC every Monday\n"
RANKING = "export const ACTIVITY_WEIGHT = 40\nexport const UNAVAILABLE_PENALTY = 20\n"
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
        self.assertIn(cm.STARTER_MODEL_URL, page)
        self.assertIn('CHAOSS does not review or endorse this catalogue', page)

    def test_states_the_thresholds_the_collector_applies(self):
        page = self.page()
        self.assertIn(f'at least {cm.MIN_OUTSIDE_ITEMS} outside issues and pull requests', page)
        self.assertIn(f'up to {cm.CARRY_FORWARD_MAX_DAYS} days', page)
        self.assertIn(cm.SCHEDULE_TEXT, page)
        self.assertIn(f'at least {cm.MIN_GROUP} measured projects', page)

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

    def test_says_bots_are_left_out_of_people_not_platform_totals(self):
        page = self.page()
        self.assertIn('left out of every count of people', page)
        self.assertNotIn('are left out of every count (', page)
        self.assertIn('Platform totals such as stars and downloads', page)

    def test_follows_only_the_dois_it_can_measure(self):
        self.assertIn('a Zenodo or Hugging Face DOI is followed to the record it names', self.page())

    def test_privacy_promise_is_about_contributors(self):
        self.assertIn('never the names, usernames or email addresses of contributors', self.page())

    def test_carry_forward_keeps_the_whole_project_measurement(self):
        page = self.page()
        self.assertIn('the project keeps its previous measurement', page)
        self.assertNotIn('A source that cannot be reached keeps', page)

    def test_future_dates_never_become_the_latest(self):
        page = self.page()
        self.assertIn('never becomes the last change or the latest release', page)
        self.assertNotIn('are ignored', page)

    def test_describes_zenodo_views(self):
        self.assertIn('views of a Zenodo record', self.page())

    def test_names_the_hosts_and_pages_we_do_not_measure_yet(self):
        catalog = {'projects': CATALOG['projects'] + [
            project('ui_5', 'https://huggingface.co/some-org'),
            project('ui_6', 'https://www.kaggle.com/datasets/o/k2'),
        ]}
        self.assertIn('3 more projects link only to pages we do not measure yet: Kaggle and organisation '
                      'pages on Hugging Face.', self.page(catalog))

    def test_says_a_fork_counts_its_original_history(self):
        self.assertIn("its counts include its original repository's history", self.page())

    def test_substitutes_coverage_from_the_catalogue(self):
        self.assertIn('2 of 4 projects', self.page())

    def test_carries_the_shared_head(self):
        page = self.page()
        self.assertIn(CSP, page)
        self.assertIn(ANALYTICS, page)
        self.assertIn('<link rel="canonical" href="https://fair-forward.github.io/datasets/chaoss/">', page)
        self.assertIn('<h1>How we apply the CHAOSS metrics</h1>', page)
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

    def test_one_starter_metric_still_reads_as_a_sentence(self):
        only = [dict(m, starter=m['key'] == 'releases') for m in cm.CHAOSS_METRICS]
        with unittest.mock.patch.object(cm, 'CHAOSS_METRICS', only):
            self.assertEqual(gp._starter_sentence(), 'Releases is part of')

if __name__ == '__main__':
    unittest.main()

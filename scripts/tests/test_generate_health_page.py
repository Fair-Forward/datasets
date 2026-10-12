"""Tests for generate_health_page: the open-source health methodology page."""
import unittest

import chaoss_metrics as cm
import generate_health_page as gp
from utils import ANALYTICS, CSP

WORKFLOW = "on:\n  schedule:\n    - cron: '0 9 * * 1'   # 09:00 UTC every Monday\n"


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
                                                'zenodo': 1, 'other_open': 1})


class PageTests(unittest.TestCase):
    def page(self):
        return gp.render_page(CATALOG, WORKFLOW)

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

    def test_substitutes_coverage_from_the_catalogue(self):
        self.assertIn('2 of 4 projects', self.page())

    def test_carries_the_shared_head(self):
        page = self.page()
        self.assertIn(CSP, page)
        self.assertIn(ANALYTICS, page)
        self.assertIn('<link rel="canonical" href="https://fair-forward.github.io/datasets/open-source-health/">', page)

    def test_is_deterministic_and_has_no_em_dash(self):
        self.assertEqual(self.page(), self.page())
        self.assertNotIn('—', self.page())

    def test_refuses_a_schedule_the_workflow_does_not_run(self):
        with self.assertRaises(ValueError):
            gp.render_page(CATALOG, "on:\n  schedule:\n    - cron: '0 6 * * 3'\n")


if __name__ == '__main__':
    unittest.main()

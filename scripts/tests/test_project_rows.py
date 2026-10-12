"""Tests for utils.project_rows: the Sheet's explanation rows are never projects."""
import unittest

import pandas as pd

from utils import project_rows


def ids(df):
    return [index for index, _ in project_rows(df)]


class ProjectRowsTests(unittest.TestCase):
    def test_skips_the_explanation_rows_above_the_first_project(self):
        # Since Oct 2026 the Sheet has a second explanation row ("Valid entries: ...") under the
        # header; build_and_sync.py drops only the first, so the second reached the catalogue.
        df = pd.DataFrame({'Project ID': [None, 'ui_0', 'ui_1'],
                           'Dataset Link': ['Valid entries: [URL(s)]', 'https://a.org', 'https://b.org']})
        self.assertEqual(ids(df), [1, 2])

    def test_a_project_further_down_without_an_id_is_still_a_project(self):
        # It gets a title-derived id, as before, and a warning.
        df = pd.DataFrame({'Project ID': ['', 'ui_0', float('nan'), 'ui_2'],
                           'Dataset Link': ['Valid entries', 'https://a.org', 'https://new.org', 'https://c.org']})
        self.assertEqual(ids(df), [1, 2, 3])

    def test_without_any_project_id_every_row_counts(self):
        # An older export without the column, or an empty column, must not empty the catalogue.
        self.assertEqual(ids(pd.DataFrame({'Dataset Link': ['https://a.org', 'https://b.org']})), [0, 1])
        self.assertEqual(ids(pd.DataFrame({'Project ID': [None, ''], 'Dataset Link': ['a', 'b']})), [0, 1])

    def test_yields_the_rows_themselves(self):
        df = pd.DataFrame({'Project ID': [None, 'ui_0'], 'Title': ['Valid entries', 'Trees']})
        self.assertEqual([row['Title'] for _, row in project_rows(df)], ['Trees'])


if __name__ == '__main__':
    unittest.main()

"""Tests for the sitemap in generate_seo_pages: every listed URL must be a served file."""
import os
import tempfile
import unittest

import generate_seo_pages as seo
from utils import SITE_BASE


class SitemapTests(unittest.TestCase):
    def test_lists_the_methodology_page_once_it_is_built(self):
        with tempfile.TemporaryDirectory() as docs:
            os.makedirs(os.path.join(docs, 'open-source-health'))
            open(os.path.join(docs, 'open-source-health', 'index.html'), 'w').close()
            self.assertIn(f'<loc>{SITE_BASE}open-source-health/</loc>', seo.build_sitemap(['ui_1-x'], docs_dir=docs))

    def test_leaves_it_out_until_then(self):
        with tempfile.TemporaryDirectory() as docs:
            sitemap = seo.build_sitemap(['ui_1-x'], docs_dir=docs)
        self.assertNotIn('open-source-health', sitemap)
        self.assertIn(f'<loc>{SITE_BASE}projects/ui_1-x/</loc>', sitemap)


if __name__ == '__main__':
    unittest.main()

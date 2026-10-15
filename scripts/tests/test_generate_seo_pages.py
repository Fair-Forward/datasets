"""Tests for the sitemap in generate_seo_pages: every listed URL must be a served file."""
import os
import tempfile
import unittest

import generate_seo_pages as seo
from utils import SITE_BASE


class SitemapTests(unittest.TestCase):
    def test_lists_the_methodology_page_once_it_is_built(self):
        with tempfile.TemporaryDirectory() as docs:
            os.makedirs(os.path.join(docs, 'chaoss'))
            open(os.path.join(docs, 'chaoss', 'index.html'), 'w').close()
            self.assertIn(f'<loc>{SITE_BASE}chaoss/</loc>', seo.build_sitemap(['ui_1-x'], docs_dir=docs))

    def test_leaves_it_out_until_then(self):
        with tempfile.TemporaryDirectory() as docs:
            sitemap = seo.build_sitemap(['ui_1-x'], docs_dir=docs)
        self.assertNotIn('chaoss', sitemap)
        self.assertIn(f'<loc>{SITE_BASE}projects/ui_1-x/</loc>', sitemap)


class AboutBlockTests(unittest.TestCase):
    def test_labels_the_editor_as_the_catalogue_entrys_not_the_projects_author(self):
        body = seo.build_body({
            'title': 'X',
            'contact': 'Ada Lovelace (ada@example.org)',
            'editor': 'Luisa Olaya',
        })
        self.assertIn('<p>Catalogue entry by Luisa Olaya</p>', body)
        self.assertNotIn('Authors:', body)
        self.assertLess(body.index('Contact:'), body.index('Catalogue entry by'))


if __name__ == '__main__':
    unittest.main()

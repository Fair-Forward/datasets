"""Tests for health_assets: which catalogue links are measurable open assets."""
import unittest

import health_assets as ha


def entry(dataset=(), usecase=(), additional=()):
    return {'dataset_links': [{'name': '', 'url': u} for u in dataset],
            'usecase_links': [{'name': '', 'url': u} for u in usecase],
            'additional_resources': [{'name': '', 'url': u} for u in additional]}


class ParseGithubTests(unittest.TestCase):
    def test_repository_urls_in_every_catalogue_shape(self):
        for url in ('https://github.com/think-ke/sheng-dataset/',
                    'https://github.com/EconAIorg/vayu-gnn/tree/main',
                    'https://github.com/WadhwaniAI/pest-management-opendata?tab=readme-ov-file',
                    'https://www.github.com/NaLamKI/geo-ai.git'):
            self.assertIsNotNone(ha.parse_github(url), url)
        self.assertEqual(ha.parse_github('https://github.com/NaLamKI/geo-ai.git'), ('NaLamKI', 'geo-ai'))

    def test_organisation_pages_and_reserved_paths_are_not_repositories(self):
        self.assertIsNone(ha.parse_github('https://github.com/crop-type-mapping'))
        self.assertIsNone(ha.parse_github('https://github.com/orgs/some-org/repositories'))


class ParseHuggingFaceTests(unittest.TestCase):
    def test_models_datasets_and_spaces(self):
        self.assertEqual(ha.parse_hf('https://huggingface.co/datasets/KaraAgroAI/CADI-AI'), ('datasets', 'KaraAgroAI/CADI-AI'))
        self.assertEqual(ha.parse_hf('https://huggingface.co/KaraAgroAI/CADI-AI'), ('models', 'KaraAgroAI/CADI-AI'))
        self.assertEqual(ha.parse_hf('https://huggingface.co/spaces/GIZ/audit_assistant/tree/main'), ('spaces', 'GIZ/audit_assistant'))
        self.assertEqual(ha.parse_hf('https://huggingface.co/roymukund/Voice-Tech-CDAC-Submission/tree/main'),
                         ('models', 'roymukund/Voice-Tech-CDAC-Submission'))
        self.assertEqual(ha.parse_hf('https://hf.co/datasets/x/y'), ('datasets', 'x/y'))

    def test_organisation_pages_are_not_assets(self):
        self.assertIsNone(ha.parse_hf('https://huggingface.co/SYSPIN'))


class ClassifyTests(unittest.TestCase):
    def assertHost(self, url, host, platform=None, id_=None, kind=None):
        info = ha.classify_url(url)
        self.assertEqual((info['host'], info['platform'], info['id'], info['kind']), (host, platform, id_, kind), url)

    def test_measured_platforms(self):
        self.assertHost('https://github.com/Marconi-Lab/Solar_irradiation', 'github', 'github', 'Marconi-Lab/Solar_irradiation')
        self.assertHost('https://huggingface.co/datasets/C4IR-RW/kinya-ag-tts', 'huggingface', 'huggingface',
                        'C4IR-RW/kinya-ag-tts', 'datasets')
        self.assertHost('https://zenodo.org/records/15778396', 'zenodo', 'zenodo', '15778396')
        self.assertHost('https://doi.org/10.5281/zenodo.15704554', 'zenodo', 'zenodo', '15704554')

    def test_hugging_face_doi_is_resolved_later(self):
        info = ha.classify_url('https://doi.org/10.57967/hf/6491')
        self.assertEqual((info['host'], info['platform'], info['id'], info['doi']),
                         ('huggingface', 'huggingface', None, '10.57967/hf/6491'))

    def test_open_hosts_we_do_not_measure_yet(self):
        self.assertHost('https://github.com/crop-type-mapping', 'github_org')
        self.assertHost('https://huggingface.co/prosa-text', 'huggingface_org')
        self.assertHost('https://gitlab.com/gramvaani/giz_kab_bert_sourcecode', 'gitlab')
        self.assertHost('https://www.kaggle.com/datasets/responsibleailab/crop-disease-ghana/code', 'kaggle')
        self.assertHost('https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/3S7KPQ', 'dataverse')
        self.assertHost('https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/CGHWZE', 'dataverse')
        self.assertHost('https://figshare.com/articles/dataset/The_First_Open_Dataset/30258772', 'figshare')
        self.assertHost('https://doi.org/10.4121/d97e338b-dc94-4e3d-a473-6dd3d4b48898.v1', 'doi_other')

    def test_websites(self):
        for url in ('https://space4innovation.github.io/ltomekatip/index.html',
                    'https://fair-forward.github.io/datasets?search=tunga',
                    'https://plus.figshare.com/account/mycontent/items',
                    'https://drive.google.com/drive/folders/abc',
                    'https://www.bmz-digital.global/'):
            self.assertHost(url, 'website')

    def test_open_hosts_exclude_websites_only(self):
        self.assertNotIn('website', ha.OPEN_HOSTS)
        self.assertIn('kaggle', ha.OPEN_HOSTS)
        self.assertEqual(set(ha.MEASURED_PLATFORMS), {'github', 'huggingface', 'zenodo'})


class DiscoverTests(unittest.TestCase):
    def test_dedupes_the_same_asset_linked_twice(self):
        e = entry(dataset=['https://github.com/WadhwaniAI/pest-management-opendata?tab=readme-ov-file'],
                  usecase=['https://github.com/wadhwaniai/pest-management-opendata/'])
        self.assertEqual([a['key'] for a in ha.discover_assets(e)], ['github:wadhwaniai/pest-management-opendata'])

    def test_a_dataset_and_a_model_with_the_same_id_are_two_assets(self):
        e = entry(dataset=['https://huggingface.co/datasets/KaraAgroAI/CADI-AI'],
                  usecase=['https://huggingface.co/KaraAgroAI/CADI-AI'])
        self.assertEqual([a['key'] for a in ha.discover_assets(e)],
                         ['huggingface:datasets/karaagroai/cadi-ai', 'huggingface:models/karaagroai/cadi-ai'])

    def test_keeps_platform_id_kind_url_and_doi(self):
        e = entry(dataset=['https://doi.org/10.5281/zenodo.15704554', 'https://doi.org/10.57967/hf/6491'])
        assets = ha.discover_assets(e)
        self.assertEqual(assets[0], {'key': 'zenodo:15704554', 'platform': 'zenodo', 'id': '15704554', 'kind': None,
                                     'url': 'https://doi.org/10.5281/zenodo.15704554', 'doi': '10.5281/zenodo.15704554'})
        self.assertEqual(assets[1]['key'], 'doi:10.57967/hf/6491')
        self.assertIsNone(assets[1]['id'])

    def test_ignores_unmeasured_hosts_and_additional_resources(self):
        e = entry(dataset=['https://www.kaggle.com/datasets/a/b', 'https://github.com/crop-type-mapping'],
                  additional=['https://github.com/waleghwa/low-resource-language-data'])
        self.assertEqual(ha.discover_assets(e), [])

    def test_host_counts_cover_every_in_scope_link(self):
        e = entry(dataset=['https://github.com/a/b', 'https://github.com/a/c', 'https://example.org/x'],
                  usecase=['https://huggingface.co/SYSPIN'], additional=['https://zenodo.org/records/1'])
        self.assertEqual(ha.host_counts(e), {'github': 2, 'huggingface_org': 1, 'website': 1})


if __name__ == '__main__':
    unittest.main()

"""Tests for sheet_corrections: correcting the master Sheet from what the sources declare."""
import json
import os
import tempfile
import unittest
from unittest import mock

import sheet_corrections as sc
from generate_catalog_data import KNOWN_LICENSE_VALUES
from text_parsing import spdx_for

HEADER = ['Project ID', 'Title', 'Access to the dataset [link]',
          'Access to AI Model /Software / AI System [link]', 'License', 'Code License']
EXPLAIN = ['Stable id', 'Name', 'Where the data is', 'Where the model is', 'Licence', 'Code licence']
ID, DATASET, MODEL, LICENSE, CODE_LICENSE = 0, 2, 3, 4, 5
TODAY = '2026-10-12'


def lic(spdx, status='detected'):
    return {'status': status, 'spdx': spdx, 'raw': spdx.lower() if spdx else None}


NONE = lic(None, 'none')


def hf(kind, repo_id, *licenses, renamed_from=None, status='measured', url=None):
    prefix = '' if kind == 'models' else f'{kind}/'
    return {'platform': 'huggingface', 'kind': kind, 'id': repo_id, 'renamed_from': renamed_from,
            'url': url or f'https://huggingface.co/{prefix}{renamed_from or repo_id}', 'status': status,
            'license': list(licenses) or [NONE]}


def gh(repo, *licenses, renamed_from=None, status='measured'):
    return {'platform': 'github', 'id': repo, 'renamed_from': renamed_from,
            'url': f'https://github.com/{renamed_from or repo}', 'status': status,
            'license': list(licenses) or [NONE]}


def zen(record, *licenses, concept=None, latest=True, resource_type='dataset', url=None):
    return {'platform': 'zenodo', 'id': str(record), 'concept_id': str(concept) if concept else None,
            'linked_is_latest': latest, 'resource_type': resource_type, 'status': 'measured',
            'url': url or f'https://zenodo.org/records/{record}', 'license': list(licenses) or [NONE]}


def entry(*assets, status='measured'):
    return {'oss': {'status': status, 'assets': list(assets)}}


def health(entries):
    return {'schema_version': 2, 'generated_at': '2026-10-09', 'entries': entries}


def row(pid, dataset='', model='', license='', code_license=''):
    return [pid, f'Project {pid}', dataset, model, license, code_license]


def sheet(*rows):
    return [HEADER, EXPLAIN] + [list(r) for r in rows]


def run(doc, grid, notes=(), formulas=(), protected=(), verify=lambda url: True, code=False):
    """The plan for the License and link cells, or with code=True for the Code License cells only."""
    changes, skipped = sc.plan(doc, grid, list(notes), list(formulas), list(protected), verify, TODAY)
    if code:
        return ([c for c in changes if c['column'] == 'code_license'],
                [x for x in skipped if x['what'] == 'Code License'])
    return ([c for c in changes if c['column'] != 'code_license'],
            [x for x in skipped if x['what'] != 'Code License'])


def notes_at(r, c, text, rows=3):
    grid = [[''] * len(HEADER) for _ in range(rows)]
    grid[r][c] = text
    return grid


class DecideLicenseTests(unittest.TestCase):
    def test_a_dataset_licence_wins_over_a_model_and_code(self):
        decision = sc.decide_license([hf('datasets', 'o/d', lic('CC-BY-SA-4.0')),
                                      hf('models', 'o/m', lic('AGPL-3.0')), gh('o/c', lic('MIT'))])
        self.assertEqual((decision['value'], decision['tier']), ('CC-BY-SA 4.0', 'dataset'))

    def test_a_model_licence_decides_when_there_is_no_dataset(self):
        decision = sc.decide_license([gh('o/c'), hf('models', 'o/m', lic('MIT'))])
        self.assertEqual((decision['value'], decision['tier']), ('MIT', 'model'))

    def test_code_decides_only_when_nothing_else_declares(self):
        decision = sc.decide_license([gh('o/c', lic('GPL-3.0'))])
        self.assertEqual((decision['value'], decision['tier']), ('GPL 3.0', 'code'))

    def test_several_licences_in_the_deciding_group_settle_nothing(self):
        decision = sc.decide_license([hf('datasets', 'o/a', lic('CC-BY-4.0')),
                                      hf('datasets', 'o/b', lic('CC-BY-2.0'))])
        self.assertNotIn('value', decision)
        self.assertIn('CC-BY-2.0, CC-BY-4.0', decision['reason'])

    def test_a_dataset_that_declares_nothing_settles_nothing(self):
        # ui_56: a Common Voice set (CC0 at Mozilla) declares nothing on Hugging Face, its sibling CC-BY-4.0.
        decision = sc.decide_license([hf('datasets', 'o/a'), hf('datasets', 'o/b', lic('CC-BY-4.0'))])
        self.assertNotIn('value', decision)
        self.assertEqual(decision['reason'], 'not every dataset declares a licence')

    def test_datasets_that_declare_nothing_leave_no_say_to_a_model(self):
        self.assertEqual(sc.decide_license([hf('datasets', 'o/a'), hf('models', 'o/m', lic('MIT'))]),
                         {'reason': None})

    def test_a_custom_licence_settles_nothing(self):
        decision = sc.decide_license([hf('datasets', 'o/a', lic(None, 'other')),
                                      hf('models', 'o/m', lic('MIT'))])
        self.assertNotIn('value', decision)

    def test_an_unreadable_asset_settles_nothing(self):
        decision = sc.decide_license([hf('datasets', 'o/a', lic('CC-BY-4.0')), gh('o/x', status='unavailable')])
        self.assertNotIn('value', decision)
        self.assertEqual(decision['reason'], 'not every linked asset could be read')

    def test_zenodo_counts_as_data_unless_it_is_software(self):
        # Uploaders file datasets as publications (ui_39 is a dataset typed "publication").
        decision = sc.decide_license([zen(1, lic('CC-BY-4.0'), resource_type='publication'),
                                      hf('models', 'o/m', lic('MIT'))])
        self.assertEqual((decision['value'], decision['tier']), ('CC-BY 4.0', 'dataset'))
        decision = sc.decide_license([zen(2, lic('MIT'), resource_type='software'),
                                      hf('models', 'o/m', lic('Apache-2.0'))])
        self.assertEqual((decision['value'], decision['tier']), ('Apache 2.0', 'model'))

    def test_hugging_face_spaces_count_as_code(self):
        decision = sc.decide_license([hf('spaces', 'o/s', lic('MIT'))])
        self.assertEqual(decision['tier'], 'code')

    def test_a_licence_the_catalogue_cannot_spell_settles_nothing(self):
        decision = sc.decide_license([hf('datasets', 'o/a', lic('CC-BY-NC-4.0'))])
        self.assertNotIn('value', decision)
        self.assertIn('CC-BY-NC-4.0', decision['reason'])

    def test_nothing_declared_gives_no_reason_to_report(self):
        self.assertEqual(sc.decide_license([gh('o/c')]), {'reason': None})


class RecognisedLicenseTests(unittest.TestCase):
    def test_reads_the_spellings_the_catalogue_normalises(self):
        for text, value in [('', ''), (' CC-BY 4.0 ', 'CC-BY 4.0'), ('cc-by', 'CC-BY 4.0'),
                            ('https://creativecommons.org/licenses/by/4.0/', 'CC-BY 4.0'),
                            ('CC BY 4.0', 'CC-BY 4.0'), ('GPL 3.0', 'GPL 3.0'), ('MIT', 'MIT')]:
            self.assertEqual(sc.recognised_license(text), value, text)

    def test_text_that_is_not_one_licence_is_left_for_a_person(self):
        self.assertIsNone(sc.recognised_license('Data CC0, code MIT'))
        self.assertIsNone(sc.recognised_license('see the repository'))

    def test_gpl_has_a_catalogue_spelling_and_an_spdx_id(self):
        self.assertIn('GPL 3.0', KNOWN_LICENSE_VALUES)
        self.assertEqual(spdx_for('GPL 3.0'), 'GPL-3.0')
        self.assertEqual(sc.SPDX_TO_CATALOGUE['GPL-3.0'], 'GPL 3.0')


class PlanLicenseTests(unittest.TestCase):
    def test_fills_an_empty_licence_from_code(self):
        changes, _ = run(health({'ui_79': entry(gh('o/c', lic('GPL-3.0')))}), sheet(row('ui_79')))
        self.assertEqual(len(changes), 1)
        change = changes[0]
        self.assertEqual((change['cell'], change['old'], change['new'], change['kind']), ('E3', '', 'GPL 3.0', 'fill'))
        self.assertTrue(change['note'].startswith(
            '[Source check] 2026-10-12: Was empty; the repository on GitHub declares GPL-3.0.'))
        self.assertIn('write Keep in square brackets', change['note'])
        self.assertNotIn('[Keep]', change['note'])

    def test_overwrites_a_licence_the_data_contradicts(self):
        changes, _ = run(health({'ui_44': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))}),
                         sheet(row('ui_44', license='Apache 2.0')))
        self.assertEqual((changes[0]['new'], changes[0]['kind']), ('CC-BY 4.0', 'overwrite'))
        self.assertIn('Was "Apache 2.0"; the dataset on Hugging Face declares CC-BY-4.0.', changes[0]['note'])

    def test_code_never_replaces_a_licence(self):
        changes, skipped = run(health({'ui_75': entry(gh('o/c', lic('Apache-2.0')))}),
                               sheet(row('ui_75', license='CC-BY 4.0')))
        self.assertEqual(changes, [])
        self.assertIn('only a dataset\'s own licence replaces a filled cell, so the Sheet keeps "CC-BY 4.0"',
                      skipped[0]['reason'])

    def test_a_model_licence_fills_an_empty_cell_but_never_replaces_one(self):
        doc = health({'ui_1': entry(hf('models', 'o/m', lic('MIT')))})
        changes, _ = run(doc, sheet(row('ui_1')))
        self.assertEqual((changes[0]['new'], changes[0]['kind']), ('MIT', 'fill'))
        changes, skipped = run(doc, sheet(row('ui_1', license='CC-BY 4.0')))
        self.assertEqual(changes, [])
        self.assertIn('so the Sheet keeps "CC-BY 4.0"', skipped[0]['reason'])

    def test_a_zenodo_publication_fills_but_never_replaces(self):
        # A record filed as a publication can be a paper with Zenodo's default licence.
        doc = health({'ui_1': entry(zen(1, lic('CC-BY-4.0'), resource_type='publication'))})
        changes, _ = run(doc, sheet(row('ui_1')))
        self.assertEqual(changes[0]['new'], 'CC-BY 4.0')
        changes, skipped = run(doc, sheet(row('ui_1', license='CC0 1.0')))
        self.assertEqual(changes, [])
        self.assertIn('so the Sheet keeps "CC0 1.0"', skipped[0]['reason'])

    def test_data_linked_where_the_check_cannot_read_blocks_any_licence_change(self):
        # ui_59: Common Voice at Mozilla's Data Collective (CC0) next to a CC-BY-4.0 set on Hugging Face.
        elsewhere = 'https://datacollective.mozillafoundation.org/datasets?q=common+voice&locale=rw'
        doc = health({'ui_59': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))})
        cells = f'{elsewhere}\nhttps://huggingface.co/datasets/o/d'
        for licence in ('CC-0', ''):
            changes, skipped = run(doc, sheet(row('ui_59', dataset=cells, license=licence)))
            self.assertEqual(changes, [], licence)
            self.assertIn(f'the dataset column also links {elsewhere}', skipped[0]['reason'])

    def test_leaves_a_cell_that_already_says_it_in_another_spelling(self):
        changes, skipped = run(health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))}),
                               sheet(row('ui_1', license='cc-by')))
        self.assertEqual((changes, skipped), ([], []))

    def test_leaves_free_text_for_a_person(self):
        changes, skipped = run(health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))}),
                               sheet(row('ui_1', license='Data CC0, code MIT')))
        self.assertEqual(changes, [])
        self.assertIn('not one licence the catalogue knows', skipped[0]['reason'])

    def test_a_silent_dataset_blocks_a_change(self):
        changes, skipped = run(health({'ui_56': entry(hf('datasets', 'o/a'), hf('datasets', 'o/b', lic('CC-BY-4.0')))}),
                               sheet(row('ui_56', license='CC0 1.0')))
        self.assertEqual((changes, skipped[0]['reason']), ([], 'not every dataset declares a licence'))

    def test_counts_several_declaring_assets(self):
        changes, _ = run(health({'ui_87': entry(hf('datasets', 'o/a', lic('CC-BY-4.0')),
                                                hf('datasets', 'o/b', lic('CC-BY-4.0')),
                                                gh('o/c', lic('CC-BY-SA-4.0')))}),
                         sheet(row('ui_87', license='Apache 2.0')))
        self.assertIn('2 datasets on Hugging Face declare CC-BY-4.0.', changes[0]['note'])

    def test_a_partial_measurement_changes_no_licence(self):
        changes, _ = run(health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')), status='partial')}),
                         sheet(row('ui_1')))
        self.assertEqual(changes, [])

    def test_a_keep_note_pins_the_cell(self):
        changes, skipped = run(health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))}),
                               sheet(row('ui_1', license='CC0 1.0')),
                               notes=notes_at(2, LICENSE, 'Agreed with the partner. [Keep]'))
        self.assertEqual(changes, [])
        self.assertEqual(skipped[0]['reason'], 'pinned with [Keep]')

    def test_protected_and_formula_cells_are_left_alone(self):
        doc = health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))})
        grid = sheet(row('ui_1'))
        changes, skipped = run(doc, grid, protected=[(1, 4, None, None)])
        self.assertEqual((changes, skipped[0]['reason']), ([], 'protected in the Sheet'))
        changes, skipped = run(doc, grid, formulas=notes_at(2, LICENSE, '=A1'))
        self.assertEqual((changes, skipped[0]['reason']), ([], 'the cell holds a formula'))

    def test_a_number_in_the_formula_view_is_not_a_formula(self):
        # The FORMULA rendering returns a number typed into the cell as a number, not text.
        doc = health({'ui_1': entry(hf('datasets', 'o/d', lic('CC0-1.0')))})
        changes, _ = run(doc, sheet(row('ui_1', license='4.0')), formulas=notes_at(2, LICENSE, 4.0))
        self.assertEqual((changes[0]['old'], changes[0]['new']), ('4.0', 'CC0 1.0'))

    def test_an_unprotected_exception_inside_a_protected_range_can_be_written(self):
        doc = health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))})
        whole_sheet = (None, None, None, None, ((2, None, LICENSE, LICENSE + 1),))
        changes, _ = run(doc, sheet(row('ui_1')), protected=[whole_sheet])
        self.assertEqual(changes[0]['new'], 'CC-BY 4.0')
        changes, skipped = run(doc, sheet(row('ui_1')), protected=[(None, None, None, None, ((2, None, 0, 1),))])
        self.assertEqual((changes, skipped[0]['reason']), ([], 'protected in the Sheet'))

    def test_keeps_a_persons_note_and_replaces_its_own_record(self):
        old = 'Checked with the partner.\n\n[Source check] 2026-10-05: Was "MIT"; something.'
        changes, _ = run(health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))}),
                         sheet(row('ui_1', license='CC0 1.0')), notes=notes_at(2, LICENSE, old))
        note = changes[0]['note']
        self.assertTrue(note.startswith('Checked with the partner.\n\n[Source check] 2026-10-12: Was "CC0 1.0"'))
        self.assertNotIn('2026-10-05', note)


class PlanLinkTests(unittest.TestCase):
    def test_a_renamed_repository_gets_its_new_address(self):
        cell = ('Code: https://github.com/Marconi-Lab/Solar_irradiation\n'
                'Portal: https://github.com/Marconi-Lab/Irradiation_Portal')
        doc = health({'ui_80': entry(gh('Marconi-Lab/SolarIrradiation', renamed_from='Marconi-Lab/Solar_irradiation'))})
        changes, _ = run(doc, sheet(row('ui_80', model=cell)))
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['cell'], 'D3')
        self.assertEqual(changes[0]['new'], 'Code: https://github.com/Marconi-Lab/SolarIrradiation\n'
                                             'Portal: https://github.com/Marconi-Lab/Irradiation_Portal')
        self.assertIn('Replaced https://github.com/Marconi-Lab/Solar_irradiation with '
                      'https://github.com/Marconi-Lab/SolarIrradiation; the repository was renamed on GitHub.',
                      changes[0]['note'])

    def test_replaces_only_the_whole_link(self):
        cell = 'https://github.com/o/r https://github.com/o/r-extra https://github.com/o/r/tree/main (see https://github.com/o/r.)'
        changes, _ = run(health({'ui_1': entry(gh('o/s', renamed_from='o/r'))}), sheet(row('ui_1', model=cell)))
        self.assertEqual(changes[0]['new'], 'https://github.com/o/s https://github.com/o/r-extra '
                                            'https://github.com/o/r/tree/main (see https://github.com/o/s.)')

    def test_an_older_zenodo_version_becomes_the_all_versions_doi(self):
        doc = health({'ui_16': entry(zen(15778396, lic('CC-BY-4.0'), concept=15778395, latest=False)),
                      'ui_18': entry(zen(15704554, lic('CC-BY-4.0'), concept=15704553, latest=False,
                                         url='https://doi.org/10.5281/zenodo.15704554'))})
        changes, _ = run(doc, sheet(row('ui_16', dataset='https://zenodo.org/records/15778396', license='CC-BY 4.0'),
                                    row('ui_18', dataset='https://doi.org/10.5281/zenodo.15704554',
                                        license='CC-BY 4.0')))
        self.assertEqual([c['new'] for c in changes], ['https://doi.org/10.5281/zenodo.15778395',
                                                       'https://doi.org/10.5281/zenodo.15704553'])
        self.assertIn('an older version of the Zenodo record', changes[0]['note'])
        self.assertIn('which always opens the latest version', changes[0]['note'])

    def test_the_latest_version_and_unknown_relations_stay(self):
        doc = health({'ui_1': entry(zen(5, concept=4, latest=True)), 'ui_2': entry(zen(7, concept=6, latest=None))})
        changes, skipped = run(doc, sheet(row('ui_1', dataset='https://zenodo.org/records/5'),
                                          row('ui_2', dataset='https://zenodo.org/records/7')))
        self.assertEqual((changes, skipped), ([], []))

    def test_renamed_links_in_one_cell_make_one_change(self):
        doc = health({'ui_12': entry(hf('datasets', 'KaraAgro-AI/CADI-AI', renamed_from='KaraAgroAI/CADI-AI'),
                                     hf('models', 'KaraAgro-AI/CADI-AI', renamed_from='KaraAgroAI/CADI-AI'))})
        both = 'https://huggingface.co/datasets/KaraAgroAI/CADI-AI, https://huggingface.co/KaraAgroAI/CADI-AI'
        changes, _ = run(doc, sheet(row('ui_12', dataset=both)))
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['new'], 'https://huggingface.co/datasets/KaraAgro-AI/CADI-AI, '
                                            'https://huggingface.co/KaraAgro-AI/CADI-AI')
        changes, _ = run(doc, sheet(row('ui_12', dataset='https://huggingface.co/datasets/KaraAgroAI/CADI-AI',
                                        model='https://huggingface.co/KaraAgroAI/CADI-AI')))
        self.assertEqual([c['cell'] for c in changes], ['C3', 'D3'])

    def test_a_new_address_that_does_not_answer_is_not_written(self):
        doc = health({'ui_1': entry(gh('o/s', renamed_from='o/r'))})
        changes, skipped = run(doc, sheet(row('ui_1', model='https://github.com/o/r')), verify=lambda url: False)
        self.assertEqual(changes, [])
        self.assertIn('did not answer', skipped[0]['reason'])

    def test_a_link_already_corrected_is_left_alone(self):
        doc = health({'ui_1': entry(gh('o/s', renamed_from='o/r'))})
        changes, skipped = run(doc, sheet(row('ui_1', model='https://github.com/o/s')))
        self.assertEqual((changes, skipped), ([], []))

    def test_a_link_missing_from_the_sheet_is_reported(self):
        doc = health({'ui_1': entry(gh('o/s', renamed_from='o/r'))})
        changes, skipped = run(doc, sheet(row('ui_1', model='https://example.org')))
        self.assertEqual(changes, [])
        self.assertIn('not found in the Sheet', skipped[0]['reason'])

    def test_a_doi_link_to_a_renamed_repository_stays(self):
        asset = hf('datasets', 'new/name', renamed_from='old/name', url='https://doi.org/10.57967/hf/1234')
        changes, skipped = run(health({'ui_9': entry(asset)}), sheet(row('ui_9', dataset='https://doi.org/10.57967/hf/1234')))
        self.assertEqual((changes, skipped), ([], []))

    def test_links_of_an_asset_not_read_this_week_stay(self):
        doc = health({'ui_1': entry(gh('o/s', renamed_from='o/r', status='failed'), status='partial')})
        changes, _ = run(doc, sheet(row('ui_1', model='https://github.com/o/r')))
        self.assertEqual(changes, [])

    def test_a_pinned_link_cell_is_left_alone(self):
        doc = health({'ui_1': entry(gh('o/s', renamed_from='o/r'))})
        changes, skipped = run(doc, sheet(row('ui_1', model='https://github.com/o/r')),
                               notes=notes_at(2, MODEL, '[Keep] the partner links the old name'))
        self.assertEqual((changes, skipped[0]['reason']), ([], 'pinned with [Keep]'))


class SheetShapeTests(unittest.TestCase):
    def test_a_project_missing_from_the_sheet_is_reported(self):
        _, skipped = run(health({'ui_9': entry(gh('o/c', lic('MIT')))}), sheet(row('ui_1')))
        self.assertEqual((skipped[0]['pid'], skipped[0]['reason']), ('ui_9', 'not in the Sheet'))

    def test_a_project_id_in_two_rows_is_left_alone(self):
        changes, skipped = run(health({'ui_1': entry(gh('o/c', lic('MIT')))}), sheet(row('ui_1'), row('ui_1')))
        self.assertEqual(changes, [])
        self.assertIn('several rows', skipped[0]['reason'])

    def test_a_row_with_only_its_project_id_is_not_a_project(self):
        # The Sheet holds placeholder rows with nothing but an ID (rows 137, 138 and 140 in Oct 2026).
        changes, skipped = run(health({'ui_87': entry(gh('o/c', lic('GPL-3.0')))}),
                               sheet(row('ui_87'), ['ui_87', '', '', '', '']))
        self.assertEqual(([c['cell'] for c in changes], skipped), (['E3'], []))

    def test_stops_when_a_column_is_missing(self):
        grid = sheet(row('ui_1'))
        grid[0] = HEADER[:4] + ['Usage notes']
        with self.assertRaises(ValueError):
            run(health({}), grid)

    def test_matches_headers_regardless_of_case_and_spacing(self):
        grid = sheet(row('ui_79'))
        grid[0] = [' project id', 'Title', 'access to the dataset  [link]',
                   'Access to AI Model /Software / AI System [link] ', 'LICENSE', 'code  license']
        changes, _ = run(health({'ui_79': entry(gh('o/c', lic('GPL-3.0')))}), grid)
        self.assertEqual(changes[0]['cell'], 'E3')

    def test_projects_are_planned_in_catalogue_order(self):
        doc = health({'ui_10': entry(gh('o/a', lic('MIT'))), 'ui_9': entry(gh('o/b', lic('MIT')))})
        changes, _ = run(doc, sheet(row('ui_10'), row('ui_9')))
        self.assertEqual([c['pid'] for c in changes], ['ui_9', 'ui_10'])


class FakeWorksheet:
    id = 7
    title = "Portfolio's sheet"

    def __init__(self, grid, edited=None):
        self.grid, self.edited, self.requests, self.reads = grid, edited or {}, [], []
        self.spreadsheet = self

    def batch_update(self, body):
        self.requests.append(body['requests'])

    def fetch_sheet_metadata(self, params=None):
        self.reads.append(params['ranges'])
        data = []
        for rng in params['ranges']:
            cell = rng.split('!')[1]
            col, r = ord(cell[0]) - 65, int(cell[1:]) - 1
            value, note = self.edited.get(cell, (self.grid[r][col], ''))
            cell_data = {}
            if value:
                cell_data['formattedValue'] = value
            if note:
                cell_data['note'] = note
            data.append({'rowData': [{'values': [cell_data]}]})
        return {'sheets': [{'data': data}]}


class CodeLicenseTests(unittest.TestCase):
    def test_fills_the_code_licence_from_every_repository(self):
        doc = health({'ui_23': entry(gh('o/a', lic('MIT')), gh('o/b', lic('Apache-2.0')), gh('o/c', lic('MIT')))})
        changes, _ = run(doc, sheet(row('ui_23', license='CC-BY 4.0')), code=True)
        self.assertEqual((changes[0]['cell'], changes[0]['new'], changes[0]['kind']), ('F3', 'Apache 2.0; MIT', 'fill'))
        self.assertIn('Was empty; 3 code repositories declare Apache-2.0, MIT.', changes[0]['note'])

    def test_the_data_licence_cell_is_not_touched_by_code(self):
        changes, _ = run(health({'ui_75': entry(gh('o/c', lic('Apache-2.0')))}),
                         sheet(row('ui_75', license='CC-BY 4.0')))
        self.assertEqual(changes, [])

    def test_replaces_a_code_licence_the_source_contradicts(self):
        changes, _ = run(health({'ui_1': entry(gh('o/c', lic('GPL-3.0')))}),
                         sheet(row('ui_1', code_license='MIT')), code=True)
        self.assertEqual((changes[0]['new'], changes[0]['kind']), ('GPL 3.0', 'overwrite'))

    def test_leaves_a_cell_that_already_lists_the_same_licences(self):
        doc = health({'ui_1': entry(gh('o/a', lic('MIT')), gh('o/b', lic('Apache-2.0')))})
        self.assertEqual(run(doc, sheet(row('ui_1', code_license='MIT; Apache 2.0')), code=True), ([], []))

    def test_a_repository_without_a_licence_settles_nothing(self):
        doc = health({'ui_1': entry(gh('o/a', lic('MIT')), gh('o/b'))})
        changes, skipped = run(doc, sheet(row('ui_1')), code=True)
        self.assertEqual(changes, [])
        self.assertEqual(skipped[0]['reason'], 'not every code repository declares a licence')

    def test_a_custom_or_unreadable_repository_settles_nothing(self):
        for asset in (gh('o/a', lic(None, 'unrecognised')), gh('o/a', lic('MIT'), status='unavailable')):
            changes, skipped = run(health({'ui_1': entry(asset)}), sheet(row('ui_1')), code=True)
            self.assertEqual(changes, [])
            self.assertTrue(skipped)

    def test_datasets_and_models_are_not_code(self):
        doc = health({'ui_1': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')), zen(5, lic('CC0-1.0')))})
        self.assertEqual(run(doc, sheet(row('ui_1')), code=True), ([], []))

    def test_spaces_and_zenodo_software_are_code(self):
        doc = health({'ui_1': entry(hf('spaces', 'o/s', lic('MIT')), zen(5, lic('MIT'), resource_type='software'))})
        changes, _ = run(doc, sheet(row('ui_1')), code=True)
        self.assertEqual(changes[0]['new'], 'MIT')

    def test_a_keep_note_pins_the_code_licence(self):
        changes, skipped = run(health({'ui_1': entry(gh('o/c', lic('MIT')))}), sheet(row('ui_1', code_license='GPL 3.0')),
                               notes=notes_at(2, CODE_LICENSE, 'Partner confirmed. [Keep]'), code=True)
        self.assertEqual(changes, [])
        self.assertEqual(skipped[0]['reason'], 'pinned with [Keep]')


class MainTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        # ui_79's Code License already says what its code declares, so only License cells change.
        self.grid = sheet(row('ui_79', code_license='GPL 3.0'), row('ui_80', license='CC0 1.0'))
        self.ws = FakeWorksheet(self.grid)
        self.doc = health({'ui_79': entry(gh('o/c', lic('GPL-3.0'))),
                           'ui_80': entry(hf('datasets', 'o/d', lic('CC-BY-4.0')))})

    def main(self, *flags, doc=None, env=None):
        path = os.path.join(self.dir.name, 'health.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(doc or self.doc, f)
        opener = lambda credentials: (self.ws, self.grid, [], [], [])
        with mock.patch.dict(os.environ, env or {}, clear=False), mock.patch('builtins.print'):
            return sc.main(['--health', path, *flags], open_sheet=opener, verify=lambda url: True, today=TODAY)

    def test_a_report_writes_nothing(self):
        self.assertEqual(self.main(), 0)
        self.assertEqual(self.ws.requests, [])

    def test_apply_writes_raw_values_with_their_notes_in_one_request(self):
        self.assertEqual(self.main('--apply'), 0)
        self.assertEqual(len(self.ws.requests), 1)
        cells = [r['updateCells'] for r in self.ws.requests[0]]
        self.assertEqual([(c['range']['sheetId'], c['range']['startRowIndex'], c['range']['startColumnIndex'])
                          for c in cells], [(7, 2, 4), (7, 3, 4)])
        values = [c['rows'][0]['values'][0] for c in cells]
        self.assertEqual([v['userEnteredValue'] for v in values],
                         [{'stringValue': 'GPL 3.0'}, {'stringValue': 'CC-BY 4.0'}])
        self.assertTrue(all(v['note'].startswith('[Source check]') for v in values))
        # Rich-text runs go too, or an old link could stay behind the new text.
        self.assertEqual({c['fields'] for c in cells}, {'userEnteredValue,note,textFormatRuns'})

    def test_rereads_the_cells_and_leaves_one_edited_meanwhile_for_next_week(self):
        self.ws.edited = {'E4': ('MIT', '')}
        summary = os.path.join(self.dir.name, 'summary.md')
        out = os.path.join(self.dir.name, 'github_output')
        self.assertEqual(self.main('--apply', '--summary', summary, env={'GITHUB_OUTPUT': out}), 0)
        self.assertEqual(self.ws.reads, [["'Portfolio''s sheet'!E3", "'Portfolio''s sheet'!E4"]])
        self.assertEqual([r['updateCells']['range']['startRowIndex'] for r in self.ws.requests[0]], [2])
        with open(summary, encoding='utf-8') as f:
            self.assertIn('ui_80, License: changed in the Sheet while this run was checking', f.read())
        with open(out, encoding='utf-8') as f:
            self.assertEqual(f.read(), 'written=1\n')

    def test_a_note_edited_meanwhile_also_holds_the_cell(self):
        self.ws.edited = {'E3': ('', 'Asked the partner, waiting.')}
        self.main('--apply')
        self.assertEqual([r['updateCells']['range']['startRowIndex'] for r in self.ws.requests[0]], [3])

    def test_more_changes_than_the_cap_write_nothing(self):
        self.assertEqual(self.main('--apply', '--max-changes', '1'), 3)
        self.assertEqual(self.ws.requests, [])

    def test_refuses_an_older_health_file(self):
        self.assertEqual(self.main('--apply', doc={'schema_version': 1, 'entries': {}}), 2)
        self.assertEqual(self.ws.requests, [])

    def test_tells_github_actions_how_many_cells_it_wrote(self):
        out = os.path.join(self.dir.name, 'github_output')
        self.main('--apply', env={'GITHUB_OUTPUT': out})
        with open(out, encoding='utf-8') as f:
            self.assertEqual(f.read(), 'written=2\n')

    def test_writes_a_summary_for_the_run(self):
        summary = os.path.join(self.dir.name, 'summary.md')
        self.main('--apply', '--summary', summary)
        with open(summary, encoding='utf-8') as f:
            text = f.read()
        self.assertIn('2 cells changed', text)
        self.assertIn('| ui_79 | License (E3) | (empty) | GPL 3.0 |', text)


class FakeResponse:
    def __init__(self, status, body=None):
        self.status_code, self.body = status, body

    def json(self):
        return self.body


class FakeSession:
    def __init__(self, responses):
        self.responses, self.urls = responses, []

    def get(self, url, **kwargs):
        self.urls.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


class VerifyLinkTests(unittest.TestCase):
    def test_a_doi_is_checked_at_the_doi_registry(self):
        api = 'https://doi.org/api/handles/10.5281/zenodo.15778395'
        self.assertTrue(sc.verify_link('https://doi.org/10.5281/zenodo.15778395',
                                       FakeSession({api: FakeResponse(200, {'responseCode': 1})})))
        self.assertFalse(sc.verify_link('https://doi.org/10.5281/zenodo.15778395',
                                        FakeSession({api: FakeResponse(404, {'responseCode': 100})})))

    def test_another_address_must_answer(self):
        url = 'https://github.com/o/s'
        self.assertTrue(sc.verify_link(url, FakeSession({url: FakeResponse(200)})))
        self.assertFalse(sc.verify_link(url, FakeSession({url: FakeResponse(404)})))
        self.assertFalse(sc.verify_link(url, FakeSession({url: sc.requests.ConnectionError('down')})))


if __name__ == '__main__':
    unittest.main()

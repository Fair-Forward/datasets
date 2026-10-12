"""validate_data.py's quality notes must not erase what people or other scripts wrote in a note."""
import sys
import unittest
from unittest import mock

with mock.patch.object(sys, 'argv', ['validate_data.py']):  # it parses its arguments on import
    import validate_data


class FakeSheet:
    def __init__(self, header, notes):
        self.header, self.notes, self.written = header, notes, None

    def row_values(self, row):
        return self.header

    def get_notes(self, default_empty_value=''):
        return self.notes

    def update_notes(self, notes):
        self.written = notes


def write(existing_note):
    # The first project is on row 3, after the header and the explanation row.
    sheet = FakeSheet(['Project ID', 'License'], [[''], [''], ['', existing_note]])
    with mock.patch.object(validate_data, 'get_gsheet_client', return_value=(None, None, sheet)), \
            mock.patch('builtins.print'):
        validate_data.write_notes_to_sheet({0: {validate_data.COL_LICENSE: 'New hint.'}}, 'creds.json')
    return sheet.written['B3']


class QualityNoteTests(unittest.TestCase):
    def test_a_second_run_keeps_a_persons_note_and_a_keep_pin(self):
        self.assertEqual(write('Agreed with the partner. [Keep]\n\n[Auto-check] Old hint.'),
                         'Agreed with the partner. [Keep]\n\n[Auto-check] New hint.')

    def test_keeps_the_record_of_a_source_correction(self):
        self.assertEqual(write('[Source check] 2026-10-12: Was "MIT".\n\n[Auto-check] Old hint.'),
                         '[Source check] 2026-10-12: Was "MIT".\n\n[Auto-check] New hint.')

    def test_a_first_run_still_appends_to_a_persons_note(self):
        self.assertEqual(write('Agreed with the partner.'), 'Agreed with the partner.\n\n[Auto-check] New hint.')


if __name__ == '__main__':
    unittest.main()

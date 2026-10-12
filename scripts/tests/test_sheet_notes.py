"""Tests for sheet_notes: one note per cell, shared by people and scripts."""
import unittest

import sheet_notes as sn


class MergeTests(unittest.TestCase):
    def test_appends_after_a_persons_note(self):
        self.assertEqual(sn.merge_note('Checked with the partner.', '[Auto-check]', '[Auto-check] Short.'),
                         'Checked with the partner.\n\n[Auto-check] Short.')

    def test_replaces_only_its_own_paragraph(self):
        existing = ('Checked with the partner. [Keep]\n\n[Auto-check] Old hint.\n\n'
                    '[Source check] 2026-10-12: Was "MIT".')
        self.assertEqual(sn.merge_note(existing, '[Auto-check]', '[Auto-check] New hint.'),
                         'Checked with the partner. [Keep]\n\n[Source check] 2026-10-12: Was "MIT".\n\n'
                         '[Auto-check] New hint.')

    def test_an_empty_paragraph_removes_its_own_and_keeps_the_rest(self):
        self.assertEqual(sn.merge_note('A person.\n\n[Auto-check] Old.', '[Auto-check]', ''), 'A person.')

    def test_starts_a_note_on_an_empty_cell(self):
        self.assertEqual(sn.merge_note('', '[Source check]', '[Source check] x'), '[Source check] x')
        self.assertEqual(sn.merge_note(None, '[Source check]', '[Source check] x'), '[Source check] x')


class PinTests(unittest.TestCase):
    def test_keep_in_square_brackets_pins_a_cell(self):
        self.assertTrue(sn.is_pinned('Partner asked for this. [Keep]'))
        self.assertTrue(sn.is_pinned('[keep]'))

    def test_other_notes_do_not_pin(self):
        self.assertFalse(sn.is_pinned(''))
        self.assertFalse(sn.is_pinned(None))
        self.assertFalse(sn.is_pinned('Keep an eye on this link.'))


if __name__ == '__main__':
    unittest.main()

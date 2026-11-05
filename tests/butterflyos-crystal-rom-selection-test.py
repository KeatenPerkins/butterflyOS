#!/usr/bin/env python3
"""Crystal event ROM qualification and ZIP routing; no real save writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-save-trade-sdl.py'
spec = importlib.util.spec_from_file_location('crystal_selection', SOURCE)
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


class CrystalSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        # Artificial bytes test container handling, not a bundled ROM.
        self.data = bytes(range(256)) * 4
        self.raw = root / 'Crystal.gbc'
        self.raw.write_bytes(self.data)
        self.zip = root / 'Crystal.zip'
        with zipfile.ZipFile(self.zip, 'w') as z:
            z.writestr('nested/Crystal.gbc', self.data)
        self.save = root / 'Crystal.srm'
        self.save.write_bytes(b'unchanged test save')
        self.expected = hashlib.sha256(self.data).hexdigest()

    def select(self, candidates):
        with patch.object(ui, '_rom_candidates', return_value=list(map(str, candidates))), \
             patch.object(ui, 'CRYSTAL_EVENT_ROM_SHA256', self.expected):
            return ui.crystal_event_rom(str(self.save))

    def test_raw_and_zip_qualify_by_identical_content(self):
        self.assertEqual(self.select([self.raw]), str(self.raw))
        self.assertEqual(self.select([self.zip]), str(self.zip))

    def test_bad_archive_does_not_hide_later_valid_rom(self):
        bad = Path(self.tmp.name) / 'broken.zip'
        bad.write_bytes(b'not a zip')
        self.assertEqual(self.select([bad, self.zip]), str(self.zip))

    def test_modified_rom_is_rejected(self):
        self.raw.write_bytes(self.data + b'modified')
        self.assertIsNone(self.select([self.raw]))

    def test_both_event_menus_pass_the_zip_to_the_helper(self):
        for workflow, payload, choices in (
            (ui.crystal_odd_egg_workflow, {'received': False}, [0]),
            (ui.crystal_celebi_workflow, {'stage': 'available'}, [0, None]),
        ):
            with self.subTest(workflow=workflow.__name__), \
                 patch.object(ui, 'generation_saves', return_value=[(str(self.save), 'KeatenC', 'Crystal', [])]), \
                 patch.object(ui, '_rom_candidates', return_value=[str(self.zip)]), \
                 patch.object(ui, 'CRYSTAL_EVENT_ROM_SHA256', self.expected), \
                 patch.object(ui, 'choose_list', side_effect=choices), \
                 patch.object(ui, 'notice'), \
                 patch.object(ui.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(payload), '')) as run, \
                 patch.object(ui, 'prepare_crystal_event') as prepare:
                workflow(Mock())
                command = run.call_args.args[0]
                self.assertEqual(command[command.index('--rom') + 1], str(self.zip))
                prepare.assert_not_called()
                self.assertEqual(self.save.read_bytes(), b'unchanged test save')


if __name__ == '__main__':
    unittest.main()

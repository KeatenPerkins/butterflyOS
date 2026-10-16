#!/usr/bin/env python3
"""ROM name-table validation and inspector enrichment regression tests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

SOURCES = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCES / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gb = load('butterflyos-gb-sprite-cache')
gba = load('butterflyos-gen3-sprite-cache')
ui = load('butterflyos-save-trade-sdl')


def entry(name):
    return bytes(0 if c == ' ' else ord(c) - ord('A') + 0xBB for c in name).ljust(13, b'\xff')


def table():
    return entry('POUND') + entry('KARATE CHOP') + entry('TEST') * 351 + entry('PSYCHO BOOST')


class MoveNames(unittest.TestCase):
    def test_item_table_validates_ids_and_ignores_unused_slots(self):
        header = bytearray(0xC0)
        header[0xAC:0xB0] = b'AXVE'
        rows = []
        for item_id in range(1, 349):
            name = 'MASTER BALL' if item_id == 1 else 'ULTRA BALL' if item_id == 2 else 'TEST'
            row = bytearray(44)
            row[:13] = entry(name)
            row[14:16] = item_id.to_bytes(2, 'little')
            rows.append(row)
        data = bytes(header) + b''.join(rows)
        self.assertEqual(len(gba.item_names(data)), 348)
        self.assertEqual(gba.item_names(data)['2'], 'ULTRA BALL')
        rows[10][14:16] = b'\xff\xff'
        with self.assertRaises(gba.CacheError):
            gba.item_names(bytes(header) + b''.join(rows))
        self.assertEqual(gba.decode_name(bytes((0x55,0x56,0x57,0x58,0x59,0xFF))), 'POKéBLOCK')

    def test_gameboy_zip_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'game.zip'
            data = bytes(0x8000)
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('nested/GAME.GBC', data)
                archive.writestr('readme.txt', 'notes')
            self.assertEqual(gb.read_rom(path), data)
            with zipfile.ZipFile(path, 'a') as archive:
                archive.writestr('other.gb', data)
            with self.assertRaises(gb.CacheError):
                gb.read_rom(path)
            path.write_bytes(b'broken zip')
            with self.assertRaises(gb.CacheError):
                gb.read_rom(path)

    def test_gameboy_zip_picker(self):
        for generation, folder in ((1, 'gb'), (2, 'gbc')):
            with self.subTest(generation=generation), \
                 patch.object(ui.os.path, 'isdir', return_value=True), \
                 patch.object(ui.os.path, 'isfile', return_value=True), \
                 patch.object(ui.os, 'listdir', return_value=['Pokemon.zip', 'notes.txt']):
                candidates = ui._rom_candidates(generation, '/storage/roms/' + folder + '/Pokemon.srm')
                self.assertIn('/storage/roms/' + folder + '/Pokemon.zip', candidates)
                self.assertTrue(all(path.endswith('.zip') for path in candidates))

    def test_fixed_width_table_and_decoy(self):
        result = gba.move_names(entry('POUND') + entry('DECOY') + table())
        self.assertEqual(len(result), 354)
        self.assertEqual(result['2'], 'KARATE CHOP')
        self.assertEqual(result['354'], 'PSYCHO BOOST')

    def test_reject_truncated_or_invalid_tables(self):
        for data in (b'', table()[:-13], table()[:26] + b'\x01' + table()[27:]):
            with self.subTest(size=len(data)), self.assertRaises(gba.CacheError):
                gba.move_names(data)

    def test_inspector_enriches_each_generation_and_preserves_unknown_ids(self):
        for generation in (1, 2, 3):
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as directory:
                names = {'format': 'butterflyos-gen3-rom-names' if generation == 3 else 'butterflyos-gb-rom-names',
                         'moves': {'10': 'SCRATCH', '29': 'HEADBUTT'}, 'items': {'200': 'LEFTOVERS'}}
                Path(directory, 'names.json').write_text(json.dumps(names))
                records = [{'species': 1, 'moves': [10, 29, 999, 0], 'held': 200}]

                class Frontend:
                    def draw_sprite_browser(self, title, cache_title, shown, index, sprite):
                        self.records = shown
                    def next_key(self):
                        return ui.KEY_CANCEL

                frontend = Frontend()
                with patch.object(ui, '_find_saves', return_value=['test.srm']), \
                     patch.object(ui, '_save_records', return_value=(generation, records)), \
                     patch.object(ui, 'ensure_sprite_cache', return_value=directory), \
                     patch.object(ui, '_cache_for_generation', return_value=(directory, 'Test')):
                    ui.sprite_browser(frontend)
                self.assertEqual(frontend.records[0]['move_labels'], ['SCRATCH', 'HEADBUTT', 'Move #999'])
                self.assertEqual(records[0]['moves'], [10, 29, 999, 0])
                self.assertEqual(records[0]['held_label'], 'LEFTOVERS')
                self.assertEqual(records[0]['held'], 200)


if __name__ == '__main__':
    unittest.main()

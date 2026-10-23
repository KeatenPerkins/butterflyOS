#!/usr/bin/env python3
"""Read-only encounter decoding and collection navigation regressions."""
import hashlib
import os
import ctypes
import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'
def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCES / (name + '.py'))
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj); return obj
locations = load('butterflyos-bdex-locations')
app = load('butterflyos-bdex-sdl')

class Tests(unittest.TestCase):
    def fixture(self):
        data = bytearray(0x8000)
        labels = ['Nothing'] * 12 + ['Route1', 'Route1', 'SeaRoutes']
        pointers = [0x4500] * 12 + [0x4510, 0x4510, 0x4540]
        struct.pack_into('<15H', data, 0x4100, *pointers)
        data[0x411e:0x4120] = b'\xff\xff'
        # Grass species 1 in all ten slots, levels 2 and 3; no Surfing.
        data[0x4510:0x4526] = bytes([25] + [2, 1] * 9 + [3, 1] + [0])
        # Surfing only, species 2.
        data[0x4540:0x4556] = bytes([0, 5] + [10, 2] * 10)
        return data, {'pokered': labels, 'pokeyellow': labels}

    def test_decode_group_aliases_levels_and_methods(self):
        data, tables = self.fixture()
        before = bytes(data)
        index = locations.extract(data, 'POKEMON RED', {1: 25, 2: 72}, tables)
        self.assertEqual(data, before)
        self.assertEqual(len(index['species']['25']), 1)
        row = index['species']['25'][0]
        self.assertEqual((row['min'], row['max'], row['weight']), (2, 3, 256))
        self.assertEqual(index['species']['72'][0]['method'], 'Surfing')
        self.assertEqual(index['species']['72'][0]['area'], 'Routes 19 / 20')
        text = locations.describe(index, 151)
        self.assertIn('does not mean', text)
        self.assertIn('Fishing', text)

    def test_reject_corruption_and_ambiguous_layout(self):
        data, tables = self.fixture()
        data[0x4512] = 255
        with self.assertRaisesRegex(ValueError, 'species'):
            locations.extract(data, 'POKEMON RED', {1: 25, 2: 72}, tables)
        data, tables = self.fixture()
        data[0x4200:0x4220] = data[0x4100:0x4120]
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            locations.extract(data, 'POKEMON RED', {1: 25, 2: 72}, tables)

    def test_species_without_stored_copy_can_open_locations(self):
        obj = app.Bdex.__new__(app.Bdex)
        obj.generation = 1
        obj.choose = Mock(side_effect=[1, None])
        obj.where_to_find, obj.copies = Mock(), Mock()
        obj.species_actions(151)
        obj.where_to_find.assert_called_once_with(151)
        obj.copies.assert_not_called()

    def test_window_exposure_requests_redraw_without_back(self):
        renderer = load('butterflyos-save-trade-sdl')
        front = renderer.SDLFrontEnd.__new__(renderer.SDLFrontEnd)
        front.sdl = Mock()
        events = []
        exposed = bytearray(64)
        struct.pack_into('<I', exposed, 0, 0x200)
        exposed[12] = 3
        events.append(bytes(exposed))
        enter = bytearray(64)
        struct.pack_into('<I', enter, 0, renderer.SDL_KEYDOWN)
        struct.pack_into('<i', enter, 20, renderer.KEY_RETURN)
        events.append(bytes(enter))
        def poll(buffer):
            if not events:
                return 0
            ctypes.memmove(buffer, events.pop(0), 64)
            return 1
        front.sdl.SDL_PollEvent.side_effect = poll
        self.assertEqual(front.next_key(), renderer.KEY_REDRAW)
        self.assertNotEqual(renderer.KEY_REDRAW, renderer.KEY_ESCAPE)
        self.assertEqual(front.next_key(), renderer.KEY_RETURN)
        self.assertIsNone(front.next_key())

    def test_tool_pad_override_is_local_and_preserves_external_pads(self):
        renderer = load('butterflyos-save-trade-sdl')
        external = 'external-guid,external,a:b0,b:b1,'
        with patch.dict(os.environ, {'SDL_GAMECONTROLLERCONFIG': external}):
            before = os.environ.copy()
            with patch.object(renderer.subprocess, 'run'), \
                    patch.object(renderer.subprocess, 'Popen') as launch:
                renderer.start_controller()
            mappings = launch.call_args.kwargs['env']['SDL_GAMECONTROLLERCONFIG'].splitlines()
            self.assertEqual(mappings[0], external)
            self.assertEqual(len(mappings), 3)
            self.assertTrue(all(',a:b1,b:b0,' in row for row in mappings[1:]))
            self.assertEqual(dict(os.environ), before)

    def test_other_generations_keep_existing_navigation(self):
        obj = app.Bdex.__new__(app.Bdex)
        obj.generation = 2
        obj.copies = Mock()
        obj.species_actions(151)
        obj.copies.assert_called_once_with(151)

    def test_private_retail_roms_when_available(self):
        files = list((ROOT / '.cache/bdex-locations').glob('*.zip'))
        if len(files) != 3:
            self.skipTest('Optional private original ROM fixtures')
        gb, gifts = load('butterflyos-gb-sprite-cache'), load('butterflyos-gen1-gift')
        results = {}
        for path in files:
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            index = locations.qualified_index(path, gb, gifts)
            results[index['game']] = index
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
            self.assertGreater(len(index['species']), 60)
            self.assertTrue(all(1 <= int(dex) <= 151 for dex in index['species']))
        self.assertIn('25', results['POKEMON RED']['species'])
        self.assertNotIn('25', results['POKEMON YELLOW']['species'])
        # Vulpix is a Blue version exclusive.
        self.assertIn('37', results['POKEMON BLUE']['species'])
        self.assertNotIn('37', results['POKEMON RED']['species'])

if __name__ == '__main__':
    unittest.main()

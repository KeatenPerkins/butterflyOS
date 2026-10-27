#!/usr/bin/env python3
"""Nested ROM discovery on both cards; shared Blink/Bslap behavior stays separate."""
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

SOURCES = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCES / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


app = load('butterflyos-bdex-sdl')
blink = load('butterflyos-save-trade-sdl')


class DiscoveryTests(unittest.TestCase):
    def bdex(self):
        obj = app.Bdex.__new__(app.Bdex)
        obj.blink = SimpleNamespace(_game_family=blink._game_family,
                                    _rom_candidates=Mock(side_effect=AssertionError('Flat picker must not be used')))
        return obj

    def test_all_generations_find_deep_raw_and_zip_roms_on_both_cards(self):
        for gen, folder, extension in ((1, 'gb', '.gb'), (2, 'gbc', '.gbc'), (3, 'gba', '.gba')):
            with self.subTest(generation=gen), tempfile.TemporaryDirectory() as directory:
                roots = [Path(directory) / 'os', Path(directory) / 'second']
                data = bytearray(0x8000)
                data[0xAC:0xB0] = b'BPEE'
                raw = roots[0] / folder / 'Pokemon' / 'English' / ('Emerald' + extension.upper())
                raw.parent.mkdir(parents=True)
                raw.write_bytes(data)
                archive = roots[1] / folder / 'Collection' / 'Gen' / 'nested.zip'
                archive.parent.mkdir(parents=True)
                with zipfile.ZipFile(archive, 'w') as zipped:
                    zipped.writestr('inside/game' + extension, data)
                (raw.parent / 'readme.txt').write_text('not a ROM')
                before = hashlib.sha256(raw.read_bytes()).hexdigest()
                obj = self.bdex()
                self.assertEqual(set(obj.rom_candidates(gen, roots=roots)), {str(raw), str(archive)})
                self.assertEqual(before, hashlib.sha256(raw.read_bytes()).hexdigest())
                obj.blink._rom_candidates.assert_not_called()

    def test_save_matching_priority_is_preserved_across_nested_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for game in ('Red', 'Blue'):
                rom = root / 'gb' / game / 'nested' / (game + '.gb')
                rom.parent.mkdir(parents=True)
                rom.write_bytes(b'fixture')
            obj = self.bdex()
            found = obj.rom_candidates(1, '/other/Blue.srm', roots=[root])
            self.assertEqual(found, [str(root / 'gb/Blue/nested/Blue.gb')])
            found = obj.rom_candidates(1, '/other/Pokemon Red - Player.srm', roots=[root])
            self.assertEqual(found, [str(root / 'gb/Red/nested/Red.gb')])

    def test_alias_roots_file_links_and_directory_loops_do_not_duplicate_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'os'
            rom = root / 'gb' / 'one' / 'two' / 'Red.gb'
            rom.parent.mkdir(parents=True)
            rom.write_bytes(b'fixture')
            (rom.parent / 'loop').symlink_to(root / 'gb', target_is_directory=True)
            (rom.parent / 'same.gb').symlink_to(rom)
            alias = Path(directory) / 'alias'
            alias.symlink_to(root, target_is_directory=True)
            found = self.bdex().rom_candidates(1, roots=[root, alias])
            self.assertEqual(len(found), 1)
            self.assertEqual(Path(found[0]).resolve(), rom)

    def test_gen3_still_rejects_unrelated_invalid_and_unsupported_language_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / 'gba' / 'nested'
            nested.mkdir(parents=True)
            for name, code in [('Emerald.gba', b'BPEE'), ('Unrelated.gba', b'ABCD'), ('Spanish.gba', b'BPES')]:
                data = bytearray(0xC0)
                data[0xAC:0xB0] = code
                (nested / name).write_bytes(data)
            (nested / 'bad.zip').write_bytes(b'invalid ZIP')
            found = self.bdex().rom_candidates(3, roots=[root, root / 'missing'])
            self.assertEqual(found, [str(nested / 'Emerald.gba')])

    def test_cache_and_where_to_find_both_use_bdex_recursive_picker(self):
        data = b'fake-qualified-ROM'
        profiles = SimpleNamespace(SUPPORTED_ROMS={hashlib.sha256(data).hexdigest(): 'POKEMON RED'})
        reader = SimpleNamespace(read_rom=lambda path: data, CacheError=RuntimeError)
        for method in ('prepare_cache', 'where_to_find'):
            with self.subTest(method=method):
                obj = self.bdex()
                obj.generation = 1
                obj.rom_candidates = Mock(return_value=['/nested/Red.gb'])
                obj.choose = Mock(return_value=None)
                obj.ui = Mock()
                def module(name, path):
                    return profiles if 'gift' in str(path) else reader
                with patch.object(app.engine, 'load_module', side_effect=module):
                    if method == 'prepare_cache':
                        obj.prepare_cache('/nested/Red.srm')
                        obj.rom_candidates.assert_called_once_with(1, '/nested/Red.srm')
                    else:
                        obj.where_to_find(65)
                        obj.rom_candidates.assert_called_once_with(1)
                obj.choose.assert_called_once()
                obj.blink._rom_candidates.assert_not_called()


if __name__ == '__main__':
    unittest.main()

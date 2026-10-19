#!/usr/bin/env python3
"""Bdex safety regression. Private fixtures are optional; originals are read only.

python3 tests/butterflyos-bdex-test.py
python3 tests/butterflyos-bdex-test.py --helper HELPER --saves SAVE_ROOT --roms ROM_ROOT
"""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

SOURCES = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

b = load('bdex_test', SOURCES / 'butterflyos-bdex.py')
OPTIONS = None


def bundle(game='red', source='card1/save.srm', slot=0, data=b'private snapshot', native=b'native record'):
    record = {'key': 'box:0:%d' % slot, 'dex': 1, 'species': 153, 'source_key': source + ':' + str(slot),
              'fingerprint': b.sha(native), 'name': 'TEST', 'source_path': source,
              'game': game, 'kind': 'box', 'box': 0, 'slot': slot, 'level': 5, 'ot': 'TESTER'}
    return {'data': data, 'digest': b.sha(data), 'records': [record],
            'names': {str(n): 'Species %d' % n for n in range(1, 152)},
            'internal': {n: n for n in range(1, 152)}, 'game': game, 'trainer': 'TESTER'}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bdex-test-')
        self.root = Path(self.temp.name)
        self.store = b.Store(self.root)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_refresh_reconnects_exact_rom_without_changing_pokemon(self):
        value = bundle(game='blue')
        value['records'][0].update(rom_digest='blue-content', cache='/old/zip-cache')
        self.store.import_records(value, value['records'])
        other = bundle(game='red', slot=1, native=b'other')
        other['records'][0].update(rom_digest='red-content', cache='/old/red-cache')
        self.store.import_records(other, other['records'])
        self.store.trash(1)
        before = self.store.entry(1)
        snapshot = self.store.snapshot(1)
        with patch.object(b, 'cache_info', return_value={'generation': 1, 'game': 'blue', 'rom_digest': 'blue-content'}):
            self.assertEqual((1, 1), self.store.reconnect_cache('/new/raw-cache'))
            self.assertEqual((1, 0), self.store.reconnect_cache('/new/raw-cache'))
        after = self.store.entry(1)
        self.assertEqual(after['metadata'].pop('cache'), '/new/raw-cache')
        before['metadata'].pop('cache')
        self.assertEqual(before, after)
        self.assertEqual(snapshot, self.store.snapshot(1))
        self.assertEqual(self.store.entry(2)['metadata']['cache'], '/old/red-cache')
        self.assertTrue(list((self.root / 'backups').glob('auto-*.sqlite3')))

    def test_refresh_rejects_wrong_generation_and_same_game_different_rom(self):
        value = bundle(game='blue')
        value['records'][0].update(rom_digest='original-blue', cache='/old/cache')
        self.store.import_records(value, value['records'])
        with patch.object(b, 'cache_info', return_value={'generation': 2, 'game': 'blue', 'rom_digest': 'original-blue'}):
            with self.assertRaises(b.BdexError): self.store.reconnect_cache('/other-generation')
        with patch.object(b, 'cache_info', return_value={'generation': 1, 'game': 'blue', 'rom_digest': 'different-revision'}):
            self.assertEqual((0, 0), self.store.reconnect_cache('/other-revision'))
        self.assertEqual('/old/cache', self.store.entry(1)['metadata']['cache'])

    def test_exact_repeats_are_always_skipped(self):
        value = bundle()
        self.assertEqual(self.store.import_records(value, value['records']), 1)
        self.assertEqual(self.store.import_records(value, value['records']), 0)
        self.assertEqual(self.store.import_records(value, value['records']), 0)
        self.assertEqual(self.store.counts(), {1: 1})
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0], 1)

    def test_identical_records_across_slots_games_and_cards_are_skipped(self):
        for value in (bundle(), bundle(slot=1), bundle(game='blue', source='card1/blue.srm'), bundle(source='card2/save.srm')):
            self.store.import_records(value, value['records'])
        self.assertEqual(self.store.counts(), {1: 1})
        self.assertEqual(self.store.counts(game='blue'), {})
        self.assertEqual(len(self.store.entries(1, game='red')), 1)

    def test_changed_record_creates_a_new_version(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        value['records'][0]['fingerprint'] = b.sha(b'new native record')
        self.assertEqual(self.store.import_records(value, value['records']), 1)
        self.assertEqual(self.store.counts(), {1: 2})

    def test_exact_duplicates_within_one_import_are_skipped(self):
        value = bundle()
        clone = dict(value['records'][0], key='box:0:1', slot=1, source_key='different slot')
        value['records'].append(clone)
        self.assertEqual(self.store.import_records(value, value['records']), 1)

    def test_different_native_records_of_same_species_are_kept(self):
        for value in (bundle(), bundle(game='blue', native=b'different OT or stats')):
            self.assertEqual(self.store.import_records(value, value['records']), 1)
        self.assertEqual(self.store.counts(), {1: 2})

    def test_trashed_record_also_blocks_exact_duplicates(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        self.store.trash(1)
        other = bundle(source='another card/save.srm')
        self.assertEqual(self.store.import_records(other, other['records']), 0)
        self.assertEqual(len(self.store.entries(trash=True)), 1)

    def test_database_constraint_blocks_duplicate_inserts(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        with self.assertRaises(sqlite3.IntegrityError), self.store.connection:
            self.store.connection.execute('INSERT INTO pokemon(dex,snapshot,source_key,fingerprint,game,metadata,imported) '
                'SELECT dex,snapshot,source_key,fingerprint,game,metadata,imported FROM pokemon')
        self.assertEqual(self.store.counts(), {1: 1})

    def test_legacy_duplicates_are_merged_with_history_and_backup(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        self.store.trash(1)
        with self.store.connection:
            self.store.connection.execute('DROP INDEX pokemon_native_unique')
            self.store.connection.execute('INSERT INTO pokemon(dex,snapshot,source_key,fingerprint,game,metadata,imported) '
                'SELECT dex,snapshot,source_key,fingerprint,game,metadata,imported+1 FROM pokemon')
            self.store.connection.execute("INSERT INTO history(pokemon,action,detail,created) VALUES (2,'import','second import',1)")
        self.store.close()
        self.store = b.Store(self.root)
        self.assertEqual(self.store.duplicates_removed, 1)
        self.assertEqual([row['id'] for row in self.store.entries()], [2])
        self.assertEqual(len(self.store.history(2)), 3)
        backup = sorted((self.root / 'backups').glob('manual-*.sqlite3'))[-1]
        with sqlite3.connect(backup) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM pokemon').fetchone()[0], 2)

    def test_legacy_cleanup_does_not_run_if_backup_fails(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        with self.store.connection:
            self.store.connection.execute('DROP INDEX pokemon_native_unique')
            self.store.connection.execute('INSERT INTO pokemon(dex,snapshot,source_key,fingerprint,game,metadata,imported) '
                'SELECT dex,snapshot,source_key,fingerprint,game,metadata,imported FROM pokemon')
        self.store.close()
        with patch.object(b.Store, 'backup', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                b.Store(self.root)
        with sqlite3.connect(self.root / 'collection.sqlite3') as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM pokemon').fetchone()[0], 2)
        self.store = b.Store(self.root)

    def test_trash_restore_preserves_record_and_history(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        first = self.store.entry(1)
        self.store.trash(1)
        self.assertEqual(self.store.counts(), {})
        self.assertEqual(len(self.store.entries(trash=True)), 1)
        self.assertEqual(self.store.snapshot(1), value['data'])
        self.store.trash(1, restore=True)
        self.assertEqual(self.store.entry(1)['metadata'], first['metadata'])
        self.assertEqual(self.store.counts(), {1: 1})
        self.assertEqual([x['action'] for x in self.store.history(1)], ['import', 'trash', 'restore-trash'])

    def test_backup_failure_prevents_collection_changes(self):
        value = bundle()
        with patch.object(self.store, 'backup', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.store.import_records(value, value['records'])
        self.assertEqual(self.store.counts(), {})

    def test_permanent_delete_requires_trash(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        with self.assertRaises(b.BdexError):
            self.store.delete(1)
        self.assertEqual(self.store.counts(), {1: 1})

    def test_delete_one_copy_keeps_shared_snapshot_and_other_copy(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        other = bundle(slot=1, native=b'different Pokemon')
        self.store.import_records(other, other['records'])
        self.store.trash(1)
        self.store.delete(1)
        with self.assertRaises(b.BdexError):
            self.store.entry(1)
        self.assertEqual(self.store.history(1), [])
        self.assertEqual(self.store.counts(), {1: 1})
        self.assertEqual(self.store.snapshot(2), value['data'])
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0], 1)

    def test_delete_last_copy_removes_unused_snapshot(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        self.store.trash(1)
        self.store.delete(1)
        self.assertEqual(self.store.entries(trash=True), [])
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0], 0)
        self.assertEqual(self.store.connection.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_delete_backup_failure_keeps_trashed_copy(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        self.store.trash(1)
        with patch.object(self.store, 'backup', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.store.delete(1)
        self.assertEqual(len(self.store.entries(trash=True)), 1)
        self.assertEqual(self.store.snapshot(1), value['data'])

    def test_pre_delete_backup_can_recover_collection(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        self.store.trash(1)
        self.store.delete(1)
        backup = sorted((self.root / 'backups').glob('auto-*.sqlite3'))[-1]
        self.store.close()
        b.recover_database(self.root, backup)
        self.store = b.Store(self.root)
        self.assertEqual(len(self.store.entries(trash=True)), 1)
        self.assertEqual(self.store.snapshot(1), value['data'])

    def test_database_backups_and_recovery_keep_replaced_database(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        manual = self.store.backup(manual=True)
        for number in range(5):
            other = bundle(native=('different %d' % number).encode())
            self.store.import_records(other, other['records'])
        self.assertEqual(len(list((self.root / 'backups').glob('auto-*.sqlite3'))), 3)
        self.assertTrue(manual.exists())
        self.store.close()
        b.recover_database(self.root, manual)
        self.store = b.Store(self.root)
        self.assertEqual(self.store.counts(), {1: 1})
        self.assertTrue(list((self.root / 'replaced-databases').glob('*.sqlite3')))

    def test_corrupt_database_recovery(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        backup = self.store.backup(manual=True)
        self.store.close()
        (self.root / 'collection.sqlite3').write_bytes(b'broken database')
        with self.assertRaises(sqlite3.DatabaseError):
            b.Store(self.root)
        b.recover_database(self.root, backup)
        self.store = b.Store(self.root)
        self.assertEqual(self.store.counts(), {1: 1})

    def test_factory_reset_preserves_collection_data(self):
        import shlex
        import subprocess
        storage = self.root / 'storage'
        for relative in ('bdex/collection.sqlite3', 'bdex/backups/manual.sqlite3',
                         'roms/gb/game.srm', 'games-external/roms/gb/game.srm', '.config/settings'):
            file = storage / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('fixture')
        script = (SOURCES.parents[2] / 'rocknix/sources/scripts/factoryreset').read_text()
        line = next(line.strip() for line in script.splitlines() if line.strip().startswith('find /storage -mindepth'))
        command = [argument.replace('/storage', str(storage)) for argument in shlex.split(line.split(' 2>', 1)[0])]
        subprocess.run(command, check=True)
        self.assertTrue((storage / 'bdex/collection.sqlite3').exists())
        self.assertTrue((storage / 'bdex/backups/manual.sqlite3').exists())
        self.assertTrue((storage / 'roms/gb/game.srm').exists())
        self.assertFalse((storage / '.config/settings').exists())

    def test_second_writer_is_rejected(self):
        with self.assertRaises(b.BdexError):
            b.Store(self.root)

    def test_bad_snapshot_or_selection_is_rejected(self):
        value = bundle()
        altered = copy.deepcopy(value['records'])
        altered[0]['dex'] = 5
        with self.assertRaises(b.BdexError):
            self.store.import_records(value, altered)
        value['data'] = b'changed snapshot'
        with self.assertRaises(b.BdexError):
            self.store.import_records(value, value['records'])
        self.assertEqual(self.store.counts(), {})

    def test_saved_snapshot_integrity_is_rechecked(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        with self.store.connection:
            self.store.connection.execute('UPDATE snapshots SET data=?', (b'corrupt',))
        with self.assertRaises(b.BdexError):
            self.store.snapshot(1)

    def test_corrupt_snapshot_does_not_replace_good_database_backups(self):
        value = bundle()
        self.store.import_records(value, value['records'])
        good = self.store.backup(manual=True)
        with self.store.connection:
            self.store.connection.execute('UPDATE snapshots SET data=?', (b'corrupt',))
        with self.assertRaises(b.BdexError):
            self.store.backup()
        b.database_valid(good)
        self.assertEqual(len(list((self.root / 'backups').glob('auto-*.sqlite3'))), 1)


class ImportFlowTests(unittest.TestCase):
    def setUp(self):
        from types import SimpleNamespace
        self.module = load('bdex_ui_test', SOURCES / 'butterflyos-bdex-sdl.py')
        self.temp = tempfile.TemporaryDirectory(prefix='bdex-ui-test-')
        self.store = self.module.engine.Store(Path(self.temp.name))
        self.app = self.module.Bdex(SimpleNamespace(link=object(), frontend=object()), self.store)
        self.app.ui = SimpleNamespace(message=lambda *args: None)
        self.value = bundle()
        party = copy.deepcopy(self.value['records'][0])
        party.update(key='party:-1:0', source_key='source:party:0', kind='party', box=-1, fingerprint=b.sha(b'party record'))
        self.value['records'].append(party)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_cancelled_import_keeps_collection_empty(self):
        with patch.object(self.app, 'pick_save', return_value=('save.srm', '', '', [])), \
             patch.object(self.app, 'matching_cache', return_value='cache'), \
             patch.object(self.module.engine, 'import_bundle', return_value=self.value), \
             patch.object(self.app, 'choose', return_value=None):
            self.app.import_workflow()
        self.assertEqual(self.store.counts(), {})

    def test_cancelled_permanent_delete_keeps_trashed_copy(self):
        self.store.import_records(self.value, [self.value['records'][0]])
        self.store.trash(1)
        with patch.object(self.app, 'choose', side_effect=[8, 0, 2, None, None]), \
             patch.object(self.app, 'confirm', return_value=False):
            self.app.options()
        self.assertEqual(len(self.store.entries(trash=True)), 1)

    def test_confirmed_permanent_delete_removes_only_selected_copy(self):
        self.store.import_records(self.value, [self.value['records'][0]])
        self.store.import_records(self.value, [self.value['records'][1]])
        self.store.trash(1)
        with patch.object(self.app, 'choose', side_effect=[8, 0, 2, None]), \
             patch.object(self.app, 'confirm', return_value=True):
            self.app.options()
        self.assertEqual(self.store.entries(trash=True), [])
        self.assertEqual(self.store.counts(), {1: 1})

    def test_recovery_menu_ignores_pending_and_unrelated_files(self):
        directory = self.store.root / 'backups'
        directory.mkdir()
        for name in ('manual-2.sqlite3', 'auto-3.sqlite3', 'manual-old.sqlite3', '.pending-auto-9.sqlite3'):
            (directory / name).write_text('fixture')
        self.assertEqual([path.name for path in self.module.database_backups(self.store.root)],
                         ['auto-3.sqlite3', 'manual-2.sqlite3'])

    def test_forward_export_ui_routes_without_switching_collection(self):
        from types import SimpleNamespace
        self.app.blink = SimpleNamespace(choose_copy_destination=lambda *_: (13, 0))
        with patch.object(self.app, 'choose', return_value=1), \
             patch.object(self.app, 'pick_save', return_value=('gold.srm', '', '', [])) as picker, \
             patch.object(self.app, 'confirm', return_value=True), \
             patch.object(self.module.engine, 'export_copy', return_value=Path('backup.srm')) as exporter:
            self.app.export_workflow(1)
        picker.assert_called_once_with('GEN 2 EXPORT DESTINATION', 2)
        self.assertEqual(exporter.call_args.kwargs['destination_generation'], 2)
        self.assertIs(self.app.store, self.store)
        self.assertEqual(self.app.generation, 1)

    def test_forward_export_cancel_keeps_saves_unchanged(self):
        from types import SimpleNamespace
        self.app.blink = SimpleNamespace(choose_copy_destination=lambda *_: (13, 0))
        with patch.object(self.app, 'choose', return_value=1), \
             patch.object(self.app, 'pick_save', return_value=('gold.srm', '', '', [])), \
             patch.object(self.app, 'confirm', return_value=False), \
             patch.object(self.module.engine, 'export_copy') as exporter:
            self.app.export_workflow(1)
        exporter.assert_not_called()

    def test_marking_party_does_not_import_unmarked_box(self):
        with patch.object(self.app, 'pick_save', return_value=('save.srm', '', '', [])), \
             patch.object(self.app, 'matching_cache', return_value='cache'), \
             patch.object(self.module.engine, 'import_bundle', return_value=self.value), \
             patch.object(self.app, 'choose', side_effect=[1, 1, 0, None, 0, 0]), \
             patch.object(self.app, 'confirm', return_value=True):
            self.app.import_workflow()
        rows = self.store.entries()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['metadata']['kind'], 'party')


class NativeFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OPTIONS.helper:
            raise unittest.SkipTest('Private native fixtures not requested')
        cls.native = b.Native(OPTIONS.helper)
        cls.gb = load('bdex_cache_test', SOURCES / 'butterflyos-gb-sprite-cache.py')
        cls.temp = tempfile.TemporaryDirectory(prefix='bdex-native-test-')
        cls.root = Path(cls.temp.name)
        cls.saves = {}
        cls.caches = {}
        for game in ('Red', 'Blue', 'Yellow'):
            cls.saves[game.lower()] = next((Path(OPTIONS.saves) / 'gb').glob('*' + game + '*srm'))
            rom = next(Path(OPTIONS.roms).glob('*' + game + '*.gb'))
            cls.caches[game.lower()] = cls.gb.cache_rom(rom, cls.root / 'cache')
        cls.hashes = {path: b.sha(path.read_bytes()) for path in cls.saves.values()}

    @classmethod
    def tearDownClass(cls):
        for path, digest in cls.hashes.items():
            assert b.sha(path.read_bytes()) == digest, 'Original fixture changed!'
        cls.temp.cleanup()

    def test_all_three_roms_have_151_shared_species_names(self):
        for cache in self.caches.values():
            info = b.cache_info(cache)
            self.assertEqual(len(info['names']), 151)
            self.assertEqual(info['names']['1'], 'BULBASAUR')
            self.assertEqual(info['types']['1'], [22, 3])
            self.assertEqual(info['types']['81'], [23])  # Gen 1 has no Steel type.
            self.assertEqual(info['type_names']['22'], 'GRASS')
            self.assertEqual(info['type_names']['3'], 'POISON')
            self.assertEqual(info['type_names']['23'], 'ELECTRIC')
            self.assertEqual(info['names']['151'], 'MEW')

    def test_zipped_rom_reuses_the_same_native_records(self):
        import zipfile
        rom = next(Path(OPTIONS.roms).glob('*Red*.gb'))
        archive = self.root / 'renamed-source.zip'
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.write(rom, 'renamed-game.gb')
        cache = self.gb.cache_rom(archive, self.root / 'zip-cache')
        info = b.cache_info(cache)
        self.assertEqual(info['game'], 'red')
        raw = b.import_bundle(self.native, self.saves['red'], self.caches['red'])
        compressed = b.import_bundle(self.native, self.saves['red'], cache)
        self.assertEqual([r['fingerprint'] for r in raw['records']], [r['fingerprint'] for r in compressed['records']])
        self.assertEqual([r['source_key'] for r in raw['records']], [r['source_key'] for r in compressed['records']])

    def test_mismatched_rom_family_is_rejected(self):
        with self.assertRaises(b.BdexError):
            b.import_bundle(self.native, self.saves['red'], self.caches['yellow'])

    def test_party_and_box_export_matrix_preserves_native_records(self):
        for source_game, source in self.saves.items():
            value = b.import_bundle(self.native, source, self.caches[source_game])
            for kind in ('party', 'box'):
                record = next(r for r in value['records'] if r['kind'] == kind)
                with tempfile.TemporaryDirectory(dir=self.root) as temporary:
                    store = b.Store(Path(temporary) / 'bank')
                    try:
                        self.assertEqual(store.import_records(value, [record]), 1)
                        for destination_game, destination in self.saves.items():
                            target = Path(temporary) / (destination_game + '.srm')
                            target.write_bytes(destination.read_bytes())
                            fields, before = self.native.inspect(target)
                            box = next(n for n in range(12) if sum(r['kind'] == 'box' and r['box'] == n for r in before) < 20)
                            slot = sum(r['kind'] == 'box' and r['box'] == box for r in before)
                            original = target.read_bytes()
                            backup = b.export_copy(store, self.native, 1, target, box, slot)
                            self.assertEqual(backup.read_bytes(), original)
                            self.assertEqual(store.counts(), {record['dex']: 1})
                            self.assertEqual(store.entry(1)['metadata'], record)
                            _, after = self.native.inspect(target)
                            copied = next(r for r in after if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
                            self.assertEqual(copied['fingerprint'], record['fingerprint'])
                            self.assertGreater(record['level'], 0)
                    finally:
                        store.close()

    def test_export_uses_snapshot_after_original_source_is_removed(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            source = Path(temporary) / 'source.srm'
            source.write_bytes(self.saves['red'].read_bytes())
            value = b.import_bundle(self.native, source, self.caches['red'])
            store = b.Store(Path(temporary) / 'bank')
            try:
                store.import_records(value, [value['records'][0]])
                source.unlink()
                target = Path(temporary) / 'target.srm'
                target.write_bytes(self.saves['blue'].read_bytes())
                _, records = self.native.inspect(target)
                box = next(n for n in range(12) if sum(r['kind'] == 'box' and r['box'] == n for r in records) < 20)
                slot = sum(r['kind'] == 'box' and r['box'] == box for r in records)
                b.export_copy(store, self.native, 1, target, box, slot)
                self.assertEqual(store.counts(), {value['records'][0]['dex']: 1})
            finally:
                store.close()

    def test_forward_party_box_matrix_and_snapshot_independence(self):
        gifts = load('bdex_forward_gifts', SOURCES / 'butterflyos-gen2-gift.py')
        for source_game in self.saves:
            for kind in ('party', 'box'):
                with tempfile.TemporaryDirectory(dir=self.root) as temporary:
                    root = Path(temporary)
                    source = root / 'source.srm'
                    source.write_bytes(self.saves[source_game].read_bytes())
                    value = b.import_bundle(self.native, source, self.caches[source_game])
                    record = next(r for r in value['records'] if r['kind'] == kind)
                    store = b.Store(root / 'bank')
                    try:
                        store.import_records(value, [record])
                        source.unlink()
                        for game in ('Gold', 'Silver', 'Crystal'):
                            with self.subTest(source=source_game, kind=kind, destination=game):
                                target = root / (game + '.srm')
                                original = next((Path(OPTIONS.saves) / 'gbc').glob('*' + game + '*.srm')).read_bytes()
                                if game == 'Crystal':
                                    original += bytes(range(48))
                                target.write_bytes(original)
                                _, before = self.native.inspect(target, 2)
                                box = 13
                                slot = sum(r['kind'] == 'box' and r['box'] == box for r in before)
                                backup = b.export_copy(store, self.native, 1, target, box, slot, destination_generation=2)
                                self.assertEqual(backup.read_bytes(), original)
                                _, after = self.native.inspect(target, 2)
                                added = next(r for r in after if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
                                self.assertEqual(bytes.fromhex(added['raw']), b.converted_gen2_raw(record, record['dex']))
                                for field in ('name', 'ot', 'ot_id', 'level', 'experience', 'moves', 'pp', 'pp_ups', 'dvs', 'stat_exp'):
                                    self.assertEqual(added[field], record[field], field)
                                self.assertFalse(added['egg'])
                                self.assertEqual((added['friendship'], added['pokerus'], added['caught_data']), (70, 0, 0))
                                self.assertEqual(store.entry(1)['metadata'], record)
                                self.assertEqual(store.counts(), {record['dex']: 1})
                                raw = target.read_bytes()
                                current, active, owned, seen, *_ = gifts.layout(game == 'Crystal')
                                bank = gifts.box_at(box)
                                self.assertEqual(raw[active:active + gifts.BOX_SIZE], raw[bank:bank + gifts.BOX_SIZE])
                                for base in (owned, seen):
                                    self.assertTrue(raw[base + (record['dex'] - 1) // 8] & (1 << ((record['dex'] - 1) % 8)))
                                if game == 'Crystal':
                                    self.assertEqual(raw[32768:], original[32768:])
                                gifts.validate_save(raw, game == 'Crystal')
                                receipt = json.loads(store.history(1)[-1]['detail'])
                                self.assertEqual((receipt['source_generation'], receipt['destination_generation']), (1, 2))
                    finally:
                        store.close()

    def test_forward_all_catch_rate_item_rules(self):
        destination = next((Path(OPTIONS.saves) / 'gbc').glob('*Gold*.srm'))
        _, before = self.native.inspect(destination, 2)
        slot = sum(r['kind'] == 'box' and r['box'] == 13 for r in before)
        _, records = self.native.inspect(self.saves['red'])
        record = next(r for r in records if r['kind'] == 'party' and r['slot'] == 0)
        info = b.cache_info(self.caches['red'])
        national = info['mapping'][record['species']]
        overrides = {0x19: 0x92, 0x2d: 0x53, 0x32: 0xae,
                     **{v: 0xad for v in (0x5a, 0x64, 0x78, 0x87, 0xbe, 0xc3, 0xdc, 0xfa)}}
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            source, output = Path(temporary) / 'source.srm', Path(temporary) / 'output.srm'
            for catch_rate in range(256):
                data = bytearray(self.saves['red'].read_bytes())
                data[0x2f2c + 8 + 7] = catch_rate
                data[0x3523] = (255 - sum(data[0x2598:0x3523])) & 255
                source.write_bytes(data)
                self.native.run('bdex-export-gen1-to-gen2', source=source, source_kind='party',
                    source_box=0, source_slot=0, destination=destination, destination_box=13,
                    destination_slot=slot, national_species=national, output_destination=output)
                _, after = self.native.inspect(output, 2)
                added = next(r for r in after if r['kind'] == 'box' and r['box'] == 13 and r['slot'] == slot)
                self.assertEqual(added['held_item'], overrides.get(catch_rate, catch_rate))
                self.assertEqual(b.time_capsule_item(catch_rate), added['held_item'])
                output.unlink()

    def test_forward_rejects_alias_occupied_slot_and_conflicting_destination(self):
        value = b.import_bundle(self.native, self.saves['red'], self.caches['red'])
        record = value['records'][0]
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            root = Path(temporary)
            store = b.Store(root / 'bank')
            try:
                store.import_records(value, [record])
                target = root / 'target.srm'
                original = next((Path(OPTIONS.saves) / 'gbc').glob('*Gold*.srm')).read_bytes()
                target.write_bytes(original)
                with self.assertRaises(b.BdexError):
                    self.native.run('bdex-export-gen1-to-gen2', source=self.saves['red'],
                        source_kind=record['kind'], source_box=max(0, record['box']), source_slot=record['slot'],
                        destination=target, destination_box=13, destination_slot=0,
                        national_species=record['dex'], output_destination=target)
                self.assertEqual(target.read_bytes(), original)
                _, records = self.native.inspect(target, 2)
                occupied = next(r for r in records if r['kind'] == 'box')
                with self.assertRaises(b.BdexError):
                    b.export_copy(store, self.native, 1, target, occupied['box'], occupied['slot'], 2)
                self.assertEqual(target.read_bytes(), original)
                original_run = self.native.run
                replacement = next((Path(OPTIONS.saves) / 'gbc').glob('*Crystal*.srm')).read_bytes()
                def change(action, **kwargs):
                    result = original_run(action, **kwargs)
                    if action == 'bdex-export-gen1-to-gen2':
                        target.write_bytes(replacement)
                    return result
                slot = sum(r['kind'] == 'box' and r['box'] == 13 for r in records)
                with patch.object(self.native, 'run', side_effect=change), self.assertRaises(b.BdexError):
                    b.export_copy(store, self.native, 1, target, 13, slot, 2)
                self.assertEqual(target.read_bytes(), replacement)
            finally:
                store.close()

    def test_native_output_alias_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            target = Path(temporary) / 'target.srm'
            target.write_bytes(self.saves['blue'].read_bytes())
            original = target.read_bytes()
            with self.assertRaises(b.BdexError):
                self.native.run('bdex-export-gen1', source=self.saves['red'], source_kind='party',
                    source_slot=0, source_box=0, destination=target, destination_box=0,
                    destination_slot=0, national_species=1, output_destination=target)
            self.assertEqual(target.read_bytes(), original)

    def test_export_rejects_occupied_slot_and_changed_destination(self):
        value = b.import_bundle(self.native, self.saves['red'], self.caches['red'])
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            store = b.Store(Path(temporary) / 'bank')
            try:
                store.import_records(value, [value['records'][0]])
                target = Path(temporary) / 'target.srm'
                target.write_bytes(self.saves['blue'].read_bytes())
                original = target.read_bytes()
                _, before = self.native.inspect(target)
                occupied = next(r for r in before if r['kind'] == 'box')
                with self.assertRaises(b.BdexError):
                    b.export_copy(store, self.native, 1, target, occupied['box'], occupied['slot'])
                self.assertEqual(target.read_bytes(), original)
                with patch.object(b, 'game_running', return_value=True):
                    with self.assertRaises(b.BdexError):
                        b.export_copy(store, self.native, 1, target, 0, 0)
                self.assertEqual(target.read_bytes(), original)
                _, current = self.native.inspect(target)
                box = next(n for n in range(12) if sum(r['kind'] == 'box' and r['box'] == n for r in current) < 20)
                slot = sum(r['kind'] == 'box' and r['box'] == box for r in current)
                real_run = self.native.run
                external_change = self.saves['yellow'].read_bytes()
                def change_destination(action, **kwargs):
                    result = real_run(action, **kwargs)
                    if action == 'bdex-export-gen1':
                        target.write_bytes(external_change)
                    return result
                with patch.object(self.native, 'run', side_effect=change_destination):
                    with self.assertRaises(b.BdexError):
                        b.export_copy(store, self.native, 1, target, box, slot)
                self.assertEqual(target.read_bytes(), external_change)
            finally:
                store.close()


class Gen2FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OPTIONS.helper:
            raise unittest.SkipTest('Private native fixtures not requested')
        cls.temp = tempfile.TemporaryDirectory(prefix='bdex-gen2-test-')
        cls.root = Path(cls.temp.name)
        cls.native = b.Native(OPTIONS.helper)
        cls.gb = load('bdex_gen2_cache_test', SOURCES / 'butterflyos-gb-sprite-cache.py')
        cls.gifts = load('bdex_gen2_gifts_test', SOURCES / 'butterflyos-gen2-gift.py')
        cls.saves, cls.roms, cls.caches = {}, {}, {}
        for game in ('Gold', 'Silver', 'Crystal'):
            key = game.lower()
            cls.saves[key] = next((Path(OPTIONS.saves) / 'gbc').glob('*' + game + '*srm'))
            cls.roms[key] = next((Path(OPTIONS.roms).parent / 'gbc').glob('*' + game + ' Version*'))
            cls.caches[key] = cls.gb.cache_rom(cls.roms[key], cls.root / 'cache')
        cls.hashes = {path: b.sha(path.read_bytes()) for path in [*cls.saves.values(), *cls.roms.values()]}

    @classmethod
    def tearDownClass(cls):
        for path, digest in cls.hashes.items():
            assert b.sha(path.read_bytes()) == digest, 'Original Gen 2 fixture changed!'
        cls.temp.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.work.cleanup)
        self.directory = Path(self.work.name)
        self.store = b.Store(self.directory / 'bank', generation=2)
        self.addCleanup(self.store.close)

    def gift_bundle(self, game='crystal', preset='sing-pichu-egg', dvs=(10, 10, 10, 10)):
        data = self.saves[game].read_bytes()
        _, records = self.native.inspect(self.saves[game], 2)
        box = 13
        slot = sum(r['kind'] == 'box' and r['box'] == box for r in records)
        output, _ = self.gifts.prepare_gift(data, self.roms[game], preset, box, slot, dvs)
        path = self.directory / ('gift-' + game + '.srm')
        path.write_bytes(output)
        value = b.import_bundle(self.native, path, self.caches[game])
        record = next(r for r in value['records'] if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
        return path, value, record

    def export_to(self, ident, game, box=13):
        target = self.directory / ('destination-' + game + '.srm')
        target.write_bytes(self.saves[game].read_bytes())
        _, before = self.native.inspect(target, 2)
        slot = sum(r['kind'] == 'box' and r['box'] == box for r in before)
        original = target.read_bytes()
        backup = b.export_copy(self.store, self.native, ident, target, box, slot)
        self.assertEqual(backup.read_bytes(), original)
        self.gifts.validate_save(target.read_bytes(), game == 'crystal')
        _, after = self.native.inspect(target, 2)
        added = next(r for r in after if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
        self.assertEqual(added['fingerprint'], self.store.entry(ident)['fingerprint'])
        self.assertEqual(len(after), len(before) + 1)
        return target, added

    def test_names_types_gender_and_families(self):
        for game, cache in self.caches.items():
            info = b.cache_info(cache)
            self.assertEqual((info['generation'], info['game']), (2, game))
            self.assertEqual(len(info['names']), 251)
            self.assertEqual(info['names']['251'], 'CELEBI')
            self.assertEqual(info['types']['81'], [23, 9])
            self.assertEqual(info['type_names']['27'], 'DARK')
            self.assertEqual(info['gender_ratios']['1'], 31)
            self.assertEqual(info['gender_ratios']['151'], 255)

    def test_party_and_box_export_across_all_families(self):
        for game in self.saves:
            value = b.import_bundle(self.native, self.saves[game], self.caches[game])
            for kind in ('party', 'box'):
                record = next(r for r in value['records'] if r['kind'] == kind)
                self.store.import_records(value, [record])
                ident = next(r['id'] for r in self.store.entries() if r['fingerprint'] == record['fingerprint'])
                for destination in self.saves:
                    with self.subTest(source=game, kind=kind, destination=destination):
                        self.export_to(ident, destination)

    def test_shiny_eggs_preserved_across_families_and_all_boxes(self):
        for game in self.saves:
            _, value, record = self.gift_bundle(game)
            self.assertTrue(record['shiny'])
            self.assertTrue(record['egg'])
            self.assertEqual(record['gender'], 'Male')
            self.store.import_records(value, [record])
            ident = next(r['id'] for r in self.store.entries() if r['fingerprint'] == record['fingerprint'])
            for destination in self.saves:
                _, added = self.export_to(ident, destination)
                self.assertTrue(added['egg'])
                self.assertTrue(added['shiny'])
        for box in range(14):
            self.export_to(ident, 'crystal', box)

    def test_held_item_and_female_gender(self):
        _, value, record = self.gift_bundle(preset='baton-pass-farfetchd', dvs=(0, 1, 2, 3))
        self.assertEqual(record['held_item'], 174)
        self.assertEqual(record['gender'], 'Female')
        self.assertFalse(record['shiny'])
        self.assertFalse(record['egg'])
        self.store.import_records(value, [record])
        _, added = self.export_to(1, 'gold')
        self.assertEqual(added['held_item'], 174)

    def test_genderless_and_species_above_151(self):
        _, value, record = self.gift_bundle(game='gold', preset='celebi')
        self.assertEqual((record['dex'], record['gender']), (251, 'Genderless'))
        self.store.import_records(value, [record])
        self.assertEqual(self.store.counts(), {251: 1})
        self.export_to(1, 'crystal')

    def test_duplicates_skip_including_trash(self):
        _, value, record = self.gift_bundle()
        self.assertEqual(self.store.import_records(value, [record]), 1)
        self.assertEqual(self.store.import_records(value, [record]), 0)
        self.store.trash(1)
        self.assertEqual(self.store.import_records(value, [record]), 0)
        self.store.trash(1, restore=True)
        self.assertEqual(self.store.counts(), {172: 1})

    def test_inspector_shows_rom_names_and_gen2_details(self):
        from types import SimpleNamespace
        _, value, record = self.gift_bundle(preset='baton-pass-farfetchd', dvs=(0, 1, 2, 3))
        self.store.import_records(value, [record])
        module = load('bdex_gen2_inspector', SOURCES / 'butterflyos-bdex-sdl.py')
        messages = []
        app = module.Bdex(SimpleNamespace(link=object(), frontend=object(),
                            message=lambda title, text: messages.append(text)), self.store)
        app.inspector(1)
        self.assertIn(b.cache_info(self.caches['crystal'])['items']['174'], messages[0])
        self.assertIn('Gender: Female', messages[0])
        self.assertIn('Egg: No', messages[0])
        self.assertNotIn('Move #', messages[0])

    def test_egg_marker_is_part_of_identity(self):
        _, value, record = self.gift_bundle()
        # A matching native body with a different egg marker is a different record.
        raw = bytes.fromhex(record['raw'] + record['ot_raw'] + record['nickname_raw'])
        self.assertEqual(record['fingerprint'], b.sha(raw + b'\x01'))
        self.assertNotEqual(record['fingerprint'], b.sha(raw + b'\x00'))

    def test_rtc_trailer_preserved(self):
        _, value, record = self.gift_bundle()
        self.store.import_records(value, [record])
        target = self.directory / 'clock.srm'
        trailer = bytes(range(48))
        target.write_bytes(self.saves['crystal'].read_bytes()[:32768] + trailer)
        b.export_copy(self.store, self.native, 1, target, 13, 0)
        self.assertEqual(target.read_bytes()[32768:], trailer)
        self.assertEqual(target.stat().st_size, 32816)
        imported = b.import_bundle(self.native, target, self.caches['crystal'])
        self.assertTrue(any(r['egg'] for r in imported['records']))

    def test_party_egg_preserved(self):
        _, value, record = self.gift_bundle()
        data = bytearray(self.saves['crystal'].read_bytes())
        party = 0x2865
        data[party + 1] = 0xfd
        data[party + 8:party + 40] = bytes.fromhex(record['raw'])
        data[party + 296:party + 307] = bytes.fromhex(record['ot_raw'])
        data[party + 362:party + 373] = bytes.fromhex(record['nickname_raw'])
        _, _, _, _, end, checksum, _ = self.gifts.layout(True)
        data[checksum:checksum + 2] = (sum(data[0x2009:end]) & 65535).to_bytes(2, 'little')
        path = self.directory / 'party-egg.srm'
        path.write_bytes(data)
        value = b.import_bundle(self.native, path, self.caches['crystal'])
        egg = next(r for r in value['records'] if r['kind'] == 'party' and r['slot'] == 0)
        self.assertTrue(egg['egg'])
        self.assertEqual(egg['fingerprint'], record['fingerprint'])
        self.store.import_records(value, [egg])
        for game in self.saves:
            _, added = self.export_to(1, game)
            self.assertTrue(added['egg'])

    def test_family_mismatch_rejected(self):
        with self.assertRaises(b.BdexError):
            b.import_bundle(self.native, self.saves['crystal'], self.caches['gold'])
        with self.assertRaises(b.BdexError):
            b.import_bundle(self.native, self.saves['gold'], self.caches['crystal'])

    def test_backward_export_rejected(self):
        value = b.import_bundle(self.native, self.saves['crystal'], self.caches['crystal'])
        self.store.import_records(value, [value['records'][0]])
        with self.assertRaises(b.BdexError):
            b.export_copy(self.store, self.native, 1, self.directory / 'missing.srm', 0, 0, 1)

    def test_wrong_generation_store_rejected(self):
        value = b.import_bundle(self.native, self.saves['crystal'], self.caches['crystal'])
        store = b.Store(self.directory / 'gen1')
        try:
            with self.assertRaises(b.BdexError):
                store.import_records(value, value['records'])
            self.assertEqual(store.entries(), [])
        finally:
            store.close()

    def test_export_survives_missing_source(self):
        path, value, record = self.gift_bundle()
        self.store.import_records(value, [record])
        path.unlink()
        self.export_to(1, 'silver')

    def test_output_alias_and_occupied_destination_rejected(self):
        value = b.import_bundle(self.native, self.saves['gold'], self.caches['gold'])
        record = value['records'][0]
        target = self.directory / 'alias.srm'
        target.write_bytes(self.saves['silver'].read_bytes())
        original = target.read_bytes()
        with self.assertRaises(b.BdexError):
            self.native.run('bdex-export-gen2', source=self.saves['gold'], source_kind=record['kind'],
                            source_box=max(0, record['box']), source_slot=record['slot'],
                            destination=target, destination_box=0, destination_slot=0,
                            national_species=record['dex'], output_destination=target)
        self.assertEqual(target.read_bytes(), original)
        self.store.import_records(value, [record])
        _, rows = self.native.inspect(target, 2)
        occupied = next(r for r in rows if r['kind'] == 'box')
        with self.assertRaises(b.BdexError):
            b.export_copy(self.store, self.native, 1, target, occupied['box'], occupied['slot'])
        self.assertEqual(target.read_bytes(), original)

    def test_zipped_rom(self):
        import zipfile
        archive = self.directory / 'renamed.zip'
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.write(self.roms['crystal'], 'anything.gbc')
        cache = self.gb.cache_rom(archive, self.directory / 'cache')
        raw = b.import_bundle(self.native, self.saves['crystal'], self.caches['crystal'])
        zipped = b.import_bundle(self.native, self.saves['crystal'], cache)
        self.assertEqual([r['fingerprint'] for r in raw['records']], [r['fingerprint'] for r in zipped['records']])


class Gen3FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OPTIONS.helper or not OPTIONS.gen3_roms:
            raise unittest.SkipTest('Gen 3 private fixtures not requested (--gen3-roms)')
        cls.temp = tempfile.TemporaryDirectory(prefix='bdex-gen3-test-')
        cls.root = Path(cls.temp.name)
        cls.native = b.Native(OPTIONS.helper)
        cls.reader = load('bdex_gen3_cache', SOURCES / 'butterflyos-gen3-sprite-cache.py')
        cls.gifts = load('bdex_gen3_gifts', SOURCES / 'butterflyos-gen3-gift.py')
        cls.gifts2 = load('bdex_gen2_migration_gifts', SOURCES / 'butterflyos-gen2-gift.py')
        cls.saves, cls.roms, cls.caches, cls.values = {}, {}, {}, {}
        for game, word in [('Ruby', 'Ruby'), ('Sapphire', 'Sapphire'), ('Emerald', 'Emerald'), ('FireRed', 'Fire Red'), ('LeafGreen', 'Leaf Green')]:
            cls.roms[game] = next(p for p in Path(OPTIONS.gen3_roms).glob('*' + game + '*.gba')
                                 if b.sha(p.read_bytes()) in cls.gifts.ROM_PROFILES)
            cls.saves[game] = next((Path(OPTIONS.saves) / 'gba').glob('*' + word + '*.srm'))
            cls.caches[game] = cls.reader.cache_rom(cls.roms[game], cls.root / 'cache')
            cls.values[game] = b.import_bundle(cls.native, cls.saves[game], cls.caches[game])
        cls.caches2, cls.saves2, cls.roms2 = {}, {}, {}
        reader2 = load('bdex_gen2_migration_cache', SOURCES / 'butterflyos-gb-sprite-cache.py')
        for game in ('Gold', 'Silver', 'Crystal'):
            cls.saves2[game] = next((Path(OPTIONS.saves) / 'gbc').glob('*' + game + '*.srm'))
            cls.roms2[game] = next((Path(OPTIONS.roms).parent / 'gbc').glob('*' + game + ' Version*'))
            cls.caches2[game] = reader2.cache_rom(cls.roms2[game], cls.root / 'cache')
        cls.hashes = {path: b.sha(path.read_bytes()) for path in [*cls.saves.values(), *cls.roms.values(), *cls.saves2.values()]}

    @classmethod
    def tearDownClass(cls):
        for path, digest in cls.hashes.items():
            assert b.sha(path.read_bytes()) == digest, 'Original private fixture changed!'
        cls.temp.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.work.cleanup)
        self.directory = Path(self.work.name)
        self.store = b.Store(self.directory / 'gen3', generation=3)
        self.addCleanup(self.store.close)

    def destination(self, game):
        path = self.directory / (game + '.srm')
        path.write_bytes(self.saves[game].read_bytes())
        _, records = self.native.inspect(path, 3)
        occupied = {(r['box'], r['slot']) for r in records if r['kind'] == 'box'}
        box, slot = next((box, slot) for box in range(14) for slot in range(30) if (box, slot) not in occupied)
        return path, box, slot

    def gen2_gift(self, preset, dvs):
        source = self.saves2['Crystal']
        _, records = self.native.inspect(source, 2)
        slot = sum(r['kind'] == 'box' and r['box'] == 13 for r in records)
        data, _ = self.gifts2.prepare_gift(source.read_bytes(), self.roms2['Crystal'], preset, 13, slot, dvs)
        path = self.directory / 'gift.srm'
        path.write_bytes(data)
        value = b.import_bundle(self.native, path, self.caches2['Crystal'])
        record = next(r for r in value['records'] if r['kind'] == 'box' and r['box'] == 13 and r['slot'] == slot)
        return path, value, record

    def test_rom_catalog_all_five_games(self):
        for game, cache in self.caches.items():
            info = b.cache_info(cache)
            self.assertEqual(len(info['names']), 386)
            self.assertEqual(info['names']['386'], 'DEOXYS')
            self.assertEqual(info['names']['29'], 'NIDORAN♀')
            self.assertEqual(info['internal'][252], 277)
            self.assertEqual(info['types']['81'], [13, 8])
            self.assertEqual(info['type_names']['17'], 'DARK')
            data, _, _, layout = self.reader.read_rom_info(self.roms[game])
            import struct
            for species in (0, 1, 172, 386, 439):
                self.assertEqual(struct.unpack_from('<H', data, layout['palette'] + species * 8 + 4)[0], species)
                self.assertEqual(struct.unpack_from('<H', data, layout['shiny_palette'] + species * 8 + 4)[0], 500 + species)
            self.assertTrue(all(1 <= r['level'] <= 100 for r in self.values[game]['records']))

    def test_party_and_pc_exports_all_25_game_pairs(self):
        for game, value in self.values.items():
            for kind in ('party', 'box'):
                record = next(r for r in value['records'] if r['kind'] == kind)
                self.store.import_records(value, [record])
                ident = next(row['id'] for row in self.store.entries() if row['fingerprint'] == record['fingerprint'])
                for target_game in self.saves:
                    with self.subTest(source=game, kind=kind, destination=target_game):
                        target, box, slot = self.destination(target_game)
                        original = target.read_bytes()
                        backup = b.export_copy(self.store, self.native, ident, target, box, slot)
                        self.assertEqual(backup.read_bytes(), original)
                        _, after = self.native.inspect(target, 3)
                        added = next(r for r in after if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
                        self.assertEqual(added['fingerprint'], record['fingerprint'])
                        self.assertEqual(self.store.entry(ident)['metadata'], record)

    def test_large_collection_duplicate_trash_and_inspector(self):
        from types import SimpleNamespace
        value = self.values['Emerald']
        unique = len({r['fingerprint'] for r in value['records']})
        self.assertEqual(self.store.import_records(value, value['records']), unique)
        self.assertEqual(self.store.import_records(value, value['records']), 0)
        self.assertTrue(any(r['dex'] > 251 for r in value['records']))
        self.store.trash(1)
        self.assertEqual(self.store.import_records(value, value['records']), 0)
        self.store.trash(1, restore=True)
        messages = []
        module = load('bdex_gen3_inspector_test', SOURCES / 'butterflyos-bdex-sdl.py')
        app = module.Bdex(SimpleNamespace(link=object(), frontend=object(), message=lambda title, text: messages.append(text)), self.store)
        app.inspector(1)
        self.assertIn('Nature:', messages[0])
        self.assertIn('IVs:', messages[0])
        self.assertIn('Personality:', messages[0])
        self.assertNotIn('Move #', messages[0])

    def test_shiny_egg_exports_all_families(self):
        rom = self.roms['Ruby'].read_bytes()
        target, box, slot = self.destination('Ruby')
        data, _ = self.gifts.prepare(target.read_bytes(), rom, 'anniversary-shiny-wish-pichu-egg', box, slot)
        target.write_bytes(data)
        value = b.import_bundle(self.native, target, self.caches['Ruby'])
        record = next(r for r in value['records'] if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
        self.assertTrue(record['egg'] and record['shiny'])
        self.store.import_records(value, [record])
        for game in self.saves:
            target, box, slot = self.destination(game)
            b.export_copy(self.store, self.native, 1, target, box, slot)
            value = b.import_bundle(self.native, target, self.caches[game])
            added = next(r for r in value['records'] if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
            self.assertEqual(added['fingerprint'], record['fingerprint'])
            self.assertTrue(added['egg'] and added['shiny'])

    def test_migration_party_pc_all_gen2_gen3_game_pairs(self):
        store = b.Store(self.directory / 'gen2', generation=2)
        try:
            for game, source in self.saves2.items():
                value = b.import_bundle(self.native, source, self.caches2[game])
                for kind in ('party', 'box'):
                    record = next(r for r in value['records'] if r['kind'] == kind and not r['egg'])
                    store.import_records(value, [record])
                    ident = next(row['id'] for row in store.entries() if row['fingerprint'] == record['fingerprint'])
                    fingerprints = set()
                    for destination in self.saves:
                        with self.subTest(source=game, kind=kind, destination=destination):
                            target, box, slot = self.destination(destination)
                            b.export_copy(store, self.native, ident, target, box, slot, 3, self.caches[destination])
                            copied = b.import_bundle(self.native, target, self.caches[destination])
                            added = next(r for r in copied['records'] if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
                            self.assertEqual((added['shiny'], added['gender']), (record['shiny'], record['gender']))
                            self.assertEqual((added['moves'], added['ot_id'], added['experience']), (record['moves'], record['ot_id'], record['experience']))
                            self.assertEqual(added['pp_ups'], record['pp_ups'])
                            self.assertLessEqual(sum(added['evs']), 510)
                            fingerprints.add(added['fingerprint'])
                    self.assertEqual(len(fingerprints), 1)
                    self.assertEqual(store.entry(ident)['metadata'], record)
        finally:
            store.close()

    def test_migration_shiny_gender_items_and_egg_refusal(self):
        for index, (preset, dvs, gender) in enumerate([
                ('baton-pass-farfetchd', [10, 10, 10, 10], 'Male'),
                ('baton-pass-farfetchd', [0, 1, 2, 3], 'Female'),
                ('mew', [10, 10, 10, 10], 'Genderless'),
                ('sing-pichu-egg', [10, 10, 10, 10], 'Male')]):
            path, value, record = self.gen2_gift(preset, dvs)
            store = b.Store(self.directory / ('bank%d' % index), generation=2)
            try:
                store.import_records(value, [record])
                path.unlink()
                for game in self.saves:
                    target, box, slot = self.destination(game)
                    original = target.read_bytes()
                    if record['egg']:
                        with self.assertRaises(b.BdexError):
                            b.export_copy(store, self.native, 1, target, box, slot, 3, self.caches[game])
                        self.assertEqual(target.read_bytes(), original)
                        continue
                    b.export_copy(store, self.native, 1, target, box, slot, 3, self.caches[game])
                    value3 = b.import_bundle(self.native, target, self.caches[game])
                    added = next(r for r in value3['records'] if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
                    self.assertEqual((added['gender'], added['shiny']), (gender, record['shiny']))
                    mapped = int(self.native.run('bdex-map-gen2-item', item=record['held_item']))
                    self.assertEqual(added['held_item'], mapped)
                    if record['dex'] == 151:
                        self.assertTrue(added['ribbons'] & (1 << 31))
            finally:
                store.close()

    def test_migration_evs_pokerus_and_unsupported_item(self):
        path, value, record = self.gen2_gift('baton-pass-farfetchd', [10] * 4)
        data = bytearray(path.read_bytes())
        at = self.gifts2.box_at(record['box']) + 22 + record['slot'] * 32
        data[at + 1] = 6  # Unused Gen II item; no verified Gen III equivalent.
        data[at + 11:at + 21] = b'\xff' * 10
        data[at + 28] = 0x42
        path.write_bytes(data)
        value = b.import_bundle(self.native, path, self.caches2['Crystal'])
        record = next(r for r in value['records'] if r['kind'] == 'box' and r['box'] == 13)
        store = b.Store(self.directory / 'gen2', generation=2)
        try:
            store.import_records(value, [record])
            target, box, slot = self.destination('Emerald')
            b.export_copy(store, self.native, 1, target, box, slot, 3, self.caches['Emerald'])
            copied = b.import_bundle(self.native, target, self.caches['Emerald'])
            added = next(r for r in copied['records'] if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot)
            self.assertEqual(sum(added['evs']), 510)
            self.assertEqual((added['held_item'], added['pokerus']), (0, 0x42))
            self.assertEqual(added['name'].replace('’', "'"), record['name'])
        finally:
            store.close()

    def test_gen3_checksum_rejection(self):
        target, box, slot = self.destination('Ruby')
        data, _ = self.gifts.prepare(target.read_bytes(), self.roms['Ruby'].read_bytes(), 'surf-pichu-egg', box, slot)
        sizes = self.gifts.section_sizes('Ruby/Sapphire')
        sections = self.gifts.active_sections(data, sizes)
        data = bytearray(data)
        logical = 4 + (box * 30 + slot) * 80 + 32
        for number in range(5, 14):
            if logical < sizes[number]:
                offset = sections[number]
                data[offset + logical] ^= 1
                import struct
                struct.pack_into('<H', data, offset + 0xff6, self.gifts.checksum(data[offset:offset + sizes[number]]))
                break
            logical -= sizes[number]
        target.write_bytes(data)
        with self.assertRaises(b.BdexError):
            self.native.inspect(target, 3)

    def test_zip_and_mismatched_family(self):
        import zipfile
        archive = self.directory / 'renamed.zip'
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.write(self.roms['Ruby'], 'renamed.gba')
        cache = self.reader.cache_rom(archive, self.root / 'cache')
        self.assertEqual(cache, self.caches['Ruby'])
        with self.assertRaises(b.BdexError):
            b.import_bundle(self.native, self.saves['Emerald'], cache)


class FilterTests(unittest.TestCase):
    def setUp(self):
        from types import SimpleNamespace
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.module = load('bdex_filter_ui', SOURCES / 'butterflyos-bdex-sdl.py')
        self.store = self.module.engine.Store(self.temp.name)
        self.addCleanup(self.store.close)
        self.ui = SimpleNamespace(link=object(), frontend=object())
        self.app = self.module.Bdex(self.ui, self.store)
        self.names = {1: 'BULBASAUR', 2: 'IVYSAUR', 3: 'VENUSAUR', 4: 'CHARMANDER'}
        self.info = {'types': {'1': [22, 3], '2': [22, 3], '3': [22, 3], '4': [20]}}

    def test_dual_types_and_stacked_filters(self):
        self.app.type_id = 3
        self.assertEqual(self.app.visible_species({}, self.names, self.info), [1, 2, 3])
        self.app.type_id = 22
        self.assertEqual(self.app.visible_species({}, self.names, self.info), [1, 2, 3])
        self.app.filter = 'Owned'
        self.app.group = 'A-D'
        self.assertEqual(self.app.visible_species({1: 2, 2: 1}, self.names, self.info), [1])
        self.app.filter = 'Missing'
        self.assertEqual(self.app.visible_species({1: 2}, self.names, self.info), [])

    def test_sort_and_saved_preferences(self):
        self.app.group = 'A-D'
        self.app.sort = 'Alphabetical'
        self.app.game = 'blue'
        self.assertEqual(self.app.visible_species({}, self.names, self.info), [1, 4])
        self.app.save_settings()
        restored = self.module.Bdex(self.ui, self.store)
        self.assertEqual((restored.group, restored.sort, restored.game), ('A-D', 'Alphabetical', 'blue'))

    def test_invalid_preferences_are_ignored(self):
        self.app.settings_path.write_text('{"1":{"filter":"wrong","sort":[]}}')
        restored = self.module.Bdex(self.ui, self.store)
        self.assertEqual((restored.filter, restored.sort), ('All', 'Pokedex'))

    def test_clear_all_filters(self):
        self.app.filter, self.app.game = 'Owned', 'blue'
        self.app.group, self.app.type_id = 'A-D', 22
        self.app.sort = 'Alphabetical'
        with patch.object(self.app, 'choose', side_effect=[5, None]):
            self.app.filters_menu()
        self.assertEqual((self.app.filter, self.app.game, self.app.group,
                          self.app.type_id, self.app.sort), ('All', None, 'All', None, 'Pokedex'))

    def test_letter_jump_keeps_filters(self):
        self.app.group = 'A-D'
        with patch.object(self.app, 'choose', return_value=4), \
             patch.object(self.app, 'choose_letter', return_value=2), \
             patch.object(self.store, 'names', return_value=self.names):
            self.app.filters_menu()
        self.assertEqual((self.app.sort, self.app.position, self.app.group), ('Alphabetical', 1, 'A-D'))

    def test_generations_keep_preferences_and_collections_separate(self):
        from types import SimpleNamespace
        self.app.blink = SimpleNamespace(_cache_for_generation=lambda *_: (None, None))
        self.app.group, self.app.game = 'A-D', 'blue'
        self.app.save_settings()
        self.app.switch_generation(2)
        self.assertEqual((self.app.species_limit, self.app.game), (251, None))
        self.assertIn('gold', self.app.games)
        self.app.type_id, self.app.game = 27, 'gold'
        self.app.save_settings()
        self.app.switch_generation(1)
        self.assertEqual((self.app.group, self.app.game), ('A-D', 'blue'))
        self.assertEqual(self.app.species_limit, 151)
        self.app.switch_generation(2)
        self.assertEqual((self.app.type_id, self.app.game), (27, 'gold'))
        self.app.store.close()

    def test_gen3_sparse_destination_and_preferences(self):
        from types import SimpleNamespace
        self.app.blink = SimpleNamespace(_cache_for_generation=lambda *_: (None, None))
        self.app.switch_generation(3)
        self.assertEqual(self.app.species_limit, 386)
        self.app.game = 'leafgreen'
        self.app.save_settings()
        with patch.object(self.app, 'choose', return_value=0):
            self.assertEqual(self.app.gen3_destination(('save', '', '', [{'box': 0, 'slot': 0}, {'box': 0, 'slot': 2}])), (0, 1))
        self.app.switch_generation(1)
        self.assertEqual(self.app.species_limit, 151)
        self.app.switch_generation(3)
        self.assertEqual(self.app.game, 'leafgreen')
        self.app.store.close()

    def test_copy_sorting(self):
        rows = [{'id': 1, 'imported': 1, 'metadata': {'level': 5, 'name': 'Z', 'game': 'blue'}},
                {'id': 2, 'imported': 2, 'metadata': {'level': 10, 'name': 'A', 'game': 'red'}}]
        for value, expected in [('Level', [2, 1]), ('Nickname', [2, 1]),
                                ('Source game', [1, 2]), ('Import date', [2, 1])]:
            self.app.copy_sort = value
            self.assertEqual([row['id'] for row in self.app.sorted_copies(rows)], expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--helper')
    parser.add_argument('--saves')
    parser.add_argument('--roms')
    parser.add_argument('--gen3-roms', help='Private qualified English GBA ROM directory')
    OPTIONS, args = parser.parse_known_args()
    if OPTIONS.helper and not (OPTIONS.saves and OPTIONS.roms):
        parser.error('--helper requires --saves and --roms')
    unittest.main(argv=[__file__] + args)

#!/usr/bin/env python3
"""Regression cases from the October 2026 safety review; disposable files only."""
import importlib.util
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SOURCES / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

blink = load('review_blink', 'butterflyos-save-trade-sdl.py')
bdex = load('review_bdex', 'butterflyos-bdex.py')
suspend = load('review_suspend', 'butterflyos-suspend-test.py')

class SaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.srm'
        self.destination = self.root / 'destination.srm'
        self.source.write_bytes(b'original source')
        self.destination.write_bytes(b'original destination')
        self.session = self.root / 'session'
        self.session.mkdir()
        self.patches = [patch.object(blink, 'new_session', return_value=str(self.session)),
                        patch.object(blink.os, 'sync')]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in reversed(self.patches): p.stop()
        self.temp.cleanup()

    def helper(self, command):
        for flag in ('--output-destination', '--output-left', '--output-right'):
            if flag in command:
                Path(command[command.index(flag) + 1]).write_bytes(b'prepared output')
        return True, 'prepared'

    def prepare(self, operation='copy'):
        left = (str(self.source), {'box': 0, 'slot': 0})
        right = (str(self.destination), 0, 0)
        with patch.object(blink, 'helper_run', side_effect=self.helper):
            if operation == 'swap':
                return blink.prepare_swap(1, left, (str(self.destination), left[1]))
            if operation == 'gen1-gen2': return blink.prepare_gen1_to_gen2(left, 1, right)
            if operation == 'gen2-gen3': return blink.prepare_gen2_to_gen3(left, 1, right)
            return blink.prepare_copy(1, left, right)

    def test_copy_and_conversions_reject_changed_inputs(self):
        for operation in ('copy', 'gen1-gen2', 'gen2-gen3'):
            for changed in (self.source, self.destination):
                with self.subTest(operation=operation, changed=changed.name):
                    self.assertIsNotNone(self.prepare(operation)[0])
                    changed.write_bytes(changed.read_bytes() + b'new progress')
                    originals = (self.source.read_bytes(), self.destination.read_bytes())
                    self.assertFalse(blink.commit_copy(str(self.session))[0])
                    self.assertEqual(originals, (self.source.read_bytes(), self.destination.read_bytes()))

    def test_swap_rejects_changed_save(self):
        self.prepare('swap')
        self.destination.write_bytes(b'new progress')
        self.assertFalse(blink.commit_swap(str(self.session))[0])
        self.assertEqual(self.source.read_bytes(), b'original source')
        self.assertEqual(self.destination.read_bytes(), b'new progress')

    def test_unchanged_copy_and_swap_succeed(self):
        self.prepare()
        self.assertTrue(blink.commit_copy(str(self.session))[0])
        self.assertEqual(self.destination.read_bytes(), b'prepared output')
        self.prepare('swap')
        self.assertTrue(blink.commit_swap(str(self.session))[0])
        self.assertEqual(self.source.read_bytes(), b'prepared output')

    def test_change_during_preparation_rejected(self):
        def change(command):
            self.source.write_bytes(b'changed during preparation')
            return self.helper(command)
        with patch.object(blink, 'helper_run', side_effect=change):
            session, message = blink.prepare_copy(1, (str(self.source), {'box':0,'slot':0}),
                                                  (str(self.destination),0,0))
        self.assertIsNone(session)
        self.assertIn('changed', message)
        self.assertEqual(self.destination.read_bytes(), b'original destination')

    def test_gift_and_event_sessions_reject_changed_destination(self):
        import json
        def generator(command, **kwargs):
            flag = '--output-record' if '--output-record' in command else '--output'
            Path(command[command.index(flag)+1]).write_bytes(b'prepared output')
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({
                'nickname':'TEST', 'national_species':1, 'rom_title':'POKEMON RED',
                'before':{'stage':'ready'}}), stderr='')
        operations = [blink.prepare_gen1_gift, blink.prepare_gen2_gift, blink.prepare_gen3_gift]
        for prepare in operations:
            with patch.object(blink.subprocess, 'run', side_effect=generator), patch.object(blink, 'helper_run', side_effect=self.helper):
                session, _ = prepare((str(self.destination),0,0), 'fixture.rom', 'test')
            self.assertIsNotNone(session)
            self.destination.write_bytes(self.destination.read_bytes()+b'new progress')
            self.assertFalse(blink.commit_copy(session)[0])
        with patch.object(blink.subprocess, 'run', side_effect=generator):
            session, _ = blink.prepare_save_event(str(self.destination), 'fixture.rom', 'test', 'fixture-tool')
        self.assertIsNotNone(session)
        self.destination.write_bytes(b'latest progress')
        self.assertFalse(blink.commit_copy(session)[0])
        self.assertEqual(self.destination.read_bytes(), b'latest progress')

    def test_missing_commit_fingerprint_rejected(self):
        self.prepare()
        (self.session/'original-destination-sha256').unlink()
        self.assertFalse(blink.commit_copy(str(self.session))[0])
        self.assertEqual(self.destination.read_bytes(), b'original destination')

    def test_change_while_backing_up_rejected(self):
        self.prepare()
        real_copy = blink.copy_with_sync
        def change(source, destination, **kwargs):
            real_copy(source, destination, **kwargs)
            self.destination.write_bytes(b'new progress during backup')
        with patch.object(blink, 'copy_with_sync', side_effect=change):
            self.assertFalse(blink.commit_copy(str(self.session))[0])
        self.assertEqual(self.destination.read_bytes(), b'new progress during backup')

class DatabaseTests(unittest.TestCase):
    def test_hot_journal_recovery_preserves_committed_collection(self):
        with tempfile.TemporaryDirectory() as folder:
            store = bdex.Store(folder)
            store.connection.executemany('INSERT INTO catalog VALUES (?,?,?)',
                [(i, 'A'*4000, i) for i in range(1,152)])
            store.connection.commit()
            store.close()
            database = Path(folder)/'collection.sqlite3'
            subprocess.run([sys.executable, '-c',
                "import sqlite3,os,sys; c=sqlite3.connect(sys.argv[1]); "
                "c.execute('PRAGMA cache_size=5'); c.execute('BEGIN IMMEDIATE'); "
                "c.execute(\"UPDATE catalog SET name=replace(name,'A','B')\"); os._exit(0)",
                str(database)], check=True)
            self.assertTrue(Path(str(database)+'-journal').exists())
            with self.assertRaises(sqlite3.OperationalError): bdex.database_valid(database)
            store = bdex.Store(folder)
            try:
                self.assertEqual(store.connection.execute('SELECT name FROM catalog LIMIT 1').fetchone()[0], 'A'*4000)
                bdex.database_valid(database)
            finally: store.close()

class RetentionTests(unittest.TestCase):
    def test_success_failure_limits_preserve_active_and_user_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for i in range(40):
                cycle = root/('20261020-120000-%03d' % i)
                cycle.mkdir()
                (cycle/('after.json' if i%2 else 'error.json')).write_text('{}')
            active = root/'20261020-120000-000'
            unrelated = root/'my-files'; unrelated.mkdir()
            external = root/'20261020-120000-999'; external.symlink_to(unrelated, target_is_directory=True)
            with patch.object(suspend, 'ROOT', root): suspend.prune_diagnostics(active)
            self.assertTrue(active.exists())
            self.assertTrue(unrelated.exists())
            self.assertTrue(external.is_symlink())
            dirs = [p for p in root.iterdir() if p.is_dir() and not p.is_symlink() and p != unrelated]
            self.assertEqual(len(dirs),31)  # 20 successes, 10 old failures, active failure.

class InstallerTests(unittest.TestCase):
    def test_write_failure_and_bad_readback_are_not_success(self):
        text = (ROOT/'projects/ROCKNIX/packages/sysutils/busybox/scripts/init').read_text()
        function = text[text.index('update_file() {'):text.index('\nupdate_partition() {')]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'SYSTEM').write_bytes(b'new'); (root/'installed').write_bytes(b'old')
            stubs = 'mount() { return 0; }\nStartProgress() { :; }\nStopProgress() { :; }\nsync() { :; }\n'
            for writer in ('return 1', 'return 0', 'command dd "$@"'):
                script = stubs + 'dd() { '+writer+'; }\n' + function + '\nUPDATE_DIR="$1"\nUPDATE_ROOT="$1"\ndisk=SD\nupdate_file System SYSTEM "$1/installed"\n'
                result = subprocess.run(['sh','-c',script,'test',folder])
                self.assertEqual(result.returncode, 0 if writer.startswith('command') else 1)

    def test_installation_stops_before_cleanup_on_write_failure(self):
        text = (ROOT/'projects/ROCKNIX/packages/sysutils/busybox/scripts/init').read_text()
        sequence = text[text.index('  # all ok, update'):text.index('\nprepare_sysroot() {')]
        sequence = sequence[:sequence.rfind('}')]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            staged = root/'update.tar'; staged.write_bytes(b'retained recovery material')
            for failed in ('Kernel', 'System', 'Boot'):
                script = r'''display_versions() { :; }
update_file() { [ "$1" != "$FAIL" ]; }
update_partition() { [ "$1" != "$FAIL" ]; }
update_bootloader() { [ "$FAIL" != Boot ]; }
update_failed() { echo "$*" >"$CASE/error"; exit 7; }
umount() { :; }
sync() { :; }
StartProgress() { echo unexpected-success >"$CASE/success"; }
do_cleanup() { rm "$CASE/update.tar"; }
do_reboot() { echo unexpected-reboot >"$CASE/reboot"; }
IMAGE_KERNEL=nonexistent-review-kernel
IMAGE_SYSTEM=SYSTEM
UPDATE_KERNEL=KERNEL
UPDATE_SYSTEM=SYSTEM
FAIL=$1
CASE=$2
''' + sequence
                result = subprocess.run(['sh','-c',script,'test',failed,folder])
                self.assertEqual(result.returncode,7)
                self.assertTrue(staged.exists())
                self.assertTrue((root/'error').exists())
                self.assertFalse((root/'success').exists())
                self.assertFalse((root/'reboot').exists())

if __name__ == '__main__': unittest.main()

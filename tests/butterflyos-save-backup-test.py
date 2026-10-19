#!/usr/bin/env python3
"""Safety tests run only against disposable temporary directories."""
import importlib.util
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import os

SOURCE = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-save-backup.py'
spec = importlib.util.spec_from_file_location('save_backup', SOURCE)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class SaveBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cards = []
        for name in ('OS-UUID', 'GAME-UUID'):
            path = self.root / name
            (path / 'roms/gba').mkdir(parents=True)
            self.cards.append(dict(path=path, uuid=name, device=path.stat().st_dev))
        self.a, self.b = self.cards

    def tearDown(self):
        self.temp.cleanup()

    def save(self, card, content=b'progress', name='gba/Pokemon.srm'):
        path = card['path'] / 'roms' / name
        path.write_bytes(content)
        os.utime(path, (1, 1))
        return path

    def copy(self, path, source=None, destination=None):
        # Temp fixtures share one filesystem; production mount validation is tested separately.
        with patch.object(backup, 'check_pair'):
            return backup.snapshot(path, source or self.a, destination or self.b)

    def versions(self, destination, source):
        return list((destination['path'] / backup.BACKUPS / source['uuid']).rglob('*.backup'))

    def test_duplicate_names_are_both_preserved(self):
        first, second = self.save(self.a, b'first'), self.save(self.b, b'second')
        self.assertEqual(self.copy(first), 'copied')
        self.assertEqual(self.copy(second, self.b, self.a), 'copied')
        self.assertEqual(self.versions(self.b, self.a)[0].read_bytes(), b'first')
        self.assertEqual(self.versions(self.a, self.b)[0].read_bytes(), b'second')
        self.assertEqual(first.read_bytes(), b'first')
        self.assertEqual(second.read_bytes(), b'second')

    def test_changes_use_content_not_source_timestamp_and_keep_five(self):
        for n in range(7):
            path = self.save(self.a, str(n).encode())
            self.assertEqual(self.copy(path), 'copied')
        self.assertEqual(len(self.versions(self.b, self.a)), 5)
        self.assertEqual(self.copy(path), 'unchanged')
        self.assertEqual(len(self.versions(self.b, self.a)), 5)

    def test_clock_going_backward_keeps_latest_snapshot(self):
        path = self.save(self.a, b'old')
        self.copy(path)
        self.save(self.a, b'new')
        with patch.object(backup.time, 'time_ns', return_value=1):
            self.assertEqual(self.copy(path), 'copied')
        self.assertEqual(self.copy(path), 'unchanged')
        self.assertEqual(sorted(self.versions(self.b, self.a))[-1].read_bytes(), b'new')

    def test_recent_empty_and_large_files_are_skipped(self):
        path = self.save(self.a)
        os.utime(path, None)
        self.assertEqual(self.copy(path), 'skipped')
        self.assertEqual(self.copy(self.save(self.a, b'')), 'skipped')
        with patch.object(backup, 'MAX_SIZE', 1):
            self.assertEqual(self.copy(self.save(self.a)), 'skipped')

    def test_low_space_preserves_last_backup(self):
        path = self.save(self.a)
        self.copy(path)
        original = self.versions(self.b, self.a)[0]
        self.save(self.a, b'new progress')
        low = os.statvfs_result((4096, 4096, 100000, 9000, 9000, 0, 0, 0, 0, 255))
        with patch.object(backup.os, 'statvfs', return_value=low):
            self.assertEqual(self.copy(path), 'space-reserve')
        self.assertEqual(original.read_bytes(), b'progress')

    def test_failed_verification_preserves_last_backup(self):
        path = self.save(self.a)
        self.copy(path)
        original = self.versions(self.b, self.a)[0]
        self.save(self.a, b'new progress')
        real_read = Path.read_bytes
        def bad_read(path):
            return b'broken' if path.name.startswith('.pending-') else real_read(path)
        with patch.object(Path, 'read_bytes', bad_read):
            with self.assertRaises(IOError):
                self.copy(path)
        self.assertEqual(original.read_bytes(), b'progress')
        self.assertFalse(list(original.parent.glob('.pending-*')))

    def test_scan_ignores_mirror_links_states_and_bios(self):
        save = self.save(self.a)
        (save.parent / 'mirror.sav').symlink_to(save)
        (save.parent / 'game.state').write_bytes(b'state')
        (self.a['path'] / 'roms/bios').mkdir()
        (self.a['path'] / 'roms/bios/example.sav').write_bytes(b'bios')
        self.assertEqual(list(backup.candidates(self.a['path'] / 'roms')), [save])

    def test_redirected_destination_rejected(self):
        (self.b['path'] / backup.BACKUPS).symlink_to(self.a['path'], target_is_directory=True)
        with self.assertRaises(ValueError):
            self.copy(self.save(self.a))

    def test_unmounted_or_duplicate_cards_rejected(self):
        with self.assertRaises(ValueError):
            backup.check_pair(self.a, self.b)
        with patch.object(backup.os.path, 'ismount', return_value=True):
            with self.assertRaises(ValueError):
                backup.check_pair(self.a, self.b)

    def test_disabled_does_not_probe_or_scan(self):
        with patch.object(backup, 'CONFIG', self.root / 'config'), patch.object(backup, 'card_info') as probe:
            self.assertEqual(backup.run(), {'status': 'disabled'})
            probe.assert_not_called()

    def test_enable_rearms_timer_after_disabled_boot(self):
        config = self.root / 'config'
        with patch.object(backup, 'CONFIG', config), patch('sys.argv', ['backup', 'enable']), \
                patch.object(backup.subprocess, 'run') as command:
            backup.main()
        self.assertTrue((config / 'enabled').exists())
        command.assert_called_once_with(
            ['systemctl', 'restart', '--no-block', 'butterflyos-save-backup.timer'], check=True)
        with patch.object(backup, 'CONFIG', config), patch('sys.argv', ['backup', 'disable']), \
                patch.object(backup.subprocess, 'run') as command:
            backup.main()
        self.assertFalse((config / 'enabled').exists())
        command.assert_not_called()

    def test_kernel_mounts_and_escaped_paths(self):
        records = backup.mount_records(
            '28 27 179:34 / /storage rw,noatime shared:3 - ext4 /dev/mmcblk0p2 rw\n'
            '72 28 179:1 / /storage/games-external rw,noatime - exfat /dev/mmcblk1p1 rw\n'
            '73 28 179:1 / /some\\040card rw - exfat /dev/mmcblk1p1 ro\n'
            'malformed\n')
        self.assertEqual(records['/storage']['source'], '/dev/mmcblk0p2')
        self.assertEqual(records['/storage/games-external']['filesystem'], 'exfat')
        self.assertIn('ro', records['/some card']['options'])
        self.assertEqual(len(records), 3)

    def test_card_info_without_findmnt(self):
        card = self.a['path']
        mountinfo = '28 27 179:34 / %s rw - ext4 /dev/mmcblk0p2 rw\n' % card
        from subprocess import CompletedProcess
        with patch.object(backup.os.path, 'ismount', return_value=True), \
                patch.object(Path, 'read_text', return_value=mountinfo), \
                patch.object(backup.subprocess, 'run', return_value=CompletedProcess([], 0, 'OS-UUID\n')) as command:
            result = backup.card_info(card)
        self.assertEqual(result['uuid'], 'OS-UUID')
        self.assertEqual(result['physical'], '/dev/mmcblk0')
        self.assertEqual(command.call_args.args[0][0], 'blkid')


if __name__ == '__main__':
    unittest.main()

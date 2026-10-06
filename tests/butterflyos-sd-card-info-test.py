#!/usr/bin/env python3
"""Storage safety cases: absent cards, bind mounts and read-only storage."""
import importlib.machinery
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

source=Path(__file__).resolve().parents[1]/'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-sd-card-info'
loader=importlib.machinery.SourceFileLoader('sd_card_info',str(source))
spec=importlib.util.spec_from_loader(loader.name,loader)
info=importlib.util.module_from_spec(spec);loader.exec_module(info)
OS='23 1 179:2 / /storage rw,noatime - ext4 /dev/mmcblk0p2 rw\n'
SECOND='24 23 179:9 / /storage/games-external rw,noatime - exfat /dev/mmcblk1p1 rw\n'
STATS=SimpleNamespace(f_frsize=4096,f_bsize=4096,f_blocks=100,f_bfree=40,f_bavail=35)

class CardTests(unittest.TestCase):
    def collect(self,mounts):
        with patch.object(info,'read',return_value=mounts),patch.object(info,'device_info',return_value={'present':False,'capacity_bytes':None}),patch.object(info,'parent_device',return_value='mmcblk0'),patch.object(info.os,'statvfs',return_value=STATS) as calls:
            return info.collect(),calls.call_args_list

    def test_missing_second_card_does_not_measure_parent_filesystem(self):
        result,calls=self.collect(OS)
        self.assertEqual([c.args[0] for c in calls],['/storage'])
        self.assertFalse(result['cards'][1]['mounted'])
        self.assertEqual(result['combined_available_bytes'],35*4096)
        self.assertNotIn('available_bytes',result['cards'][1])

    def test_two_filesystems_and_reserved_blocks(self):
        result,calls=self.collect(OS+SECOND)
        self.assertEqual(len(calls),2)
        self.assertEqual(result['combined_available_bytes'],70*4096)
        self.assertEqual(result['cards'][0]['reserved_bytes'],5*4096)
        self.assertEqual(result['cards'][0]['used_bytes'],60*4096)

    def test_same_filesystem_bind_mount_is_not_counted_twice(self):
        bind='24 23 179:2 /games /storage/games-external rw - ext4 /dev/mmcblk0p2 rw\n'
        result,_=self.collect(OS+bind)
        self.assertEqual(result['combined_available_bytes'],35*4096)

    def test_readonly_superblock_and_escaped_mount_path(self):
        mounts=info.parse_mounts('24 23 179:9 / /storage/games\\040external rw - ext4 /dev/mmcblk1p1 ro\n')
        self.assertTrue(mounts['/storage/games external']['readonly'])
        result,_=self.collect(OS.replace('ext4 /dev/mmcblk0p2 rw','ext4 /dev/mmcblk0p2 ro'))
        self.assertIn('updates need writable storage',info.render(result))

if __name__=='__main__':unittest.main()

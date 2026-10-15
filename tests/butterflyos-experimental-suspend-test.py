#!/usr/bin/env python3
"""Exercise real scratch-file checks with a simulated suspend, never sleep host."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-suspend-test.py'
spec = importlib.util.spec_from_file_location('suspend_test', SOURCE)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

class SuspendTests(unittest.TestCase):
    def cycle(self, failure=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); card = root/'card'; card.mkdir()
            driver = root/'driver'; driver.mkdir()
            power = root/'mem_sleep'; power.write_text('s2idle [deep]')
            flag = root/'enabled'; flag.touch()
            def run(args, **kwargs):
                if args[:2] == ['systemctl', 'start']:
                    self.assertEqual(args, ['systemctl', 'start', 'systemd-suspend.service'])
                    probes = list(card.glob('.butterfly-suspend-probe-*'))
                    self.assertEqual(len(probes), 1)
                    self.assertEqual(probes[0].stat().st_size, 4096)
                    self.assertTrue(next((root/'logs').glob('*/before.json')).exists())
                    self.assertEqual(power.read_text(), 'deep')
                    if failure == 'corrupt': probes[0].write_bytes(b'bad')
                    return subprocess.CompletedProcess(args, 1 if failure=='reject' else 0, stdout='simulated')
                return subprocess.CompletedProcess(args, 0)
            def command(args):
                return '-- cursor: test' if '--show-cursor' in args else 'mmc0: error -110' if failure=='kernel' else ''
            with patch.multiple(s, ROOT=root/'logs', ENABLED=flag, DRIVER=driver, POWER=power, UPDATE=root/'update/lock'), patch.object(s, 'probe_targets', return_value=[card]), patch.object(s, 'snapshot', return_value={'kernel':''}), patch.object(s, 'command', side_effect=command), patch.object(s.subprocess, 'run', side_effect=run), patch.object(s.os, 'sync'):
                if failure:
                    with self.assertRaises(RuntimeError): s.run_cycle()
                    self.assertFalse(flag.exists())
                    self.assertTrue(next((root/'logs').glob('*/error.json')).exists())
                else:
                    directory = Path(s.run_cycle())
                    self.assertTrue((directory/'after.json').exists())
                    self.assertTrue(flag.exists())
                self.assertEqual(list(card.iterdir()), [])
    def test_roundtrip(self): self.cycle()
    def test_corrupt_probe_disables_lid(self): self.cycle('corrupt')
    def test_kernel_timeout_disables_lid(self): self.cycle('kernel')
    def test_rejected_suspend_disables_lid(self): self.cycle('reject')
    def test_missing_driver_refuses(self):
        with tempfile.TemporaryDirectory() as d, patch.object(s, 'DRIVER', Path(d)/'missing'):
            with self.assertRaises(RuntimeError): s.run_cycle()

if __name__=='__main__': unittest.main()

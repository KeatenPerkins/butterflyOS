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
    def wake(self, online=0, **changes):
        result = {'lid_closed': True, 'charger_online': online,
                  'irqs': dict.fromkeys(s.WAKE_IRQ_NAMES, 0)}
        result.update(changes)
        return result

    def test_only_charger_wakes_qualify(self):
        before, after = self.wake(), self.wake(1)
        self.assertTrue(s.charger_only_wake(before, after))
        self.assertTrue(s.charger_only_wake(after, before))
        self.assertFalse(s.charger_only_wake(before, before))
        for key in ('rk805_pwrkey_fall', 'rk805_pwrkey_rise'):
            changed = self.wake(1)
            changed['irqs'][key] += 1
            self.assertFalse(s.charger_only_wake(before, changed))
        self.assertFalse(s.charger_only_wake(before, self.wake(1, lid_closed=False)))
        self.assertFalse(s.charger_only_wake(before, self.wake(1, irqs={})))
        self.assertFalse(s.charger_only_wake(before, self.wake(None)))

    def test_charger_with_single_closed_lid_irq(self):
        before, after = self.wake(1), self.wake(0)
        before['irqs']['Lid'] = 1
        after['irqs']['Lid'] = 2
        self.assertTrue(s.charger_only_wake(before, after))
        self.assertFalse(s.same_user_inputs(before, after))  # Still strict during debounce.
        for delta in (0, 2, 3, -1):
            changed = self.wake(0)
            changed['irqs']['Lid'] = before['irqs']['Lid'] + delta
            self.assertEqual(s.charger_only_wake(before, changed), delta == 0)
        for key in ('rk805_pwrkey_fall', 'rk805_pwrkey_rise'):
            changed = self.wake(0)
            changed['irqs']['Lid'] = 2
            changed['irqs'][key] = 1
            self.assertFalse(s.charger_only_wake(before, changed))
        for closed in (False, None):
            self.assertFalse(s.charger_only_wake(before, dict(after, lid_closed=closed)))
        # A hall IRQ alone, with no charger status/IRQ change, is not a USB wake.
        self.assertFalse(s.charger_only_wake(before, dict(after, charger_online=1)))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);flag=root/'enabled';flag.touch()
            cycle=root/'cycle';cycle.mkdir()
            (cycle/'after.json').write_text(__import__('json').dumps({
                'wake_inputs_before':before, 'wake_inputs_after':after,
                'sleep_elapsed_seconds':18}))
            # Opening during debounce or another lid IRQ cancels the retry.
            additional = dict(after, irqs=dict(after['irqs'], Lid=3))
            for current in (dict(after, lid_closed=False), additional):
                with patch.object(s,'ENABLED',flag), patch.object(s,'run_cycle',return_value=str(cycle)) as run, patch.object(s.time,'sleep'), patch.object(s,'wake_inputs',return_value=current):
                    s.run_lid_cycles()
                    self.assertEqual(run.call_count,1)

    def test_retry_limit_and_user_cancel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);flag=root/'enabled';flag.touch()
            before, after = self.wake(), self.wake(1)
            cycle=root/'cycle';cycle.mkdir()
            def report(seconds=30):
                (cycle/'after.json').write_text(__import__('json').dumps({
                    'wake_inputs_before':before, 'wake_inputs_after':after,
                    'sleep_elapsed_seconds':seconds}))
            report()
            with patch.object(s,'ENABLED',flag), patch.object(s,'run_cycle',return_value=str(cycle)) as run, patch.object(s.time,'sleep'), patch.object(s,'wake_inputs',return_value=after):
                s.run_lid_cycles()
                self.assertEqual(run.call_count,4)  # First sleep plus at most three retries.
                report(1)
                run.reset_mock();s.run_lid_cycles();self.assertEqual(run.call_count,2)
                report()
                run.reset_mock()
                with patch.object(s,'wake_inputs',return_value=self.wake(1,lid_closed=False)):
                    s.run_lid_cycles();self.assertEqual(run.call_count,1)
                run.reset_mock();flag.unlink()
                s.run_lid_cycles();self.assertEqual(run.call_count,1)

    def test_hardware_toggle_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            enabled = Path(directory)/'enabled'
            disabled = Path(directory)/'disabled'
            with patch.multiple(s, ENABLED=enabled, DISABLED=disabled):
                for value, expected in [('off', False), ('on', True)]:
                    with patch.object(s.sys, 'argv', ['helper', 'set-lid-sleep', value]):
                        self.assertEqual(s.main(), 0)
                    self.assertEqual(enabled.exists(), expected)
                    self.assertEqual(disabled.exists(), not expected)
                with patch.object(s.sys, 'argv', ['helper', 'set-lid-sleep', 'invalid']):
                    with self.assertRaises(ValueError): s.main()
                self.assertTrue(enabled.exists())

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
            with patch.multiple(s, ROOT=root/'logs', ENABLED=flag, DISABLED=root/'disabled', DRIVER=driver, POWER=power, UPDATE=root/'update/lock'), patch.object(s, 'probe_targets', return_value=[card]), patch.object(s, 'snapshot', return_value={'kernel':''}), patch.object(s, 'command', side_effect=command), patch.object(s.subprocess, 'run', side_effect=run), patch.object(s.os, 'sync'):
                if failure:
                    with self.assertRaises(RuntimeError): s.run_cycle()
                    self.assertFalse(flag.exists())
                    self.assertTrue((root/'disabled').exists())
                    self.assertTrue(next((root/'logs').glob('*/error.json')).exists())
                else:
                    directory = Path(s.run_cycle())
                    self.assertTrue((directory/'after.json').exists())
                    self.assertTrue(flag.exists())
                self.assertEqual(list(card.iterdir()), [])
    def test_boot_default_and_persistent_disable(self):
        quirk = SOURCE.parents[3]/'hardware/quirks/devices/Miyoo Flip/030-suspend_mode'
        script = quirk.read_text()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            flag = root/'.config/butterflyos/experimental-lid-suspend.enabled'
            disabled = flag.with_name('experimental-lid-suspend.disabled')
            script = script.replace('/storage', str(root)).replace(
                '. /etc/profile.d/001-functions', 'set_setting() { :; }').replace(
                'systemctl try-restart systemd-logind.service', ':')
            def boot(): subprocess.run(['sh', '-c', script], check=True)
            with patch.multiple(s, ENABLED=flag, DISABLED=disabled):
                boot(); self.assertTrue(flag.exists())
                s.set_lid_sleep(False); boot()
                self.assertFalse(flag.exists()); self.assertTrue(disabled.exists())
                s.set_lid_sleep(True); boot()
                self.assertTrue(flag.exists()); self.assertFalse(disabled.exists())

    def test_mountinfo_without_findmnt(self):
        mounts = ('31 1 179:2 / /storage rw - ext4 /dev/mmcblk0p2 rw\n'
                  '32 1 179:9 / /var/media/Second\\040Card rw - exfat /dev/mmcblk1p1 rw\n'
                  '33 1 0:20 / /storage/roms rw - fuse.mergerfs mergerfs rw\n'
                  '34 1 179:1 / /flash ro - vfat /dev/mmcblk0p1 ro\n')
        with patch.object(s.Path, 'read_text', return_value=mounts):
            self.assertEqual(s.probe_targets(), [Path('/storage'), Path('/var/media/Second Card')])
    def test_roundtrip(self): self.cycle()
    def test_corrupt_probe_disables_lid(self): self.cycle('corrupt')
    def test_kernel_timeout_disables_lid(self): self.cycle('kernel')
    def test_rejected_suspend_disables_lid(self): self.cycle('reject')
    def test_missing_driver_refuses(self):
        with tempfile.TemporaryDirectory() as d, patch.object(s, 'DRIVER', Path(d)/'missing'):
            with self.assertRaises(RuntimeError): s.run_cycle()

if __name__=='__main__': unittest.main()

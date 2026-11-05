#!/usr/bin/env python3
"""Exercise boot installer progress and failure paths on disposable files only."""
from pathlib import Path
import subprocess
import tempfile
import unittest

INIT = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/sysutils/busybox/scripts/init'
SOURCE = INIT.read_text()
FUNCTIONS = SOURCE[SOURCE.index('update_stage_done() {'):SOURCE.index('\nupdate_partition() {')]


class InstallProgressTests(unittest.TestCase):
    def run_install(self, mode='ok'):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'SYSTEM').write_bytes(b'new system payload\0' * 1024)
            (root / 'installed').write_bytes(b'previous system')
            harness = r'''
UPDATE_DIR=$1
UPDATE_ROOT=$1
disk=LABEL=test
mode=$2
StartProgress() { printf 'START %s %s\n' "$1" "$2"; }
StopProgress() { printf 'STOP %s\n' "$1"; }
mount() {
  printf 'MOUNT %s\n' "$*"
  case "$mode:$*" in rw-fail:*remount,rw*|ro-fail:*remount,ro*) return 1;; esac
  return 0
}
sync() { printf 'SYNC\n'; }
dd() {
  command dd "$@" || return 1
  case "$mode" in
    write-fail) return 1;;
    corrupt) printf 'corrupt' >> "$destination";;
  esac
}
'''
            script = harness + FUNCTIONS + '\nupdate_file System SYSTEM "$1/installed"\nexit $?\n'
            result = subprocess.run(['sh', '-c', script, 'installer-test', tmp, mode],
                                    capture_output=True, text=True)
            self.assertTrue((root / 'SYSTEM').is_file(), 'Staged input must survive')
            if mode == 'ok':
                self.assertEqual((root / 'SYSTEM').read_bytes(), (root / 'installed').read_bytes())
                self.assertIn('MOUNT -o remount,ro /flash', (root / 'install-error.log').read_text())
            return result

    def test_success_has_animated_write_verify_and_finalize(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        stages = [line for line in result.stdout.splitlines() if line.startswith('START')]
        self.assertEqual(stages, ['START spinner Writing System / flushing SD card... ',
                                  'START spinner Verifying System... ',
                                  'START spinner Finalizing System... '])
        self.assertNotIn('100%', result.stdout)
        self.assertEqual(result.stdout.count('STOP done'), 3)

    def test_failed_write_skips_verification_and_reports_failure(self):
        result = self.run_install('write-fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Verifying', result.stdout)
        self.assertEqual(result.stdout.count('STOP FAILED'), 2)
        self.assertIn('SYNC', result.stdout)

    def test_corrupt_readback_still_fails(self):
        result = self.run_install('corrupt')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Verifying', result.stdout)
        self.assertEqual(result.stdout.count('STOP FAILED'), 2)

    def test_readonly_remount_failure_still_fails(self):
        result = self.run_install('ro-fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stdout.rstrip().endswith('STOP FAILED'))

    def test_initial_mount_failure_never_starts_writing(self):
        result = self.run_install('rw-fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('START', result.stdout)


if __name__ == '__main__':
    unittest.main()

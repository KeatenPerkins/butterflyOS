#!/usr/bin/env python3
"""Exercise the real formatter flow without accessing any block device."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'
spec = importlib.util.spec_from_file_location('game_card_ui', SOURCES / 'butterflyos-game-card-sdl.py')
UI = importlib.util.module_from_spec(spec)
spec.loader.exec_module(UI)


class FakeUI:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.frontend = self
        self.messages = []
        self.confirmations = 0

    def draw_message(self, title, text, footer, offset):
        self.messages.append(text)
        return 0

    def action(self):
        return 'select'

    def menu(self, title, items, selected):
        self.confirmations += 1
        assert selected == 0 and items[0][0] == 'Cancel'
        return next(self.replies)

    def message(self, title, text):
        self.messages.append(text)


class FormatSafetyTest(unittest.TestCase):
    def run_flow(self, replies, fail_check=0, mounted=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            trace = path / 'trace'
            source = (SOURCES / 'game-card-ui.sh').read_text().split(
                'if [[ "$GRAPHICAL_BACKEND" == 1 ]]; then\n  case "${2:-}"', 1)[0]
            # The functions above are real; only disk/system commands are replaced.
            # A regular-file stand-in avoids needing a block device for the final
            # existence checks. All mkfs/partition/mount/index calls are mocked.
            source = source.replace('! -b "${PARTITION}"', '! -f "${PARTITION}"')
            source = source.replace('/tmp/butterflyos-game-card-format.log', str(path / 'format.log'))
            mocks = r'''
GRAPHICAL_BACKEND=1
PARTITION="TEST_PARTITION"
INDEXER=true
checks=0
safety_check() {
  checks=$((checks + 1))
  echo "check-$checks" >> "TRACE"
  if [[ "$checks" == FAIL_CHECK ]]; then
    message 'SAFETY CHECK FAILED'
    return 1
  fi
}
device_size() { echo '64 GiB'; }
umount() { echo unmount >> "TRACE"; }
awk() {
  if [[ "$*" == *'/proc/mounts'* ]]; then return MOUNT_RETURN; fi
  echo 1
}
mkfs.exfat() { echo mkfs >> "TRACE"; }
fsck.exfat() { echo fsck >> "TRACE"; }
sync() { :; }
mount_card() { echo mount >> "TRACE"; }
create_library() { echo library >> "TRACE"; }
format_card
'''
            partition = path / 'partition'
            partition.touch()
            mocks = mocks.replace('TEST_PARTITION', str(partition)).replace('TRACE', str(trace))
            mocks = mocks.replace('FAIL_CHECK', str(fail_check)).replace('MOUNT_RETURN', '0' if mounted else '1')
            backend = path / 'backend.sh'
            backend.write_text(source + mocks)
            ui = FakeUI(replies)
            UI.run_backend(ui, 'format', backend)
            return trace.read_text().splitlines(), ui

    def test_cancel_first_confirmation_never_formats(self):
        trace, ui = self.run_flow([0])
        self.assertEqual(trace, ['check-1'])
        self.assertEqual(ui.confirmations, 1)
        self.assertFalse(any('could not finish' in text for text in ui.messages))

    def test_cancel_final_confirmation_never_formats(self):
        trace, ui = self.run_flow([1, 0])
        self.assertEqual(trace, ['check-1'])
        self.assertEqual(ui.confirmations, 2)

    def test_changed_target_after_confirmations_never_formats(self):
        trace, ui = self.run_flow([1, 1], fail_check=2)
        self.assertEqual(trace, ['check-1', 'check-2'])
        self.assertIn('SAFETY CHECK FAILED', ui.messages)

    def test_still_mounted_never_formats(self):
        trace, ui = self.run_flow([1, 1], mounted=True)
        self.assertNotIn('mkfs', trace)
        self.assertTrue(any('CARD IS IN USE' in text for text in ui.messages))

    def test_both_confirmations_allow_mock_format_in_order(self):
        trace, ui = self.run_flow([1, 1])
        self.assertEqual(trace, ['check-1', 'check-2', 'unmount', 'unmount',
                                 'mkfs', 'fsck', 'mount', 'library'])
        self.assertEqual(ui.confirmations, 2)
        self.assertTrue(any('GAME CARD READY' in text for text in ui.messages))

    def test_b_button_cancels_warning(self):
        ui = FakeUI([])
        ui.action = lambda: 'back'
        self.assertFalse(UI.confirm(ui, 'Erase second card?'))
        self.assertEqual(ui.confirmations, 0)


if __name__ == '__main__':
    unittest.main()

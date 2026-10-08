#!/usr/bin/env python3
"""Exercise lid shutdown safety without shutting down the test machine."""
import fcntl
import importlib.machinery
import importlib.util
from pathlib import Path
import struct
import tempfile
import zlib
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-lid-shutdown'
loader = importlib.machinery.SourceFileLoader('lid_shutdown', str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
lid = importlib.util.module_from_spec(spec)
loader.exec_module(lid)


class TimerTests(unittest.TestCase):
    def test_deadline(self):
        for minutes in (15, 30, 60):
            timer = lid.LidTimer()
            self.assertFalse(timer.expired(True, minutes, 100))
            self.assertFalse(timer.expired(True, minutes, 100 + minutes * 60 - 1))
            self.assertTrue(timer.expired(True, minutes, 100 + minutes * 60))

    def test_off_open_unknown_and_setting_change_cancel(self):
        for closed, minutes in ((False, 15), (None, 15), (True, 0), (True, 30)):
            timer = lid.LidTimer()
            timer.expired(True, 15, 0)
            self.assertFalse(timer.expired(closed, minutes, 899))
            self.assertFalse(timer.expired(True, 15, 900))
            self.assertTrue(timer.expired(True, 15, 1800))

    def test_restart_has_no_old_deadline(self):
        self.assertFalse(lid.LidTimer().expired(True, 15, 100000))

    def test_config_is_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'system.cfg'
            self.assertEqual(lid.read_minutes(config), 0)
            for value, expected in (('', 0), ('bad', 0), ('-1', 0), ('1', 0), ('15', 15), ('30', 30), ('60', 60)):
                config.write_text('#' + lid.KEY + '=15\n' + lid.KEY + '=' + value + '\n')
                self.assertEqual(lid.read_minutes(config), expected)

    def test_update_lock_checks_owner_not_presence(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / 'update.lock'
            self.assertFalse(lid.update_busy(lock))
            with lock.open('w') as held:
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertTrue(lid.update_busy(lock))
            self.assertFalse(lid.update_busy(lock))

    def test_brief_opening_cancels_even_if_currently_closed(self):
        sensor = lid.LidSensor()
        sensor.fd = 123
        events = struct.pack('@llHHi', 0, 0, 5, 0, 0) + struct.pack('@llHHi', 0, 1, 5, 0, 1)

        def closed_bitmap(fd, request, bitmap, mutate):
            self.assertEqual(request, 0x8004451b)
            bitmap[0] = 1

        with patch.object(lid.os, 'read', side_effect=[events, BlockingIOError()]), patch.object(lid.fcntl, 'ioctl', side_effect=closed_bitmap):
            self.assertFalse(sensor.closed())
        with patch.object(lid.os, 'read', side_effect=BlockingIOError()), patch.object(lid.fcntl, 'ioctl', side_effect=closed_bitmap):
            self.assertTrue(sensor.closed())

    def test_disconnected_sensor_is_unknown(self):
        sensor = lid.LidSensor()
        sensor.fd = 123
        with patch.object(lid.os, 'read', return_value=b''), patch.object(lid.os, 'close') as close:
            self.assertIsNone(sensor.closed())
            close.assert_called_once_with(123)
            self.assertIsNone(sensor.fd)


class ShutdownTests(unittest.TestCase):
    def setUp(self):
        self.update = patch.object(lid, 'update_busy', return_value=False)
        self.update.start()
        self.addCleanup(self.update.stop)
        self.frontend = patch.object(lid, 'frontend_request')
        self.request = self.frontend.start()
        self.addCleanup(self.frontend.stop)
        self.retroarch = patch.object(lid, 'retroarch_running', return_value=False)
        self.running = self.retroarch.start()
        self.addCleanup(self.retroarch.stop)

    def test_normal_shutdown_only_after_frontend_idle(self):
        self.request.side_effect = [(201, b'{"msg":"NO GAME RUNNING"}'), (200, b'')]
        self.assertEqual(lid.Shutdown().attempt(), 'Shutdown requested')
        self.assertEqual([call.args[0] for call in self.request.call_args_list], ['/runningGame', '/shutdown'])

    def test_active_tool_or_unsupported_game_waits(self):
        self.request.return_value = (200, b'{"name":"Format card"}')
        self.assertIn('Waiting', lid.Shutdown().attempt())
        self.request.assert_called_once_with('/runningGame')

    def test_update_inhibits_all_actions(self):
        with patch.object(lid, 'update_busy', return_value=True):
            self.assertIn('update', lid.Shutdown().attempt())
        self.request.assert_not_called()

    def test_cancel_before_shutdown(self):
        self.request.return_value = (201, b'{"msg":"NO GAME RUNNING"}')
        self.assertEqual(lid.Shutdown().attempt(lambda: False), 'Lid timer cancelled')
        self.request.assert_called_once_with('/runningGame')

    def test_update_starting_during_frontend_check_defers(self):
        self.request.return_value = (201, b'{"msg":"NO GAME RUNNING"}')
        with patch.object(lid, 'update_busy', side_effect=[False, True]):
            self.assertIn('update', lid.Shutdown().attempt())
        self.request.assert_called_once_with('/runningGame')

    def test_bad_or_unreachable_frontend_never_powers_off(self):
        for reply in ((403, b''), (201, b'bad json'), (201, b'[]'), (500, b'')):
            self.request.reset_mock()
            self.request.return_value = reply
            self.assertIn('Waiting', lid.Shutdown().attempt())
            self.request.assert_called_once_with('/runningGame')
        self.request.side_effect = OSError('offline')
        self.assertIn('Waiting', lid.Shutdown().attempt())

    def test_retroarch_saving_blocks_shutdown_even_if_frontend_idle(self):
        self.request.return_value = (201, b'{"msg":"NO GAME RUNNING"}')
        self.running.return_value = True
        self.assertIn('saving', lid.Shutdown().attempt())
        self.request.assert_called_once_with('/runningGame')


class SaveShutdownTests(unittest.TestCase):
    def setUp(self):
        for name, value in [('update_busy', False), ('retroarch_running', True)]:
            mock = patch.object(lid, name, return_value=value)
            active = mock.start()
            if name == 'retroarch_running': self.running = active
            self.addCleanup(mock.stop)
        frontend = patch.object(lid, 'frontend_request')
        self.request = frontend.start()
        self.addCleanup(frontend.stop)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'Crystal.state.auto'
        self.session = ('100', '200', str(self.path), 'gambatte,Crystal,crc32=123')
        self.running.return_value = True
        self.request.return_value = (200, b'{"name":"Game"}')
        for name, value in [('save_shutdown_enabled', True), ('retroarch_session', self.session)]:
            mock = patch.object(lid, name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        self.commands = patch.object(lid, 'retroarch_command')
        self.command = self.commands.start()
        self.addCleanup(self.commands.stop)
        sleeper = patch.object(lid.time, 'sleep')
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def write_state(self, compressed=False):
        raw = b'RASTATE\x01' + struct.pack('<4sI', b'MEM ', 4) + b'test' + b'\0'*4 + struct.pack('<4sI', b'END ', 0)
        if compressed:
            payload = zlib.compress(raw)
            raw = b'#RZIPv\x01#' + struct.pack('<IQI', 131072, len(raw), len(payload)) + payload
        self.path.write_bytes(raw)
        return raw

    def test_verified_save_then_two_quits_then_normal_shutdown(self):
        shutdown = lid.Shutdown()
        self.assertIn('requested', shutdown.attempt())
        self.command.assert_called_once_with('SAVE_STATE_SLOT -1')
        self.write_state(True)
        self.assertIn('verified', shutdown.attempt())
        self.assertIn('normally', shutdown.attempt())
        self.assertEqual([call.args[0] for call in self.command.call_args_list], ['SAVE_STATE_SLOT -1', 'QUIT', 'QUIT'])
        self.running.return_value = False
        self.request.side_effect = [(201, b'{"msg":"NO GAME RUNNING"}'), (200, b'')]
        self.assertEqual(shutdown.attempt(), 'Shutdown requested')

    def test_option_off_never_saves_or_quits(self):
        with patch.object(lid, 'save_shutdown_enabled', return_value=False):
            self.assertIn('off', lid.Shutdown().attempt())
        self.command.assert_not_called()

    def test_old_state_alone_cannot_authorize_quit(self):
        old = self.write_state()
        shutdown = lid.Shutdown()
        shutdown.attempt()
        self.assertEqual(self.path.with_name(self.path.name + '.lid-backup').read_bytes(), old)
        shutdown.attempt()
        shutdown.attempt()
        self.assertEqual(self.command.call_count, 1)
        with patch.object(lid.time, 'monotonic', return_value=shutdown.started + 31):
            self.assertIn('could not be verified', shutdown.attempt())
        self.assertTrue(shutdown.failed)

    def test_partial_save_never_quits(self):
        shutdown = lid.Shutdown()
        shutdown.attempt()
        self.path.write_bytes(b'RASTATE\x01')
        shutdown.attempt()
        shutdown.attempt()
        self.assertEqual(self.command.call_count, 1)

    def test_cancel_after_new_state_never_quits(self):
        shutdown = lid.Shutdown()
        shutdown.attempt()
        self.write_state()
        shutdown.attempt()
        self.assertIn('cancelled', shutdown.attempt(lambda: False))
        self.assertEqual(self.command.call_count, 1)

    def test_changed_game_cannot_be_quit(self):
        shutdown = lid.Shutdown()
        shutdown.attempt()
        with patch.object(lid, 'retroarch_session', return_value=('101', '201', str(self.path), 'other')):
            self.assertIn('changed', shutdown.attempt())
        self.assertEqual(self.command.call_count, 1)

    def test_complete_compressed_and_raw_states_and_truncation(self):
        for compressed in (False, True):
            raw = self.write_state(compressed)
            self.assertTrue(lid.valid_state(self.path))
            self.path.write_bytes(raw[:-1])
            self.assertFalse(lid.valid_state(self.path))

    def test_invalid_final_state_blocks_shutdown(self):
        shutdown = lid.Shutdown()
        shutdown.session = self.session
        self.path.write_bytes(b'broken')
        self.running.return_value = False
        self.request.return_value = (201, b'{"msg":"NO GAME RUNNING"}')
        self.assertIn('deferred', shutdown.attempt())
        self.request.assert_called_once_with('/runningGame')

    def test_backup_failure_never_saves(self):
        with patch.object(lid, 'backup_auto_state', side_effect=OSError('disk full')):
            self.assertIn('Waiting', lid.Shutdown().attempt())
        self.command.assert_not_called()


if __name__ == '__main__':
    unittest.main()

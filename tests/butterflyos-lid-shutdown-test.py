#!/usr/bin/env python3
"""Exercise lid shutdown safety without shutting down the test machine."""
import fcntl
import importlib.machinery
import importlib.util
from pathlib import Path
import struct
import tempfile
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

    def test_game_exit_then_frontend_shutdown(self):
        shutdown = lid.Shutdown()
        self.request.return_value = (200, b'{"name":"Game"}')
        self.running.return_value = True
        with patch.object(lid.socket, 'socket'):
            self.assertIn('normally', shutdown.attempt())
        self.running.return_value = False
        self.request.side_effect = [(201, b'{"msg":"NO GAME RUNNING"}'), (200, b'')]
        self.assertEqual(shutdown.attempt(), 'Shutdown requested')

    def test_bad_or_unreachable_frontend_never_powers_off(self):
        for reply in ((403, b''), (201, b'bad json'), (201, b'[]'), (500, b'')):
            self.request.reset_mock()
            self.request.return_value = reply
            self.assertIn('Waiting', lid.Shutdown().attempt())
            self.request.assert_called_once_with('/runningGame')
        self.request.side_effect = OSError('offline')
        self.assertIn('Waiting', lid.Shutdown().attempt())

    def test_retroarch_gets_normal_quit_once_and_no_forced_shutdown(self):
        self.request.return_value = (200, b'{"name":"Game"}')
        self.running.return_value = True
        shutdown = lid.Shutdown()
        with patch.object(lid.socket, 'socket') as socket:
            self.assertIn('normally', shutdown.attempt())
            self.assertIn('normally', shutdown.attempt())
            socket.return_value.__enter__.return_value.sendto.assert_called_once_with(b'QUIT\n', ('127.0.0.1', 55355))
            shutdown.reset()
            shutdown.attempt()
            self.assertEqual(socket.call_count, 2)
        self.assertTrue(all(call.args[0] == '/runningGame' for call in self.request.call_args_list))

    def test_retroarch_saving_blocks_shutdown_even_if_frontend_idle(self):
        self.request.return_value = (201, b'{"msg":"NO GAME RUNNING"}')
        self.running.return_value = True
        self.assertIn('saving', lid.Shutdown().attempt())
        self.request.assert_called_once_with('/runningGame')


if __name__ == '__main__':
    unittest.main()

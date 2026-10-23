#!/usr/bin/env python3
"""Exercise the actual shared SDL event reader without hardware or save files."""
import ctypes
import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import Mock, call

SOURCE = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-save-trade-sdl.py'
spec = importlib.util.spec_from_file_location('blink_input', SOURCE)
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


def event(kind, instance=7, button=0, repeat=0, key=0):
    data = bytearray(64)
    struct.pack_into('<I', data, 0, kind)
    struct.pack_into('<i', data, 8, instance)
    data[12], data[13] = button, repeat
    struct.pack_into('<i', data, 20, key)
    return bytes(data)


def frontend(events=(), raw_ids=()):
    front = ui.SDLFrontEnd.__new__(ui.SDLFrontEnd)
    front.sdl = Mock()
    front.raw_joystick_ids = set(raw_ids)
    queued = list(events)

    def poll(buffer):
        if not queued:
            return 0
        ctypes.memmove(buffer, queued.pop(0), 64)
        return 1
    front.sdl.SDL_PollEvent.side_effect = poll
    return front


class InputRegression(unittest.TestCase):
    def test_flip_press_is_one_action_in_both_event_orders(self):
        # Raw button 1 is mapped A on the Flip, but the generic fallback maps
        # it to Back. Raw button 0 has the inverse conflict.
        for mapped, raw, expected in ((ui.CONTROLLER_A, 1, ui.KEY_RETURN),
                                       (ui.CONTROLLER_B, 0, ui.KEY_ESCAPE)):
            pair = [event(ui.SDL_CONTROLLERBUTTONDOWN, button=mapped),
                    event(ui.SDL_JOYBUTTONDOWN, button=raw)]
            for events in (pair, list(reversed(pair))):
                with self.subTest(mapped=mapped, first=events[0][:4]):
                    front = frontend(events)
                    self.assertEqual(expected, front.next_key())
                    self.assertIsNone(front.next_key())

    def test_generic_joystick_keeps_buttons_and_hat(self):
        front = frontend([event(ui.SDL_JOYBUTTONDOWN, instance=9, button=0),
                          event(ui.SDL_JOYBUTTONDOWN, instance=9, button=1),
                          event(ui.SDL_JOYHATMOTION, instance=9, repeat=ui.HAT_UP)], (9,))
        self.assertEqual(ui.KEY_RETURN, front.next_key())
        self.assertEqual(ui.KEY_ESCAPE, front.next_key())
        self.assertEqual(ui.KEY_UP, front.next_key())

    def test_mapped_controller_does_not_repeat_raw_hat(self):
        front = frontend([event(ui.SDL_CONTROLLERBUTTONDOWN, button=ui.CONTROLLER_DPAD_UP),
                          event(ui.SDL_JOYHATMOTION, repeat=ui.HAT_UP)])
        self.assertEqual(ui.KEY_UP, front.next_key())
        self.assertIsNone(front.next_key())

    def test_held_keyboard_confirm_cannot_dismiss_next_screen(self):
        front = frontend([event(ui.SDL_KEYDOWN, key=ui.KEY_RETURN),
                          event(ui.SDL_KEYDOWN, repeat=1, key=ui.KEY_RETURN),
                          event(ui.SDL_KEYDOWN, key=ui.KEY_ESCAPE)])
        self.assertEqual(ui.KEY_RETURN, front.next_key())
        self.assertEqual(ui.KEY_ESCAPE, front.next_key())

    def test_only_generic_joystick_instance_accepts_raw_events(self):
        front = frontend()
        front.controllers = []
        front.sdl.SDL_NumJoysticks.return_value = 2
        front.sdl.SDL_IsGameController.side_effect = [True, False]
        front.sdl.SDL_GameControllerOpen.return_value = 101
        front.sdl.SDL_JoystickOpen.return_value = 202
        front.sdl.SDL_JoystickInstanceID.return_value = 9
        front._open_input_devices()
        self.assertEqual({9}, front.raw_joystick_ids)
        self.assertEqual([('controller', 101), ('joystick', 202)], front.controllers)

    def test_saved_mappings_load_before_flip_overrides(self):
        front = frontend()
        front.sdl.SDL_RWFromFile.return_value = 123
        front._load_controller_mappings()
        methods = [item[0] for item in front.sdl.method_calls]
        self.assertEqual(['SDL_RWFromFile', 'SDL_GameControllerAddMappingsFromRW',
                          'SDL_GameControllerAddMapping', 'SDL_GameControllerAddMapping'], methods)
        front.sdl.SDL_GameControllerAddMappingsFromRW.assert_called_once_with(123, 1)
        self.assertEqual([call(line.encode()) for line in ui.TOOL_PAD_MAPPINGS.splitlines()],
                         front.sdl.SDL_GameControllerAddMapping.call_args_list)

    def test_missing_optional_database_keeps_builtin_mappings(self):
        front = frontend()
        front.sdl.SDL_RWFromFile.return_value = None
        front._load_controller_mappings()
        front.sdl.SDL_GameControllerAddMappingsFromRW.assert_not_called()
        self.assertEqual(2, front.sdl.SDL_GameControllerAddMapping.call_count)

    def test_short_sprite_label_preserves_refresh_action(self):
        front = frontend()
        front.draw_list = Mock()
        front.draw_page('main', 0)
        self.assertIn(('Sprites', 'Refresh Sprites'), front.draw_list.call_args.args[2])
        self.assertIn(('refresh-sprites', 'Refresh Sprites'), ui.PAGES['main'][2])


if __name__ == '__main__':
    unittest.main()

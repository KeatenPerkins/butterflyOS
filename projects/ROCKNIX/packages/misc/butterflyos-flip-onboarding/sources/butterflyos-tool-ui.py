#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Shared tool menus using Butterfly Link's existing renderer and input bridge."""
import ctypes
import importlib.util
from pathlib import Path
import time


def load_python(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError('Unable to load tool component: ' + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ToolUI:
    def __init__(self, title, native_controller=False):
        self.link = load_python('butterfly_tool_renderer',
                                Path(__file__).with_name('butterflyos-save-trade-sdl.py'))
        # Bdex and Bslap use a controller-first interface. Reading SDL
        # controller events directly avoids the A/B keyboard translation in
        # gptokeyb, which reverses the Flip's face buttons for these menus.
        self.controller = (None if native_controller else
                           self.link.start_controller())
        self.frontend = None
        try:
            time.sleep(0.15)
            bridge = (not native_controller and self.controller is not None and
                      self.controller.poll() is None)
            self.frontend = self.link.SDLFrontEnd(keyboard_bridge=bridge)
            sdl = self.frontend.sdl
            sdl.SDL_SetWindowTitle.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            sdl.SDL_SetWindowTitle(self.frontend.window, title.encode('utf-8'))
        except Exception:
            self.close()
            raise

    def action(self):
        key = self.frontend.next_key()
        link = self.link
        if key in (link.KEY_RETURN, link.KEY_A, ord('A'), link.KEY_CONFIRM, ord('Z')):
            return 'select'
        if key in (link.KEY_ESCAPE, link.KEY_B, ord('B'), link.KEY_CANCEL, ord('X'), link.KEY_Q, ord('Q')):
            return 'back'
        if key in (link.KEY_UP, ord('k')):
            return 'up'
        if key in (link.KEY_DOWN, ord('j')):
            return 'down'
        return None

    def wait_for_release(self):
        """Keep a held confirm/back press from activating the next screen."""
        if self.controller is not None or self.frontend is None:
            return
        sdl = self.frontend.sdl
        get_button = sdl.SDL_GameControllerGetButton
        get_button.argtypes = [ctypes.c_void_p, ctypes.c_int]
        get_button.restype = ctypes.c_uint8
        deadline = time.monotonic() + 2.0
        neutral_since = None
        while time.monotonic() < deadline:
            sdl.SDL_PumpEvents()
            pressed = any(get_button(opened, button)
                          for kind, opened in self.frontend.controllers
                          if kind == 'controller'
                          for button in range(21))
            if pressed:
                neutral_since = None
            elif neutral_since is None:
                neutral_since = time.monotonic()
            elif time.monotonic() - neutral_since >= 0.05:
                break
            time.sleep(0.01)
        # Drop any duplicate down events queued as the button was released.
        event = ctypes.create_string_buffer(64)
        while sdl.SDL_PollEvent(event):
            pass

    def menu(self, title, items, selected=0):
        selected = min(max(0, selected), len(items) - 1)
        while True:
            self.frontend.draw_list(title, 'A Select    B Back', items, selected)
            action = self.action()
            if action == 'back':
                self.wait_for_release()
                return None
            if action == 'select':
                self.wait_for_release()
                return selected
            if action == 'up':
                selected = (selected - 1) % len(items)
            elif action == 'down':
                selected = (selected + 1) % len(items)
            if action is None:
                time.sleep(0.01)

    def message(self, title, text):
        offset = 0
        while True:
            maximum = self.frontend.draw_message(title, text, 'A / B Back', offset)
            action = self.action()
            if action in ('back', 'select'):
                self.wait_for_release()
                return
            if action == 'up':
                offset = max(0, offset - 1)
            elif action == 'down':
                offset = min(maximum, offset + 1)
            if action is None:
                time.sleep(0.01)

    def close(self):
        try:
            if self.frontend is not None:
                self.frontend.close()
        finally:
            self.link.stop_controller(self.controller)
            self.frontend = None
            self.controller = None

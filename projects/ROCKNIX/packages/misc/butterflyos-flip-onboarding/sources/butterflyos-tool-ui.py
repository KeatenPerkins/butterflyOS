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
    def __init__(self, title):
        self.link = load_python('butterfly_tool_renderer',
                                Path(__file__).with_name('butterflyos-save-trade-sdl.py'))
        self.controller = self.link.start_controller()
        self.frontend = None
        try:
            time.sleep(0.15)
            bridge = self.controller is not None and self.controller.poll() is None
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

    def menu(self, title, items, selected=0):
        selected = min(max(0, selected), len(items) - 1)
        while True:
            self.frontend.draw_list(title, 'A Select    B Back', items, selected)
            action = self.action()
            if action == 'back':
                return None
            if action == 'select':
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

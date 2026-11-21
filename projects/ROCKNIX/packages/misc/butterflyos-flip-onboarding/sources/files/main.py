#!/usr/bin/python3
"""ButterflyOS single-screen file browser."""
import ctypes as C
import os
from pathlib import Path
import signal
import struct
import time

from fileops import Files, card_roots
import sdl2 as sdl

BG = (8, 19, 38, 255)
CARD = (18, 41, 72, 255)
ACCENT = (16, 217, 255, 255)
TEXT = (235, 242, 255, 255)
MUTED = (160, 184, 212, 255)


def bind(name, result, *args):
    function = getattr(sdl._sdl, name)
    function.restype, function.argtypes = result, args
    return function


class Screen:
    def __init__(self, title):
        self.window = sdl.CreateWindow(title.encode(), sdl.WINDOWPOS_UNDEFINED,
                                      sdl.WINDOWPOS_UNDEFINED, 640, 480, sdl.WINDOW_BORDERLESS | 0x1001)
        self.renderer = sdl.CreateRenderer(self.window, -1, 1)
        if not self.window or not self.renderer:
            raise RuntimeError(sdl.error())
        width, height = C.c_int(), C.c_int()
        bind('SDL_GetRendererOutputSize', C.c_int, C.c_void_p, C.POINTER(C.c_int),
             C.POINTER(C.c_int))(self.renderer, C.byref(width), C.byref(height))
        self.scale = min(width.value / 1024, height.value / 768) or 0.625
        self.left = (width.value - 1024 * self.scale) / 2
        self.top = (height.value - 768 * self.scale) / 2
        fonts = list(Path('/usr/share/fonts').rglob('DejaVuSansCondensed.ttf'))
        fonts += list(Path('/usr/share/fonts').rglob('LiberationSans-Regular.ttf'))
        fonts += list(Path('/usr/share/fonts').rglob('NotoSansCJKsc-Regular.otf'))
        self.fonts = {n: sdl.TTF_OpenFont(os.fsencode(fonts[0]), round(n * self.scale)) for n in (22, 28, 36, 52)}

    def box(self, rect, color):
        sdl.SetRenderDrawColor(self.renderer, *color)
        sdl.RenderFillRect(self.renderer, C.byref(sdl.Rect(round(self.left + rect[0] * self.scale),
                                                     round(self.top + rect[1] * self.scale),
                                                     round(rect[2] * self.scale), round(rect[3] * self.scale))))

    def text(self, value, x, y, size=28, color=TEXT, width=950):
        value = str(value).replace('\n', ' ')
        original = value
        w, h = C.c_int(), C.c_int()
        while value:
            sdl.TTF_SizeUTF8(self.fonts[size], value.encode(errors='replace'), C.byref(w), C.byref(h))
            if w.value <= width * self.scale:
                break
            original = original[:-1]
            value = original + '…'
        surface = sdl.TTF_RenderUTF8_Blended(self.fonts[size], value.encode(errors='replace'), sdl.Color(*color))
        if surface:
            texture = sdl.CreateTextureFromSurface(self.renderer, surface)
            sdl.RenderCopy(self.renderer, texture, None, C.byref(sdl.Rect(round(self.left + x * self.scale), round(self.top + y * self.scale),
                                                              surface.contents.w, surface.contents.h)))
            sdl.DestroyTexture(texture)
            sdl.FreeSurface(surface)

    def clear(self):
        self.box((0, 0, 1024, 768), BG)

    def present(self):
        sdl.RenderPresent(self.renderer)

    def close(self):
        for font in self.fonts.values():
            sdl.TTF_CloseFont(font)
        sdl.DestroyRenderer(self.renderer)
        sdl.DestroyWindow(self.window)


class Browser:
    def __init__(self):
        os.environ['SDL_VIDEO_WAYLAND_WMCLASS'] = 'butterflyos-files'
        sdl.SetHint(sdl.HINT_VIDEO_WAYLAND_WMCLASS, b'butterflyos-files')
        sdl.SetHint(b'SDL_TOUCH_MOUSE_EVENTS', b'1')
        sdl.SetHint(b'SDL_MOUSE_TOUCH_EVENTS', b'0')
        if sdl.Init(sdl.INIT_VIDEO | sdl.INIT_EVENTS | 0x2000):
            raise RuntimeError(sdl.error())
        sdl._sdl.SDL_ShowCursor(0)
        sdl.TTF_Init()
        self.screen = Screen('ButterflyOS Files')
        self.roots = card_roots()
        self.files = Files(self.roots)
        self.path = None
        self.rows = []
        self.selected = self.offset = 0
        self.clipboard = None
        self.mode = 'browse'
        self.options = []
        self.dialog = None
        self.name = ''
        self.shift = False
        self.key = 0
        self.running = True
        self.pads = {}
        self.flip_pads = set()
        self.last_scan = 0
        self.revision = 0
        self.reload()

    def reload(self):
        if self.path is None:
            self.rows = [(label, root, True) for label, root in self.roots]
        else:
            try:
                self.rows = [(name, self.path / name, directory) for name, directory in self.files.entries(self.path)]
            except (OSError, ValueError) as error:
                self.files.message = str(error)
                self.path = None
                self.reload()
        self.selected = min(self.selected, max(0, len(self.rows) - 1))
        self.offset = max(0, min(self.offset, max(0, len(self.rows) - 6)))

    def current(self):
        return self.rows[self.selected] if self.rows else None

    def back(self):
        if self.files.busy:
            self.files.cancel.set()
        elif self.mode != 'browse':
            self.mode = 'browse'
        elif self.path is None:
            self.options = [('Close Files', 'confirm-close'), ('Keep browsing', 'cancel')]
            self.choice = 1
            self.mode = 'confirm'
        else:
            self.path = None if self.path in self.files.roots else self.path.parent
            self.selected = self.offset = 0
            self.reload()

    def open(self):
        row = self.current()
        if not row or self.files.busy:
            return
        if row[2]:
            self.path = row[1]
            self.selected = self.offset = 0
            self.reload()
        else:
            self.actions()

    def actions(self):
        if self.files.busy:
            return
        self.options = []
        row = self.current()
        if row and row[1] not in self.files.roots:
            self.options += [('Copy', 'copy'), ('Move', 'move'), ('Rename', 'rename'), ('Move to Trash', 'trash')]
        if self.path and self.clipboard:
            self.options += [('Paste here (keep both if name exists)', 'paste')]
        if self.path:
            self.options += [('New folder', 'mkdir')]
        self.options += [('Restore last delete', 'restore'), ('Cancel', 'cancel')]
        self.choice = 0
        self.mode = 'actions'

    def action(self, action):
        row = self.current()
        self.mode = 'browse'
        if action in ('copy', 'move') and row:
            self.clipboard = (row[1], action == 'move')
            self.files.message = 'Open a destination folder, then choose Paste.'
        elif action in ('rename', 'mkdir'):
            self.dialog = action
            self.name = row[0] if action == 'rename' and row else ''
            self.mode = 'keyboard'
            bind('SDL_StartTextInput', None)()
        elif action == 'trash' and row:
            self.options = [('Move selected item to Trash', 'confirm-trash'), ('Keep it', 'cancel')]
            self.choice = 1
            self.mode = 'confirm'
        elif action == 'confirm-trash' and row:
            self.files.start(self.files.trash, row[1])
        elif action == 'paste' and self.path and self.clipboard:
            source, move = self.clipboard
            self.files.start(self.files.paste, source, self.path, move)
        elif action == 'restore':
            self.files.start(self.files.restore)
        elif action == 'confirm-close':
            self.running = False

    def accept_name(self):
        row = self.current()
        try:
            self.files.name(self.name)
        except ValueError as error:
            self.files.message = str(error)
            return
        if self.dialog == 'rename' and row:
            self.files.start(self.files.rename, row[1], self.name)
        elif self.path:
            self.files.start(self.files.mkdir, self.path, self.name)
        self.mode = 'browse'

    def shift_key(self):
        self.shift = not self.shift

    def keys(self):
        letters = '1234567890qwertyuiopasdfghjkl-zxcvbnm_.'
        return (letters.upper() if self.shift else letters) + ' '

    def press(self, key):
        if self.files.busy:
            if key == 'back': self.files.cancel.set()
            return
        if key == 'back':
            self.back()
        elif self.mode == 'keyboard':
            if key == 'open': self.name += self.keys()[self.key]
            elif key == 'actions': self.name = self.name[:-1]
            elif key == 'start': self.accept_name()
            elif key == 'shift': self.shift_key()
            elif key in ('up', 'down', 'left', 'right'):
                delta = {'up': -10, 'down': 10, 'left': -1, 'right': 1}[key]
                self.key = (self.key + delta) % len(self.keys())
        elif self.mode in ('actions', 'confirm'):
            if key in ('up', 'down'):
                self.choice = (self.choice + (1 if key == 'down' else -1)) % len(self.options)
            elif key == 'open': self.action(self.options[self.choice][1])
        elif key == 'open': self.open()
        elif key == 'actions': self.actions()
        elif key in ('up', 'down', 'left', 'right'):
            delta = {'up': -1, 'down': 1, 'left': -6, 'right': 6}[key]
            self.selected = max(0, min(len(self.rows) - 1, self.selected + delta))
            self.offset = max(0, min(self.offset, self.selected))
            if self.selected >= self.offset + 6: self.offset = self.selected - 5

    def draw(self):
        bottom = self.screen
        bottom.clear()
        bottom.text('Files' if self.path is None else self.path.name or str(self.path), 32, 25, 36, ACCENT, 950)
        bottom.text(str(self.path) if self.path else 'Select a location', 32, 78, 22, MUTED, 950)
        if self.files.busy:
            bottom.text('Working…', 50, 230, 52)
            bottom.text('Your original stays until the operation completes.', 50, 330, 28)
        elif self.mode == 'keyboard':
            bottom.text('Rename' if self.dialog == 'rename' else 'New folder', 42, 125, 28)
            bottom.box((32, 170, 960, 48), CARD)
            bottom.text(self.name + '|', 42, 175)
            for index, key in enumerate(self.keys()):
                x, y = 42 + index % 10 * 94, 230 + index // 10 * 70
                bottom.box((x, y, 86, 62), ACCENT if index == self.key else CARD)
                bottom.text(key if key != ' ' else '␣', x + 30, y + 12, 28, BG if index == self.key else TEXT)
            for x, label in ((32, 'Shift'), (352, 'Space'), (672, 'Delete')):
                bottom.box((x, 540, 312, 70), CARD); bottom.text(label, x + 85, 558)
        elif self.mode in ('actions', 'confirm'):
            for index, (label, _) in enumerate(self.options):
                y = 120 + index * 56
                bottom.box((32, y, 960, 50), (25, 74, 106, 255) if index == self.choice else CARD)
                bottom.text(label, 54, y + 15)
        else:
            for index, (name, _, directory) in enumerate(self.rows[self.offset:self.offset + 6], self.offset):
                y = 120 + (index - self.offset) * 72
                bottom.box((32, y, 930, 66), (25, 74, 106, 255) if index == self.selected else CARD)
                bottom.text('DIR' if directory else 'FILE', 48, y + 20, 22, ACCENT, 75)
                bottom.text(name, 138, y + 16, 28, width=800)
            if not self.rows: bottom.text('This folder is empty.', 50, 220, 28, MUTED)
            if len(self.rows) > 6:
                height = max(24, 432 * 6 // len(self.rows))
                y = 120 + int((432 - height) * self.offset / max(1, len(self.rows) - 6))
                bottom.box((978, 120, 8, 432), CARD)
                bottom.box((978, y, 8, height), ACCENT)
        bottom.text(self.files.message, 32, 594, 22, MUTED, 950)
        if self.clipboard and self.mode == 'browse':
            source, move = self.clipboard
            bottom.text(('Move: ' if move else 'Copy: ') + source.name, 32, 628, 22, ACCENT, 950)
        if self.files.busy:
            hint = f'{self.files.bytes / 1048576:.1f} MB processed    B Cancel'
        elif self.mode == 'keyboard':
            hint = 'A Type    Y Shift    X Delete    Start Save    B Back'
        elif self.mode == 'browse':
            hint = 'A Open    X Actions    B Back'
        else:
            hint = 'A Select    B Back'
        bottom.box((32, 684, 960, 60), CARD)
        bottom.text(hint, 54, 700, 28, width=920)
        bottom.present()

    def run(self):
        event = sdl.Event()
        last = None
        controllers = bind('SDL_NumJoysticks', C.c_int)
        open_pad = bind('SDL_GameControllerOpen', C.c_void_p, C.c_int)
        pad_name = bind('SDL_GameControllerName', C.c_char_p, C.c_void_p)
        attached = bind('SDL_GameControllerGetAttached', C.c_int, C.c_void_p)
        close_pad = bind('SDL_GameControllerClose', None, C.c_void_p)
        instance = bind('SDL_JoystickGetDeviceInstanceID', C.c_int, C.c_int)
        try:
            while self.running:
                now = time.monotonic()
                if now - self.last_scan > 1:
                    self.last_scan = now
                    for key, pad in list(self.pads.items()):
                        if not attached(pad):
                            close_pad(self.pads.pop(key))
                            self.flip_pads.discard(key)
                    for index in range(controllers()):
                        key = instance(index)
                        if key not in self.pads:
                            pad = open_pad(index)
                            if pad:
                                self.pads[key] = pad
                                if pad_name(pad) == b'retrogame_joypad':
                                    self.flip_pads.add(key)
                if self.files.revision != self.revision:
                    self.revision = self.files.revision
                    if self.clipboard and self.clipboard[1] and not self.clipboard[0].exists():
                        self.clipboard = None
                    self.reload()
                while sdl.PollEvent(C.byref(event)):
                    raw = bytes(event.data)
                    if event.type == sdl.EVENT_QUIT: self.back()
                    elif event.type == 0x200:
                        last = None
                    elif event.type == 0x651:
                        controller = struct.unpack_from('<i', raw, 8)[0]
                        button = raw[12]
                        if controller in self.flip_pads and button in (0, 1):
                            button ^= 1
                        key = {0: 'open', 1: 'back', 2: 'actions', 3: 'shift', 6: 'start',
                               11: 'up', 12: 'down', 13: 'left', 14: 'right'}.get(button)
                        if key: self.press(key)
                    elif event.type == 0x303 and self.mode == 'keyboard':
                        self.name += raw[12:44].split(b'\0')[0].decode(errors='replace')
                    elif event.type == 0x300:
                        symbol = struct.unpack_from('<i', raw, 20)[0]
                        if self.mode == 'keyboard':
                            if symbol == 13: self.accept_name()
                            elif symbol == 8: self.name = self.name[:-1]
                            elif symbol == 27: self.back()
                            continue
                        key = {13: 'open', 27: 'back', 120: 'actions',
                               1073741906: 'up', 1073741905: 'down',
                               1073741904: 'left', 1073741903: 'right'}.get(symbol)
                        if key: self.press(key)
                state = (self.path, self.mode, self.selected, self.offset, self.name, self.shift, self.key,
                         getattr(self, 'choice', 0), self.files.busy, self.files.bytes // 1048576, self.files.message, self.revision, self.clipboard)
                if state != last:
                    self.draw()
                    last = state
                time.sleep(.02)
        finally:
            if self.files.busy:
                self.files.cancel.set()
                while self.files.busy: time.sleep(.05)
            for pad in self.pads.values(): close_pad(pad)
            self.screen.close()
            sdl.TTF_Quit(); sdl.Quit()


if __name__ == '__main__':
    browser = Browser()
    signal.signal(signal.SIGTERM, lambda *_: setattr(browser, 'running', False))
    signal.signal(signal.SIGINT, lambda *_: setattr(browser, 'running', False))
    browser.run()

#!/usr/bin/env python3
"""Desktop SDL preview of the Butterfly Link UI.

This is a visual/input prototype only. It never opens or changes ROMs or save
files.  It uses Pillow for text rasterization and the host SDL2 runtime for a
window, so it can preview large fonts without rebuilding or flashing the OS.

Examples:
  python3 tools/butterfly-link-sdl-preview.py
  python3 tools/butterfly-link-sdl-preview.py --font-scale 3

Keys: Up/Down, Enter or A to select, Escape or B to go back, Q to quit.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_W, BASE_H = 640, 480
SDL_INIT_VIDEO = 0x00000020
SDL_WINDOW_SHOWN = 0x00000004
SDL_RENDERER_ACCELERATED = 0x00000002
SDL_RENDERER_PRESENTVSYNC = 0x00000004
SDL_PIXELFORMAT_ABGR8888 = 0x16762004
SDL_QUIT = 0x100
SDL_KEYDOWN = 0x300

# SDL_Keycode values used by the preview.
KEY_RETURN = 13
KEY_ESCAPE = 27
KEY_A = ord("a")
KEY_B = ord("b")
KEY_Q = ord("q")
KEY_UP = 1073741906
KEY_DOWN = 1073741905


PAGES = {
    "main": ("BUTTERFLY LINK", "Choose an action.  A Select   B Back", [
        ("local", "Local transfer"),
        ("remote", "Another ButterflyOS device"),
        ("inspect", "Inspect a save  -  read-only"),
        ("prepare", "Resume prepared transfer"),
        ("commit", "Commit prepared transfer"),
        ("discard", "Discard prepared transfer"),
        ("about", "How Butterfly Link works"),
        ("close", "Back to Tools"),
    ]),
    "local": ("LOCAL TRANSFER", "Choose a generation.  A Select   B Back", [
        ("gen1", "Generation 1  -  Red / Blue / Yellow"),
        ("gen2", "Generation 2  -  Gold / Silver / Crystal"),
        ("gen3", "Generation 3  -  Ruby / Sapphire / Emerald / FRLG"),
    ]),
    "gen3": ("GENERATION 3", "Choose how to move a Pokemon.  A Select   B Back", [
        ("swap", "Trade / Swap  -  exchange two Pokemon"),
        ("copy", "Copy  -  leave the source unchanged"),
    ]),
    "copy": ("LOCAL COPY  -  GENERATION 3", "Choose the source save.  A Select   B Back", [
        ("ruby", "OS Card  |  Ruby  |  ZZZ  |  PC: 3"),
        ("emerald", "Game Card  |  Emerald  |  KEATEN  |  PC: 5"),
        ("back", "Back"),
    ]),
}


class SDL:
    def __init__(self) -> None:
        name = ctypes.util.find_library("SDL2") or "libSDL2-2.0.so.0"
        self.lib = ctypes.CDLL(name)
        L = self.lib
        L.SDL_Init.argtypes = [ctypes.c_uint32]
        L.SDL_Init.restype = ctypes.c_int
        L.SDL_Quit.argtypes = []
        L.SDL_CreateWindow.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        L.SDL_CreateWindow.restype = ctypes.c_void_p
        L.SDL_DestroyWindow.argtypes = [ctypes.c_void_p]
        L.SDL_CreateRenderer.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint32]
        L.SDL_CreateRenderer.restype = ctypes.c_void_p
        L.SDL_DestroyRenderer.argtypes = [ctypes.c_void_p]
        L.SDL_CreateTexture.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        L.SDL_CreateTexture.restype = ctypes.c_void_p
        L.SDL_DestroyTexture.argtypes = [ctypes.c_void_p]
        L.SDL_UpdateTexture.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
        L.SDL_RenderClear.argtypes = [ctypes.c_void_p]
        L.SDL_RenderCopy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        L.SDL_RenderPresent.argtypes = [ctypes.c_void_p]
        L.SDL_PollEvent.argtypes = [ctypes.c_void_p]
        L.SDL_PollEvent.restype = ctypes.c_int
        L.SDL_SetHint.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

        if L.SDL_Init(SDL_INIT_VIDEO) != 0:
            raise RuntimeError("SDL2 could not initialize")
        L.SDL_SetHint(b"SDL_RENDER_SCALE_QUALITY", b"linear")
        self.window = L.SDL_CreateWindow(b"Butterfly Link UI Preview", 0x2FFF0000, 0x2FFF0000, 1280, 960, SDL_WINDOW_SHOWN)
        if not self.window:
            L.SDL_Quit()
            raise RuntimeError("SDL2 could not create a window")
        self.renderer = L.SDL_CreateRenderer(self.window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
        self.texture = None

    def present(self, image: Image.Image) -> None:
        raw = image.convert("RGBA").tobytes()
        L = self.lib
        if self.texture:
            L.SDL_DestroyTexture(self.texture)
        self.texture = L.SDL_CreateTexture(self.renderer, SDL_PIXELFORMAT_ABGR8888, 1, image.width, image.height)
        pixels = ctypes.create_string_buffer(raw)
        L.SDL_UpdateTexture(self.texture, None, pixels, image.width * 4)
        L.SDL_RenderClear(self.renderer)
        L.SDL_RenderCopy(self.renderer, self.texture, None, None)
        L.SDL_RenderPresent(self.renderer)

    def key(self) -> int | None:
        event = ctypes.create_string_buffer(64)
        while self.lib.SDL_PollEvent(event):
            kind = struct.unpack_from("<I", event.raw, 0)[0]
            if kind == SDL_QUIT:
                return KEY_Q
            if kind == SDL_KEYDOWN:
                return struct.unpack_from("<i", event.raw, 20)[0]
        return None

    def close(self) -> None:
        if self.texture:
            self.lib.SDL_DestroyTexture(self.texture)
        self.lib.SDL_DestroyRenderer(self.renderer)
        self.lib.SDL_DestroyWindow(self.window)
        self.lib.SDL_Quit()


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=max(10, size))


def draw_page(page: str, selected: int, scale: int, regular: str, bold: str) -> Image.Image:
    title, prompt, items = PAGES[page]
    width, height = BASE_W * scale, BASE_H * scale
    image = Image.new("RGB", (width, height), (6, 9, 22))
    draw = ImageDraw.Draw(image)
    def xy(v: int) -> int:
        return v * scale

    # Deep navy panel with a restrained cyan/blue ButterflyOS border.
    draw.rounded_rectangle((xy(10), xy(10), xy(630), xy(470)), radius=xy(10), fill=(10, 15, 34), outline=(38, 129, 190), width=max(2, xy(2)))
    draw.text((width // 2, xy(22)), title, font=font(bold, 16 * scale), fill=(36, 226, 224), anchor="ma")
    draw.text((xy(24), xy(66)), prompt, font=font(regular, 11 * scale), fill=(177, 196, 214))
    draw.line((xy(22), xy(93), xy(618), xy(93)), fill=(38, 80, 140), width=max(2, xy(1)))

    top, bottom = 112, 416
    draw.rounded_rectangle((xy(22), xy(top), xy(618), xy(bottom)), radius=xy(5), fill=(5, 8, 18), outline=(35, 88, 160), width=max(2, xy(2)))
    row_h = 34
    for index, (tag, label) in enumerate(items):
        y = top + 14 + index * row_h
        if y + row_h > bottom - 6:
            break
        active = index == selected
        if active:
            draw.rounded_rectangle((xy(30), xy(y - 4), xy(610), xy(y + row_h - 7)), radius=xy(4), fill=(24, 83, 153))
        color = (255, 255, 255) if active else (222, 231, 242)
        tag_color = (255, 255, 255) if active else (36, 226, 224)
        draw.text((xy(42), xy(y)), tag.upper(), font=font(bold, 11 * scale), fill=tag_color)
        draw.text((xy(145), xy(y)), label, font=font(regular, 11 * scale), fill=color)

    footer = "UP/DOWN Navigate    A / ENTER Select    B / ESC Back    Q Quit"
    draw.text((width // 2, xy(442)), footer, font=font(regular, 10 * scale), fill=(150, 176, 202), anchor="ma")
    return image


def run(scale: int) -> None:
    regular = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"
    bold = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
    sdl = SDL()
    page, selected = "main", 0
    try:
        while True:
            sdl.present(draw_page(page, selected, scale, regular, bold))
            key = sdl.key()
            if key is None:
                continue
            items = PAGES[page][2]
            if key in (KEY_UP, ord("k")):
                selected = (selected - 1) % len(items)
            elif key in (KEY_DOWN, ord("j")):
                selected = (selected + 1) % len(items)
            elif key in (KEY_Q, ord("Q")):
                return
            elif key in (KEY_ESCAPE, KEY_B, ord("B")):
                if page == "main":
                    return
                page, selected = "main", 0
            elif key in (KEY_RETURN, KEY_A, ord("A")):
                choice = items[selected][0]
                if choice in ("close", "back"):
                    if page == "main":
                        return
                    page, selected = "main", 0
                elif choice in PAGES:
                    page, selected = choice, 0
                else:
                    # Preview pages intentionally do not touch real files.
                    page, selected = "copy", 0
    finally:
        sdl.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--font-scale", type=int, default=3, choices=range(1, 6))
    args = parser.parse_args()
    try:
        run(args.font_scale)
    except (RuntimeError, OSError) as exc:
        print(f"Butterfly Link SDL preview unavailable: {exc}", file=sys.stderr)
        sys.exit(1)

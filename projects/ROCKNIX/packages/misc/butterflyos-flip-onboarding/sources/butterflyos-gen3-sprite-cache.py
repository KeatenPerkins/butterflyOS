#!/usr/bin/env python3
"""Extract and cache front/shiny Gen III Pokemon sprites from a user ROM.

The ROM remains the source of the artwork.  ButterflyOS ships only this
extractor; generated PNGs live in writable user storage and are keyed by the
ROM SHA-256, so a different ROM (including a ROM hack) cannot reuse stale
sprites accidentally.
"""

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path


EXTRACTOR_VERSION = "1"
DEFAULT_CACHE_ROOT = "/storage/.config/butterflyos/save-trade/sprite-cache"
GBA_BASE = 0x08000000

# These are the English retail layouts used by the supported Gen III games.
# The tables contain pointers to compressed 4bpp graphics/palettes.  FireRed
# and LeafGreen share the same table shape as Ruby/Sapphire.  Emerald's front
# and palette tables are included as well; its front images can be taller due
# to the game's two-frame animation data.
ROM_LAYOUTS = {
    "AXVE": {
        "title": "Pokemon Ruby",
        "front": 0x1E8354,
        "palette": 0x1EA5B4,
        "shiny_palette": 0x1EB374,
        "count": 440,
    },
    "AXPE": {
        "title": "Pokemon Sapphire",
        "front": 0x1E8354,
        "palette": 0x1EA5B4,
        "shiny_palette": 0x1EB374,
        "count": 440,
    },
    "BPRE": {
        "title": "Pokemon FireRed",
        "front": 0x2350AC,
        "palette": 0x23730C,
        "shiny_palette": 0x2380CC,
        "count": 440,
    },
    "BPGE": {
        "title": "Pokemon LeafGreen",
        "front": 0x235088,
        "palette": 0x2372E8,
        "shiny_palette": 0x2380A8,
        "count": 440,
    },
    "BPEE": {
        "title": "Pokemon Emerald",
        # Emerald's normal and shiny palette tables are adjacent to one
        # another.  Its front table contains the taller animated frame data.
        "front": 0x30A18C,
        "palette": 0x303678,
        "shiny_palette": 0x304288,
        "count": 440,
    },
}

# Revision-2 Ruby/Sapphire moved the asset tables while keeping the same ROM
# header code.  The revision byte at 0xBC distinguishes these retail dumps.
REVISION_2_LAYOUTS = {
    "AXVE": {
        "title": "Pokemon Ruby (revision 2)",
        "front": 0x1E836C,
        "palette": 0x1EA5CC,
        "shiny_palette": 0x1EB1DC,
        "count": 440,
    },
    "AXPE": {
        "title": "Pokemon Sapphire (revision 2)",
        "front": 0x1E82FC,
        "palette": 0x1EA55C,
        "shiny_palette": 0x1EB16C,
        "count": 440,
    },
}

REVISION_1_LAYOUTS = {
    "BPRE": {
        "title": "Pokemon FireRed (revision 1)",
        "front": 0x23511C,
        "palette": 0x23737C,
        "shiny_palette": 0x237F8C,
        "count": 440,
    },
}


class CacheError(Exception):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_pointer(data, table, index):
    offset = table + index * 8
    if offset < 0 or offset + 4 > len(data):
        raise CacheError("pointer-table-out-of-range")
    pointer = struct.unpack_from("<I", data, offset)[0]
    if pointer < GBA_BASE:
        raise CacheError("invalid-gba-pointer")
    rom_offset = pointer - GBA_BASE
    if rom_offset >= len(data):
        raise CacheError("pointer-out-of-range")
    return rom_offset


def lz77(data, offset):
    if offset + 4 > len(data) or data[offset] != 0x10:
        raise CacheError("sprite-data-is-not-gba-lz77")
    size = data[offset + 1] | (data[offset + 2] << 8) | (data[offset + 3] << 16)
    source = offset + 4
    output = bytearray()
    while len(output) < size:
        if source >= len(data):
            raise CacheError("truncated-lz77-flags")
        flags = data[source]
        source += 1
        for bit in range(7, -1, -1):
            if len(output) >= size:
                break
            if flags & (1 << bit):
                if source + 2 > len(data):
                    raise CacheError("truncated-lz77-reference")
                first, second = data[source], data[source + 1]
                source += 2
                length = (first >> 4) + 3
                distance = ((first & 0x0F) << 8 | second) + 1
                if distance > len(output):
                    raise CacheError("invalid-lz77-distance")
                for _ in range(length):
                    if len(output) >= size:
                        break
                    output.append(output[-distance])
            else:
                if source >= len(data):
                    raise CacheError("truncated-lz77-literal")
                output.append(data[source])
                source += 1
    return bytes(output)


def untile(data):
    # Gen III battle graphics are 4bpp tiles arranged in 64-pixel rows.  An
    # Emerald frame can be 128 pixels high; deriving height from the decoded
    # byte count keeps both layouts correct.
    if len(data) == 0 or len(data) % 32:
        raise CacheError("unexpected-sprite-size")
    width = 64
    height = (len(data) * 2) // width
    pixels = bytearray(width * height)
    source = 0
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    value = data[source]
                    source += 1
                    row = (tile_y + y) * width + tile_x + x
                    pixels[row] = value & 0x0F
                    pixels[row + 1] = value >> 4
    return width, height, pixels


def decode_palette(data, offset):
    raw = lz77(data, offset)
    if len(raw) < 32:
        raise CacheError("unexpected-palette-size")
    colors = []
    for index in range(16):
        value = struct.unpack_from("<H", raw, index * 2)[0]
        red = (value & 0x1F) * 255 // 31
        green = ((value >> 5) & 0x1F) * 255 // 31
        blue = ((value >> 10) & 0x1F) * 255 // 31
        # Palette index zero is the transparent background in these assets.
        alpha = 0 if index == 0 else 255
        colors.append((red, green, blue, alpha))
    return colors


def png_chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))


def write_png(path, width, height, pixels, palette):
    rows = bytearray()
    for y in range(height):
        rows.append(0)  # PNG filter type: none
        for x in range(width):
            rows.extend(palette[pixels[y * width + x]])
    payload = (b"\x89PNG\r\n\x1a\n" +
               png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
               png_chunk(b"IDAT", zlib.compress(bytes(rows), 9)) +
               png_chunk(b"IEND", b""))
    with open(path, "wb") as stream:
        stream.write(payload)


def write_front_frames(directory, filename, width, height, pixels, palette):
    """Write the first frame as the UI sprite and preserve extra frames."""
    frame_height = 64 if height >= 64 and height % 64 == 0 else height
    frame_count = height // frame_height
    for frame in range(frame_count):
        start = frame * width * frame_height
        frame_pixels = pixels[start:start + width * frame_height]
        suffix = "" if frame == 0 else "-frame%d" % (frame + 1)
        write_png(directory / (Path(filename).stem + suffix + ".png"),
                  width, frame_height, frame_pixels, palette)
    return frame_count


def read_rom_info(path):
    data = Path(path).read_bytes()
    if len(data) < 0xB0:
        raise CacheError("rom-too-small")
    try:
        code = data[0xAC:0xB0].decode("ascii")
    except UnicodeDecodeError as error:
        raise CacheError("invalid-game-code") from error
    revision = data[0xBC]
    if revision == 2:
        layout = REVISION_2_LAYOUTS.get(code)
    elif revision == 1:
        layout = REVISION_1_LAYOUTS.get(code, ROM_LAYOUTS.get(code))
    else:
        layout = ROM_LAYOUTS.get(code)
    if layout is None:
        raise CacheError("unsupported-gen3-game-code:" + code)
    return data, code, revision, layout


def cache_rom(rom_path, cache_root, force=False):
    rom_path = os.path.abspath(rom_path)
    if not os.path.isfile(rom_path):
        raise CacheError("rom-not-found")
    data, code, revision, layout = read_rom_info(rom_path)
    digest = sha256_file(rom_path)
    destination = Path(cache_root) / digest
    manifest_path = destination / "manifest.json"
    if not force and manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
            if (manifest.get("rom_sha256") == digest and
                    manifest.get("extractor_version") == EXTRACTOR_VERSION):
                print("cache_hit=1")
                print("cache_dir=" + str(destination))
                return destination
        except (OSError, ValueError):
            pass

    Path(cache_root).mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".sprite-cache-", dir=cache_root))
    try:
        front_dir = temporary / "front"
        shiny_dir = temporary / "front-shiny"
        front_dir.mkdir()
        shiny_dir.mkdir()
        front_table = layout["front"]
        palette_table = layout["palette"]
        shiny_table = layout["shiny_palette"]
        count = layout["count"]
        for species in range(count):
            front_pointer = read_pointer(data, front_table, species)
            palette_pointer = read_pointer(data, palette_table, species)
            shiny_pointer = read_pointer(data, shiny_table, species)
            width, height, pixels = untile(lz77(data, front_pointer))
            palette = decode_palette(data, palette_pointer)
            shiny_palette = decode_palette(data, shiny_pointer)
            filename = "%03d.png" % species
            frame_count = write_front_frames(front_dir, filename, width, height, pixels, palette)
            write_front_frames(shiny_dir, filename, width, height, pixels, shiny_palette)

        manifest = {
            "format": "butterflyos-gen3-sprite-cache",
            "format_version": 1,
            "extractor_version": EXTRACTOR_VERSION,
            "rom_sha256": digest,
            "rom_filename": os.path.basename(rom_path),
            "game_code": code,
            "rom_revision": revision,
            "game_title": layout["title"],
            "species_count": count,
            "variants": ["front", "front-shiny"],
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        }
        (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        if destination.exists():
            shutil.rmtree(destination)
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    print("cache_hit=0")
    print("cache_dir=" + str(destination))
    print("game=" + layout["title"])
    print("species_count=" + str(count))
    return destination


def main(argv):
    parser = argparse.ArgumentParser(description="Cache Gen III sprites from a user-owned ROM")
    parser.add_argument("rom", help="path to a .gba ROM")
    parser.add_argument("--cache-root", default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        cache_rom(args.rom, args.cache_root, args.force)
    except (OSError, CacheError) as error:
        print("error=" + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

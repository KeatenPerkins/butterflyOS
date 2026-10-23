#!/usr/bin/env python3
"""Extract and cache front/shiny Gen III Pokemon sprites from a user ROM.

The ROM remains the source of the artwork.  ButterflyOS ships only this
extractor; generated PNGs live in writable user storage and are keyed by the
ROM SHA-256, so a different ROM (including a ROM hack) cannot reuse stale
sprites accidentally.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import sys
import tempfile
import zlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path


EXTRACTOR_VERSION = "6"
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
        "shiny_palette": 0x304438,
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
        "shiny_palette": 0x1EB38C,
        "count": 440,
    },
    "AXPE": {
        "title": "Pokemon Sapphire (revision 2)",
        "front": 0x1E82FC,
        "palette": 0x1EA55C,
        "shiny_palette": 0x1EB31C,
        "count": 440,
    },
}

REVISION_1_LAYOUTS = {
    "BPGE": {
        "title": "Pokemon LeafGreen (revision 1)",
        "front": 0x2350F8,
        "palette": 0x237358,
        "shiny_palette": 0x238118,
        "count": 440,
    },
    "BPRE": {
        "title": "Pokemon FireRed (revision 1)",
        "front": 0x23511C,
        "palette": 0x23737C,
        "shiny_palette": 0x23813C,
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
    spec = importlib.util.spec_from_file_location('rom_filter', Path(__file__).with_name('butterflyos_rom_filter.py'))
    rom_filter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rom_filter)
    try:
        data = rom_filter.read_gen3_rom(path)
    except (OSError, ValueError, zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError) as error:
        raise CacheError(str(error)) from error
    if len(data) < 0xC0:
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


def decode_name(raw):
    # The five POKEBLOCK logo glyphs render one English word.
    raw = raw.replace(bytes((0x55, 0x56, 0x57, 0x58, 0x59)),
                      bytes((0xCA, 0xC9, 0xC5, 0x1B, 0xBC, 0xC6, 0xC9, 0xBD, 0xC5)))
    end = raw.find(b"\xff")
    if end < 1:
        return None
    result = []
    for byte in raw[:end]:
        if 0xBB <= byte <= 0xD4:
            result.append(chr(ord('A') + byte - 0xBB))
        elif 0xD5 <= byte <= 0xEE:
            result.append(chr(ord('a') + byte - 0xD5))
        elif 0xA1 <= byte <= 0xAA:
            result.append(chr(ord('0') + byte - 0xA1))
        elif byte in (0x00, 0x1B, 0xAC, 0xAD, 0xAE, 0xB4, 0xB5, 0xB6, 0xBA, 0xAB, 0xB8, 0xB9, 0x5C, 0x5D, 0xF0, 0x36, 0x53, 0x54):
            result.append({0x00: ' ', 0x1B: 'é', 0xAC: '?', 0xAD: '.', 0xAE: '-', 0xB4: "'", 0xB5: '♂', 0xB6: '♀', 0xBA: '/', 0xAB: '!', 0xB8: ',', 0xB9: '×', 0x5C: '(', 0x5D: ')', 0xF0: ':', 0x36: ';', 0x53: '<', 0x54: '>'}[byte])
        else:
            return None
    return ''.join(result).strip() or None


def move_names(data):
    """Locate the English fixed-width move-name table in the user's ROM.

    Gen III uses 13-byte entries (12 glyphs plus terminator), IDs 1..354.
    Encoding/table shape reference: pret/pokeemerald charmap.txt and
    src/data/text/move_names.h. Validate a whole table rather than using ROM
    offsets that change between game families and revisions.
    """
    # POUND in the English game encoding, with its end marker.
    first = bytes((0xCA, 0xC9, 0xCF, 0xC8, 0xBE, 0xFF))
    start = 0
    while True:
        offset = data.find(first, start)
        if offset < 0:
            raise CacheError('missing-gen3-move-name-table')
        start = offset + 1
        if decode_name(data[offset+13:offset+26]) != 'KARATE CHOP':
            continue
        names = [decode_name(data[offset+i*13:offset+(i+1)*13]) for i in range(354)]
        if all(names) and names[-1] == 'PSYCHO BOOST':
            return {str(i+1): name for i, name in enumerate(names)}


def item_names(data):
    """Read names from the ROM's 44-byte Item structs (pret item.h)."""
    count = 376 if data[0xAC:0xB0] == b'BPEE' else (374 if data[0xAC:0xB0] in (b'BPRE', b'BPGE') else 348)
    first = bytes((0xC7, 0xBB, 0xCD, 0xCE, 0xBF, 0xCC, 0x00, 0xBC, 0xBB, 0xC6, 0xC6, 0xFF))
    start = 0
    while True:
        offset = data.find(first, start)
        if offset < 0:
            raise CacheError('missing-gen3-item-name-table')
        start = offset + 1
        if decode_name(data[offset+44:offset+58]) != 'ULTRA BALL':
            continue
        names = {}
        for item_id in range(1, count + 1):
            entry = offset + (item_id - 1) * 44
            if entry + 44 > len(data):
                break
            stored_id = struct.unpack_from('<H', data, entry + 14)[0]
            name = decode_name(data[entry:entry+14])
            if stored_id == 0 and name and set(name) == {'?'}:
                continue  # Unused item slots are not real held items.
            if stored_id != item_id or not name:
                break
            names[str(item_id)] = name
        else:
            return names


def collection_names(data):
    """Read bank catalog data only from the qualified user's retail revision."""
    spec = importlib.util.spec_from_file_location('sprite_gen3_profiles', Path(__file__).with_name('butterflyos-gen3-gift.py'))
    gifts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gifts)
    profile = gifts.ROM_PROFILES.get(hashlib.sha256(data).hexdigest())
    if profile is None:
        return {}  # Existing Blink sprite support remains independent of Bdex qualification.
    _, _, mapping_at, stats_at, experience_at, _, names_at = profile
    mapping = {internal: dex for internal, dex in enumerate(struct.unpack_from('<411H', data, mapping_at), 1)
               if 1 <= dex <= 386}
    if len(mapping) != 386 or set(mapping.values()) != set(range(1, 387)):
        raise CacheError('invalid-gen3-national-mapping')
    names, types, ratios, growth, base_stats = {}, {}, {}, {}, {}
    for internal, dex in mapping.items():
        key = str(dex)
        name = decode_name(data[names_at + internal * 11:names_at + (internal + 1) * 11])
        if not name:
            raise CacheError('invalid-gen3-species-name')
        names[key] = name
        stats = data[stats_at + internal * 28:stats_at + (internal + 1) * 28]
        base_stats[key] = list(stats[:6])
        types[key] = list(dict.fromkeys(stats[6:8]))
        ratios[key], growth[key] = stats[16], stats[19]
    encoded = lambda text: bytes(ord(c) - ord('A') + 0xbb for c in text)
    table = data.find(encoded('NORMAL') + b'\xff' + encoded('FIGHT'))
    if table < 0:
        raise CacheError('missing-gen3-type-names')
    type_names = {str(ident): decode_name(data[table + ident * 7:table + (ident + 1) * 7])
                  for ident in {value for values in types.values() for value in values}}
    if not all(type_names.values()):
        raise CacheError('invalid-gen3-type-names')
    tables = {str(rate): list(struct.unpack_from('<101I', data, experience_at + rate * 404))
              for rate in set(growth.values())}
    return {'species': names, 'internal_to_national': {str(k): v for k, v in mapping.items()},
            'types': types, 'type_names': type_names, 'gender_ratios': ratios,
            'growth_rates': growth, 'experience_tables': tables, 'base_stats': base_stats}


def cache_rom(rom_path, cache_root, force=False):
    rom_path = os.path.abspath(rom_path)
    if not os.path.isfile(rom_path):
        raise CacheError("rom-not-found")
    data, code, revision, layout = read_rom_info(rom_path)
    digest = hashlib.sha256(data).hexdigest()
    destination = Path(cache_root) / digest
    manifest_path = destination / "manifest.json"
    if not force and manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
            if (manifest.get("rom_sha256") == digest and
                    manifest.get("extractor_version") == EXTRACTOR_VERSION and
                    (destination / "names.json").is_file()):
                print("cache_hit=1")
                print("cache_dir=" + str(destination))
                return destination
        except (OSError, ValueError):
            pass

    Path(cache_root).mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".sprite-cache-", dir=cache_root))
    try:
        (temporary / "names.json").write_text(json.dumps({
            "format": "butterflyos-gen3-rom-names", "format_version": 1,
            "generation": 3, "moves": move_names(data), "items": item_names(data),
            **collection_names(data),
        }, indent=2) + "\n")
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
            "rom_sha256": digest, "rom_content_sha256": digest, "generation": 3,
            "rom_filename": os.path.basename(rom_path),
            "game_code": code,
            "rom_revision": revision,
            "game_title": layout["title"],
            "name_cache": "names.json",
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

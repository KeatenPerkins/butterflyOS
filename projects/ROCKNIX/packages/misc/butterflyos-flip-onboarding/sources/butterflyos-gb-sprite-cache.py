#!/usr/bin/env python3
"""Cache Gen I/II Pokemon front sprites from a user-owned Game Boy ROM.

ButterflyOS deliberately ships no Pokemon art.  This program recognizes the
English retail Red, Blue, Yellow, Gold, Silver, and Crystal layouts, decodes
their front sprites locally, and stores only a cache derived from the user's
own ROM.  Unknown revisions and ROM hacks fail safely instead of guessing.

The Gen I decompressor and Gen II LZ decoder were independently adapted from
the BSD-2-Clause ``pokemon-sprites-rby`` project by Andrew Ekstedt:
https://github.com/magical/pokemon-sprites-rby (commit 36966acd74c2a93e3).
See the installed third-party notices for its license text.
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
from pathlib import Path


VERSION = "4"
DEFAULT_CACHE_ROOT = "/storage/.config/butterflyos/save-trade/sprite-cache"


class CacheError(Exception):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def write_png(path, width, height, pixels, palette):
    """Write indexed pixels as a small transparent RGBA PNG, dependency-free."""
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for value in pixels[y * width:(y + 1) * width]:
            rows.extend(palette[value])
    output = (b"\x89PNG\r\n\x1a\n" +
              png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
              png_chunk(b"IDAT", zlib.compress(bytes(rows), 9)) +
              png_chunk(b"IEND", b""))
    Path(path).write_bytes(output)


class BitReader:
    def __init__(self, data, offset):
        self.data = data
        self.offset = offset
        self.bits = 0
        self.available = 0

    def read(self, count):
        while self.available < count:
            if self.offset >= len(self.data):
                raise CacheError("truncated-gen1-sprite")
            self.bits = (self.bits << 8) | self.data[self.offset]
            self.offset += 1
            self.available += 8
        shift = self.available - count
        value = (self.bits >> shift) & ((1 << count) - 1)
        self.available -= count
        self.bits &= (1 << self.available) - 1
        return value


GEN1_TABLE1 = [(2 << index) - 1 for index in range(16)]
GEN1_TABLE2 = (
    (0, 1, 3, 2, 7, 6, 4, 5, 15, 14, 12, 13, 8, 9, 11, 10),
    (15, 14, 12, 13, 8, 9, 11, 10, 0, 1, 3, 2, 7, 6, 4, 5),
)
GEN1_REVERSE_NIBBLE = tuple(int(f"{index:04b}"[::-1], 2) for index in range(16))


def gen1_read_rle(bits, output):
    leading = 0
    while bits.read(1):
        leading += 1
        if leading >= len(GEN1_TABLE1):
            raise CacheError("invalid-gen1-rle")
    count = GEN1_TABLE1[leading] + bits.read(leading + 1)
    output.extend([0] * count)


def gen1_deinterlace(values, width_tiles, height_tiles):
    result = []
    for y in range(height_tiles):
        for x in range(width_tiles):
            offset = 4 * y * width_tiles + x
            for _ in range(4):
                result.append(values[offset])
                offset += width_tiles
    return result


def gen1_bitgroups_to_bytes(values):
    return bytearray((values[index] << 6) | (values[index + 1] << 4) |
                     (values[index + 2] << 2) | values[index + 3]
                     for index in range(0, len(values) - 3, 4))


def gen1_transform_one(data, width, height):
    for x in range(width):
        previous = 0
        for y in range(height):
            index = y * width + x
            high = GEN1_TABLE2[previous][data[index] >> 4]
            previous = high & 1
            low = GEN1_TABLE2[previous][data[index] & 15]
            previous = low & 1
            data[index] = (high << 4) | low


def gen1_decode(data, offset):
    bits = BitReader(data, offset)
    width_tiles, height_tiles = bits.read(4), bits.read(4)
    if not width_tiles or not height_tiles or width_tiles > 7 or height_tiles > 7:
        raise CacheError("invalid-gen1-sprite-dimensions")
    size = width_tiles * 8 * height_tiles
    first = bits.read(1)
    order = (first, first ^ 1)
    planes = [None, None]

    def read_plane():
        mode = bits.read(1)  # 0: RLE first; 1: literal first
        out = []
        while len(out) < size * 4:
            if mode == 0:
                gen1_read_rle(bits, out)
                mode = 1
            else:
                while len(out) < size * 4:
                    value = bits.read(2)
                    if value == 0:
                        break
                    out.append(value)
                mode = 0
        if len(out) != size * 4:
            raise CacheError("invalid-gen1-plane-size")
        return gen1_deinterlace(out, width_tiles * 8, height_tiles)

    planes[order[0]] = read_plane()
    transform = bits.read(1)
    if transform:
        transform = 1 + bits.read(1)
    planes[order[1]] = read_plane()
    # The transform stream addresses the two RAM planes in the order recorded
    # by ``first`` above, not necessarily plane 0 then plane 1.  Treating
    # those as fixed left/right planes happens to decode many sprites but
    # scrambles any that selected the opposite plane order (for example,
    # Beedrill in the English Red/Blue ROMs).
    plane_bytes = [gen1_bitgroups_to_bytes(planes[0]),
                   gen1_bitgroups_to_bytes(planes[1])]
    if transform == 0:
        gen1_transform_one(plane_bytes[0], width_tiles * 8, height_tiles)
        gen1_transform_one(plane_bytes[1], width_tiles * 8, height_tiles)
    elif transform == 1:
        gen1_transform_one(plane_bytes[order[0]], width_tiles * 8, height_tiles)
        for index in range(len(plane_bytes[order[1]])):
            plane_bytes[order[1]][index] ^= plane_bytes[order[0]][index]
    else:
        gen1_transform_one(plane_bytes[order[1]], width_tiles * 8, height_tiles)
        gen1_transform_one(plane_bytes[order[0]], width_tiles * 8, height_tiles)
        for index in range(len(plane_bytes[order[1]])):
            plane_bytes[order[1]][index] ^= plane_bytes[order[0]][index]
    left, right = plane_bytes
    planar = bytearray()
    for low, high in zip(left, right):
        for shift in range(7, -1, -1):
            planar.append(((low >> shift) & 1) | (((high >> shift) & 1) << 1))
    # Original data is tile-column-major.  Move it to ordinary row-major.
    width, height = width_tiles * 8, height_tiles * 8
    pixels = bytearray(width * height)
    source = 0
    for tile_x in range(width_tiles):
        for y in range(height):
            start = y * width + tile_x * 8
            pixels[start:start + 8] = planar[source:source + 8]
            source += 8
    return width, height, pixels


def find_bytes(data, needle):
    position = data.find(needle)
    if position < 0:
        raise CacheError("unknown-gen1-rom-layout")
    return position


def decode_gb_text(value):
    """Decode the English Gen I/II subset used by move and item labels."""
    output = []
    for byte in value:
        if 0x80 <= byte <= 0x99:
            output.append(chr(ord("A") + byte - 0x80))
        elif 0xA0 <= byte <= 0xB9:
            output.append(chr(ord("a") + byte - 0xA0))
        elif 0xF6 <= byte <= 0xFF:
            output.append(chr(ord("0") + byte - 0xF6))
        else:
            output.append({0x7F: " ", 0xE0: "'", 0xE3: "-", 0xE8: ".",
                           0xE9: "?", 0xEA: "!", 0xF2: "/"}.get(byte, "?"))
    return "".join(output).strip()


def gb_name_table(data, first_encoded, expected_second, count):
    """Locate a sequential, 0x50-terminated ROM text table.

    Game Boy ROMs can contain a move or item name in unrelated text/data.
    Validate every occurrence of the first name against its next entry rather
    than assuming the first byte match is the table itself.
    """
    start = 0
    saw_candidate = False
    while True:
        offset = data.find(first_encoded, start)
        if offset < 0:
            break
        saw_candidate = True
        names, cursor = [], offset
        for _ in range(count):
            end = data.find(b"\x50", cursor)
            if end < cursor:
                names = []
                break
            names.append(decode_gb_text(data[cursor:end]))
            cursor = end + 1
        if len(names) >= 2 and names[1] == expected_second:
            return names
        start = offset + 1
    if not saw_candidate:
        raise CacheError("missing-gb-name-table")
    raise CacheError("unexpected-gb-name-table")


def write_name_cache(data, destination, generation, species_ids=None):
    """Cache labels derived from this user-owned ROM; ship no game text."""
    pound = bytes((0x8F, 0x8E, 0x94, 0x8D, 0x83))
    master_ball = bytes((0x8C, 0x80, 0x92, 0x93, 0x84, 0x91, 0x7F,
                         0x81, 0x80, 0x8B, 0x8B))
    move_count = 165 if generation == 1 else 251
    moves = gb_name_table(data, pound, "KARATE CHOP", move_count)
    items = gb_name_table(data, master_ball, "ULTRA BALL", 255)
    payload = {
        "format": "butterflyos-gb-rom-names",
        "format_version": 1,
        "generation": generation,
        "moves": {str(index + 1): name for index, name in enumerate(moves)},
        "items": {str(index + 1): name for index, name in enumerate(items)},
    }
    if species_ids:
        # Gen I save files use an internal species order. Retain only the
        # conversion derived from the user's matching ROM, never ship it.
        payload["internal_to_national"] = {str(internal): dex
                                           for internal, dex in species_ids.items()}
    (destination / "names.json").write_text(json.dumps(payload, indent=2) + "\n")


def gen1_cache(rom_path, data, title, destination):
    # The searches make this work for the known English retail R/B/Y revisions
    # without baking copyrighted ROM offsets into ButterflyOS.
    base = find_bytes(data, bytes((1, 0x2d, 0x31, 0x31, 0x2d, 0x41)))
    mew = data.find(bytes((151, 100, 100, 100, 100, 100)))
    if mew > 0x8000:
        mew = -1
    dex_order = find_bytes(data, bytes((0x70, 0x73, 0x20, 0x23, 0x15, 0x64, 0x22, 0x50)))
    order = data[dex_order:dex_order + 0xbe]
    if len(order) != 0xbe:
        raise CacheError("truncated-gen1-pokedex-order")
    internal_by_dex = {dex: order.index(dex) + 1 for dex in range(1, 152)}
    grayscale = ((255, 255, 255, 0), (205, 214, 223, 255),
                 (100, 117, 139, 255), (18, 29, 46, 255))
    front = destination / "front"
    front.mkdir()
    for dex in range(1, 152):
        stats = mew if dex == 151 and mew >= 0 else base + (dex - 1) * 28
        if stats + 15 > len(data):
            raise CacheError("truncated-gen1-base-stats")
        internal = internal_by_dex[dex]
        pointer = struct.unpack_from("<H", data, stats + 11)[0]
        if internal == 0x15 and mew >= 0:
            bank = 1
        elif internal == 0xb6:
            bank = 0xb
        elif internal < 0x1f:
            bank = 9
        elif internal < 0x4a:
            bank = 10
        elif internal < 0x74:
            bank = 11
        elif internal < 0x99:
            bank = 12
        else:
            bank = 13
        offset = (bank - 1) * 0x4000 + pointer
        width, height, pixels = gen1_decode(data, offset)
        # Save IDs are Gen I internal IDs, not National Dex IDs.
        write_png(front / f"{internal:03d}.png", width, height, pixels, grayscale)
    write_name_cache(data, destination, 1,
                     {internal: dex for dex, internal in internal_by_dex.items()})
    return {"generation": 1, "game_title": title, "species_count": 151,
            "variants": ["front"], "save_species_ids": "gen1-internal",
            "name_cache": "names.json"}


GSC_LAYOUTS = {
    "POKEMON_GLD": ("Pokemon Gold", 0x51B0B, 0xAD3D, 0x48000, 0x7C000),
    "POKEMON_SLV": ("Pokemon Silver", 0x51B0B, 0xAD3D, 0x48000, 0x7C000),
    "PM_CRYSTAL": ("Pokemon Crystal", 0x51424, 0xA8CE, 0x120000, 0x124000),
}


def reverse_byte(value):
    return int(f"{value:08b}"[::-1], 2)


def gsc_decode(data, offset, width_tiles, height_tiles):
    output, position = bytearray(), offset
    while True:
        if position >= len(data):
            raise CacheError("truncated-gen2-sprite")
        control_byte = data[position]
        position += 1
        if control_byte == 0xff:
            break
        if control_byte >> 5 == 7:
            if position >= len(data):
                raise CacheError("truncated-gen2-command")
            packed = (control_byte << 8) | data[position]
            position += 1
            control, count = (packed >> 10) & 7, (packed & 0x3ff) + 1
        else:
            control, count = control_byte >> 5, (control_byte & 0x1f) + 1
        seek = None
        if control >= 4:
            if position >= len(data):
                raise CacheError("truncated-gen2-seek")
            seek = data[position]
            position += 1
            if seek & 0x80:
                seek = len(output) - (seek & 0x7f) - 1
            else:
                if position >= len(data):
                    raise CacheError("truncated-gen2-long-seek")
                seek = (seek << 8) | data[position]
                position += 1
            if seek < 0 or seek >= len(output):
                raise CacheError("invalid-gen2-seek")
        if control == 0:
            if position + count > len(data):
                raise CacheError("truncated-gen2-literal")
            output.extend(data[position:position + count])
            position += count
        elif control == 1:
            if position >= len(data): raise CacheError("truncated-gen2-repeat")
            output.extend((data[position],) * count); position += 1
        elif control == 2:
            if position + 2 > len(data): raise CacheError("truncated-gen2-alternate")
            first, second = data[position], data[position + 1]; position += 2
            output.extend(first if index % 2 == 0 else second for index in range(count))
        elif control == 3:
            output.extend((0,) * count)
        elif control == 4:
            for index in range(count): output.append(output[seek + index])
        elif control == 5:
            for index in range(count): output.append(reverse_byte(output[seek + index]))
        elif control == 6:
            if count - 1 > seek: raise CacheError("invalid-gen2-reverse")
            for index in range(count): output.append(output[seek - index])
        else:
            raise CacheError("unsupported-gen2-command")
        if len(output) > 0x10000: raise CacheError("gen2-sprite-too-large")
    # A Game Boy Color 2bpp tile is 16 bytes.  The decoder may emit extra
    # animation-frame bytes, but a static front image needs this minimum.
    required = width_tiles * height_tiles * 16
    if len(output) < required:
        raise CacheError("gen2-sprite-too-small")
    pixels = bytearray(width_tiles * 8 * height_tiles * 8)
    source, width = 0, width_tiles * 8
    for tile_x in range(width_tiles):
        for tile_y in range(height_tiles):
            for y in range(8):
                low, high = output[source], output[source + 1]; source += 2
                for x in range(8):
                    pixels[(tile_y * 8 + y) * width + tile_x * 8 + x] = ((low >> (7 - x)) & 1) | (((high >> (7 - x)) & 1) << 1)
    return width, height_tiles * 8, pixels


def gsc_far_pointer(data, table, index, crystal):
    at = table + index * 3
    if at + 3 > len(data): raise CacheError("truncated-gen2-pointer-table")
    bank, address = data[at], struct.unpack_from("<H", data, at + 1)[0]
    if address < 0x4000: raise CacheError("invalid-gen2-pointer")
    offset = bank * 0x4000 + address - 0x4000
    if crystal:
        offset += 0x36 * 0x4000
    elif offset >> 14 in (0x13, 0x14):
        offset += 0x0c * 0x4000
    elif offset >> 14 == 0x1f:
        offset += 0x0f * 0x4000
    return offset


def gsc_palette(data, offset):
    if offset + 4 > len(data): raise CacheError("truncated-gen2-palette")
    colors = [(255, 255, 255, 0)]
    for index in range(0, 4, 2):
        raw = struct.unpack_from("<H", data, offset + index)[0]
        colors.append(((raw & 31) * 255 // 31, ((raw >> 5) & 31) * 255 // 31,
                       ((raw >> 10) & 31) * 255 // 31, 255))
    colors.append((0, 0, 0, 255))
    return tuple(colors[:4])


def gen2_cache(data, title, destination):
    if title not in GSC_LAYOUTS: raise CacheError("unsupported-gen2-rom")
    label, stats, palettes, pointers, unown_pointers = GSC_LAYOUTS[title]
    crystal = title == "PM_CRYSTAL"
    normal_dir, shiny_dir = destination / "front", destination / "front-shiny"
    normal_dir.mkdir(); shiny_dir.mkdir()
    for species in range(1, 252):
        at = stats + (species - 1) * 32 + 17
        if at >= len(data): raise CacheError("truncated-gen2-base-stats")
        size = data[at]
        width_tiles, height_tiles = (size >> 4) & 15, size & 15
        if not width_tiles or not height_tiles: raise CacheError("invalid-gen2-sprite-dimensions")
        table, index = (unown_pointers, 0) if species == 201 else (pointers, (species - 1) * 2)
        offset = gsc_far_pointer(data, table, index, crystal)
        width, height, pixels = gsc_decode(data, offset, width_tiles, height_tiles)
        write_png(normal_dir / f"{species:03d}.png", width, height, pixels,
                  gsc_palette(data, palettes + species * 8))
        write_png(shiny_dir / f"{species:03d}.png", width, height, pixels,
                  gsc_palette(data, palettes + species * 8 + 4))
    # Unlike Gen I, Gold/Silver/Crystal save files store the National Dex
    # species ID directly.  Keep that explicit identity mapping in the cache
    # so cross-generation migration can validate a selected Pokémon without
    # guessing or shipping game data.
    write_name_cache(data, destination, 2,
                     {species: species for species in range(1, 252)})
    return {"generation": 2, "game_title": label, "species_count": 251,
            "variants": ["front", "front-shiny"], "save_species_ids": "national",
            "name_cache": "names.json"}


def cache_rom(rom_path, cache_root, force=False):
    rom_path = os.path.abspath(rom_path)
    data = Path(rom_path).read_bytes()
    if len(data) < 0x150: raise CacheError("rom-too-small")
    title = data[0x134:0x144].split(b"\0")[0].decode("ascii", "replace")
    generation = 1 if title in ("POKEMON RED", "POKEMON BLUE", "POKEMON YELLOW") else 2
    if generation == 2:
        title = data[0x134:0x13f].split(b"\0")[0].decode("ascii", "replace")
        if title not in GSC_LAYOUTS: raise CacheError("unsupported-gameboy-rom")
    digest = sha256_file(rom_path)
    destination = Path(cache_root) / digest
    manifest_path = destination / "manifest.json"
    if not force and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("rom_sha256") == digest and manifest.get("extractor_version") == VERSION:
            print("cache_hit=1\ncache_dir=" + str(destination)); return destination
    Path(cache_root).mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".gb-sprite-cache-", dir=cache_root))
    try:
        details = gen1_cache(rom_path, data, title, temporary) if generation == 1 else gen2_cache(data, title, temporary)
        details.update({"format": "butterflyos-gameboy-sprite-cache", "format_version": 1,
                        "extractor_version": VERSION, "rom_sha256": digest,
                        "rom_filename": os.path.basename(rom_path)})
        (temporary / "manifest.json").write_text(json.dumps(details, indent=2) + "\n")
        if destination.exists(): shutil.rmtree(destination)
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True); raise
    print("cache_hit=0\ncache_dir=" + str(destination) + "\ngeneration=" + str(generation))
    return destination


def main(argv):
    parser = argparse.ArgumentParser(description="Cache Gen I/II sprites from a user-owned ROM")
    parser.add_argument("rom"); parser.add_argument("--cache-root", default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try: cache_rom(args.rom, args.cache_root, args.force)
    except (OSError, CacheError, ValueError) as error:
        print("error=" + str(error), file=sys.stderr); return 1
    return 0


if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))

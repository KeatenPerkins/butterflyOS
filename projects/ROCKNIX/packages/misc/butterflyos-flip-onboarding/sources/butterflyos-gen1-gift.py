#!/usr/bin/env python3
"""Generate Gen I gift records using only a user's verified retail ROM.

No extracted Pokemon records, names, sprites or stat tables are shipped here.
Outputs are local session data and must never be included in release assets.
"""
import argparse
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import struct

SUPPORTED_ROMS = {
    '5ca7ba01642a3b27b0cc0b5349b52792795b62d3ed977e98a09390659af96b7b': 'POKEMON RED',
    '2a951313c2640e8c2cb21f25d1db019ae6245d9c7121f754fa61afd7bee6452d': 'POKEMON BLUE',
    '8cbaa499397e4f1a679c992ea9382a2dd7942ab398b48c19829c2d9529de47bf': 'POKEMON YELLOW',
}
PRESETS = {'mew': 151, 'surf-pikachu': 25, 'fly-pikachu': 25,
           'dragon-rage-magikarp': 129, 'pay-day-fearow': 22, 'pay-day-rapidash': 78}
PRESETS.update({'amnesia-psyduck': 54, 'stadium-bulbasaur': 1, 'stadium-charmander': 4,
                'stadium-squirtle': 7, 'stadium-hitmonlee': 106, 'stadium-hitmonchan': 107,
                'stadium-eevee': 133, 'stadium-omanyte': 138, 'stadium-kabuto': 140})
SPECIAL_MOVES = {'surf-pikachu': 57, 'fly-pikachu': 19,
                 'dragon-rage-magikarp': 82, 'pay-day-fearow': 6, 'pay-day-rapidash': 6}
SPECIAL_MOVES['amnesia-psyduck'] = 133


@lru_cache(maxsize=1)
def reader():
    path = Path(__file__).with_name('butterflyos-gb-sprite-cache.py')
    spec = importlib.util.spec_from_file_location('butterfly_gb_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encoded(text):
    return bytes(ord(c) - ord('A') + 0x80 for c in text)


def gift_from_rom(rom, preset, dvs=None):
    if preset not in PRESETS:
        raise ValueError('unsupported-gift')
    data = Path(rom).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest not in SUPPORTED_ROMS:
        raise ValueError('unsupported-gift-rom: use a verified English retail Red, Blue or Yellow ROM')
    gb = reader()
    dex = PRESETS[preset]
    base = gb.find_bytes(data, bytes((1, 0x2d, 0x31, 0x31, 0x2d, 0x41)))
    order_at = gb.find_bytes(data, bytes((0x70, 0x73, 0x20, 0x23, 0x15, 0x64, 0x22, 0x50)))
    order = data[order_at:order_at + 0xbe]
    if any(order.count(number) != 1 for number in range(1, 152)):
        raise ValueError('invalid-species-table')
    species = order.index(dex) + 1
    stats_at = gb.find_bytes(data, bytes((151, 100, 100, 100, 100, 100))) if dex == 151 else base + (dex - 1) * 28
    stats = data[stats_at:stats_at + 28]
    if len(stats) != 28 or stats[0] != dex:
        raise ValueError('invalid-base-stats')
    # Gen I Pokemon names are ten-byte fixed records in internal species order.
    names_at = gb.find_bytes(data, encoded('RHYDON') + b'\x50' * 4 + encoded('KANGASKHAN'))
    raw_name = data[names_at + (species - 1) * 10:names_at + species * 10]
    nickname = gb.decode_gb_text(raw_name.split(b'\x50')[0])
    if not nickname or len(nickname) > 10 or not nickname.isascii():
        raise ValueError('invalid-species-name')
    moves = list(stats[15:19])
    if preset in SPECIAL_MOVES:
        # Use a free move slot, or replace the fourth starting move when full.
        moves[moves.index(0) if 0 in moves else 3] = SPECIAL_MOVES[preset]
    # Every six-byte move record starts with its own animation/move ID.
    move_at = gb.find_bytes(data, bytes((1, 0, 40, 0, 255, 35, 2, 0, 50)))
    pp = []
    for move in moves:
        if move == 0:
            pp.append(0)
        else:
            at = move_at + (move - 1) * 6
            if not 1 <= move <= 165 or data[at] != move or not 1 <= data[at + 5] <= 40:
                raise ValueError('invalid-move-table')
            pp.append(data[at + 5])
    level = 5
    # Only the growth formulas used by these gifts are supported.
    if stats[19] == 0:
        experience = level ** 3
    elif stats[19] == 3:
        experience = 6 * level ** 3 // 5 - 15 * level ** 2 + 100 * level - 140
    elif stats[19] == 5:
        experience = 5 * level ** 3 // 4
    else:
        raise ValueError('unsupported-growth-rate')
    dvs = list(dvs) if dvs is not None else [secrets.randbelow(16) for _ in range(4)]
    if len(dvs) != 4 or any(not isinstance(v, int) or not 0 <= v <= 15 for v in dvs):
        raise ValueError('invalid-dvs')
    attack, defense, speed, special = dvs
    hp_dv = (attack & 1) * 8 + (defense & 1) * 4 + (speed & 1) * 2 + (special & 1)
    hp = 2 * (stats[1] + hp_dv) * level // 100 + level + 10
    ivs = attack << 12 | defense << 8 | speed << 4 | special
    record = struct.pack('>BHBBBBB4BH3s5HH4B', species, hp, level, 0,
                         stats[6], stats[7], stats[8], *moves, 0,
                         experience.to_bytes(3, 'big'), 0, 0, 0, 0, 0, ivs, *pp)
    return record, {'preset': preset, 'national_species': dex, 'species': species,
                    'nickname': nickname, 'level': level, 'moves': moves,
                    'move_pps': pp, 'rom_sha256': digest, 'rom_title': SUPPORTED_ROMS[digest]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--preset', choices=PRESETS, required=True)
    parser.add_argument('--output-record', type=Path, required=True)
    args = parser.parse_args()
    try:
        record, metadata = gift_from_rom(args.rom, args.preset)
        # Refuse input aliases and existing files, including symlinks.
        with args.output_record.open('xb') as handle:
            handle.write(record)
        print(json.dumps(metadata))
    except (OSError, ValueError, reader().CacheError) as error:
        parser.exit(1, 'gift-error=%s\n' % error)


if __name__ == '__main__':
    main()

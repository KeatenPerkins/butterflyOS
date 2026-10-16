#!/usr/bin/python3
"""Stage generated Box-style eggs for qualified English Emerald saves.

No original distribution records or ROM text/art are bundled. Numeric recipes:
PKHeX EncountersWC3.cs, Box eggs. Layout/encryption: pret/pokeemerald
include/{pokemon,global}.h, src/{pokemon,save}.c. Output is always a new file.
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import secrets
import struct
import subprocess
import sys
import zipfile
import zlib

ROM_SHA256 = 'a9dec84dfe7f62ab2220bafaef7479da0929d066ece16a6885f6226db19085af'
# National species and complete move recipe; level 5, no held item.
PRESETS = {
    'false-swipe-swablu-egg': (333, (64, 45, 206, 0)),
    'extremespeed-zigzagoon-egg': (263, (33, 45, 39, 245)),
    'pay-day-skitty-egg': (300, (45, 33, 39, 6)),
    'surf-pichu-egg': (172, (84, 204, 57, 0)),
}
SIZES = (0xF2C, 0xF80, 0xF80, 0xF80, 0xF08) + (0xF80,) * 8 + (0x7D0,)
ORDERS = tuple(itertools.permutations(range(4)))


def checksum(data):
    total = sum(struct.unpack('<%dI' % (len(data)//4), data)) & 0xFFFFFFFF
    return ((total >> 16) + total) & 0xFFFF


def active_sections(data):
    if len(data) != 0x20000:
        raise ValueError('Use a 128 KiB Emerald in-game save, not a save state.')
    slots = []
    for base in (0, 0xE000):
        if data[base:base+0xE000] == b'\xff' * 0xE000: continue
        sections, counters = {}, set()
        for i in range(14):
            offset = base + i*0x1000
            number, stored, magic, counter = struct.unpack_from('<HHII', data, offset+0xFF4)
            if magic != 0x08012025 or number >= 14 or number in sections:
                raise ValueError('Incomplete or damaged save slot; save normally twice first.')
            if stored != checksum(data[offset:offset+SIZES[number]]):
                raise ValueError('Save checksum mismatch; no changes made.')
            sections[number] = offset
            counters.add(counter)
        if len(counters) != 1: raise ValueError('Mixed save counters; save normally twice first.')
        slots.append((counters.pop(), sections))
    if not slots: raise ValueError('No valid save slot.')
    if len(slots) == 1: return slots[0][1]
    if slots[0][0] == slots[1][0]: raise ValueError('Ambiguous save counters.')
    if {s[0] for s in slots} == {0, 0xFFFFFFFF}:
        return next(sections for counter, sections in slots if counter == 0)
    return max(slots, key=lambda s: s[0])[1]


def read_rom(path):
    spec = importlib.util.spec_from_file_location('rom_filter', Path(__file__).with_name('butterflyos_rom_filter.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    data = module.read_gen3_rom(path)
    if hashlib.sha256(data).hexdigest() != ROM_SHA256:
        raise ValueError('This first egg batch requires the qualified English Emerald ROM.')
    return data


def make_egg(rom, save2, preset):
    national, moves = PRESETS[preset]
    # ROM tables qualified by the complete ROM SHA-256, never guessed for hacks.
    mapping = struct.unpack_from('<411H', rom, 0x31DC82)
    species = mapping.index(national) + 1
    stats = rom[0x3203CC+species*28:0x3203CC+(species+1)*28]
    exp = struct.unpack_from('<I', rom, 0x31F72C+stats[19]*404+5*4)[0]
    personality = secrets.randbits(32)
    ot_id = struct.unpack_from('<I', save2, 10)[0]
    header = bytearray(32)
    struct.pack_into('<II', header, 0, personality, ot_id)
    header[8:18] = bytes((0xBF, 0xC1, 0xC1, 0xFF)) + b'\xff'*6  # EGG, game encoding.
    header[18:20] = bytes((2, 6))  # English; hasSpecies + isEgg.
    header[20:27] = save2[:7]
    growth, attacks, effort, misc = (bytearray(12) for _ in range(4))
    struct.pack_into('<HHI', growth, 0, species, 0, exp)
    growth[9] = stats[17]  # Egg cycles, not adult friendship.
    struct.pack_into('<4H', attacks, 0, *moves)
    attacks[8:12] = bytes(rom[0x31C898+move*12+4] if move else 0 for move in moves)
    misc[1] = 253  # Gift egg; normal hatching replaces met data.
    origins = (3 << 7) | (4 << 11) | ((save2[8] & 1) << 15)  # Emerald, Poke Ball, OT gender.
    struct.pack_into('<H', misc, 2, origins)
    ivs = secrets.randbits(30) | (1 << 30)
    if stats[23] and personality & 1: ivs |= 1 << 31
    struct.pack_into('<I', misc, 4, ivs)
    blocks = (growth, attacks, effort, misc)
    plain = b''.join(blocks[i] for i in ORDERS[personality % 24])
    struct.pack_into('<H', header, 28, sum(struct.unpack('<24H', plain)) & 0xFFFF)
    key = personality ^ ot_id
    encrypted = b''.join(struct.pack('<I', word ^ key) for word in struct.unpack('<12I', plain))
    encoded_name = rom[0x3185C8+species*11:0x3185C8+(species+1)*11]
    nickname = ''.join(chr(c-0xBB+65) for c in encoded_name if 0xBB <= c <= 0xD4)
    return bytes(header)+encrypted, {'nickname': nickname, 'species': species,
        'national_species': national, 'moves': moves, 'egg_cycles': stats[17],
        'level': 5, 'held': 0, 'egg': True}


def prepare(data, rom, preset, box, slot):
    if not 0 <= box < 14 or not 0 <= slot < 30: raise ValueError('Invalid box or slot.')
    if hashlib.sha256(rom).hexdigest() != ROM_SHA256: raise ValueError('Unsupported ROM.')
    sections = active_sections(data)
    pc = bytearray().join(data[sections[n]:sections[n]+SIZES[n]] for n in range(5,14))
    at = 4+(box*30+slot)*80
    if pc[at:at+80] != bytes(80): raise ValueError('Destination slot is not empty; no Pokemon replaced.')
    save2 = data[sections[0]:sections[0]+SIZES[0]]
    record, metadata = make_egg(rom, save2, preset)
    pc[at:at+80] = record
    result = bytearray(data);cursor=0
    for n in range(5,14):
        offset,size = sections[n],SIZES[n];block=pc[cursor:cursor+size];cursor+=size
        if result[offset:offset+size] == block: continue
        result[offset:offset+size] = block
        struct.pack_into('<H',result,offset+0xFF6,checksum(block))
    active_sections(result)
    return bytes(result), metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save',type=Path,required=True)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--preset',choices=PRESETS,required=True)
    parser.add_argument('--box',type=int,required=True)
    parser.add_argument('--slot',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--helper',default='/usr/bin/butterflyos-save-trade')
    args=parser.parse_args()
    inspected=subprocess.run([args.helper,'inspect','--save',str(args.save)],capture_output=True,text=True)
    if inspected.returncode or 'save_type=Emerald\n' not in inspected.stdout:
        raise ValueError('This first egg batch supports Emerald saves only.')
    original=args.save.read_bytes()
    result,metadata=prepare(original,read_rom(args.rom),args.preset,args.box,args.slot)
    if args.save.read_bytes()!=original: raise ValueError('Save changed during preparation.')
    with args.output.open('xb') as stream:stream.write(result)
    print(json.dumps(metadata))


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,struct.error,zipfile.BadZipFile,zlib.error,RuntimeError,NotImplementedError) as error:
        print('error='+str(error),file=sys.stderr);sys.exit(1)

#!/usr/bin/python3
"""Stage generated gift eggs for qualified English Gen III saves.

No original distribution records or ROM text/art are bundled. Numeric recipes:
PKHeX EncountersWC3.cs, documented Gen III egg recipes. Layout/encryption:
pret/{pokeemerald,pokeruby,pokefirered} include/{pokemon,global}.h and src/save.c. Output is always a new file.
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
# Full retail-ROM hashes qualify these exact English revisions. No ROM data is bundled.
# family, origin game ID, mapping, species stats, experience, battle moves, names
ROM_PROFILES = {
    ROM_SHA256: ('Emerald', 3, 0x31DC82, 0x3203CC, 0x31F72C, 0x31C898, 0x3185C8),
    '0fdd36e92b75bed65d09df4635ab0b707b288c2bf1dc4c6e7a4a4f0eebe9d64c':
        ('Ruby/Sapphire', 2, 0x1FC52E, 0x1FEC30, 0x1FDF90, 0x1FB144, 0x1F7184),
    '02ca41513580a8b780989dee428df747b52a0b1a55bec617886b4059eb1152fb':
        ('Ruby/Sapphire', 1, 0x1FC4BE, 0x1FEBC0, 0x1FDF20, 0x1FB0D4, 0x1F7114),
    '729041b940afe031302d630fdbe57c0c145f3f7b6d9b8eca5e98678d0ca4d059':
        ('FireRed/LeafGreen', 4, 0x25205E, 0x2547F4, 0x253B54, 0x250C74, 0x245F50),
    '2f978f635b9593f6ca26ec42481c53a6b39f6cddd894ad5c062c1419fac58825':
        ('FireRed/LeafGreen', 5, 0x25203A, 0x2547D0, 0x253B30, 0x250C50, 0x245F2C),
}


def rom_profile(rom):
    try:
        return ROM_PROFILES[hashlib.sha256(rom).hexdigest()]
    except KeyError:
        raise ValueError('Use a qualified English ROM: Emerald, Ruby/Sapphire revision 2, or FireRed/LeafGreen revision 1.') from None


def section_sizes(family):
    first, last = {'Emerald': (0xF2C, 0xF08),
                   'Ruby/Sapphire': (0x890, 0xC40),
                   'FireRed/LeafGreen': (0xF24, 0xEE8)}[family]
    return (first, 0xF80, 0xF80, 0xF80, last) + (0xF80,) * 8 + (0x7D0,)

# National species and complete move recipe; level 5, no held item.
PRESETS = {
    'false-swipe-swablu-egg': (333, (64, 45, 206, 0)),
    'extremespeed-zigzagoon-egg': (263, (33, 45, 39, 245)),
    'pay-day-skitty-egg': (300, (45, 33, 39, 6)),
    'surf-pichu-egg': (172, (84, 204, 57, 0)),
}
# PokéPark 2005 Wonder Card species/moves, one generated equivalent per recipe.
POKEPARK_PRESETS = {
    'pokepark-psyduck-egg': (54, (346, 10, 39, 300)),
    'pokepark-pichu-egg': (172, (84, 204, 266, 0)),
    'pokepark-igglybuff-egg': (174, (47, 204, 111, 321)),
    'pokepark-corsola-egg': (222, (33, 300, 0, 0)),
    'pokepark-taillow-egg': (276, (64, 45, 116, 297)),
    'pokepark-surskit-egg': (283, (145, 300, 0, 0)),
    'pokepark-whismur-egg': (293, (1, 253, 298, 0)),
    'pokepark-skitty-egg': (300, (45, 33, 39, 205)),
    'pokepark-plusle-egg': (311, (45, 86, 346, 0)),
    'pokepark-minun-egg': (312, (45, 86, 300, 0)),
    'pokepark-spoink-egg': (325, (150, 253, 0, 0)),
    'pokepark-spinda-egg': (327, (33, 253, 47, 0)),
    'pokepark-cacnea-egg': (331, (40, 43, 71, 227)),
    'pokepark-corphish-egg': (341, (145, 346, 0, 0)),
    'pokepark-wynaut-egg': (360, (150, 204, 227, 321)),
}
PRESETS.update(POKEPARK_PRESETS)
# Anniversary recipes were distributed for Japanese Ruby; these are explicitly
# expanded English Gen III equivalents, not original distribution records.
ANNIVERSARY_PRESETS = {
    'anniversary-teeter-pichu-egg': (172, (84, 204, 298, 0)),
    'anniversary-wish-pichu-egg': (172, (84, 204, 273, 0)),
    'anniversary-charm-ralts-egg': (280, (45, 204, 0, 0)),
    'anniversary-wish-ralts-egg': (280, (45, 273, 0, 0)),
    'anniversary-spite-absol-egg': (359, (10, 43, 180, 0)),
    'anniversary-wish-absol-egg': (359, (10, 43, 273, 0)),
    'anniversary-iron-defense-bagon-egg': (371, (99, 44, 334, 0)),
    'anniversary-wish-bagon-egg': (371, (99, 44, 273, 0)),
    'anniversary-shiny-teeter-pichu-egg': (172, (84, 204, 298, 0)),
    'anniversary-shiny-wish-pichu-egg': (172, (84, 204, 273, 0)),
}
SHINY_PRESETS = frozenset(p for p in ANNIVERSARY_PRESETS if '-shiny-' in p)
PRESETS.update(ANNIVERSARY_PRESETS)

# Expanded English Gen III equivalents of the 2004 Japanese FRLG campaign.
PROMOTIONAL_PRESETS = {
    'promotional-oddish-egg': (43, (71, 73, 0, 0)),
    'promotional-meowth-egg': (52, (10, 45, 80, 0)),
    'promotional-poliwag-egg': (60, (145, 186, 0, 0)),
    'promotional-bellsprout-egg': (69, (22, 298, 0, 0)),
}
PRESETS.update(PROMOTIONAL_PRESETS)

# Expanded English Gen III equivalents of the FRLG PCNY Wish campaign.
PCNY_PRESETS = {'pcny-farfetchd-egg': (83, (281, 273, 0, 0)), 'pcny-drowzee-egg': (96, (187, 273, 0, 0)), 'pcny-exeggcute-egg': (102, (230, 273, 0, 0)), 'pcny-lickitung-egg': (108, (215, 273, 0, 0)), 'pcny-chansey-egg': (113, (230, 273, 0, 0)), 'pcny-kangaskhan-egg': (115, (281, 273, 0, 0))}
PRESETS.update(PCNY_PRESETS)

SIZES = (0xF2C, 0xF80, 0xF80, 0xF80, 0xF08) + (0xF80,) * 8 + (0x7D0,)
ORDERS = tuple(itertools.permutations(range(4)))


def checksum(data):
    total = sum(struct.unpack('<%dI' % (len(data)//4), data)) & 0xFFFFFFFF
    return ((total >> 16) + total) & 0xFFFF


def active_sections(data, sizes=SIZES):
    if len(data) != 0x20000:
        raise ValueError('Use a 128 KiB Gen III in-game save, not a save state.')
    slots = []
    for base in (0, 0xE000):
        if data[base:base+0xE000] == b'\xff' * 0xE000: continue
        sections, counters = {}, set()
        for i in range(14):
            offset = base + i*0x1000
            number, stored, magic, counter = struct.unpack_from('<HHII', data, offset+0xFF4)
            if magic != 0x08012025 or number >= 14 or number in sections:
                raise ValueError('Incomplete or damaged save slot; save normally twice first.')
            if stored != checksum(data[offset:offset+sizes[number]]):
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
    rom_profile(data)
    return data


def choose_personality(ot_id, preset):
    value = secrets.randbits(32)
    if preset not in SHINY_PRESETS:
        return value
    low = value & 0xFFFF
    high = (ot_id & 0xFFFF) ^ (ot_id >> 16) ^ low ^ ((value >> 16) & 7)
    return low | (high << 16)


def make_egg(rom, save2, preset):
    national, moves = PRESETS[preset]
    family, origin, mapping_at, stats_at, exp_at, moves_at, names_at = rom_profile(rom)
    # ROM tables qualified by the complete ROM SHA-256, never guessed for hacks.
    mapping = struct.unpack_from('<411H', rom, mapping_at)
    species = mapping.index(national) + 1
    stats = rom[stats_at+species*28:stats_at+(species+1)*28]
    exp = struct.unpack_from('<I', rom, exp_at+stats[19]*404+5*4)[0]
    ot_id = struct.unpack_from('<I', save2, 10)[0]
    personality = choose_personality(ot_id, preset)
    header = bytearray(32)
    struct.pack_into('<II', header, 0, personality, ot_id)
    header[8:18] = bytes((0xBF, 0xC1, 0xC1, 0xFF)) + b'\xff'*6  # EGG, game encoding.
    header[18:20] = bytes((2, 6))  # English; hasSpecies + isEgg.
    header[20:27] = save2[:7]
    growth, attacks, effort, misc = (bytearray(12) for _ in range(4))
    struct.pack_into('<HHI', growth, 0, species, 0, exp)
    growth[9] = stats[17]  # Egg cycles, not adult friendship.
    struct.pack_into('<4H', attacks, 0, *moves)
    attacks[8:12] = bytes(rom[moves_at+move*12+4] if move else 0 for move in moves)
    misc[1] = 253  # Gift egg; normal hatching replaces met data.
    origins = (origin << 7) | (4 << 11) | ((save2[8] & 1) << 15)  # Destination game, Poke Ball, OT gender.
    struct.pack_into('<H', misc, 2, origins)
    ivs = secrets.randbits(30) | (1 << 30)
    if stats[23] and personality & 1: ivs |= 1 << 31
    struct.pack_into('<I', misc, 4, ivs)
    if preset in POKEPARK_PRESETS or preset in PROMOTIONAL_PRESETS or preset in PCNY_PRESETS:
        struct.pack_into('<I', misc, 8, 1 << 31)  # Modern fateful-encounter flag.
    blocks = (growth, attacks, effort, misc)
    plain = b''.join(blocks[i] for i in ORDERS[personality % 24])
    struct.pack_into('<H', header, 28, sum(struct.unpack('<24H', plain)) & 0xFFFF)
    key = personality ^ ot_id
    encrypted = b''.join(struct.pack('<I', word ^ key) for word in struct.unpack('<12I', plain))
    encoded_name = rom[names_at+species*11:names_at+(species+1)*11]
    nickname = ''.join(chr(c-0xBB+65) for c in encoded_name if 0xBB <= c <= 0xD4)
    return bytes(header)+encrypted, {'nickname': nickname, 'species': species,
        'national_species': national, 'moves': moves, 'egg_cycles': stats[17],
        'level': 5, 'held': 0, 'egg': True}


def prepare(data, rom, preset, box, slot):
    if not 0 <= box < 14 or not 0 <= slot < 30: raise ValueError('Invalid box or slot.')
    family = rom_profile(rom)[0]
    sizes = section_sizes(family)
    sections = active_sections(data, sizes)
    save2 = data[sections[0]:sections[0]+sizes[0]]
    game_code = struct.unpack_from('<I', save2, 0xAC)[0]
    if family == 'Ruby/Sapphire':
        matches = game_code == 0
    elif family == 'FireRed/LeafGreen':
        matches = game_code == 1 and save2[0xAF8:0xAFC] == save2[0xF20:0xF24]
    else:
        matches = save2[0xAC:0xB0] == save2[0x1F4:0x1F8]
    if not matches: raise ValueError('Save family does not match the selected ROM.')
    pc = bytearray().join(data[sections[n]:sections[n]+sizes[n]] for n in range(5,14))
    at = 4+(box*30+slot)*80
    if pc[at:at+80] != bytes(80): raise ValueError('Destination slot is not empty; no Pokemon replaced.')
    save2 = data[sections[0]:sections[0]+sizes[0]]
    record, metadata = make_egg(rom, save2, preset)
    pc[at:at+80] = record
    result = bytearray(data);cursor=0
    for n in range(5,14):
        offset,size = sections[n],sizes[n];block=pc[cursor:cursor+size];cursor+=size
        if result[offset:offset+size] == block: continue
        result[offset:offset+size] = block
        struct.pack_into('<H',result,offset+0xFF6,checksum(block))
    active_sections(result, sizes)
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
    rom = read_rom(args.rom)
    family = rom_profile(rom)[0]
    if inspected.returncode or ('save_type='+family+'\n') not in inspected.stdout:
        raise ValueError('Save family does not match the selected ROM.')
    original=args.save.read_bytes()
    result,metadata=prepare(original,rom,args.preset,args.box,args.slot)
    if args.save.read_bytes()!=original: raise ValueError('Save changed during preparation.')
    with args.output.open('xb') as stream:stream.write(result)
    print(json.dumps(metadata))


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,struct.error,zipfile.BadZipFile,zlib.error,RuntimeError,NotImplementedError) as error:
        print('error='+str(error),file=sys.stderr);sys.exit(1)

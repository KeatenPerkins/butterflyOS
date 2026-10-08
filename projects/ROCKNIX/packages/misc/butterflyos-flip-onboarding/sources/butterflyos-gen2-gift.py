#!/usr/bin/env python3
"""Stage generated Gen II gifts from qualified user ROMs and in-game saves.

Names, growth rates and move PP come from the user's ROM. Outputs are isolated;
the caller owns preview, verified backup and explicit Commit. No assets bundled.
Save layouts checked against pret/pokegold and pret/pokecrystal RAM symbols.
"""
import argparse
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets

SUPPORTED_ROMS = {
    'fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e': 'POKEMON_GLD',
    '72b190859a59623cbef6c49d601f8de52c1d2331b4f08a8d2acc17274fc19a8c': 'POKEMON_SLV',
    'fdcc3c8c43813cf8731fc037d2a6d191bac75439c34b24ba1c27526e6acdc8a2': 'PM_CRYSTAL',
}
# Species, complete move recipe, held item. Generated player-owned equivalents.
PRESETS = {'mew': (151, (1, 0, 0, 0), 0),
           'celebi': (251, (73, 93, 215, 105), 0),
           'baton-pass-farfetchd': (83, (226, 14, 97, 163), 174),
           'earthquake-gligar': (207, (89, 40, 68, 17), 150)}
EGG_PRESETS = {
    'ancientpower-bulbasaur-egg': (1, (33, 45, 246, 0), 0),
    'crunch-charmander-egg': (4, (10, 45, 242, 0), 0),
    'submission-totodile-egg': (158, (10, 43, 66, 0), 0),
    'night-shade-hoothoot-egg': (163, (33, 45, 101, 0), 0),
    'sing-pichu-egg': (172, (84, 204, 47, 0), 0),
    'petal-dance-psyduck-egg': (54, (10, 39, 80, 0), 0),
    'petal-dance-chikorita-egg': (152, (33, 45, 80, 0), 0),
    'petal-dance-pichu-egg': (172, (84, 204, 80, 0), 0),
    'petal-dance-cleffa-egg': (173, (1, 204, 227, 80), 0),
    'petal-dance-igglybuff-egg': (174, (47, 204, 111, 80), 0),
    'petal-dance-smoochum-egg': (238, (1, 122, 80, 0), 0),
    'swift-cleffa-egg': (173, (1, 204, 227, 129), 0),
    'belly-drum-wooper-egg': (194, (55, 39, 187, 0), 0),
    'encore-phanpy-egg': (231, (33, 45, 227, 0), 0),
    'metronome-smoochum-egg': (238, (1, 122, 118, 0), 0),
}
PRESETS.update(EGG_PRESETS)
PCNY_EGG_PRESETS = {
    'zap-cannon-squirtle-egg': (7, (33, 39, 192, 0), 0),
    'growth-eevee-egg': (133, (33, 39, 74, 0), 0),
    'lovely-kiss-snorlax-egg': (143, (33, 142, 0, 0), 0),
    'hydro-pump-dratini-egg': (147, (35, 43, 56, 0), 0),
    'double-edge-cyndaquil-egg': (155, (33, 43, 38, 0), 0),
    'mimic-igglybuff-egg': (174, (47, 204, 111, 102), 0),
    'pursuit-elekid-egg': (239, (98, 43, 228, 0), 0),
    'faint-attack-magby-egg': (240, (52, 185, 0, 0), 0),
    'rage-tyrogue-egg': (236, (33, 99, 0, 0), 0),
    'dizzy-punch-sentret-egg': (161, (33, 111, 146, 0), 0),
    'barrier-ledyba-egg': (165, (33, 112, 0, 0), 0),
    'growth-spinarak-egg': (167, (40, 81, 74, 0), 0),
    'light-screen-chinchou-egg': (170, (145, 86, 48, 113), 0),
    'safeguard-natu-egg': (177, (64, 43, 219, 0), 0),
    'dizzy-punch-marill-egg': (183, (33, 111, 146, 0), 0),
    'dizzy-punch-pichu-egg': (172, (84, 204, 146, 0), 0),
    'scary-face-pichu-egg': (172, (84, 204, 184, 0), 0),
    'scary-face-cleffa-egg': (173, (1, 204, 227, 184), 0),
    'scary-face-igglybuff-egg': (174, (47, 204, 111, 184), 0),
    'hydro-pump-marill-egg': (183, (33, 111, 56, 0), 0),
    'scary-face-marill-egg': (183, (33, 111, 184, 0), 0),
    'substitute-sudowoodo-egg': (185, (88, 102, 164, 0), 0),
    'agility-hoppip-egg': (187, (150, 235, 39, 97), 0),
    'scary-face-wooper-egg': (194, (55, 39, 184, 0), 0),
    'dizzy-punch-elekid-egg': (239, (98, 43, 146, 0), 0),
    'sonicboom-spearow-egg': (21, (64, 45, 49, 0), 0),
    'lovely-kiss-nidoran-female-egg': (29, (45, 33, 142, 0), 0),
    'moonlight-nidoran-female-egg': (29, (45, 33, 236, 0), 0),
    'sweet-kiss-nidoran-female-egg': (29, (45, 33, 186, 0), 0),
    'lovely-kiss-nidoran-male-egg': (32, (43, 33, 142, 0), 0),
    'morning-sun-nidoran-male-egg': (32, (43, 33, 234, 0), 0),
    'sweet-kiss-nidoran-male-egg': (32, (43, 33, 186, 0), 0),
    'flail-zubat-egg': (41, (141, 175, 0, 0), 0),
    'leech-seed-oddish-egg': (43, (71, 73, 0, 0), 0),
    'synthesis-paras-egg': (46, (10, 235, 0, 0), 0),
    'tri-attack-psyduck-egg': (54, (10, 39, 161, 0), 0),
    'growth-poliwag-egg': (60, (145, 74, 0, 0), 0),
    'lovely-kiss-poliwag-egg': (60, (145, 142, 0, 0), 0),
    'sweet-kiss-poliwag-egg': (60, (145, 186, 0, 0), 0),
    'foresight-abra-egg': (63, (100, 193, 0, 0), 0),
    'false-swipe-machop-egg': (66, (67, 43, 206, 0), 0),
    'thrash-machop-egg': (66, (67, 43, 37, 0), 0),
    'lovely-kiss-bellsprout-egg': (69, (22, 142, 0, 0), 0),
    'sweet-kiss-bellsprout-egg': (69, (22, 186, 0, 0), 0),
    'confuse-ray-tentacool-egg': (72, (40, 109, 0, 0), 0),
    'rapid-spin-geodude-egg': (74, (33, 229, 0, 0), 0),
    'low-kick-ponyta-egg': (77, (33, 45, 67, 0), 0),
    'agility-magnemite-egg': (81, (33, 97, 0, 0), 0),
    'fury-cutter-farfetchd-egg': (83, (64, 210, 0, 0), 0),
    'low-kick-doduo-egg': (84, (64, 45, 67, 0), 0),
    'flail-seel-egg': (86, (29, 45, 175, 0), 0),
    'sharpen-onix-egg': (95, (33, 103, 159, 0), 0),
    'amnesia-drowzee-egg': (96, (1, 95, 133, 0), 0),
    'metal-claw-krabby-egg': (98, (145, 43, 232, 0), 0),
    'agility-voltorb-egg': (100, (33, 97, 0, 0), 0),
    'sweet-scent-exeggcute-egg': (102, (140, 95, 230, 0), 0),
    'fury-attack-cubone-egg': (104, (45, 39, 31, 0), 0),
    'doubleslap-lickitung-egg': (108, (122, 3, 0, 0), 0),
    'sweet-scent-chansey-egg': (113, (1, 230, 0, 0), 0),
    'synthesis-tangela-egg': (114, (132, 79, 235, 0), 0),
    'faint-attack-kangaskhan-egg': (115, (4, 185, 0, 0), 0),
    'haze-horsea-egg': (116, (145, 114, 0, 0), 0),
    'swords-dance-goldeen-egg': (118, (64, 39, 14, 0), 0),
    'twister-staryu-egg': (120, (33, 106, 239, 0), 0),
    'mind-reader-mr-mime-egg': (122, (112, 170, 0, 0), 0),
    'sonicboom-scyther-egg': (123, (98, 43, 49, 0), 0),
    'rock-throw-pinsir-egg': (127, (11, 88, 0, 0), 0),
    'quick-attack-tauros-egg': (128, (33, 39, 98, 0), 0),
    'bubble-magikarp-egg': (129, (150, 145, 0, 0), 0),
    'reversal-magikarp-egg': (129, (150, 179, 0, 0), 0),
    'bite-lapras-egg': (131, (55, 45, 47, 44), 0),
    'future-sight-lapras-egg': (131, (55, 45, 47, 248), 0),
    'barrier-porygon-egg': (137, (33, 160, 176, 112), 0),
    'rock-throw-omanyte-egg': (138, (132, 110, 88, 0), 0),
    'rock-throw-kabuto-egg': (140, (10, 106, 88, 0), 0),
    'rock-throw-aerodactyl-egg': (142, (17, 88, 0, 0), 0),
    'splash-snorlax-egg': (143, (33, 150, 0, 0), 0),
    'sweet-kiss-snorlax-egg': (143, (33, 186, 0, 0), 0),
    'mimic-aipom-egg': (190, (10, 39, 102, 0), 0),
    'splash-sunkern-egg': (191, (71, 74, 150, 0), 0),
    'steel-wing-yanma-egg': (193, (33, 193, 211, 0), 0),
    'sweet-kiss-yanma-egg': (193, (33, 193, 186, 0), 0),
    'beat-up-murkrow-egg': (198, (64, 251, 0, 0), 0),
    'hypnosis-misdreavus-egg': (200, (45, 149, 95, 0), 0),
    'mimic-wobbuffet-egg': (202, (243, 219, 194, 102), 0),
    'substitute-pineco-egg': (204, (33, 182, 164, 0), 0),
    'fury-attack-dunsparce-egg': (206, (99, 111, 31, 0), 0),
    'horn-drill-dunsparce-egg': (206, (99, 111, 32, 0), 0),
    'lovely-kiss-snubbull-egg': (209, (33, 184, 39, 142), 0),
    'double-edge-qwilfish-egg': (211, (33, 40, 38, 0), 0),
    'seismic-toss-heracross-egg': (214, (33, 43, 69, 0), 0),
    'moonlight-sneasel-egg': (215, (10, 43, 236, 0), 0),
    'sweet-scent-teddiursa-egg': (216, (10, 43, 230, 0), 0),
    'whirlwind-swinub-egg': (220, (33, 18, 0, 0), 0),
    'amnesia-remoraid-egg': (223, (55, 133, 0, 0), 0),
    'mist-remoraid-egg': (223, (55, 54, 0, 0), 0),
    'pay-day-delibird-egg': (225, (217, 6, 0, 0), 0),
    'spikes-delibird-egg': (225, (217, 191, 0, 0), 0),
    'gust-mantine-egg': (226, (33, 145, 16, 0), 0),
    'fury-cutter-skarmory-egg': (227, (43, 64, 210, 0), 0),
    'absorb-phanpy-egg': (231, (33, 45, 71, 0), 0),
    'safeguard-stantler-egg': (234, (33, 219, 0, 0), 0),
    'mega-kick-miltank-egg': (241, (33, 45, 25, 0), 0),
    'rage-larvitar-egg': (246, (44, 43, 99, 0), 0),
}
PRESETS.update(PCNY_EGG_PRESETS)
PCNY_SHINY_PRESETS = {
    'shiny-venusaur': (3, (77, 79, 75, 230), 0),
    'shiny-charizard': (6, (99, 184, 53, 17), 0),
    'shiny-blastoise': (9, (55, 44, 229, 182), 0),
    'shiny-articuno': (144, (54, 97, 170, 58), 0),
    'shiny-zapdos': (145, (86, 97, 197, 65), 0),
    'shiny-moltres': (146, (83, 97, 203, 53), 0),
    'shiny-mewtwo': (150, (244, 248, 54, 94), 0),
    'shiny-mew': (151, (1, 0, 0, 0), 0),
    'shiny-meganium': (154, (115, 77, 235, 34), 0),
    'shiny-typhlosion': (157, (108, 52, 98, 172), 0),
    'shiny-feraligatr': (160, (55, 44, 184, 163), 0),
    'shiny-raikou': (243, (43, 84, 46, 98), 0),
    'shiny-entei': (244, (43, 52, 46, 83), 0),
    'shiny-suicune': (245, (43, 55, 46, 16), 0),
    'shiny-lugia': (249, (177, 219, 16, 105), 0),
    'shiny-ho-oh': (250, (221, 219, 16, 105), 0),
}
PRESETS.update(PCNY_SHINY_PRESETS)
PCNY_GIFT_LEVELS = {
    'shiny-venusaur': 40,
    'shiny-charizard': 40,
    'shiny-blastoise': 40,
    'shiny-articuno': 50,
    'shiny-zapdos': 50,
    'shiny-moltres': 50,
    'shiny-mewtwo': 70,
    'shiny-mew': 5,
    'shiny-meganium': 40,
    'shiny-typhlosion': 40,
    'shiny-feraligatr': 40,
    'shiny-raikou': 40,
    'shiny-entei': 40,
    'shiny-suicune': 40,
    'shiny-lugia': 40,
    'shiny-ho-oh': 40,
}
BOX_SIZE = 0x450
GS_MIRRORS = ((0x2009, 0x222F, 0x15C7), (0x222F, 0x23D9, 0x3D96),
              (0x23D9, 0x2856, 0xC6B), (0x2856, 0x288A, 0x7E39),
              (0x288A, 0x2D69, 0x10E8))


@lru_cache(maxsize=1)
def reader():
    spec = importlib.util.spec_from_file_location('gift_gb_reader', Path(__file__).with_name('butterflyos-gb-sprite-cache.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def qualified_rom(path):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest not in SUPPORTED_ROMS:
        raise ValueError('Use a qualified English retail Gold, Silver or Crystal ROM. Modified ROMs are refused.')
    title = SUPPORTED_ROMS[digest]
    if not data[0x134:0x143].startswith(title.encode('ascii')):
        raise ValueError('Unexpected ROM header.')
    return data, title, digest


def gift_from_rom(path, preset, dvs=None):
    data, title, digest = qualified_rom(path)
    if preset not in PRESETS:
        raise ValueError('Unknown Gen II gift.')
    if preset == 'celebi' and title == 'PM_CRYSTAL':
        raise ValueError('Use Crystal Events for the native Celebi quest. This boxed gift is for Gold/Silver.')
    dex, moves, item = PRESETS[preset]
    gb = reader()
    base = gb.GSC_LAYOUTS[title][1] + (dex - 1) * 32
    stats = data[base:base + 32]
    if len(stats) != 32 or stats[0] != dex:
        raise ValueError('Unexpected ROM base-stat table.')
    encoded = lambda text: bytes(ord(c) - ord('A') + 0x80 for c in text)
    names = gb.find_bytes(data, encoded('BULBASAUR') + b'\x50' + encoded('IVYSAUR'))
    raw_name = data[names + (dex - 1) * 10:names + dex * 10]
    nickname = gb.decode_gb_text(raw_name.split(b'\x50')[0])
    if len(raw_name) != 10 or not nickname or len(nickname) > 10 or not nickname.isascii():
        raise ValueError('Unexpected species name.')
    move_table = gb.find_bytes(data, bytes((1, 0, 40, 0, 255, 35, 0, 2, 0, 50)))
    pp = []
    for move in moves:
        at = move_table + (move - 1) * 7
        if move and (data[at] != move or not 1 <= data[at + 5] <= 40):
            raise ValueError('Unexpected move PP table.')
        pp.append(data[at + 5] if move else 0)
    level = PCNY_GIFT_LEVELS.get(preset, 5)
    growth = stats[22]
    if growth == 0:
        experience = level ** 3
    elif growth == 3:
        experience = 6 * level ** 3 // 5 - 15 * level ** 2 + 100 * level - 140
    elif growth == 4:
        experience = 4 * level ** 3 // 5
    elif growth == 5:
        experience = 5 * level ** 3 // 4
    else:
        raise ValueError('Unsupported gift growth rate.')
    dvs = list(dvs) if dvs is not None else [secrets.randbelow(16) for _ in range(4)]
    if len(dvs) != 4 or any(not isinstance(v, int) or not 0 <= v <= 15 for v in dvs):
        raise ValueError('Invalid DVs.')
    if preset in PCNY_SHINY_PRESETS:
        # Documented shiny gifts: native shiny DVs, male where the catalog specifies.
        # Player-owned generated equivalents; do not recreate donor OT/ID records.
        dvs = [10, 10, 10, 10]
    record = bytearray(32)
    record[0:6] = bytes((dex, item, *moves))
    record[8:11] = experience.to_bytes(3, 'big')
    record[21:23] = bytes((dvs[0] * 16 + dvs[1], dvs[2] * 16 + dvs[3]))
    record[23:27] = bytes(pp)
    record[27] = 70  # Native initial friendship.
    record[31] = level
    is_egg = preset in EGG_PRESETS or preset in PCNY_EGG_PRESETS
    hatch_cycles = stats[15] if is_egg else None
    if is_egg:
        if not 1 <= hatch_cycles <= 255:
            raise ValueError('Unexpected egg hatch counter.')
        record[27] = hatch_cycles
        # Native EGG nickname, read from the qualified user's ROM.
        egg_at = data.find(encoded('EGG') + b'\x50')
        if egg_at < 0:
            raise ValueError('Native egg name not found.')
        raw_name = data[egg_at:egg_at + 3] + b'\x50' * 7
    return bytes(record), {'preset': preset, 'national_species': dex, 'species': dex,
                           'nickname': ('Egg: ' + nickname) if is_egg else nickname,
                           'is_egg': is_egg, 'hatch_cycles': hatch_cycles,
                           'level': level, 'moves': list(moves),
                           'move_pps': pp, 'held_item': item, 'rom_title': title, 'rom_sha256': digest,
                           'encoded_nickname': raw_name.hex()}


def layout(crystal):
    return (0x2700, 0x2D10, 0x2A27, 0x2A47, 0x2B83, 0x2D0D, 0x1F0D) if crystal else \
           (0x2724, 0x2D6C, 0x2A4C, 0x2A6C, 0x2D69, 0x2D69, 0x7E6D)


def backup_data(data, crystal):
    if crystal:
        return data[0x1209:0x1D83]
    return b''.join(data[dest:dest + end - start] for start, end, dest in GS_MIRRORS)


def validate_save(data, crystal):
    if len(data) not in (0x8000, 0x8030):
        raise ValueError('Use an ordinary in-game save, not a save state.')
    current, active, owned, seen, end, checksum, backup_checksum = layout(crystal)
    for contents, at in ((data[0x2009:end], checksum), (backup_data(data, crystal), backup_checksum)):
        if sum(contents) & 65535 != int.from_bytes(data[at:at + 2], 'little'):
            raise ValueError('Save checksum/family mismatch. Load the matching game and save normally first.')
    if data[current] >= 14:
        raise ValueError('Invalid active PC box.')


def box_at(number):
    return (0x4000 if number < 7 else 0x6000) + number % 7 * BOX_SIZE


def validate_box(data, at):
    count = data[at]
    if count > 20 or data[at + 1 + count] != 0xFF:
        raise ValueError('Invalid PC box header. Save normally in-game first.')
    for slot in range(count):
        species = data[at + 1 + slot]
        record_species = data[at + 22 + slot * 32]
        if not 1 <= record_species <= 251 or species not in (record_species, 0xFD):
            raise ValueError('Invalid occupied PC slot; no gift prepared.')
    return count


def prepare_gift(data, rom, preset, box, slot, dvs=None):
    record, metadata = gift_from_rom(rom, preset, dvs)
    crystal = metadata['rom_title'] == 'PM_CRYSTAL'
    validate_save(data, crystal)
    if not 0 <= box < 14 or not 0 <= slot < 20:
        raise ValueError('Invalid destination box/slot.')
    current, active, owned, seen, end, checksum, backup_checksum = layout(crystal)
    banked = box_at(box)
    at = active if data[current] == box else banked
    count = validate_box(data, at)
    if count >= 20 or slot != count:
        raise ValueError('Gift requires the next empty PC slot; occupied and full boxes are refused.')
    # The active representation is authoritative for current-box records.
    target = bytearray(data[at:at + BOX_SIZE])
    record = bytearray(record); record[6:8] = data[0x2009:0x200B]
    target[22 + slot * 32:22 + (slot + 1) * 32] = record
    target[662 + slot * 11:662 + (slot + 1) * 11] = data[0x200B:0x2012] + b'\x50' * 4
    target[882 + slot * 11:882 + (slot + 1) * 11] = bytes.fromhex(metadata['encoded_nickname']) + b'\x50'
    target[0] += 1; target[1 + slot] = 0xFD if metadata['is_egg'] else record[0]; target[2 + slot] = 0xFF
    result = bytearray(data)
    result[banked:banked + BOX_SIZE] = target
    if at == active:
        result[active:active + BOX_SIZE] = target
    dex = metadata['national_species'] - 1
    for base in (() if metadata['is_egg'] else (owned, seen)):
        offset = base + dex // 8; result[offset] |= 1 << (dex % 8)
        # Update only the corresponding backup bit, preserving unrelated data.
        dest = offset - 0xE00 if crystal else offset - 0x288A + 0x10E8
        result[dest] |= 1 << (dex % 8)
    result[checksum:checksum + 2] = (sum(result[0x2009:end]) & 65535).to_bytes(2, 'little')
    result[backup_checksum:backup_checksum + 2] = (sum(backup_data(result, crystal)) & 65535).to_bytes(2, 'little')
    validate_save(result, crystal)
    return bytes(result), metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--preset', choices=PRESETS, required=True)
    parser.add_argument('--box', type=int, required=True)
    parser.add_argument('--slot', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result, metadata = prepare_gift(args.save.read_bytes(), args.rom, args.preset, args.box, args.slot)
        with args.output.open('xb') as handle:
            handle.write(result)
        print(json.dumps(metadata))
    except (OSError, ValueError, reader().CacheError) as error:
        parser.exit(1, 'Gen II gift: %s\n' % error)


if __name__ == '__main__':
    main()

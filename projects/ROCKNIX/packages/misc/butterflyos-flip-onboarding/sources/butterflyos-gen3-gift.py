#!/usr/bin/python3
"""Stage generated gift eggs and adult rewards for qualified English Gen III saves.

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

# Numeric gameplay equivalents; custom BLINK identity, not distributor records.
# national species, level, complete moves, possible held items, shiny policy, fateful
DIRECT_PRESETS = {
    'gift-jirachi': (385, 5, (273, 93, 156, 0), (169, 170), 'random', False),
    'gift-celebi': (251, 30, (215, 219, 246, 248), (0,), 'never', False),
    'gift-mew': (151, 10, (1, 144, 0, 0), (0,), 'never', True),
    'gift-deoxys': (386, 70, (322, 105, 354, 63), (0,), 'never', True),
    'gift-shiny-zigzagoon': (263, 5, (33, 45, 39, 0), (168,), 'always', False),
}
# GameCube reward equivalents. Colosseum rewards use the legacy event-location
# memo; XD gifts also retain the modern fateful flag. BLINK identity and destination
# origin policy are shared with direct gifts, not exact GameCube event records.
GAMECUBE_PRESETS = {
    'cube-pikachu': (25, 10, (84, 45, 39, 86), (202,), 'never', False),
    'cube-ageto-celebi': (251, 10, (93, 105, 215, 219), (0,), 'never', False),
    'cube-mattle-ho-oh': (250, 70, (105, 126, 241, 129), (0,), 'never', False),
    'cube-xd-chikorita': (152, 5, (246, 33, 45, 338), (0,), 'random', True),
    'cube-xd-cyndaquil': (155, 5, (179, 33, 43, 307), (0,), 'random', True),
    'cube-xd-totodile': (158, 5, (242, 10, 43, 308), (0,), 'random', True),
}
# PCNY adult batches; numeric gameplay equivalents, not distributor records.
PCNY_ADULT_PRESETS = {
    'pcny-adult-pikachu': (25, 50, (85, 97, 87, 113), (0,), 'never', False),
    'pcny-adult-gloom': (44, 50, (79, 51, 236, 80), (0,), 'never', False),
    'pcny-adult-staryu': (120, 50, (107, 113, 322, 56), (0,), 'never', False),
    'pcny-adult-seadra': (117, 45, (82, 56, 239, 58), (0,), 'never', False),
    'pcny-adult-flygon': (330, 45, (328, 242, 225, 53), (0,), 'never', False),
    'pcny-adult-altaria': (334, 45, (332, 225, 349, 53), (0,), 'never', False),
    'pcny-adult-seadra-leer': (117, 45, (82, 56, 239, 43), (0,), 'never', False),
    'pcny-adult-altaria-ice-beam': (334, 45, (36, 225, 349, 58), (0,), 'never', False),
    'pcny-adult-salamence-thrash': (373, 50, (182, 225, 37, 19), (0,), 'never', False),
    'pcny-adult-shedinja': (292, 50, (180, 109, 247, 288), (0,), 'never', False),
    'pcny-adult-cacturne': (332, 50, (185, 191, 302, 178), (0,), 'never', False),
    'pcny-adult-shuppet': (353, 25, (103, 101, 174, 180), (0,), 'never', False),
    'pcny-adult-duskull-lv25-d2': (355, 25, (50, 193, 310, 109), (0,), 'never', False),
    'pcny-adult-exploud-lv50-d3': (295, 50, (23, 304, 247, 46), (0,), 'never', False),
    'pcny-adult-exploud-lv100-d3': (295, 100, (46, 247, 280, 304), (0,), 'never', False),
    'pcny-adult-aggron-lv50-d3': (306, 50, (269, 231, 182, 232), (0,), 'never', False),
    'pcny-adult-aggron-lv100-d3': (306, 100, (231, 337, 58, 38), (0,), 'never', False),
    'pcny-adult-wailord-lv50-d3': (321, 50, (352, 59, 156, 323), (0,), 'never', False),
    'pcny-adult-wailord-lv100-d3': (321, 100, (59, 323, 89, 56), (0,), 'never', False),
    'pcny-adult-crawdaunt-lv50-d3': (342, 50, (91, 61, 152, 14), (0,), 'never', False),
    'pcny-adult-crawdaunt-lv100-d3': (342, 100, (92, 152, 258, 12), (0,), 'never', False),
    'pcny-adult-altaria-lv45-d4': (334, 45, (36, 225, 349, 287), (0,), 'never', False),
    'pcny-adult-flygon-lv45-d4': (330, 45, (328, 242, 225, 103), (0,), 'never', False),
    'pcny-adult-seadra-lv32-d4': (117, 32, (108, 43, 55, 239), (0,), 'never', False),
    'pcny-adult-salamence-lv50-d4': (373, 50, (182, 225, 184, 19), (0,), 'never', False),
    'pcny-adult-gardevoir-lv35-d5': (282, 35, (100, 347, 94, 286), (0,), 'never', False),
    'pcny-adult-tropius-lv30-d5': (357, 30, (75, 23, 230, 18), (0,), 'never', False),
    'pcny-adult-houndour-lv5-d6': (228, 5, (43, 52, 0, 0), (0,), 'never', False),
    'pcny-adult-mareep-lv5-d6': (179, 5, (33, 45, 0, 0), (0,), 'never', False),
    'pcny-adult-seviper-lv30-d7': (336, 30, (342, 103, 137, 242), (0,), 'never', False),
    'pcny-adult-absol-lv35-d7': (359, 35, (13, 44, 14, 180), (0,), 'never', False),
    'pcny-adult-absol-lv35-d7-wish': (359, 35, (13, 44, 14, 273), (0,), 'never', False),
    'pcny-adult-azurill-lv5-d8': (298, 5, (150, 204, 0, 0), (0,), 'never', False),
    'pcny-adult-wynaut-lv5-d8': (360, 5, (150, 204, 227, 0), (0,), 'never', False),
    'pcny-adult-huntail-lv20-d8': (367, 20, (250, 44, 103, 0), (0,), 'never', False),
    'pcny-adult-gorebyss-lv20-d8': (368, 20, (250, 93, 97, 0), (0,), 'never', False),
    'pcny-adult-kingdra-lv35-d9': (230, 35, (108, 43, 55, 239), (0,), 'never', False),
    'pcny-adult-zangoose-lv18-d9': (335, 18, (43, 98, 14, 210), (0,), 'never', False),
    'pcny-adult-seviper-lv18-d9': (336, 18, (35, 122, 44, 342), (0,), 'never', False),
    'pcny-adult-milotic-lv35-d9': (350, 35, (352, 239, 105, 240), (0,), 'never', False),
    'pcny-adult-sableye-lv18-d10': (302, 18, (193, 101, 310, 154), (0,), 'never', False),
    'pcny-adult-mawile-lv18-d10': (303, 18, (310, 313, 44, 230), (0,), 'never', False),
    'pcny-adult-cradily-lv40-d10': (346, 40, (51, 275, 109, 133), (0,), 'never', False),
    'pcny-adult-armaldo-lv40-d10': (348, 40, (55, 232, 182, 246), (0,), 'never', False),
    'pcny-adult-machamp-lv30-d11': (68, 30, (2, 69, 193, 279), (0,), 'never', False),
    'pcny-adult-golem-lv30-d11': (76, 30, (88, 222, 120, 205), (0,), 'never', False),
    'pcny-adult-ludicolo-lv20-d11': (272, 20, (310, 45, 71, 267), (0,), 'never', False),
    'pcny-adult-shiftry-lv20-d11': (275, 20, (1, 106, 74, 267), (0,), 'never', False),
}

# Tenth-anniversary campaigns grouped by distinct gameplay recipe.
TENTH_ANNIVERSARY_PRESETS = {
    'tenth-bulbasaur': (1, 70, (230, 74, 76, 235), (0,), 'never', False),
    'tenth-charizard': (6, 70, (17, 163, 82, 83), (0,), 'never', False),
    'tenth-blastoise': (9, 70, (182, 240, 130, 56), (0,), 'never', False),
    'tenth-pikachu-fly': (25, 70, (85, 87, 113, 19), (0,), 'never', False),
    'tenth-pikachu-standard': (25, 70, (85, 97, 87, 113), (0,), 'never', False),
    'tenth-alakazam': (65, 70, (248, 347, 94, 271), (0,), 'never', False),
    'tenth-articuno': (144, 70, (97, 170, 58, 115), (0,), 'never', False),
    'tenth-zapdos': (145, 70, (97, 197, 65, 268), (0,), 'never', False),
    'tenth-moltres': (146, 70, (97, 203, 53, 219), (0,), 'never', False),
    'tenth-dragonite': (149, 70, (97, 219, 17, 200), (0,), 'never', False),
    'tenth-typhlosion': (157, 70, (98, 172, 129, 53), (0,), 'never', False),
    'tenth-espeon': (196, 70, (60, 244, 94, 234), (0,), 'never', False),
    'tenth-umbreon': (197, 70, (185, 212, 103, 236), (0,), 'never', False),
    'tenth-raikou': (243, 70, (98, 209, 115, 242), (0,), 'never', False),
    'tenth-entei': (244, 70, (83, 23, 53, 207), (0,), 'never', False),
    'tenth-suicune': (245, 70, (16, 62, 54, 243), (0,), 'never', False),
    'tenth-tyranitar': (248, 70, (37, 184, 242, 89), (0,), 'never', False),
    'tenth-lugia': (249, 70, (105, 56, 240, 129), (0,), 'never', False),
    'tenth-ho-oh': (250, 70, (105, 126, 241, 129), (0,), 'never', False),
    'tenth-celebi': (251, 70, (246, 248, 226, 195), (0,), 'never', False),
    'tenth-blaziken': (257, 70, (299, 163, 119, 327), (0,), 'never', False),
    'tenth-absol': (359, 70, (104, 163, 248, 195), (0,), 'never', False),
    'tenth-latias': (380, 70, (296, 94, 105, 204), (0,), 'never', False),
    'tenth-latios': (381, 70, (295, 94, 105, 349), (0,), 'never', False),
}
# Regional campaign gameplay equivalents, grouping identical distributions.
REGIONAL_PRESETS = {
    'regional-jirachi-lv5': (385, 5, (273, 93, 156, 0), (0,), 'never', False),
    'regional-pikachu-ana': (25, 10, (19, 84, 39, 86), (0,), 'never', False),
    'regional-meowth': (52, 5, (10, 45, 0, 0), (0,), 'never', False),
    'regional-pikachu-surf': (25, 10, (84, 45, 86, 57), (0,), 'never', False),
    'regional-pikachu-gw': (25, 10, (45, 39, 86, 19), (0,), 'never', False),
    'regional-metang': (375, 30, (36, 93, 232, 287), (0,), 'never', False),
    'regional-wobbuffet': (202, 5, (68, 243, 219, 194), (0,), 'never', False),
    'regional-regirock': (377, 40, (174, 276, 246, 63), (0,), 'never', False),
    'regional-regice': (378, 40, (174, 276, 246, 63), (0,), 'never', False),
    'regional-registeel': (379, 40, (174, 276, 246, 63), (0,), 'never', False),
    'regional-mew-lv30': (151, 30, (1, 144, 5, 118), (0,), 'never', True),
    'regional-celebi-lv10': (251, 10, (73, 105, 215, 219), (0,), 'never', False),
    'regional-jirachi-lv30': (385, 30, (273, 94, 270, 156), (0,), 'never', False),
}
# Purified gameplay equivalents; no Shadow state or capture mechanics in GBA.
SHADOW_PRESETS = {
    'shadow-colo-296-lv30': (296, 30, (193, 116, 233, 238), (0,), 'random', False),
    'shadow-colo-153-lv30': (153, 30, (241, 235, 75, 34), (0,), 'random', False),
    'shadow-colo-156-lv30': (156, 30, (241, 108, 91, 172), (0,), 'random', False),
    'shadow-colo-159-lv30': (159, 30, (240, 184, 44, 57), (0,), 'random', False),
    'shadow-colo-164-lv30': (164, 30, (211, 95, 115, 19), (0,), 'random', False),
    'shadow-colo-180-lv30': (180, 30, (85, 86, 178, 84), (0,), 'random', False),
    'shadow-colo-188-lv30': (188, 30, (235, 79, 178, 72), (0,), 'random', False),
    'shadow-colo-195-lv30': (195, 30, (341, 133, 21, 57), (0,), 'random', False),
    'shadow-colo-200-lv30': (200, 30, (60, 109, 212, 247), (0,), 'random', False),
    'shadow-colo-193-lv33': (193, 33, (197, 48, 49, 253), (0,), 'random', False),
    'shadow-colo-162-lv33': (162, 33, (231, 270, 98, 70), (0,), 'random', False),
    'shadow-colo-218-lv30': (218, 30, (241, 281, 88, 53), (0,), 'random', False),
    'shadow-colo-223-lv20': (223, 20, (61, 199, 60, 62), (0,), 'random', False),
    'shadow-colo-226-lv33': (226, 33, (17, 48, 61, 36), (0,), 'random', False),
    'shadow-colo-211-lv33': (211, 33, (42, 107, 40, 57), (0,), 'random', False),
    'shadow-colo-307-lv33': (307, 33, (197, 347, 93, 136), (0,), 'random', False),
    'shadow-colo-206-lv33': (206, 33, (180, 137, 281, 36), (0,), 'random', False),
    'shadow-colo-333-lv33': (333, 33, (119, 47, 219, 19), (0,), 'random', False),
    'shadow-colo-185-lv35': (185, 35, (175, 335, 67, 157), (0,), 'random', False),
    'shadow-colo-237-lv38': (237, 38, (97, 116, 167, 229), (0,), 'random', False),
    'shadow-colo-244-lv40': (244, 40, (241, 43, 44, 126), (0,), 'random', False),
    'shadow-colo-166-lv40': (166, 40, (226, 219, 48, 4), (0,), 'random', False),
    'shadow-colo-245-lv40': (245, 40, (240, 43, 16, 57), (0,), 'random', False),
    'shadow-colo-245-lv40-hydro-pump': (245, 40, (240, 43, 16, 56), (0,), 'random', False),
    'shadow-colo-207-lv43': (207, 43, (185, 28, 40, 163), (0,), 'random', False),
    'shadow-colo-234-lv43': (234, 43, (310, 95, 43, 36), (0,), 'random', False),
    'shadow-colo-221-lv43': (221, 43, (203, 316, 91, 59), (0,), 'random', False),
    'shadow-colo-215-lv43': (215, 43, (185, 103, 154, 196), (0,), 'random', False),
    'shadow-colo-190-lv43': (190, 43, (226, 321, 154, 129), (0,), 'random', False),
    'shadow-colo-198-lv43': (198, 43, (185, 212, 101, 19), (0,), 'random', False),
    'shadow-colo-205-lv43': (205, 43, (153, 182, 117, 229), (0,), 'random', False),
    'shadow-colo-210-lv43': (210, 43, (44, 184, 46, 70), (0,), 'random', False),
    'shadow-colo-329-lv43': (329, 43, (242, 103, 328, 225), (0,), 'random', False),
    'shadow-colo-168-lv43': (168, 43, (169, 184, 141, 188), (0,), 'random', False),
    'shadow-colo-243-lv40': (243, 40, (240, 43, 98, 87), (0,), 'random', False),
    'shadow-colo-192-lv45': (192, 45, (241, 74, 275, 76), (0,), 'random', False),
    'shadow-colo-225-lv45': (225, 45, (59, 213, 217, 19), (0,), 'random', False),
    'shadow-colo-214-lv45': (214, 45, (179, 203, 68, 280), (0,), 'random', False),
    'shadow-colo-227-lv47': (227, 47, (65, 319, 314, 211), (0,), 'random', False),
    'shadow-colo-241-lv48': (241, 48, (208, 111, 205, 34), (0,), 'random', False),
    'shadow-colo-359-lv48': (359, 48, (195, 14, 163, 185), (0,), 'random', False),
    'shadow-colo-229-lv48': (229, 48, (185, 336, 123, 53), (0,), 'random', False),
    'shadow-colo-357-lv49': (357, 49, (76, 235, 345, 19), (0,), 'random', False),
    'shadow-colo-376-lv50': (376, 50, (63, 334, 232, 94), (0,), 'random', False),
    'shadow-colo-248-lv55': (248, 55, (242, 87, 157, 59), (0,), 'random', False),
    'shadow-colo-235-lv45': (235, 45, (166, 39, 3, 231), (0,), 'random', False),
    'shadow-colo-217-lv45': (217, 45, (185, 313, 122, 163), (0,), 'random', False),
    'shadow-colo-213-lv45': (213, 45, (219, 227, 156, 117), (0,), 'random', False),
    'shadow-colo-176-lv20': (176, 20, (118, 204, 186, 281), (0,), 'random', False),
    'shadow-xd-216-lv11': (216, 11, (216, 287, 122, 232), (0,), 'never', True),
    'shadow-xd-037-lv18': (37, 18, (257, 204, 52, 91), (0,), 'never', True),
    'shadow-xd-363-lv17': (363, 17, (62, 204, 55, 189), (0,), 'never', True),
    'shadow-xd-343-lv17': (343, 17, (317, 287, 189, 60), (0,), 'never', True),
    'shadow-xd-179-lv17': (179, 17, (34, 215, 84, 86), (0,), 'never', True),
    'shadow-xd-316-lv17': (316, 17, (351, 47, 124, 92), (0,), 'never', True),
    'shadow-xd-273-lv17': (273, 17, (202, 287, 331, 290), (0,), 'never', True),
    'shadow-xd-167-lv14': (167, 14, (91, 287, 324, 101), (0,), 'never', True),
    'shadow-xd-322-lv14': (322, 14, (36, 204, 91, 52), (0,), 'never', True),
    'shadow-xd-318-lv15': (318, 15, (352, 287, 184, 44), (0,), 'never', True),
    'shadow-xd-315-lv22': (315, 22, (345, 186, 320, 73), (0,), 'never', True),
    'shadow-xd-301-lv18': (301, 18, (290, 186, 213, 351), (0,), 'never', True),
    'shadow-xd-299-lv26': (299, 26, (85, 270, 86, 157), (0,), 'never', True),
    'shadow-xd-228-lv17': (228, 17, (185, 204, 52, 46), (0,), 'never', True),
    'shadow-xd-296-lv18': (296, 18, (280, 287, 292, 317), (0,), 'never', True),
    'shadow-xd-355-lv19': (355, 19, (247, 270, 310, 109), (0,), 'never', True),
    'shadow-xd-280-lv20': (280, 20, (351, 47, 115, 93), (0,), 'never', True),
    'shadow-xd-303-lv22': (303, 22, (206, 47, 11, 334), (0,), 'never', True),
    'shadow-xd-361-lv20': (361, 20, (352, 47, 44, 196), (0,), 'never', True),
    'shadow-xd-204-lv20': (204, 20, (42, 287, 191, 68), (0,), 'never', True),
    'shadow-xd-220-lv22': (220, 22, (246, 204, 54, 341), (0,), 'never', True),
    'shadow-xd-177-lv22': (177, 22, (248, 226, 101, 332), (0,), 'never', True),
    'shadow-xd-285-lv15': (285, 15, (206, 287, 72, 78), (0,), 'never', True),
    'shadow-xd-052-lv22': (52, 22, (163, 47, 6, 44), (0,), 'never', True),
    'shadow-xd-021-lv22': (21, 22, (206, 226, 43, 332), (0,), 'never', True),
    'shadow-xd-088-lv23': (88, 23, (188, 270, 325, 107), (0,), 'never', True),
    'shadow-xd-086-lv23': (86, 23, (57, 270, 219, 58), (0,), 'never', True),
    'shadow-xd-337-lv25': (337, 25, (94, 226, 240, 317), (0,), 'never', True),
    'shadow-xd-100-lv19': (100, 19, (243, 287, 209, 129), (0,), 'never', True),
    'shadow-xd-335-lv28': (335, 28, (280, 287, 68, 306), (0,), 'never', True),
    'shadow-xd-058-lv28': (58, 28, (53, 204, 44, 36), (0,), 'never', True),
    'shadow-xd-046-lv28': (46, 28, (147, 287, 163, 206), (0,), 'never', True),
    'shadow-xd-090-lv29': (90, 29, (36, 287, 57, 62), (0,), 'never', True),
    'shadow-xd-015-lv30': (15, 30, (188, 226, 41, 14), (0,), 'never', True),
    'shadow-xd-017-lv30': (17, 30, (17, 287, 211, 297), (0,), 'never', True),
    'shadow-xd-012-lv30': (12, 30, (94, 234, 79, 332), (0,), 'never', True),
    'shadow-xd-114-lv30': (114, 30, (76, 234, 241, 275), (0,), 'never', True),
    'shadow-xd-020-lv34': (20, 34, (162, 287, 184, 158), (0,), 'never', True),
    'shadow-xd-049-lv32': (49, 32, (318, 287, 164, 94), (0,), 'never', True),
    'shadow-xd-070-lv32': (70, 32, (345, 234, 188, 230), (0,), 'never', True),
    'shadow-xd-024-lv33': (24, 33, (188, 287, 137, 44), (0,), 'never', True),
    'shadow-xd-057-lv34': (57, 34, (238, 270, 116, 179), (0,), 'never', True),
    'shadow-xd-097-lv34': (97, 34, (94, 226, 96, 247), (0,), 'never', True),
    'shadow-xd-055-lv33': (55, 33, (127, 204, 244, 280), (0,), 'never', True),
    'shadow-xd-302-lv33': (302, 33, (247, 270, 185, 105), (0,), 'never', True),
    'shadow-xd-082-lv30': (82, 30, (38, 287, 240, 87), (0,), 'never', True),
    'shadow-xd-085-lv34': (85, 34, (65, 226, 97, 161), (0,), 'never', True),
    'shadow-xd-083-lv36': (83, 36, (163, 226, 14, 332), (0,), 'never', True),
    'shadow-xd-334-lv36': (334, 36, (225, 215, 76, 332), (0,), 'never', True),
    'shadow-xd-115-lv35': (115, 35, (89, 47, 39, 146), (0,), 'never', True),
    'shadow-xd-354-lv37': (354, 37, (185, 270, 247, 174), (0,), 'never', True),
    'shadow-xd-126-lv36': (126, 36, (126, 266, 238, 9), (0,), 'never', True),
    'shadow-xd-127-lv35': (127, 35, (12, 270, 206, 66), (0,), 'never', True),
    'shadow-xd-219-lv38': (219, 38, (257, 287, 89, 53), (0,), 'never', True),
    'shadow-xd-078-lv40': (78, 40, (76, 226, 241, 53), (0,), 'never', True),
    'shadow-xd-107-lv38': (107, 38, (5, 270, 170, 327), (0,), 'never', True),
    'shadow-xd-106-lv38': (106, 38, (136, 287, 170, 25), (0,), 'never', True),
    'shadow-xd-108-lv38': (108, 38, (38, 270, 111, 205), (0,), 'never', True),
    'shadow-xd-123-lv40': (123, 40, (13, 234, 318, 163), (0,), 'never', True),
    'shadow-xd-113-lv39': (113, 39, (85, 186, 135, 285), (0,), 'never', True),
    'shadow-xd-338-lv41': (338, 41, (94, 226, 241, 322), (0,), 'never', True),
    'shadow-xd-121-lv41': (121, 41, (127, 287, 58, 105), (0,), 'never', True),
    'shadow-xd-125-lv43': (125, 43, (238, 266, 86, 85), (0,), 'never', True),
    'shadow-xd-277-lv43': (277, 43, (143, 226, 97, 263), (0,), 'never', True),
    'shadow-xd-143-lv43': (143, 43, (90, 287, 174, 34), (0,), 'never', True),
    'shadow-xd-062-lv42': (62, 42, (56, 270, 240, 280), (0,), 'never', True),
    'shadow-xd-122-lv42': (122, 42, (94, 266, 227, 9), (0,), 'never', True),
    'shadow-xd-051-lv40': (51, 40, (89, 204, 201, 161), (0,), 'never', True),
    'shadow-xd-310-lv44': (310, 44, (87, 287, 240, 44), (0,), 'never', True),
    'shadow-xd-373-lv50': (373, 50, (337, 287, 349, 332), (0,), 'never', True),
    'shadow-xd-105-lv44': (105, 44, (89, 47, 14, 157), (0,), 'never', True),
    'shadow-xd-131-lv44': (131, 44, (56, 215, 240, 59), (0,), 'never', True),
    'shadow-xd-249-lv50': (249, 50, (354, 297, 89, 56), (0,), 'never', True),
    'shadow-xd-145-lv50': (145, 50, (326, 226, 319, 85), (0,), 'never', True),
    'shadow-xd-146-lv50': (146, 50, (326, 234, 261, 53), (0,), 'never', True),
    'shadow-xd-144-lv50': (144, 50, (326, 215, 114, 58), (0,), 'never', True),
    'shadow-xd-128-lv46': (128, 46, (89, 287, 39, 34), (0,), 'never', True),
    'shadow-xd-112-lv46': (112, 46, (224, 270, 184, 89), (0,), 'never', True),
    'shadow-xd-103-lv46': (103, 46, (94, 287, 95, 246), (0,), 'never', True),
    'shadow-xd-149-lv55': (149, 55, (63, 215, 349, 89), (0,), 'never', True),
    'shadow-xd-175-lv25': (175, 25, (266, 161, 246, 270), (0,), 'never', True),
    'shadow-xd-261-lv10': (261, 10, (91, 215, 305, 336), (0,), 'never', True),
    'shadow-xd-165-lv10': (165, 10, (60, 287, 332, 48), (0,), 'never', True),
    'shadow-ereader-175-lv20': (175, 20, (118, 204, 186, 281), (0,), 'random', False),
    'shadow-ereader-179-lv37': (179, 37, (87, 84, 86, 178), (0,), 'random', False),
    'shadow-ereader-212-lv50': (212, 50, (210, 232, 14, 163), (0,), 'random', False),
}
ZERO_IV_PRESETS = frozenset({'shadow-ereader-175-lv20', 'shadow-ereader-212-lv50', 'shadow-ereader-179-lv37'})
NATIONAL_RIBBON_PRESETS = frozenset({"regional-metang"}) | frozenset(SHADOW_PRESETS)
GIFT_PRESETS = {**DIRECT_PRESETS, **GAMECUBE_PRESETS, **PCNY_ADULT_PRESETS, **TENTH_ANNIVERSARY_PRESETS, **REGIONAL_PRESETS, **SHADOW_PRESETS}

SHINY_PRESETS = SHINY_PRESETS | frozenset(p for p, v in GIFT_PRESETS.items() if v[4] == 'always')
NEVER_SHINY_PRESETS = frozenset(p for p, v in GIFT_PRESETS.items() if v[4] == 'never')


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
    if preset in NEVER_SHINY_PRESETS:
        shiny = (ot_id & 0xFFFF) ^ (ot_id >> 16) ^ (value & 0xFFFF) ^ (value >> 16)
        return value ^ (1 << 19) if shiny < 8 else value
    if preset not in SHINY_PRESETS:
        return value
    low = value & 0xFFFF
    high = (ot_id & 0xFFFF) ^ (ot_id >> 16) ^ low ^ ((value >> 16) & 7)
    return low | (high << 16)


def make_egg(rom, save2, preset):
    egg = preset not in GIFT_PRESETS
    if egg:
        national, moves = PRESETS[preset]
        level, held, fateful = 5, 0, preset in POKEPARK_PRESETS or preset in PROMOTIONAL_PRESETS or preset in PCNY_PRESETS
    else:
        national, level, moves, items, _shiny_policy, fateful = GIFT_PRESETS[preset]
        held = secrets.choice(items)
    family, origin, mapping_at, stats_at, exp_at, moves_at, names_at = rom_profile(rom)
    # ROM tables qualified by the complete ROM SHA-256, never guessed for hacks.
    mapping = struct.unpack_from('<411H', rom, mapping_at)
    species = mapping.index(national) + 1
    stats = rom[stats_at+species*28:stats_at+(species+1)*28]
    exp = struct.unpack_from('<I', rom, exp_at+stats[19]*404+level*4)[0]
    ot_id = struct.unpack_from('<I', save2, 10)[0]
    # A distinct low trainer ID guarantees the event-memo branch even for a
    # recipient whose name happens to be BLINK. Recalculate shininess for this OT.
    if not egg: ot_id ^= 1
    personality = choose_personality(ot_id, preset)
    header = bytearray(32)
    struct.pack_into('<II', header, 0, personality, ot_id)
    encoded_name = rom[names_at+species*11:names_at+(species+1)*11]
    header[8:18] = (bytes((0xBF, 0xC1, 0xC1, 0xFF)) + b'\xff'*6) if egg else encoded_name[:10]
    header[18:20] = bytes((2, 6 if egg else 2))  # English; hasSpecies; isEgg only for eggs.
    header[20:27] = save2[:7] if egg else bytes((0xBC, 0xC6, 0xC3, 0xC8, 0xC5, 0xFF, 0xFF))  # BLINK
    growth, attacks, effort, misc = (bytearray(12) for _ in range(4))
    struct.pack_into('<HHI', growth, 0, species, held, exp)
    growth[9] = stats[17] if egg else stats[18]  # Egg cycles or base friendship.
    struct.pack_into('<4H', attacks, 0, *moves)
    attacks[8:12] = bytes(rom[moves_at+move*12+4] if move else 0 for move in moves)
    misc[1] = 253 if egg else 255  # Gift egg / generated event gift.
    origins = (0 if egg else level) | (origin << 7) | (4 << 11) | ((save2[8] & 1) << 15)  # Destination game, Poke Ball, OT gender.
    struct.pack_into('<H', misc, 2, origins)
    ivs = (0 if preset in ZERO_IV_PRESETS else secrets.randbits(30)) | ((1 << 30) if egg else 0)
    if stats[23] and personality & 1: ivs |= 1 << 31
    struct.pack_into('<I', misc, 4, ivs)
    ribbons = (1 << 31) if fateful else 0
    if preset in NATIONAL_RIBBON_PRESETS:
        ribbons |= 1 << 24  # National Ribbon: pret/pokeemerald PokemonSubstruct3.
    struct.pack_into('<I', misc, 8, ribbons)
    blocks = (growth, attacks, effort, misc)
    plain = b''.join(blocks[i] for i in ORDERS[personality % 24])
    struct.pack_into('<H', header, 28, sum(struct.unpack('<24H', plain)) & 0xFFFF)
    key = personality ^ ot_id
    encrypted = b''.join(struct.pack('<I', word ^ key) for word in struct.unpack('<12I', plain))
    encoded_name = rom[names_at+species*11:names_at+(species+1)*11]
    nickname = ''.join(chr(c-0xBB+65) for c in encoded_name if 0xBB <= c <= 0xD4)
    return bytes(header)+encrypted, {'nickname': nickname, 'species': species,
        'national_species': national, 'moves': moves, 'egg_cycles': stats[17],
        'level': level, 'held': held, 'egg': egg}


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
    parser.add_argument('--preset',choices=tuple(PRESETS)+tuple(GIFT_PRESETS),required=True)
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

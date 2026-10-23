#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Read-only Gen 1 encounter index derived from a qualified user ROM.

Table shape/map labels follow pret/pokered and pret/pokeyellow (see the
adjacent metadata). No encounter species, levels or ROM bytes are bundled.
"""
import hashlib
import json
import re
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEIGHTS = (51, 51, 39, 25, 25, 25, 13, 13, 10, 4)


def area_name(label):
    if label == 'SeaRoutes':
        return 'Routes 19 / 20'
    label = re.sub(r'([a-z])([A-Z0-9])', r'\1 \2', label)
    label = re.sub(r'(B[1-4]F|[1-7]F)$', r' \1', label)
    return ' '.join(label.split())


def table_at(data, labels):
    """Locate the pointer table by its complete alias structure; reject ambiguity."""
    size = len(labels) * 2
    found, cursor = [], 0
    while True:
        end = data.find(b'\xff\xff', cursor)
        if end < 0:
            break
        cursor = end + 1
        start = end - size
        if start < 0 or data[start:start + 24] != data[start:start + 2] * 12:
            continue
        pointers = struct.unpack_from('<%dH' % len(labels), data, start)
        aliases, reverse = {}, {}
        for label, pointer in zip(labels, pointers):
            if not 0x4000 <= pointer < 0x8000:
                break
            if aliases.get(label, pointer) != pointer or reverse.get(pointer, label) != label:
                break
            aliases[label], reverse[pointer] = pointer, label
        else:
            bank = start // 0x4000 * 0x4000
            empty = bank + pointers[0] - 0x4000
            if data[empty:empty + 2] == b'\0\0':
                found.append((bank, pointers))
    if len(found) != 1:
        raise ValueError('Unsupported or ambiguous encounter-table layout')
    return found[0]


def extract(data, game, internal_to_dex, tables=None):
    if tables is None:
        tables = json.loads((HERE / 'butterflyos-gen1-encounter-maps.json').read_text())['tables']
    labels = tables['pokeyellow' if game == 'POKEMON YELLOW' else 'pokered']
    bank, pointers = table_at(data, labels)
    index, visited = {}, set()
    for label, pointer in zip(labels, pointers):
        if label == 'Nothing' or (label, pointer) in visited:
            continue
        visited.add((label, pointer))
        pos = bank + pointer - 0x4000
        for method in ('Grass / cave', 'Surfing'):
            if not bank <= pos < min(len(data), bank + 0x4000):
                raise ValueError('Truncated encounter table')
            rate = data[pos]
            pos += 1
            if not rate:
                continue
            if pos + 20 > min(len(data), bank + 0x4000):
                raise ValueError('Truncated encounter table')
            grouped = {}
            for slot, weight in enumerate(WEIGHTS):
                level, internal = data[pos + slot * 2:pos + slot * 2 + 2]
                dex = internal_to_dex.get(internal)
                if dex is None or not 1 <= level <= 100:
                    raise ValueError('Invalid encounter species or level')
                row = grouped.setdefault(dex, {'area': area_name(label), 'method': method,
                                               'min': level, 'max': level, 'weight': 0})
                row['min'], row['max'] = min(row['min'], level), max(row['max'], level)
                row['weight'] += weight
            for dex, row in grouped.items():
                index.setdefault(str(dex), []).append(row)
            pos += 20
    return {'version': 1, 'game': game, 'rom_sha256': hashlib.sha256(data).hexdigest(),
            'coverage': 'Grass/caves and Surfing only. Fishing, gifts, trades, evolutions and special encounters are not indexed yet.',
            'species': index}


def qualified_index(path, gb, gifts):
    data = gb.read_rom(path)  # Same bounded raw/ZIP reader as shared sprites.
    digest = hashlib.sha256(data).hexdigest()
    game = gifts.SUPPORTED_ROMS.get(digest)
    if game is None:
        raise ValueError('Choose a supported English retail Red, Blue or Yellow ROM')
    order_at = gb.find_bytes(data, bytes((0x70, 0x73, 0x20, 0x23, 0x15, 0x64, 0x22, 0x50)))
    order = data[order_at:order_at + 0xbe]
    mapping = {internal: dex for internal, dex in enumerate(order, 1) if 1 <= dex <= 151}
    if set(mapping.values()) != set(range(1, 152)):
        raise ValueError('Incomplete species mapping')
    return extract(data, game, mapping)


def describe(index, dex):
    rows = index['species'].get(str(dex), [])
    lines = [index['game'].title(), 'Read from your matching ROM.', '']
    for row in rows:
        levels = str(row['min']) if row['min'] == row['max'] else '%d-%d' % (row['min'], row['max'])
        lines.append('%s | %s | Lv %s' % (row['area'], row['method'], levels))
    if not rows:
        lines.append('No grass/cave or Surfing encounters found in this game.')
    lines.extend(['', index['coverage'], 'An empty result does not mean this Pokemon is unobtainable.'])
    return '\n'.join(lines)

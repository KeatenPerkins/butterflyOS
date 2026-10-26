#!/usr/bin/env python3
"""Compile offline acquisition facts. Inputs are developer-only public sources.

No ROMs, sprites, species-name table or game dialogue are written to the output.
See documentation/BDEX_ACQUISITION_SOURCES.md for pinned inputs and provenance.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import urllib.request


POKEAPI_REV = '2bf639e5572812a67d2b94903fdcb9d095f5aeb2'
PRET_REVISIONS = {
    'pokered': '171e2c204f9c1ff8e577ca387a4bbb009e130843',
    'pokeyellow': '31b7c2ea2ba6c8c64ed083723fbaa8cbb74669cb',
    'pokegold': 'fc702b6d922aecce274782d68bba8639936a1182',
    'pokecrystal': '5c877ef55197039c9676e8e3eec6d254b1c40fe8',
    'pokeruby': '5784633ce4ef7ade1a7f2d2d0c288e3d5e6cdd7f',
    'pokeemerald': '731ad5bfd6e6f265508d0efcca0ba42f9dcf5881',
    'pokefirered': 'ce6406d8c2eaf46d543c8a2606de0c3cb1951982',
}
CSV_INPUTS = ('encounters', 'encounter_slots', 'encounter_methods',
              'encounter_condition_values', 'encounter_condition_value_prose',
              'encounter_condition_value_map', 'location_areas', 'location_area_prose',
              'locations', 'location_names', 'versions', 'pokemon_species', 'pokemon_egg_groups')
GAMES = ('red', 'blue', 'yellow', 'gold', 'silver', 'crystal',
         'ruby', 'sapphire', 'emerald', 'firered', 'leafgreen')
LIMITS = {game: 151 if i < 3 else 251 if i < 6 else 386 for i, game in enumerate(GAMES)}


def source_urls():
    sources = {name + '.csv': 'https://raw.githubusercontent.com/PokeAPI/pokeapi/%s/data/v2/csv/%s.csv' % (POKEAPI_REV, name)
               for name in CSV_INPUTS}
    sources['PokeAPI-LICENSE.txt'] = 'https://raw.githubusercontent.com/PokeAPI/pokeapi/%s/LICENSE.md' % POKEAPI_REV
    for repo, revision in PRET_REVISIONS.items():
        path = ('data/pokemon/evos_moves.asm' if repo in ('pokered', 'pokeyellow') else
                'data/pokemon/evos_attacks.asm' if repo in ('pokegold', 'pokecrystal') else
                'src/data/pokemon/evolution.h')
        sources[repo + '-evolution.txt'] = 'https://raw.githubusercontent.com/pret/%s/%s/%s' % (repo, revision, path)
    return sources


def fetch_inputs(root):
    from concurrent.futures import ThreadPoolExecutor
    root.mkdir(parents=True, exist_ok=True)
    def fetch(pair):
        name, url = pair
        data = urllib.request.urlopen(url, timeout=45).read()
        (root / name).write_bytes(data)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, source_urls().items()))


def build(root):
    def rows(name):
        with (root / (name + '.csv')).open() as stream:
            return list(csv.DictReader(stream))

    def english(name, key):
        return {row[key]: row['name'] for row in rows(name) if row['local_language_id'] == '9'}

    species = rows('pokemon_species')
    normalize = lambda s: re.sub('[^a-z0-9]', '', s.lower())
    ids = {normalize(row['identifier']): int(row['id']) for row in species}
    ids.update(nidoranf=29, nidoranm=32)
    versions = {row['id']: row['identifier'] for row in rows('versions')}
    methods = {row['id']: row['identifier'] for row in rows('encounter_methods')}
    slots = {row['id']: methods[row['encounter_method_id']] for row in rows('encounter_slots')}
    areas = {row['id']: row for row in rows('location_areas')}
    area_names = english('location_area_prose', 'location_area_id')
    location_names = english('location_names', 'location_id')
    location_ids = {row['id']: row['identifier'] for row in rows('locations')}
    condition_names = english('encounter_condition_value_prose', 'encounter_condition_value_id')
    conditions = {row['id']: row for row in rows('encounter_condition_values')}
    encounter_conditions = defaultdict(set)
    for row in rows('encounter_condition_value_map'):
        c = conditions[row['encounter_condition_value_id']]
        # Keep time, swarms, story and event gates; omit only negative defaults.
        if c['is_default'] == '0' or c['identifier'].startswith(('time-', 'tv-option-')):
            encounter_conditions[row['encounter_id']].add(condition_names.get(c['id'], c['identifier']))
    games = {game: {'encounters': {}, 'evolutions': {}} for game in GAMES}
    grouped = {game: defaultdict(dict) for game in GAMES}
    for row in rows('encounters'):
        game = versions[row['version_id']]
        if game not in games or not 1 <= int(row['pokemon_id']) <= LIMITS[game]:
            continue
        area = areas[row['location_area_id']]
        place = location_names.get(area['location_id'], location_ids[area['location_id']].replace('-', ' ').title())
        detail = area_names.get(area['id'], '')
        if detail and detail.casefold() != place.casefold():
            place += ' / ' + detail
        condition = ', '.join(sorted(encounter_conditions[row['id']]))
        key = (place, slots[row['encounter_slot_id']], condition)
        values = grouped[game][row['pokemon_id']]
        low, high = int(row['min_level']), int(row['max_level'])
        if key in values:
            low, high = min(low, values[key][0]), max(high, values[key][1])
        values[key] = low, high
    for game in games:
        games[game]['encounters'] = {
            dex: [[place, method, low, high, condition]
                  for (place, method, condition), (low, high) in sorted(entries.items())]
            for dex, entries in sorted(grouped[game].items(), key=lambda pair: int(pair[0]))}

    def dex(name):
        return ids[normalize(name.replace('SPECIES_', ''))]

    def item(name):
        return name.removeprefix('ITEM_').replace('_', ' ').title().replace('Kings Rock', "King's Rock")

    def add(target, source, method, parameter, game):
        assert 1 <= source <= LIMITS[game] and 1 <= target <= LIMITS[game]
        games[game]['evolutions'].setdefault(str(target), []).append([source, method, parameter])

    for repo, targets, generation in [
            ('pokered', ('red', 'blue'), 1), ('pokeyellow', ('yellow',), 1),
            ('pokegold', ('gold', 'silver'), 2), ('pokecrystal', ('crystal',), 2)]:
        source = None
        text = (root / (repo + '-evolution.txt')).read_text()
        for line in text.splitlines():
            match = re.match(r'([A-Za-z0-9]+)Evos(?:Moves|Attacks):', line)
            if match:
                source = ids.get(normalize(match[1]))
            fields = re.search(r'^\s*db EVOLVE_(\w+),\s*(.*?)(?:\s*;.*)?$', line)
            if not fields:
                continue
            assert source is not None, line
            kind, tail = fields.groups()
            args = [part.strip() for part in tail.split(',')]
            target, parameter = dex(args[-1]), args[0]
            if kind == 'LEVEL':
                method, parameter = 'level', int(parameter)
            elif kind == 'ITEM':
                method, parameter = 'stone', item(parameter)
            elif kind == 'TRADE':
                method, parameter = ('trade', '') if generation == 1 or parameter == '-1' else ('trade-item', item(parameter))
            elif kind == 'HAPPINESS':
                method, parameter = 'friendship', {'TR_ANYTIME': 'any', 'TR_MORNDAY': 'day', 'TR_NITE': 'night'}[parameter]
            elif kind == 'STAT':
                method, parameter = 'stats', [int(args[0]), {'ATK_LT_DEF': '<', 'ATK_GT_DEF': '>', 'ATK_EQ_DEF': '='}[args[1]]]
            else:
                raise ValueError('Unrecognised evolution: ' + line)
            for game in targets:
                add(target, source, method, parameter, game)

    for repo, targets in [('pokeruby', ('ruby', 'sapphire')), ('pokeemerald', ('emerald',)),
                          ('pokefirered', ('firered', 'leafgreen'))]:
        text = (root / (repo + '-evolution.txt')).read_text()
        blocks = re.findall(r'\[SPECIES_(\w+)\]\s*=\s*\{(.*?)\},\s*(?=\[|\n\s*\};)', text, re.S)
        assert len(blocks) > 150, (repo, len(blocks))
        for source, block in blocks:
            for kind, param, target in re.findall(r'\{EVO_(\w+),\s*(\w+),\s*SPECIES_(\w+)\}', block):
                if kind == 'LEVEL':
                    method, parameter = 'level', int(param)
                elif kind == 'ITEM':
                    method, parameter = 'stone', item(param)
                elif kind in ('TRADE', 'TRADE_ITEM'):
                    method, parameter = ('trade', '') if kind == 'TRADE' else ('trade-item', item(param))
                elif kind.startswith('FRIENDSHIP'):
                    method, parameter = 'friendship', {'FRIENDSHIP': 'any', 'FRIENDSHIP_DAY': 'day', 'FRIENDSHIP_NIGHT': 'night'}[kind]
                elif kind in ('LEVEL_ATK_GT_DEF', 'LEVEL_ATK_EQ_DEF', 'LEVEL_ATK_LT_DEF'):
                    method, parameter = 'stats', [int(param), {'LEVEL_ATK_GT_DEF': '>', 'LEVEL_ATK_EQ_DEF': '=', 'LEVEL_ATK_LT_DEF': '<'}[kind]]
                elif kind in ('LEVEL_SILCOON', 'LEVEL_CASCOON'):
                    method, parameter = 'personality', int(param)
                elif kind == 'LEVEL_NINJASK':
                    method, parameter = 'level', int(param)
                elif kind == 'LEVEL_SHEDINJA':
                    method, parameter = 'shedinja', int(param)
                elif kind == 'BEAUTY':
                    method, parameter = 'beauty', int(param)
                else:
                    raise ValueError('Unrecognised evolution: ' + kind)
                for game in targets:
                    add(dex(target), dex(source), method, parameter, game)

    # Breeding ancestry changes across generations (Gen 1 has no eggs).
    for game, data in games.items():
        parents = {int(target): entries[0][0] for target, entries in data['evolutions'].items()}
        breedable = {int(r['species_id']) for r in rows('pokemon_egg_groups')
                     if r['egg_group_id'] not in ('13', '15') and int(r['species_id']) <= LIMITS[game]}
        data['breeding'] = {}
        if LIMITS[game] == 151:
            continue
        for original in sorted(breedable):
            base, visited = original, set()
            while base in parents:
                assert base not in visited
                visited.add(base)
                base = parents[base]
            if original != base:
                data['breeding'].setdefault(str(base), []).append(original)
        # Baby species cannot breed themselves, but their evolved relatives can.
        # Incense is mandatory for these two Gen 3 babies; describe it at runtime.
        if LIMITS[game] == 386:
            data['breeding']['298'] = [183, 184]
            data['breeding']['360'] = [202]

    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in sorted(source_urls())}
    return {'version': 1, 'pokeapi_revision': POKEAPI_REV,
            'pret_revisions': PRET_REVISIONS,
            'input_sha256': hashes, 'games': games}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--download', action='store_true', help='Fetch pinned public inputs first (developer PC only)')
    args = parser.parse_args()
    if args.download:
        fetch_inputs(args.inputs)
    result = build(args.inputs)
    args.output.write_text(json.dumps(result, ensure_ascii=True, separators=(',', ':')) + '\n')
    for game, data in result['games'].items():
        print(game, len(data['encounters']), 'direct species;', len(data['evolutions']), 'evolved species')

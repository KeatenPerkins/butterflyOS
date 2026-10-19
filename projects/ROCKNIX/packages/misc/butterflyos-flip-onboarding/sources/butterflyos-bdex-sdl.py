#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Controller-first Bdex. Shares Blink's ROM cache, rendering and A/B controls."""
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time


def load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).resolve().parent
engine = load('bdex_engine', HERE / 'butterflyos-bdex.py')


def database_backups(root):
    return sorted((path for path in (Path(root) / 'backups').glob('*.sqlite3')
                   if re.fullmatch(r'(auto|manual)-[0-9]+\.sqlite3', path.name)
                   and path.is_file() and not path.is_symlink()),
                  key=lambda path: int(path.stem.split('-', 1)[1]), reverse=True)


def backup_label(path):
    label = 'Manual' if path.name.startswith('manual-') else 'Automatic'
    return (label, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(path.stat().st_mtime)))


class Bdex:
    def __init__(self, ui, store, settings_path=None):
        self.ui, self.store = ui, store
        self.blink, self.front = ui.link, ui.frontend
        self.native = engine.Native()
        self.generation = store.generation
        self.base_root = store.root if self.generation == 1 else store.root.parent
        self.position = 0
        self.filter = 'All'
        self.game = None
        self.group, self.type_id, self.sort, self.copy_sort = 'All', None, 'Pokedex', 'Import date'
        self.settings_path = Path(settings_path) if settings_path else self.base_root / 'ui-settings.json'
        self.read_settings()
        self.cache = None
        self.sprites = {}
        self.error_types = (engine.BdexError, OSError, ValueError, sqlite3.Error, subprocess.SubprocessError)

    @property
    def species_limit(self):
        return {1: 151, 2: 251, 3: 386}[self.generation]

    @property
    def games(self):
        return self.generation_games(self.generation)

    @staticmethod
    def generation_games(generation):
        return {1: ('red', 'blue', 'yellow'), 2: ('gold', 'silver', 'crystal'),
                3: ('ruby', 'sapphire', 'emerald', 'firered', 'leafgreen')}[generation]

    def read_settings(self):
        try:
            settings = json.loads(self.settings_path.read_text()).get(str(self.generation), {})
            for key, values in self.setting_choices().items():
                if key in settings and settings[key] in values:
                    setattr(self, key, settings[key])
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def switch_generation(self, generation):
        if generation != self.generation:
            root = self.base_root if generation == 1 else self.base_root / ('gen%d' % generation)
            try:
                new_store = engine.Store(root, generation=generation)
            except (sqlite3.DatabaseError, engine.BdexError) as error:
                backups = database_backups(root)
                self.ui.message('COLLECTION UNAVAILABLE', str(error))
                if not backups:
                    return
                picked = self.choose('RECOVER GEN %d DATABASE' % generation, [backup_label(path) for path in backups])
                if picked is None or not self.confirm('REPLACE COLLECTION?', 'Restore this generation from a checked backup. The replaced database is retained.'):
                    return
                engine.recover_database(root, backups[picked])
                new_store = engine.Store(root, generation=generation)
            self.store.close()
            self.store, self.generation = new_store, generation
            self.position, self.filter, self.game = 0, 'All', None
            self.group, self.type_id, self.sort, self.copy_sort = 'All', None, 'Pokedex', 'Import date'
            self.read_settings()
            self.cache = None
        cache, _ = self.blink._cache_for_generation(generation, '')
        if cache:
            try:
                if engine.cache_info(cache)['generation'] == generation:
                    self.cache = cache
            except self.error_types:
                pass

    def setting_choices(self):
        return {'filter': ['All', 'Owned', 'Missing'], 'game': [None] + list(self.games),
                'group': ['All', 'A-D', 'E-H', 'I-L', 'M-P', 'Q-T', 'U-Z'],
                'type_id': [None] + list(range(28)), 'sort': ['Pokedex', 'Alphabetical'],
                'copy_sort': ['Import date', 'Level', 'Nickname', 'Source game']}

    def save_settings(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.settings_path.with_suffix('.tmp')
        try:
            settings = json.loads(self.settings_path.read_text())
            if not isinstance(settings, dict):
                settings = {}
        except (OSError, ValueError):
            settings = {}
        settings[str(self.generation)] = {key: getattr(self, key) for key in self.setting_choices()}
        temporary.write_text(json.dumps(settings) + '\n')
        temporary.replace(self.settings_path)

    def visible_species(self, counts, names, info):
        result = []
        for dex in range(1, self.species_limit + 1):
            if self.filter == 'Owned' and not counts.get(dex):
                continue
            if self.filter == 'Missing' and counts.get(dex):
                continue
            name = names.get(dex, '').upper()
            if self.group != 'All' and (not name or not self.group[0] <= name[0] <= self.group[-1]):
                continue
            if self.type_id is not None and self.type_id not in info.get('types', {}).get(str(dex), []):
                continue
            result.append(dex)
        if self.sort == 'Alphabetical':
            result.sort(key=lambda dex: (names.get(dex, '').upper(), dex))
        return result

    def sorted_copies(self, rows):
        if self.copy_sort == 'Level':
            return sorted(rows, key=lambda row: (-(row['metadata'].get('level') or 0), row['id']))
        if self.copy_sort in ('Nickname', 'Source game'):
            field = 'name' if self.copy_sort == 'Nickname' else 'game'
            return sorted(rows, key=lambda row: (row['metadata'].get(field, '').upper(), row['id']))
        return sorted(rows, key=lambda row: (-row['imported'], row['id']))

    def choose_letter(self):
        selected = 0
        while True:
            f, link = self.front, self.blink
            f.refresh_text_scale()
            f.fill(0, 0, 640, 480, (6, 9, 22))
            f.draw_text('JUMP TO LETTER', 320, 36, 24, (36, 226, 224), center=True)
            for index in range(26):
                x, y = 60 + index % 7 * 75, 110 + index // 7 * 65
                f.fill(x, y, 65, 50, (24, 83, 153) if index == selected else (14, 30, 67))
                f.draw_text(chr(65 + index), x + 32, y + 12, 22, (255, 255, 255), center=True)
            f.draw_text('D-pad Choose   A Jump   B Back', 320, 424, 16, (210, 222, 235), center=True)
            f.sdl.SDL_RenderPresent(f.renderer)
            while True:
                key = f.next_key()
                if key is not None:
                    break
                time.sleep(0.03)
            if key in (link.KEY_ESCAPE, link.KEY_B, ord('B'), link.KEY_CANCEL, ord('X')):
                return None
            if key in (link.KEY_RETURN, link.KEY_A, ord('A'), link.KEY_CONFIRM, ord('Z')):
                return selected
            if key == link.KEY_LEFT:
                selected = (selected - 1) % 26
            elif key == link.KEY_RIGHT:
                selected = (selected + 1) % 26
            elif key == link.KEY_UP:
                selected = max(0, selected - 7)
            elif key == link.KEY_DOWN:
                selected = min(25, selected + 7)

    def filters_menu(self):
        while True:
            info = engine.cache_info(self.cache) if self.cache else {}
            labels = info.get('type_names', {})
            rows = [('Name group', self.group), ('Type', labels.get(str(self.type_id), 'Any')),
                    ('Species order', self.sort), ('Copy order', self.copy_sort),
                    ('Jump to letter', 'Choose A-Z with the D-pad; keeps active filters'),
                    ('Clear all filters', 'All species, all games, Pokedex order')]
            choice = self.choose('FILTERS AND SORTING', rows)
            if choice is None:
                return
            if choice in (0, 2, 3):
                key = {0: 'group', 2: 'sort', 3: 'copy_sort'}[choice]
                values = self.setting_choices()[key]
                picked = self.choose(rows[choice][0].upper(), [(value, '') for value in values])
                if picked is not None:
                    setattr(self, key, values[picked])
                    self.position = 0
            elif choice == 1:
                if not labels:
                    self.ui.message('ROM CACHE UPDATE NEEDED', 'Choose Prepare ROM cache to read types from your own ROM, then return here.')
                    continue
                values = [None] + sorted(map(int, labels), key=lambda ident: labels[str(ident)])
                picked = self.choose('TYPE — MATCHES EITHER TYPE', [('Any' if value is None else labels[str(value)], '') for value in values])
                if picked is not None:
                    self.type_id = values[picked]
                    self.position = 0
            elif choice == 4:
                picked = self.choose_letter()
                if picked is not None:
                    names = self.store.names()
                    names.update({int(key): value for key, value in info.get('names', {}).items()})
                    old_sort = self.sort
                    self.sort = 'Alphabetical'
                    species = self.visible_species(self.store.counts(game=self.game), names, info)
                    matches = [i for i, dex in enumerate(species) if names.get(dex, '').upper().startswith(chr(65 + picked))]
                    if matches:
                        self.position = matches[0]
                        self.save_settings()
                        return
                    self.sort = old_sort
                    self.ui.message('NO MATCHING SPECIES', 'No species beginning with this letter match the active filters.')
            elif choice == 5:
                self.filter, self.game, self.group, self.type_id = 'All', None, 'All', None
                self.sort, self.copy_sort, self.position = 'Pokedex', 'Import date', 0
            self.save_settings()

    def choose(self, title, items, selected=0):
        return self.ui.menu(title, items, selected)

    def confirm(self, title, message):
        return self.choose(title, [('Cancel', 'Keep everything unchanged'), ('Confirm', message)]) == 1

    def guarded(self, action):
        try:
            action()
        except self.error_types as error:
            self.ui.message('BDEX STOPPED SAFELY', str(error))

    def prepare_cache(self, save_path='', generation=None, force=False):
        generation = self.generation if generation is None else generation
        gb = engine.load_module('bdex_rom_cache_%d' % generation, HERE / ('butterflyos-gen3-sprite-cache.py' if generation == 3 else 'butterflyos-gb-sprite-cache.py'))
        gifts = engine.load_module('bdex_gen1_roms', HERE / ('butterflyos-gen%d-gift.py' % generation))
        choices = []
        supported = gifts.ROM_PROFILES if generation == 3 else gifts.SUPPORTED_ROMS
        for path in self.blink._rom_candidates(generation, save_path):
            try:
                digest = engine.sha(gb.read_rom_info(path)[0] if generation == 3 else gb.read_rom(path))
                if digest in supported:
                    title = ('Pokemon ' + self.generation_games(3)[{2: 0, 1: 1, 3: 2, 4: 3, 5: 4}[supported[digest][1]]].title()) if generation == 3 else supported[digest]
                    choices.append((path, title.replace('POKEMON_GLD', 'Pokemon Gold').replace('POKEMON_SLV', 'Pokemon Silver').replace('PM_CRYSTAL', 'Pokemon Crystal')))
            except (OSError, ValueError, gb.CacheError):
                pass
        if not choices:
            self.ui.message('MATCHING ROM NEEDED', 'Add a supported English retail %s ROM (.gb/.gbc/.gba or a ZIP containing one ROM). Names and sprites come from your own ROM; no game assets are included.' % ', '.join(game.title() for game in self.generation_games(generation)))
            return None
        chosen = self.choose('CHOOSE SOURCE GAME ROM', [(title, Path(path).name) for path, title in choices])
        if chosen is None:
            return None
        path, title = choices[chosen]
        self.front.draw_message('PREPARING SHARED CACHE', 'Reading your ROM. Blink and Bdex will both reuse these names and sprites.', 'Please wait')
        cache = gb.cache_rom(path, engine.CACHE_ROOT, force=True) if force else gb.cache_rom(path, engine.CACHE_ROOT)
        engine.cache_info(cache)
        if generation == self.generation:
            self.cache = str(cache)
        return str(cache)

    def refresh_sprites(self):
        self.ui.message('REFRESH SPRITES',
            'Choose the ROM for the game whose artwork needs refreshing. Bdex will rebuild its shared sprites and names, then reconnect stored copies from that exact ROM. Repeat for other games if needed.\n\nPokemon data and game saves stay unchanged. The web viewer updates after you refresh its page.')
        cache = self.prepare_cache(force=True)
        if not cache:
            return
        matched, reconnected = self.store.reconnect_cache(cache)
        self.sprites.clear()
        self.ui.message('SPRITES REFRESHED',
            'Shared artwork rebuilt. %d stored copies match this ROM; %d cache references repaired.\n\nIf a game is not listed, add its supported ROM first. Refresh your browser page to reload artwork.' % (matched, reconnected))

    def matching_cache(self, save_path, generation=None):
        generation = self.generation if generation is None else generation
        cache, _ = self.blink._cache_for_generation(generation, str(save_path))
        if cache:
            try:
                info = engine.cache_info(cache)
                if info['generation'] != generation:
                    raise engine.BdexError('Cache generation mismatch.')
                choice = self.choose('CONFIRM SOURCE GAME', [
                    ('Use ' + info['game'].title(), 'Confirm this ROM matches the selected save'),
                    ('Choose another ROM', 'Select a different matching source game'),
                    ('Cancel import', 'Leave the collection and save unchanged')])
                if choice is None or choice == 2:
                    return None
                if choice == 0:
                    if generation == self.generation:
                        self.cache = cache
                    return cache
            except self.error_types:
                pass
        return self.prepare_cache(str(save_path), generation)

    def pick_save(self, title, generation=None):
        generation = self.generation if generation is None else generation
        games = self.generation_games(generation)
        saves = self.blink.generation_saves(generation)
        if not saves:
            self.ui.message('NO GEN %d SAVES' % generation, 'Add a supported %s .srm or .sav file, save normally in-game, and close the game before trying again.' % ', '.join(game.title() for game in games))
            return None
        rows = [(entry[2], '%s: %s | %s' % (
                    'Game Card' if entry[0].startswith('/storage/games-external/') else 'OS Card',
                    Path(entry[0]).name, entry[1])) for entry in saves]
        choice = self.choose(title, rows)
        return saves[choice] if choice is not None else None

    def import_workflow(self):
        save = self.pick_save('IMPORT FROM SAVE')
        if save is None:
            return
        cache = self.matching_cache(save[0])
        if cache is None:
            return
        bundle = engine.import_bundle(self.native, save[0], cache)
        records = bundle['records']
        if not records:
            self.ui.message('NOTHING TO IMPORT', 'This save contains no supported party or PC Pokemon.')
            return
        mode = self.choose('IMPORT SELECTION', [('All Pokemon', 'Copy the party and all PC boxes'),
                    ('Choose Pokemon', 'Mark individual Pokemon or an entire box')])
        if mode is None:
            return
        if mode == 1:
            selected = set()
            groups = [('party', -1)] + [('box', box) for box in range(12 if self.generation == 1 else 14)]
            while True:
                groups_with_records = [group for group in groups if any((r['kind'], r['box']) == group for r in records)]
                items = [('Review import', '%d marked; continue to review' % len(selected))]
                items += [('Party' if kind == 'party' else 'Box %d' % (box + 1),
                           '%d Pokemon' % sum((r['kind'], r['box']) == (kind, box) for r in records)) for kind, box in groups_with_records]
                group = self.choose('MARK POKEMON', items)
                if group is None:
                    return
                if group == 0:
                    break
                members = [r for r in records if (r['kind'], r['box']) == groups_with_records[group - 1]]
                position = 0
                while True:
                    items = [('Mark all', 'Select every Pokemon here'), ('Clear marks', 'Unselect every Pokemon here')]
                    items += [('[x]' if r['key'] in selected else '[ ]', '%s | Lv. %s | %s' % (r['name'], r['level'] or '?', r['ot'])) for r in members]
                    choice = self.choose('A TOGGLE MARK / B BACK', items, position)
                    if choice is None:
                        break
                    position = choice
                    if choice == 0:
                        selected.update(r['key'] for r in members)
                    elif choice == 1:
                        selected.difference_update(r['key'] for r in members)
                    else:
                        key = members[choice - 2]['key']
                        selected.symmetric_difference_update({key})
            records = [r for r in records if r['key'] in selected]
        if not records:
            return
        unique = self.store.import_selection(records)
        repeated = len(records) - len(unique)
        if not unique:
            self.ui.message('ALREADY IN BDEX', 'All %d selected Pokemon are exact duplicates of stored copies. Nothing was imported. Copies in Trash also count; restore them from Trash if needed.' % repeated)
            return
        mode = self.choose('REVIEW IMPORT', [
            ('Import unique', '%d import; %d exact duplicates skipped' % (len(unique), repeated)),
            ('Cancel', 'Leave collection and save unchanged')])
        if mode is None or mode == 1:
            return
        if not self.confirm('COPY INTO BDEX?', '%s: %d selected. The source save will stay unchanged.' % (bundle['game'].title(), len(records))):
            return
        count = self.store.import_records(bundle, records)
        self.ui.message('IMPORT COMPLETE', '%d Pokemon copied into Bdex; %d exact duplicates skipped. The original save is unchanged.' % (count, repeated))

    def gen3_destination(self, save):
        occupied = {box: set() for box in range(14)}
        for record in save[3]:
            if record.get('box') in occupied:
                occupied[record['box']].add(record['slot'])
        boxes = [box for box in occupied if len(occupied[box]) < 30]
        if not boxes:
            self.ui.message('NO FREE PC SLOT', 'Every PC box is full. Make room in-game first.')
            return None
        picked = self.choose('COPY DESTINATION', [('Box %d' % (box + 1), '%d free slots' % (30 - len(occupied[box]))) for box in boxes])
        if picked is None:
            return None
        box = boxes[picked]
        return box, next(slot for slot in range(30) if slot not in occupied[box])

    def export_workflow(self, ident=None):
        if ident is None:
            counts, names = self.store.counts(), self.store.names()
            species = sorted(counts)
            if not species:
                self.ui.message('COLLECTION EMPTY', 'Import Pokemon before exporting.')
                return
            choice = self.choose('EXPORT SPECIES', [('%03d' % dex, '%s x%d' % (names.get(dex, 'Species #%d' % dex), counts[dex])) for dex in species])
            if choice is None:
                return
            copies = self.store.entries(species[choice])
            choice = self.choose('EXPORT WHICH COPY?', [self.copy_label(row) for row in copies])
            if choice is None:
                return
            ident = copies[choice]['id']
        target_generation = self.generation
        if self.generation == 1:
            choice = self.choose('COPY TO WHICH GENERATION?', [
                ('Gen 1', 'Red, Blue or Yellow; keeps native Gen 1 data'),
                ('Gen 2', 'Gold, Silver or Crystal; Time Capsule conversion')])
            if choice is None:
                return
            target_generation = choice + 1
        elif self.generation == 2:
            choice = self.choose('COPY TO WHICH GENERATION?', [
                ('Gen 2', 'Gold, Silver or Crystal; keeps native Gen 2 data'),
                ('Gen 3', 'Ruby/Sapphire/Emerald/FireRed/LeafGreen; hatched Pokemon only')])
            if choice is None:
                return
            target_generation = choice + 2
            if target_generation == 3 and self.store.entry(ident)['metadata'].get('egg'):
                self.ui.message('HATCH THE EGG FIRST', 'Hatch this Gen 2 egg in-game and import the hatched Pokemon before copying it to Gen 3.')
                return
        save = self.pick_save('GEN %d EXPORT DESTINATION' % target_generation, target_generation)
        if save is None:
            return
        target_cache = None
        if self.generation == 2 and target_generation == 3:
            target_cache = self.matching_cache(save[0], 3)
            if target_cache is None:
                return
        destination = self.gen3_destination(save) if target_generation == 3 else self.blink.choose_copy_destination(self.front, target_generation, save)
        if destination is None:
            return
        box, slot = destination
        conversion_note = (' Gen 1 to Gen 2 uses Time Capsule item rules, keeps moves and DVs, and starts friendship at 70. No trade evolution.'
                           if (self.generation, target_generation) == (1, 2) else
                           ' Gen 2 to Gen 3 is a one-way generated copy. Shiny status and gender are retained; DVs and stat experience become Gen 3 IVs/EVs. Verified equivalent held items are retained; others are cleared. No trade evolution.'
                           if (self.generation, target_generation) == (2, 3) else '')
        if not self.confirm('COPY INTO THIS SAVE?', '%s | Box %d, slot %d. Bdex keeps its copy. A destination-save backup is retained.%s' % (Path(save[0]).name, box + 1, slot + 1, conversion_note)):
            return
        backup = engine.export_copy(self.store, self.native, ident, save[0], box, slot, destination_generation=target_generation, destination_cache=target_cache)
        self.ui.message('EXPORT COMPLETE', 'Copied into Box %d, slot %d. The Bdex copy is unchanged.\nOriginal save backup:\n%s\nStart the game normally; do not resume an older save state.' % (box + 1, slot + 1, backup))

    def copy_label(self, row):
        record = row['metadata']
        return ('[%s] #%d' % (record['game'][0].upper(), row['id']),
                '%s%s | Lv. %s | OT %s' % ('Egg ' if record.get('egg') else 'Shiny ' if record.get('shiny') else '', record['name'], record['level'] or '?', record['ot']))

    def inspector(self, ident):
        row = self.store.entry(ident)
        record = row['metadata']
        names, info = {}, {}
        try:
            info = engine.cache_info(record['cache'])
            names = info['moves']
        except self.error_types:
            pass
        lines = [record['name'], 'Imported from: ' + record['game'].title(),
                 'Level: %s    Original trainer: %s (%05d)' % (record['level'] or '?', record['ot'], record['ot_id']),
                 'Experience: %d' % record['experience'], 'Moves:']
        lines += ['%s — PP %d, PP Ups %d' % (names.get(str(move), 'Move #%d' % move), record['pp'][index], record['pp_ups'][index]) for index, move in enumerate(record['moves']) if move]
        lines += (['EVs (HP/Atk/Def/Speed/SpAtk/SpDef): ' + ' / '.join(map(str, record['evs'])),
                   'IVs: ' + ' / '.join(map(str, record['ivs']))] if record.get('generation') == 3 else
                  ['Stat experience (HP/Atk/Def/Speed/Special):', ' / '.join(map(str, record['stat_exp'])),
                   'DVs (Atk/Def/Speed/Special): ' + ' / '.join(map(str, record['dvs']))])
        lines += [
                  'Imported: ' + time.strftime('%Y-%m-%d %H:%M', time.localtime(row['imported'] / 1e9)),
                  'Source save: ' + record['source_path'],
                  'Source position: ' + ('Party' if record['kind'] == 'party' else 'Box %d' % (record['box'] + 1)) + ', slot %d' % (record['slot'] + 1)]
        if record.get('generation', 1) in (2, 3):
            item = record.get('held_item', 0)
            lines[4:4] = ['Held item: ' + (info.get('items', {}).get(str(item), 'Item #%d' % item) if item else 'None'),
                      'Shiny: %s    Gender: %s' % ('Yes' if record['shiny'] else 'No', record['gender']),
                      'Egg: ' + ('Yes — remaining hatch cycles: %d' % record['friendship'] if record['egg'] else 'No')]
            lines += ['Friendship byte: %d    Pokerus byte: %d' % (record['friendship'], record['pokerus']),
                      'Caught data: %04x (preserved unchanged)' % record['caught_data']]
            if record['generation'] == 3:
                lines += ['Nature: %s    Ability slot: %d' % (record['nature'], record['ability_slot']),
                          'Personality: %08x    Secret ID: %05d' % (record['personality'], record['secret_id']),
                          'Origin game: %d    Met location: %d    Met level: %d' % (record['origin_game'], record['met_location'], record['met_level']),
                          'Ball: %d    Language: %d    Markings: %02x' % (record['ball'], record['language'], record['markings']),
                          'Ribbons / fateful flags: %08x' % record['ribbons'],
                          'Contest stats: ' + ' / '.join(map(str, record['contest']))]
        else:
            lines[4:4] = ['HP when archived: %d    Status byte: %d' % (record['hp'], record['status']),
                      'Gen 1 has no held items or shiny designation.']
        lines.append('History:')
        for event in self.store.history(ident):
            lines.append('%s — %s' % (time.strftime('%Y-%m-%d %H:%M', time.localtime(event['created'] / 1e9)), event['action']))
            if event['action'] == 'export':
                detail = json.loads(event['detail'])
                lines.append('%s | Box %d, slot %d' % (detail['destination'], detail['box'], detail['slot']))
        self.ui.message('STORED POKEMON #%d' % ident, '\n'.join(lines))

    def copies(self, dex):
        position = 0
        while True:
            rows = self.sorted_copies(self.store.entries(dex, game=self.game))
            if not rows:
                self.ui.message('NO STORED COPIES', 'No copies match this species and source filter. Use Import to copy Pokemon from a save.')
                return
            choice = self.choose('STORED COPIES', [self.copy_label(row) for row in rows], position)
            if choice is None:
                return
            position = choice
            ident = rows[choice]['id']
            action = self.choose('STORED COPY #%d' % ident, [('Inspect', 'Moves, PP, trainer, DVs and source'),
                         ('Export copy', 'Copy to Gen %d or Gen %d' % (self.generation, self.generation + 1) if self.generation < 3 else 'Copy to an empty Gen 3 PC slot'),
                         ('Move to Trash', 'Recoverable; source save stays unchanged')])
            if action == 0:
                self.inspector(ident)
            elif action == 1:
                self.guarded(lambda: self.export_workflow(ident))
            elif action == 2 and self.confirm('MOVE TO TRASH?', 'This stored copy can be recovered from Options > Trash.'):
                self.store.trash(ident)

    def recovery(self):
        backups = database_backups(self.store.root)
        if not backups:
            self.ui.message('NO DATABASE BACKUPS', 'Create a database backup first.')
            return
        choice = self.choose('RECOVER ENTIRE COLLECTION', [backup_label(path) for path in backups])
        if choice is None or not self.confirm('REPLACE COLLECTION?', 'Restore the entire collection to this backup. The replaced database is retained for recovery.'):
            return
        root = self.store.root
        self.store.close()
        try:
            engine.recover_database(root, backups[choice])
        finally:
            self.store = engine.Store(root, generation=self.generation)
        self.ui.message('COLLECTION RECOVERED', 'The selected database backup was restored. Your game saves were not changed.')

    def options(self):
        while True:
            choice = self.choose('GEN %d OPTIONS' % self.generation, [
                ('Species filter', self.filter), ('Source game', (self.game or 'All').title()),
                ('Prepare ROM cache', 'Share sprites and names with Blink'),
                ('Trash', 'Inspect, restore or permanently delete copies'),
                ('Database backup', 'Create a checked collection backup'),
                ('Database recovery', 'Restore the entire collection from a backup'),
                ('About Bdex', 'Storage, safety and current scope'),
                ('Filters and sorting', 'Name group, type, sorting, jump, clear all'),
                ('Web viewer', 'Read-only collection viewer on your local network'),
                ('Refresh sprites', 'Rebuild ROM artwork and repair matching cache references')])
            if choice is None:
                return
            if choice == 0:
                values = ['All', 'Owned', 'Missing']
                picked = self.choose('SPECIES FILTER', [(value, 'Show ' + value.lower() + ' species') for value in values])
                if picked is not None:
                    self.filter = values[picked]
                    self.position = 0
            elif choice == 1:
                values = [None] + list(self.games)
                picked = self.choose('IMPORTED-FROM FILTER', [((value or 'All').title(), 'Filter stored copies by confirmed source game') for value in values])
                if picked is not None:
                    self.game = values[picked]
                    self.position = 0
            elif choice == 9:
                self.guarded(self.refresh_sprites)
            elif choice == 8:
                self.guarded(self.web_viewer)
            elif choice == 7:
                self.filters_menu()
            elif choice == 2:
                self.guarded(self.prepare_cache)
            elif choice == 3:
                while True:
                    rows = self.store.entries(trash=True)
                    if not rows:
                        self.ui.message('TRASH EMPTY', 'Removed copies can be recovered here. Nothing is automatically purged.')
                        break
                    picked = self.choose('TRASH', [self.copy_label(row) for row in rows])
                    if picked is None:
                        break
                    ident = rows[picked]['id']
                    action = self.choose('TRASHED COPY', [
                        ('Inspect', 'Review this stored Pokemon'),
                        ('Restore', 'Return this copy to the collection'),
                        ('Delete permanently', 'Remove this one stored copy from the database')])
                    if action == 0:
                        self.inspector(ident)
                    elif action == 1:
                        self.store.trash(ident, restore=True)
                    elif action == 2:
                        record = rows[picked]['metadata']
                        if self.confirm('DELETE THIS COPY PERMANENTLY?',
                                        '%s [%s], copy #%d. It cannot be restored from Trash. Game saves and other stored copies stay unchanged.' %
                                        (record['name'], record['game'].title(), ident)):
                            self.store.delete(ident)
                            self.ui.message('COPY DELETED', 'This copy was removed from Bdex. An older whole-database backup can still contain it.')
            elif choice == 4:
                path = self.store.backup(manual=True)
                self.ui.message('DATABASE BACKUP CREATED', 'Copy this file to a PC or another drive too:\n%s\nIt includes the collection and its source snapshots, but not ROM-derived sprites.' % path)
            elif choice == 5:
                self.guarded(self.recovery)
            elif choice == 6:
                self.ui.message('ABOUT BDEX', 'Gen 1, Gen 2 and Gen 3 collection prototype. Forward copy exports: Gen 1 to Gen 2, Gen 2 to Gen 3. An optional read-only web viewer is available in Options.\n\nImports and exports copy; originals stay intact. Source badges mean imported from the selected game, not necessarily the Pokemon\'s birthplace.\n\nExact native-record duplicates are skipped across all saves, cards, games and slots. Different native data can be stored separately. Copies in Trash also block duplicate imports; restore them from Trash instead.\n\nCollections: /storage/bdex/collection.sqlite3 (Gen 1), /storage/bdex/gen2/collection.sqlite3 (Gen 2), /storage/bdex/gen3/collection.sqlite3 (Gen 3)\nThree automatic database backups are kept before changes; manual backups remain until you remove them. Copy a database backup off the device for card-failure protection. Automatic Save Backup does not yet include Bdex databases.\n\nNo ROMs, saves, names or sprites are bundled.')

            self.save_settings()

    def web_viewer(self):
        web = load('bdex_web_settings', HERE / 'butterflyos-bdex-web.py')
        while True:
            config = web.settings()
            enabled = config.get('enabled', False)
            choice = self.choose('READ-ONLY WEB VIEWER', [
                ('Connection details', 'Use your root SSH password'),
                ('Disable viewer' if enabled else 'Enable viewer', 'Current setting: ' + ('On' if enabled else 'Off'))])
            if choice is None:
                return
            if choice == 1:
                config = web.configure(not enabled)
                subprocess.run(['systemctl', 'restart' if not enabled else 'stop', 'butterflyos-bdex-web.service'], check=True, timeout=20)
            addresses = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5).stdout.split()
            address = next((value for value in addresses if ':' not in value), 'DEVICE-IP')
            self.ui.message('WEB VIEWER CONNECTION',
                'Status: %s\nAddress: http://%s:8088\nUsername: bdex\nPassword: your root SSH password\n\nSet or change it in Settings > Network Settings > Set SSH Password. Password changes apply immediately.\n\nUse a browser on the same trusted network. The device must remain awake. Disable the viewer here when finished.' %
                ('On' if config.get('enabled') else 'Off', address))

    def sprite(self, cache, internal, shiny=False):
        if not cache or not internal:
            return None
        path = str(Path(cache) / ('front-shiny' if shiny else 'front') / ('%03d.png' % internal))
        if path not in self.sprites:
            self.sprites[path] = self.blink._read_cache_png(path)
        return self.sprites[path]

    def draw_collection(self, species, selected, counts, names, tab):
        f = self.front
        f.refresh_text_scale()
        f.fill(0, 0, 640, 480, (6, 9, 22))
        f.outline(10, 10, 620, 460, (38, 129, 190), 3)
        f.draw_text('BDEX — GEN %d' % self.generation, 30, 25, 24, (36, 226, 224), bold=True)
        f.draw_text('Collected %d / %d   Stored %d' % (len(counts), self.species_limit, sum(counts.values())), 30, 59, 15, (210, 222, 235))
        for index, title in enumerate(('Collection', 'Import', 'Export', 'Options')):
            x = 28 + index * 147
            f.fill(x, 87, 141, 33, (24, 83, 153) if index == tab else (14, 30, 67))
            f.draw_text(title, x + 70, 94, 16, (255, 255, 255), bold=(index == tab), center=True)
        labels = engine.cache_info(self.cache).get('type_names', {}) if self.cache else {}
        summary = '%s | %s | %s | %s | %d results' % (self.filter, self.group,
                    labels.get(str(self.type_id), 'Any type'), (self.game or 'All games').title(), len(species))
        f.draw_text(summary, 30, 128, 12, (153, 187, 220))
        f.outline(24, 154, 377, 254, (35, 88, 160), 2)
        if not species:
            f.draw_text('No species match this filter.', 38, 180, 16, (222, 231, 242))
        else:
            start = max(0, min(selected - 3, len(species) - 7))
            for row, dex in enumerate(species[start:start + 7]):
                y = 171 + row * 32
                if dex == species[selected]:
                    f.fill(31, y - 4, 362, 29, (24, 83, 153))
                f.draw_text('%03d %s' % (dex, names.get(dex, 'Species #%d' % dex)), 39, y, 15, (255, 255, 255))
                f.draw_text('x%d' % counts.get(dex, 0), 341, y, 15, (36, 226, 224))
            dex = species[selected]
            copies = self.store.entries(dex, game=self.game)
            cache = copies[0]['metadata']['cache'] if copies else self.cache
            internal = copies[0]['metadata']['species'] if copies else None
            if internal is None and cache:
                try:
                    internal = engine.cache_info(cache)['internal'].get(dex)
                except self.error_types:
                    pass
            image = self.sprite(cache, internal, copies[0]['metadata'].get('shiny', False) if copies else False)
            if image:
                width, height, pixels = image
                scale = max(1, min(2, 164 // max(width, height)))
                f.fill(417, 178, 190, 161, (216, 220, 226))
                for y in range(height):
                    for x in range(width):
                        offset = (y * width + x) * 4
                        r, g, b, alpha = pixels[offset:offset + 4]
                        if alpha:
                            f.fill(512 - width * scale // 2 + x * scale, 258 - height * scale // 2 + y * scale, scale, scale, (r, g, b))
            else:
                f.draw_text('ROM cache needed', 512, 245, 13, (255, 173, 74), center=True)
            # Text accompanies color. Five Gen 3 sources use two compact rows.
            colors = ((240, 80, 90), (80, 150, 255), (245, 210, 75)) if self.generation == 1 else ((240, 195, 70), (190, 202, 214), (130, 140, 245))
            badges = ('R', 'B', 'Y') if self.generation == 1 else ('G', 'S', 'C') if self.generation == 2 else ('R', 'S', 'E', 'FR', 'LG')
            for index, game in enumerate(self.games):
                x, y = 420 + index % 3 * 63, 354 + index // 3 * 24
                count = sum(row['metadata']['game'] == game for row in copies)
                f.fill(x, y + 5, 8, 8, colors[index % 3])
                f.draw_text('%s:%d' % (badges[index], count), x + 12, y, 13, (220, 230, 240))
        f.draw_text('LEFT/RIGHT Tabs   UP/DOWN Species', 320, 426, 13, (150, 176, 202), center=True)
        f.draw_text('A Select / View   B Back', 320, 446, 13, (150, 176, 202), center=True)
        f.sdl.SDL_RenderPresent(f.renderer)

    def collection(self):
        tab, dirty = 0, True
        while True:
            if dirty:
                counts = self.store.counts(game=self.game)
                names = self.store.names()
                info = {}
                if self.cache:
                    try:
                        info = engine.cache_info(self.cache)
                        names.update({int(dex): name for dex, name in info['names'].items()})
                    except self.error_types:
                        pass
                species = self.visible_species(counts, names, info)
                self.position = min(self.position, max(0, len(species) - 1))
                self.draw_collection(species, self.position, counts, names, tab)
                dirty = False
            key = self.front.next_key()
            if key is None:
                time.sleep(0.03)
                continue
            dirty = True
            link = self.blink
            if key in (link.KEY_ESCAPE, link.KEY_B, ord('B'), link.KEY_CANCEL, ord('X')):
                return
            if key == link.KEY_LEFT:
                tab = (tab - 1) % 4
            elif key == link.KEY_RIGHT:
                tab = (tab + 1) % 4
            elif key == link.KEY_UP and species:
                self.position = (self.position - 1) % len(species)
            elif key == link.KEY_DOWN and species:
                self.position = (self.position + 1) % len(species)
            elif key in (link.KEY_RETURN, link.KEY_A, ord('A'), link.KEY_CONFIRM, ord('Z')):
                if tab == 0 and species:
                    self.guarded(lambda: self.copies(species[self.position]))
                elif tab == 1:
                    self.guarded(self.import_workflow)
                elif tab == 2:
                    self.guarded(self.export_workflow)
                elif tab == 3:
                    self.guarded(self.options)

    def run(self):
        while True:
            choice = self.choose('BDEX', [('Gen 1', '151 species | party and PC imports | safe copy exports'),
                                        ('Gen 2', '251 species | Gold, Silver and Crystal'), ('Gen 3', '386 species | Ruby/Sapphire/Emerald/FireRed/LeafGreen'),
                                        ('Close', 'Return to Tools')])
            if choice is None or choice == 3:
                return
            if choice in (0, 1, 2):
                self.guarded(lambda: self.switch_generation(choice + 1))
                if self.generation != choice + 1:
                    continue
                if not self.store.names():
                    try:
                        engine.cache_info(self.cache or '')
                    except self.error_types:
                        self.ui.message('PREPARE SPECIES NAMES', 'Choose your matching ROM to read all species names and sprites. Cancel to browse by number instead. This cache is also shared with Blink.')
                        self.guarded(self.prepare_cache)
                self.guarded(self.collection)
            else:
                self.ui.message('COMING LATER', 'Gen 1 and Gen 2 are available for testing. This option does not read or change later-generation saves.')


def main():
    common = load('bdex_tool_ui', HERE / 'butterflyos-tool-ui.py')
    ui, app = None, None
    try:
        ui = common.ToolUI('Bdex')
        try:
            store = engine.Store()
        except (sqlite3.DatabaseError, engine.BdexError) as error:
            ui.message('COLLECTION UNAVAILABLE', str(error) + '\nChoose a database backup to recover; the current database will be retained.')
            backups = database_backups(engine.ROOT)
            if not backups:
                return 1
            choice = ui.menu('RECOVER DATABASE', [backup_label(path) for path in backups])
            if choice is None or ui.menu('CONFIRM RECOVERY', [('Cancel', 'Leave files unchanged'), ('Recover', 'Restore the selected collection backup')]) != 1:
                return 0
            engine.recover_database(engine.ROOT, backups[choice])
            store = engine.Store()
        app = Bdex(ui, store)
        cache, _ = app.blink._cache_for_generation(1, '')
        if cache:
            app.cache = cache
        app.run()
        return 0
    except Exception as error:
        if ui:
            ui.message('BDEX ERROR', str(error))
        else:
            print('Bdex initialization failed: ' + str(error), file=sys.stderr)
        return 1
    finally:
        if app:
            app.store.close()
        if ui:
            ui.close()


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Read-only, version-specific acquisition guidance for the original Gen 1-3 games."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
TITLES = dict(red='Red', blue='Blue', yellow='Yellow', gold='Gold', silver='Silver',
              crystal='Crystal', ruby='Ruby', sapphire='Sapphire', emerald='Emerald',
              firered='FireRed', leafgreen='LeafGreen')
GENERATION = {game: 1 if i < 3 else 2 if i < 6 else 3 for i, game in enumerate(TITLES)}
LIMITS = {1: 151, 2: 251, 3: 386}
METHODS = {'walk': 'Grass / cave', 'surf': 'Surfing', 'old-rod': 'Old Rod',
           'good-rod': 'Good Rod', 'super-rod': 'Super Rod', 'rock-smash': 'Rock Smash',
           'headbutt-low': 'Headbutt (tree group 1)', 'headbutt-normal': 'Headbutt (tree group 2)',
           'headbutt-high': 'Headbutt (tree group 3)', 'gift': 'Gift / prize / fossil revival',
           'gift-egg': 'Gift Egg', 'static': 'Special encounter', 'pokeflute': 'Use Poke Flute',
           'squirt-bottle': 'Use SquirtBottle', 'wailmer-pail': 'Use Wailmer Pail',
           'seaweed': 'Underwater seaweed', 'roaming-grass': 'Roaming (land)',
           'roaming-water': 'Roaming (water)', 'devon-scope': 'Use Devon Scope',
           'feebas-tile-fishing': 'Fishing (six special Route 119 tiles)', 'npc-trade': 'NPC trade',
           'colosseum-bonus-disc-us': 'Historical US Colosseum Bonus Disc',
           'colosseum-bonus-disc-jpn': 'Historical Japanese Colosseum Bonus Disc',
           'pokemon-channel-pal': 'Historical PAL Pokemon Channel'}


@lru_cache(maxsize=1)
def reference():
    data = json.loads((HERE / 'butterflyos-bdex-acquisition.json').read_text())
    if data.get('version') != 1 or set(data.get('games', {})) != set(TITLES):
        raise ValueError('Unsupported acquisition guide data; reinstall Bdex')
    return data['games']


def supported_games(generation, profiles):
    """Reuse Blink/Bdex full-ROM hash allowlists, never infer a game from its filename."""
    if generation == 1:
        names = {'POKEMON RED': 'red', 'POKEMON BLUE': 'blue', 'POKEMON YELLOW': 'yellow'}
        return {digest: names[title] for digest, title in profiles.SUPPORTED_ROMS.items()}
    if generation == 2:
        names = {'POKEMON_GLD': 'gold', 'POKEMON_SLV': 'silver', 'PM_CRYSTAL': 'crystal'}
        return {digest: names[title] for digest, title in profiles.SUPPORTED_ROMS.items()}
    if generation == 3:
        names = {1: 'sapphire', 2: 'ruby', 3: 'emerald', 4: 'firered', 5: 'leafgreen'}
        return {digest: names[profile[1]] for digest, profile in profiles.ROM_PROFILES.items()}
    raise ValueError('Unsupported generation')


def qualify(path, reader, allowlist):
    try:
        data = reader(path)
    except (zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError) as error:
        raise ValueError('Cannot read the selected ROM archive: ' + str(error)) from error
    game = allowlist.get(hashlib.sha256(data).hexdigest())
    if game is None:
        raise ValueError('Choose a qualified English retail ROM; other languages, revisions and hacks are not supported')
    return game, data


def evolution_text(game, source, method, parameter, name):
    prefix = name(source) + ': '
    if method == 'level':
        return prefix + 'level up to Lv %d or higher.' % parameter
    if method == 'stone':
        extra = ' The starter in Yellow refuses the stone; trade it to Red/Blue to evolve it.' if game == 'yellow' and source == 25 else ''
        return prefix + 'use %s.' % parameter + extra
    if method in ('trade', 'trade-item'):
        held = ' while holding %s' % parameter if method == 'trade-item' else ''
        return prefix + 'trade in-game%s. Blink/Bdex copies do not trigger evolution; use a compatible Bslap session.' % held
    if method == 'friendship':
        if game in ('firered', 'leafgreen') and parameter != 'any':
            return prefix + 'this time-of-day evolution is unavailable in FireRed/LeafGreen. Evolve in Ruby/Sapphire/Emerald, then trade back after unlocking trading.'
        time = ''
        if parameter != 'any':
            if GENERATION[game] == 2:
                time = ' at 04:00-17:59' if parameter == 'day' else ' at 18:00-03:59'
            else:
                time = ' at 12:00-23:59' if parameter == 'day' else ' at 00:00-11:59'
        return prefix + 'level up with friendship at least 220%s.' % time
    if method == 'stats':
        return prefix + 'level up at Lv %d or higher with Attack %s Defense (actual stats, not IVs/EVs).' % tuple(parameter)
    if method == 'personality':
        return prefix + 'level up at Lv %d. The branch is fixed by its personality value; changing time does not change the result.' % parameter
    if method == 'shedinja':
        return prefix + 'evolve into %s at Lv %d or higher with an empty party slot; this creates an extra Pokemon. Gen 3 does not require a spare Poke Ball.' % (name(291), parameter)
    if method == 'beauty':
        if game in ('firered', 'leafgreen'):
            return prefix + 'raise Beauty to at least 170 in Ruby/Sapphire/Emerald using Pokeblocks, then level up. Beauty cannot be raised in FireRed/LeafGreen.'
        return prefix + 'raise Beauty to at least 170 using Pokeblocks, then level up. Gen 3 does not use a Prism Scale trade.'
    raise ValueError('Unknown evolution method: ' + method)


def special_notes(game, dex):
    notes = []
    generation = GENERATION[game]
    if generation == 1 and dex == 151:
        notes.append('Historical event distribution only in ordinary retail play; no normal wild encounter. Blink offers a generated gift equivalent. Glitches are not indexed.')
    if generation == 2 and dex in (151, 251):
        notes.append('Historical event-only source; no ordinary repeatable wild encounter in the supported English retail ROM.')
        if dex == 151:
            notes.append('A Gen 1 copy can also be brought over through the in-game Time Capsule or a supported Blink/Bdex Gen 1 to Gen 2 copy.')
        if game == 'crystal' and dex == 251:
            notes.append('The English retail GS Ball quest is not normally enabled. Blink can enable/replay that quest; Virtual Console release availability does not apply to this ROM.')
    if generation == 3:
        if game in ('firered', 'leafgreen'):
            notes.append('FireRed/LeafGreen restrict non-Kanto evolutions until the National Pokedex. Cross-region trades and breeding require postgame progress, including Celio\'s Ruby/Sapphire quest for the trading link.')
        if dex == 151:
            if game == 'emerald':
                notes.append('Faraway Island requires the Old Sea Map. Its original distribution was for Japanese Emerald; this is not an ordinary English retail encounter. Blink provides a separately generated event equivalent.')
            else:
                notes.append('No ordinary in-game source here; use a compatible trade or a separately generated Blink gift/event equivalent.')
        if dex in (249, 250, 386):
            ticket = 'MysticTicket for Navel Rock' if dex in (249, 250) else 'AuroraTicket for Birth Island'
            if game in ('emerald', 'firered', 'leafgreen'):
                notes.append('Historical event: requires %s and the corresponding event access flags. The island is not normally accessible; Blink has separate event tools.' % ticket)
            else:
                notes.append('No island event access in Ruby/Sapphire for this species; trade from another compatible game or use a separate gift equivalent.')
        if dex == 251:
            notes.append('Historical Japanese Colosseum Bonus Disc distribution, not a normal wild encounter. Regional/hardware requirements applied; Blink offers a generated gift equivalent.')
        if dex == 385:
            notes.append('Historical US Colosseum Bonus Disc or PAL Pokemon Channel distribution to compatible Ruby/Sapphire saves; other games require a trade or a separate gift equivalent.')
        if dex in (380, 381):
            if game == 'emerald':
                color = 'red' if dex == 380 else 'blue'
                notes.append('After the Hall of Fame, choose %s in the TV report for this roamer. The opposite species is on Southern Island only with historical Eon Ticket access.' % color)
            elif game in ('ruby', 'sapphire'):
                roamer = 381 if game == 'ruby' else 380
                notes.append('Postgame roamer.' if dex == roamer else 'Southern Island requires historical Eon Ticket access; this is not ordinary island access.')
        if game in ('firered', 'leafgreen') and dex in (243, 244, 245):
            starter = {243: 7, 244: 1, 245: 4}[dex]
            notes.append('One beast roams after completing Celio\'s Network Machine quest, determined by your starter (#%03d for this beast). A second Elite Four win is not the actual trigger.' % starter)
        if game == 'emerald' and dex == 349:
            notes.append('Only six water tiles on Route 119 contain this species. Any rod works; fish repeatedly on a tile. Changing the Dewford trendy phrase can change the tiles.')
    if generation >= 2 and dex in (29, 32):
        notes.append('Breeding the female line can produce either Nidoran sex; Nidorina/Nidoqueen themselves cannot breed.')
    if generation == 3 and dex in (313, 314):
        notes.append('Breeding Illumise can produce either Volbeat or Illumise. Volbeat is male-only; Ditto can be used where available.')
    return notes


def describe(game, dex, names=None, rom_index=None):
    """All facts are read-only. Missing reference rows never prove unobtainability."""
    if game not in TITLES or not 1 <= dex <= LIMITS[GENERATION[game]]:
        raise ValueError('Species is outside the selected game generation')
    names = names or {}
    def name(number):
        label = names.get(number, names.get(str(number), ''))
        return '#%03d%s' % (number, (' ' + label) if label else '')

    guide = reference()[game]
    lines = [TITLES[game] + ' - ' + name(dex), 'Offline acquisition guide; no save progress is inspected.', '']
    if rom_index is not None:
        lines += ['GRASS / CAVE / SURF - READ FROM YOUR ROM']
        for row in rom_index['species'].get(str(dex), []):
            levels = str(row['min']) if row['min'] == row['max'] else '%d-%d' % (row['min'], row['max'])
            lines.append('%s | %s | Lv %s' % (row['area'], row['method'], levels))
        lines.append('')

    def source_rows(number, include_wild=True):
        result = []
        for place, method, low, high, condition in guide['encounters'].get(str(number), []):
            if not include_wild and method in ('walk', 'surf'):
                continue
            # VC Crystal event is not in the qualified original retail game.
            if game == 'crystal' and number == 251:
                continue
            # Dataset's FRLG roaming prerequisite is corrected by special_notes.
            if game in ('firered', 'leafgreen') and number in (243, 244, 245):
                condition = ''
            level = str(low) if low == high else '%d-%d' % (low, high)
            text = '%s | %s | Lv %s' % (place, METHODS[method], level)
            if condition:
                text += ' | ' + condition
            result.append(text)
        return result

    for note in special_notes(game, dex):
        lines.extend([note, ''])
    evolutions = guide['evolutions'].get(str(dex), [])
    if evolutions:
        lines += ['EVOLUTION']
        for source, method, parameter in evolutions:
            lines.append(evolution_text(game, source, method, parameter, name))
        lines.append('')
    direct = source_rows(dex, include_wild=rom_index is None)
    if direct:
        lines += ['LOCATIONS / OTHER SOURCES - REFERENCE DATA'] + direct + ['']
    breed = guide['breeding'].get(str(dex), [])
    if breed:
        incense = {298: 'Sea Incense', 360: 'Lax Incense'}.get(dex)
        lines += ['BREEDING', 'Hatch an Egg from a compatible female relative or a breedable relative with Ditto: ' + ', '.join(name(n) for n in breed) + '.']
        if incense:
            lines.append('A parent must hold %s; otherwise the Egg hatches as the evolved species.' % incense)
        lines += ['Parents must be compatible. Baby Pokemon cannot breed. Use the breeding Day Care; FireRed/LeafGreen use Four Island after postgame access.', '']
    # Show the chain and base locations, so "trade Kadabra" is actionable even
    # when Kadabra itself has no direct encounter in the selected game.
    visited = {dex}
    def other_versions(number):
        return [TITLES[g] for g, data in reference().items()
                if GENERATION[g] == GENERATION[game] and g != game
                and data['encounters'].get(str(number))]

    def ancestors(number):
        for source, method, parameter in guide['evolutions'].get(str(number), []):
            if source in visited:
                continue
            visited.add(source)
            rows = source_rows(source)
            lines.extend(['FIND THE PRE-EVOLUTION: ' + name(source)] + rows)
            if not rows and not guide['evolutions'].get(str(source)):
                others = other_versions(source)
                if others:
                    lines.append('Recorded direct sources in other versions: ' + ', '.join(others) + '. A compatible trade/copy is needed to bring it here.')
                else:
                    lines.append('No direct source recorded in this game; a compatible trade, breeding, or special source may be needed.')
            for before, how, value in guide['evolutions'].get(str(source), []):
                lines.append(evolution_text(game, before, how, value, name))
            lines.append('')
            ancestors(source)
    ancestors(dex)
    if not direct and not evolutions and not breed:
        others = other_versions(dex)
        if others:
            lines += ['Other versions with recorded direct sources: ' + ', '.join(others) + '.', 'Use a compatible in-game trade or supported Blink/Bdex copy. Version/progress restrictions still apply.', '']
        lines += ['No ordinary source is recorded here. This is not proof that the Pokemon is unobtainable; a trade, historical event, or unindexed special source may be needed.', '']
    lines += ['Reference coverage is not a walkthrough: gifts can be one-time or choice-dependent; story, item, version and historical event requirements apply.',
              'This guide does not create Pokemon, trigger evolution, activate events or change your saves.']
    return '\n'.join(lines)

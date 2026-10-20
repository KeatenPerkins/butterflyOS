#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Stage native Gen III island events in an isolated output; never edit inputs.

Numeric layouts/flags follow pret/pokeruby, pret/pokeemerald and pret/pokefirered.
Only qualified English Ruby/Sapphire revision 2, Emerald and FRLG revision 1
ROMs are accepted. No event scripts,
ROM contents, official distributions or Pokemon records are bundled.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import struct

spec = importlib.util.spec_from_file_location('island_save_layout', Path(__file__).with_name('butterflyos-gen3-gift.py'))
gift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gift)

EVENTS = {
    'eon-ticket': {'title': 'Eon Ticket', 'destination': 'Southern Island', 'item': 275,
                   'description': 'Native Latias or Latios encounter; the roaming Pokemon is preserved.'},
    'mystic-ticket': {'title': 'MysticTicket', 'destination': 'Navel Rock', 'item': 370,
                      'description': 'Native Lugia and Ho-Oh encounters. Replay resets both island encounters.'},
    'aurora-ticket': {'title': 'AuroraTicket', 'destination': 'Birth Island', 'item': 371,
                      'description': 'Native triangle puzzle and Deoxys encounter.'},
    'old-sea-map': {'title': 'Old Sea Map', 'destination': 'Faraway Island', 'item': 376,
                    'description': 'Native Mew chase; expanded English experience, originally distributed in Japanese Emerald only.'},
}
# Completion flags are scoped to the island encounter, never the normal roamer.
RULES = {
    'Ruby/Sapphire': {
        'eon-ticket': dict(travel=0x853, received=None, shown=None,
                           completed=(0xCE,), clear=(), show=(), hide=(), variables=()),
    },
    'Emerald': {
        'eon-ticket': dict(travel=0x8B3, received=None, shown=0x1AE,
                           completed=(0x1C8, 0x1C9), clear=(0xCE,), show=(), hide=(), variables=()),
        'mystic-ticket': dict(travel=0x8E0, received=0x13B, shown=0x1DB,
                              completed=(0x91, 0x92, 0x1DC, 0x1DD), clear=(),
                              show=(0x320, 0x321), hide=(), variables=()),
        'aurora-ticket': dict(travel=0x8D5, received=0x13A, shown=0x1AF,
                              completed=(0x1AC, 0x1AD), clear=(0x8D3, 0x8D4),
                              show=(0x2FC,), hide=(0x2FB,), variables=(0x4034, 0x4035)),
        'old-sea-map': dict(travel=0x8D6, received=0x13C, shown=0x1B0,
                            completed=(0x1C7, 0x1CA), clear=(), show=(0x2CE,),
                            hide=(), variables=(0x403A,)),
    },
    'FireRed/LeafGreen': {
        'mystic-ticket': dict(travel=0x84A, received=0x2A8, shown=0x2F0,
                              completed=(0x2F2, 0x2F3, 0x2F5, 0x2F6), clear=(),
                              show=(0x9B, 0x9C), hide=(), variables=()),
        'aurora-ticket': dict(travel=0x84B, received=0x2A7, shown=0x2F1,
                              completed=(0x2E4, 0x2F7), clear=(0x848,),
                              show=(0x9A,), hide=(0x99,), variables=(0x4026, 0x403E)),
    },
}


def load_save(data, rom):
    profile = gift.rom_profile(gift.read_rom(rom))
    family = profile[0]
    if family not in RULES:
        raise ValueError('Use qualified English Ruby/Sapphire revision 2, Emerald or FireRed/LeafGreen revision 1.')
    sizes = gift.section_sizes(family)
    sections = gift.active_sections(data, sizes)
    save2 = data[sections[0]:sections[0] + sizes[0]]
    emerald = family == 'Emerald'
    ruby_sapphire = family == 'Ruby/Sapphire'
    if ruby_sapphire:
        matches = struct.unpack_from('<I', save2, 0xAC)[0] == 0
    elif emerald:
        matches = save2[0xAC:0xB0] == save2[0x1F4:0x1F8]
    else:
        matches = struct.unpack_from('<I', save2, 0xAC)[0] == 1 and save2[0xAF8:0xAFC] == save2[0xF20:0xF24]
    if not matches:
        raise ValueError('Save family/security-key mismatch. Use a matching ROM and save.')
    block = bytearray().join(data[sections[n]:sections[n] + sizes[n]] for n in range(1, 5))
    # Ruby/Sapphire quantities are plain u16 values and their key pocket has
    # 20 slots, unlike Emerald/FRLG's 30 encrypted entries.
    key = 0 if ruby_sapphire else struct.unpack_from('<H', save2, 0xAC if emerald else 0xF20)[0]
    flags, variables, pocket, slots = {'Ruby/Sapphire': (0x1220, 0x1340, 0x5B0, 20),
                                     'Emerald': (0x1270, 0x139C, 0x5D8, 30),
                                     'FireRed/LeafGreen': (0xEE0, 0x1000, 0x3B8, 30)}[family]
    ctx = dict(family=family, sizes=sizes, sections=sections, block=block,
               key=key, flags_at=flags, vars_at=variables, pocket_at=pocket,
               pocket_slots=slots, origin=profile[1])
    entries = [struct.unpack_from('<HH', block, pocket + n * 4) for n in range(slots)]
    ids = [item for item, _ in entries if item]
    if len(ids) != len(set(ids)) or any(item > (376 if emerald else 374) or
            (quantity ^ key) != (1 if item else 0) for item, quantity in entries):
        raise ValueError('Unrecognized key-item pocket. No changes made.')
    ctx['items'] = ids
    return ctx


def flag(ctx, number):
    return bool(ctx['block'][ctx['flags_at'] + number // 8] & (1 << (number % 8)))


def set_flag(ctx, number, value):
    at, mask = ctx['flags_at'] + number // 8, 1 << (number % 8)
    ctx['block'][at] = (ctx['block'][at] | mask) if value else (ctx['block'][at] & ~mask)


def variable(ctx, number):
    return struct.unpack_from('<H', ctx['block'], ctx['vars_at'] + (number - 0x4000) * 2)[0]


def status(ctx, event):
    if event not in RULES[ctx['family']]:
        raise ValueError('This event is not supported by the selected game.')
    rule, info = RULES[ctx['family']][event], EVENTS[event]
    completed = {hex(number): flag(ctx, number) for number in rule['completed']}
    has_ticket, travel = info['item'] in ctx['items'], flag(ctx, rule['travel'])
    stage = 'Encounter finished or partly finished' if any(completed.values()) else (
        'Island travel enabled' if has_ticket and travel else 'Not enabled')
    group, number = ctx['block'][4:6]
    if ctx['family'] == 'Ruby/Sapphire':
        on_island = group == 26 and number in (9, 10)
        postgame = flag(ctx, 0x804) and flag(ctx, 0x123) and 265 in ctx['items']
    elif ctx['family'] == 'Emerald':
        on_island = group == 26 and (number in (9, 10, 56, 57, 58, 59) or 66 <= number <= 87)
        postgame = flag(ctx, 0x864) and flag(ctx, 0x123) and 265 in ctx['items']
    else:
        on_island = group == 2 and (number == 0 or 36 <= number <= 56 or number in (58, 59))
        postgame = flag(ctx, 0x82C) and flag(ctx, 0x840) and variable(ctx, 0x4076) >= 5
    description = info['description']
    if ctx['family'] == 'Ruby/Sapphire':
        description = 'Native %s encounter; the normal roaming Pokemon is preserved.' % ('Latias' if ctx['origin'] == 2 else 'Latios')
    return dict(event=event, title=info['title'], family=ctx['family'], stage=stage,
                has_ticket=has_ticket, travel=travel, completed=completed,
                free_key_slots=ctx['pocket_slots']-len(ctx['items']), island_map=on_island,
                postgame_travel=postgame, destination=info['destination'],
                expanded_experience=event == 'old-sea-map', description=description)


def inspect_event(data, rom, event='aurora-ticket'):
    return status(load_save(data, rom), event)


def prepare_event(data, rom, action, event='aurora-ticket'):
    if action not in ('enable', 'replay'):
        raise ValueError('Choose enable or replay.')
    ctx = load_save(data, rom)
    before = status(ctx, event)
    if not before['postgame_travel']:
        raise ValueError('Unlock normal postgame ferry travel first. Story progress is not changed.')
    if before['island_map']:
        raise ValueError('Save away from the event islands and their harbors, then exit the game.')
    if action == 'enable' and any(before['completed'].values()):
        raise ValueError('An encounter has finished. Choose Replay explicitly to reset this event.')
    if action == 'enable' and before['has_ticket'] and before['travel']:
        raise ValueError('This island is already enabled. Visit the ferry attendant.')
    rule, info = RULES[ctx['family']][event], EVENTS[event]
    if not before['has_ticket']:
        if not before['free_key_slots']:
            raise ValueError('Make room in the key-item pocket first.')
        for n in range(ctx['pocket_slots']):
            at = ctx['pocket_at'] + n * 4
            if struct.unpack_from('<H', ctx['block'], at)[0] == 0:
                struct.pack_into('<HH', ctx['block'], at, info['item'], ctx['key'] ^ 1)
                break
    set_flag(ctx, rule['travel'], True)
    if rule['received'] is not None:
        set_flag(ctx, rule['received'], True)
    if action == 'replay':
        flags_to_clear = (*rule['completed'], *rule['clear'], *rule['show'])
        if rule['shown'] is not None:
            flags_to_clear += (rule['shown'],)
        for number in flags_to_clear:
            set_flag(ctx, number, False)
        for number in rule['hide']:
            set_flag(ctx, number, True)
        for number in rule['variables']:
            struct.pack_into('<H', ctx['block'], ctx['vars_at'] + (number - 0x4000) * 2, 0)
    result = bytearray(data)
    cursor = 0
    for n in range(1, 5):
        offset, size = ctx['sections'][n], ctx['sizes'][n]
        contents = ctx['block'][cursor:cursor + size]
        cursor += size
        if contents != data[offset:offset + size]:
            result[offset:offset + size] = contents
            struct.pack_into('<H', result, offset + 0xFF6, gift.checksum(contents))
    after = inspect_event(result, rom, event)
    if not after['has_ticket'] or not after['travel'] or (action == 'replay' and any(after['completed'].values())):
        raise ValueError('Prepared event did not pass verification.')
    return bytes(result), before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--event', choices=EVENTS, default='aurora-ticket')
    parser.add_argument('--action', choices=('inspect', 'enable', 'replay'), default='inspect')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        data = args.save.read_bytes()
        if args.action == 'inspect':
            print(json.dumps(inspect_event(data, args.rom, args.event)))
        else:
            if not args.output:
                raise ValueError('An isolated output path is required.')
            result, before = prepare_event(data, args.rom, args.action, args.event)
            with args.output.open('xb') as handle:
                handle.write(result)
                handle.flush()
                os.fsync(handle.fileno())
            print(json.dumps({'action': args.action, 'before': before,
                              'after': inspect_event(result, args.rom, args.event)}))
    except (OSError, ValueError) as error:
        parser.exit(1, 'Gen III event: %s\n' % error)


if __name__ == '__main__':
    main()

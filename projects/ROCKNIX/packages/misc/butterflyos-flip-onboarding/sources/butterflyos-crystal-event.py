#!/usr/bin/env python3
"""Prepare Crystal's native GS Ball quest and Odd Egg replay on isolated outputs.

Offsets and event IDs qualified against pret/pokecrystal RAM symbols and scripts.
No ROM content or Pokemon records are bundled. Never modifies the input save.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_SHA256 = 'fdcc3c8c43813cf8731fc037d2a6d191bac75439c34b24ba1c27526e6acdc8a2'
EVENTS = {'well': 43, 'can_give': 190, 'gave': 191, 'restless': 192,
          'received': 832, 'gate_lass': 1771, 'forest_lass': 1773, 'kurt_outside': 1956}
EVENT_BASE = 0x2600
QUEST_MAPS = {(3, 52), (8, 4), (8, 7), (11, 20)}
GS_BALL = 0x73
ODD_EGG_EVENT = 830
DAYCARE_MAN = 0x2A83
DAYCARE_HAS_EGG = 0x40


def flag(data, number):
    return bool(data[EVENT_BASE + number // 8] & (1 << (number % 8)))


def set_flag(data, number, value):
    at, mask = EVENT_BASE + number // 8, 1 << (number % 8)
    data[at] = (data[at] | mask) if value else (data[at] & ~mask)


def validate(data, rom):
    if hashlib.sha256(Path(rom).read_bytes()).hexdigest() != ROM_SHA256:
        raise ValueError('Use the qualified English retail Crystal ROM. Gold/Silver and modified ROMs are unsupported.')
    if len(data) not in (0x8000, 0x8000 + 48):
        raise ValueError('Use an ordinary Crystal in-game save, not a save state.')
    for start, end, checksum in ((0x2009, 0x2B83, 0x2D0D), (0x1209, 0x1D83, 0x1F0D)):
        if sum(data[start:end]) & 0xFFFF != int.from_bytes(data[checksum:checksum + 2], 'little'):
            raise ValueError('Crystal save checksum is invalid. Load the game and save normally first.')
    if data[0x2009:0x2B83] != data[0x1209:0x1D83]:
        raise ValueError('Crystal primary and backup saves differ. Load the game and save normally first.')
    count = data[0x244A]
    if count > 25 or data[0x244B + count] != 0xFF:
        raise ValueError('Unrecognized key-item pocket; no changes made.')
    keys = list(data[0x244B:0x244B + count])
    if any(not 1 <= item < 0xFF for item in keys) or len(keys) != len(set(keys)):
        raise ValueError('Invalid or duplicate key items; no changes made.')
    return keys


def inspect_event(data, rom):
    keys = validate(data, rom)
    flags = {name: flag(data, number) for name, number in EVENTS.items()}
    has_ball = GS_BALL in keys
    available = data[0x3E44] == 0x0B  # Continue restores this backup into the live flag.
    if flags['restless']:
        stage = 'Ready for shrine' if has_ball and data[0x2781] & 4 else 'Collect returned GS Ball from Kurt'
    elif flags['gave']:
        stage = 'Kurt examining GS Ball'
    elif has_ball or flags['can_give']:
        stage = 'Take GS Ball to Kurt'
    elif flags['received']:
        stage = 'Encounter finished'
    else:
        stage = 'GS Ball delivery enabled' if available else 'Not started'
    apricorn_work = any(flag(data, number) for number in range(600, 607))
    unrelated_timer = bool(data[0x27AC] & 1) and not flags['gave']
    return {'stage': stage, 'flags': flags, 'has_gs_ball': has_ball,
            'kurt_busy': apricorn_work or unrelated_timer,
            'quest_map': tuple(data[0x2843:0x2845]) in QUEST_MAPS,
            'key_items': len(keys), 'delivery_flag': data[0x3E44]}


def prepare_event(data, rom, action):
    status = inspect_event(data, rom)
    if action not in ('enable', 'replay'):
        raise ValueError('Unknown Crystal event action.')
    if status['quest_map']:
        raise ValueError('Save outside Goldenrod Pokemon Center, Azalea Town, Kurt\'s house and Ilex Forest, then exit the game.')
    if status['kurt_busy']:
        raise ValueError('Finish and collect Kurt\'s apricorn work, then save outside the quest maps.')
    if data[0x2521] != 0:
        raise ValueError('Unknown Goldenrod scene state; no changes made.')
    if action == 'enable':
        if status['stage'] != 'Not started':
            raise ValueError('The quest is enabled, in progress or finished. Continue it in-game, or explicitly choose Replay.')
    keys = validate(data, rom)
    keys = [item for item in keys if item != GS_BALL]
    if len(keys) >= 25:
        raise ValueError('Make room in the key-item pocket before enabling GS Ball delivery.')
    result = bytearray(data)
    if action == 'replay':
        # Rearm only the native delivery/Kurt/shrine flags. Existing Pokemon and
        # Pokedex data are preserved, including any previously caught Celebi.
        for name in ('received', 'can_give', 'gave', 'restless'):
            set_flag(result, EVENTS[name], False)
        set_flag(result, EVENTS['kurt_outside'], True)
        set_flag(result, EVENTS['gate_lass'], True)
        set_flag(result, EVENTS['forest_lass'], False)
        result[0x2781] &= ~4  # ENGINE_FOREST_IS_RESTLESS only.
        if status['flags']['gave']:
            result[0x27AC] &= ~1  # Cancel only the GS Ball examination timer.
        if result[0x251E] == 2:
            result[0x251E] = 0  # Kurt returning scene; preserve rival scene 1.
        result[0x244A] = len(keys)
        # Keep unrelated keys in order and terminate the compacted list.
        result[0x244B:0x244B + len(keys) + 1] = bytes(keys + [0xFF])
    result[0x3E3C] = result[0x3E44] = 0x0B
    result[0x1209:0x1D83] = result[0x2009:0x2B83]
    checksum = (sum(result[0x2009:0x2B83]) & 0xFFFF).to_bytes(2, 'little')
    result[0x2D0D:0x2D0F] = result[0x1F0D:0x1F0F] = checksum
    inspect_event(result, rom)
    return bytes(result), status


def inspect_odd_egg(data, rom):
    validate(data, rom)
    received = flag(data, ODD_EGG_EVENT)
    return {'stage': 'Odd Egg already received' if received else 'Odd Egg available from Day-Care Man',
            'received': received, 'breeding_egg_waiting': bool(data[DAYCARE_MAN] & DAYCARE_HAS_EGG)}


def prepare_odd_egg(data, rom):
    status = inspect_odd_egg(data, rom)
    if not status['received']:
        raise ValueError('The Odd Egg is already available. Leave room in your party and visit the Day-Care Man inside the Day Care.')
    if status['breeding_egg_waiting']:
        raise ValueError('Collect the ordinary breeding egg first, then save and exit. Breeding progress is preserved.')
    result = bytearray(data)
    set_flag(result, ODD_EGG_EVENT, False)
    # Mirror only this bit. Every other event, item, Pokemon and breeding byte
    # remains untouched; the qualified validator has checked both save copies.
    at = EVENT_BASE + ODD_EGG_EVENT // 8
    result[at - 0xE00] = result[at]
    checksum = (sum(result[0x2009:0x2B83]) & 0xFFFF).to_bytes(2, 'little')
    result[0x2D0D:0x2D0F] = result[0x1F0D:0x1F0F] = checksum
    inspect_odd_egg(result, rom)
    return bytes(result), status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--action', choices=('inspect', 'enable', 'replay', 'odd-egg-inspect', 'odd-egg-replay'), default='inspect')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        original = args.save.read_bytes()
        inspect = inspect_odd_egg if args.action.startswith('odd-egg-') else inspect_event
        if args.action in ('inspect', 'odd-egg-inspect'):
            print(json.dumps(inspect(original, args.rom)))
        else:
            if not args.output:
                raise ValueError('An isolated output path is required.')
            result, before = (prepare_odd_egg(original, args.rom) if args.action == 'odd-egg-replay'
                              else prepare_event(original, args.rom, args.action))
            with args.output.open('xb') as handle:
                handle.write(result)
            print(json.dumps({'action': args.action, 'before': before, 'after': inspect(result, args.rom)}))
    except (OSError, ValueError) as error:
        parser.exit(1, 'Crystal event: %s\n' % error)


if __name__ == '__main__':
    main()

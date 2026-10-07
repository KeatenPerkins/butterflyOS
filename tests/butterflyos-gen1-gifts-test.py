#!/usr/bin/env python3
"""Gen I gift regression using private ROM/save fixtures, never modifying originals.

Usage: python3 tests/butterflyos-gen1-gifts-test.py HELPER SAVE_ROOT ROM_ROOT
SAVE_ROOT/gb contains English Red, Blue and Yellow saves. ROM_ROOT contains their
verified English retail .gb files. Every generated record/cache stays in /tmp.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import struct
import subprocess
import tempfile
from contextlib import ExitStack
from unittest.mock import patch
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(helper, action, **kwargs):
    cmd = [str(helper), action]
    for name, value in kwargs.items():
        cmd += ['--' + name.replace('_', '-'), str(value)]
    return subprocess.run(cmd, capture_output=True, text=True)


def inspect(helper, path):
    r = run(helper, 'inspect', save=path)
    assert r.returncode == 0, r.stderr
    return r.stdout


def records(output):
    return [line.split('\t') for line in output.splitlines() if line.startswith('box_record\t')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('helper', type=Path)
    parser.add_argument('save_root', type=Path)
    parser.add_argument('rom_root', type=Path)
    args = parser.parse_args()
    helper = args.helper.resolve()
    generator = load('gift_generator', SOURCES / 'butterflyos-gen1-gift.py')
    ui = load('gift_ui', SOURCES / 'butterflyos-save-trade-sdl.py')
    expected = {
        'mew': (21, 135, [1, 0, 0, 0], [35, 0, 0, 0]),
        'surf-pikachu': (84, 125, [84, 45, 57, 0], [30, 40, 15, 0]),
        'fly-pikachu': (84, 125, [84, 45, 19, 0], [30, 40, 15, 0]),
        'dragon-rage-magikarp': (133, 156, [150, 82, 0, 0], [40, 10, 0, 0]),
        'pay-day-fearow': (35, 125, [64, 45, 43, 6], [35, 40, 30, 20]),
        'pay-day-rapidash': (164, 125, [52, 39, 23, 6], [25, 30, 20, 20]),
        'amnesia-psyduck': (47, 125, [10, 133, 0, 0], [35, 20, 0, 0]),
        'stadium-bulbasaur': (153, 135, [33, 45, 0, 0], [35, 40, 0, 0]),
        'stadium-charmander': (176, 135, [10, 45, 0, 0], [35, 40, 0, 0]),
        'stadium-squirtle': (177, 135, [33, 39, 0, 0], [35, 30, 0, 0]),
        'stadium-hitmonlee': (43, 125, [24, 96, 0, 0], [30, 40, 0, 0]),
        'stadium-hitmonchan': (44, 125, [4, 97, 0, 0], [15, 30, 0, 0]),
        'stadium-eevee': (102, 125, [33, 28, 0, 0], [35, 15, 0, 0]),
        'stadium-omanyte': (98, 125, [55, 110, 0, 0], [25, 40, 0, 0]),
        'stadium-kabuto': (90, 125, [10, 106, 0, 0], [35, 30, 0, 0]),
    }
    assert set(expected) == set(generator.PRESETS) == {p[0] for p in ui.GEN1_GIFTS + ui.STADIUM_GIFTS}
    for selected, handler, kwargs in ((3, 'time_capsule_workflow', {}),
                                      (4, 'gen2_to_gen3_workflow', {})):
        with patch.object(ui, 'choose_list', return_value=selected), patch.object(ui, handler) as route:
            ui.local_swap_workflow(None)
            route.assert_called_once_with(None, **kwargs)
    saves = [('/storage/roms/gb/Red.srm', 'PLAYER', 'Red/Blue', []),
             ('/storage/roms/gb/Yellow.srm', 'PLAYER', 'Yellow', [])]
    with patch.object(ui, 'generation_saves', return_value=saves), patch.object(ui, 'choose_list', return_value=1):
        assert ui.choose_gen1_local_save(None) == saves[1]
    for selected, stadium in ((2, False), (3, True)):
        with patch.object(ui, 'generation_saves', return_value=saves), \
             patch.object(ui, 'choose_list', side_effect=[selected, None]) as menu, \
             patch.object(ui, 'gen1_gift_workflow') as route:
            assert ui.choose_gen1_local_save(None) is None
            route.assert_called_once_with(None, stadium=stadium)
            rows = menu.call_args.args[3]
            assert [r[0] for r in rows] == ['GAME', 'GAME', 'GEN 1 GIFTS', 'STADIUM GIFTS']
    with patch.object(ui, 'generation_saves', return_value=[]), \
         patch.object(ui, 'choose_list', side_effect=[1, None]), \
         patch.object(ui, 'gen1_gift_workflow') as route:
        assert ui.choose_gen1_local_save(None) is None
        route.assert_called_once_with(None, stadium=True)
    originals = {}
    checked = 0
    with tempfile.TemporaryDirectory(prefix='butterfly-gen1-gift-test-') as directory:
        scratch = Path(directory)
        last_output = None
        for game in ('Red', 'Blue', 'Yellow'):
            source = next((args.save_root / 'gb').glob('*' + game + ' Version*.srm'))
            rom = next(args.rom_root.glob('*' + game + ' Version*.gb'))
            originals[source] = digest(source)
            originals[rom] = digest(rom)
            before = inspect(helper, source)
            original_records = records(before)
            source_bytes = source.read_bytes()
            number = source_bytes[0x284C] & 0x7F
            for preset in generator.PRESETS:
                record, metadata = generator.gift_from_rom(rom, preset, dvs=[15, 15, 15, 15])
                assert len(record) == 33 and record[3] == 5 and record[4] == 0
                species, experience, moves, pp = expected[preset]
                if game == 'Yellow' and preset == 'stadium-eevee':
                    moves, pp = [33, 39, 0, 0], [35, 30, 0, 0]
                assert record[0] == species and list(record[8:12]) == moves
                assert int.from_bytes(record[14:17], 'big') == experience
                assert record[29:33] == bytes(pp)
                record_path = scratch / ('%s-%s.bin' % (game, preset))
                record_path.write_bytes(record)
                for box in (number, (number + 1) % 12, 6, 11):
                    occupied = sum(int(r[1]) == box for r in original_records)
                    output = scratch / ('%d.srm' % checked)
                    options = dict(destination=source, destination_box=box,
                                   destination_slot=occupied, record=record_path,
                                   national_species=metadata['national_species'],
                                   nickname=metadata['nickname'],
                                   rom_family='yellow' if game == 'Yellow' else 'red-blue',
                                   output_destination=output)
                    r = run(helper, 'gift-gen1', **options)
                    assert r.returncode == 0, r.stderr
                    after = inspect(helper, output)
                    result = records(after)
                    added = next(row for row in result if int(row[1]) == box and int(row[2]) == occupied)
                    assert int(added[3]) == metadata['species'] and added[5] == metadata['nickname']
                    assert 'level=5' in added and 'held=0' in added
                    assert 'moves=' + ','.join(map(str, metadata['moves'])) in added
                    assert [row for row in result if row is not added] == original_records
                    raw = output.read_bytes()
                    assert raw[0x284C] == (0x80 | box), 'PC initialization/current-box flag missing'
                    for start in (0x4000, 0x6000):
                        end = start + 6 * 0x462
                        assert raw[end] == (~sum(raw[start:end]) & 0xFF)
                        for index in range(6):
                            at = start + index * 0x462
                            assert raw[end + 1 + index] == (~sum(raw[at:at + 0x462]) & 0xFF)
                    banked = (0x4000 if box < 6 else 0x6000) + (box % 6) * 0x462
                    active = raw[0x30C0:0x30C0 + 0x462]
                    assert active == raw[banked:banked + 0x462], 'banked gift differs from active box'
                    offset = 22 + occupied * 33
                    entry = active[offset:offset + 33]
                    assert entry[:12] == record[:12] and entry[14:] == record[14:]
                    assert entry[12:14] == source_bytes[0x2605:0x2607], 'gift trainer ID differs'
                    ot = active[22 + 20 * 33 + occupied * 11:22 + 20 * 33 + (occupied + 1) * 11]
                    assert ot[:7] == source_bytes[0x2598:0x259F] and ot[7:] == b'\x50' * 4
                    nickname = active[22 + 20 * 33 + 20 * 11 + occupied * 11:
                                      22 + 20 * 33 + 20 * 11 + (occupied + 1) * 11]
                    assert 0x50 in nickname and 0 not in nickname
                    for at in (0x25A3, 0x25B6):
                        dex_index = metadata['national_species'] - 1
                        assert raw[at + dex_index // 8] & (1 << (dex_index % 8))
                    # Refuse occupied slots and mismatched Yellow/RB save families.
                    bad = dict(options, output_destination=scratch / ('bad-%d.srm' % checked),
                               destination_slot=max(0, occupied - 1) if occupied else 1)
                    assert run(helper, 'gift-gen1', **bad).returncode != 0
                    assert not bad['output_destination'].exists()
                    bad = dict(options, output_destination=scratch / ('family-%d.srm' % checked),
                               rom_family='red-blue' if game == 'Yellow' else 'yellow')
                    assert run(helper, 'gift-gen1', **bad).returncode != 0
                    assert not bad['output_destination'].exists()
                    assert digest(source) == originals[source]
                    last_output = output
                    checked += 1
                # A second gift switches boxes in an already initialized save:
                # retain the first gift and every original record.
                second = dict(options, destination=last_output,
                              destination_box=number,
                              destination_slot=sum(int(r[1]) == number for r in records(inspect(helper, last_output))),
                              output_destination=scratch / ('second-%s-%s.srm' % (game, preset)))
                assert run(helper, 'gift-gen1', **second).returncode == 0
                rows = records(inspect(helper, second['output_destination']))
                assert len(rows) == len(original_records) + 2
                assert all(row in rows for row in records(inspect(helper, last_output)))
                # Reject an existing output/symlink before opening it.
                existing = scratch / 'existing.srm'
                existing.write_bytes(b'keep')
                options['output_destination'] = existing
                assert run(helper, 'gift-gen1', **options).returncode != 0
                assert existing.read_bytes() == b'keep'
                alias = scratch / 'alias.srm'
                alias.symlink_to(source)
                options['output_destination'] = alias
                assert run(helper, 'gift-gen1', **options).returncode != 0
                alias.unlink()
                if game == 'Red' and preset == 'mew':
                    # Fill a real PC box to capacity, then refuse an additional gift.
                    full = last_output
                    for count in range(1, 20):
                        filled = scratch / ('fill-%d.srm' % count)
                        fill_options = dict(options, destination=full, destination_box=11,
                                            destination_slot=count, output_destination=filled)
                        r = run(helper, 'gift-gen1', **fill_options)
                        assert r.returncode == 0, r.stderr
                        full = filled
                    assert sum(int(r[1]) == 11 for r in records(inspect(helper, full))) == 20
                    full_hash = digest(full)
                    rejected = scratch / 'full-rejected.srm'
                    fill_options.update(destination=full, destination_slot=19, output_destination=rejected)
                    assert run(helper, 'gift-gen1', **fill_options).returncode != 0
                    assert not rejected.exists() and digest(full) == full_hash
                corrupt = scratch / 'bad-record.bin'
                malformed = bytearray(record); malformed[29] = 0
                corrupt.write_bytes(malformed)
                invalid = dict(options, record=corrupt, output_destination=scratch / 'invalid-record.srm')
                assert run(helper, 'gift-gen1', **invalid).returncode != 0
                assert not invalid['output_destination'].exists()
            broken = scratch / 'modified.gb'
            data = bytearray(rom.read_bytes()); data[-1] ^= 1; broken.write_bytes(data)
            try:
                generator.gift_from_rom(broken, 'mew')
                raise AssertionError('modified ROM accepted')
            except ValueError:
                pass
        # Exercise the actual commit function: backup, persisted write, conflict refusal.
        destination = scratch / 'live.srm'
        destination.write_bytes(source_bytes)
        session = scratch / 'session'; session.mkdir()
        (session / 'destination-original').write_text(str(destination))
        (session / 'original-destination-sha256').write_text(digest(destination))
        (session / 'destination-live.srm').write_bytes(last_output.read_bytes())
        (session / 'state').write_text('READY')
        assert ui.session_output(str(session)) == str(session / 'destination-live.srm')
        unchanged = digest(destination)  # preparation/cancel require no write
        assert unchanged == hashlib.sha256(source_bytes).hexdigest()
        ok, message = ui.commit_copy(str(session))
        assert ok, message
        assert (session / 'original-destination-backup').read_bytes() == source_bytes
        assert destination.read_bytes() == last_output.read_bytes()
        (session / 'original-destination-sha256').write_text(unchanged)
        assert ui.commit_copy(str(session))[0] is False
        assert (session / 'original-destination-backup').read_bytes() == source_bytes
        # Run the actual UI cancellation paths without SDL or device input.
        cache = scratch / 'cache'; cache.mkdir()
        (cache / 'manifest.json').write_text(json.dumps({'rom_sha256': digest(rom)}))
        class Frontend:
            def draw_sprite_browser(self, *args):
                pass
            def next_key(self):
                return key
        for key, selections in ((ui.KEY_ESCAPE, [0]), (ui.KEY_RETURN, [0, 0])):
            cancelled = scratch / 'cancelled'; cancelled.mkdir()
            (cancelled / 'state').write_text('READY')
            baseline = digest(destination)
            with ExitStack() as stack:
                replacements = {
                    'notice': lambda *a, **k: None,
                    'choose_save': lambda *a: (str(destination), 'PLAYER', 'Yellow'),
                    'ensure_sprite_cache': lambda *a: str(cache),
                    '_rom_candidates': lambda *a: [str(rom)],
                    'choose_copy_destination': lambda *a: (0, 0),
                    'prepare_gen1_gift': lambda *a: (str(cancelled), 'MEW'),
                    'session_output': lambda *a: str(last_output),
                    'save_metadata': lambda *a: (None, None, None, [{'box': 0, 'slot': 0, 'species': 21}]),
                    '_enrich_rom_names': lambda *a: None,
                    '_read_cache_png': lambda *a: None,
                }
                for name, value in replacements.items():
                    stack.enter_context(patch.object(ui, name, value))
                stack.enter_context(patch.object(ui, 'choose_list', side_effect=selections))
                commit = stack.enter_context(patch.object(ui, 'commit_copy'))
                ui.gen1_gift_workflow(Frontend())
                commit.assert_not_called()
            assert digest(destination) == baseline and not cancelled.exists()
    assert all(digest(p) == value for p, value in originals.items())
    print('PASS: %d Gen I gift/save reloads, ROM-derived PP/experience, trainer identity, '
          'PC persistence, Pokedex flags, full-box/malformed-record refusal, invalid '
          'destinations/ROMs, cancellation and backup/conflict handling; '
          'private originals unchanged' % checked)


if __name__ == '__main__':
    main()

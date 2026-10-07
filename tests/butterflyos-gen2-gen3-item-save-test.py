#!/usr/bin/env python3
"""Test item migration through complete saves using private, disposable fixtures.

Usage: python3 tests/butterflyos-gen2-gen3-item-save-test.py HELPER FIXTURE_DIR
FIXTURE_DIR contains gbc/{Gold,Silver,Crystal} and gba/{Ruby,Sapphire,Emerald,
Fire Red,Leaf Green} .srm files. No save data is distributed with this test.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

CASES = {0: 0, 0x92: 200, 0x70: 195, 0x8F: 199, 0xAD: 139, 0xAE: 142,
         0x96: 138, 0xD5: 310, 0x98: 0, 0xFF: 0}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(helper, action, **options):
    args = [str(helper), action]
    for key, value in options.items():
        args.extend(['--' + key.replace('_', '-'), str(value)])
    return subprocess.check_output(args, text=True)


def records(helper, path):
    return [line.split('\t') for line in run(helper, 'inspect', save=path).splitlines()
            if line.startswith('box_record\t')]


def held(record):
    return int(next(field.split('=', 1)[1] for field in record if field.startswith('held=')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('helper', type=Path)
    parser.add_argument('fixtures', type=Path)
    args = parser.parse_args()
    helper, fixtures = args.helper.resolve(), args.fixtures.resolve()
    sources = [next((fixtures / 'gbc').glob('*' + name + '*.srm'))
               for name in ('Gold', 'Silver', 'Crystal')]
    destinations = [next((fixtures / 'gba').glob('*' + name + '*.srm'))
                    for name in ('Ruby', 'Sapphire', 'Emerald', 'Fire Red', 'Leaf Green')]
    original_hashes = {p: digest(p) for p in sources + destinations}
    checked = 0
    with tempfile.TemporaryDirectory(prefix='butterfly-item-save-test-') as directory:
        scratch = Path(directory)
        for source in sources:
            record = records(helper, source)[0]
            box, slot, species = map(int, record[1:4])
            crystal = 'Crystal' in source.name
            active_offset, number_offset = (0x2D10, 0x2700) if crystal else (0x2D6C, 0x2724)
            banked = (0x4000 if box < 7 else 0x6000) + (box % 7) * 0x450
            for item, expected in CASES.items():
                raw = bytearray(source.read_bytes())
                raw[banked + 22 + slot * 32 + 1] = item
                if raw[number_offset] & 0x7F == box:
                    raw[active_offset + 22 + slot * 32 + 1] = item
                # PC-box records lie outside the two main Gen II checksum ranges.
                test_source = scratch / 'source.srm'
                test_source.write_bytes(raw)
                test_hash = digest(test_source)
                test_record = next(r for r in records(helper, test_source)
                                   if list(map(int, r[1:3])) == [box, slot])
                assert held(test_record) == item
                for destination in destinations:
                    occupied = {(int(r[1]), int(r[2])) for r in records(helper, destination)}
                    free_box, free_slot = next((b, s) for b in range(14) for s in range(30)
                                              if (b, s) not in occupied)
                    output = scratch / 'destination.srm'
                    message = run(helper, 'copy-gen2-to-gen3', source=test_source,
                                  source_box=box, source_slot=slot, national_species=species,
                                  destination=destination, destination_box=free_box,
                                  destination_slot=free_slot, output_destination=output)
                    result = next(r for r in records(helper, output)
                                  if (int(r[1]), int(r[2])) == (free_box, free_slot))
                    assert held(result) == expected, (source.name, destination.name, item, result)
                    assert 'held_item_cleared=%d\n' % int(item != 0 and expected == 0) in message
                    assert digest(test_source) == test_hash, 'migration changed source item/save'
                    checked += 1
    assert all(digest(p) == value for p, value in original_hashes.items()), 'private original changed'
    print('PASS: %d save migrations across Gold/Silver/Crystal and all five Gen III games; '
          'preserved/cleared items reload correctly; originals unchanged' % checked)


if __name__ == '__main__':
    main()

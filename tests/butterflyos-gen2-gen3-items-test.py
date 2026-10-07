#!/usr/bin/env python3
"""Compile the production mapper and audit all 256 source IDs against item facts.

Requires a host C compiler; no ROMs, saves, network access or device required.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / 'tests/fixtures/butterflyos-gen2-gen3-item-ids.json').read_text())
HEADER = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'

# Renamed versions of the same item; bows are not renamed to Silk Scarf.
ALIASES = {
    'PARLYZ_HEAL': 'PARALYZE_HEAL', 'ELIXER': 'ELIXIR',
    'MAX_ELIXER': 'MAX_ELIXIR', 'BLACKBELT_I': 'BLACK_BELT',
    'BERRY': 'ORAN_BERRY', 'GOLD_BERRY': 'SITRUS_BERRY',
    'PSNCUREBERRY': 'PECHA_BERRY', 'PRZCUREBERRY': 'CHERI_BERRY',
    'BURNT_BERRY': 'RAWST_BERRY', 'ICE_BERRY': 'ASPEAR_BERRY',
    'BITTER_BERRY': 'PERSIM_BERRY', 'MINT_BERRY': 'CHESTO_BERRY',
    'MIRACLEBERRY': 'LUM_BERRY', 'MYSTERYBERRY': 'LEPPA_BERRY',
}


def expected_items():
    items = FACTS['gen3_items']
    by_name = {name.replace('_', ''): value for name, value in items.items()
               if value < 259 and not name.startswith(('TM', 'HM'))}
    expected = [0] * 256
    for name, source in FACTS['gen2_items'].items():
        if name in FACTS['gen2_key_items'] or name.startswith('ITEM_'):
            continue
        counterpart = ALIASES.get(name, name)
        expected[source] = by_name.get(counterpart.replace('_', ''), 0)
    for source, move in FACTS['gen2_tm_moves'].items():
        move = {'SOLARBEAM': 'SOLAR_BEAM', 'PSYCHIC_M': 'PSYCHIC'}.get(move, move)
        expected[int(source)] = FACTS['gen3_tm_moves'].get(move, 0)
    return expected


def main():
    program = r'''
#include <stdio.h>
#include "butterflyos-gen2-gen3-items.h"
int main(void) {
    for (unsigned item = 0; item < 256; ++item) {
        unsigned cleared = 99;
        unsigned mapped = gen2_held_item_to_gen3((uint8_t)item, &cleared);
        if (gen2_held_item_to_gen3((uint8_t)item, NULL) != mapped) return 1;
        printf("%u %u %u\n", item, mapped, cleared);
    }
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='butterfly-item-test-') as directory:
        source = Path(directory) / 'check.c'
        binary = Path(directory) / 'check'
        source.write_text(program)
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-Wall', '-Wextra',
                        '-Werror', '-I', str(HEADER), str(source), '-o', str(binary)], check=True)
        output = subprocess.check_output([str(binary)], text=True)
    rows = [list(map(int, line.split())) for line in output.splitlines()]
    assert len(rows) == 256
    expected = expected_items()
    for item, mapped, cleared in rows:
        assert mapped == expected[item], (hex(item), mapped, expected[item])
        assert cleared == int(item != 0 and mapped == 0), (hex(item), cleared)
    # Regression guards for ID collisions, renamed berries, removals and TMs.
    assert rows[0x92][1:] == [200, 0]  # Leftovers is NOT Gen III ID 146 (Figy Berry).
    assert rows[0x70][1:] == [195, 0]  # Everstone.
    assert rows[0x8F][1:] == [199, 0]  # Metal Coat.
    assert rows[0xAD][1:] == [139, 0]  # Berry -> Oran.
    assert rows[0xAE][1:] == [142, 0]  # Gold Berry -> Sitrus.
    assert rows[0x96][1:] == [138, 0]  # MysteryBerry -> Leppa.
    assert rows[0xC4][1:] == [293, 0]  # Roar TM05 remains Roar.
    assert rows[0xD5][1:] == [310, 0]  # SolarBeam TM22, different item ID.
    for item in (0x19, 0x3C, 0x55, 0x68, 0x98, 0x9D, 0x9E, 0xAA, 0xBF, 0xF3, 0xFF):
        assert rows[item][1:] == [0, 1], rows[item]
    assert rows[0][1:] == [0, 0]
    print('PASS: all 256 item IDs, cleared flags and nullable flag output; '
          '%d verified equivalents' % sum(value != 0 for value in expected))


if __name__ == '__main__':
    main()

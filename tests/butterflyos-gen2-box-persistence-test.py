#!/usr/bin/env python3
"""Regression tests using private save fixtures supplied outside the repo.

Usage: python3 tests/butterflyos-gen2-box-persistence-test.py HELPER FIXTURE_DIR
FIXTURE_DIR must contain gb/Yellow.srm and gbc/{Gold,Silver,Crystal} saves under
their usual Pokemon filenames. No ROM or save data is distributed with this test.
Every mutation operates on disposable working copies.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(helper, action, **options):
    command = [str(helper), action]
    for key, value in options.items():
        command.extend(["--" + key.replace("_", "-"), str(value)])
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def inspect(helper, path):
    output = run(helper, "inspect", save=path)
    return [line.split("\t") for line in output.splitlines()
            if line.startswith("box_record\t")]


def check_game_load(helper, path, scratch, expected_box, expected_species):
    """Read banked bytes independently, then emulate Continue's LoadBox copy."""
    raw = bytearray(path.read_bytes())
    kind = "Crystal" if "save_type=Crystal" in run(helper, "inspect", save=path) else "GS"
    number_offset, active_offset = (0x2700, 0x2D10) if kind == "Crystal" else (0x2724, 0x2D6C)
    box = raw[number_offset]
    assert box == expected_box, (kind, box, expected_box)
    box_size = 0x450
    banked_offset = (0x4000 if box < 7 else 0x6000) + (box % 7) * box_size
    active = raw[active_offset:active_offset + box_size]
    banked = raw[banked_offset:banked_offset + box_size]
    assert active == banked, "active box differs from the banked box loaded by the game"
    assert expected_species in banked[1:1 + banked[0]], "copied species missing from banked list"
    # Inspect's decoded strings tolerate zero bytes, but the actual game's PC
    # renderer does not. Independently validate native text terminators.
    for slot in range(banked[0]):
        for start in (22 + 20 * 32, 22 + 20 * 32 + 20 * 11):
            name = banked[start + slot * 11:start + (slot + 1) * 11]
            assert 0x50 in name, "Pokemon name has no native GB string terminator"
            assert 0 not in name[:name.index(0x50)], "Pokemon name contains a text control NUL"
    before = inspect(helper, path)
    raw[active_offset:active_offset + box_size] = banked
    loaded = scratch / "after-continue.srm"
    loaded.write_bytes(raw)
    assert inspect(helper, loaded) == before, "Continue discarded edited PC records"
    return before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("helper", type=Path)
    parser.add_argument("fixtures", type=Path)
    args = parser.parse_args()
    helper, fixtures = args.helper.resolve(), args.fixtures.resolve()
    yellow = fixtures / "gb/Pokemon - Yellow Version - Special Pikachu Edition (USA, Europe).srm"
    saves = [fixtures / "gbc" / name for name in (
        "Pokemon - Gold Version (USA, Europe).srm",
        "Pokemon - Silver Version (USA, Europe).srm",
        "Pokemon - Crystal Version (USA, Europe) (Rev A).srm",
    )]
    originals = {p: digest(p) for p in [yellow] + saves}
    # Source fixture's Yellow Pikachu is internal species 84; national species 25.
    pika = next(r for r in inspect(helper, yellow) if r[3] == "84")
    checked = 0
    with tempfile.TemporaryDirectory(prefix="butterfly-gen2-box-") as directory:
        scratch = Path(directory)
        for save in saves:
            records = inspect(helper, save)
            for box in (0, 1, 7, 13):
                slot = sum(int(r[1]) == box for r in records)
                converted = scratch / "converted.srm"
                run(helper, "transfer-gen1-to-gen2", source=yellow,
                    source_box=pika[1], source_slot=pika[2], national_species=25,
                    destination=save, destination_box=box, destination_slot=slot,
                    output_destination=converted)
                check_game_load(helper, converted, scratch, box, 25)
                checked += 1

                # Exercise the separate same-generation copy writer.
                copied = scratch / "copied.srm"
                source = saves[1] if save == saves[0] else saves[0]
                source_record = inspect(helper, source)[0]
                run(helper, "copy-gen2", source=source,
                    source_box=source_record[1], source_slot=source_record[2],
                    destination=save, destination_box=box, destination_slot=slot,
                    output_destination=copied)
                check_game_load(helper, copied, scratch, box, int(source_record[3]))
                checked += 1

                # Synthetic Kadabra record tests evolution writeback; the GUI's
                # species/rule validation is outside this save-format regression.
                kadabra, alakazam = scratch / "kadabra.srm", scratch / "alakazam.srm"
                run(helper, "evolve-gen2", source=converted, box=box, slot=slot,
                    evolved_species=64, nickname="KADABRA", output=kadabra)
                run(helper, "evolve-gen2", source=kadabra, box=box, slot=slot,
                    evolved_species=65, nickname="ALAKAZAM", output=alakazam)
                evolved = check_game_load(helper, alakazam, scratch, box, 65)
                assert any(int(r[1]) == box and int(r[2]) == slot and
                           r[3] == "65" and r[5] == "ALAKAZAM" for r in evolved)
                checked += 1

                # Both output files must survive Continue after a swap, including
                # cases where the selected boxes span different SRAM banks.
                left_out, right_out = scratch / "left.srm", scratch / "right.srm"
                run(helper, "swap-gen2", left=converted, left_box=box, left_slot=slot,
                    right=source, right_box=source_record[1], right_slot=source_record[2],
                    output_left=left_out, output_right=right_out)
                check_game_load(helper, left_out, scratch, box, int(source_record[3]))
                check_game_load(helper, right_out, scratch, int(source_record[1]), 25)
                checked += 1
    assert all(digest(p) == value for p, value in originals.items()), "private input save changed"
    print("PASS: %d Gen 2 persistence cases; private originals unchanged" % checked)


if __name__ == "__main__":
    main()

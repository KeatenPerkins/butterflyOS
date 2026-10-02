#!/usr/bin/env python3
"""Tests for mapping ordered Butterfly Link serial events to Gen 1 sections."""

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SOURCE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


safety = load("butterflyos_gen1_safety", "butterflyos_gen1_safety.py")
serial = load("butterflyos_gen1_serial", "butterflyos_gen1_serial.py")


def valid_stream():
    sections = bytearray(safety.SECTION_SIZES[0] + safety.SECTION_SIZES[1] + safety.SECTION_SIZES[2])
    sections[safety.SECTION_SIZES[0] + safety.PARTY_COUNT_OFFSET] = 1
    party_start = safety.SECTION_SIZES[0]
    sections[party_start + safety.PARTY_SPECIES_OFFSET] = 0x99
    mon_start = party_start + safety.POKEMON_OFFSET
    sections[mon_start] = 0x99
    sections[mon_start + safety.POKEMON_LEVEL_OFFSET] = 25
    return bytes(sections)


def event(sequence, event_type, payload=b""):
    return ({"sequence": sequence, "type": event_type}, payload)


def main():
    raw = valid_stream()
    collector = serial.Gen1SerialCollector()
    sequence = 0
    for offset in range(0, len(raw), 31):
        block = raw[offset:offset + 31]
        collector.add_event(*event(sequence, "serial-read", block))
        sequence += 1
    collector.add_event(*event(sequence, "transfer-complete"))
    assert collector.complete
    assert collector.byte_count == len(raw)
    assert b"".join(collector.sections()) == raw

    ignored = serial.Gen1SerialCollector()
    ignored.add_event(*event(0, "mode", b"multi"))
    ignored.add_event(*event(1, "serial-write", b"local"))
    ignored.add_event(*event(2, "serial-read", raw))
    ignored.add_event(*event(3, "transfer-complete"))
    assert ignored.sections()[1][safety.PARTY_COUNT_OFFSET] == 1

    def rejects(events, expected):
        candidate = serial.Gen1SerialCollector()
        try:
            for header, payload in events:
                candidate.add_event(header, payload)
            candidate.sections()
        except serial.Gen1SerialTraceError as error:
            assert str(error) == expected, (str(error), expected)
        else:
            raise AssertionError("unsafe serial trace accepted: " + expected)

    rejects((event(0, "serial-read", raw),), "transfer-not-complete")
    rejects((event(1, "serial-read", raw),), "serial-sequence-gap")
    rejects((event(0, "transfer-complete", b"duplicate"),), "completion-carries-data")
    rejects((event(0, "serial-read", raw), event(1, "transfer-complete"), event(2, "serial-read", b"x")), "event-after-complete")
    print("PASS: Gen 1 serial trace collection and boundary tests")


if __name__ == "__main__":
    main()

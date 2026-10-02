#!/usr/bin/env python3
"""Safety checks for the conservative Gen 1 buffered payload validator."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos_gen1_safety.py"
spec = importlib.util.spec_from_file_location("butterflyos_gen1_safety", MODULE_PATH)
safety = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safety)


def valid_sections():
    section0 = bytes(safety.SECTION_SIZES[0])
    section1 = bytearray(safety.SECTION_SIZES[1])
    section2 = bytes(safety.SECTION_SIZES[2])
    section1[safety.PARTY_COUNT_OFFSET] = 2
    section1[safety.PARTY_SPECIES_OFFSET:safety.PARTY_SPECIES_OFFSET + 2] = bytes((0x99, 0xA5))
    section1[safety.PARTY_SPECIES_OFFSET + 2:safety.PARTY_SPECIES_OFFSET + 6] = bytes((0xFF, 0xFF, 0xFF, 0xFF))
    for index, (species, level) in enumerate(((0x99, 20), (0xA5, 37))):
        start = safety.POKEMON_OFFSET + index * safety.POKEMON_SIZE
        section1[start] = species
        section1[start + safety.POKEMON_LEVEL_OFFSET] = level
    return (section0, bytes(section1), section2)


def rejects(mutator, expected):
    sections = list(valid_sections())
    sections[1] = bytearray(sections[1])
    mutator(sections[1])
    try:
        safety.validate_sections(tuple(sections))
    except safety.Gen1PayloadError as error:
        assert str(error) == expected, (str(error), expected)
    else:
        raise AssertionError("unsafe payload accepted: " + expected)


def main():
    sections = valid_sections()
    metadata = safety.validate_sections(sections)
    assert metadata["team_size"] == 2
    assert metadata["species"] == (0x99, 0xA5)
    assert metadata["levels"] == (20, 37)
    assert len(metadata["sha256"]) == 64

    rejects(lambda data: data.__setitem__(safety.PARTY_COUNT_OFFSET, 0), "invalid-party-size")
    rejects(lambda data: data.__setitem__(safety.PARTY_SPECIES_OFFSET, 0), "empty-active-species")
    rejects(lambda data: data.__setitem__(safety.PARTY_SPECIES_OFFSET + 2, 0x01), "trailing-party-species")
    rejects(lambda data: data.__setitem__(safety.POKEMON_OFFSET + safety.POKEMON_LEVEL_OFFSET, 101), "invalid-pokemon-level")
    rejects(lambda data: data.__setitem__(safety.POKEMON_OFFSET, 0xA5), "species-list-mismatch")

    digest = metadata["sha256"]
    assert safety.validate_digest(sections, digest)["sha256"] == digest
    try:
        safety.validate_digest(sections, "0" * 64)
    except safety.Gen1PayloadError as error:
        assert str(error) == "payload-digest-mismatch"
    else:
        raise AssertionError("digest mismatch accepted")
    print("PASS: Gen 1 structural safety and digest validation tests")


if __name__ == "__main__":
    main()

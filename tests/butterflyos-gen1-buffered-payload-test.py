#!/usr/bin/env python3
"""Safety/shape tests for the first Gen 1 buffered-trade payload."""

import hashlib
import struct


GEN1_SECTION_SIZES = (0x0A, 0x1A2, 0xC5)
GEN1_TOTAL_SIZE = sum(GEN1_SECTION_SIZES)
HEADER = struct.Struct("!4sBBH32s")
MAGIC = b"B1TR"
VERSION = 1


def pack_sections(sections):
    if len(sections) != len(GEN1_SECTION_SIZES):
        raise ValueError("invalid section count")
    payload = b"".join(bytes(section) for section in sections)
    if tuple(map(len, sections)) != GEN1_SECTION_SIZES:
        raise ValueError("invalid section size")
    digest = hashlib.sha256(payload).digest()
    return HEADER.pack(MAGIC, VERSION, len(sections), len(payload), digest) + payload


def unpack(frame):
    if len(frame) < HEADER.size:
        raise ValueError("truncated trade payload")
    magic, version, count, length, digest = HEADER.unpack(frame[:HEADER.size])
    payload = frame[HEADER.size:]
    if magic != MAGIC or version != VERSION or count != len(GEN1_SECTION_SIZES):
        raise ValueError("invalid trade header")
    if length != GEN1_TOTAL_SIZE or len(payload) != length:
        raise ValueError("invalid trade length")
    if hashlib.sha256(payload).digest() != digest:
        raise ValueError("trade checksum failed")
    offset = 0
    sections = []
    for size in GEN1_SECTION_SIZES:
        sections.append(payload[offset:offset + size])
        offset += size
    return tuple(sections)


def main():
    sections = tuple(bytes([index]) * size for index, size in enumerate(GEN1_SECTION_SIZES))
    frame = pack_sections(sections)
    assert unpack(frame) == sections
    assert len(frame) == HEADER.size + GEN1_TOTAL_SIZE

    corrupt = bytearray(frame)
    corrupt[-1] ^= 0xFF
    try:
        unpack(corrupt)
    except ValueError:
        pass
    else:
        raise AssertionError("corrupt trade payload accepted")

    try:
        pack_sections((sections[0], b"short", sections[2]))
    except ValueError:
        pass
    else:
        raise AssertionError("wrong section size accepted")
    print("PASS: Gen 1 buffered-trade payload shape and checksum tests")


if __name__ == "__main__":
    main()

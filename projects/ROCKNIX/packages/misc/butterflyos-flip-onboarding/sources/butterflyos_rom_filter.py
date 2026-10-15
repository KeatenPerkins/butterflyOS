#!/usr/bin/env python3
"""Cheap ROM discovery filter; deeper ROM/save qualification stays in writers."""
import sys
from pathlib import Path
import zipfile
import zlib

# English Gen III families supported by the sprite extractor and save tools.
GEN3_CODES = {b'AXVE': 'ruby', b'AXPE': 'sapphire', b'BPEE': 'emerald',
              b'BPRE': 'firered', b'BPGE': 'leafgreen'}
MAX_ROM_BYTES = 32 * 1024 * 1024


def read_gen3_rom(path, header_only=False):
    """Read one bounded GBA payload without extracting archive paths to disk."""
    if Path(path).suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            members = [m for m in archive.infolist()
                       if not m.is_dir() and m.filename.lower().endswith('.gba')]
            if len(members) != 1:
                raise ValueError('A ROM ZIP must contain exactly one GBA game.')
            member = members[0]
            if not 0xC0 <= member.file_size <= MAX_ROM_BYTES:
                raise ValueError('Unsupported GBA ROM size.')
            with archive.open(member) as handle:
                return handle.read(0xC0 if header_only else MAX_ROM_BYTES + 1)
    if not 0xC0 <= Path(path).stat().st_size <= MAX_ROM_BYTES:
        raise ValueError('Unsupported GBA ROM size.')
    with open(path, 'rb') as handle:
        return handle.read(0xC0 if header_only else MAX_ROM_BYTES + 1)


def gen3_rom_family(path):
    try:
        header = read_gen3_rom(path, header_only=True)
        return GEN3_CODES.get(header[0xAC:0xB0], '') if len(header) == 0xC0 else ''
    except (OSError, ValueError, zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError):
        return ''


if __name__ == '__main__':
    raise SystemExit(0 if len(sys.argv) == 2 and gen3_rom_family(sys.argv[1]) else 1)

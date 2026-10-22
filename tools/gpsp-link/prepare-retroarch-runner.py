#!/usr/bin/env python3
"""Adapt a copied live runemu.sh only for the isolated frontend test."""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
build = root / '.cache/gpsp-link-tests/retroarch-current'
source = (build / 'device-runemu.sh').read_text()
assert source.count('/usr/bin/${RABIN}') == 1
source = source.replace('/usr/bin/${RABIN}',
    '/storage/.config/butterflyos/gpsp-link-tests/retroarch-current/retroarch32')
old = 'RETROARCH_TEMP_CONFIG="/storage/.config/retroarch/retroarch.cfg"'
assert source.count(old) == 1
source = source.replace(old,
    'RETROARCH_TEMP_CONFIG="${BF_RA_TEST_CONFIG:?Missing isolated test configuration}"')
(build / 'runemu-retroarch-current.sh').write_text(source)

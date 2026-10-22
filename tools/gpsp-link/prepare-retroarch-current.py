#!/usr/bin/env python3
"""Prepare the pinned development frontend from its verified source archive."""
from pathlib import Path
import hashlib
import subprocess

root = Path(__file__).resolve().parents[2]
build = root / '.cache/gpsp-link-tests/retroarch-current'
archive = build / 'source.tar.gz'
expected = '0d9a7c3acf988fe06f0fc7b27f72ad65adaa8b7e6681fbda48e4f59ac1883f1b'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
source = build / 'source'
if source.exists():
    raise SystemExit('Source directory exists; refusing to overwrite')
source.mkdir()
subprocess.run(['tar', '-xzf', str(archive), '--strip-components=1', '-C', str(source)], check=True)
patches = root / 'projects/ROCKNIX/packages/emulators/libretro/retroarch/patches'
for name in ['0003-fix-oga-no-preferred.patch', '0004-drm-resolution.patch',
             '0008-disable_search.patch', '0009-hide-wayland-checkerboard.patch',
             '0014-fallback-to-built-in-controls.patch']:
    subprocess.run(['patch', '--batch', '-p1', '-i', str(patches / name)], cwd=source, check=True)
subprocess.run(['patch', '--batch', '-p1', '-i', str(root / 'tools/gpsp-link/retroarch-current-local-socket.patch')], cwd=source, check=True)
print('Prepared RetroArch 9e1c1e8ac897625ed75920019f4f62a173a4eedf')

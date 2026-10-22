#!/usr/bin/env python3
"""Prepare an isolated pinned gpSP tree from the already downloaded source cache."""
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[2]
revision = 'b0d5d27ae51c23f514974ddffa5760f1e1d05d9b'
repo = root / 'sources/gpsp-lr' / ('gpsp-lr-' + revision)
out = root / '.cache/gpsp-link-tests/diagnostic-core/source'
if out.exists():
    raise SystemExit('Source directory already exists; use the existing prepared tree or a fresh cache directory.')
out.mkdir(parents=True)
p = subprocess.Popen(['git', '-C', str(repo), 'archive', revision], stdout=subprocess.PIPE)
subprocess.run(['tar', '-xf', '-', '-C', str(out)], stdin=p.stdout, check=True)
p.stdout.close()
if p.wait(): raise SystemExit('Source export failed')
platform = (root / 'projects/ROCKNIX/packages/emulators/libretro/gpsp-lr/patches/000-platform.patch').read_text().replace('@DEVICE@', 'RK3566')
subprocess.run(['patch', '-p1'], cwd=out, input=platform, text=True, check=True)
subprocess.run(['patch', '-p1', '-i', str(Path(__file__).with_name('rfu-diagnostics.patch'))], cwd=out, check=True)
print(out)

#!/usr/bin/env python3
"""Export a pinned newer gpSP into an isolated diagnostic cable-test build tree."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2]
revision='5819380c2ffb0900219d700a382ee68c464ebb99'
repo=root/'.cache/gpsp-link-upstream'
out=root/'.cache/gpsp-link-tests/cable-close-words/source'
if out.exists():raise SystemExit('Cable source directory already exists; refusing to overwrite it.')
out.mkdir(parents=True)
p=subprocess.Popen(['git','-C',str(repo),'archive',revision],stdout=subprocess.PIPE)
subprocess.run(['tar','-xf','-','-C',str(out)],stdin=p.stdout,check=True);p.stdout.close()
if p.wait():raise SystemExit('Source export failed')
platform=(root/'projects/ROCKNIX/packages/emulators/libretro/gpsp-lr/patches/000-platform.patch').read_text().replace('@DEVICE@','RK3566')
subprocess.run(['patch','-p1'],cwd=out,input=platform,text=True,check=True)
subprocess.run(['patch','-p1'],cwd=out,input=(root/'tools/gpsp-link/cable-diagnostics.patch').read_text(),text=True,check=True)
subprocess.run(['patch','-p1'],cwd=out,input=(root/'tools/gpsp-link/cable-handshake-wait.patch').read_text(),text=True,check=True)
subprocess.run(['patch','-p1'],cwd=out,input=(root/'tools/gpsp-link/cable-close-trace.patch').read_text(),text=True,check=True)
subprocess.run(['patch','-p1'],cwd=out,input=(root/'tools/gpsp-link/cable-close-words.patch').read_text(),text=True,check=True)
print(out)

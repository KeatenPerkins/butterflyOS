#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prepare a reversible live-test bundle from completed native OS packages.

Extract the tar in LIVE_ROOT on each matching development device, then run
activate.py with no game open. Bind mounts disappear on reboot. Never writes
ordinary ROMs, saves, settings, or binaries in the read-only OS image.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[2]
LIVE_ROOT=Path('/storage/.config/butterflyos/bslap-single-instance-test')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
parser=argparse.ArgumentParser()
parser.add_argument('--build',required=True,type=Path)
parser.add_argument('--out',required=True,type=Path)
args=parser.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
manifest_path=args.build/'install_pkg/bslap-backend-1.0.3/usr/share/bslap/backend.json'
manifest=json.loads(manifest_path.read_text())
canonical='/usr/lib/libretro/gambatte_bslap_libretro.so'
core=args.build/'install_pkg/gambatte-bslap-lr-466e8b174982b3fdb5a026f60efc51972d1576b0'/canonical.lstrip('/')
assert digest(core)==manifest['files'][canonical]
shutil.copy2(core,args.out/'gambatte_bslap_libretro.so')
sources=ROOT/'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'
for name in ('butterflyos-bslap.py','butterflyos-bslap-gb.py','butterflyos-bslap-gb-netpacket.py'):
    text=(sources/name).read_text()
    if name=='butterflyos-bslap.py':
        old='path = Path(__file__).with_name(names[mode])'
        assert text.count(old)==1
        text=text.replace(old,'path = Path('+repr(str(LIVE_ROOT))+') / names[mode]')
    if name.endswith('-netpacket.py'):
        old="CORE = Path('/usr/lib/libretro/gambatte_bslap_libretro.so')"
        assert text.count(old)==1
        text=text.replace(old,'CORE = Path('+repr(str(LIVE_ROOT/'gambatte_bslap_libretro.so'))+')')
    compile(text,name,'exec')
    (args.out/name).write_text(text)
    (args.out/name).chmod(0o755)
manifest['files'][str(LIVE_ROOT/'gambatte_bslap_libretro.so')]=manifest['files'][canonical]
manifest['backend']='bslap-live-netpacket-'+hashlib.sha256(json.dumps(manifest['files'],sort_keys=True).encode()).hexdigest()[:16]
(args.out/'backend.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(ROOT/'tests/butterflyos-bslap-netpacket-core-test.py',args.out)
checks={p.name:digest(p) for p in args.out.iterdir() if p.is_file() and p.name not in ('checks.json','activate.py','live-test.tar')}
(args.out/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
activation='''#!/usr/bin/env python3
import hashlib, json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
assert root==Path(LIVE_PATH), 'Extract into the documented live-test folder'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
if subprocess.run(['pidof','retroarch','retroarch32'],stdout=subprocess.DEVNULL).returncode==0:
    raise SystemExit('Exit the running game first.')
for name, expected in json.loads((root/'checks.json').read_text()).items():
    assert digest(root/name)==expected, name+' changed'
manifest=json.loads((root/'backend.json').read_text())
for name, expected in manifest['files'].items():
    if name==CANONICAL_PATH:continue # live core uses the verified storage path
    assert digest(Path(name))==expected, 'Installed backend differs: '+name
for name in ('butterflyos-bslap.py','butterflyos-bslap-gb.py','butterflyos-bslap-gb-netpacket.py'):
    compile((root/name).read_text(),name,'exec')
# Both targets already exist; only temporary bind mounts are used.
targets=[('backend.json','/usr/share/bslap/backend.json'),
         ('butterflyos-bslap.py','/usr/bin/butterflyos-bslap.py')]
# Tar extraction replaces source inodes; unmount our earlier live files first.
# A bind onto a deleted old inode can otherwise fail even when ls can read it.
for source,target in reversed(targets):
    while True:
        entries=[line.split() for line in Path('/proc/self/mountinfo').read_text().splitlines()]
        existing=[fields for fields in entries if fields[4]==target]
        if not existing:break
        if any('/bslap-single-instance-test/' not in fields[3] for fields in existing):
            raise SystemExit('Another override owns '+target)
        subprocess.run(['umount',target],check=True)
mounted=[]
try:
    for source,target in targets:
        subprocess.run(['mount','--bind',str(root/source),target],check=True)
        mounted.append(target)
except BaseException:
    for target in reversed(mounted):subprocess.run(['umount',target],check=False)
    raise
print('Ready after reopening Bslap. Temporary until reboot. '+manifest['backend'])
'''.replace('LIVE_PATH',repr(str(LIVE_ROOT))).replace('CANONICAL_PATH',repr(canonical))
(args.out/'activate.py').write_text(activation)
with tarfile.open(args.out/'live-test.tar','w') as archive:
    for path in sorted(args.out.iterdir()):
        if path.is_file() and path.name!='live-test.tar':archive.add(path,arcname=path.name)
print(json.dumps(dict(bundle=str(args.out/'live-test.tar'),backend=manifest['backend'],core_sha=manifest['files'][canonical]),indent=2))

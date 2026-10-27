#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Install checksum-pinned, live-tested Bslap binaries without replacing defaults.

Inputs are deliberately explicit: reconstruct them using tools/gpsp-link if the
verified local cache is absent. A different compiler output requires renewed
validation and an intentional checksum update, never silently accepting it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = (
    ('.cache/gpsp-link-tests/retroarch-current/source/retroarch',
     '/usr/libexec/bslap/retroarch32',
     '556a1d7b09ea280ba06d34ad53347864d6f4288702894cbe104842591bb5da89'),
    ('.cache/gpsp-link-tests/cable-handshake-plain/source/gpsp_libretro.so',
     '/usr/lib/libretro/gpsp_bslap_libretro.so',
     '1ae51cbbc844f4c9574dbb2dc3853097d9badc53b32057ec84e1577615b91f55'),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(install, build):
    files = {}
    for source, target, expected in ARTIFACTS:
        source = ROOT / source
        if not source.is_file() or digest(source) != expected:
            raise SystemExit('Missing/changed Bslap input: %s. See tools/bslap/README.md.' % source)
        out = install / target.lstrip('/')
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, out)
        out.chmod(0o755)
        files[target] = expected
    # Hash the completed, stripped native packages that this image will install.
    for package, version, target in (
        ('retroarch', 'bdba046fa6766380bc2457532f38e589df769aaf', '/usr/bin/retroarch'),
        ('sameboy-lr', '2d29ece3b8e7ec44347c9daad0fabb84912ed44f', '/usr/lib/libretro/sameboy_libretro.so'),
        ('gambatte-bslap-lr', '466e8b174982b3fdb5a026f60efc51972d1576b0', '/usr/lib/libretro/gambatte_bslap_libretro.so'),
    ):
        source = build / 'install_pkg' / (package + '-' + version) / target.lstrip('/')
        if not source.is_file():
            raise SystemExit('Missing native Bslap dependency: ' + str(source))
        files[target] = digest(source)
    infos = list((build / 'install_pkg').glob('core-info-*/usr/lib/libretro/gpsp_libretro.info'))
    if len(infos) != 1:
        raise SystemExit('Expected one installed gpSP core info file.')
    shutil.copy2(infos[0], install / 'usr/lib/libretro/gpsp_bslap_libretro.info')
    gambatte_infos = list((build / 'install_pkg').glob('core-info-*/usr/lib/libretro/gambatte_libretro.info'))
    if len(gambatte_infos) != 1:
        raise SystemExit('Expected one installed Gambatte core info file.')
    shutil.copy2(gambatte_infos[0], install / 'usr/lib/libretro/gambatte_bslap_libretro.info')
    manifest = dict(schema=1, files=files, sources={
        'retroarch32': '9e1c1e8ac897625ed75920019f4f62a173a4eedf',
        'gpsp': '5819380c2ffb0900219d700a382ee68c464ebb99',
        'gambatte-netpacket': '466e8b174982b3fdb5a026f60efc51972d1576b0',
        'sameboy': '2d29ece3b8e7ec44347c9daad0fabb84912ed44f',
        'retroarch': 'bdba046fa6766380bc2457532f38e589df769aaf',
    })
    manifest['backend'] = 'bslap-v4-' + hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16]
    destination = install / 'usr/share/bslap/backend.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + '\n')
    print('Staged', manifest['backend'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', required=True, type=Path)
    parser.add_argument('--build', required=True, type=Path)
    args = parser.parse_args()
    stage(args.install, args.build)

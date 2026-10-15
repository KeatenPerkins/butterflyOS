#!/usr/bin/env python3
"""Package audited SYSTEM/KERNEL files in the format accepted by the updater."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import runpy
import tarfile


def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare(payload, output, version, release):
    root = Path(__file__).resolve().parents[1]
    updater = runpy.run_path(str(root/'projects/ROCKNIX/packages/rocknix/sources/scripts/butterflyos-update'), run_name='package_validation')
    identity = dict(schema=1, os='ButterflyOS', device='Miyoo_Flip_V2', arch='aarch64', version=version)
    name = 'ButterflyOS-Miyoo-Flip-V2-' + version + '.tar'
    # Validate inputs before creating an output. The real updater owns the contract.
    updater['validate_manifest'](dict(identity, size=1, unpacked_size=1, sha256='0'*64,
        url='https://github.com/KeatenPerkins/butterflyOS/releases/download/' + release + '/' + name))
    for n in ['SYSTEM', 'KERNEL']:
        if not (payload/n).is_file(): raise ValueError('Missing payload ' + n)
    output.mkdir(parents=True, exist_ok=True)
    archive = output/name
    prefix = 'ButterflyOS-' + version
    def add_bytes(t, name, data):
        member = tarfile.TarInfo(name); member.mode=0o644; member.size=len(data)
        t.addfile(member, io.BytesIO(data))
    with tarfile.open(archive, 'x', format=tarfile.USTAR_FORMAT) as t:
        add_bytes(t, prefix+'/butterflyos-update.json', (json.dumps(identity, indent=2)+'\n').encode())
        for n in ['SYSTEM', 'KERNEL']:
            p = payload/n
            add_bytes(t, prefix+'/target/'+n+'.md5', (digest(p, 'md5')+'  target/'+n+'\n').encode())
            member=tarfile.TarInfo(prefix+'/target/'+n); member.mode=0o644; member.size=p.stat().st_size
            with p.open('rb') as f: t.addfile(member, f)
    with tarfile.open(archive) as t: expanded=sum(m.size for m in t.getmembers())
    manifest=dict(identity, size=archive.stat().st_size, unpacked_size=expanded, sha256=digest(archive),
        url='https://github.com/KeatenPerkins/butterflyOS/releases/download/'+release+'/'+name)
    updater['validate_manifest'](manifest)
    updater['validate_archive'](archive, manifest)
    (output/'butterflyos-update.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (output/(name+'.sha256')).write_text(manifest['sha256']+'  '+name+'\n')
    return archive


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--release', required=True)
    args=parser.parse_args()
    print(prepare(args.payload_dir, args.output_dir, args.version, args.release))

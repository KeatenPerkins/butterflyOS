#!/usr/bin/env python3
"""Reject mismatched game families without modifying private fixture saves.

Usage: test.py SOURCE_DIR FIXTURES_DIR NATIVE_HELPER
Fixtures are matching English ROM/save pairs (.gba or single-ROM .zip + .srm).
"""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

sources,fixtures,helper=map(Path,sys.argv[1:4])
spec=importlib.util.spec_from_file_location('gift',sources/'butterflyos-gen3-gift.py')
gift=importlib.util.module_from_spec(spec);spec.loader.exec_module(gift)
pairs=[]
for save in fixtures.glob('*.srm'):
    rom=next((save.with_suffix(ext) for ext in ('.zip','.gba') if save.with_suffix(ext).is_file()),None)
    if rom is not None:pairs.append((save,rom,gift.rom_profile(gift.read_rom(rom))[0]))
assert len(pairs)==5,'Supply all five game pairs'
before={save:hashlib.sha256(save.read_bytes()).hexdigest() for save,_,_ in pairs}
count=0
with tempfile.TemporaryDirectory() as directory:
    for save,_,save_family in pairs:
        for _,rom,rom_family in pairs:
            if rom_family==save_family:continue
            out=Path(directory)/('mismatch-'+str(count)+'.srm')
            cmd=['python3',str(sources/'butterflyos-gen3-gift.py'),'--save',str(save),'--rom',str(rom),'--preset','surf-pichu-egg','--box','0','--slot','0','--output',str(out),'--helper',str(helper)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            assert result.returncode!=0 and 'family does not match' in result.stderr,(save,rom,result.stderr)
            assert not out.exists(),'A refused operation created output'
            count+=1
assert count==16,count
assert all(hashlib.sha256(save.read_bytes()).hexdigest()==digest for save,digest in before.items())
print('PASS: 16 cross-family ROM/save mismatches refused; no output created; all source saves unchanged')

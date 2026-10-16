#!/usr/bin/env python3
"""Private-fixture direct-gift matrix. Usage: test.py SOURCE_DIR FIXTURES_DIR HELPER"""
import hashlib
import importlib.util
import itertools
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from unittest.mock import patch

sources,fixtures,helper=map(Path,sys.argv[1:4])
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('gift',sources/'butterflyos-gen3-gift.py')
u=module('ui',sources/'butterflyos-save-trade-sdl.py')
expected={
 'gift-jirachi':(385,5,(273,93,156,0),(169,170),'random',False),
 'gift-celebi':(251,30,(215,219,246,248),(0,),'never',False),
 'gift-mew':(151,10,(1,144,0,0),(0,),'never',True),
 'gift-deoxys':(386,70,(322,105,354,63),(0,),'never',True),
 'gift-shiny-zigzagoon':(263,5,(33,45,39,0),(168,),'always',False),
}
assert g.DIRECT_PRESETS==expected
assert {entry[0] for entry in u.GEN3_DIRECT_GIFTS}==set(expected)
for trainer in (0,1,0xffffffff,0x12345678):
 for seed in (0,1,23,0x12345678,0xffffffff,trainer):
  for preset,(_,_,_,_,policy,_) in expected.items():
   with patch.object(g.secrets,'randbits',return_value=seed):pid=g.choose_personality(trainer,preset)
   shiny=((trainer&65535)^(trainer>>16)^(pid&65535)^(pid>>16))<8
   if policy=='never':assert not shiny
   elif policy=='always':assert shiny
   else:assert pid==seed
count=0;games=0
with tempfile.TemporaryDirectory() as directory:
 d=Path(directory);u.STATE_ROOT=str(d/'sessions')
 for save in fixtures.glob('*.srm'):
  rom_path=next((save.with_suffix(ext) for ext in ('.zip','.gba') if save.with_suffix(ext).is_file()),None)
  if not rom_path:continue
  rom=g.read_rom(rom_path);profile=g.rom_profile(rom);sizes=g.section_sizes(profile[0]);original=save.read_bytes();sections=g.active_sections(original,sizes)
  pc=b''.join(original[sections[n]:sections[n]+sizes[n]] for n in range(5,14));free=next(i for i in range(420) if pc[4+i*80:4+(i+1)*80]==bytes(80));box,slot=divmod(free,30);at=4+free*80
  ot=struct.unpack_from('<I',original,sections[0]+10)[0]
  for preset,(national,level,moves,items,policy,fateful) in expected.items():
   for order in range(24):
    if policy=='always':
     tx=(ot&65535)^(ot>>16)
     pid=next(v for low in range(256) for sv in range(8) if (v:=low|((tx^low^sv)<<16))%24==order)
    else:
     pid=next(v for v in range(order,order+240,24) if ((ot&65535)^(ot>>16)^(v&65535)^(v>>16))>=8)
    item=items[order%len(items)]
    with patch.object(g,'choose_personality',return_value=pid),patch.object(g.secrets,'choice',return_value=item):result,meta=g.prepare(original,rom,preset,box,slot)
    assert meta['egg'] is False and meta['level']==level and meta['held']==item
    edited=b''.join(result[sections[n]:sections[n]+sizes[n]] for n in range(5,14));record=edited[at:at+80];key=pid^ot
    plain=b''.join(struct.pack('<I',x^key) for x in struct.unpack('<12I',record[32:]));orderlist=list(itertools.permutations(range(4)))[pid%24];blocks={kind:plain[i*12:(i+1)*12] for i,kind in enumerate(orderlist)}
    species,held,exp=struct.unpack_from('<HHI',blocks[0]);assert held==item
    assert struct.unpack_from('<411H',rom,profile[2])[species-1]==national
    stats=rom[profile[3]+species*28:profile[3]+(species+1)*28]
    assert exp==struct.unpack_from('<I',rom,profile[4]+stats[19]*404+level*4)[0]
    assert blocks[0][9]==stats[18] and record[19]==2
    assert record[8:18]==rom[profile[6]+species*11:profile[6]+species*11+10]
    assert struct.unpack('<4H',blocks[1][:8])==moves
    assert blocks[1][8:12]==bytes(rom[profile[5]+move*12+4] if move else 0 for move in moves)
    assert not struct.unpack_from('<I',blocks[3],4)[0]&(1<<30)
    assert bool(struct.unpack_from('<I',blocks[3],8)[0]&(1<<31))==fateful
    origins=struct.unpack_from('<H',blocks[3],2)[0];assert origins&127==level and origins>>7&15==profile[1]
    assert record[20:27]==original[sections[0]:sections[0]+7]
    assert edited[:at]==pc[:at] and edited[at+80:]==pc[at+80:]
    allowed={sections[5+i//0xF80]+i%0xF80 for i in range(at,at+80)}|{sections[n]+j for n in range(5,14) for j in (0xFF6,0xFF7)}
    assert all(i in allowed for i,(a,b) in enumerate(zip(original,result)) if a!=b)
    g.active_sections(result,sizes);out=d/'native.srm';out.write_bytes(result)
    inspected=subprocess.check_output([str(helper),'inspect','--save',str(out)],text=True)
    line=next(l for l in inspected.splitlines() if l.startswith('box_record\t%d\t%d\t'%(box,slot)))
    assert int(line.split('\t')[3])==species and 'moves='+','.join(map(str,moves)) in line and 'held='+str(item) in line
    assert line.split('\t')[6]==('yes' if policy=='always' else 'no')
    count+=1
   # Exercise the actual protected UI prepare, backup and Commit with this gift.
   dest=d/'destination.srm';dest.write_bytes(original)
   session,message=u.prepare_gen3_gift((str(dest),box,slot),str(rom_path),preset);assert session,message
   assert dest.read_bytes()==original
   ok,message=u.commit_copy(session);assert ok,message
   assert Path(session,'original-destination-backup').read_bytes()==original
   assert not u.commit_copy(session)[0]
  assert save.read_bytes()==original
  games+=1;print(profile[0],rom[0xAC:0xB0].decode(),'passed',flush=True)
assert games==5 and count==600,(games,count)
print('PASS: 600 direct-gift/layout/game combinations, shiny policies, ROM data, native reader, exact writes and 25 protected commits; source saves unchanged')

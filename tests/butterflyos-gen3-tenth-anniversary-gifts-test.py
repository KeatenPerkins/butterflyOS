#!/usr/bin/env python3
"""Private-fixture tenth-anniversary reward matrix; no source save or ROM is modified. Usage: test.py SOURCE_DIR FIXTURES_DIR HELPER"""
import hashlib
import json
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
expected={'tenth-bulbasaur': (1, 70, (230, 74, 76, 235), (0,), 'never', False), 'tenth-charizard': (6, 70, (17, 163, 82, 83), (0,), 'never', False), 'tenth-blastoise': (9, 70, (182, 240, 130, 56), (0,), 'never', False), 'tenth-pikachu-fly': (25, 70, (85, 87, 113, 19), (0,), 'never', False), 'tenth-pikachu-standard': (25, 70, (85, 97, 87, 113), (0,), 'never', False), 'tenth-alakazam': (65, 70, (248, 347, 94, 271), (0,), 'never', False), 'tenth-articuno': (144, 70, (97, 170, 58, 115), (0,), 'never', False), 'tenth-zapdos': (145, 70, (97, 197, 65, 268), (0,), 'never', False), 'tenth-moltres': (146, 70, (97, 203, 53, 219), (0,), 'never', False), 'tenth-dragonite': (149, 70, (97, 219, 17, 200), (0,), 'never', False), 'tenth-typhlosion': (157, 70, (98, 172, 129, 53), (0,), 'never', False), 'tenth-espeon': (196, 70, (60, 244, 94, 234), (0,), 'never', False), 'tenth-umbreon': (197, 70, (185, 212, 103, 236), (0,), 'never', False), 'tenth-raikou': (243, 70, (98, 209, 115, 242), (0,), 'never', False), 'tenth-entei': (244, 70, (83, 23, 53, 207), (0,), 'never', False), 'tenth-suicune': (245, 70, (16, 62, 54, 243), (0,), 'never', False), 'tenth-tyranitar': (248, 70, (37, 184, 242, 89), (0,), 'never', False), 'tenth-lugia': (249, 70, (105, 56, 240, 129), (0,), 'never', False), 'tenth-ho-oh': (250, 70, (105, 126, 241, 129), (0,), 'never', False), 'tenth-celebi': (251, 70, (246, 248, 226, 195), (0,), 'never', False), 'tenth-blaziken': (257, 70, (299, 163, 119, 327), (0,), 'never', False), 'tenth-absol': (359, 70, (104, 163, 248, 195), (0,), 'never', False), 'tenth-latias': (380, 70, (296, 94, 105, 204), (0,), 'never', False), 'tenth-latios': (381, 70, (295, 94, 105, 349), (0,), 'never', False)}
assert g.TENTH_ANNIVERSARY_PRESETS==expected
catalog=json.loads((Path(__file__).parent/"fixtures/butterflyos-gen3-tenth-anniversary-catalog.json").read_text())["records"]
for species,level,moves,items,policy,fateful in expected.values():
 assert any(row[0]==species and row[1]==level and tuple(row[2:])==moves for row in catalog)
 assert items==(0,) and policy=="never" and not fateful
assert {entry[0] for entry in u.GEN3_TENTH_ANNIVERSARY_GIFTS}==set(expected)
assert {(v[0],v[1],v[2]) for v in expected.values()}=={(r[0],r[1],tuple(r[2:])) for r in catalog}
assert len({(label,desc) for _,label,desc in u.GEN3_TENTH_ANNIVERSARY_GIFTS})==24
for trainer in (0,1,0xffffffff,0x12345678):
 for seed in (0,1,23,0x12345678,0xffffffff,trainer):
  for preset,(_,_,_,_,policy,_) in expected.items():
   with patch.object(g.secrets,'randbits',return_value=seed):pid=g.choose_personality(trainer,preset)
   shiny=((trainer&65535)^(trainer>>16)^(pid&65535)^(pid>>16))<8
   if policy=='never':assert not shiny
   elif policy=='always':assert shiny
   else:assert pid==seed
# Run the real gift CLI with the host helper, preserving production defaults.
real_run=subprocess.run
def run_local(command,**kwargs):
 command=list(command)
 if len(command)>1 and command[1]=='/usr/bin/butterflyos-gen3-gift.py':
  command[1]=str(sources/'butterflyos-gen3-gift.py');command+=['--helper',str(helper)]
 return real_run(command,**kwargs)
# The shared subprocess module is restored after each protected prepare call.
count=0;games=0
with tempfile.TemporaryDirectory() as directory:
 d=Path(directory);u.STATE_ROOT=str(d/'sessions')
 for save in fixtures.glob('*.srm'):
  rom_path=next((save.with_suffix(ext) for ext in ('.zip','.gba') if save.with_suffix(ext).is_file()),None)
  if not rom_path:continue
  rom=g.read_rom(rom_path);profile=g.rom_profile(rom);sizes=g.section_sizes(profile[0]);original=save.read_bytes();sections=g.active_sections(original,sizes)
  pc=b''.join(original[sections[n]:sections[n]+sizes[n]] for n in range(5,14));free=next(i for i in range(420) if pc[4+i*80:4+(i+1)*80]==bytes(80));box,slot=divmod(free,30);at=4+free*80
  recipient_ot=struct.unpack_from('<I',original,sections[0]+10)[0]
  ot=recipient_ot^1
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
    assert record[20:27]==bytes((0xBC,0xC6,0xC3,0xC8,0xC5,0xFF,0xFF))
    assert struct.unpack_from('<I',record,4)[0]==ot and (ot&65535)!=(recipient_ot&65535)
    assert blocks[3][1]==255  # Foreign OT + event location selects fateful encounter in Emerald.
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
   with patch.object(u.subprocess,'run',side_effect=run_local):
    session,message=u.prepare_gen3_gift((str(dest),box,slot),str(rom_path),preset)
   assert session,message
   assert dest.read_bytes()==original
   ok,message=u.commit_copy(session);assert ok,message
   assert Path(session,'original-destination-backup').read_bytes()==original
   assert not u.commit_copy(session)[0]
  assert save.read_bytes()==original
  games+=1;print(profile[0],rom[0xAC:0xB0].decode(),'passed',flush=True)
assert games==5 and count==2880,(games,count)
print('PASS: 2880 tenth-anniversary-gift/layout/game combinations, shiny policies, ROM data, native reader, exact writes and 120 protected commits; source saves unchanged')

# Naturally shiny candidates must be rejected for every tenth-anniversary, using
# the actual BLINK trainer identity.
for save in fixtures.glob('*.srm'):
 rom_path=save.with_suffix('.gba')
 if not rom_path.exists():continue
 rom=g.read_rom(rom_path);profile=g.rom_profile(rom);sections=g.active_sections(save.read_bytes(),g.section_sizes(profile[0]))
 save2=save.read_bytes()[sections[0]:sections[0]+g.section_sizes(profile[0])[0]]
 ot=struct.unpack_from('<I',save2,10)[0]^1
 low=0x1234;seed=low|(((ot&65535)^(ot>>16)^low)<<16)
 for preset,spec in expected.items():
  with patch.object(g.secrets,'randbits',return_value=seed):record,metadata=g.make_egg(rom,save2,preset)
  pid,actual_ot=struct.unpack_from('<II',record)
  shiny=((actual_ot&65535)^(actual_ot>>16)^(pid&65535)^(pid>>16))<8
  assert shiny==(spec[4]=='random'),(preset,'incorrect shiny policy')
  assert actual_ot==ot
with patch.object(u,'generation_saves',return_value=[]),patch.object(u,'choose_list',side_effect=[9,None]) as choose,patch.object(u,'generated_gift_workflow') as workflow:
 assert u.choose_gen3_local_save(None) is None
 workflow.assert_called_once_with(None,3,gen3_group='tenth-anniversary')
 assert choose.call_args_list[0].args[3][9][0]=='10TH ANNIVERSARY GIFTS'
print('PASS: anti-shiny anniversary records and controller menu routing')

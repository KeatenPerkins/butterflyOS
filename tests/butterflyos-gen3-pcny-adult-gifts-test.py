#!/usr/bin/env python3
"""Private-fixture PCNY adult reward matrix; no source save or ROM is modified. Usage: test.py SOURCE_DIR FIXTURES_DIR HELPER"""
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
expected={'pcny-adult-pikachu': (25, 50, (85, 97, 87, 113), (0,), 'never', False), 'pcny-adult-gloom': (44, 50, (79, 51, 236, 80), (0,), 'never', False), 'pcny-adult-staryu': (120, 50, (107, 113, 322, 56), (0,), 'never', False), 'pcny-adult-seadra': (117, 45, (82, 56, 239, 58), (0,), 'never', False), 'pcny-adult-flygon': (330, 45, (328, 242, 225, 53), (0,), 'never', False), 'pcny-adult-altaria': (334, 45, (332, 225, 349, 53), (0,), 'never', False), 'pcny-adult-seadra-leer': (117, 45, (82, 56, 239, 43), (0,), 'never', False), 'pcny-adult-altaria-ice-beam': (334, 45, (36, 225, 349, 58), (0,), 'never', False), 'pcny-adult-salamence-thrash': (373, 50, (182, 225, 37, 19), (0,), 'never', False), 'pcny-adult-shedinja': (292, 50, (180, 109, 247, 288), (0,), 'never', False), 'pcny-adult-cacturne': (332, 50, (185, 191, 302, 178), (0,), 'never', False), 'pcny-adult-shuppet': (353, 25, (103, 101, 174, 180), (0,), 'never', False), 'pcny-adult-duskull-lv25-d2': (355, 25, (50, 193, 310, 109), (0,), 'never', False), 'pcny-adult-exploud-lv50-d3': (295, 50, (23, 304, 247, 46), (0,), 'never', False), 'pcny-adult-exploud-lv100-d3': (295, 100, (46, 247, 280, 304), (0,), 'never', False), 'pcny-adult-aggron-lv50-d3': (306, 50, (269, 231, 182, 232), (0,), 'never', False), 'pcny-adult-aggron-lv100-d3': (306, 100, (231, 337, 58, 38), (0,), 'never', False), 'pcny-adult-wailord-lv50-d3': (321, 50, (352, 59, 156, 323), (0,), 'never', False), 'pcny-adult-wailord-lv100-d3': (321, 100, (59, 323, 89, 56), (0,), 'never', False), 'pcny-adult-crawdaunt-lv50-d3': (342, 50, (91, 61, 152, 14), (0,), 'never', False), 'pcny-adult-crawdaunt-lv100-d3': (342, 100, (92, 152, 258, 12), (0,), 'never', False), 'pcny-adult-altaria-lv45-d4': (334, 45, (36, 225, 349, 287), (0,), 'never', False), 'pcny-adult-flygon-lv45-d4': (330, 45, (328, 242, 225, 103), (0,), 'never', False), 'pcny-adult-seadra-lv32-d4': (117, 32, (108, 43, 55, 239), (0,), 'never', False), 'pcny-adult-salamence-lv50-d4': (373, 50, (182, 225, 184, 19), (0,), 'never', False), 'pcny-adult-gardevoir-lv35-d5': (282, 35, (100, 347, 94, 286), (0,), 'never', False), 'pcny-adult-tropius-lv30-d5': (357, 30, (75, 23, 230, 18), (0,), 'never', False), 'pcny-adult-houndour-lv5-d6': (228, 5, (43, 52, 0, 0), (0,), 'never', False), 'pcny-adult-mareep-lv5-d6': (179, 5, (33, 45, 0, 0), (0,), 'never', False), 'pcny-adult-seviper-lv30-d7': (336, 30, (342, 103, 137, 242), (0,), 'never', False), 'pcny-adult-absol-lv35-d7': (359, 35, (13, 44, 14, 180), (0,), 'never', False), 'pcny-adult-absol-lv35-d7-wish': (359, 35, (13, 44, 14, 273), (0,), 'never', False), 'pcny-adult-azurill-lv5-d8': (298, 5, (150, 204, 0, 0), (0,), 'never', False), 'pcny-adult-wynaut-lv5-d8': (360, 5, (150, 204, 227, 0), (0,), 'never', False), 'pcny-adult-huntail-lv20-d8': (367, 20, (250, 44, 103, 0), (0,), 'never', False), 'pcny-adult-gorebyss-lv20-d8': (368, 20, (250, 93, 97, 0), (0,), 'never', False), 'pcny-adult-kingdra-lv35-d9': (230, 35, (108, 43, 55, 239), (0,), 'never', False), 'pcny-adult-zangoose-lv18-d9': (335, 18, (43, 98, 14, 210), (0,), 'never', False), 'pcny-adult-seviper-lv18-d9': (336, 18, (35, 122, 44, 342), (0,), 'never', False), 'pcny-adult-milotic-lv35-d9': (350, 35, (352, 239, 105, 240), (0,), 'never', False), 'pcny-adult-sableye-lv18-d10': (302, 18, (193, 101, 310, 154), (0,), 'never', False), 'pcny-adult-mawile-lv18-d10': (303, 18, (310, 313, 44, 230), (0,), 'never', False), 'pcny-adult-cradily-lv40-d10': (346, 40, (51, 275, 109, 133), (0,), 'never', False), 'pcny-adult-armaldo-lv40-d10': (348, 40, (55, 232, 182, 246), (0,), 'never', False), 'pcny-adult-machamp-lv30-d11': (68, 30, (2, 69, 193, 279), (0,), 'never', False), 'pcny-adult-golem-lv30-d11': (76, 30, (88, 222, 120, 205), (0,), 'never', False), 'pcny-adult-ludicolo-lv20-d11': (272, 20, (310, 45, 71, 267), (0,), 'never', False), 'pcny-adult-shiftry-lv20-d11': (275, 20, (1, 106, 74, 267), (0,), 'never', False)}
assert g.PCNY_ADULT_PRESETS==expected
catalog=json.loads((Path(__file__).parent/"fixtures/butterflyos-gen3-pcny-catalog.json").read_text())["records"]
for species,level,moves,items,policy,fateful in expected.values():
 assert any(row[0]==species and row[1]==level and tuple(row[3:])==moves for row in catalog)
 assert items==(0,) and policy=="never" and not fateful
assert {entry[0] for entry in u.GEN3_PCNY_ADULT_GIFTS}==set(expected)
assert {(v[0],v[1],v[2]) for v in expected.values()}=={(r[0],r[1],tuple(r[3:])) for r in catalog}
assert len({(label,desc) for _,label,desc in u.GEN3_PCNY_ADULT_GIFTS})==48
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
assert games==5 and count==5760,(games,count)
print('PASS: 5760 PCNY adult-gift/layout/game combinations, shiny policies, ROM data, native reader, exact writes and 240 protected commits; source saves unchanged')

# Naturally shiny candidates must be rejected for every PCNY adult, using
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
with patch.object(u,'generation_saves',return_value=[]),patch.object(u,'choose_list',side_effect=[8,None]) as choose,patch.object(u,'generated_gift_workflow') as workflow:
 assert u.choose_gen3_local_save(None) is None
 workflow.assert_called_once_with(None,3,gen3_group='pcny-adults')
 assert choose.call_args_list[0].args[3][8][0]=='PCNY ADULT GIFTS'
print('PASS: anti-shiny PCNY records and controller menu routing')

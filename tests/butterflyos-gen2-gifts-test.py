#!/usr/bin/env python3
"""Private fixture tests. Usage: HELPER SAVE_ROOT ROM_ROOT. Inputs stay unchanged. Add --ui-only for focused workflow checks."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT/'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'
def load(name, filename):
    s=importlib.util.spec_from_file_location(name,SOURCES/filename);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=load('g','butterflyos-gen2-gift.py');ui=load('ui','butterflyos-save-trade-sdl.py')
helper,save_root,rom_root=map(Path,sys.argv[1:4])
ui_only="--ui-only" in sys.argv[4:]
expected={'mew':(151,[1,0,0,0],[35,0,0,0],0,135),
          'celebi':(251,[73,93,215,105],[10,25,5,20],0,135),
          'baton-pass-farfetchd':(83,[226,14,97,163],[40,30,30,20],174,125),
          'earthquake-gligar':(207,[89,40,68,17],[10,35,20,35],150,135)}
expected.update({
    'ancientpower-bulbasaur-egg':(1,[33,45,246,0],[35,40,5,0],0,135),
    'crunch-charmander-egg':(4,[10,45,242,0],[35,40,15,0],0,135),
    'submission-totodile-egg':(158,[10,43,66,0],[35,30,25,0],0,135),
    'night-shade-hoothoot-egg':(163,[33,45,101,0],[35,40,15,0],0,125),
    'sing-pichu-egg':(172,[84,204,47,0],[30,20,15,0],0,125),
    'petal-dance-psyduck-egg':(54,[10,39,80,0],[35,30,20,0],0,125),
    'petal-dance-chikorita-egg':(152,[33,45,80,0],[35,40,20,0],0,135),
    'petal-dance-pichu-egg':(172,[84,204,80,0],[30,20,20,0],0,125),
    'petal-dance-cleffa-egg':(173,[1,204,227,80],[35,20,5,20],0,100),
    'petal-dance-igglybuff-egg':(174,[47,204,111,80],[15,20,40,20],0,100),
    'petal-dance-smoochum-egg':(238,[1,122,80,0],[35,30,20,0],0,125),
    'swift-cleffa-egg':(173,[1,204,227,129],[35,20,5,20],0,100),
    'belly-drum-wooper-egg':(194,[55,39,187,0],[25,30,10,0],0,125),
    'encore-phanpy-egg':(231,[33,45,227,0],[35,40,5,0],0,125),
    'metronome-smoochum-egg':(238,[1,122,118,0],[35,30,10,0],0,125),
    'zap-cannon-squirtle-egg':(7,[33,39,192,0],[35,30,5,0],0,135),
    'growth-eevee-egg':(133,[33,39,74,0],[35,30,40,0],0,125),
    'lovely-kiss-snorlax-egg':(143,[33,142,0,0],[35,10,0,0],0,156),
    'hydro-pump-dratini-egg':(147,[35,43,56,0],[20,30,5,0],0,156),
    'double-edge-cyndaquil-egg':(155,[33,43,38,0],[35,30,15,0],0,135),
    'mimic-igglybuff-egg':(174,[47,204,111,102],[15,20,40,10],0,100),
    'pursuit-elekid-egg':(239,[98,43,228,0],[30,30,20,0],0,125),
    'faint-attack-magby-egg':(240,[52,185,0,0],[25,20,0,0],0,125),
    'rage-tyrogue-egg':(236,[33,99,0,0],[35,20,0,0],0,125),
    'dizzy-punch-sentret-egg':(161,[33,111,146,0],[35,40,10,0],0,125),
    'barrier-ledyba-egg':(165,[33,112,0,0],[35,30,0,0],0,100),
    'growth-spinarak-egg':(167,[40,81,74,0],[35,40,40,0],0,100),
    'light-screen-chinchou-egg':(170,[145,86,48,113],[30,20,20,30],0,156),
    'safeguard-natu-egg':(177,[64,43,219,0],[35,30,25,0],0,125),
    'dizzy-punch-marill-egg':(183,[33,111,146,0],[35,40,10,0],0,100),
    'dizzy-punch-pichu-egg':(172,[84,204,146,0],[30,20,10,0],0,125),
    'scary-face-pichu-egg':(172,[84,204,184,0],[30,20,10,0],0,125),
    'scary-face-cleffa-egg':(173,[1,204,227,184],[35,20,5,10],0,100),
    'scary-face-igglybuff-egg':(174,[47,204,111,184],[15,20,40,10],0,100),
    'hydro-pump-marill-egg':(183,[33,111,56,0],[35,40,5,0],0,100),
    'scary-face-marill-egg':(183,[33,111,184,0],[35,40,10,0],0,100),
    'substitute-sudowoodo-egg':(185,[88,102,164,0],[15,10,10,0],0,125),
    'agility-hoppip-egg':(187,[150,235,39,97],[40,5,30,30],0,135),
    'scary-face-wooper-egg':(194,[55,39,184,0],[25,30,10,0],0,125),
    'dizzy-punch-elekid-egg':(239,[98,43,146,0],[30,30,10,0],0,125),
})
pcny_remaining=json.loads((ROOT/'tests/fixtures/butterflyos-gen2-pcny-recipes.json').read_text())
assert len(pcny_remaining)==95
assert len(g.PCNY_EGG_PRESETS)==104 and len(g.PCNY_SHINY_PRESETS)==16
assert len(ui.GEN2_PCNY_GIFTS)==120
remaining={r['preset']:r for r in pcny_remaining}
expected.update({r['preset']:(r['species'],r['moves'],r['pp'],0,r['experience']) for r in pcny_remaining})
assert len(g.EGG_PRESETS)==15 and len({recipe[0] for recipe in g.EGG_PRESETS.values()})==12
assert len(set(g.EGG_PRESETS.values()))==15
assert not set(g.PCNY_EGG_PRESETS.values()) & set(g.EGG_PRESETS.values()), "duplicate Mystery Egg recipe"
assert len(set(g.PCNY_EGG_PRESETS.values()))==len(g.PCNY_EGG_PRESETS)
assert set(expected)==set(g.PRESETS)=={x[0] for x in ui.GEN2_GIFTS+ui.STADIUM2_GIFTS+ui.GEN2_MYSTERY_EGGS+ui.GEN2_PCNY_GIFTS}
def rows(save):
    result=subprocess.run([str(helper),'inspect','--save',str(save)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    return [line for line in result.stdout.splitlines() if line.startswith('box_record\t')]
def refuse(data,rom,box=0,slot=0):
    try:g.prepare_gift(data,rom,'mew',box,slot)
    except ValueError:return
    raise AssertionError('unsafe input accepted')
cases=0;inputs={}
with tempfile.TemporaryDirectory(prefix='gen2-gifts-test-') as directory:
    scratch=Path(directory)
    for word in ('Gold','Silver','Crystal'):
        source=next((save_root/'gbc').glob('*'+word+'*'));rom=next(rom_root.glob('*'+word+' Version*'))
        data=source.read_bytes();inputs[source]=data;inputs[rom]=rom.read_bytes()
        crystal=word=='Crystal';current,active,owned,seen,end,cs,bcs=g.layout(crystal)
        old_rows=rows(source)
        for preset,(dex,moves,pp,item,exp) in ({} if ui_only else expected).items():
            if word=='Crystal' and preset=='celebi':
                try:g.prepare_gift(data,rom,preset,data[current],data[active])
                except ValueError as error:assert 'native Celebi quest' in str(error)
                else:raise AssertionError('Crystal bypassed the native Celebi quest')
                continue
            for box in range(14):
                at=active if box==data[current] else g.box_at(box);slot=data[at]
                result,metadata=g.prepare_gift(data,rom,preset,box,slot,[1,2,3,4])
                bank=g.box_at(box);record=result[bank+22+slot*32:bank+22+(slot+1)*32]
                assert record[0:6]==bytes((dex,item,*moves)) and record[6:8]==data[0x2009:0x200B]
                assert int.from_bytes(record[8:11],'big')==exp and record[11:21]==bytes(10)
                assert record[21:23]==(b'\xaa\xaa' if preset in g.PCNY_SHINY_PRESETS else b'\x12\x34') and record[23:27]==bytes(pp)
                egg=preset in g.EGG_PRESETS or preset in g.PCNY_EGG_PRESETS
                cycles={1:20,4:20,158:20,163:15,172:10,54:20,152:20,173:10,174:10,238:25,194:20,231:20,7:20,133:35,143:40,147:40,155:20,239:25,240:25,236:25,161:15,165:15,167:15,170:20,177:20,183:20,185:20,187:20}.get(dex)
                if preset in remaining:cycles=remaining[preset]['hatch_cycles']
                level=remaining[preset]['level'] if preset in remaining else 5
                assert metadata['level']==level
                assert metadata['is_egg']==egg
                assert record[27:32]==bytes((cycles if egg else 70,0,0,0,level))
                assert result[bank+1+slot]==(0xFD if egg else dex)
                if egg:
                    assert result[bank+882+slot*11:bank+882+(slot+1)*11]==bytes((0x84,0x86,0x86))+b'\x50'*8
                    for base in (owned,seen):
                        dest=base-0xE00 if crystal else base-0x288A+0x10E8
                        assert result[base:base+32]==data[base:base+32]
                        assert result[dest:dest+32]==data[dest:dest+32]
                assert result[bank]==slot+1 and result[bank+2+slot]==255
                assert result[bank+22:bank+22+slot*32]==data[at+22:at+22+slot*32]
                for names in (662,882):
                    assert result[bank+names:bank+names+slot*11]==data[at+names:at+names+slot*11]
                    assert result[bank+names+(slot+1)*11-1]==0x50
                if box==data[current]:assert result[active:active+g.BOX_SIZE]==result[bank:bank+g.BOX_SIZE]
                else:assert result[active:active+g.BOX_SIZE]==data[active:active+g.BOX_SIZE]
                allowed=set(range(bank,bank+g.BOX_SIZE))
                if box==data[current]:allowed.update(range(active,active+g.BOX_SIZE))
                allowed.update((cs,cs+1,bcs,bcs+1))
                for base in (() if egg else (owned,seen)):
                    offset=base+(dex-1)//8;dest=offset-0xE00 if crystal else offset-0x288A+0x10E8
                    allowed.update((offset,dest));assert result[offset]&(1<<((dex-1)%8))
                assert all(a==b or at in allowed for at,(a,b) in enumerate(zip(data,result))), 'unrelated data changed'
                out=scratch/'result.srm';out.write_bytes(result);after_rows=rows(out)
                assert set(old_rows)<=set(after_rows) and len(after_rows)==len(old_rows)+1
                added=next(line for line in after_rows if line not in old_rows)
                assert ('egg=yes' if egg else 'egg=no') in added
                if preset in g.PCNY_SHINY_PRESETS:assert added.split('\t')[6]=='yes'
                # Exercise native box switching/copy using the staged gift as source.
                copied=scratch/'copied.srm'
                command=[str(helper),'copy-gen2','--source',str(out),'--source-box',str(box),'--source-slot',str(slot),
                         '--destination',str(source),'--destination-box','0','--destination-slot',str(data[active]),'--output-destination',str(copied)]
                check=subprocess.run(command,capture_output=True,text=True);assert check.returncode==0,check.stderr
                copied_rows=rows(copied)
                assert len(copied_rows)==len(old_rows)+1
                if egg:
                    added_copy=next(line for line in copied_rows if line not in old_rows)
                    assert 'egg=yes' in added_copy
                cases+=1
        # Fill a box through its last slot; refusal must preserve that result.
        filled=data
        for slot in range(data[active],20):filled,_=g.prepare_gift(filled,rom,'mew',data[current],slot)
        refuse(filled,rom,data[current],19);refuse(data,rom,data[current],0)
        for box,slot in ((-1,0),(14,0),(0,-1),(0,20)):refuse(data,rom,box,slot)
        corrupt=bytearray(data);corrupt[0x2009]^=1;refuse(corrupt,rom)
        rtc=bytes(range(48));result,_=g.prepare_gift(data+rtc,rom,'mew',data[current],data[active]);assert result[0x8000:]==rtc
        other=next(rom_root.glob('*'+('Gold' if crystal else 'Crystal')+' Version*'));refuse(data,other,data[current],data[active])
        bad_rom=scratch/'bad.gbc';bad_rom.write_bytes(b'bad');refuse(data,bad_rom)
        # Output collision and a real protected prepare/Commit/backup/Cancel flow.
        save=scratch/(word+'.srm');save.write_bytes(data);out=scratch/'existing.srm';out.write_bytes(b'keep')
        command=[sys.executable,str(SOURCES/'butterflyos-gen2-gift.py'),'--save',str(save),'--rom',str(rom),
                 '--preset','mew','--box',str(data[current]),'--slot',str(data[active]),'--output',str(out)]
        assert subprocess.run(command,capture_output=True).returncode!=0 and out.read_bytes()==b'keep'
        real_run=subprocess.run
        def run(command,**kwargs):
            command=[str(SOURCES/'butterflyos-gen2-gift.py') if x=='/usr/bin/butterflyos-gen2-gift.py' else x for x in command]
            return real_run(command,**kwargs)
        with patch.object(ui,'subprocess') as proc,patch.object(ui,'new_session',side_effect=lambda:tempfile.mkdtemp(dir=scratch)):
            proc.run.side_effect=run
            session,message=ui.prepare_gen2_gift((str(save),data[current],data[active]),str(rom),'mew');assert session,message
            assert save.read_bytes()==data
            ok,message=ui.commit_copy(session);assert ok,message
            assert (Path(session)/'original-destination-backup').read_bytes()==data
            assert ui.commit_copy(session)[0] is False
        save.write_bytes(data)
        cache=scratch/'cache';cache.mkdir(exist_ok=True)
        (cache/'manifest.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest()}))
        for eggs,pcny,key,selections in ((False,False,ui.KEY_ESCAPE,[0]),(False,False,ui.KEY_RETURN,[0,0]),(True,False,ui.KEY_ESCAPE,[0]),(True,False,ui.KEY_RETURN,[0,0]),(False,True,ui.KEY_ESCAPE,[0,0]),(False,True,ui.KEY_RETURN,[0,0,0]),(False,True,ui.KEY_ESCAPE,[1,0]),(False,True,ui.KEY_RETURN,[1,0,0])):
            sessions=[]
            def new_session():
                result=tempfile.mkdtemp(dir=scratch);sessions.append(result);return result
            class Frontend:
                def draw_sprite_browser(self,*args):
                    assert args[0]==("EGG HATCHLING PREVIEW" if eggs or (pcny and selections[0]==0) else "GENERATED GIFT PREVIEW")
                def next_key(self):return key
            with ExitStack() as stack:
                proc=stack.enter_context(patch.object(ui,'subprocess'));proc.run.side_effect=run
                stack.enter_context(patch.object(ui,'new_session',side_effect=new_session))
                for name,value in {'notice':lambda *a,**k:None,
                    'choose_save':lambda *a:(str(save),'PLAYER',word,[]),
                    'ensure_sprite_cache':lambda *a:str(cache),
                    '_rom_candidates':lambda *a:[str(rom)],
                    'choose_copy_destination':lambda *a:(data[current],data[active]),
                    'save_metadata':lambda *a:(2,'PLAYER',word,[{'box':data[current],'slot':data[active],'species':151}]),
                    '_enrich_rom_names':lambda *a:None,'_read_cache_png':lambda *a:None}.items():
                    stack.enter_context(patch.object(ui,name,value))
                choices=stack.enter_context(patch.object(ui,'choose_list',side_effect=selections))
                commit=stack.enter_context(patch.object(ui,'commit_copy'))
                ui.gen2_gift_workflow(Frontend(),eggs=eggs,pcny=pcny);commit.assert_not_called()
                if pcny:
                    categories=choices.call_args_list[0][0][3]
                    assert [label for label,description in categories]==['SPECIAL-MOVE EGGS','SHINY ADULT GIFTS']
                    gift_rows=choices.call_args_list[1][0][3]
                    selected=selections[0]
                    assert len(gift_rows)==(104 if selected==0 else 16)
                    assert all(('EGG' in label) if selected==0 else label.startswith('SHINY ') for label,description in gift_rows)
                if not eggs and not pcny:
                    labels=[item[0] for item in choices.call_args_list[0][0][3]]
                    assert ('CELEBI' in labels)==(word!='Crystal')
            assert sessions and not Path(sessions[0]).exists() and save.read_bytes()==data
    with patch.object(ui,'choose_list',return_value=None),patch.object(ui,'choose_save') as destination,patch.object(ui,'prepare_gen2_gift') as prepare:
        ui.gen2_gift_workflow(None,pcny=True)
        destination.assert_not_called();prepare.assert_not_called()
    saves=[('Crystal.srm','PLAYER','Crystal',[])]
    for index,handler,kwargs in ((1,'gen2_gift_workflow',{'stadium':False}),
                                 (2,'gen2_gift_workflow',{'stadium':True}),
                                 (3,'crystal_event_workflow',{}),
                                 (4,'gen2_gift_workflow',{'eggs':True}),
                                 (5,'gen2_gift_workflow',{'pcny':True})):
        with patch.object(ui,'generation_saves',return_value=saves),patch.object(ui,'choose_list',side_effect=[index,None]),patch.object(ui,handler) as route:
            assert ui.choose_gen2_local_save(None) is None;route.assert_called_once_with(None,**kwargs)
    # Native DV shininess is visible in the UI; eggs remain blocked as transfer sources.
    original=next((save_root/'gbc').glob('*Crystal*')).read_bytes()
    rom=next(rom_root.glob('*Crystal Version*'))
    current,active,*_=g.layout(True)
    out=scratch/'shiny-egg.srm'
    for attack in range(16):
        result,_=g.prepare_gift(original,rom,'sing-pichu-egg',original[current],original[active],[attack,10,10,10])
        out.write_bytes(result)
        native=rows(out)
        new=next(line for line in native if line not in rows(next((save_root/'gbc').glob('*Crystal*'))))
        columns=new.split('\t')[1:]
        parsed=ui._record_from_columns('box',original[current],original[active],172,'EGG',columns)
        assert parsed['egg'] and parsed['shiny']==bool(attack&2)
    destination=next((save_root/'gba').glob('*Emerald*.srm'))
    destination_bytes=destination.read_bytes()
    refused=scratch/'egg-to-gen3.srm'
    check=subprocess.run([str(helper),'copy-gen2-to-gen3','--source',str(out),
        '--source-box',str(original[current]),'--source-slot',str(original[active]),
        '--national-species','172','--destination',str(destination),'--destination-box','0',
        '--destination-slot','0','--output-destination',str(refused)],capture_output=True,text=True)
    assert check.returncode!=0 and 'hatch-gen2-egg-before-gen3-transfer' in check.stderr,check.stderr
    assert destination.read_bytes()==destination_bytes and not refused.exists()
    keys=iter((ui.KEY_RETURN,ui.KEY_ESCAPE))
    class EggFrontend:
        def draw_sprite_browser(self,*args):pass
        def next_key(self):return next(keys)
    with patch.object(ui,'choose_box',return_value=0),patch.object(ui,'_enrich_rom_names'),patch.object(ui,'notice') as note:
        assert ui.choose_record(EggFrontend(),'TEST',('test.srm','PLAYER','Crystal',[dict(parsed,box=0)]),None) is None
        assert note.call_count==1 and note.call_args[0][1]=='HATCH THE EGG FIRST'
for path,data in inputs.items():assert path.read_bytes()==data
if ui_only:
    print('PASS: focused Gold/Silver/Crystal workflow checks, egg/adult categories and previews, safe cancellation, protected Commit/backup and menu routes; originals unchanged')
else:
    print('PASS: %d gift/family/box cases plus native box copy/reload, full/occupied refusal, RTC, checksums, ROM/family qualification, preparation/Commit/backup/conflict/Cancel and menu routes; originals unchanged'%cases)

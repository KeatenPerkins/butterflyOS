#!/usr/bin/env python3
"""Native island-event qualification on disposable copies of private fixtures.

Usage: test.py PUBLIC_SAVE_ROOT ROM_AND_FIRERED_SAVE_ROOT NATIVE_HELPER
No source ROM or save is changed. Synthetic flags exist only in temporary files.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT/'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'

def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,SOURCES/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

e=load('island_events_test','butterflyos-gen3-event.py')
u=load('island_ui_test','butterflyos-save-trade-sdl.py')
public,assets,helper=map(Path,sys.argv[1:4]);del sys.argv[1:4]
FIXTURES=[('Emerald',public/'extracted/emerald-389hours/original.sav',assets/'Pokemon - Emerald Version - Bdex Gen3 Test.gba'),
          ('FireRed',assets/'Pokemon - FireRed Version - Bdex Gen3 Test.srm',assets/'Pokemon - FireRed Version - Bdex Gen3 Test.gba'),
          ('LeafGreen',public/'extracted/leafgreen-postgame/original.sav',assets/'Pokemon - LeafGreen Version - Bdex Gen3 Test.gba')]
ORIGINALS={p:hashlib.sha256(p.read_bytes()).hexdigest() for _,save,rom in FIXTURES for p in (save,rom)}


def fixture(data,rom,rotation=0,finished=False):
    ctx=e.load_save(data,rom)
    for rule in e.RULES[ctx['family']].values():
        for number in (rule['travel'],rule['shown'],*rule['completed'],*rule['clear'],*rule['show'],*rule['hide']):e.set_flag(ctx,number,False)
        if rule['received'] is not None:e.set_flag(ctx,rule['received'],False)
        if finished:
            for number in (*rule['completed'],*rule['clear'],*rule['show'],rule['shown']):e.set_flag(ctx,number,True)
            for number in rule['variables']:struct.pack_into('<H',ctx['block'],ctx['vars_at']+(number-0x4000)*2,17)
    emerald=ctx['family']=='Emerald'
    e.set_flag(ctx,0x864 if emerald else 0x82C,True)
    e.set_flag(ctx,0x123 if emerald else 0x840,True)
    if not emerald:struct.pack_into('<H',ctx['block'],ctx['vars_at']+(0x4076-0x4000)*2,5)
    ctx['block'][4:6]=bytes((3,0))
    for n in range(30):struct.pack_into('<HH',ctx['block'],ctx['pocket_at']+4*n,0,ctx['key'])
    struct.pack_into('<HH',ctx['block'],ctx['pocket_at'],265,ctx['key']^1)
    out=bytearray(data)
    for base,count in ((0,100),(0xE000,101)):
        cursor=0
        for n,size in enumerate(ctx['sizes']):
            payload=data[ctx['sections'][n]:ctx['sections'][n]+size]
            if 1<=n<=4:
                payload=ctx['block'][cursor:cursor+size];cursor+=size
            off=base+((n+rotation)%14)*4096
            out[off:off+4096]=bytes([0xAB])*4096
            out[off:off+size]=payload
            struct.pack_into('<HHII',out,off+0xFF4,n,e.gift.checksum(payload),0x08012025,count)
    return bytes(out)


def write_block(data,ctx):
    result=bytearray(data);cursor=0
    for n in range(1,5):
        off,size=ctx['sections'][n],ctx['sizes'][n];payload=ctx['block'][cursor:cursor+size];cursor+=size
        result[off:off+size]=payload;struct.pack_into('<H',result,off+0xFF6,e.gift.checksum(payload))
    return bytes(result)


class IslandTests(unittest.TestCase):
    def tearDown(self):
        for p,digest in ORIGINALS.items():self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),digest)

    def assert_boundaries(self,before,after,ctx,event,action):
        masks={}
        def allowed_block(at,mask=255):
            cursor=0
            for n in range(1,5):
                size=ctx['sizes'][n]
                if cursor<=at<cursor+size:
                    absolute=ctx['sections'][n]+at-cursor;masks[absolute]=masks.get(absolute,0)|mask;return
                cursor+=size
            self.fail('Bad logical offset')
        rule=e.RULES[ctx['family']][event]
        flags=[rule['travel']]+([rule['received']] if rule['received'] is not None else [])
        if action=='replay':flags+=list((*rule['completed'],*rule['clear'],*rule['show'],*rule['hide'],rule['shown']))
        for number in flags:allowed_block(ctx['flags_at']+number//8,1<<(number%8))
        if e.EVENTS[event]['item'] not in ctx['items']:
            for n in range(30):
                at=ctx['pocket_at']+4*n
                if struct.unpack_from('<H',ctx['block'],at)[0]==0:
                    for i in range(4):allowed_block(at+i)
                    break
        if action=='replay':
            for number in rule['variables']:
                at=ctx['vars_at']+(number-0x4000)*2;allowed_block(at);allowed_block(at+1)
        for n in range(1,5):
            for off in (0xFF6,0xFF7):masks[ctx['sections'][n]+off]=255
        changes=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        self.assertTrue(changes)
        for i in changes:self.assertEqual((before[i]^after[i])&~masks.get(i,0),0,'Unexpected change at '+hex(i))

    def test_all_rotations_enable_replay_and_native_reader(self):
        count=0
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'prepared.sav'
            for label,save,rom in FIXTURES:
                original=save.read_bytes();family=e.load_save(original,rom)['family']
                for rotation in range(14):
                    for action in ('enable','replay'):
                        data=fixture(original,rom,rotation,finished=action=='replay')
                        for event in e.RULES[family]:
                            with self.subTest(game=label,rotation=rotation,action=action,event=event):
                                ctx=e.load_save(data,rom);new,before=e.prepare_event(data,rom,action,event)
                                self.assert_boundaries(data,new,ctx,event,action)
                                state=e.inspect_event(new,rom,event)
                                self.assertTrue(state['has_ticket'] and state['travel']);self.assertFalse(any(state['completed'].values()))
                                output.write_bytes(new)
                                result=subprocess.run([str(helper),'inspect','--save',str(output)],capture_output=True,text=True)
                                self.assertEqual(result.returncode,0,result.stderr)
                                count+=1
        print('Validated',count,'game/event/rotation/action combinations')

    def test_story_map_full_pocket_finished_and_corrupt_refusal(self):
        for label,save,rom in FIXTURES:
            original=save.read_bytes();data=fixture(original,rom);family=e.load_save(data,rom)['family']
            for event in e.RULES[family]:
                for case in ('story','island','full','finished','corrupt'):
                    with self.subTest(game=label,event=event,case=case):
                        ctx=e.load_save(data,rom)
                        if case=='story':e.set_flag(ctx,0x864 if family=='Emerald' else 0x82C,False)
                        if case=='island':ctx['block'][4:6]=bytes((26,58) if family=='Emerald' else (2,56))
                        if case=='full':
                            for n in range(30):struct.pack_into('<HH',ctx['block'],ctx['pocket_at']+4*n,300+n,ctx['key']^1)
                        if case=='finished':e.set_flag(ctx,e.RULES[family][event]['completed'][0],True)
                        modified=bytearray(write_block(data,ctx))
                        if case=='corrupt':modified[ctx['sections'][1]+100]^=1
                        with self.assertRaises(ValueError):e.prepare_event(modified,rom,'enable',event)

    def test_already_enabled_and_existing_ticket(self):
        for label,save,rom in FIXTURES:
            data=fixture(save.read_bytes(),rom);ctx=e.load_save(data,rom)
            for event,rule in e.RULES[ctx['family']].items():
                prepared,_=e.prepare_event(data,rom,'enable',event)
                with self.assertRaises(ValueError):e.prepare_event(prepared,rom,'enable',event)
                existing=e.load_save(prepared,rom);e.set_flag(existing,rule['travel'],False)
                restored,_=e.prepare_event(write_block(prepared,existing),rom,'enable',event)
                self.assertEqual(e.load_save(restored,rom)['items'].count(e.EVENTS[event]['item']),1)

    def test_wrong_rom_and_cross_family_refusal(self):
        with tempfile.TemporaryDirectory() as folder:
            wrong=Path(folder)/'wrong.gba';wrong.write_bytes(b'not a supported ROM')
            with self.assertRaises(ValueError):e.inspect_event(FIXTURES[0][1].read_bytes(),wrong)
        with self.assertRaises(ValueError):e.inspect_event(FIXTURES[0][1].read_bytes(),FIXTURES[2][2])
        with self.assertRaises(ValueError):e.inspect_event(FIXTURES[2][1].read_bytes(),FIXTURES[0][2])
        with self.assertRaises(ValueError):e.inspect_event(FIXTURES[2][1].read_bytes(),FIXTURES[2][2],'old-sea-map')

    def test_existing_roamer_data_untouched(self):
        _,save,rom=FIXTURES[0];data=fixture(save.read_bytes(),rom,finished=True);ctx=e.load_save(data,rom)
        # In addition to exact change masks, assert the independent roamer choice
        # and roaming flag are not reset by Southern Island replay.
        e.set_flag(ctx,0xFF,True)
        struct.pack_into('<H',ctx['block'],ctx['vars_at']+(0x40D5-0x4000)*2,1)
        data=write_block(data,ctx);new,_=e.prepare_event(data,rom,'replay','eon-ticket');after=e.load_save(new,rom)
        self.assertTrue(e.flag(after,0xFF));self.assertEqual(e.variable(after,0x40D5),1)

    def test_cli_exclusive_output_and_real_prepare_backup_commit(self):
        _,save,rom=FIXTURES[0]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);original=fixture(save.read_bytes(),rom);working=root/'test.srm';working.write_bytes(original)
            output=root/'prepared.srm'
            args=[sys.executable,str(SOURCES/'butterflyos-gen3-event.py'),'--save',str(working),'--rom',str(rom),'--event','aurora-ticket','--action','enable','--output',str(output)]
            self.assertEqual(subprocess.run(args,capture_output=True).returncode,0)
            self.assertNotEqual(subprocess.run(args,capture_output=True).returncode,0)
            self.assertEqual(working.read_bytes(),original)
            real_run=subprocess.run
            def local_run(command,**kwargs):
                command=list(command)
                if command[1]=='/usr/bin/butterflyos-gen3-event.py':command[1]=str(SOURCES/'butterflyos-gen3-event.py')
                return real_run(command,**kwargs)
            with patch.object(u,'STATE_ROOT',str(root/'sessions')),patch.object(u.subprocess,'run',side_effect=local_run),patch.object(u.os,'sync'):
                session,_=u.prepare_save_event(str(working),str(rom),'enable','butterflyos-gen3-event.py',('--event','aurora-ticket'))
                self.assertIsNotNone(session)
                self.assertEqual(working.read_bytes(),original) # Cancel leaves the original intact.
                working.write_bytes(b'changed')
                self.assertFalse(u.commit_copy(session)[0]);working.write_bytes(original)
                ok,message=u.commit_copy(session);self.assertTrue(ok,message)
                self.assertEqual((Path(session)/'original-destination-backup').read_bytes(),original)
                self.assertTrue(e.inspect_event(working.read_bytes(),rom)['travel'])
                self.assertFalse(u.commit_copy(session)[0])

    def test_zip_rom_and_counter_rollover(self):
        import zipfile
        _,save,rom=FIXTURES[0];data=fixture(save.read_bytes(),rom)
        with tempfile.TemporaryDirectory() as folder:
            zipped=Path(folder)/'Emerald.zip'
            with zipfile.ZipFile(zipped,'w') as archive:archive.write(rom,'Emerald.gba')
            self.assertEqual(e.prepare_event(data,zipped,'enable','eon-ticket')[0],e.prepare_event(data,rom,'enable','eon-ticket')[0])
        rotated=bytearray(data)
        for base,count in ((0,0xFFFFFFFF),(0xE000,0)):
            for i in range(14):struct.pack_into('<I',rotated,base+i*4096+0xFFC,count)
        prepared,_=e.prepare_event(rotated,rom,'enable','eon-ticket')
        self.assertEqual(prepared[:0xE000],rotated[:0xE000])
        self.assertTrue(e.inspect_event(prepared,rom,'eon-ticket')['travel'])

    def test_actual_ui_cancel_and_commit_each_emerald_event(self):
        _,save,rom=FIXTURES[0]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);working=root/'test.srm';original=fixture(save.read_bytes(),rom)
            for index,event in enumerate(e.RULES['Emerald']):
                for commit in (False,True):
                    with self.subTest(event=event,commit=commit):
                        working.write_bytes(original)
                        with patch.object(u,'STATE_ROOT',str(root/'state')),patch.object(u,'GEN3_EVENT_TOOL',str(SOURCES/'butterflyos-gen3-event.py')),patch.object(u,'generation_saves',return_value=[(str(working),'TEST','Emerald',[])]),patch.object(u,'_rom_candidates',return_value=[str(rom)]),patch.object(u,'choose_list',side_effect=[0,index,0,int(commit)]),patch.object(u,'notice') as notice,patch.object(u,'save_event_game_running',return_value=False),patch.object(u.os,'sync'):
                            u.gen3_event_workflow(None)
                        if commit:
                            self.assertTrue(e.inspect_event(working.read_bytes(),rom,event)['travel'])
                            self.assertEqual(notice.call_args.args[1],'ISLAND EVENT READY')
                        else:self.assertEqual(working.read_bytes(),original)

    def test_event_menu_available_without_development_marker(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(u,'STATE_ROOT',folder),patch.object(u,'generation_saves',return_value=[]),patch.object(u,'choose_list',side_effect=[6,None]) as choose,patch.object(u,'gen3_event_workflow') as workflow:
            self.assertIsNone(u.choose_gen3_local_save(None))
            workflow.assert_called_once_with(None)
            self.assertEqual(choose.call_args_list[0].args[3][6][0],'GEN 3 ISLAND EVENTS')

if __name__=='__main__':unittest.main()

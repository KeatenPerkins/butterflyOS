#!/usr/bin/env python3
"""Private-fixture quest tests; no input ROM/save is modified or bundled.
Usage: python3 tests/butterflyos-crystal-event-test.py HELPER SAVE ROM
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SOURCES / filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

event = load('event', 'butterflyos-crystal-event.py')
ui = load('ui', 'butterflyos-save-trade-sdl.py')
helper, source, rom = map(Path, sys.argv[1:])
original = source.read_bytes(); rom_hash = hashlib.sha256(rom.read_bytes()).hexdigest()

def sync(data):
    data[0x1209:0x1D83] = data[0x2009:0x2B83]
    checksum = (sum(data[0x2009:0x2B83]) & 65535).to_bytes(2, 'little')
    data[0x2D0D:0x2D0F] = data[0x1F0D:0x1F0F] = checksum
    return bytes(data)

def fixture(stage):
    d = bytearray(original)
    for number in event.EVENTS.values(): event.set_flag(d, number, False)
    for number in range(600, 607): event.set_flag(d, number, False)
    d[0x27AC] &= ~1; d[0x2781] &= ~4
    d[0x251E] = 1  # The unrelated rival scene must survive replay.
    d[0x2521] = 0; d[0x2843:0x2845] = bytes((26, 5))
    d[0x244A:0x244E] = bytes((2, 7, 0x3A, 0xFF))
    d[0x3E3C] = d[0x3E44] = 0
    if stage != 'new': d[0x3E3C] = d[0x3E44] = 11
    if stage not in ('new', 'available'): event.set_flag(d, 832, True)
    if stage == 'delivered':
        event.set_flag(d, 190, True); d[0x244A:0x244F] = bytes((3, 7, 0x73, 0x3A, 0xFF))
    if stage == 'examining':
        event.set_flag(d, 190, True); event.set_flag(d, 191, True); d[0x27AC] |= 1
    if stage in ('returned', 'shrine'):
        event.set_flag(d, 192, True)
    if stage == 'shrine':
        d[0x2781] |= 4; d[0x244A:0x244F] = bytes((3, 7, 0x73, 0x3A, 0xFF))
    if stage == 'caught':
        # A caught Celebi's Pokedex bits and all existing Pokemon must remain.
        d[0x2A27 + 250 // 8] |= 1 << (250 % 8)
        d[0x2A47 + 250 // 8] |= 1 << (250 % 8)
    return sync(d)

def reject(data, action='replay'):
    try: event.prepare_event(data, rom, action)
    except ValueError: return
    raise AssertionError('unsafe state accepted')

checked = 0
with tempfile.TemporaryDirectory(prefix='butterfly-celebi-test-') as directory:
    scratch = Path(directory)
    for stage in ('new', 'available', 'delivered', 'examining', 'returned', 'shrine', 'finished', 'caught'):
        data = fixture(stage)
        for action in ('enable', 'replay'):
            if action == 'enable' and stage != 'new': reject(data, action); checked += 1; continue
            result, before = event.prepare_event(data, rom, action)
            status = event.inspect_event(result, rom)
            assert status['stage'] == 'GS Ball delivery enabled' and not status['has_gs_ball']
            assert result[0x3E3C] == result[0x3E44] == 11
            assert result[0x251E] == 1  # Do not restart the rival battle.
            assert result[0x244A:0x244E] == bytes((2, 7, 0x3A, 0xFF))
            for start, end in ((0x2865, 0x2B83), (0x2D10, 0x3160), (0x4000, 0x8000)):
                assert result[start:end] == data[start:end], 'Pokemon/PC data changed'
            before_save = scratch/'before.srm'; after_save = scratch/'after.srm'
            before_save.write_bytes(data); after_save.write_bytes(result)
            before_rows = subprocess.check_output([str(helper), 'inspect', '--save', str(before_save)], text=True)
            after_rows = subprocess.check_output([str(helper), 'inspect', '--save', str(after_save)], text=True)
            assert [l for l in before_rows.splitlines() if 'record\t' in l] == [l for l in after_rows.splitlines() if 'record\t' in l]
            # Every changed byte belongs to a specifically allowed field/mirror/checksum.
            allowed = {0x3E3C, 0x3E44, 0x2D0D, 0x2D0E, 0x1F0D, 0x1F0E}
            fields = {0x2781, 0x27AC, 0x251E, 0x244A, 0x244B, 0x244C, 0x244D}
            fields |= {event.EVENT_BASE + event.EVENTS[k]//8 for k in ('received','can_give','gave','restless','kurt_outside','gate_lass','forest_lass')}
            allowed |= fields | {at - 0xE00 for at in fields}
            assert all(a == b or at in allowed for at,(a,b) in enumerate(zip(data,result)))
            checked += 1
    for number in range(600, 607):
        d=bytearray(fixture('finished')); event.set_flag(d,number,True); reject(sync(d)); checked+=1
    d=bytearray(fixture('new'));d[0x27AC]|=1;reject(sync(d));checked+=1
    for group,number in event.QUEST_MAPS:
        d=bytearray(fixture('new'));d[0x2843:0x2845]=bytes((group,number));reject(sync(d),'enable');checked+=1
    d=bytearray(fixture('new'));d[0x2009]^=1;reject(bytes(d));checked+=1
    d=bytearray(fixture('new'));d[0x244A]=25;d[0x244B:0x2465]=bytes(range(1,26))+b'\xff';reject(sync(d),'enable');checked+=1
    d=bytearray(fixture('new'));d[0x2521]=1
    for action in ('enable','replay'): reject(sync(d),action);checked+=1
    d=bytearray(fixture('examining'));d[0x251E]=2
    result,_=event.prepare_event(sync(d),rom,'replay');assert result[0x251E]==0
    rtc=bytes(range(48));result,_=event.prepare_event(fixture('new')+rtc,rom,'enable');assert result[0x8000:]==rtc
    wrong_rom=scratch/'wrong.gbc';wrong_rom.write_bytes(b'unsupported')
    try: event.prepare_event(fixture('new'),wrong_rom,'enable')
    except ValueError: pass
    else: raise AssertionError('wrong ROM accepted')
    data=fixture('finished');save=scratch/'Crystal.srm';save.write_bytes(data)
    out=scratch/'output.srm';out.write_bytes(b'keep')
    command=[sys.executable,str(SOURCES/'butterflyos-crystal-event.py'),'--save',str(save),'--rom',str(rom),'--action','replay','--output',str(out)]
    assert subprocess.run(command,capture_output=True).returncode!=0 and out.read_bytes()==b'keep'
    # Real preparation/Commit functions with installed paths redirected to source.
    real_run=subprocess.run
    def run(command, **kwargs):
        command=[str(SOURCES/'butterflyos-crystal-event.py') if x=='/usr/bin/butterflyos-crystal-event.py' else x for x in command]
        return real_run(command,**kwargs)
    with patch.object(ui,'subprocess') as processes, patch.object(ui,'new_session',side_effect=lambda: tempfile.mkdtemp(dir=scratch)):
        processes.run.side_effect=run
        session,message=ui.prepare_crystal_event(str(save),str(rom),'replay');assert session,message
        assert save.read_bytes()==data
        expected=Path(ui.session_output(session)).read_bytes()
        ok,message=ui.commit_copy(session);assert ok,message
        assert save.read_bytes()==expected and (Path(session)/'original-destination-backup').read_bytes()==data
    assert ui.commit_copy(session)[0] is False  # Original fingerprint now differs.
    # Cancel from the actual UI must remove its staging output, never the save.
    save.write_bytes(fixture('new')); untouched=save.read_bytes(); sessions=[]
    def new_session():
        result=tempfile.mkdtemp(dir=scratch);sessions.append(result);return result
    with patch.object(ui,'subprocess') as processes, patch.object(ui,'new_session',side_effect=new_session), \
         patch.object(ui,'generation_saves',return_value=[(str(save),'TEST','Crystal',[])]), \
         patch.object(ui,'_rom_candidates',return_value=[str(rom)]), \
         patch.object(ui,'notice'), patch.object(ui,'choose_list',side_effect=[0,0,0,0]):
        processes.run.side_effect=run
        ui.crystal_event_workflow(None)
    assert save.read_bytes()==untouched and sessions and not Path(sessions[0]).exists()
    # Odd Egg replay changes exactly one event bit, its mirror and checksums.
    for stage in ('new','available','delivered','examining','returned','shrine','finished','caught'):
        for neighbors in (0,0x3F,0xBF):
            d=bytearray(fixture(stage));d[event.DAYCARE_MAN]&=~event.DAYCARE_HAS_EGG
            at=event.EVENT_BASE+event.ODD_EGG_EVENT//8
            d[at]=neighbors;event.set_flag(d,event.ODD_EGG_EVENT,True)
            data=sync(d);result,before=event.prepare_odd_egg(data,rom)
            assert before['received'] and not event.inspect_odd_egg(result,rom)['received']
            assert result[at]==neighbors and result[at-0xE00]==neighbors
            allowed={at,at-0xE00,0x2D0D,0x2D0E,0x1F0D,0x1F0E}
            assert all(a==b or index in allowed for index,(a,b) in enumerate(zip(data,result)))
            assert event.inspect_event(result,rom)==event.inspect_event(data,rom)
            before_save=scratch/'odd-before.srm';after_save=scratch/'odd-after.srm'
            before_save.write_bytes(data);after_save.write_bytes(result)
            old=subprocess.check_output([str(helper),'inspect','--save',str(before_save)],text=True)
            new=subprocess.check_output([str(helper),'inspect','--save',str(after_save)],text=True)
            assert [l for l in old.splitlines() if 'record\t' in l]==[l for l in new.splitlines() if 'record\t' in l]
            try:event.prepare_odd_egg(result,rom)
            except ValueError as error:assert 'already available' in str(error)
            else:raise AssertionError('already available Odd Egg was rearmed')
    d=bytearray(fixture('caught'));event.set_flag(d,event.ODD_EGG_EVENT,True)
    d[event.DAYCARE_MAN]|=event.DAYCARE_HAS_EGG
    try:event.prepare_odd_egg(sync(d),rom)
    except ValueError as error:assert 'breeding egg' in str(error)
    else:raise AssertionError('pending breeding egg accepted')
    d[event.DAYCARE_MAN]&=~event.DAYCARE_HAS_EGG;data=sync(d)
    rtc=bytes(range(48));result,_=event.prepare_odd_egg(data+rtc,rom);assert result[0x8000:]==rtc
    bad=bytearray(data);bad[0x1209]^=1
    for invalid in (bytes(bad),data[:-1]):
        try:event.prepare_odd_egg(invalid,rom)
        except ValueError:pass
        else:raise AssertionError('invalid Odd Egg save accepted')
    # Protected commit and cancellation through the real submenu/workflow.
    save.write_bytes(data)
    with patch.object(ui,'subprocess') as processes,patch.object(ui,'new_session',side_effect=lambda:tempfile.mkdtemp(dir=scratch)):
        processes.run.side_effect=run
        session,message=ui.prepare_crystal_event(str(save),str(rom),'odd-egg-replay');assert session,message
        assert save.read_bytes()==data
        ok,message=ui.commit_copy(session);assert ok,message
        assert (Path(session)/'original-destination-backup').read_bytes()==data
        assert not ui.commit_copy(session)[0]
    save.write_bytes(data);sessions=[]
    with patch.object(ui,'subprocess') as processes,patch.object(ui,'new_session',side_effect=new_session), \
         patch.object(ui,'generation_saves',return_value=[(str(save),'TEST','Crystal',[])]), \
         patch.object(ui,'_rom_candidates',return_value=[str(rom)]), \
         patch.object(ui,'notice'),patch.object(ui,'choose_list',side_effect=[1,0,0]):
        processes.run.side_effect=run
        ui.crystal_event_workflow(None)
    assert save.read_bytes()==data and sessions and not Path(sessions[0]).exists()
assert source.read_bytes()==original and hashlib.sha256(rom.read_bytes()).hexdigest()==rom_hash
print('PASS: 24 Odd Egg replay/preservation cases plus breeding-egg/refusal, native reload, Commit/backup/Cancel; %d Celebi quest-state/refusal cases, RTC preservation, ROM qualification, exact change boundaries, native reload, output protection, prepare/Commit/backup/conflict/Cancel; originals unchanged' % checked)

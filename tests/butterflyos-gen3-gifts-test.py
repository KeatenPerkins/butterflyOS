#!/usr/bin/env python3
"""Private-fixture egg checks; never change the supplied save or ROM.

Usage: test.py SOURCE_DIR ROM SAVE NATIVE_HELPER
"""
import importlib.util
import itertools
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sources, rom_path, save_path, helper = map(Path, sys.argv[1:5])
del sys.argv[1:5]
spec = importlib.util.spec_from_file_location('gift', sources/'butterflyos-gen3-gift.py')
gift = importlib.util.module_from_spec(spec);spec.loader.exec_module(gift)
ROM = gift.read_rom(rom_path)
SAVE = save_path.read_bytes()
SECTIONS = gift.active_sections(SAVE)
PC = b''.join(SAVE[SECTIONS[n]:SECTIONS[n]+gift.SIZES[n]] for n in range(5,14))
FREE = next(i for i in range(420) if PC[4+i*80:4+(i+1)*80] == bytes(80))
BOX, SLOT = divmod(FREE,30)


class Eggs(unittest.TestCase):
    def test_four_recipes_all_24_record_orders(self):
        for preset,(national,moves) in gift.PRESETS.items():
            for pid in range(24):
                with self.subTest(preset=preset,pid=pid), patch.object(gift.secrets,'randbits',side_effect=[pid,0x1234567]):
                    result,meta=gift.prepare(SAVE,ROM,preset,BOX,SLOT)
                    pc=b''.join(result[SECTIONS[n]:SECTIONS[n]+gift.SIZES[n]] for n in range(5,14))
                    at=4+FREE*80;record=pc[at:at+80]
                    key=pid ^ struct.unpack_from('<I',record,4)[0]
                    plain=b''.join(struct.pack('<I',n^key) for n in struct.unpack('<12I',record[32:]))
                    order=list(itertools.permutations(range(4)))[pid%24]
                    blocks={kind:plain[i*12:(i+1)*12] for i,kind in enumerate(order)}
                    self.assertEqual(struct.unpack_from('<H',blocks[0])[0],meta['species'])
                    self.assertEqual(struct.unpack_from('<H',blocks[0],2)[0],0)
                    self.assertEqual(struct.unpack('<4H',blocks[1][:8]),moves)
                    self.assertEqual(record[19]&6,6)
                    self.assertEqual((struct.unpack_from('<I',blocks[3],4)[0]>>30)&1,1)
                    self.assertEqual(struct.unpack_from('<H',record,28)[0],sum(struct.unpack('<24H',plain))&0xffff)
                    self.assertEqual(pc[:at],PC[:at]);self.assertEqual(pc[at+80:],PC[at+80:])
                    # Only the selected record and its section checksums may differ.
                    allowed=set()
                    for i in range(at,at+80):allowed.add(SECTIONS[5+i//0xF80]+i%0xF80)
                    for n in range(5,14):allowed.update((SECTIONS[n]+0xFF6,SECTIONS[n]+0xFF7))
                    self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(SAVE,result)) if a!=b))
                    gift.active_sections(result)
                    with tempfile.TemporaryDirectory() as directory:
                        p=Path(directory)/'egg.srm';p.write_bytes(result)
                        inspected=subprocess.run([str(helper),'inspect','--save',str(p)],capture_output=True,text=True)
                        self.assertEqual(inspected.returncode,0,inspected.stderr)
                        line=next(l for l in inspected.stdout.splitlines() if l.startswith('box_record\t%d\t%d\t'%(BOX,SLOT)))
                        self.assertIn('moves='+','.join(map(str,moves)),line)

    def test_record_crossing_sector_boundary(self):
        # Slot 49 begins 44 bytes before a PC-sector boundary.
        pc=bytearray(PC);at=4+49*80;pc[at:at+80]=bytes(80)
        baseline=bytearray(SAVE);cursor=0
        for n in range(5,14):
            offset,size=SECTIONS[n],gift.SIZES[n]
            baseline[offset:offset+size]=pc[cursor:cursor+size];cursor+=size
            struct.pack_into('<H',baseline,offset+0xFF6,gift.checksum(baseline[offset:offset+size]))
        result,_=gift.prepare(bytes(baseline),ROM,'surf-pichu-egg',1,19)
        gift.active_sections(result)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'crossing.srm';p.write_bytes(result)
            inspected=subprocess.run([str(helper),'inspect','--save',str(p)],capture_output=True,text=True)
            self.assertEqual(inspected.returncode,0,inspected.stderr)
            line=next(l for l in inspected.stdout.splitlines() if l.startswith('box_record\t1\t19\t'))
            self.assertIn('moves=84,204,57,0',line)

    def test_protected_ui_flow_and_zip_cache_match(self):
        spec=importlib.util.spec_from_file_location('ui',sources/'butterflyos-save-trade-sdl.py')
        ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui)
        self.assertEqual(ui.rom_cache_digest(3,str(rom_path)),gift.ROM_SHA256)
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory);ui.STATE_ROOT=str(d/'sessions');save=d/'test.srm'
            for scenario in ('cancel','commit','changed'):
                save.write_bytes(SAVE)
                session,message=ui.prepare_gen3_gift((str(save),BOX,SLOT),str(rom_path),'surf-pichu-egg')
                self.assertTrue(session,message);self.assertEqual(save.read_bytes(),SAVE)
                if scenario=='cancel':__import__('shutil').rmtree(session)
                elif scenario=='commit':
                    ok,message=ui.commit_copy(session);self.assertTrue(ok,message)
                    self.assertEqual(Path(session,'original-destination-backup').read_bytes(),SAVE)
                    ok,_=ui.commit_copy(session);self.assertFalse(ok)
                else:
                    changed=SAVE[:-1]+bytes((SAVE[-1]^1,));save.write_bytes(changed)
                    ok,_=ui.commit_copy(session);self.assertFalse(ok);self.assertEqual(save.read_bytes(),changed)

    def test_corrupt_occupied_wrong_rom_and_bounds_refused(self):
        changed=bytearray(SAVE);changed[SECTIONS[5]]^=1
        with self.assertRaises(ValueError):gift.prepare(changed,ROM,next(iter(gift.PRESETS)),BOX,SLOT)
        occupied=next(i for i in range(420) if PC[4+i*80:4+(i+1)*80] != bytes(80))
        with self.assertRaises(ValueError):gift.prepare(SAVE,ROM,next(iter(gift.PRESETS)),*divmod(occupied,30))
        for box,slot in ((-1,0),(14,0),(0,-1),(0,30)):
            with self.assertRaises(ValueError):gift.prepare(SAVE,ROM,next(iter(gift.PRESETS)),box,slot)
        with self.assertRaises(ValueError):gift.prepare(SAVE,b'wrong',next(iter(gift.PRESETS)),BOX,SLOT)

    def test_exclusive_cli_output_and_original_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'output.srm'
            args=['python3',str(sources/'butterflyos-gen3-gift.py'),'--save',str(save_path),'--rom',str(rom_path),'--preset','surf-pichu-egg','--box',str(BOX),'--slot',str(SLOT),'--output',str(out),'--helper',str(helper)]
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(json.loads(result.stdout)['egg'])
            original=out.read_bytes()
            again=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0);self.assertEqual(out.read_bytes(),original)
        self.assertEqual(save_path.read_bytes(),SAVE)


if __name__=='__main__':unittest.main()

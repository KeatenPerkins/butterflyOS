#!/usr/bin/env python3
"""Peer/save boundaries and player routing for the experimental SameBoy backend."""
import base64
import importlib.util
import json
from pathlib import Path
import socket
import struct
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-bslap-gb.py'
spec = importlib.util.spec_from_file_location('gb', SOURCE)
gb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gb)

class GBTests(unittest.TestCase):
    def test_peer_requires_token_selected_rom_generation_and_bounded_save(self):
        sha = next(k for k,v in gb.ROM_CODES.items() if v == 'G2CR')
        meta = dict(gb_token='a'*64, remote_rom_sha=sha, game_code='G2GO')
        message = dict(token='a'*64, rom_sha=sha, save=base64.b64encode(b'S'*32768).decode())
        self.assertEqual(gb.validate_peer(message, meta), b'S'*32768)
        for field, value in [('token', 'b'*64), ('rom_sha', 'f'*64), ('save', 'invalid!')]:
            with self.assertRaises(ValueError):
                gb.validate_peer(dict(message, **{field:value}), meta)
        with self.assertRaises(ValueError):
            gb.validate_peer(message, dict(meta, game_code='G1RE'))

    def test_frame_rejects_oversized_length_before_payload(self):
        left,right=socket.socketpair()
        try:
            right.sendall(struct.pack('!I', 256*1024+1))
            with self.assertRaises(ValueError): gb.receive(left)
        finally: left.close(); right.close()

    def test_save_return_uses_joiner_netplay_result_preserves_rtc_and_conflicts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); content=root/'content'; (content/'.netplay').mkdir(parents=True)
            original=root/'game.srm'; original.write_bytes(b'O'*32768+b'RTC-TRAILER')
            (content/'player1.srm').write_bytes(b'H'*32768)
            (content/'player2.srm').write_bytes(b'X'*32768)
            (content/'.netplay/player2.srm').write_bytes(b'J'*32768)
            meta=dict(role='join', save=str(original), save_sha=gb.digest(original))
            with mock.patch.object(gb,'validate_save'):
                gb.finish(root,meta,1)
                self.assertEqual(original.read_bytes(), b'O'*32768+b'RTC-TRAILER')
                gb.finish(root,meta,0)
                self.assertEqual(original.read_bytes(), b'J'*32768+b'RTC-TRAILER')
                with self.assertRaises(ValueError): gb.finish(root,meta,0)

    def test_frontend_routes_both_roms_and_only_local_view(self):
        for role, player in [('host',1),('join',2)]:
            with self.subTest(role=role), tempfile.TemporaryDirectory() as d:
                root=Path(d); (root/'states').mkdir()
                rom=root/'local.gbc'; rom.write_bytes(b'LOCAL')
                peer=root/'remote.gbc'; peer.write_bytes(b'REMOTE')
                save=root/'before.srm'; save.write_bytes(b'L'*32768)
                remote=root/'peer-before.srm'; remote.write_bytes(b'P'*32768)
                base=root/'base.cfg'; base.write_text('audio_driver = "pipewire"\n')
                meta=dict(role=role, rom=str(rom), remote_rom_sha=gb.digest(peer), peer='192.168.1.20')
                args=['-L',str(gb.CORE),'--appendconfig',str(base),str(rom)]
                with mock.patch.object(gb,'validate_backend'), mock.patch.object(gb,'exchange',return_value=remote), mock.patch.object(gb.time,'sleep'), mock.patch.object(gb.os,'execv') as execute:
                    gb.frontend(root,meta,args,lambda:[peer])
                command=execute.call_args.args[1]
                self.assertIn('gb_link_2p',command)
                self.assertIn('--sram-mode=load-save',command)
                self.assertIn('sameboy_screen_layout = "game-boy-%d"'%player,(root/'options.cfg').read_text())
                self.assertEqual((root/'content/player1.srm').read_bytes(), (b'L' if role=='host' else b'P')*32768)
                self.assertEqual((root/'content/player2.srm').read_bytes(), (b'P' if role=='host' else b'L')*32768)
                self.assertIn('savestate_auto_load = "false"',(root/'overrides.cfg').read_text())

if __name__=='__main__': unittest.main()

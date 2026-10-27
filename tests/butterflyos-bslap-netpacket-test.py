#!/usr/bin/env python3
"""Single-instance routing, save isolation, clock handling and fallback checks."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SOURCES = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'
def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCES / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
app = load('butterflyos-bslap')
core = load('butterflyos-bslap-gb-netpacket')

class NetpacketTests(unittest.TestCase):
    def test_selects_explicit_fallback_and_rejects_unknown_mode(self):
        self.assertEqual(app.gb_backend('sameboy-dual').ID, 'sameboy-dual')
        self.assertEqual(app.gb_backend('gambatte-netpacket').ID, 'gambatte-netpacket')
        with self.assertRaises(ValueError): app.gb_backend('unexpected')

    def test_lobby_rejects_different_gb_backend_before_launch(self):
        meta=dict(game_code='G1RE', backend='gambatte-netpacket', rom_sha='a'*64)
        message=dict(type='ready',game_code='G1BL',backend=app.BACKEND,
                     gb_backend='sameboy-dual',rom_sha='b'*64)
        connection=mock.Mock();connection.read.return_value=message
        server=mock.MagicMock();server.__enter__.return_value=server
        server.accept.return_value=(mock.Mock(),('192.168.1.20',1000))
        with mock.patch.object(app.socket,'socket',return_value=server), \
                mock.patch.object(app.select,'select',return_value=([server],[],[])), \
                mock.patch.object(app,'Advertisement'), \
                mock.patch.object(app,'LobbyConnection',return_value=connection):
            with self.assertRaisesRegex(ValueError,'unsupported game or Bslap build'):
                app.host_lobby(mock.Mock(),meta)
        self.assertNotIn('gb_token',meta)

    def test_each_player_launches_only_their_game_and_save(self):
        for role in ('host', 'join'):
            for game in ('G1RE', 'G1YE', 'G2CR'):
                with self.subTest(role=role, game=game), tempfile.TemporaryDirectory() as directory:
                    session=Path(directory)/'sessions/test';session.mkdir(parents=True)
                    rom=Path(directory)/'Owned game.gbc';rom.write_bytes(b'ROM')
                    (session/'before.srm').write_bytes(b'L'*32768)
                    (session/'before.rtc').write_bytes(b'CLOCK123')
                    base=session/'base.cfg';base.write_text('input_enable_hotkey_btn = "10"\n')
                    args=['-L','ordinarycore','--appendconfig',str(base),str(rom)]
                    meta=dict(role=role,rom=str(rom),game_code=game,peer='192.168.1.20',gb_token='a'*64)
                    with mock.patch.object(core,'validate_backend'),mock.patch.object(core.time,'sleep'),mock.patch.object(core.os,'execv') as execute:
                        core.frontend(session,meta,args,mock.Mock(side_effect=AssertionError('Peer ROM lookup forbidden')))
                    command=execute.call_args.args[1]
                    self.assertNotIn('--subsystem',command)
                    self.assertEqual(command[command.index('-L')+1],str(core.CORE))
                    self.assertEqual((session/'content/local.srm').read_bytes(),b'L'*32768)
                    self.assertEqual((session/'content/local.rtc').read_bytes(),b'CLOCK123')
                    self.assertIn('--host' if role=='host' else '--connect',command)
                    text=(session/'overrides.cfg').read_text()
                    self.assertIn('netplay_password = ""',text)
                    self.assertIn('netplay_spectate_password = ""',text)
                    self.assertIn('savestate_auto_save = "false"',text)
                    self.assertIn('input_enable_hotkey_btn = "10"',text)
                    options=(session/'options.cfg').read_text()
                    self.assertEqual('Special 3' in options,game.startswith('G1'))
                    self.assertFalse((session/'peer-before.srm').exists())
                    if role=='join':
                        self.assertEqual((session/'content/.netplay/local.srm').read_bytes(),b'L'*32768)
                        self.assertEqual((session/'content/.netplay/local.rtc').read_bytes(),b'CLOCK123')

    def test_bad_session_password_is_rejected_before_working_files(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory)
            with mock.patch.object(core,'validate_backend'):
                for value in ('bad', 'a'*64+'\n', None):
                    with self.assertRaises(ValueError):
                        core.frontend(session,dict(gb_token=value),[],lambda:[])
            self.assertFalse((session/'content').exists())

    def test_failed_exit_or_conflict_never_replaces_original(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory);(session/'content').mkdir()
            original=session/'original.srm';original.write_bytes(b'O'*32768)
            (session/'before.srm').write_bytes(original.read_bytes())
            (session/'content/local.srm').write_bytes(b'N'*32768)
            meta=dict(save=str(original),save_sha=core.digest(original),rtc_sha=None)
            with mock.patch.object(core,'validate_save'):
                core.finish(session,meta,1)
                self.assertEqual(original.read_bytes(),b'O'*32768)
                original.write_bytes(b'X'*32768)
                with self.assertRaises(ValueError):core.finish(session,meta,0)
                self.assertEqual(original.read_bytes(),b'X'*32768)

    def test_clean_exit_preserves_legacy_trailer_and_returns_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory);(session/'content').mkdir()
            original=session/'original.srm';original.write_bytes(b'O'*32768+b'TRAILER')
            rtc=original.with_suffix('.rtc');rtc.write_bytes(b'CLOCKOLD')
            meta=dict(save=str(original),save_sha=core.digest(original))
            (session/'before.srm').write_bytes(original.read_bytes())
            core.prepare_save(session,meta)
            self.assertEqual((session/'before.rtc').read_bytes(),b'CLOCKOLD')
            (session/'content/local.srm').write_bytes(b'N'*32768)
            (session/'content/local.rtc').write_bytes(b'CLOCKNEW')
            with mock.patch.object(core,'validate_save'):core.finish(session,meta,0)
            self.assertEqual(original.read_bytes(),b'N'*32768+b'TRAILER')
            self.assertEqual(rtc.read_bytes(),b'CLOCKNEW')
            self.assertEqual((session/'before.srm').read_bytes(),b'O'*32768+b'TRAILER')

    def test_joiner_returns_netplay_result_and_clock_instead_of_seed_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory);(session/'content/.netplay').mkdir(parents=True)
            original=session/'original.srm';original.write_bytes(b'O'*32768)
            (session/'before.srm').write_bytes(original.read_bytes())
            (session/'content/local.srm').write_bytes(original.read_bytes())
            (session/'content/.netplay/local.srm').write_bytes(b'J'*32768)
            (session/'content/.netplay/local.rtc').write_bytes(b'CLOCKNEW')
            meta=dict(role='join',save=str(original),save_sha=core.digest(original),rtc_sha=None)
            with mock.patch.object(core,'validate_save'):core.finish(session,meta,0)
            self.assertEqual(original.read_bytes(),b'J'*32768)
            self.assertEqual(original.with_suffix('.rtc').read_bytes(),b'CLOCKNEW')

    def test_joiner_returns_updated_root_when_netplay_path_is_only_startup_seed(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory);(session/'content/.netplay').mkdir(parents=True)
            original=session/'original.srm';original.write_bytes(b'O'*32768)
            (session/'before.srm').write_bytes(original.read_bytes())
            seed=session/'content/.netplay/local.srm';seed.write_bytes(original.read_bytes())
            os.utime(seed,ns=(1_000_000_000,1_000_000_000))
            (session/'content/local.srm').write_bytes(b'R'*32768)
            meta=dict(role='join',save=str(original),save_sha=core.digest(original),rtc_sha=None)
            with mock.patch.object(core,'validate_save'):core.finish(session,meta,0)
            self.assertEqual(original.read_bytes(),b'R'*32768)

    def test_bad_clock_or_save_validator_rejects_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory);(session/'content').mkdir()
            original=session/'original.srm';original.write_bytes(b'O'*32768)
            (session/'before.srm').write_bytes(original.read_bytes())
            (session/'content/local.srm').write_bytes(b'N'*32768)
            meta=dict(save=str(original),save_sha=core.digest(original),rtc_sha=None)
            (session/'content/local.rtc').write_bytes(b'BAD')
            with mock.patch.object(core,'validate_save'):
                with self.assertRaises(ValueError):core.finish(session,meta,0)
            self.assertEqual(original.read_bytes(),b'O'*32768)
            (session/'content/local.rtc').unlink()
            with mock.patch.object(core,'validate_save',side_effect=ValueError('checksum')):
                with self.assertRaises(ValueError):core.finish(session,meta,0)
            self.assertEqual(original.read_bytes(),b'O'*32768)

if __name__=='__main__':unittest.main()

#!/usr/bin/env python3
"""Protocol boundary and ROM-selection checks for the experimental launcher."""
import importlib.util
import json
import hashlib
import zipfile
from pathlib import Path
import tempfile
import unittest
import socket
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-bslap.py'
spec = importlib.util.spec_from_file_location('bslap', SOURCE)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class BslapTests(unittest.TestCase):
    def test_packaged_backend_uses_manifest_and_immutable_paths(self):
        manifest = dict(backend='bslap-v4-test', files={
            '/usr/libexec/bslap/retroarch32': 'a' * 64,
            '/usr/lib/libretro/gpsp_bslap_libretro.so': 'b' * 64})
        packaged_spec = importlib.util.spec_from_file_location('packaged_bslap', SOURCE)
        packaged = importlib.util.module_from_spec(packaged_spec)
        with mock.patch.object(Path, 'is_file', return_value=True), \
                mock.patch.object(Path, 'read_text', return_value=json.dumps(manifest)):
            packaged_spec.loader.exec_module(packaged)
        self.assertEqual(str(packaged.FRONTEND), '/usr/libexec/bslap/retroarch32')
        self.assertEqual(str(packaged.CORE), '/usr/lib/libretro/gpsp_bslap_libretro.so')
        self.assertEqual(packaged.BACKEND, 'bslap-v4-test')
        self.assertEqual(packaged.FRONTEND_SHA, 'a' * 64)
        self.assertEqual(packaged.CORE_SHA, 'b' * 64)

    def test_host_cannot_start_before_joiner_ready(self):
        class Front:
            def draw_message(self, title, text, footer):
                assert footer, 'Empty footer crashes the shared renderer'
            def draw_list(self, *args):
                raise AssertionError('Start menu shown before peer readiness')
        class UI:
            frontend = Front()
            actions = iter(['select', 'back'])
            def action(self):
                return next(self.actions)
        with mock.patch.object(app.socket, 'socket'), \
                mock.patch.object(app.select, 'select', return_value=([], [], [])), \
                mock.patch.object(app, 'Advertisement'):
            self.assertIsNone(app.host_lobby(UI(), {'rom_sha': 'a' * 64, 'game_code': 'BPEE'}))

    def test_lobby_handles_fragmented_messages_and_rejects_disconnect(self):
        left, right = socket.socketpair()
        try:
            connection = app.LobbyConnection(left)
            right.sendall(b'{"type":"sta')
            self.assertIsNone(connection.read())
            right.sendall(b'rt"}\n{"type":"go"}\n')
            self.assertEqual(connection.read(), {'type': 'start'})
            self.assertEqual(connection.read(), {'type': 'go'})
            right.close()
            with self.assertRaises(ValueError):
                connection.read()
        finally:
            left.close()
            right.close()

    def test_frontend_isolates_options_and_routes_save_without_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = root / 'session'
            session.mkdir()
            (session / 'session.json').write_text(json.dumps(dict(
                save=str(root / 'games with spaces/Emerald.srm'), role='join', peer='192.168.1.20')))
            base = root / 'base.cfg'
            base.write_text('audio_driver = "pipewire"\n')
            current = root / 'generated.cfg'
            current.write_text('input_enable_hotkey_btn = "10"\ninput_exit_emulator_btn = "9"\nquit_press_twice = "true"\n')
            (session / 'retroarch.cfg').write_text('input_enable_hotkey_btn = "8"\n')
            args = ['--config', str(session / 'retroarch.cfg'), '--appendconfig', str(base), '-L', str(app.CORE), '/games/Emerald.gba']
            with mock.patch.dict(app.os.environ, BSLAP_SESSION=str(session)), \
                    mock.patch.object(app, 'SYSTEM_RETROARCH_CONFIG', current), \
                    mock.patch.object(app.os, 'execv') as execute:
                app.frontend(args)
            self.assertEqual(current.read_text(), (session / 'retroarch.cfg').read_text())
            self.assertIn('input_enable_hotkey_btn = "10"', (session / 'retroarch.cfg').read_text())
            text = (session / 'overrides.cfg').read_text()
            for option in ['global_core_options = "true"', 'game_specific_options = "false"',
                           'savestate_auto_load = "false"', 'config_save_on_exit = "false"']:
                self.assertIn(option, text)
            self.assertIn(str(session / 'options.cfg'), text)
            self.assertIn(str(root / 'games with spaces'), text)
            self.assertEqual(base.read_text(), 'audio_driver = "pipewire"\n')
            command = execute.call_args.args[1]
            self.assertEqual(command[-2:], ['--connect', '192.168.1.20'])
            self.assertEqual(command[command.index('--appendconfig') + 1], str(session / 'overrides.cfg'))

    def test_gen1_and_gen2_refresh_first_boot_hotkeys_before_backend_dispatch(self):
        for game in ('G1RE', 'G2CR'):
            for role in ('host', 'join'):
                with self.subTest(game=game, role=role), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    session = root / 'session'
                    session.mkdir()
                    (session / 'session.json').write_text(json.dumps(dict(game_code=game, role=role)))
                    (session / 'retroarch.cfg').write_text('input_enable_hotkey_btn = "8"\n')
                    current = root / 'generated.cfg'
                    fresh = ('input_enable_hotkey_btn = "10"\ninput_exit_emulator_btn = "9"\n'
                             'quit_press_twice = "true"\ninput_player1_joypad_index = "0"\n')
                    current.write_text(fresh)
                    backend = mock.Mock()
                    def launch(actual_session, meta, args, find_games):
                        self.assertEqual(actual_session, session)
                        self.assertEqual(meta['role'], role)
                        self.assertEqual((actual_session / 'retroarch.cfg').read_text(), fresh)
                    backend.frontend.side_effect = launch
                    with mock.patch.dict(app.os.environ, BSLAP_SESSION=str(session)), \
                            mock.patch.object(app, 'SYSTEM_RETROARCH_CONFIG', current), \
                            mock.patch.object(app, 'gb_backend', return_value=backend):
                        app.frontend(['--config', str(session / 'retroarch.cfg')])
                    backend.frontend.assert_called_once()
                    self.assertEqual(current.read_text(), fresh)

    def test_header_filter_and_duplicate_mount(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gba = root / 'gba'
            gba.mkdir()
            for name, code in [('renamed.gba', b'BPEE'), ('Ruby.gba', b'AXVE'),
                               ('Sapphire.gba', b'AXPE'), ('FireRed.gba', b'BPRE'),
                               ('LeafGreen.gba', b'BPGE'), ('Emerald.gba', b'AWRE'),
                               ('Japanese.gba', b'BPEJ')]:
                data = bytearray(192)
                data[0xAC:0xB0] = code
                (gba / name).write_bytes(data)
            (gba / 'short.gba').write_bytes(b'BPEE')
            alias = root / 'alias'
            alias.symlink_to(gba, target_is_directory=True)
            qualified = {hashlib.sha256(p.read_bytes()).hexdigest(): p.read_bytes()[172:176].decode()
                         for p in gba.glob('*.gba') if p.name not in ('short.gba', 'Emerald.gba', 'Japanese.gba')}
            with mock.patch.dict(app.GBA_ROM_CODES, qualified, clear=True):
                found = app.find_games([gba, alias])
            self.assertEqual([p.name for p in found], ['FireRed.gba', 'LeafGreen.gba', 'renamed.gba', 'Ruby.gba', 'Sapphire.gba'])

    def test_zip_and_raw_content_qualification_rejects_header_preserving_hack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = bytearray(192)
            data[172:176] = b'BPRE'
            rom = root / 'renamed.zip'
            with zipfile.ZipFile(rom, 'w') as archive:
                archive.writestr('nested/game.gba', data)
            with mock.patch.dict(app.GBA_ROM_CODES, {hashlib.sha256(data).hexdigest(): 'BPRE'}, clear=True):
                self.assertEqual(app.game_code(rom), 'BPRE')
                hack = root / 'hack.gba'
                hack.write_bytes(bytes(data) + b'modified')
                with self.assertRaises(ValueError): app.game_code(hack)
                with zipfile.ZipFile(rom, 'a') as archive:
                    archive.writestr('another.gba', data)
                with self.assertRaises(ValueError): app.game_code(rom)

    def test_zip_preparation_reads_rom_once_and_preserves_original_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / 'LeafGreen.zip'
            data = bytearray(192); data[172:176] = b'BPGE'
            with zipfile.ZipFile(rom, 'w') as archive:
                archive.writestr('game.gba', data)
            save = rom.with_suffix('.srm'); save.write_bytes(b'original-save')
            config = root / 'retroarch.cfg'; config.write_text('')
            with mock.patch.object(app, 'ROOT', root / 'bslap'), \
                 mock.patch.object(app, 'SYSTEM_RETROARCH_CONFIG', config), \
                 mock.patch.object(app, 'validate_backend'), \
                 mock.patch.object(app.subprocess, 'run', return_value=mock.Mock(returncode=0)), \
                 mock.patch.dict(app.GBA_ROM_CODES, {hashlib.sha256(data).hexdigest(): 'BPGE'}, clear=True), \
                 mock.patch.object(app, 'gba_rom_data', wraps=app.gba_rom_data) as read:
                session, meta = app.prepare_session(rom, 'host')
            self.assertEqual(read.call_count, 1)
            self.assertEqual(Path(meta['rom']).read_bytes(), bytes(data))
            self.assertEqual(meta['save'], str(save))
            self.assertEqual(save.read_bytes(), b'original-save')
            self.assertEqual((session / 'before.srm').read_bytes(), b'original-save')
            self.assertEqual(meta['rom_sha'], hashlib.sha256(data).hexdigest())

    def test_gameboy_zip_prepare_and_frontend_keep_save_clock_and_content_paths(self):
        for extension, code in (('.gb', 'G1BL'), ('.gbc', 'G2CR')):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                data = bytearray(bytes(range(256)) * 4)
                title = b'POKEMON BLUE' if code == 'G1BL' else b'PM_CRYSTAL'
                data[0x134:0x134 + len(title)] = title
                data = bytes(data)
                raw = root / ('renamed' + extension); raw.write_bytes(data)
                rom = root / 'renamed.zip'
                with zipfile.ZipFile(rom, 'w') as archive:
                    archive.writestr('../../nested/game' + extension, data)
                save = rom.with_suffix('.srm'); save.write_bytes(b'original-save')
                rtc = rom.with_suffix('.rtc'); rtc.write_bytes(b'12345678')
                config = root / 'retroarch.cfg'; config.write_text('')
                base = root / 'base.cfg'; base.write_text('')
                gb = app.gb_backend('gambatte-netpacket')
                sha = hashlib.sha256(data).hexdigest()
                with mock.patch.object(app, 'ROOT', root / 'bslap'), \
                     mock.patch.object(app, 'gb_backend', return_value=gb), \
                     mock.patch.object(app, 'SYSTEM_RETROARCH_CONFIG', config), \
                     mock.patch.object(app, 'validate_backend'), \
                     mock.patch.object(gb, 'validate_backend'), \
                     mock.patch.object(app.subprocess, 'run', return_value=mock.Mock(returncode=0)), \
                     mock.patch.dict(gb.dual.ROM_CODES, {sha: code}, clear=True):
                    self.assertEqual(app.game_code(raw), code)
                    self.assertEqual(app.game_code(rom), code)
                    session, meta = app.prepare_session(rom, 'join', '192.168.1.20')
                    self.assertEqual(meta['rom_sha'], sha)
                    self.assertEqual(meta['save'], str(save))
                    self.assertEqual(meta['source_rom'], str(rom))
                    self.assertEqual(Path(meta['rom']).suffix, extension)
                    self.assertEqual(Path(meta['rom']).read_bytes(), data)
                    self.assertFalse((session / 'content').exists())
                    self.assertEqual((session / 'before.rtc').read_bytes(), b'12345678')
                    gb.prepare_token(meta)
                    args = ['--appendconfig', str(base), '-L', str(app.CORE), meta['rom']]
                    with mock.patch.object(gb.os, 'execv') as execute, mock.patch.object(gb.time, 'sleep'):
                        gb.frontend(session, meta, args, app.find_games)
                    content = session / 'content'
                    self.assertEqual((content / ('local' + extension)).read_bytes(), data)
                    self.assertEqual((content / 'local.srm').read_bytes(), b'original-save')
                    self.assertEqual((content / '.netplay/local.srm').read_bytes(), b'original-save')
                    self.assertEqual((content / 'local.rtc').read_bytes(), b'12345678')
                    self.assertIn(str(content / ('local' + extension)), execute.call_args.args[1])
                self.assertEqual(save.read_bytes(), b'original-save')
                self.assertEqual(rtc.read_bytes(), b'12345678')

    def test_gameboy_zip_rejects_ambiguous_oversized_and_modified_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); rom = root / 'game.zip'
            with zipfile.ZipFile(rom, 'w') as archive:
                archive.writestr('game.gb', b'X' * 1024)
                archive.writestr('other.gba', b'X' * 1024)
            with self.assertRaises(ValueError): app.game_code(rom)
            with zipfile.ZipFile(rom, 'w') as archive:
                archive.writestr('game.gbc', b'X' * (4 * 1024**2 + 1))
            with self.assertRaises(ValueError): app.game_code(rom)
            with zipfile.ZipFile(rom, 'w') as archive:
                archive.writestr('game.gb', b'X' * 1024)
            with self.assertRaises(ValueError): app.game_code(rom)
            rom.write_bytes(b'broken archive')
            with self.assertRaises(ValueError): app.game_code(rom)

    def test_gameboy_scan_reads_only_header_for_unrelated_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            rom = Path(directory) / 'renamed.zip'
            with zipfile.ZipFile(rom, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('unrelated.gbc', b'X' * (2 * 1024**2))
            reads = []
            original = zipfile.ZipExtFile.read
            def read(stream, size=-1):
                reads.append(size)
                return original(stream, size)
            with mock.patch.object(zipfile.ZipExtFile, 'read', read):
                with self.assertRaises(ValueError): app.gb_rom_data(rom)
            self.assertEqual(reads, [0x150])

    def test_scan_cache_reuses_unchanged_results_and_rechecks_changed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); library = root / 'gb'; library.mkdir()
            rom = library / 'game.zip'; rom.write_bytes(b'first-version')
            cache = root / 'bslap'; cache.mkdir()
            with mock.patch.object(app, 'ROOT', cache), mock.patch.object(app, 'game_code', return_value='G1BL') as qualify:
                self.assertEqual(app.find_games([library]), [rom])
                self.assertEqual(app.find_games([library]), [rom])
                self.assertEqual(qualify.call_count, 1)
                rom.write_bytes(b'changed-version')
                self.assertEqual(app.find_games([library]), [rom])
                self.assertEqual(qualify.call_count, 2)
                qualify.side_effect = ValueError('not qualified')
                rom.write_bytes(b'new-unqualified-content')
                self.assertEqual(app.find_games([library]), [])
                self.assertEqual(app.find_games([library]), [])
                self.assertEqual(qualify.call_count, 3)

    def test_corrupt_scan_cache_does_not_hide_a_supported_game(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); rom = root / 'game.gb'; rom.write_bytes(b'fixture')
            (root / 'rom-scan-cache.json').write_text('not json')
            with mock.patch.object(app, 'ROOT', root), mock.patch.object(app, 'game_code', return_value='G1BL'):
                self.assertEqual(app.find_games([root]), [rom])

    def test_cross_game_gen3_matrix_rejects_unsupported_headers(self):
        for first in app.GAMES:
            for second in app.GAMES:
                self.assertEqual(app.compatible_games(first, second),
                                 (first[:2] if first.startswith('G') else 'G3') ==
                                 (second[:2] if second.startswith('G') else 'G3'))
        for unsupported in ('BPRJ', 'BPGJ', 'BPEJ', '', None, []):
            self.assertFalse(app.compatible_games('BPEE', unsupported))

    def test_time_capsule_requires_opposite_gb_generations(self):
        for a in app.GAMES:
            for b in app.GAMES:
                expected = {a[:2], b[:2]} == {'G1', 'G2'}
                self.assertEqual(app.compatible_games(a, b, 'time-capsule'), expected)
        self.assertFalse(app.compatible_games('G1BL', 'G2CR'))
        self.assertFalse(app.compatible_games('BPEE', 'G2CR', 'time-capsule'))
        self.assertFalse(app.compatible_games('G1BL', None, 'time-capsule'))

    def test_room_uses_sender_address_and_requires_matching_backend(self):
        room = dict(app='Bslap', version=4, backend=app.BACKEND, port=app.PORT,
                    lobby_port=app.LOBBY_PORT,
                    game_code='AXVE',
                    name='My Flip', rom_sha='a' * 64, ip='8.8.8.8')
        result = app.valid_room(json.dumps(room), '192.168.1.17')
        self.assertEqual(result['ip'], '192.168.1.17')
        for key, value in [('backend', 'other-build'), ('port', 22), ('game_code', 'BPRJ'),
                           ('rom_sha', []), ('name', 'x' * 65)]:
            changed = dict(room, **{key: value})
            self.assertIsNone(app.valid_room(json.dumps(changed), '192.168.1.17'))
        self.assertIsNone(app.valid_room('[]', '192.168.1.17'))
        self.assertIsNone(app.valid_room('broken', '192.168.1.17'))
        self.assertIsNone(app.valid_room(json.dumps(room), '127.0.0.1'))
        self.assertIsNone(app.valid_room(json.dumps(dict(room, version=1)), '192.168.1.17'))


if __name__ == '__main__':
    unittest.main()

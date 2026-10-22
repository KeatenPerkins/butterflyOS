#!/usr/bin/env python3
"""Protocol boundary and ROM-selection checks for the experimental launcher."""
import importlib.util
import json
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
            args = ['--appendconfig', str(base), '-L', str(app.CORE), '/games/Emerald.gba']
            with mock.patch.dict(app.os.environ, BSLAP_SESSION=str(session)), \
                    mock.patch.object(app.os, 'execv') as execute:
                app.frontend(args)
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
            found = app.find_games([gba, alias])
            self.assertEqual([p.name for p in found], ['FireRed.gba', 'LeafGreen.gba', 'renamed.gba', 'Ruby.gba', 'Sapphire.gba'])

    def test_cross_game_gen3_matrix_rejects_unsupported_headers(self):
        for first in app.GAMES:
            for second in app.GAMES:
                self.assertEqual(app.compatible_games(first, second),
                                 (first[:2] if first.startswith('G') else 'G3') ==
                                 (second[:2] if second.startswith('G') else 'G3'))
        for unsupported in ('BPRJ', 'BPGJ', 'BPEJ', '', None, []):
            self.assertFalse(app.compatible_games('BPEE', unsupported))

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

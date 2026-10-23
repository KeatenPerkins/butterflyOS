#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bslap LAN launcher. Shares Blink/Bdex's controller UI."""
import fcntl
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path('/storage/.config/butterflyos/bslap')
TEST = Path('/storage/.config/butterflyos/gpsp-link-tests')
FRONTEND = TEST / 'retroarch-current/retroarch32'
CORE = Path('/tmp/cores/gpsp_bfplain_libretro.so')
FRONTEND_SHA = '556a1d7b09ea280ba06d34ad53347864d6f4288702894cbe104842591bb5da89'
CORE_SHA = '1ae51cbbc844f4c9574dbb2dc3853097d9badc53b32057ec84e1577615b91f55'
PORT, DISCOVERY_PORT, LOBBY_PORT = 55435, 55436, 55437
REQUEST = b'BSLAP_DISCOVER_V4'
BACKEND = 'gpsp-bfplain1-sameboy-c8564b65-v4'
MANIFEST = Path('/usr/share/bslap/backend.json')
if MANIFEST.is_file():
    packaged = json.loads(MANIFEST.read_text())
    FRONTEND = Path('/usr/libexec/bslap/retroarch32')
    CORE = Path('/usr/lib/libretro/gpsp_bslap_libretro.so')
    FRONTEND_SHA = packaged['files'][str(FRONTEND)]
    CORE_SHA = packaged['files'][str(CORE)]
    BACKEND = packaged['backend']
GAMES = {'AXVE': 'Ruby', 'AXPE': 'Sapphire', 'BPEE': 'Emerald', 'BPRE': 'FireRed', 'BPGE': 'LeafGreen'}
GAMES.update({'G2CR': 'Crystal', 'G2GO': 'Gold', 'G2SI': 'Silver',
              'G1RE': 'Red', 'G1BL': 'Blue', 'G1YE': 'Yellow'})

def gb_backend():
    path = Path(__file__).with_name('butterflyos-bslap-gb.py')
    spec = importlib.util.spec_from_file_location('bslap_gb', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ISSUE = ('Gen 3 only: room exits can show a communication error. '
         'Gen 1 and Gen 2 use a different link backend and have passed '
         'room-exit testing without this issue.\n\n'
         'For better results, let ONE player initiate leaving. On the other '
         'device, respond to the exit dialogue that follows. Avoid independently '
         'starting the exit on both devices. This is not a guaranteed fix.\n\n'
         'Save normally after leaving safely. Each session backs up your '
         'ordinary save before play. Bslap uses that same save during play; '
         'your in-game saves update it. Automatic state loading is disabled.')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def find_games(roots=None):
    roots = roots or [Path(base) / system for base in
                      ('/storage/roms', '/storage/games-external/roms')
                      for system in ('gba', 'gbc', 'gb')]
    found, seen = [], set()
    for root in roots:
        for folder, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in
                       ('images', 'media', 'savestates', 'screenshots')]
            for name in sorted(files):
                if Path(name).suffix.lower() not in ('.gba', '.gbc', '.gb'):
                    continue
                path = Path(folder) / name
                try:
                    real = path.resolve()
                    if real in seen:
                        continue
                    try:
                        game_code(path)
                    except ValueError:
                        continue
                    seen.add(real)
                    found.append(path)
                except OSError:
                    continue
    return sorted(found, key=lambda p: (p.stem.lower(), str(p)))


def game_code(path):
    if Path(path).suffix.lower() in ('.gb', '.gbc'):
        return gb_backend().rom_code(path)
    with Path(path).open('rb') as stream:
        header = stream.read(192)
    code = header[0xAC:0xB0].decode('ascii', 'replace')
    if code not in GAMES:
        raise ValueError('Choose an English Ruby, Sapphire, Emerald, FireRed or LeafGreen ROM.')
    return code


def compatible_games(first, second):
    return (isinstance(first, str) and isinstance(second, str) and
            first in GAMES and second in GAMES and
            (first[:2] if first.startswith('G') else 'G3') ==
            (second[:2] if second.startswith('G') else 'G3'))


def valid_room(data, address):
    try:
        room = json.loads(data)
        ip = ipaddress.IPv4Address(address)
        if ip.is_unspecified or ip.is_multicast or ip.is_loopback:
            return None
        if (room.get('app') != 'Bslap' or room.get('version') != 4 or
                room.get('backend') != BACKEND or room.get('port') != PORT or
                room.get('lobby_port') != LOBBY_PORT or
                room.get('game_code') not in GAMES or
                not re.fullmatch('[0-9a-f]{64}', room.get('rom_sha', '')) or
                not isinstance(room.get('name'), str) or len(room['name']) > 64):
            return None
        # Never trust an advertised destination supplied in the packet.
        return dict(name=room['name'], ip=str(ip), rom_sha=room['rom_sha'],
                    game_code=room['game_code'])
    except (ValueError, TypeError, AttributeError):
        return None


def discover(seconds=2.5):
    rooms = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.2)
        sock.bind(('', 0))
        deadline, last = time.monotonic() + seconds, 0
        while time.monotonic() < deadline:
            if time.monotonic() - last > 0.6:
                sock.sendto(REQUEST, ('255.255.255.255', DISCOVERY_PORT))
                last = time.monotonic()
            try:
                data, peer = sock.recvfrom(2048)
                room = valid_room(data, peer[0])
                if room:
                    rooms[room['ip']] = room
            except socket.timeout:
                pass
    return sorted(rooms.values(), key=lambda r: (r['name'], r['ip']))


class Advertisement:
    def __init__(self, rom_sha, code):
        self.stop_event = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', DISCOVERY_PORT))
        self.sock.settimeout(0.2)
        self.data = json.dumps(dict(app='Bslap', version=4, backend=BACKEND,
                                   name=socket.gethostname()[:64], port=PORT,
                                   lobby_port=LOBBY_PORT,
                                   rom_sha=rom_sha, game_code=code)).encode()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        while not self.stop_event.is_set():
            try:
                data, peer = self.sock.recvfrom(256)
                if data == REQUEST:
                    self.sock.sendto(self.data, peer)
            except socket.timeout:
                pass
            except OSError:
                break

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=1)
        self.sock.close()


class LobbyConnection:
    def __init__(self, sock):
        self.sock, self.buffer = sock, b''
        self.sock.settimeout(1)

    def send(self, kind, **fields):
        self.sock.sendall((json.dumps(dict(type=kind, **fields)) + '\n').encode())

    def read(self):
        if b'\n' not in self.buffer:
            if not select.select([self.sock], [], [], 0)[0]:
                return None
            data = self.sock.recv(4096)
            if not data:
                raise ValueError('The other player left the Bslap lobby.')
            self.buffer += data
            if len(self.buffer) > 4096:
                raise ValueError('Invalid Bslap lobby message.')
        if b'\n' not in self.buffer:
            return None
        line, self.buffer = self.buffer.split(b'\n', 1)
        message = json.loads(line)
        if not isinstance(message, dict) or message.get('type') not in (
                'ready', 'start', 'ack', 'go', 'cancel'):
            raise ValueError('Invalid Bslap lobby message.')
        if message['type'] == 'cancel':
            raise ValueError('The other player cancelled the Bslap session.')
        return message

    def close(self):
        self.sock.close()


def host_lobby(ui, meta):
    """Keep both apps in their lobby until the joining player is ready."""
    connection = None
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', LOBBY_PORT))
        server.listen(1)
        advert = Advertisement(meta['rom_sha'], meta['game_code'])
        advert.thread.start()
        ready, starting, selected = False, False, 0
        try:
            while True:
                if connection is None and select.select([server], [], [], 0)[0]:
                    peer, address = server.accept()
                    meta['peer'] = address[0]
                    connection = LobbyConnection(peer)
                message = connection.read() if connection else None
                if message:
                    if message['type'] == 'ready':
                        if (not compatible_games(meta['game_code'], message.get('game_code')) or
                                message.get('backend') != BACKEND):
                            raise ValueError('The joining player has an unsupported game or Bslap build.')
                        meta['remote_rom_sha'] = message.get('rom_sha')
                        if not re.fullmatch('[0-9a-f]{64}', str(meta['remote_rom_sha'])):
                            raise ValueError('Invalid joining ROM checksum.')
                        ready = True
                    elif message['type'] == 'ack' and starting:
                        result, connection = connection, None
                        return result
                    else:
                        raise ValueError('Unexpected Bslap lobby response.')
                if ready and not starting:
                    ui.frontend.draw_list('BSLAP - BOTH PLAYERS READY',
                        'Start launches the host, then the joining game.',
                        [('Start', 'Begin the linked session'), ('Cancel', 'Return to Bslap')], selected)
                else:
                    ui.frontend.draw_message('BSLAP - HOST LOBBY',
                        'Preparing both games...' if starting else
                        'Waiting for the other player.\n\nOn the other device, choose '
                        'Join, select this host and confirm readiness. Your game '
                        'will stay closed until both players are ready.', 'B Cancel')
                action = ui.action()
                if action == 'back' or (ready and not starting and action == 'select' and selected == 1):
                    if connection:
                        connection.send('cancel')
                    return None
                if ready and not starting:
                    if action in ('up', 'down'):
                        selected = 1 - selected
                    elif action == 'select' and selected == 0:
                        if meta['game_code'].startswith('G'):
                            gb_backend().prepare_token(meta)
                        connection.send('start', rom_sha=meta['rom_sha'],
                                        gb_token=meta.get('gb_token', ''))
                        starting = True
                time.sleep(0.02)
        finally:
            advert.close()
            if connection:
                connection.close()


def join_lobby(ui, meta):
    with socket.create_connection((meta['peer'], LOBBY_PORT), timeout=5) as sock:
        connection = LobbyConnection(sock)
        connection.send('ready', rom_sha=meta['rom_sha'], backend=BACKEND,
                        game_code=meta['game_code'])
        started, deadline = False, None
        while True:
            message = connection.read()
            if message:
                if message['type'] == 'start' and not started:
                    meta['remote_rom_sha'] = message.get('rom_sha')
                    meta['gb_token'] = message.get('gb_token', '')
                    connection.send('ack')
                    started, deadline = True, time.monotonic() + 60
                elif message['type'] == 'go' and started:
                    return True
                else:
                    raise ValueError('Unexpected Bslap host response.')
            if deadline and time.monotonic() > deadline:
                raise ValueError('The host game did not become ready. Return to Bslap and retry.')
            ui.frontend.draw_message('BSLAP - JOIN LOBBY',
                'The host is starting its game. Yours will follow automatically.' if started else
                'You are ready. Waiting for the host to choose Start.\n\nNeither game '
                'will launch until the host confirms.', 'B Cancel')
            if ui.action() == 'back':
                connection.send('cancel')
                return False
            time.sleep(0.02)


def host_frontend_ready():
    if (ROOT / 'gb-exchange-ready').exists():
        return gb_backend().listening()
    if not (ROOT / 'host-ready').exists():
        return False
    return any(':%04X' % PORT in line and line.split()[3] == '0A'
               for path in ('/proc/net/tcp', '/proc/net/tcp6')
               for line in Path(path).read_text().splitlines()[1:])


def validate_backend():
    for path, expected in [(FRONTEND, FRONTEND_SHA), (CORE, CORE_SHA)]:
        if not path.is_file() or digest(path) != expected:
            raise ValueError('Bslap components are missing or changed. '
                             'Install the matching Bslap package first.')
    if subprocess.run(['pidof', 'retroarch', 'retroarch32'],
                      stdout=subprocess.DEVNULL).returncode == 0:
        raise ValueError('Exit the running game before opening Bslap.')


def frontend(args):
    """Test-only runemu executable target; append isolated overrides last."""
    session = Path(os.environ['BSLAP_SESSION'])
    meta = json.loads((session / 'session.json').read_text())
    if meta.get('game_code', '').startswith('G'):
        return gb_backend().frontend(session, meta, args, find_games)
    append = session / 'overrides.cfg'
    args = list(args)
    index = args.index('--appendconfig')
    # The base runemu configuration was just generated for this game.
    append.write_text(Path(args[index + 1]).read_text() + '\n' +
                      '\n'.join('%s = "%s"' % pair for pair in [
                          ('config_save_on_exit', 'false'),
                          ('savestate_auto_load', 'false'), ('savestate_auto_save', 'false'),
                          ('savestate_directory', str(session / 'states')),
                          ('savefile_directory', str(Path(meta['save']).parent)),
                          ('savefiles_in_content_dir', 'false'),
                          ('sort_savefiles_enable', 'false'),
                          ('sort_savefiles_by_content_enable', 'false'),
                          ('game_specific_options', 'false'),
                          ('global_core_options', 'true'),
                          ('auto_overrides_enable', 'false'),
                          ('core_options_path', str(session / 'options.cfg'))]) + '\n')
    args[index + 1] = str(append)
    extra = ['--port', str(PORT), '--nick', 'Bslap']
    extra += ['--host'] if meta['role'] == 'host' else ['--connect', meta['peer']]
    if meta['role'] == 'host':
        (ROOT / 'host-ready').touch()
    os.execv(str(FRONTEND), [str(FRONTEND)] + args + extra)


def prepare_session(rom, role, peer=''):
    validate_backend()
    code = game_code(rom)
    if code.startswith('G'):
        gb_backend().validate_backend()
    save = rom.with_suffix('.srm')
    if not save.is_file():
        raise ValueError('No adjacent ordinary .srm save found for this game. '
                         'Launch and save the game normally first. This '
                         'Bslap supports uncompressed English Ruby, Sapphire, Emerald, FireRed and LeafGreen.')
    # Reject configuration metacharacters in paths before generating RA config.
    if any(c in str(rom) for c in ('"', '\n', '\r')):
        raise ValueError('This ROM path cannot be used in the Bslap launcher.')
    result = subprocess.run(['/usr/bin/butterflyos-save-trade', 'inspect', '--save', str(save)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise ValueError('The ordinary save failed validation. It has not been changed.')
    (ROOT / 'sessions').mkdir(parents=True, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix=time.strftime('%Y%m%d-%H%M%S-'), dir=ROOT / 'sessions'))
    shutil.copy2(save, session / 'before.srm')
    shutil.copy2('/storage/.config/retroarch/retroarch.cfg', session / 'retroarch.cfg')
    (session / 'states').mkdir()
    (session / 'options.cfg').write_text('gpsp_serial = "mul_poke"\n')
    meta = dict(rom=str(rom), save=str(save), role=role, peer=peer, game_code=game_code(rom),
                rom_sha=digest(rom), save_sha=digest(save), frontend_sha=FRONTEND_SHA, core_sha=CORE_SHA)
    if code.startswith('G'):
        gb = gb_backend()
        meta.update(frontend_sha=gb.FRONTEND_SHA, core_sha=gb.CORE_SHA, backend='sameboy-dual')
    (session / 'session.json').write_text(json.dumps(meta, indent=2))
    return session, meta


def play(session, meta, lobby=None):
    (session / 'session.json').write_text(json.dumps(meta, indent=2))
    runner = ROOT / 'runemu.sh'
    source = Path('/usr/bin/runemu.sh').read_text()
    if source.count('/usr/bin/${RABIN}') != 1:
        raise ValueError('The system game launcher changed; update the Bslap test package.')
    source = source.replace('/usr/bin/${RABIN}', str(ROOT / 'frontend'))
    old = 'RETROARCH_TEMP_CONFIG="/storage/.config/retroarch/retroarch.cfg"'
    if source.count(old) != 1:
        raise ValueError('The system configuration layout changed; update Bslap.')
    source = source.replace(old, 'RETROARCH_TEMP_CONFIG="${BSLAP_SESSION}/retroarch.cfg"')
    runner.write_text(source)
    runner.chmod(0o755)
    wrapper = ROOT / 'frontend'
    wrapper.write_text('#!/bin/sh\nexec /usr/bin/python3 "' + str(Path(__file__).resolve()) +
                       '" --frontend "$@"\n')
    wrapper.chmod(0o755)
    (ROOT / 'host-ready').unlink(missing_ok=True)
    (ROOT / 'gb-exchange-ready').unlink(missing_ok=True)
    is_gb = meta['game_code'].startswith('G')
    system, core = ('gbc', 'sameboy') if is_gb else ('gba', CORE.name.removesuffix('_libretro.so'))
    try:
        env = dict(os.environ, BSLAP_SESSION=str(session))
        with subprocess.Popen([str(runner), meta['rom'], '-P' + system, '--core=' + core,
                               '--emulator=retroarch', '--controllers=', '-state_slot', '0',
                               '-autosave', '0'], env=env) as process:
            if lobby:
                deadline = time.monotonic() + 50
                while process.poll() is None and not host_frontend_ready():
                    if time.monotonic() > deadline:
                        lobby.send('cancel')
                        break
                    time.sleep(0.05)
                else:
                    if process.poll() is None:
                        lobby.send('go')
                lobby.close()
                lobby = None
            result = process.wait()
            if is_gb:
                gb_backend().finish(session, meta, result)
            return result
    finally:
        if lobby:
            lobby.close()
        (ROOT / 'host-ready').unlink(missing_ok=True)
        (ROOT / 'gb-exchange-ready').unlink(missing_ok=True)
        if Path(meta['save']).is_file():
            shutil.copy2(meta['save'], session / 'after.srm')
        log = Path('/storage/.cache/log/exec.log')
        if log.is_file():
            shutil.copy2(log, session / 'exec.log')


def load_ui():
    path = Path(__file__).with_name('butterflyos-tool-ui.py')
    if not path.is_file():
        path = Path('/usr/bin/butterflyos-tool-ui.py')
    spec = importlib.util.spec_from_file_location('bslap_tool_ui', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ToolUI('Bslap', native_controller=True)


def choose_game(ui, games):
    if not games:
        ui.message('NO SUPPORTED ROM FOUND', 'Bslap supports uncompressed '
                   'English Gen 1/2 (.gb/.gbc) and Gen 3 (.gba) on either card. ROMs are '
                   'identified by their header, not their filename.')
        return None
    choice = ui.menu('BSLAP - CHOOSE GAME', [(p.stem, str(p.parent)) for p in games])
    return games[choice] if choice is not None else None


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    with (ROOT / 'launcher.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 1
        ui = load_ui()
        try:
            while True:
                choice = ui.menu('BSLAP', [
                    ('Host', 'Start a nearby trade or battle session'),
                    ('Join', 'Find a Bslap host on your local network'),
                    ('How to play', 'Cable Club, saves and controls'),
                    ('Gen 3 known issue', 'Recommended Gen 3 room-exit workflow'),
                    ('Back', 'Return to Tools')])
                if choice is None or choice == 4:
                    return 0
                if choice == 3:
                    ui.message('GEN 3 ROOM EXIT - KNOWN ISSUE', ISSUE)
                    continue
                if choice == 2:
                    ui.message('HOW TO PLAY', 'Connect both devices to the same Wi-Fi. '
                               'Host chooses a game and waits in the lobby. The other '
                               'chooses Join and a compatible game. Once both are ready, '
                               'the host chooses Start. No typing is needed.\n\nChoose Continue '
                               'from the Pokemon title screen, then use the upstairs '
                               'Cable Club to trade or battle. Use the normal game-exit '
                               'hotkey to return here.\n\nGen 1 and Gen 2 use SameBoy: both '
                               'selected ROMs must exist on both devices. Temporary save '
                               'copies are exchanged. Save in BOTH games before either '
                               'player exits. The room-exit communication warning applies '
                               'only to Gen 3. '
                               'Save backups are kept in /storage/.config/butterflyos/'
                               'bslap/sessions. Blink and Bdex are separate tools.')
                    continue
                try:
                    validate_backend()
                    games = find_games()
                    peer = ''
                    role = 'host' if choice == 0 else 'join'
                    if role == 'join':
                        ui.frontend.draw_message('FINDING BSLAP HOSTS',
                                                 'Searching your local network...', 'Searching...')
                        rooms = discover()
                        if not rooms:
                            ui.message('NO HOST FOUND', 'Open Host on the other device '
                                       'first, then choose Join again. Both devices need '
                                       'the same Bslap build and local network. Guest '
                                       'Wi-Fi may block discovery.')
                            continue
                        pick = ui.menu('JOIN BSLAP', [(r['name'], r['ip'] + ' | ' + GAMES[r['game_code']]) for r in rooms])
                        if pick is None:
                            continue
                        room = rooms[pick]
                        peer = room['ip']
                        games = [p for p in games if compatible_games(game_code(p), room['game_code'])]
                        if not games:
                            ui.message('COMPATIBLE GAME NEEDED', 'Choose a supported English ROM '
                                       'from the same generation. Both devices must use '
                                       'the same Bslap build.')
                            continue
                    if role == 'host':
                        generation = ui.menu('BSLAP - GENERATION', [
                            ('Gen 1', 'Red, Blue and Yellow'),
                            ('Gen 2', 'Gold, Silver and Crystal'),
                            ('Gen 3', 'Ruby, Sapphire, Emerald, FireRed and LeafGreen')])
                        if generation is None:
                            continue
                        prefix = ('G1', 'G2', '')[generation]
                        games = [p for p in games if
                                 (game_code(p).startswith(prefix) if prefix else
                                  not game_code(p).startswith('G'))]
                    rom = choose_game(ui, games)
                    if rom is None:
                        continue
                    ui.message('BEFORE YOU PLAY',
                               gb_backend().NOTICE if game_code(rom).startswith('G') else ISSUE)
                    confirm = ui.menu('ENTER BSLAP LOBBY?', [('Ready', role.title() + ': ' + rom.stem),
                                                      ('Back', 'Return without launching')])
                    if confirm != 0:
                        continue
                    session, meta = prepare_session(rom, role, peer)
                    lobby = None
                    if role == 'host':
                        lobby = host_lobby(ui, meta)
                        if lobby is None:
                            continue
                    elif not join_lobby(ui, meta):
                        continue
                    if meta['game_code'].startswith('G') and not any(
                            p.suffix.lower() in ('.gb', '.gbc') and
                            digest(p) == meta.get('remote_rom_sha') for p in games):
                        if lobby:
                            lobby.send('cancel')
                            lobby.close()
                        raise ValueError('Both selected ROMs must already exist on each device.')
                    ui.close()
                    ui = None
                    try:
                        result = play(session, meta, lobby)
                    finally:
                        ui = load_ui()
                    ui.message('BSLAP SESSION ENDED', 'Save backup and logs:\n' +
                               str(session) + ('\n\nThe launcher reported an error.' if result else '') +
                               ('\n\nGen 1/2: save on BOTH games before either player exits. '
                                'The validated local result is returned after a clean exit.'
                                if meta['game_code'].startswith('G') else
                                '\n\nGen 3: save in-game after safely leaving the room. '
                                'An exit error does not confirm whether a trade was saved.'))
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    if ui is None:
                        ui = load_ui()
                    ui.message('BSLAP COULD NOT START', str(error))
        finally:
            if ui is not None:
                ui.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--frontend':
        frontend(sys.argv[2:])
    else:
        sys.exit(main())

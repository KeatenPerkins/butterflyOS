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
import zipfile
import zlib

ROOT = Path('/storage/.config/butterflyos/bslap')
SYSTEM_RETROARCH_CONFIG = Path('/storage/.config/retroarch/retroarch.cfg')
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

def gb_backend(mode=None):
    if mode is None:
        setting = ROOT / 'gb-backend'
        mode = setting.read_text().strip() if setting.is_file() else (
            'gambatte-netpacket' if MANIFEST.is_file() and
            '/usr/lib/libretro/gambatte_bslap_libretro.so' in
            json.loads(MANIFEST.read_text())['files'] else 'sameboy-dual')
    names = {'sameboy-dual': 'butterflyos-bslap-gb.py',
             'gambatte-netpacket': 'butterflyos-bslap-gb-netpacket.py'}
    if mode not in names:
        raise ValueError('Unknown Game Boy link backend.')
    path = Path(__file__).with_name(names[mode])
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
                if Path(name).suffix.lower() not in ('.gba', '.gbc', '.gb', '.zip'):
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


# Same retail revisions already qualified by Blink's Gen 3 gifts.
GBA_ROM_CODES = {
 'a9dec84dfe7f62ab2220bafaef7479da0929d066ece16a6885f6226db19085af': 'BPEE',
 '0fdd36e92b75bed65d09df4635ab0b707b288c2bf1dc4c6e7a4a4f0eebe9d64c': 'AXVE',
 '02ca41513580a8b780989dee428df747b52a0b1a55bec617886b4059eb1152fb': 'AXPE',
 '729041b940afe031302d630fdbe57c0c145f3f7b6d9b8eca5e98678d0ca4d059': 'BPRE',
 '2f978f635b9593f6ca26ec42481c53a6b39f6cddd894ad5c062c1419fac58825': 'BPGE',
}


def gba_rom_data(path):
    path = Path(path)
    if path.suffix.lower() == '.zip':
        try:
            with zipfile.ZipFile(path) as archive:
                members = [m for m in archive.infolist() if not m.is_dir()
                           and Path(m.filename).suffix.lower() == '.gba']
                if len(members) != 1 or not 192 <= members[0].file_size <= 32 * 1024**2:
                    raise ValueError('Choose a ZIP containing exactly one supported GBA ROM.')
                with archive.open(members[0]) as stream:
                    header = stream.read(192)
                    if header[172:176].decode('ascii', 'replace') not in GAMES:
                        raise ValueError('Not a supported Pokemon GBA header.')
                    return header + stream.read()
        except (zipfile.BadZipFile, RuntimeError) as error:
            raise ValueError('Cannot read this GBA ZIP archive.') from error
    if not 192 <= path.stat().st_size <= 32 * 1024**2:
        raise ValueError('Unsupported GBA ROM size.')
    with path.open('rb') as stream:
        header = stream.read(192)
        if header[172:176].decode('ascii', 'replace') not in GAMES:
            raise ValueError('Not a supported Pokemon GBA header.')
        return header + stream.read()


def rom_extension(path):
    """Determine one ZIP's ROM family without trusting the archive filename."""
    path = Path(path)
    if path.suffix.lower() != '.zip':
        return path.suffix.lower()
    try:
        with zipfile.ZipFile(path) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()
                       and Path(m.filename).suffix.lower() in ('.gb', '.gbc', '.gba')]
            if len(members) != 1:
                raise ValueError('Choose a ZIP containing exactly one Game Boy or GBA ROM.')
            return Path(members[0].filename).suffix.lower()
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
        raise ValueError('Cannot read this ROM ZIP archive.') from error


def gb_rom_data(path):
    path = Path(path)
    limit = 4 * 1024**2
    if path.suffix.lower() != '.zip':
        if not 0x150 <= path.stat().st_size <= limit:
            raise ValueError('Unsupported Game Boy ROM size.')
        return path.read_bytes()
    try:
        with zipfile.ZipFile(path) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()
                       and Path(m.filename).suffix.lower() in ('.gb', '.gbc', '.gba')]
            if (len(members) != 1 or Path(members[0].filename).suffix.lower() not in ('.gb', '.gbc')
                    or not 0x150 <= members[0].file_size <= limit):
                raise ValueError('Choose a ZIP containing exactly one supported Game Boy ROM.')
            with archive.open(members[0]) as stream:
                data = stream.read(limit + 1)
            if len(data) != members[0].file_size:
                raise ValueError('Invalid Game Boy ROM size.')
            return data
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, zlib.error) as error:
        raise ValueError('Cannot read this Game Boy ZIP archive.') from error


def generation_roots(code):
    system = 'gb' if code.startswith('G1') else 'gbc' if code.startswith('G2') else 'gba'
    return [Path(base) / system for base in ('/storage/roms', '/storage/games-external/roms')]


def game_code(path, data=None):
    if rom_extension(path) in ('.gb', '.gbc'):
        return gb_backend().rom_code(path, gb_rom_data(path) if data is None else data)
    data = gba_rom_data(path) if data is None else data
    code = GBA_ROM_CODES.get(hashlib.sha256(data).hexdigest())
    if code is None or data[0xAC:0xB0].decode('ascii', 'replace') != code:
        raise ValueError('Use qualified English Emerald, Ruby/Sapphire revision 2, '
                         'or FireRed/LeafGreen revision 1. ROM hacks are unsupported.')
    return code


def compatible_games(first, second, mode='same-generation'):
    if mode == 'time-capsule':
        return (isinstance(first, str) and isinstance(second, str) and
                first in GAMES and second in GAMES and
                {first[:2], second[:2]} == {'G1', 'G2'})
    if mode != 'same-generation':
        return False
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
        mode = room.get('session_mode', 'same-generation')
        if mode not in ('same-generation', 'time-capsule') or (mode == 'time-capsule' and not room['game_code'].startswith('G')):
            return None
        # Never trust an advertised destination supplied in the packet.
        return dict(name=room['name'], ip=str(ip), rom_sha=room['rom_sha'],
                    game_code=room['game_code'], session_mode=mode)
    except (ValueError, TypeError, AttributeError):
        return None


def discover(seconds=60.0, ui=None):
    rooms = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.1)
        sock.bind(('', 0))
        deadline, last = time.monotonic() + seconds, float('-inf')
        displayed = None
        while time.monotonic() < deadline:
            if ui:
                if ui.action() == 'back':
                    return None
                remaining = max(1, int(deadline - time.monotonic() + 0.999))
                status = 'Host found. Checking nearby hosts...' if rooms else (
                    'Searching your local network...\n%d seconds remaining.' % remaining)
                if status != displayed:
                    ui.frontend.draw_message('FINDING BSLAP HOSTS', status, 'B Cancel')
                    displayed = status
            if time.monotonic() - last > 0.6:
                sock.sendto(REQUEST, ('255.255.255.255', DISCOVERY_PORT))
                last = time.monotonic()
            try:
                data, peer = sock.recvfrom(2048)
                room = valid_room(data, peer[0])
                if room:
                    if not rooms:
                        # Show hosts promptly, with a short window for other replies.
                        deadline = min(deadline, time.monotonic() + 0.6)
                    rooms[room['ip']] = room
            except socket.timeout:
                pass
    return sorted(rooms.values(), key=lambda r: (r['name'], r['ip']))


class Advertisement:
    def __init__(self, rom_sha, code, session_mode='same-generation'):
        self.stop_event = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', DISCOVERY_PORT))
        self.sock.settimeout(0.2)
        self.data = json.dumps(dict(app='Bslap', version=4, backend=BACKEND,
                                   name=socket.gethostname()[:64], port=PORT,
                                   lobby_port=LOBBY_PORT,
                                   rom_sha=rom_sha, game_code=code, session_mode=session_mode)).encode()
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
        advert = Advertisement(meta['rom_sha'], meta['game_code'], meta.get('session_mode', 'same-generation'))
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
                        if (not compatible_games(meta['game_code'], message.get('game_code'), meta.get('session_mode', 'same-generation')) or
                                message.get('session_mode', 'same-generation') != meta.get('session_mode', 'same-generation') or
                                (meta['game_code'].startswith('G') and
                                 message.get('gb_backend', 'sameboy-dual') != meta.get('backend')) or
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
                        game_code=meta['game_code'], gb_backend=meta.get('backend'),
                        session_mode=meta.get('session_mode', 'same-generation'))
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
    # runemu has now generated this launch's controller/hotkey configuration.
    # prepare_session's earlier snapshot can still contain first-boot defaults
    # (Select instead of Menu). Refresh before either backend reads --config.
    # Keep the session copy isolated; never save emulator changes globally.
    shutil.copyfile(SYSTEM_RETROARCH_CONFIG, session / 'retroarch.cfg')
    if meta.get('game_code', '').startswith('G'):
        return gb_backend(meta.get('backend')).frontend(session, meta, args, find_games)
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
    # Validate the exact decompressed bytes used for play; never trust an
    # archive's filename or earlier picker qualification. Read the ROM once.
    extension = rom_extension(rom)
    rom_data = gb_rom_data(rom) if extension in ('.gb', '.gbc') else gba_rom_data(rom)
    code = game_code(rom, rom_data)
    if Path(rom).suffix.lower() == '.zip' and code.startswith('G') and gb_backend().ID != 'gambatte-netpacket':
        raise ValueError('Game Boy ZIPs require the default Gambatte link backend; use raw ROMs for the SameBoy fallback.')
    if code.startswith('G'):
        gb_backend().validate_backend()
    save = rom.with_suffix('.srm')
    if not save.is_file():
        raise ValueError('No adjacent ordinary .srm save found for this game. '
                         'Launch and save the game normally first. This '
                         'Bslap needs an in-game save matching the selected ROM filename.')
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
    shutil.copy2(SYSTEM_RETROARCH_CONFIG, session / 'retroarch.cfg')
    (session / 'states').mkdir()
    (session / 'options.cfg').write_text('gpsp_serial = "mul_poke"\n')
    meta = dict(rom=str(rom), save=str(save), role=role, peer=peer, game_code=code,
                rom_sha=hashlib.sha256(rom_data).hexdigest(), save_sha=digest(save), frontend_sha=FRONTEND_SHA, core_sha=CORE_SHA)
    if Path(rom).suffix.lower() == '.zip':
        # The Game Boy backend creates its own content/save working folder.
        # Keep extracted ROMs separate, and keep the original archive's save path.
        content = session / 'rom'
        content.mkdir()
        unpacked = content / (rom.stem + extension)
        unpacked.write_bytes(rom_data)
        meta['source_rom'] = str(rom)
        meta['rom'] = str(unpacked)
    if code.startswith('G'):
        gb = gb_backend()
        meta.update(frontend_sha=gb.FRONTEND_SHA, core_sha=gb.CORE_SHA, backend=gb.ID)
        if hasattr(gb, 'prepare_save'):
            gb.prepare_save(session, meta)
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
    system, core = ('gbc', 'gambatte' if meta.get('backend') == 'gambatte-netpacket' else 'sameboy') if is_gb else ('gba', CORE.name.removesuffix('_libretro.so'))
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
                gb_backend(meta.get('backend')).finish(session, meta, result)
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
        ui.message('NO SUPPORTED ROM FOUND', 'Bslap supports qualified English Gen 1/2/3 raw ROMs or single-ROM ZIP archives on either card. ROM content is validated; hacks are unsupported.')
        return None
    choice = ui.menu('BSLAP - CHOOSE GAME', [(p.stem, ('ZIP archive' if p.suffix.lower() == '.zip' else 'Uncompressed ' + p.suffix.lower()) + ' | ' + str(p.parent)) for p in games])
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
                               'hotkey to return here.\n\nGen 1 and Gen 2 use the selected '
                               'Game Boy link backend. The single-instance test runs only '
                               'your own game; SameBoy fallback requires both ROMs on both '
                               'devices. Save in BOTH games before exiting. The room-exit warning applies '
                               'only to Gen 3. '
                               'Save backups are kept in /storage/.config/butterflyos/'
                               'bslap/sessions. Blink and Bdex are separate tools.')
                    continue
                try:
                    validate_backend()
                    peer = ''
                    role = 'host' if choice == 0 else 'join'
                    session_mode = 'same-generation'
                    if role == 'join':
                        rooms = discover(ui=ui)
                        if rooms is None:
                            continue
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
                        session_mode = room.get('session_mode', 'same-generation')
                        ui.frontend.draw_message('CHECKING LOCAL GAMES',
                                                 'Finding compatible ROMs on your SD cards...',
                                                 'Please wait')
                        roots = generation_roots('G2' if room['game_code'].startswith('G1') else 'G1') if session_mode == 'time-capsule' else generation_roots(room['game_code'])
                        games = [p for p in find_games(roots) if compatible_games(game_code(p), room['game_code'], session_mode)]
                        if not games:
                            ui.message('COMPATIBLE GAME NEEDED', 'Choose a supported English ROM '
                                       'compatible with the selected session. Both devices must use '
                                       'the same Bslap build.')
                            continue
                    if role == 'host':
                        generation = ui.menu('BSLAP - GENERATION', [
                            ('Gen 1', 'Red, Blue and Yellow'),
                            ('Gen 2', 'Gold, Silver and Crystal'),
                            ('Gen 3', 'Ruby, Sapphire, Emerald, FireRed and LeafGreen'),
                            ('Time Capsule', 'Gen 1 to Gen 2 trading only')])
                        if generation is None:
                            continue
                        ui.frontend.draw_message('CHECKING LOCAL GAMES',
                                                 'Finding supported ROMs on your SD cards...',
                                                 'Please wait')
                        session_mode = 'time-capsule' if generation == 3 else 'same-generation'
                        roots = generation_roots('G1') + generation_roots('G2') if generation == 3 else generation_roots(('G1', 'G2', 'G3')[generation])
                        games = find_games(roots)
                        prefix = ('G1', 'G2', '', 'G')[generation]
                        games = [p for p in games if
                                 (game_code(p).startswith(prefix) if prefix else
                                  not game_code(p).startswith('G'))]
                    rom = choose_game(ui, games)
                    if rom is None:
                        continue
                    if session_mode == 'time-capsule':
                        if gb_backend().ID != 'gambatte-netpacket':
                            raise ValueError('Time Capsule requires the single-instance Gambatte backend.')
                        ui.message('TIME CAPSULE - TRADING ONLY',
                                   'Gen 2: use the unlocked Time Capsule. Gen 1: use the normal Trade Center. '
                                   'Gen 2 party must contain only Gen 1 species and moves; no Eggs. '
                                   'The games enforce their normal restrictions. Save on both games before exiting. '
                                   'Initial development test: use disposable saves.')
                    ui.message('BEFORE YOU PLAY',
                               gb_backend().NOTICE if game_code(rom).startswith('G') else ISSUE)
                    confirm = ui.menu('ENTER BSLAP LOBBY?', [('Ready', role.title() + ': ' + rom.stem),
                                                      ('Back', 'Return without launching')])
                    if confirm != 0:
                        continue
                    session, meta = prepare_session(rom, role, peer)
                    meta['session_mode'] = session_mode
                    lobby = None
                    if role == 'host':
                        lobby = host_lobby(ui, meta)
                        if lobby is None:
                            continue
                    elif not join_lobby(ui, meta):
                        continue
                    if meta.get('backend') == 'sameboy-dual' and not any(
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

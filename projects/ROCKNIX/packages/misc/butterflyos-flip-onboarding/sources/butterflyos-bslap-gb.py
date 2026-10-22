#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""SameBoy dual-GB integration for Bslap's Gen 1/2 sessions.

Reuses the former link session's host/player1 and guest/player2 arrangement.
Only save working copies cross the LAN. Both ROMs must already be owned locally.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import struct
import subprocess
import time

CORE = Path('/usr/lib/libretro/sameboy_libretro.so')
FRONTEND = Path('/usr/bin/retroarch')
CORE_SHA = 'c8564b6539097ecf0ee90bd6edf0574a24576e3ca28e93d0288aaefd013b3fbd'
FRONTEND_SHA = 'f1ff8a00dea858cc4266f96bf381e628e748b9dff824dbef4482b2bfb9013eb7'
MANIFEST = Path('/usr/share/bslap/backend.json')
if MANIFEST.is_file():
    files = json.loads(MANIFEST.read_text())['files']
    CORE_SHA, FRONTEND_SHA = files[str(CORE)], files[str(FRONTEND)]
PORT = 55438
NOTICE = ('Gen 1/2: each device runs both linked Game Boys, but shows and '
          'controls its own player. Both selected ROMs must exist on both devices. '
          'Only temporary save copies are exchanged on your local network; no ROMs '
          'are sent. Save normally on BOTH games before either player exits. '
          'Exit on both devices when finished.\n\n'
          'A validated local result is copied back only after a clean emulator '
          'exit. Original saves are backed up before play. Failed results stay '
          'in the session folder for recovery. Automatic states are disabled.')
ROM_CODES = {
    'fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e': 'G2GO',
    '72b190859a59623cbef6c49d601f8de52c1d2331b4f08a8d2acc17274fc19a8c': 'G2SI',
    'fdcc3c8c43813cf8731fc037d2a6d191bac75439c34b24ba1c27526e6acdc8a2': 'G2CR',
    '5ca7ba01642a3b27b0cc0b5349b52792795b62d3ed977e98a09390659af96b7b': 'G1RE',
    '2a951313c2640e8c2cb21f25d1db019ae6245d9c7121f754fa61afd7bee6452d': 'G1BL',
    '8cbaa499397e4f1a679c992ea9382a2dd7942ab398b48c19829c2d9529de47bf': 'G1YE',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rom_code(path):
    if Path(path).stat().st_size > 4 * 1024 * 1024:
        raise ValueError('Unsupported Game Boy ROM size.')
    code = ROM_CODES.get(digest(path))
    if not code:
        raise ValueError('This Game Boy ROM revision/language is not qualified for Bslap.')
    return code


def validate_backend():
    for path, expected in ((CORE, CORE_SHA), (FRONTEND, FRONTEND_SHA)):
        if not path.is_file() or digest(path) != expected:
            raise ValueError('The matching SameBoy backend is not installed.')


def prepare_token(meta):
    meta['gb_token'] = secrets.token_hex(32)


def listening(port=PORT):
    return any(':%04X' % port in line and line.split()[3] == '0A'
               for name in ('/proc/net/tcp', '/proc/net/tcp6')
               for line in Path(name).read_text().splitlines()[1:])


def receive_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise ValueError('The other player disconnected during save preparation.')
        data.extend(part)
    return bytes(data)


def send(sock, message):
    data = json.dumps(message).encode()
    if len(data) > 256 * 1024:
        raise ValueError('Invalid Game Boy session data size.')
    sock.sendall(struct.pack('!I', len(data)) + data)


def receive(sock):
    size = struct.unpack('!I', receive_exact(sock, 4))[0]
    if not 0 < size <= 256 * 1024:
        raise ValueError('Invalid Game Boy session data size.')
    message = json.loads(receive_exact(sock, size))
    if not isinstance(message, dict):
        raise ValueError('Invalid Game Boy session data.')
    return message


def validate_peer(message, meta):
    token = message.get('token')
    expected = meta.get('gb_token')
    if not isinstance(token, str) or not isinstance(expected, str) or len(expected) != 64 or not secrets.compare_digest(token, expected):
        raise ValueError('Invalid Game Boy session token.')
    sha = message.get('rom_sha')
    if sha != meta.get('remote_rom_sha') or sha not in ROM_CODES:
        raise ValueError('The other player changed their selected ROM.')
    if ROM_CODES[sha][:2] != meta['game_code'][:2]:
        raise ValueError('Choose two games from the same generation.')
    try:
        save = base64.b64decode(message['save'], validate=True)
    except (KeyError, ValueError, TypeError) as error:
        raise ValueError('Invalid peer save data.') from error
    if not 32768 <= len(save) <= 131072:
        raise ValueError('Invalid Game Boy save size.')
    return save


def validate_save(path):
    result = subprocess.run(['/usr/bin/butterflyos-save-trade', 'inspect', '--save', str(path)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError('The Game Boy save failed validation; original save was not replaced.')


def exchange(session, meta):
    """Authenticate the selected peer and exchange bounded save copies, never ROMs."""
    message = dict(token=meta['gb_token'], rom_sha=meta['rom_sha'],
                   save=base64.b64encode((session / 'before.srm').read_bytes()).decode())
    if meta['role'] == 'host':
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('', PORT))
            server.listen(1)
            server.settimeout(45)
            (session.parent.parent / 'gb-exchange-ready').touch()
            sock, address = server.accept()
            with sock:
                sock.settimeout(30)
                if address[0] != meta['peer']:
                    raise ValueError('An unexpected device connected to the save exchange.')
                peer = receive(sock)
                save = validate_peer(peer, meta)
                send(sock, message)
    else:
        with socket.create_connection((meta['peer'], PORT), timeout=20) as sock:
            sock.settimeout(30)
            send(sock, message)
            peer = receive(sock)
            save = validate_peer(peer, meta)
    target = session / 'peer-before.srm'
    target.write_bytes(save)
    target.chmod(0o600)
    validate_save(target)
    return target


def frontend(session, meta, args, find_games):
    validate_backend()
    remote_rom = next((p for p in find_games() if p.suffix.lower() in ('.gb', '.gbc')
                       and digest(p) == meta['remote_rom_sha']), None)
    if remote_rom is None:
        raise ValueError('Both selected ROMs must already exist on each device; no ROMs are transferred.')
    peer_save = exchange(session, meta)
    content = session / 'content'
    content.mkdir(mode=0o700)
    local = (Path(meta['rom']), session / 'before.srm')
    remote = (remote_rom, peer_save)
    sources = (local, remote) if meta['role'] == 'host' else (remote, local)
    roms = []
    for number, (rom, save) in enumerate(sources, 1):
        target = content / ('player%d' % number + rom.suffix.lower())
        target.symlink_to(rom)
        roms.append(str(target))
        shutil.copy2(save, content / ('player%d.srm' % number))
    player = 1 if meta['role'] == 'host' else 2
    # Both simulations must use an identical emulated RTC for rollback netplay.
    # Wall-clock RTC differs across devices; SameBoy's accurate mode advances
    # the RTC with emulated time instead.
    options = {
        'sameboy_link': 'enabled', 'sameboy_audio_output': 'Game Boy #%d' % player,
        'sameboy_screen_layout': 'game-boy-%d' % player,
        'sameboy_model': 'Auto', 'sameboy_model_1': 'Auto', 'sameboy_model_2': 'Auto',
        'sameboy_rtc': 'accurate', 'sameboy_border': 'never',
        'sameboy_audio_interference': '0', 'sameboy_rumble': 'never',
    }
    (session / 'options.cfg').write_text(''.join('%s = "%s"\n' % item for item in options.items()))
    args = list(args)
    index = args.index('--appendconfig')
    base = Path(args[index + 1]).read_text()
    overrides = dict(config_save_on_exit='false', savestate_auto_load='false',
                     savestate_auto_save='false', savestate_directory=str(session / 'states'),
                     savefile_directory=str(content), savefiles_in_content_dir='false',
                     sort_savefiles_enable='false', sort_savefiles_by_content_enable='false',
                     game_specific_options='false', global_core_options='true',
                     auto_overrides_enable='false', core_options_path=str(session / 'options.cfg'),
                     autosave_interval='5', video_smooth='false',
                     netplay_public_announce='false', netplay_use_mitm_server='false',
                     netplay_check_frames='30')
    append = session / 'overrides.cfg'
    append.write_text(base + '\n' + ''.join('%s = "%s"\n' % item for item in overrides.items()))
    args[index + 1] = str(append)
    args[args.index('-L') + 1] = str(CORE)
    # runemu passes the local content once; replace only that exact argument.
    at = args.index(meta['rom'])
    args[at:at + 1] = ['--subsystem', 'gb_link_2p'] + roms
    args += ['--port', '55435', '--nick', 'Bslap', '--sram-mode=load-save']
    if meta['role'] == 'host':
        args += ['--host']
    else:
        # Match the earlier tested dual-GB launcher: give the host time to
        # open Netplay without making a spurious protocol connection.
        time.sleep(2)
        args += ['--connect', meta['peer']]
    os.execv(str(FRONTEND), [str(FRONTEND)] + args)


def finish(session, meta, result):
    if result:
        return
    name = 'player1.srm' if meta['role'] == 'host' else 'player2.srm'
    candidate = session / 'content' / name
    alternate = session / 'content/.netplay' / name
    if meta['role'] == 'join' and alternate.is_file():
        candidate = alternate
    if not candidate.is_file():
        raise ValueError('The local result save is missing; original save was not changed.')
    validate_save(candidate)
    original = Path(meta['save'])
    if digest(original) != meta['save_sha']:
        raise ValueError('The original save changed outside Bslap; the result is kept in the session folder.')
    temporary = original.with_name('.' + original.name + '.bslap-' + secrets.token_hex(6))
    try:
        data = candidate.read_bytes()
        if len(data) != 32768:
            raise ValueError('Unexpected SameBoy SRAM size; original save was not changed.')
        # Gambatte may append its RTC trailer to the ordinary SRAM file.
        # Retain it; SameBoy stores its own RTC separately in the session.
        temporary.write_bytes(data + original.read_bytes()[32768:])
        shutil.copymode(original, temporary)
        os.replace(temporary, original)
    finally:
        temporary.unlink(missing_ok=True)

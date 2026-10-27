#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bslap single-Game-Boy Netpacket experiment; no peer ROM/save exchange."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import time

spec = importlib.util.spec_from_file_location('bslap_gb_dual', Path(__file__).with_name('butterflyos-bslap-gb.py'))
dual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dual)
ID = 'gambatte-netpacket'
CORE = Path('/usr/lib/libretro/gambatte_bslap_libretro.so')
FRONTEND = dual.FRONTEND
FRONTEND_SHA = dual.FRONTEND_SHA
CORE_SHA = ''
if dual.MANIFEST.is_file():
    CORE_SHA = json.loads(dual.MANIFEST.read_text())['files'].get(str(CORE), '')
PORT = 55435
NOTICE = ('Gen 1/2 single-instance test: each device runs its own Game Boy. '
          'Only link-cable messages cross your local network; ROMs and saves are '
          'not exchanged. This backend is not yet release-qualified.\n\n'
          'Save normally on BOTH games after leaving the Cable Club. '
          'Menu + Start twice exits. A validated local save returns after a clean '
          'exit. Original save and clock backups remain in the session folder.')
rom_code, digest, validate_save = dual.rom_code, dual.digest, dual.validate_save


def validate_backend():
    for path, expected in ((CORE, CORE_SHA), (FRONTEND, FRONTEND_SHA)):
        if not expected or not path.is_file() or digest(path) != expected:
            raise ValueError('The matching single-instance Game Boy backend is not installed.')


def prepare_token(meta):
    # Retain a bounded lobby session identifier, as used by the fallback.
    meta['gb_token'] = secrets.token_hex(32)


def listening():
    return dual.listening(PORT)


def prepare_save(session, meta):
    rtc = Path(meta['save']).with_suffix('.rtc')
    meta['rtc_sha'] = digest(rtc) if rtc.is_file() else None
    if rtc.is_file():
        if rtc.stat().st_size != 8:
            raise ValueError('Unsupported Game Boy clock format; original files were not changed.')
        shutil.copy2(rtc, session / 'before.rtc')


def frontend(session, meta, args, find_games):
    validate_backend()
    if not isinstance(meta.get('gb_token'), str) or not re.fullmatch('[0-9a-f]{64}', meta['gb_token']):
        raise ValueError('Invalid Game Boy session token.')
    # No peer save exchange, second content, or subsystem is used.
    content = session / 'content'
    content.mkdir(mode=0o700)
    rom = content / ('local' + Path(meta['rom']).suffix.lower())
    rom.symlink_to(meta['rom'])
    shutil.copy2(session / 'before.srm', content / 'local.srm')
    # This pinned frontend can select the client .netplay path during startup,
    # before it recognizes the core packet interface. Seed both isolated paths.
    if meta['role'] == 'join':
        (content / '.netplay').mkdir(mode=0o700)
        shutil.copy2(session / 'before.srm', content / '.netplay/local.srm')
    if (session / 'before.rtc').is_file():
        shutil.copy2(session / 'before.rtc', content / 'local.rtc')
        if meta['role'] == 'join':
            shutil.copy2(session / 'before.rtc', content / '.netplay/local.rtc')
    options = {'gambatte_gb_colorization': 'internal',
               'gambatte_gb_internal_palette': 'Special 3',
               'gambatte_gb_palette_switching': 'disabled'} if meta['game_code'].startswith('G1') else {}
    (session / 'options.cfg').write_text(''.join('%s = "%s"\n' % item for item in options.items()))
    args = list(args)
    at = args.index('--appendconfig')
    base = Path(args[at + 1]).read_text()
    overrides = dict(config_save_on_exit='false', savestate_auto_load='false',
                     savestate_auto_save='false', savestate_directory=str(session / 'states'),
                     savefile_directory=str(content), savefiles_in_content_dir='false',
                     sort_savefiles_enable='false', sort_savefiles_by_content_enable='false',
                     game_specific_options='false', global_core_options='true',
                     auto_overrides_enable='false', core_options_path=str(session / 'options.cfg'),
                     autosave_interval='5', video_smooth='false',
                     netplay_public_announce='false', netplay_use_mitm_server='false',
                     netplay_nat_traversal='false', netplay_max_connections='1',
                     netplay_start_as_spectator='false', netplay_password='',
                     netplay_spectate_password='',
                     netplay_allow_pausing='false',
                     rewind_enable='false', run_ahead_enabled='false',
                     preemptive_frames_enable='false', cheevos_enable='false')
    append = session / 'overrides.cfg'
    append.write_text(base + '\n' + ''.join('%s = "%s"\n' % item for item in overrides.items()))
    args[at + 1] = str(append)
    args[args.index('-L') + 1] = str(CORE)
    args[args.index(meta['rom'])] = str(rom)
    args += ['--port', str(PORT), '--nick', 'Bslap', '--sram-mode=load-save']
    if meta['role'] == 'host':
        (session.parent.parent / 'host-ready').touch()
        args += ['--host']
    else:
        time.sleep(1)
        args += ['--connect', meta['peer']]
    if (session.parent.parent / 'serial-trace').is_file():
        os.environ['BSLAP_SERIAL_TRACE'] = '1'
    else:
        os.environ.pop('BSLAP_SERIAL_TRACE', None)
    os.execv(str(FRONTEND), [str(FRONTEND)] + args)


def finish(session, meta, result):
    if result:
        return
    candidate = session / 'content/local.srm'
    alternate = session / 'content/.netplay/local.srm'
    if meta.get('role') == 'join':
        # Startup may log .netplay then switch back once Netpacket is active.
        # Select the file actually written most recently, never a stale seed.
        available = [path for path in (candidate, alternate) if path.is_file()]
        if available:
            before = hashlib.sha256((session / 'before.srm').read_bytes()[:32768]).digest()
            changed = [path for path in available if
                       hashlib.sha256(path.read_bytes()[:32768]).digest() != before]
            candidate = max(changed or available,
                            key=lambda path: (path.stat().st_mtime_ns, path == candidate))
    if not candidate.is_file() or candidate.stat().st_size != 32768:
        raise ValueError('Unexpected Game Boy result save; original save was not changed.')
    validate_save(candidate)
    original = Path(meta['save'])
    rtc = original.with_suffix('.rtc')
    candidate_rtc = candidate.with_suffix('.rtc')
    if digest(original) != meta['save_sha'] or (
            digest(rtc) if rtc.is_file() else None) != meta.get('rtc_sha'):
        raise ValueError('The original save or clock changed outside Bslap; result kept for recovery.')
    if candidate_rtc.is_file() and candidate_rtc.stat().st_size != 8:
        raise ValueError('Unexpected result clock format; original files were not changed.')
    # Ordinary saves can contain a historical appended clock trailer. Preserve
    # it exactly; current Gambatte/RetroArch keeps its active RTC in a sidecar.
    data = candidate.read_bytes() + (session / 'before.srm').read_bytes()[32768:]
    staged = original.with_name('.' + original.name + '.bslap-' + secrets.token_hex(6))
    rtc_staged = staged.with_suffix('.rtc')
    try:
        staged.write_bytes(data)
        shutil.copymode(original, staged)
        if candidate_rtc.is_file():
            rtc_staged.write_bytes(candidate_rtc.read_bytes())
            rtc_staged.chmod(rtc.stat().st_mode & 0o777 if rtc.is_file() else 0o600)
        os.replace(staged, original)
        if rtc_staged.is_file():
            os.replace(rtc_staged, rtc)
    finally:
        staged.unlink(missing_ok=True)
        rtc_staged.unlink(missing_ok=True)

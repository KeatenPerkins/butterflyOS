#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Opt-in, versioned ordinary-save snapshots. Never restores or changes a save."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time

CONFIG = Path('/storage/.config/butterflyos/save-backup')
OS_CARD = Path('/storage')
GAME_CARD = Path('/storage/games-external')
BACKUPS = 'ButterflyOS Save Backups'
EXTENSIONS = {'.srm', '.sav', '.rtc', '.eep', '.fla', '.sra', '.mcr', '.mcd'}
EXCLUDED = {'bios', 'savestates', 'screenshots', 'downloaded_images', BACKUPS}
KEEP = 5
MAX_SIZE = 32 * 1024 * 1024
QUIET_SECONDS = 120


def real_directory(path):
    """Reject symlink components, including a redirected backup parent."""
    path = Path(path)
    for part in [path] + list(path.parents):
        if part.is_symlink():
            raise ValueError('symlink directory: ' + str(part))
    return path


def mount_records(text):
    """Read exact kernel mountpoints without requiring util-linux findmnt."""
    def unescape(value):
        return re.sub(r'\\([0-7]{3})', lambda match: chr(int(match.group(1), 8)), value)
    records = {}
    for line in text.splitlines():
        try:
            before, after = line.split(' - ', 1)
            fields, extra = before.split(), after.split()
            records[unescape(fields[4])] = {
                'root': unescape(fields[3]), 'source': unescape(extra[1]),
                'filesystem': extra[0],
                'options': set(fields[5].split(',') + extra[2].split(',')),
            }
        except (ValueError, IndexError):
            continue
    return records


def card_info(path):
    real_directory(path)
    if not os.path.ismount(path):
        raise ValueError('card is not mounted: ' + str(path))
    record = mount_records(Path('/proc/self/mountinfo').read_text()).get(str(path))
    if record is None or record['root'] != '/':
        raise ValueError('expected a complete mounted card partition')
    source, filesystem, options = record['source'], record['filesystem'], record['options']
    if filesystem not in {'ext4', 'exfat', 'vfat'} or 'rw' not in options or 'ro' in options:
        raise ValueError('card needs a writable supported filesystem')
    if not re.fullmatch(r'/dev/mmcblk[01]p[0-9]+', source):
        raise ValueError('expected a physical SD-card partition')
    uuid = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', source],
                          check=True, capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r'[A-Za-z0-9-]+', uuid):
        raise ValueError('card UUID unavailable')
    real_directory(path / 'roms')
    if not (path / 'roms').is_dir():
        raise ValueError('prepare the second card before enabling backups')
    return {'path': path, 'device': path.stat().st_dev, 'uuid': uuid,
            'physical': source.split('p', 1)[0]}


def check_pair(source, destination):
    for card in (source, destination):
        if not os.path.ismount(card['path']) or card['path'].stat().st_dev != card['device']:
            raise ValueError('card removed or mount changed')
        if os.statvfs(card['path']).f_flag & os.ST_RDONLY:
            raise ValueError('card became read-only')
    if source['device'] == destination['device'] or source['uuid'] == destination['uuid']:
        raise ValueError('source and destination must be different cards')
    if source.get('physical') and source['physical'] == destination.get('physical'):
        raise ValueError('source and destination must be physically different cards')
    if (source['path'] / 'roms').stat().st_dev != source['device']:
        raise ValueError('ROM directory is on another mount')


def candidates(root):
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in EXCLUDED and not name.startswith('.')
                   and not (Path(directory) / name).is_symlink()]
        for name in files:
            path = Path(directory) / name
            if path.suffix.lower() in EXTENSIONS and not path.is_symlink():
                yield path


def snapshot(path, source, destination, now=None):
    check_pair(source, destination)
    now = time.time() if now is None else now
    real_directory(path.parent)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_dev != source['device']:
            return 'skipped'
        if before.st_size == 0 or before.st_size > MAX_SIZE or now - before.st_mtime < QUIET_SECONDS:
            return 'skipped'
        data = stream.read(MAX_SIZE + 1)
        after = os.fstat(stream.fileno())
    signature = lambda info: (info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if signature(before) != signature(after) or signature(before) != signature(path.lstat()):
        return 'skipped'
    digest = hashlib.sha256(data).hexdigest()
    relative = path.relative_to(source['path'] / 'roms')
    folder = destination['path'] / BACKUPS / source['uuid'] / relative
    real_directory(folder)
    existing = sorted(p for p in folder.glob('*.backup')
                          if re.fullmatch(r'[0-9]{20}-[0-9a-f]{64}\.backup', p.name)) if folder.exists() else []
    if existing and existing[-1].name.endswith('-' + digest + '.backup'):
        # Verify the existing snapshot instead of trusting its name.
        if not existing[-1].is_symlink() and hashlib.sha256(existing[-1].read_bytes()).hexdigest() == digest:
            return 'unchanged'
    free = os.statvfs(destination['path'])
    reserve = (free.f_blocks * free.f_frsize + 9) // 10
    # Include allocation rounding and modest directory overhead. Never prune to make room.
    required = ((len(data) + free.f_frsize - 1) // free.f_frsize) * free.f_frsize + 65536
    if free.f_bavail * free.f_frsize - required < reserve:
        return 'space-reserve'
    check_pair(source, destination)
    folder.mkdir(parents=True, exist_ok=True)
    real_directory(folder)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.pending-', dir=folder, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != digest:
            raise IOError('backup verification failed')
        check_pair(source, destination)
        previous = int(existing[-1].name.split('-', 1)[0]) if existing else 0
        sequence = max(time.time_ns(), previous + 1)
        target = folder / ('%020d-%s.backup' % (sequence, digest))
        os.replace(temporary, target)
        temporary = None
        directory_fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        # Remove old snapshots only after a verified replacement is durable.
        for old in sorted(p for p in folder.glob('*.backup')
                          if re.fullmatch(r'[0-9]{20}-[0-9a-f]{64}\.backup', p.name))[:-KEEP]:
            if old.is_file() and not old.is_symlink():
                old.unlink()
        return 'copied'
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run():
    if not (CONFIG / 'enabled').exists():
        return {'status': 'disabled'}
    try:
        first, second = card_info(OS_CARD), card_info(GAME_CARD)
        check_pair(first, second)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        return {'status': 'waiting-for-cards', 'reason': str(error)}
    counts = {'copied': 0, 'unchanged': 0, 'skipped': 0, 'space-reserve': 0, 'errors': 0}
    for source, destination in ((first, second), (second, first)):
        for path in candidates(source['path'] / 'roms'):
            if not (CONFIG / 'enabled').exists():
                return {'status': 'disabled', **counts}
            try:
                counts[snapshot(path, source, destination)] += 1
            except (ValueError, OSError) as error:
                counts['errors'] += 1
                print(json.dumps({'file': str(path), 'error': str(error)}), flush=True)
    return {'status': 'complete', **counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'status', 'enable', 'disable'])
    args = parser.parse_args()
    if args.command == 'status':
        print(json.dumps({'enabled': (CONFIG / 'enabled').exists(),
                          'last_run': json.loads((CONFIG / 'status.json').read_text())
                          if (CONFIG / 'status.json').exists() else None}))
        return
    CONFIG.mkdir(parents=True, exist_ok=True)
    if args.command in ('enable', 'disable'):
        if args.command == 'enable':
            (CONFIG / 'enabled').touch()
            # Re-arm the timer even when its previous boot-time run was skipped
            # while this opt-in setting was disabled.
            subprocess.run(['systemctl', 'restart', '--no-block',
                            'butterflyos-save-backup.timer'], check=True)
        else:
            (CONFIG / 'enabled').unlink(missing_ok=True)
        return
    with (CONFIG / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'status': 'busy'}))
            return
        result = dict(run(), time=int(time.time()))
        temporary = CONFIG / 'status.tmp'
        temporary.write_text(json.dumps(result) + '\n')
        os.replace(temporary, CONFIG / 'status.json')
        print(json.dumps(result))


if __name__ == '__main__':
    main()

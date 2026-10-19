#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Bdex Gen 1/2/3 storage. No bundled game data; imports and exports always copy."""
import fcntl
from contextlib import closing
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import tempfile
import time
import uuid

# Collection data belongs outside settings: resetting preferences must not erase it.
ROOT = Path('/storage/bdex')
CACHE_ROOT = Path('/storage/.config/butterflyos/save-trade/sprite-cache')
HELPER = Path('/usr/bin/butterflyos-save-trade')
SCHEMA_VERSION = 1


class BdexError(Exception):
    pass


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sync_directory(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def database_valid(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise BdexError('Database integrity check failed.')
        if connection.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
            raise BdexError('Unsupported Bdex database version.')
        for table in ('snapshots', 'pokemon', 'catalog', 'history'):
            connection.execute('SELECT * FROM ' + table + ' LIMIT 0')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise BdexError('Database contains broken source-snapshot references.')
        for digest, data in connection.execute('SELECT digest,data FROM snapshots'):
            if sha(data) != digest:
                raise BdexError('A source snapshot failed SHA-256 verification. Recover a database backup.')


def acquire_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (root / 'writer.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise BdexError('Bdex is already open. Close it before trying again.')
    return lock


def recover_database(root, backup):
    """Recover an explicitly selected checked database; retain the replaced file."""
    root, backup = Path(root), Path(backup).resolve()
    if backup.parent != (root / 'backups').resolve() or backup.is_symlink():
        raise BdexError('Choose a database from the Bdex backup directory.')
    lock = acquire_lock(root)
    temporary = root / ('recover-' + uuid.uuid4().hex + '.sqlite3')
    try:
        database_valid(backup)
        shutil.copyfile(backup, temporary)
        with temporary.open('rb') as stream:
            os.fsync(stream.fileno())
        database_valid(temporary)
        current = root / 'collection.sqlite3'
        if current.exists():
            quarantine = root / 'replaced-databases'
            quarantine.mkdir(exist_ok=True)
            # Copy first: the existing database remains in place until atomic replacement.
            retained = quarantine / (str(time.time_ns()) + '-' + uuid.uuid4().hex + '.sqlite3')
            shutil.copyfile(current, retained)
            with retained.open('rb') as stream:
                os.fsync(stream.fileno())
            # The retained copy is a recovery artifact, not a database to open automatically.
            sync_directory(quarantine)
            # A crash can leave hot SQLite sidecars. Never let an old journal
            # replay against the recovered database.
            for suffix in ('-journal', '-wal', '-shm'):
                sidecar = Path(str(current) + suffix)
                if sidecar.exists():
                    os.replace(sidecar, quarantine / (uuid.uuid4().hex + suffix))
            sync_directory(quarantine)
        os.replace(temporary, current)
        sync_directory(root)
    finally:
        temporary.unlink(missing_ok=True)
        lock.close()


class Store:
    def __init__(self, root=ROOT, generation=1):
        if generation not in (1, 2, 3):
            raise BdexError('Unsupported collection generation.')
        self.generation = generation
        self.root = Path(root)
        self.lock = acquire_lock(self.root)
        self.path = self.root / 'collection.sqlite3'
        self.connection = None
        try:
            existed = self.path.exists()
            if existed:
                database_valid(self.path)
            self.connection = sqlite3.connect(self.path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute('PRAGMA foreign_keys=ON')
            self.connection.execute('PRAGMA synchronous=FULL')
            self.connection.execute('PRAGMA journal_mode=DELETE')
            if not existed:
                self.connection.executescript('''
                    CREATE TABLE snapshots (digest TEXT PRIMARY KEY, data BLOB NOT NULL);
                    CREATE TABLE catalog (dex INTEGER PRIMARY KEY CHECK(dex BETWEEN 1 AND 386), name TEXT NOT NULL, internal INTEGER NOT NULL);
                    CREATE TABLE pokemon (
                      id INTEGER PRIMARY KEY, dex INTEGER NOT NULL CHECK(dex BETWEEN 1 AND 386),
                      snapshot TEXT NOT NULL REFERENCES snapshots(digest), source_key TEXT NOT NULL,
                      fingerprint TEXT NOT NULL, game TEXT NOT NULL, metadata TEXT NOT NULL, imported INTEGER NOT NULL,
                      trashed INTEGER);
                    CREATE INDEX pokemon_dex ON pokemon(dex, trashed);
                    CREATE INDEX pokemon_repeat ON pokemon(source_key, fingerprint);
                    CREATE TABLE history (id INTEGER PRIMARY KEY, pokemon INTEGER REFERENCES pokemon(id),
                      action TEXT NOT NULL, detail TEXT NOT NULL, created INTEGER NOT NULL);
                    PRAGMA user_version=1;
                ''')
                self.connection.commit()
                sync_directory(self.root)
            self.duplicates_removed = self.enforce_unique_records()
        except Exception:
            self.close()
            raise

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        if self.lock is not None:
            self.lock.close()
            self.lock = None

    def backup(self, manual=False):
        self.connection.commit()
        directory = self.root / 'backups'
        directory.mkdir(exist_ok=True)
        versions = [int(path.stem.split('-', 1)[1]) for path in directory.glob('*.sqlite3')
                    if re.fullmatch(r'(auto|manual)-[0-9]+\.sqlite3', path.name)]
        sequence = max(time.time_ns(), max(versions, default=0) + 1)
        name = ('manual-' if manual else 'auto-') + str(sequence) + '.sqlite3'
        target = directory / name
        pending = directory / ('.pending-' + name)
        try:
            with closing(sqlite3.connect(pending)) as destination:
                self.connection.backup(destination)
            database_valid(pending)
            with pending.open('rb') as stream:
                os.fsync(stream.fileno())
            os.replace(pending, target)
            sync_directory(directory)
        finally:
            pending.unlink(missing_ok=True)
        for old in sorted(directory.glob('auto-*.sqlite3'))[:-3]:
            old.unlink()
        return target

    def reconnect_cache(self, cache):
        """Reconnect artwork only for the exact verified source ROM, including Trash."""
        info = cache_info(cache)
        if info['generation'] != self.generation:
            raise BdexError('The ROM cache belongs to another generation.')
        updates, matched = [], 0
        for row in self.connection.execute('SELECT id,metadata FROM pokemon'):
            metadata = json.loads(row['metadata'])
            if metadata.get('rom_digest') != info['rom_digest'] or metadata.get('game') != info['game']:
                continue
            matched += 1
            if metadata.get('cache') != str(cache):
                metadata['cache'] = str(cache)
                updates.append((json.dumps(metadata), row['id']))
        if updates:
            self.backup()
            with self.connection:
                self.connection.executemany('UPDATE pokemon SET metadata=? WHERE id=?', updates)
        return matched, len(updates)

    def counts(self, game=None):
        query = 'SELECT dex, COUNT(*) AS n FROM pokemon WHERE trashed IS NULL'
        if game:
            query += ' AND game=?'
        return {row['dex']: row['n'] for row in self.connection.execute(query + ' GROUP BY dex', (game,) if game else ())}

    def names(self):
        return {row['dex']: row['name'] for row in self.connection.execute('SELECT dex,name FROM catalog')}

    def entries(self, dex=None, trash=False, game=None):
        query = 'SELECT * FROM pokemon WHERE trashed IS ' + ('NOT NULL' if trash else 'NULL')
        params = []
        if dex is not None:
            query += ' AND dex=?'
            params.append(dex)
        if game:
            query += ' AND game=?'
            params.append(game)
        rows = [dict(row) for row in self.connection.execute(query + ' ORDER BY id', params)]
        for row in rows:
            row['metadata'] = json.loads(row['metadata'])
        return rows

    def entry(self, ident):
        row = self.connection.execute('SELECT * FROM pokemon WHERE id=?', (ident,)).fetchone()
        if row is None:
            raise BdexError('Stored Pokemon not found.')
        result = dict(row)
        result['metadata'] = json.loads(result['metadata'])
        return result

    def repeated(self, record):
        return bool(self.connection.execute(
            'SELECT 1 FROM pokemon WHERE fingerprint=? LIMIT 1',
            (record['fingerprint'],)).fetchone())

    def enforce_unique_records(self):
        """Upgrade prototype databases without losing distinct native records."""
        groups = self.connection.execute(
            'SELECT fingerprint FROM pokemon GROUP BY fingerprint HAVING COUNT(*)>1').fetchall()
        removed = 0
        if groups:
            self.backup(manual=True)
        with self.connection:
            for group in groups:
                copies = self.connection.execute(
                    'SELECT id FROM pokemon WHERE fingerprint=? '
                    'ORDER BY (trashed IS NOT NULL), imported, id', (group[0],)).fetchall()
                keeper = copies[0]['id']
                for duplicate in copies[1:]:
                    self.connection.execute('UPDATE history SET pokemon=? WHERE pokemon=?',
                                            (keeper, duplicate['id']))
                    self.connection.execute('DELETE FROM pokemon WHERE id=?', (duplicate['id'],))
                    removed += 1
            if groups:
                self.connection.execute('DELETE FROM snapshots WHERE NOT EXISTS '
                                        '(SELECT 1 FROM pokemon WHERE snapshot=snapshots.digest)')
            self.connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS pokemon_native_unique ON pokemon(fingerprint)')
        return removed

    def import_selection(self, records):
        chosen, seen = [], set()
        for record in records:
            fingerprint = record['fingerprint']
            if fingerprint not in seen and not self.repeated(record):
                chosen.append(record)
            seen.add(fingerprint)
        return chosen

    def import_records(self, bundle, records):
        if bundle.get('generation', 1) != self.generation:
            raise BdexError('Choose the collection matching this save generation.')
        limit = {1: 151, 2: 251, 3: 386}[self.generation]
        if any(not 1 <= record['dex'] <= limit for record in records):
            raise BdexError('Species is outside this generation.')
        chosen = []
        valid = {r['key']: r for r in bundle['records']}
        for record in records:
            if record['key'] not in valid or record != valid[record['key']]:
                raise BdexError('Import selection does not match the inspected snapshot.')
        chosen = self.import_selection(records)
        if not chosen:
            return 0
        if sha(bundle['data']) != bundle['digest']:
            raise BdexError('Source snapshot integrity check failed.')
        self.backup()
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO snapshots VALUES (?,?)', (bundle['digest'], bundle['data']))
            for dex, name in bundle['names'].items():
                self.connection.execute('INSERT OR REPLACE INTO catalog VALUES (?,?,?)',
                    (int(dex), name, bundle['internal'][int(dex)]))
            for record in chosen:
                cursor = self.connection.execute('INSERT INTO pokemon(dex,snapshot,source_key,fingerprint,game,metadata,imported) VALUES (?,?,?,?,?,?,?)',
                    (record['dex'], bundle['digest'], record['source_key'], record['fingerprint'], record['game'], json.dumps(record), time.time_ns()))
                self.connection.execute('INSERT INTO history(pokemon,action,detail,created) VALUES (?,?,?,?)',
                    (cursor.lastrowid, 'import', record['source_path'], time.time_ns()))
        return len(chosen)

    def trash(self, ident, restore=False):
        self.entry(ident)
        self.backup()
        with self.connection:
            self.connection.execute('UPDATE pokemon SET trashed=? WHERE id=?', (None if restore else time.time_ns(), ident))
            self.connection.execute('INSERT INTO history(pokemon,action,detail,created) VALUES (?,?,?,?)',
                (ident, 'restore-trash' if restore else 'trash', '', time.time_ns()))

    def delete(self, ident):
        """Permanently remove one trashed copy; retain shared source snapshots."""
        entry = self.entry(ident)
        if entry['trashed'] is None:
            raise BdexError('Move this copy to Trash before deleting it permanently.')
        self.backup()
        with self.connection:
            self.connection.execute('DELETE FROM history WHERE pokemon=?', (ident,))
            self.connection.execute('DELETE FROM pokemon WHERE id=?', (ident,))
            self.connection.execute(
                'DELETE FROM snapshots WHERE digest=? AND NOT EXISTS '
                '(SELECT 1 FROM pokemon WHERE snapshot=?)',
                (entry['snapshot'], entry['snapshot']))

    def history(self, ident):
        return [dict(row) for row in self.connection.execute('SELECT * FROM history WHERE pokemon=? ORDER BY id', (ident,))]

    def snapshot(self, ident):
        entry = self.entry(ident)
        row = self.connection.execute('SELECT data FROM snapshots WHERE digest=?', (entry['snapshot'],)).fetchone()
        if row is None or sha(row['data']) != entry['snapshot']:
            raise BdexError('Stored source snapshot failed verification. Use database recovery.')
        return bytes(row['data'])


def decode_gen2_name(raw):
    output = []
    for byte in raw:
        if byte == 0x50:
            break
        if 0x80 <= byte <= 0x99:
            output.append(chr(byte - 0x80 + ord('A')))
        elif 0xa0 <= byte <= 0xb9:
            output.append(chr(byte - 0xa0 + ord('a')))
        elif byte >= 0xf6:
            output.append(chr(byte - 0xf6 + ord('0')))
        else:
            output.append({0x7f: ' ', 0xe0: "'", 0xe1: '<', 0xe2: '>', 0xe3: '-',
                           0xe6: '?', 0xe7: '!', 0xe8: '.', 0xea: 'é', 0xef: '♂', 0xf5: '♀',
                           0xf1: '×', 0xf3: '/', 0xf4: ',', 0x9a: '(', 0x9b: ')', 0x9c: ':', 0x9d: ';'}.get(byte, '?'))
    return ''.join(output).strip()


class Native:
    def __init__(self, helper=HELPER):
        self.helper = str(helper)

    def run(self, action, **arguments):
        command = [self.helper, action]
        for key, value in arguments.items():
            command += ['--' + key.replace('_', '-'), str(value)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise BdexError(result.stderr.strip() or 'The save helper rejected this file. A Bdex-enabled helper is required.')
        return result.stdout

    def inspect(self, path, generation=1):
        if generation == 2:
            return self.inspect_gen2(path)
        if generation == 3:
            return self.inspect_gen3(path)
        output = self.run('bdex-inspect-gen1', save=path)
        fields, details, records = {}, {}, []
        for line in output.splitlines():
            columns = line.split('\t')
            if len(columns) == 1 and '=' in line:
                key, value = line.split('=', 1)
                fields[key] = value
            elif columns[0] == 'party_record':
                details[('party', -1, int(columns[1]))] = columns[4]
            elif columns[0] == 'box_record':
                details[('box', int(columns[1]), int(columns[2]))] = columns[5]
            elif columns[0] == 'bdex_record':
                if len(columns) != 8:
                    raise BdexError('Unexpected native record format.')
                kind, box, slot = columns[1], int(columns[2]), int(columns[3])
                raw, ot, nickname = [bytes.fromhex(value) for value in columns[4:7]]
                if len(raw) != 33 or len(ot) != 11 or len(nickname) != 11:
                    raise BdexError('Invalid native Gen 1 record size.')
                if (kind, box, slot) not in details:
                    raise BdexError('Native record location mismatch.')
                dvs = int.from_bytes(raw[27:29], 'big')
                records.append({'kind': kind, 'box': box, 'slot': slot,
                    'key': '%s:%d:%d' % (kind, box, slot), 'species': raw[0],
                    'name': details[(kind, box, slot)], 'ot': columns[7], 'ot_id': int.from_bytes(raw[12:14], 'big'),
                    'level': raw[3], 'hp': int.from_bytes(raw[1:3], 'big'), 'status': raw[4],
                    'experience': int.from_bytes(raw[14:17], 'big'), 'moves': list(raw[8:12]),
                    'pp': [v & 63 for v in raw[29:33]], 'pp_ups': [v >> 6 for v in raw[29:33]],
                    'stat_exp': list(struct.unpack('>5H', raw[17:27])),
                    'dvs': [(dvs >> shift) & 15 for shift in (12, 8, 4, 0)],
                    'raw': raw.hex(), 'ot_raw': ot.hex(), 'nickname_raw': nickname.hex(),
                    'fingerprint': sha(raw + ot + nickname)})
        if fields.get('generation') != '1' or len(records) != len(details):
            raise BdexError('Expected a supported English Gen 1 save.')
        return fields, records

    def inspect_gen2(self, path):
        output = self.run('bdex-inspect-gen2', save=path)
        fields, details, records = {}, {}, []
        for line in output.splitlines():
            columns = line.split('\t')
            if len(columns) == 1 and '=' in line:
                key, value = line.split('=', 1)
                fields[key] = value
            elif columns[0] == 'party_record':
                details[('party', -1, int(columns[1]))] = columns[4]
            elif columns[0] == 'box_record':
                details[('box', int(columns[1]), int(columns[2]))] = columns[5]
            elif columns[0] == 'bdex_record':
                if len(columns) != 9:
                    raise BdexError('Unexpected Gen 2 native record format.')
                kind, box, slot = columns[1], int(columns[2]), int(columns[3])
                raw, ot, nickname = [bytes.fromhex(value) for value in columns[4:7]]
                if len(raw) != 32 or len(ot) != 11 or len(nickname) != 11 or columns[8] not in ('0', '1'):
                    raise BdexError('Invalid native Gen 2 record size or egg marker.')
                if (kind, box, slot) not in details:
                    raise BdexError('Native record location mismatch.')
                dvs = int.from_bytes(raw[21:23], 'big')
                values = [(dvs >> shift) & 15 for shift in (12, 8, 4, 0)]
                egg = columns[8] == '1'
                records.append({'kind': kind, 'box': box, 'slot': slot,
                    'key': '%s:%d:%d' % (kind, box, slot), 'species': raw[0],
                    'name': decode_gen2_name(nickname), 'ot': decode_gen2_name(ot), 'ot_id': int.from_bytes(raw[6:8], 'big'),
                    'level': raw[31], 'hp': None, 'status': None,
                    'experience': int.from_bytes(raw[8:11], 'big'), 'moves': list(raw[2:6]),
                    'pp': [v & 63 for v in raw[23:27]], 'pp_ups': [v >> 6 for v in raw[23:27]],
                    'stat_exp': list(struct.unpack('>5H', raw[11:21])), 'dvs': values,
                    'held_item': raw[1], 'friendship': raw[27], 'pokerus': raw[28],
                    'caught_data': int.from_bytes(raw[29:31], 'big'), 'egg': egg,
                    'shiny': values[1:] == [10, 10, 10] and values[0] in (2, 3, 6, 7, 10, 11, 14, 15),
                    'raw': raw.hex(), 'ot_raw': ot.hex(), 'nickname_raw': nickname.hex(),
                    'fingerprint': sha(raw + ot + nickname + bytes([egg]))})
        if fields.get('generation') != '2' or len(records) != len(details):
            raise BdexError('Expected a supported English Gen 2 save.')
        return fields, records

    def inspect_gen3(self, path):
        output = self.run('bdex-inspect-gen3', save=path)
        reader = load_module('bdex_native_gba_text', Path(__file__).with_name('butterflyos-gen3-sprite-cache.py'))
        fields, records, listed = {}, [], 0
        for line in output.splitlines():
            columns = line.split('\t')
            if len(columns) == 1 and '=' in line:
                key, value = line.split('=', 1)
                fields[key] = value
            elif columns[0] in ('party_record', 'box_record'):
                listed += 1
            elif columns[0] == 'bdex_record':
                if len(columns) != 8:
                    raise BdexError('Unexpected Gen 3 native record format.')
                kind, box, slot = columns[1], int(columns[2]), int(columns[3])
                raw = bytes.fromhex(columns[4])
                if len(raw) != 80 or raw[28:30] != b'\x00\x00':
                    raise BdexError('Invalid canonical Gen 3 record.')
                pid, trainer = struct.unpack_from('<II', raw)
                ivs = int.from_bytes(raw[72:76], 'little')
                origin = int.from_bytes(raw[70:72], 'little')
                records.append({'kind': kind, 'box': box, 'slot': slot,
                    'key': '%s:%d:%d' % (kind, box, slot), 'species': int.from_bytes(raw[32:34], 'little'),
                    'name': reader.decode_name(raw[8:18] + b'\xff') or columns[6],
                    'ot': reader.decode_name(raw[20:27] + b'\xff') or columns[5], 'ot_id': trainer & 65535, 'secret_id': trainer >> 16,
                    'personality': pid, 'level': None, 'hp': None, 'status': None,
                    'experience': int.from_bytes(raw[36:40], 'little'), 'moves': list(struct.unpack_from('<4H', raw, 44)),
                    'pp': list(raw[52:56]), 'pp_ups': [(raw[40] >> (index * 2)) & 3 for index in range(4)],
                    'evs': list(raw[56:62]), 'ivs': [(ivs >> (index * 5)) & 31 for index in range(6)],
                    'contest': list(raw[62:68]), 'held_item': int.from_bytes(raw[34:36], 'little'),
                    'friendship': raw[41], 'pokerus': raw[68], 'caught_data': origin, 'met_location': raw[69],
                    'origin_game': (origin >> 7) & 15, 'met_level': origin & 127, 'ball': (origin >> 11) & 15,
                    'egg': bool(ivs & (1 << 30)), 'ability_slot': 1 + (ivs >> 31), 'nature': columns[7],
                    'ribbons': int.from_bytes(raw[76:80], 'little'), 'language': int.from_bytes(raw[18:20], 'little') & 255,
                    'markings': raw[27], 'shiny': ((pid >> 16) ^ (pid & 65535) ^ (trainer >> 16) ^ (trainer & 65535)) < 8,
                    'raw': raw.hex(), 'fingerprint': sha(raw)})
        if fields.get('generation') != '3' or len(records) != listed:
            raise BdexError('Expected a supported Gen 3 save.')
        return fields, records


def read_stable(path):
    path = Path(path).resolve(strict=True)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        if before.st_size not in (32768, 32816, 65536, 131072):
            raise BdexError('Unexpected save size.')
        data = stream.read(131073)
        after = os.fstat(stream.fileno())
    signature = lambda s: (s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after) or signature(before) != signature(path.stat()):
        raise BdexError('The save changed while being read. Exit the game and try again.')
    return path, data


def game_running():
    for command in Path('/proc').glob('[0-9]*/comm'):
        try:
            if command.read_text().strip() in {'retroarch', 'retroarch32'}:
                return True
        except OSError:
            pass
    return False


def source_identity(path):
    """Include a physical card's UUID so swapping equal-looking saves is safe."""
    device = path.stat().st_dev
    device_id = '%d:%d' % (os.major(device), os.minor(device))
    try:
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            before, after = line.split(' - ', 1)
            fields, extra = before.split(), after.split()
            if fields[2] != device_id or not re.fullmatch(r'/dev/mmcblk[01]p[0-9]+', extra[1]):
                continue
            result = subprocess.run(['blkid', '-s', 'UUID', '-o', 'value', extra[1]],
                                    capture_output=True, text=True, timeout=5)
            identity = result.stdout.strip()
            if result.returncode == 0 and re.fullmatch(r'[A-Za-z0-9-]+', identity):
                return identity
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        pass
    return 'filesystem-' + device_id


def cache_info(cache):
    cache = Path(cache)
    manifest = json.loads((cache / 'manifest.json').read_text())
    names = json.loads((cache / 'names.json').read_text())
    generation = manifest.get('generation')
    if generation not in (1, 2, 3):
        raise BdexError('Prepare a verified English Gen 1, Gen 2 or Gen 3 ROM cache.')
    presets = load_module('bdex_supported_%d' % generation,
                          Path(__file__).with_name('butterflyos-gen%d-gift.py' % generation))
    digest = manifest.get('rom_content_sha256', manifest.get('rom_sha256'))
    supported = presets.ROM_PROFILES if generation == 3 else presets.SUPPORTED_ROMS
    if digest not in supported:
        raise BdexError('Prepare a cache from a verified English retail ROM. Gen 3: Emerald, Ruby/Sapphire rev 2, FireRed/LeafGreen rev 1.')
    limit = {1: 151, 2: 251, 3: 386}[generation]
    mapping = {int(k): int(v) for k, v in names.get('internal_to_national', {}).items()}
    labels = names.get('species', {})
    if set(mapping.values()) != set(range(1, limit + 1)) or len(mapping) != limit or set(map(int, labels)) != set(range(1, limit + 1)):
        raise BdexError('Update the shared sprite cache to include all species names.')
    if generation == 1:
        game = presets.SUPPORTED_ROMS[digest].split()[-1].lower()
    elif generation == 3:
        game = {1: 'sapphire', 2: 'ruby', 3: 'emerald', 4: 'firered', 5: 'leafgreen'}[supported[digest][1]]
    else:
        game = {'POKEMON_GLD': 'gold', 'POKEMON_SLV': 'silver', 'PM_CRYSTAL': 'crystal'}[presets.SUPPORTED_ROMS[digest]]
    return {'game': game, 'generation': generation, 'rom_digest': digest, 'mapping': mapping,
            'names': labels, 'internal': {v: k for k, v in mapping.items()}, 'moves': names.get('moves', {}),
            'items': names.get('items', {}), 'gender_ratios': names.get('gender_ratios', {}),
            'types': names.get('types', {}), 'type_names': names.get('type_names', {}),
            'growth_rates': names.get('growth_rates', {}), 'experience_tables': names.get('experience_tables', {})}


def import_bundle(native, path, cache):
    if game_running():
        raise BdexError('Exit the game before importing its save.')
    path, data = read_stable(path)
    info = cache_info(cache)
    with tempfile.TemporaryDirectory(prefix='bdex-inspect-') as temporary:
        snapshot = Path(temporary) / 'source.srm'
        snapshot.write_bytes(data)
        fields, records = native.inspect(snapshot, info['generation'])
    expected_family = {'red': 'Red/Blue', 'blue': 'Red/Blue', 'yellow': 'Yellow',
                       'gold': 'Gold/Silver', 'silver': 'Gold/Silver', 'crystal': 'Crystal',
                       'ruby': 'Ruby/Sapphire', 'sapphire': 'Ruby/Sapphire', 'emerald': 'Emerald',
                       'firered': 'FireRed/LeafGreen', 'leafgreen': 'FireRed/LeafGreen'}[info['game']]
    if fields['save_type'] != expected_family:
        raise BdexError('The selected ROM and save families do not match.')
    # Native fingerprints block exact repeats across saves, cards and slots.
    card_id = source_identity(path)
    source_key = sha((card_id + '\0' + str(path) + '\0' + fields.get('trainer_public_id', '') + '\0' +
                      fields.get('trainer_name', '') + '\0' + info['game']).encode())
    for record in records:
        dex = info['mapping'].get(record['species'])
        if dex is None:
            raise BdexError('Unsupported or glitch species in this save. No Pokemon were imported.')
        record.update(dex=dex, source_key=source_key + ':' + record['key'],
            source_path=str(path), game=info['game'], trainer=fields.get('trainer_name', ''),
            trainer_id=fields.get('trainer_public_id', ''), cache=str(Path(cache)),
            rom_digest=info['rom_digest'], source_card=card_id, generation=info['generation'])
        if info['generation'] in (2, 3):
            ratio = info['gender_ratios'].get(str(dex))
            if ratio is None:
                raise BdexError('Rebuild this ROM cache to read gender information.')
            value = record['dvs'][0] * 16 if info['generation'] == 2 else record['personality'] & 255
            record['gender'] = pokemon_gender(value, ratio)
        if info['generation'] == 3:
            rate = info['growth_rates'][str(dex)]
            thresholds = info['experience_tables'][str(rate)]
            record['level'] = max((level for level in range(1, 101) if record['experience'] >= thresholds[level]), default=1)
    return {'data': data, 'digest': sha(data), 'records': records, 'names': info['names'],
            'generation': info['generation'], 'internal': info['internal'], 'trainer': fields.get('trainer_name', ''), 'game': info['game']}


def pokemon_gender(value, ratio):
    return 'Genderless' if ratio == 255 else 'Female' if ratio == 254 or value < ratio else 'Male'


def migration_pid(record, ratio):
    raw = bytes.fromhex(record['raw'])
    value = 2166136261
    for byte in raw:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    base = (value ^ (record['dex'] * 0x9e3779b9)) & 0xffffffff or 1
    nature, tid = base % 25, record['ot_id']
    def matches(pid):
        shiny = ((pid >> 16) ^ (pid & 65535) ^ tid) < 8
        return shiny == record['shiny'] and pokemon_gender(pid & 255, ratio) == record['gender']
    if record['shiny']:
        for low in range(65536):
            for variant in range(8):
                pid = ((low ^ tid ^ variant) << 16) | low
                if pid % 25 == nature and matches(pid):
                    return pid
    else:
        for index in range(65536):
            pid = (base + index * 25) & 0xffffffff
            if matches(pid):
                return pid
    raise BdexError('Cannot preserve shiny status and gender for this destination species.')


def migration_blocks(record, held_item):
    evs = [(value * 255 + 32767) // 65535 for value in record['stat_exp']]
    evs.append(evs[-1])
    total = sum(evs)
    if total > 510:
        evs = [value * 510 // total for value in evs]
        remaining = 510 - sum(evs)
        for index in range(6):
            if remaining and 0 < evs[index] < 255:
                evs[index] += 1
                remaining -= 1
    attack, defense, speed, special = record['dvs']
    hp = ((attack & 1) << 3) | ((defense & 1) << 2) | ((speed & 1) << 1) | (special & 1)
    ivs = sum((dv * 2 + 1) << (index * 5) for index, dv in enumerate((hp, attack, defense, speed, special, special)))
    pp_ups = sum(record['pp_ups'][index] << (index * 2) for index, move in enumerate(record['moves']) if move <= 251)
    growth = struct.pack('<HHIBBH', record['dex'], held_item, record['experience'], pp_ups, record['friendship'], 0)
    attacks = struct.pack('<4H4B', *[move if move <= 251 else 0 for move in record['moves']],
                          *[pp if record['moves'][index] <= 251 else 0 for index, pp in enumerate(record['pp'])])
    misc = struct.pack('<BBHII', record['pokerus'], 0, 0, ivs, (1 << 31) if record['dex'] == 151 else 0)
    return growth + attacks + bytes(evs) + bytes(6) + misc


def time_capsule_item(catch_rate):
    if catch_rate == 0x19:
        return 0x92
    if catch_rate == 0x2d:
        return 0x53
    if catch_rate == 0x32:
        return 0xae
    if catch_rate in (0x5a, 0x64, 0x78, 0x87, 0xbe, 0xc3, 0xdc, 0xfa):
        return 0xad
    return catch_rate


def converted_gen2_raw(record, national):
    """Independent validation of the shared native Time Capsule conversion."""
    raw = bytes.fromhex(record['raw'])
    if len(raw) != 33 or not 1 <= national <= 151:
        raise BdexError('Invalid Gen 1 conversion source.')
    return (bytes((national, time_capsule_item(raw[7]))) + raw[8:12] + raw[12:14] +
            raw[14:29] + raw[29:33] + bytes((70, 0, 0, 0, raw[3])))


def export_copy(store, native, ident, destination, box, slot, destination_generation=None, destination_cache=None):
    """Prepare, validate and commit one append-only supported copy."""
    if game_running():
        raise BdexError('Exit the game before exporting into its save.')
    entry = store.entry(ident)
    if entry['trashed'] is not None:
        raise BdexError('Restore this Pokemon from Trash before exporting.')
    record = entry['metadata']
    generation = record.get('generation', 1)
    destination_generation = generation if destination_generation is None else destination_generation
    if (generation, destination_generation) not in ((1, 1), (1, 2), (2, 2), (2, 3), (3, 3)):
        raise BdexError('Choose the same generation or the next supported generation.')
    forward = (generation, destination_generation) == (1, 2)
    migrate = (generation, destination_generation) == (2, 3)
    pid, held_item = None, None
    if migrate:
        if record['egg']:
            raise BdexError('Hatch this Gen 2 egg in-game before copying it to Gen 3.')
        if len(record['ot']) > 7:
            raise BdexError('This original trainer name exceeds Gen 3 storage capacity.')
        if not destination_cache:
            raise BdexError('Choose a matching Gen 3 destination ROM.')
        info = cache_info(destination_cache)
        if info['generation'] != 3:
            raise BdexError('Choose a matching Gen 3 destination ROM.')
        pid = migration_pid(record, info['gender_ratios'][str(entry['dex'])])
        held_item = int(native.run('bdex-map-gen2-item', item=record['held_item']).strip())
    destination, original = read_stable(destination)
    sessions = store.root / 'exports'
    sessions.mkdir(exist_ok=True)
    session = sessions / uuid.uuid4().hex
    session.mkdir(mode=0o700)
    source, target, output = session / 'stored-source.srm', session / 'destination-input.srm', session / 'destination-output.srm'
    source.write_bytes(store.snapshot(ident))
    target.write_bytes(original)
    _, archived = native.inspect(source, generation)
    match = next((r for r in archived if r['key'] == record['key']), None)
    if match is None or match['fingerprint'] != record['fingerprint']:
        raise BdexError('Stored Pokemon does not match its immutable snapshot.')
    fields, before = native.inspect(target, destination_generation)
    if migrate:
        family = {'ruby': 'Ruby/Sapphire', 'sapphire': 'Ruby/Sapphire', 'emerald': 'Emerald',
                  'firered': 'FireRed/LeafGreen', 'leafgreen': 'FireRed/LeafGreen'}[info['game']]
        if fields['save_type'] != family:
            raise BdexError('The destination ROM and save families do not match.')
    capacity = 30 if destination_generation == 3 else 20
    occupied = {r['slot'] for r in before if r['kind'] == 'box' and r['box'] == box}
    next_slot = next((index for index in range(capacity) if index not in occupied), capacity)
    if box not in range(12 if destination_generation == 1 else 14) or slot != next_slot or slot >= capacity:
        raise BdexError('Choose the next empty slot in a box with space.')
    command = 'bdex-export-gen1-to-gen2' if forward else 'bdex-export-gen2-to-gen3' if migrate else 'bdex-export-gen%d' % generation
    extra = {'personality': pid} if migrate else {}
    native.run(command, source=source, source_kind=record['kind'],
        source_box=max(0, record['box']), source_slot=record['slot'], destination=target,
        destination_box=box, destination_slot=slot, national_species=entry['dex'], output_destination=output, **extra)
    _, after = native.inspect(output, destination_generation)
    added = next((r for r in after if r['kind'] == 'box' and r['box'] == box and r['slot'] == slot), None)
    if added is None or len(after) != len(before) + 1:
        raise BdexError('Export output did not add exactly one Pokemon.')
    if forward:
        if (bytes.fromhex(added['raw']) != converted_gen2_raw(record, entry['dex']) or
            added['name'] != record['name'] or added['ot'] != record['ot'] or added['egg']):
            raise BdexError('Converted output did not match the expected Time Capsule copy.')
    elif migrate:
        if (bytes.fromhex(added['raw'])[32:] != migration_blocks(record, held_item) or
            added['personality'] != pid or added['ot_id'] != record['ot_id'] or added['secret_id'] != 0 or
            added['name'].replace('’', "'") != record['name'].replace('’', "'") or
            added['ot'].replace('’', "'") != record['ot'].replace('’', "'") or added['egg'] or
            added['language'] != 2 or added['shiny'] != record['shiny']):
            raise BdexError('Converted output did not match the expected Gen 3 copy.')
    elif added['fingerprint'] != record['fingerprint']:
        raise BdexError('Export output did not preserve the archived native record.')
    prior = {r['key']: r['fingerprint'] for r in before}
    if any(r['key'] in prior and prior[r['key']] != r['fingerprint'] for r in after):
        raise BdexError('Export would change an existing Pokemon. No save was replaced.')
    if game_running() or sha(destination.read_bytes()) != sha(original):
        raise BdexError('Destination changed during preparation. Try again with the game closed.')
    # Save a durable recovery copy before replacing the original.
    backup = session / 'original-destination-backup.srm'
    with backup.open('xb') as stream:
        stream.write(original); stream.flush(); os.fsync(stream.fileno())
    sync_directory(session)
    store.backup()
    if game_running() or sha(read_stable(destination)[1]) != sha(original):
        raise BdexError('Destination changed before commit. No save was replaced.')
    blink = load_module('bdex_blink_commit', Path(__file__).with_name('butterflyos-save-trade-sdl.py'))
    receipt = {'pokemon': ident, 'source_generation': generation,
               'destination_generation': destination_generation, 'destination': str(destination), 'box': box + 1,
               'slot': slot + 1, 'backup': str(backup), 'state': 'prepared',
               'original_sha256': sha(original), 'output_sha256': sha(output.read_bytes())}
    def save_receipt():
        pending = session / '.receipt.pending'
        with pending.open('w') as stream:
            json.dump(receipt, stream, indent=2)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(pending, session / 'receipt.json')
        sync_directory(session)
    save_receipt()
    blink.replace_save_with_verified_output(str(destination), str(output), str(backup))
    receipt['state'] = 'committed'
    try:
        save_receipt()
        with store.connection:
            store.connection.execute('INSERT INTO history(pokemon,action,detail,created) VALUES (?,?,?,?)',
                (ident, 'export', json.dumps(receipt), time.time_ns()))
    except (OSError, sqlite3.Error) as error:
        # A history/log error after a verified commit must not invite a user to
        # repeat the export, creating an unintended second copy.
        print('Bdex export committed; history update failed: ' + str(error), flush=True)
    return backup

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Opt-in LAN collection viewer. All collection connections are read-only."""
import argparse
import base64
import hmac
import importlib.util
import json
import os
from pathlib import Path
import re
import ctypes
import threading
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

CONFIG = Path('/storage/.config/butterflyos/bdex-web.json')
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('bdex_web_engine', HERE / 'butterflyos-bdex.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def settings(path=CONFIG):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {'enabled': False}


def configure(enabled, path=CONFIG):
    path = Path(path)
    value = settings(path)
    value.pop('password', None)
    value['enabled'] = bool(enabled)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    return value


_CRYPT_LOCK = threading.Lock()
_CRYPT_LIBRARY = None


def verify_root_password(password, shadow_path=Path('/etc/shadow')):
    """Verify against the current root hash; never retain a plaintext password."""
    global _CRYPT_LIBRARY
    if not password or len(password.encode()) > 1024 or '\x00' in password:
        return False
    try:
        fields = next(line.split(':') for line in Path(shadow_path).read_text().splitlines()
                      if line.startswith('root:'))
        stored = fields[1]
        if not stored or stored.startswith(('!', '*')):
            return False
        with _CRYPT_LOCK:
            if _CRYPT_LIBRARY is None:
                for name in ('libcrypt.so.2', 'libcrypt.so.1', 'libcrypt.so'):
                    try:
                        library = ctypes.CDLL(name)
                        library.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
                        library.crypt.restype = ctypes.c_char_p
                        _CRYPT_LIBRARY = library
                        break
                    except (OSError, AttributeError):
                        continue
            if _CRYPT_LIBRARY is None:
                return False
            result = _CRYPT_LIBRARY.crypt(password.encode(), stored.encode())
            return bool(result) and hmac.compare_digest(result, stored.encode())
    except (OSError, ValueError, StopIteration, IndexError):
        return False


def authenticated(header, verifier=verify_root_password):
    try:
        scheme, encoded = header.split(' ', 1)
        if scheme.lower() != 'basic' or len(encoded) > 2048:
            return False
        username, password = base64.b64decode(encoded, validate=True).decode().split(':', 1)
        return username == 'bdex' and verifier(password)
    except (ValueError, UnicodeError):
        return False


class Collection:
    def __init__(self, root=engine.ROOT, cache_root=engine.CACHE_ROOT):
        self.root, self.cache_root = Path(root).resolve(), Path(cache_root).resolve()
        self.infos = {}

    def connect(self, generation):
        folder = self.root if generation == 1 else self.root / ('gen%d' % generation)
        path = folder / 'collection.sqlite3'
        if not path.exists():
            return None
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):
            raise ValueError('Invalid collection path')
        db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        if db.execute('PRAGMA user_version').fetchone()[0] != engine.SCHEMA_VERSION:
            db.close()
            raise ValueError('Unsupported collection version')
        return db

    def cache(self, path, generation):
        try:
            path = Path(path).resolve()
            if not path.is_relative_to(self.cache_root) or path == self.cache_root:
                return None
            stamp = (path / 'manifest.json').stat().st_mtime_ns
            key = (str(path), stamp)
            if key not in self.infos:
                self.infos[key] = engine.cache_info(path)
            info = self.infos[key]
            return (path, info) if info['generation'] == generation else None
        except (OSError, ValueError, KeyError, engine.BdexError):
            return None

    def fallback_cache(self, generation):
        for path in sorted(self.cache_root.glob('*')):
            result = self.cache(path, generation)
            if result:
                return result
        return None

    def record(self, row, generation):
        meta = json.loads(row['metadata'])
        allowed = ('name', 'ot', 'ot_id', 'secret_id', 'level', 'experience', 'shiny',
                   'egg', 'gender', 'nature', 'friendship', 'pokerus', 'ivs', 'evs',
                   'dvs', 'stat_exp', 'pp', 'pp_ups', 'met_level', 'origin_game',
                   'ball', 'ability_slot', 'imported')
        result = {key: meta[key] for key in allowed if key in meta}
        result.update(id=row['id'], dex=row['dex'], game=row['game'], imported=row['imported'] / 1_000_000_000)
        cache = self.cache(meta.get('cache', ''), generation)
        info = cache[1] if cache else {}
        result['moves'] = [info.get('moves', {}).get(str(move), 'Move #%d' % move)
                           for move in meta.get('moves', []) if move]
        item = meta.get('held_item', 0)
        result['held_item'] = info.get('items', {}).get(str(item), 'Item #%d' % item) if item else 'None'
        result['types'] = [info.get('type_names', {}).get(str(t), str(t))
                           for t in info.get('types', {}).get(str(row['dex']), [])]
        result['sprite'] = '/sprite/%d/%d' % (generation, row['id'])
        return result

    def collection(self, generation):
        limit = {1: 151, 2: 251, 3: 386}[generation]
        names, rows = {}, []
        db = self.connect(generation)
        if db:
            with closing(db):
                db.execute('BEGIN')
                names = dict(db.execute('SELECT dex,name FROM catalog'))
                rows = [self.record(row, generation) for row in db.execute(
                    'SELECT id,dex,game,metadata,imported FROM pokemon WHERE trashed IS NULL ORDER BY id')]
        fallback = self.fallback_cache(generation)
        if fallback:
            names.update({int(k): v for k, v in fallback[1]['names'].items()})
        counts = {}
        for row in rows:
            counts[row['dex']] = counts.get(row['dex'], 0) + 1
        return {'generation': generation, 'species': [
            {'dex': dex, 'name': names.get(dex, 'Species #%d' % dex), 'count': counts.get(dex, 0)}
            for dex in range(1, limit + 1)], 'copies': rows}

    def sprite(self, generation, ident):
        db = self.connect(generation)
        if not db:
            return None
        with closing(db):
            row = db.execute('SELECT dex,metadata FROM pokemon WHERE id=? AND trashed IS NULL', (ident,)).fetchone()
        if not row:
            return None
        meta = json.loads(row['metadata'])
        cache = self.cache(meta.get('cache', ''), generation)
        if not cache:
            return None
        folder, info = cache
        internal = info['internal'].get(row['dex'])
        if not internal:
            return None
        path = folder / ('front-shiny' if meta.get('shiny') else 'front') / ('%03d.png' % internal)
        resolved = path.resolve()
        if not resolved.is_relative_to(self.cache_root) or not resolved.is_relative_to(folder):
            return None
        if resolved.stat().st_size > 1024 * 1024:
            return None
        return resolved.read_bytes()


class Server(ThreadingHTTPServer):
    daemon_threads = True
    password_verifier = staticmethod(verify_root_password)
    request_queue_size = 8


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass  # URLs and authentication never go into device logs.

    def reply(self, status, data=b'', kind='text/plain; charset=utf-8', challenge=False):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        if challenge:
            self.send_header('WWW-Authenticate', 'Basic realm="Bdex collection", charset="UTF-8"')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def do_GET(self):
        config = settings(self.server.config_path)
        if not config.get('enabled'):
            return self.reply(503, b'Viewer disabled')
        if not authenticated(self.headers.get('Authorization', ''), self.server.password_verifier):
            return self.reply(401, b'Sign in as bdex using your root SSH password.', challenge=True)
        path = urlsplit(self.path).path
        try:
            if path in ('/', '/app.js', '/style.css', '/bdex.png'):
                name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/bdex.png': 'bdex.png'}[path]
                kind = {'/': 'text/html; charset=utf-8', '/app.js': 'text/javascript; charset=utf-8', '/style.css': 'text/css; charset=utf-8', '/bdex.png': 'image/png'}[path]
                return self.reply(200, (HERE / 'bdex-web' / name).read_bytes(), kind)
            match = re.fullmatch(r'/api/collection/([123])', path)
            if match:
                value = self.server.collection.collection(int(match[1]))
                return self.reply(200, json.dumps(value).encode(), 'application/json')
            match = re.fullmatch(r'/sprite/([123])/([1-9][0-9]{0,9})', path)
            if match:
                data = self.server.collection.sprite(int(match[1]), int(match[2]))
                return self.reply(200, data, 'image/png') if data else self.reply(404)
            return self.reply(404)
        except (OSError, ValueError, KeyError, sqlite3.Error, engine.BdexError):
            return self.reply(503, b'Collection temporarily unavailable. Refresh to try again.')

    def do_HEAD(self):
        self.do_GET()

    def reject_write(self):
        self.close_connection = True
        self.reply(405, b'Read-only viewer')

    do_POST = do_PUT = do_PATCH = do_DELETE = reject_write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8088)
    parser.add_argument('--config', type=Path, default=CONFIG)
    args = parser.parse_args()
    if not settings(args.config).get('enabled'):
        return 0
    server = Server(('0.0.0.0', args.port), Handler)
    server.config_path = args.config
    server.collection = Collection()
    server.serve_forever(poll_interval=1)


if __name__ == '__main__':
    main()

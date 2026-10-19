#!/usr/bin/env python3
"""HTTP auth, private-file boundaries and read-only SQLite regression checks."""
import base64
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

SOURCES = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'
spec = importlib.util.spec_from_file_location('web', SOURCES / 'butterflyos-bdex-web.py')
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / 'config.json'
        web.configure(True, path=self.config)
        self.password = '1111'
        self.accepted_password = '1111'
        self.database = self.root / 'collection.sqlite3'
        with sqlite3.connect(self.database) as db:
            db.executescript('PRAGMA user_version=1; CREATE TABLE catalog(dex,name); CREATE TABLE pokemon(id,dex,game,metadata,imported,trashed);')
            db.execute('INSERT INTO catalog VALUES (1,?)', ('<Bulbasaur>',))
            meta = {'name': '<script>alert(1)</script>', 'source_path': '/private/save.srm', 'raw': 'PRIVATE', 'moves': [10], 'ot': 'Trainer'}
            db.execute('INSERT INTO pokemon VALUES (1,1,?,?,?,NULL)', ('red', json.dumps(meta), 1000000000))
            db.execute('INSERT INTO pokemon VALUES (2,1,?,?,?,1)', ('red', json.dumps(meta), 1000000000))
        self.before = self.database.read_bytes()
        self.server = web.Server(('127.0.0.1', 0), web.Handler)
        self.server.config_path = self.config
        self.server.password_verifier = lambda password: password == self.accepted_password
        self.server.collection = web.Collection(self.root, self.root / 'cache')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.assertEqual(self.before, self.database.read_bytes())
        self.temp.cleanup()

    def request(self, path, method='GET', auth=True):
        conn = http.client.HTTPConnection(*self.server.server_address)
        headers = {'Authorization': 'Basic ' + base64.b64encode(('bdex:' + self.password).encode()).decode()} if auth else {}
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        result = response.status, response.read()
        conn.close()
        return result

    def test_authentication_covers_every_route(self):
        for path in ('/', '/app.js', '/style.css', '/bdex.png', '/api/collection/1', '/sprite/1/1'):
            self.assertEqual(401, self.request(path, auth=False)[0])
        self.password = 'wrong'
        self.assertEqual(401, self.request('/')[0])

    def test_collection_excludes_private_fields_and_trash(self):
        status, body = self.request('/api/collection/1')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(len(data['species']), 151)
        self.assertEqual(len(data['copies']), 1)
        self.assertEqual(data['copies'][0]['imported'], 1)
        self.assertNotIn(b'PRIVATE', body)
        self.assertNotIn(b'/private', body)
        self.assertNotIn(b'source_path', body)
        self.assertEqual(386, len(json.loads(self.request('/api/collection/3')[1])['species']))

    def test_write_methods_and_private_paths(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            self.assertEqual(405, self.request('/api/collection/1', method)[0])
        for path in ('/../config.json', '/%2e%2e/config.json', '/collection.sqlite3', '/snapshots', '/api/collection/4', '/sprite/1/../../config.json'):
            self.assertEqual(404, self.request(path)[0])

    def test_disabled_and_ssh_password_change(self):
        web.configure(False, path=self.config)
        self.assertEqual(503, self.request('/')[0])
        web.configure(True, path=self.config)
        self.accepted_password = 'new-ssh-password'
        self.assertEqual(401, self.request('/')[0])
        self.password = self.accepted_password
        self.assertEqual(200, self.request('/')[0])
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)
        self.assertNotIn('password', json.loads(self.config.read_text()))

    def test_symlink_and_read_only_connection(self):
        db = self.server.collection.connect(1)
        with self.assertRaises(sqlite3.OperationalError):
            db.execute('DELETE FROM pokemon')
        db.close()
        external = self.root / 'outside'
        external.mkdir()
        (external / 'manifest.json').write_text('{}')
        cache = self.root / 'cache'
        cache.mkdir()
        (cache / 'escape').symlink_to(external)
        self.assertIsNone(self.server.collection.cache(cache / 'escape', 1))

    def test_real_shadow_password_verification(self):
        import ctypes
        library = ctypes.CDLL('libcrypt.so.1')
        library.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        library.crypt.restype = ctypes.c_char_p
        hashed = library.crypt(b'actual-password', b'$6$bdex-test$').decode()
        shadow = self.root / 'shadow'
        shadow.write_text('root:' + hashed + ':0:0:99999:7:::\n')
        self.assertTrue(web.verify_root_password('actual-password', shadow))
        self.assertFalse(web.verify_root_password('wrong', shadow))
        self.assertFalse(web.verify_root_password('', shadow))
        shadow.write_text('root:!:0:0:99999:7:::\n')
        self.assertFalse(web.verify_root_password('actual-password', shadow))

    def test_browser_uses_safe_text_and_authenticated_assets(self):
        self.assertEqual(200, self.request('/style.css')[0])
        js = self.request('/app.js')[1]
        self.assertIn(b'textContent', js)
        self.assertNotIn(b'innerHTML', js)


if __name__ == '__main__':
    unittest.main()

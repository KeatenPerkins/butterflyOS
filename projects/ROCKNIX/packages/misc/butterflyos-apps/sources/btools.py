#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Signed app catalog and versioned, data-preserving tool installation."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ET
import shlex

MAX_CATALOG = 1024 * 1024
MAX_DOWNLOAD = 512 * 1024 * 1024
MAX_UNPACKED = 2 * 1024 * 1024 * 1024
IDENTIFIER = re.compile(r'[a-z][a-z0-9-]{0,47}')
TOKEN = re.compile(r'[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}-[0-9a-f]{16}(?:-[0-9a-f]{8})?')
VERSION = re.compile(r'[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}')
SHA256 = re.compile(r'[0-9a-f]{64}')


class AppError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise AppError(message)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate metadata field')
        result[key] = value
    return result


def read_json(data):
    try:
        return json.loads(data, object_pairs_hook=object_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (ValueError, TypeError) as error:
        raise AppError('Invalid app metadata') from error


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def lock(path, shared=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a') as stream:
        try:
            fcntl.flock(stream, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise AppError('Close the app and its web viewer before updating, or wait for the current download.') from error
        yield stream


def relative_path(value):
    require(isinstance(value, str) and value and '\\' not in value, 'Invalid package path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and '.' not in path.parts
            and str(path) == value, 'Unsafe package path')
    return path


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, validate):
        self.validate = validate

    def redirect_request(self, request, fp, code, message, headers, url):
        self.validate(url)
        return super().redirect_request(request, fp, code, message, headers, url)


class Manager:
    def __init__(self, root, profile, public_key, local_test=False, progress=None):
        self.progress = progress or (lambda message: None)
        self.root = Path(root)
        require(not self.root.is_symlink(), 'App storage must not be a symlink')
        self.root.mkdir(parents=True, exist_ok=True)
        self.profile, self.key, self.local_test = profile, Path(public_key), local_test
        require(isinstance(profile, dict), 'Invalid device profile')
        require(profile.get('api') == 1 and isinstance(profile.get('id'), str), 'Unsupported OS app API')
        self.state_path = self.root / 'state.json'

    def directory(self, *parts):
        path = self.root
        for part in parts:
            path = path / part
            require(not path.is_symlink(), 'App storage contains an unsafe directory link')
        return path

    def state(self):
        require(not self.state_path.is_symlink(), 'Installed-app state must not be a symlink')
        if not self.state_path.exists():
            return dict(schema=1, sequence=0, apps={})
        result = read_json(self.state_path.read_bytes())
        require(isinstance(result, dict) and result.get('schema') == 1 and
                type(result.get('sequence')) is int and result['sequence'] >= 0 and
                isinstance(result.get('apps'), dict), 'Invalid installed-app state')
        removed = result.get('removed', [])
        require(isinstance(removed, list) and all(isinstance(ident, str) and IDENTIFIER.fullmatch(ident) for ident in removed), 'Invalid removed-tool state')
        for ident, versions in result['apps'].items():
            require(IDENTIFIER.fullmatch(ident) and isinstance(versions, dict), 'Invalid installed app')
            for slot, item in versions.items():
                require(slot in ('current', 'previous'), 'Unknown installed-app slot')
                if item is not None:
                    require(isinstance(item, dict) and isinstance(item.get('token'), str) and
                            TOKEN.fullmatch(item['token']) and isinstance(item.get('version'), str) and
                            VERSION.fullmatch(item['version']), 'Invalid installed-app version')
        return result

    def url(self, value):
        parsed = urllib.parse.urlsplit(value)
        require(not parsed.username and not parsed.password and bool(parsed.hostname), 'Invalid download URL')
        require(parsed.scheme == 'https' or
                (self.local_test and parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', '::1')),
                'App downloads require HTTPS')

    def fetch(self, url, target, limit, expected=None):
        self.url(url)
        opener = urllib.request.build_opener(Redirects(self.url))
        count, digest = 0, hashlib.sha256()
        deadline = time.monotonic() + 1800
        request = urllib.request.Request(url, headers={'User-Agent': 'ButterflyOS-Tools/1'})
        with opener.open(request, timeout=20) as response, target.open('xb') as output:
            while True:
                require(time.monotonic() < deadline, 'Download timed out; please try again')
                block = response.read(min(1024 * 1024, limit + 1 - count))
                if not block:
                    break
                count += len(block)
                require(count <= limit, 'Download exceeds its declared size')
                digest.update(block)
                output.write(block)
                self.progress('Downloading: ' + str(min(100, count * 100 // limit)) + '%')
            output.flush()
            os.fsync(output.fileno())
        require(expected is None or digest.hexdigest() == expected, 'Download checksum failed')
        return count

    def authenticate(self, raw, signature):
        require(len(raw) <= MAX_CATALOG and len(signature) == 64, 'Invalid catalog size or signature')
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            data, sig = Path(temporary) / 'catalog', Path(temporary) / 'signature'
            data.write_bytes(raw)
            sig.write_bytes(signature)
            result = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey',
                                     str(self.key), '-rawin', '-in', str(data), '-sigfile', str(sig)],
                                    capture_output=True, timeout=10)
            require(result.returncode == 0, 'Catalog signature verification failed')
        catalog = read_json(raw)
        require(isinstance(catalog, dict), 'Invalid app catalog')
        require(catalog.get('schema') == 1 and type(catalog.get('sequence')) is int
                and catalog['sequence'] >= self.state()['sequence'], 'Catalog is unsupported or older than the last verified catalog')
        require(type(catalog.get('expires')) is int and type(catalog.get('created')) is int
                and catalog['created'] <= time.time() + 86400 and catalog['expires'] > time.time(),
                'Catalog expired or device clock is incorrect')
        apps = catalog.get('apps')
        require(isinstance(apps, list) and len(apps) <= 256, 'Invalid app catalog')
        seen = set()
        for app in apps:
            require(isinstance(app, dict), 'Invalid app entry')
            ident = app.get('id', '')
            require(isinstance(ident, str) and IDENTIFIER.fullmatch(ident) and ident not in seen, 'Invalid or duplicate app ID')
            seen.add(ident)
            require(isinstance(app.get('name'), str) and 0 < len(app['name']) <= 80
                    and isinstance(app.get('variants'), list), 'Invalid app entry')
            require(isinstance(app.get('version'), str) and VERSION.fullmatch(app['version']), 'Invalid app version')
        return catalog

    def refresh(self, url):
        with lock(self.root / 'operation.lock'), tempfile.TemporaryDirectory(dir=self.root) as temporary:
            raw, sig = Path(temporary) / 'catalog', Path(temporary) / 'signature'
            require(bool(url), 'Downloads are not published yet. Your installed tools remain available.')
            self.fetch(url, raw, MAX_CATALOG)
            self.fetch(url + '.sig', sig, 64)
            catalog = self.authenticate(raw.read_bytes(), sig.read_bytes())
            icons = self.directory('catalog-icons')
            icons.mkdir(exist_ok=True)
            for app in catalog['apps']:
                icon = app.get('icon')
                if not icon:
                    continue
                require(isinstance(icon, dict) and isinstance(icon.get('sha256'), str) and
                        SHA256.fullmatch(icon['sha256']) and type(icon.get('size')) is int and
                        0 < icon['size'] <= 2 * 1024 * 1024, 'Invalid catalog icon')
                cached = icons / (icon['sha256'] + '.png')
                if cached.is_file() and not cached.is_symlink() and file_digest(cached) == icon['sha256']:
                    continue
                target = Path(temporary) / (app['id'] + '.png')
                received = self.fetch(icon['url'], target, icon['size'], icon['sha256'])
                require(received == icon['size'], 'Incomplete catalog icon')
                os.replace(target, cached)
            state = self.state()
            state['sequence'] = catalog['sequence']
            atomic_json(self.state_path, state)
            # Advance the rollback floor before replacing the cached catalog.
            atomic_json(self.root / 'catalog.json', {'data': raw.read_text(), 'signature': sig.read_bytes().hex()})
        return catalog

    def catalog(self):
        require((self.root / 'catalog.json').is_file(), 'Refresh Downloads while connected to Wi-Fi first')
        envelope = read_json((self.root / 'catalog.json').read_bytes())
        try:
            signature = bytes.fromhex(envelope['signature'])
        except (KeyError, ValueError, TypeError) as error:
            raise AppError('Invalid cached catalog') from error
        return self.authenticate(envelope['data'].encode(), signature)

    def variant(self, app):
        matches = []
        for variant in app['variants']:
            require(isinstance(variant, dict), 'Invalid package requirements')
            platforms, arches = variant.get('platforms', []), variant.get('architectures', [])
            require(isinstance(platforms, list) and isinstance(arches, list) and
                    all(isinstance(value, str) for value in platforms + arches) and
                    isinstance(variant.get('requires', []), list) and
                    all(isinstance(value, str) for value in variant.get('requires', [])),
                    'Invalid package requirements')
            if self.profile['id'] not in platforms and '*' not in platforms:
                continue
            if self.profile.get('arch') not in arches and '*' not in arches:
                continue
            if variant.get('native', True) and ('*' in platforms or '*' in arches):
                continue
            if variant.get('api') != self.profile['api'] or not set(variant.get('requires', [])).issubset(self.profile.get('features', [])):
                continue
            require(isinstance(variant.get('sha256'), str) and SHA256.fullmatch(variant['sha256']) and
                    type(variant.get('size')) is int and 0 < variant['size'] <= MAX_DOWNLOAD and
                    type(variant.get('unpacked_size')) is int and 0 < variant['unpacked_size'] <= MAX_UNPACKED,
                    'Invalid app artifact')
            self.url(variant['url'])
            matches.append(variant)
        require(len(matches) == 1, 'No qualified package for this device, or ambiguous package requirements')
        return matches[0]

    def extract(self, archive, destination, app, variant):
        with zipfile.ZipFile(archive) as package:
            members = package.infolist()
            require(0 < len(members) <= 4096, 'Too many package files')
            require(sum(member.file_size for member in members) <= variant['unpacked_size'], 'Package expands beyond its declared size')
            seen = set()
            for member in members:
                relative_path(member.filename)
                require(member.filename not in seen and not member.is_dir() and
                        stat.S_IFMT(member.external_attr >> 16) in (0, stat.S_IFREG),
                        'Duplicate or non-regular package file')
                seen.add(member.filename)
            require('manifest.json' in seen and package.getinfo('manifest.json').file_size <= MAX_CATALOG, 'Missing package manifest')
            manifest = read_json(package.read('manifest.json'))
            require(isinstance(manifest, dict), 'Invalid package manifest')
            require(manifest.get('schema') == 1 and manifest.get('id') == app['id'] and
                    manifest.get('version') == app['version'] and manifest.get('api') == self.profile['api'] and
                    manifest.get('platform') in (self.profile['id'], '*' if not variant.get('native', True) else self.profile['id']), 'Package identity does not match catalog')
            files = manifest.get('files')
            require(isinstance(files, dict) and set(files) | {'manifest.json'} == seen, 'Package file list does not match manifest')
            require(manifest.get('kind') in ('python', 'binary') and manifest.get('entry') in files, 'Invalid app entry point')
            for name, metadata in files.items():
                require(isinstance(metadata, dict) and isinstance(metadata.get('sha256'), str) and SHA256.fullmatch(metadata['sha256']) and
                        metadata.get('mode') in (0o644, 0o755), 'Invalid file metadata')
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(name) as source, target.open('xb') as output:
                    digest = hashlib.sha256()
                    for block in iter(lambda: source.read(1024 * 1024), b''):
                        digest.update(block)
                        output.write(block)
                    output.flush()
                    os.fsync(output.fileno())
                require(digest.hexdigest() == metadata['sha256'], 'Package file checksum failed')
                target.chmod(metadata['mode'])
            atomic_json(destination / 'manifest.json', manifest)
            for folder in sorted((path for path in destination.rglob('*') if path.is_dir()), key=lambda path: len(path.parts), reverse=True):
                descriptor = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            return manifest

    def install(self, ident):
        require(IDENTIFIER.fullmatch(ident), 'Invalid app ID')
        with lock(self.root / 'operation.lock'), lock(self.directory('locks') / (ident + '.lock')):
            catalog = self.catalog()
            app = next((app for app in catalog['apps'] if app['id'] == ident), None)
            require(app is not None, 'App is not in the verified catalog')
            variant = self.variant(app)
            required = variant['size'] + variant['unpacked_size'] + 32 * 1024 * 1024
            require(shutil.disk_usage(self.root).free >= required, 'Not enough free space to download and safely install this app')
            token = app['version'] + '-' + variant['sha256'][:16]
            state = self.state()
            previous = state['apps'].get(ident, {}).get('current')
            if previous:
                require(tuple(map(int, app['version'].split('.'))) >= tuple(map(int, previous['version'].split('.'))),
                        'Use Roll Back to select an older installed version')
            parent = self.directory('store', ident)
            parent.mkdir(parents=True, exist_ok=True)
            destination = parent / token
            with tempfile.TemporaryDirectory(prefix='.install-', dir=parent) as temporary:
                temporary = Path(temporary)
                archive, unpack = temporary / 'download.zip', temporary / 'unpacked'
                unpack.mkdir()
                received = self.fetch(variant['url'], archive, variant['size'], variant['sha256'])
                require(received == variant['size'], 'Incomplete app download')
                self.progress('Verifying and unpacking app...')
                self.extract(archive, unpack, app, variant)
                if destination.exists():
                    token += '-' + os.urandom(4).hex()
                    destination = parent / token
                os.replace(unpack, destination)
                directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            state['removed'] = [value for value in state.get('removed', []) if value != ident]
            self.progress('Activating verified app...')
            state['apps'][ident] = dict(current={'token': token, 'version': app['version']}, previous=previous)
            atomic_json(self.state_path, state)
            self.collect(ident)
            self.sync(ident)

    def collect(self, ident):
        keep = {item['token'] for item in self.state()['apps'].get(ident, {}).values() if item}
        parent = self.directory('store', ident)
        if parent.is_dir():
            for path in parent.iterdir():
                if path.is_dir() and not path.is_symlink() and not path.name.startswith('.') and path.name not in keep:
                    shutil.rmtree(path)

    def change(self, ident, rollback=False):
        require(IDENTIFIER.fullmatch(ident), 'Invalid app ID')
        with lock(self.root / 'operation.lock'), lock(self.directory('locks') / (ident + '.lock')):
            state = self.state()
            current = state['apps'].get(ident, {})
            if rollback:
                require(current.get('previous'), 'No previous download is available')
                self.verify(ident, current['previous'])
                state['apps'][ident] = dict(current=current['previous'], previous=current.get('current'))
            else:
                state['apps'].pop(ident, None)
                state['removed'] = sorted(set(state.get('removed', [])) | {ident})
            atomic_json(self.state_path, state)
            self.collect(ident)
            self.sync(ident)

    def sync(self, ident):
        tools = self.profile.get('tools_directory')
        if not tools:
            return
        directory = Path(tools)
        directory.mkdir(parents=True, exist_ok=True)
        bundled = self.profile.get('bundled', {}).get(ident, {})
        launcher = {'blink': 'Blink.sh', 'bdex': 'Bdex.sh', 'bslap': 'Bslap.sh'}.get(ident, 'btools-' + ident + '.sh')
        item = self.state()['apps'].get(ident, {}).get('current')
        if not item and (not bundled or ident in self.state().get('removed', [])):
            (directory / launcher).unlink(missing_ok=True)
            gamelist = directory / 'gamelist.xml'
            if gamelist.exists():
                tree = ET.parse(gamelist)
                for game in list(tree.getroot().findall('game')):
                    if game.findtext('path') in ('./' + launcher, str(directory / launcher)):
                        tree.getroot().remove(game)
                self.write_gamelist(gamelist, tree)
            (directory / 'images' / ('btools-' + ident + '.png')).unlink(missing_ok=True)
            return
        command = self.profile.get('launcher_command', '/usr/bin/btools')
        target = directory / launcher
        fd, temporary = tempfile.mkstemp(prefix='.btools-', dir=directory)
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write('#!/bin/sh\n. /etc/profile\nexec ' + shlex.quote(command) + ' run ' + shlex.quote(ident) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o755)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
        if not item:
            return
        bundle, manifest = self.verify(ident, item)
        gamelist = directory / 'gamelist.xml'
        tree = ET.parse(gamelist) if gamelist.exists() else ET.ElementTree(ET.Element('gameList'))
        root = tree.getroot()
        game = next((game for game in root.findall('game') if game.findtext('path') == './' + launcher), None)
        if game is None:
            game = ET.SubElement(root, 'game')
            ET.SubElement(game, 'path').text = './' + launcher
        for key, value in [('name', manifest.get('name', ident)), ('desc', 'Downloaded ButterflyOS tool')]:
            element = game.find(key)
            if element is None:
                element = ET.SubElement(game, key)
            element.text = value
        if manifest.get('icon') in manifest['files']:
            icon = directory / 'images' / ('btools-' + ident + '.png')
            icon.parent.mkdir(exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='.btools-icon-', dir=icon.parent)
            try:
                with os.fdopen(fd, 'wb') as output, (bundle / manifest['icon']).open('rb') as source:
                    shutil.copyfileobj(source, output)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, icon)
            finally:
                Path(temporary).unlink(missing_ok=True)
            element = game.find('image')
            if element is None:
                element = ET.SubElement(game, 'image')
            element.text = './images/' + icon.name
        self.write_gamelist(gamelist, tree)

    @staticmethod
    def write_gamelist(gamelist, tree):
        fd, temporary = tempfile.mkstemp(prefix='.btools-gamelist-', dir=gamelist.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                tree.write(stream, encoding='utf-8', xml_declaration=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, gamelist)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def verify(self, ident, item):
        directory = self.directory('store', ident) / item['token']
        require(not directory.is_symlink(), 'Installed app directory is invalid')
        manifest = read_json((directory / 'manifest.json').read_bytes())
        require(manifest['id'] == ident and manifest['version'] == item['version'], 'Installed app identity is invalid')
        for name, metadata in manifest['files'].items():
            relative_path(name)
            path = directory / name
            require(not path.is_symlink() and directory.resolve() in path.resolve().parents and
                    file_digest(path) == metadata['sha256'], 'Installed app integrity check failed; reinstall or roll back')
        return directory, manifest

    def launch(self, ident, role=None):
        require(IDENTIFIER.fullmatch(ident), 'Invalid app ID')
        with lock(self.root / 'operation.lock', shared=True):
            state = self.state()
            if ident in state.get('removed', []):
                require(role == 'web', 'This tool was removed. Add it again from Add Tools.')
                return 0
            item = state['apps'].get(ident, {}).get('current')
            if role == 'web' and not item and ident not in self.profile.get('bundled', {}):
                return 0
            running = lock(self.directory('locks') / (ident + '.lock'), shared=True)
            held = running.__enter__()
        try:
            if item:
                directory, manifest = self.verify(ident, item)
                entry = manifest.get('services', {}).get(role) if role else manifest['entry']
                require(entry in manifest['files'], 'App service is not available')
                arguments = ([sys.executable] if manifest['kind'] == 'python' else []) + [str(directory / entry)]
                environment = dict(os.environ, BTOOLS_ROOT=str(directory), BTOOLS_PLATFORM=self.profile['id'],
                                   BTOOLS_LAYOUT=self.profile.get('layout', 'single'), BTOOLS_BIN=str(directory / 'bin'),
                                   BTOOLS_CONFIRM_BUTTON=str(self.profile.get('confirm_button', 1)),
                                   BTOOLS_CANCEL_BUTTON=str(self.profile.get('cancel_button', 0)), PYTHONDONTWRITEBYTECODE='1')
                for key, value in self.profile.get('window', {}).items():
                    require(key in ('x', 'y', 'width', 'height') and type(value) is int and 0 <= value <= 16384, 'Invalid device window geometry')
                    environment['BTOOLS_WINDOW_' + key.upper()] = str(value)
            else:
                bundled = self.profile.get('bundled', {}).get(ident, {})
                arguments = bundled.get('services', {}).get(role) if role else bundled.get('command')
                require(arguments and isinstance(arguments, list), 'This tool is not installed')
                environment = os.environ.copy()
            return subprocess.run(arguments, env=environment, pass_fds=(held.fileno(),)).returncode
        finally:
            running.__exit__(None, None, None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['list', 'refresh', 'install', 'remove', 'rollback', 'run', 'sync'])
    parser.add_argument('app', nargs='?')
    parser.add_argument('--role')
    parser.add_argument('--progress', action='store_true')
    parser.add_argument('--config', default='/usr/share/butterflyos/apps/config.json')
    args = parser.parse_args()
    try:
        config = read_json(Path(args.config).read_bytes())
        manager = Manager(config['root'], config['profile'], config['public_key'], config.get('local_test', False),
                          (lambda message: print(json.dumps({'progress': message}), flush=True)) if args.progress else None)
        if args.action == 'sync':
            with lock(manager.root / 'operation.lock'):
                for ident in set(manager.state()['apps']) | set(manager.profile.get('bundled', {})) | set(manager.state().get('removed', [])):
                    manager.sync(ident)
        elif args.action == 'refresh':
            manager.refresh(config['catalog_url'])
        elif args.action == 'install':
            manager.install(args.app)
        elif args.action in ('remove', 'rollback'):
            manager.change(args.app, args.action == 'rollback')
        elif args.action == 'run':
            return manager.launch(args.app, args.role)
        if args.action == 'list':
            result = dict(installed=manager.state()['apps'], bundled={ident: value for ident, value in manager.profile.get('bundled', {}).items() if ident not in manager.state().get('removed', [])}, apps=[], error='')
            try:
                for app in manager.catalog()['apps']:
                    app = dict(app)
                    icon = app.get('icon', {})
                    expected = icon.get('sha256', '') if isinstance(icon, dict) else ''
                    if isinstance(expected, str) and SHA256.fullmatch(expected):
                        cached = manager.directory('catalog-icons') / (expected + '.png')
                        if cached.is_file() and not cached.is_symlink() and file_digest(cached) == expected:
                            app['icon_path'] = str(cached)
                    try:
                        manager.variant(app)
                        app['compatible'] = True
                    except AppError as error:
                        app.update(compatible=False, reason=str(error))
                    result['apps'].append(app)
            except AppError as error:
                result['error'] = str(error)
            print(json.dumps(result))
        else:
            print(json.dumps({'ok': True}))
        return 0
    except urllib.error.HTTPError as error:
        print(json.dumps({'ok': False, 'error': f'The download server returned HTTP {error.code}. Try again later.'}))
        return 1
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        print(json.dumps({'ok': False, 'error': 'Cannot reach the tools feed. Connect to Wi-Fi or check your internet connection, then choose Refresh.'}))
        return 1
    except (AppError, OSError, KeyError, TypeError, ValueError, AttributeError, zipfile.BadZipFile, ET.ParseError, subprocess.SubprocessError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())

"""SD-card file operations with cancellation and recoverable deletion."""
import ctypes
import errno
import json
import os
from pathlib import Path
import shutil
import stat
import threading
import time
import uuid


class Cancelled(Exception):
    pass


def card_roots():
    roots = [('Games and saves', Path('/storage/roms')), ('OS card', Path('/storage'))]
    storage_device = os.stat('/storage').st_dev
    for line in Path('/proc/mounts').read_text().splitlines():
        fields = line.split()
        if len(fields) < 3 or not fields[0].startswith('/dev/mmcblk'):
            continue
        mount = Path(fields[1].replace('\\040', ' '))
        if not str(mount).startswith(('/var/media/', '/run/media/', '/media/', '/storage/')):
            continue
        if mount.is_dir() and mount.stat().st_dev != storage_device:
            if not any(root == mount for _, root in roots):
                roots.append(('Second SD card', mount))
    return [(name, root) for name, root in roots if root.is_dir()]


def signature(path):
    info = path.lstat()
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def publish(source, target):
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(target), 1):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(target))
    for parent in {source.parent, target.parent}:
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def free_name(parent, name):
    candidate = parent / name
    index = 2
    while os.path.lexists(candidate):
        item = Path(name)
        candidate = parent / f'{item.stem} ({index}){item.suffix}'
        index += 1
    return candidate


class Files:
    def __init__(self, roots):
        self.roots = [root.resolve() for _, root in roots]
        self.devices = {root: root.stat().st_dev for root in self.roots}
        self.cancel = threading.Event()
        self.busy = False
        self.message = 'Choose a card to browse.'
        self.bytes = 0
        self.revision = 0

    def check(self, path, change=False):
        path = Path(os.path.abspath(path))
        resolved = path.resolve()
        root = next((r for r in sorted(self.roots, key=lambda r: len(r.parts), reverse=True)
                     if resolved == r or r in resolved.parents), None)
        if root is None or root.stat().st_dev != self.devices[root]:
            raise ValueError('That card or folder is no longer available.')
        if path.is_symlink() or path != resolved:
            raise ValueError('Symbolic links are not supported in Files.')
        if change and resolved in self.roots:
            raise ValueError('A card or library root cannot be changed.')
        return resolved, root

    def entries(self, path):
        path, _ = self.check(path)
        with os.scandir(path) as items:
            result = [(entry.name, entry.is_dir(follow_symlinks=False))
                      for entry in items if not entry.name.startswith('.')]
        return sorted(result, key=lambda item: (not item[1], item[0].casefold()))

    def name(self, text):
        text = text.strip()
        if not text or text in ('.', '..') or any(c in text for c in '/\\\0') or text.startswith('.'):
            raise ValueError('Choose a visible name without slashes.')
        if any(ord(c) < 32 for c in text) or len(text.encode()) > 240:
            raise ValueError('That name is too long or contains control characters.')
        return text

    def start(self, function, *args):
        if self.busy:
            return
        self.busy = True
        self.bytes = 0
        self.cancel.clear()
        def work():
            try:
                self.message = function(*args)
            except Cancelled:
                self.message = 'Cancelled. Original files were kept.'
            except Exception as error:
                self.message = str(error)
            finally:
                self.busy = False
                self.revision += 1
        threading.Thread(target=work, daemon=True).start()

    def checkpoint(self, *paths):
        if self.cancel.is_set():
            raise Cancelled()
        for path in paths:
            self.check(path)

    def copy_tree(self, source, target, manifest):
        self.checkpoint(source, target.parent)
        info = source.lstat()
        manifest[source] = signature(source)
        if stat.S_ISDIR(info.st_mode):
            target.mkdir()
            for entry in source.iterdir():
                self.copy_tree(entry, target / entry.name, manifest)
        elif stat.S_ISREG(info.st_mode):
            descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, 'rb') as reader, target.open('xb') as writer:
                while True:
                    self.checkpoint(source, target.parent)
                    block = reader.read(1024 * 1024)
                    if not block:
                        break
                    writer.write(block)
                    self.bytes += len(block)
                    self.message = f'Copying {source.name} — {self.bytes / 1048576:.1f} MB'
                writer.flush()
                os.fsync(writer.fileno())
        else:
            raise ValueError('Links and special files cannot be copied.')
        if signature(source) != manifest[source]:
            raise ValueError('The source changed during copying. Original kept.')
        shutil.copystat(source, target, follow_symlinks=False)
        if target.is_dir():
            descriptor = os.open(target, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    def paste(self, source, folder, move=False):
        source, _ = self.check(source, change=move)
        folder, _ = self.check(folder)
        if source == folder or source in folder.parents:
            raise ValueError('Choose a destination outside the selected folder.')
        target = free_name(folder, source.name)
        if move and source.parent == folder:
            return 'That file is already here.'
        self.checkpoint(source, folder)
        if move and source.stat().st_dev == folder.stat().st_dev:
            publish(source, target)
            return 'Moved: ' + target.name
        staging = folder / ('.butterfly-copy-' + uuid.uuid4().hex)
        manifest = {}
        try:
            self.copy_tree(source, staging, manifest)
            self.checkpoint(source, folder)
            publish(staging, target)
        finally:
            if staging.is_dir():
                shutil.rmtree(staging)
            elif staging.exists():
                staging.unlink()
        if move:
            if any(signature(path) != saved for path, saved in manifest.items()):
                return 'Copied, but source changed. Both copies kept.'
            self.check(source, change=True)
            if source.is_dir():
                shutil.rmtree(source)
            else:
                source.unlink()
        return ('Moved: ' if move else 'Copied: ') + target.name

    def rename(self, source, text):
        source, _ = self.check(source, change=True)
        target = source.with_name(self.name(text))
        publish(source, target)
        return 'Renamed: ' + target.name

    def mkdir(self, folder, text):
        folder, _ = self.check(folder)
        (folder / self.name(text)).mkdir()
        return 'Folder created.'

    def trash(self, source):
        source, root = self.check(source, change=True)
        directory = root / '.butterflyos-trash' / uuid.uuid4().hex
        self.check(directory)
        directory.mkdir(parents=True)
        record = directory / 'restore.json'
        record.write_text(json.dumps({'original': str(source), 'name': source.name}))
        with record.open('rb') as stream:
            os.fsync(stream.fileno())
        publish(source, directory / source.name)
        return 'Moved to Trash. Use Restore last delete to undo.'

    def restore(self):
        records = []
        for root in self.roots:
            self.check(root)
            records += list((root / '.butterflyos-trash').glob('*/restore.json'))
        for record in sorted(records, key=lambda p: p.stat().st_mtime_ns, reverse=True):
            info = json.loads(record.read_text())
            name = self.name(info['name'])
            source, _ = self.check(record.parent / name, change=True)
            if source.parent != record.parent:
                raise ValueError('Invalid Trash record.')
            if not source.exists():
                continue
            target, _ = self.check(info['original'], change=True)
            self.check(target.parent)
            publish(source, free_name(target.parent, target.name))
            record.unlink()
            record.parent.rmdir()
            return 'Restored: ' + target.name
        return 'There are no deleted files to restore.'

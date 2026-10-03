#!/usr/bin/env python3
"""Offline update-package rejection tests; never touch device storage."""
import hashlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

path = Path(__file__).resolve().parents[1] / "projects/ROCKNIX/packages/rocknix/sources/scripts/butterflyos-update"
loader = importlib.machinery.SourceFileLoader("updater", str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
updater = importlib.util.module_from_spec(spec)
loader.exec_module(updater)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.identity = dict(schema=1, os="ButterflyOS", device="Miyoo_Flip_V2",
                             arch="aarch64", version="20261004")
        self.manifest = dict(self.identity, size=10240, unpacked_size=1, sha256="a" * 64,
                             url="https://github.com/KeatenPerkins/butterflyOS/releases/download/v1/test.tar")

    def archive(self, path, extra=None, corrupt=False):
        files = {"release/butterflyos-update.json": json.dumps(self.identity).encode()}
        for name in ("SYSTEM", "KERNEL"):
            raw = (name * 10).encode()
            files["release/target/" + name] = raw
            digest = "0" * 32 if corrupt else hashlib.md5(raw).hexdigest()
            files["release/target/" + name + ".md5"] = (digest + "  target/" + name + "\n").encode()
        if extra:
            files[extra] = b"unexpected"
        self.manifest["unpacked_size"] = sum(map(len, files.values()))
        with tarfile.open(path, "w") as archive:
            for name, raw in files.items():
                entry = tarfile.TarInfo(name)
                entry.size = len(raw)
                archive.addfile(entry, io.BytesIO(raw))

    def test_official_manifest(self):
        updater.validate_manifest(self.manifest)

    def test_wrong_device_and_unofficial_url(self):
        for change in ({"device": "Other"}, {"url": "http://example.com/file.tar"},
                       {"sha256": "bad"}, {"size": True}):
            with self.assertRaises(ValueError):
                updater.validate_manifest(dict(self.manifest, **change))

    def test_valid_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.tar"
            self.archive(path)
            updater.validate_archive(path, self.manifest)

    def test_unsafe_or_unexpected_archive(self):
        for extra in ("../escape", "/absolute", "release/target/extra", "release/script.sh"):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "test.tar"
                self.archive(path, extra=extra)
                with self.assertRaises(ValueError):
                    updater.validate_archive(path, self.manifest)

    def test_corrupt_internal_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.tar"
            self.archive(path, corrupt=True)
            with self.assertRaises(ValueError):
                updater.validate_archive(path, self.manifest)

    def test_stages_only_complete_verified_download(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "source.tar"
            self.archive(path)
            raw = path.read_bytes()
            self.manifest.update(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            with patch.object(updater, "STAGING", root / "staging"), \
                 patch.object(updater, "DOWNLOADS", root / "cache"), \
                 patch.object(updater, "check_battery"), \
                 patch.object(updater, "request", side_effect=lambda url: io.BytesIO(raw)), \
                 patch.object(updater.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)), \
                 patch.object(updater.os, "sync"):
                # Corrupted metadata must leave staging completely empty.
                with self.assertRaises(ValueError):
                    updater.stage(dict(self.manifest, sha256="0" * 64))
                self.assertEqual(list((root / "staging").iterdir()), [])
                self.assertFalse((root / "cache/download.part").exists())
                updater.stage(self.manifest)
                staged = root / "staging/ButterflyOS-20261004.tar"
                self.assertEqual(staged.read_bytes(), raw)
                with self.assertRaises(ValueError):
                    updater.stage(self.manifest)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Build a narrow, device-specific update archive from completed image outputs.

SPDX-License-Identifier: GPL-2.0-only
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", type=Path, required=True)
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--tag", required=True, help="GitHub release tag")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.tag):
        parser.error("Invalid release tag")
    def read_stamp(name):
        # Older squashfs-tools releases support extraction but not -cat.
        with tempfile.TemporaryDirectory(prefix="butterflyos-stamp-") as folder:
            destination = Path(folder) / "system"
            relative = "usr/share/butterflyos/" + name
            subprocess.run(["unsquashfs", "-no-progress", "-d", str(destination),
                            str(args.system), relative], check=True, stdout=subprocess.DEVNULL)
            return (destination / relative).read_text().strip()
    device = read_stamp("update-device")
    version = read_stamp("update-version")
    if device != "Miyoo_Flip_V2" or not re.fullmatch(r"20[0-9]{6}", version):
        parser.error("SYSTEM must contain matching Flip V2 updater identity and build date")
    identity = dict(schema=1, os="ButterflyOS", arch="aarch64", device=device, version=version)
    args.output.mkdir(parents=True, exist_ok=True)
    filename = "ButterflyOS-Miyoo-Flip-V2-" + version + ".tar"
    archive_path = args.output / filename
    if archive_path.exists() or (args.output / "butterflyos-update.json").exists():
        parser.error("Output already exists; choose a fresh output directory")
    root = "ButterflyOS-" + version
    unpacked_size = 0
    with tarfile.open(archive_path, "w") as archive:
        def add_bytes(name, raw):
            nonlocal unpacked_size
            entry = tarfile.TarInfo(root + "/" + name)
            entry.size = len(raw)
            entry.mode = 0o644
            archive.addfile(entry, io.BytesIO(raw))
            unpacked_size += len(raw)
        add_bytes("butterflyos-update.json", (json.dumps(identity) + "\n").encode())
        for name, source in (("SYSTEM", args.system), ("KERNEL", args.kernel)):
            entry = archive.gettarinfo(str(source), root + "/target/" + name)
            if not entry.isfile() or entry.size == 0:
                parser.error("SYSTEM and KERNEL must be nonempty regular files")
            with source.open("rb") as stream:
                archive.addfile(entry, stream)
            unpacked_size += entry.size
            digest = hashlib.md5()
            with source.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            add_bytes("target/" + name + ".md5", (digest.hexdigest() + "  target/" + name + "\n").encode())
    digest = hashlib.sha256()
    with archive_path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    manifest = dict(identity, size=archive_path.stat().st_size, unpacked_size=unpacked_size,
                    sha256=digest.hexdigest(),
                    url="https://github.com/KeatenPerkins/butterflyOS/releases/download/" + args.tag + "/" + filename)
    (args.output / "butterflyos-update.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.output / (filename + ".sha256")).write_text(digest.hexdigest() + "  " + filename + "\n")
    print("Upload the .tar, .sha256, and butterflyos-update.json to release " + args.tag)


if __name__ == "__main__":
    main()

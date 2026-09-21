#!/usr/bin/env python3
"""Loopback protocol and isolated-runtime test for experimental GBA linking."""

import json
import os
import pathlib
import socket
import subprocess
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-link-session"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    with tempfile.TemporaryDirectory(prefix="butterfly-gba-link-session-") as temporary:
        root = pathlib.Path(temporary)
        roms = root / "roms"
        roms.mkdir()
        ruby = roms / "Pokemon Ruby.gba"
        sapphire = roms / "Pokemon Sapphire.gba"
        ruby.write_bytes(b"RUBY-ROM" * 1024)
        sapphire.write_bytes(b"SAPPHIRE-ROM" * 1024)
        ruby_save = root / "ruby.srm"
        sapphire_save = root / "sapphire.srm"
        ruby_save.write_bytes(b"R" * 131072)
        sapphire_save.write_bytes(b"S" * 131072)

        command_log = root / "retroarch-command"
        fake_retroarch = root / "retroarch"
        fake_retroarch.write_text(
            "#!/bin/sh\n"
            "case \" $* \" in *' --command '*) exit 0;; esac\n"
            f"printf '%s\\n' \"$*\" >>'{command_log}'\n"
            "for arg in \"$@\"; do case \"$arg\" in --appendconfig=*) cfg=${arg#--appendconfig=};; esac; done\n"
            "content=$(sed -n 's/^savefile_directory = \"\\(.*\\)\"/\\1/p' \"$cfg\")\n"
            "case \" $* \" in\n"
            "  *' --host '*) sleep 1;;\n"
            "  *) mkdir -p \"$content/.netplay\"; cp \"$content/player2.srm\" \"$content/.netplay/player2.srm\"; sleep 2;;\n"
            "esac\n",
            encoding="utf-8",
        )
        fake_retroarch.chmod(0o755)
        core = root / "mgba-link.so"
        core.write_bytes(b"test-gba-core")
        port = free_port()
        common = os.environ.copy()
        common.update(
            {
                "BUTTERFLY_LINK_ROM_ROOTS": str(roms),
                "BUTTERFLY_LINK_SESSION_PORT": str(port),
                "BUTTERFLY_LINK_RETROARCH": str(fake_retroarch),
                "BUTTERFLY_LINK_GBA_CORE": str(core),
                "BUTTERFLY_LINK_ANNOUNCEMENT": str(root / "announcement.json"),
                "BUTTERFLY_LINK_HEADLESS": "1",
            }
        )
        host_env = dict(common, BUTTERFLY_LINK_STATE_ROOT=str(root / "host"))
        join_env = dict(common, BUTTERFLY_LINK_STATE_ROOT=str(root / "join"))
        host = subprocess.Popen(
            [str(TOOL), "host", "--session", "gba-host", "--rom", str(ruby), "--save", str(ruby_save), "--timeout", "15"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=host_env,
        )
        announcement = root / "announcement.json"
        for _ in range(100):
            if announcement.exists():
                break
            time.sleep(0.03)
        else:
            raise AssertionError("host announcement was not created")
        metadata = json.loads(announcement.read_text(encoding="utf-8"))
        assert metadata["rom"]["system"] == "gba"
        join = subprocess.run(
            [str(TOOL), "join", "--peer", "127.0.0.1", "--port", str(port), "--token", metadata["token"],
             "--session", "gba-join", "--rom", str(sapphire), "--save", str(sapphire_save)],
            capture_output=True,
            text=True,
            env=join_env,
            timeout=20,
        )
        host_stdout, host_stderr = host.communicate(timeout=20)
        assert host.returncode == 0, host_stderr
        assert join.returncode == 0, (join.stdout, join.stderr)
        commands = command_log.read_text(encoding="utf-8")
        assert "--subsystem=gbalink" in commands
        assert str(core) in commands
        assert 'butterfly_gba_link_player = "1"' in (root / "host/sessions/gba-host/runtime/mgba-link.opt").read_text()
        assert 'butterfly_gba_link_player = "2"' in (root / "join/sessions/gba-join/runtime/mgba-link.opt").read_text()
        assert 'video_driver = "null"' in (root / "host/sessions/gba-host/runtime/retroarch.cfg").read_text()
        assert "result_save=" in host_stdout
        assert "result_save=" in join.stdout
        assert not announcement.exists()
        print("Butterfly Link GBA session protocol test passed")


if __name__ == "__main__":
    main()

#!/usr/bin/python3
"""Loopback protocol test for Butterfly Link save exchange and launch setup."""

import hashlib
import os
import pathlib
import socket
import subprocess
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-link-session"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    with tempfile.TemporaryDirectory(prefix="butterfly-link-session-") as temporary:
        root = pathlib.Path(temporary)
        roms = root / "roms"
        roms.mkdir()
        red = roms / "Pokemon Red.gb"
        blue = roms / "Pokemon Blue.gb"
        red.write_bytes(b"RED-ROM" * 1024)
        blue.write_bytes(b"BLUE-ROM" * 1024)
        red_save = root / "red.srm"
        blue_save = root / "blue.srm"
        red_save.write_bytes(b"R" * 32768)
        blue_save.write_bytes(b"B" * 32768)
        fake_retroarch = root / "retroarch"
        fake_retroarch.write_text(
            "#!/bin/sh\n"
            "trap 'exit 0' INT TERM\n"
            "case \" $* \" in\n"
            "  *' --command '*) exit 0;;\n"
            "  *' --host '*) sleep 1;;\n"
            "  *)\n"
            "    for arg in \"$@\"; do case \"$arg\" in --appendconfig=*) cfg=${arg#--appendconfig=};; esac; done\n"
            "    content=$(sed -n 's/^savefile_directory = \"\\(.*\\)\"/\\1/p' \"$cfg\")\n"
            "    mkdir -p \"$content/.netplay\"\n"
            "    cp \"$content/player2.srm\" \"$content/.netplay/player2.srm\"\n"
            "    printf N | dd of=\"$content/.netplay/player2.srm\" bs=1 seek=0 conv=notrunc 2>/dev/null\n"
            "    sleep 10;;\n"
            "esac\n",
            encoding="utf-8",
        )
        fake_retroarch.chmod(0o755)
        core = root / "sameboy.so"
        core.write_bytes(b"test-core")
        port = free_port()
        common = os.environ.copy()
        common.update(
            {
                "BUTTERFLY_LINK_ROM_ROOTS": str(roms),
                "BUTTERFLY_LINK_SESSION_PORT": str(port),
                "BUTTERFLY_LINK_RETROARCH": str(fake_retroarch),
                "BUTTERFLY_LINK_CORE": str(core),
                "BUTTERFLY_LINK_ANNOUNCEMENT": str(root / "announcement.json"),
                "BUTTERFLY_LINK_BUFFERED_DEMO": "1",
            }
        )
        host_env = dict(common, BUTTERFLY_LINK_STATE_ROOT=str(root / "host"))
        join_env = dict(common, BUTTERFLY_LINK_STATE_ROOT=str(root / "join"))
        token = "0123456789abcdef0123456789abcdef"

        # Override secrets only through the generated announcement: read the
        # host token before starting the client, as the discovery agent does.
        host = subprocess.Popen(
            [str(TOOL), "host", "--session", "host-session", "--rom", str(red), "--save", str(red_save), "--timeout", "15"],
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
        import json
        token = json.loads(announcement.read_text(encoding="utf-8"))["token"]
        join = subprocess.run(
            [str(TOOL), "join", "--peer", "127.0.0.1", "--port", str(port), "--token", token, "--session", "join-session", "--rom", str(blue), "--save", str(blue_save)],
            capture_output=True,
            text=True,
            env=join_env,
            timeout=20,
        )
        host_stdout, host_stderr = host.communicate(timeout=20)
        assert host.returncode == 0, host_stderr
        assert join.returncode == 0, (join.returncode, join.stdout, join.stderr)
        host_result = root / "host/sessions/host-session/runtime/content/player1.srm"
        join_result = root / "join/sessions/join-session/runtime/content/.netplay/player2.srm"
        assert digest(host_result) == digest(red_save)
        assert digest(join_result) != digest(blue_save)
        assert "result_save=" in host_stdout
        assert "result_save=" in join.stdout
        assert "/.netplay/player2.srm" in join.stdout
        assert not announcement.exists()
        print("Butterfly Link session protocol test passed")


if __name__ == "__main__":
    main()

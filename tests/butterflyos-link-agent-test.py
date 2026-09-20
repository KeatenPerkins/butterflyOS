#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-link-agent"
UDP_PORT = 45110
TCP_PORT = 45111


def wait_for_server(process):
    for _ in range(40):
        if process.poll() is not None:
            raise RuntimeError("agent exited before accepting connections")
        try:
            with socket.create_connection(("127.0.0.1", TCP_PORT), timeout=0.1):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("agent did not open its control port")


def main():
    with tempfile.TemporaryDirectory(prefix="butterfly-link-agent-test.") as temporary:
        core = Path(temporary) / "sameboy.so"
        core.write_bytes(b"sameboy-test-core")
        environment = os.environ.copy()
        environment.update(
            {
                "BUTTERFLY_LINK_DISCOVERY_PORT": str(UDP_PORT),
                "BUTTERFLY_LINK_CONTROL_PORT": str(TCP_PORT),
                "BUTTERFLY_LINK_CORE": str(core),
            }
        )
        process = subprocess.Popen(
            [sys.executable, str(AGENT), "serve"],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            wait_for_server(process)

            probe = subprocess.run(
                [sys.executable, str(AGENT), "probe", "127.0.0.1", "--port", str(TCP_PORT)],
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            assert "compatible=yes" in probe.stdout
            assert "protocol=1" in probe.stdout

            nonce = "test-nonce"
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.settimeout(2)
            udp.sendto(
                f"BUTTERFLY_LINK_DISCOVER 1 {nonce}".encode(),
                ("127.0.0.1", UDP_PORT),
            )
            response, _ = udp.recvfrom(4096)
            payload = json.loads(response)
            assert payload["ok"] is True
            assert payload["nonce"] == nonce
            assert payload["protocol"] == 1
            udp.close()

            with socket.create_connection(("127.0.0.1", TCP_PORT), timeout=2) as connection:
                connection.sendall(b'{"action":"write"}\n')
                invalid = json.loads(connection.makefile("rb").readline())
            assert invalid == {"error": "unsupported-action", "ok": False}
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

    print("PASS: Butterfly Link agent tests")


if __name__ == "__main__":
    main()

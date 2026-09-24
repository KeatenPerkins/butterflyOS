#!/usr/bin/python3
"""Offline loopback harness for the one-core Butterfly Link transport.

This intentionally does not start RetroArch. It validates the transport and
transfer ordering that the eventual mGBA driver will use, without touching
ROMs, saves, or device networking.
"""

import argparse
import importlib.util
import pathlib
import socket
import threading


_protocol_path = pathlib.Path(__file__).with_name("butterflyos-link-protocol.py")
_spec = importlib.util.spec_from_file_location("butterflyos_link_protocol", _protocol_path)
_protocol = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_protocol)


def _peer(connection, received):
    header, payload = _protocol.receive_event(connection)
    received.append((header, payload))
    _protocol.send_event(
        connection,
        header["session"],
        header["sequence"],
        header["timestamp"],
        "transfer-complete",
        payload,
    )


def run():
    left, right = socket.socketpair()
    received = []
    worker = threading.Thread(target=_peer, args=(right, received), daemon=True)
    worker.start()
    _protocol.send_event(left, "loopback", 0, 1000, "serial-write", b"\x34\x12")
    response, payload = _protocol.receive_event(left)
    worker.join(timeout=1)
    if response["type"] != "transfer-complete" or payload != b"\x34\x12":
        raise RuntimeError("loopback-transfer-mismatch")
    if len(received) != 1 or received[0][1] != b"\x34\x12":
        raise RuntimeError("loopback-peer-did-not-receive")
    left.close()
    right.close()
    print("loopback-transfer=ok")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run()

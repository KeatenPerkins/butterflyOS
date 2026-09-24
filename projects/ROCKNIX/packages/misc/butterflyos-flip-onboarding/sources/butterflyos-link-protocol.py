#!/usr/bin/python3
"""Transport-neutral Butterfly Link event framing.

This module deliberately has no RetroArch or socket policy.  It provides the
small, bounded packet format used by the future one-core-per-device adapter.
The existing protocol-1 session launcher does not import it yet.
"""

import hashlib
import json
import struct
import zlib

PROTOCOL = 2
MAX_HEADER = 4096
MAX_PAYLOAD = 4096
EVENT_TYPES = frozenset(("mode", "serial-write", "serial-read", "transfer-complete", "disconnect"))


class ProtocolError(ValueError):
    pass


def encode_event(session, sequence, timestamp, event_type, payload=b""):
    if not isinstance(session, str) or not session or len(session) > 128:
        raise ProtocolError("invalid-session")
    if not isinstance(sequence, int) or sequence < 0:
        raise ProtocolError("invalid-sequence")
    if not isinstance(timestamp, int) or timestamp < 0:
        raise ProtocolError("invalid-timestamp")
    if event_type not in EVENT_TYPES:
        raise ProtocolError("invalid-event-type")
    if not isinstance(payload, bytes) or len(payload) > MAX_PAYLOAD:
        raise ProtocolError("event-payload-too-large")
    header = {
        "protocol": PROTOCOL,
        "session": session,
        "sequence": sequence,
        "timestamp": timestamp,
        "type": event_type,
        "payload_size": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
    }
    encoded = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("ascii")
    if len(encoded) > MAX_HEADER:
        raise ProtocolError("event-header-too-large")
    checksum = zlib.crc32(encoded)
    checksum = zlib.crc32(payload, checksum) & 0xFFFFFFFF
    return struct.pack("!II", len(encoded), checksum) + encoded + payload


def _receive_exact(connection, length):
    chunks = []
    while length:
        block = connection.recv(length)
        if not block:
            raise ProtocolError("peer-disconnected")
        chunks.append(block)
        length -= len(block)
    return b"".join(chunks)


def decode_event(frame):
    if not isinstance(frame, bytes) or len(frame) < 8:
        raise ProtocolError("truncated-event")
    header_size, expected_checksum = struct.unpack("!II", frame[:8])
    if header_size < 2 or header_size > MAX_HEADER:
        raise ProtocolError("invalid-header-size")
    try:
        header = json.loads(frame[8:8 + header_size].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError("invalid-header") from error
    payload = frame[8 + header_size:]
    if header.get("protocol") != PROTOCOL:
        raise ProtocolError("unsupported-protocol")
    if header.get("payload_size") != len(payload) or len(payload) > MAX_PAYLOAD:
        raise ProtocolError("invalid-payload-size")
    if hashlib.sha256(payload).hexdigest() != header.get("payload_sha256"):
        raise ProtocolError("payload-checksum-failed")
    actual_checksum = zlib.crc32(frame[8:8 + header_size])
    actual_checksum = zlib.crc32(payload, actual_checksum) & 0xFFFFFFFF
    if actual_checksum != expected_checksum:
        raise ProtocolError("frame-checksum-failed")
    if header.get("type") not in EVENT_TYPES or not isinstance(header.get("sequence"), int):
        raise ProtocolError("invalid-event")
    return header, payload


def send_event(connection, *args, **kwargs):
    connection.sendall(encode_event(*args, **kwargs))


def receive_event(connection):
    prefix = _receive_exact(connection, 8)
    header_size = struct.unpack("!I", prefix[:4])[0]
    if header_size < 2 or header_size > MAX_HEADER:
        raise ProtocolError("invalid-header-size")
    body = _receive_exact(connection, header_size)
    header = json.loads(body.decode("ascii"))
    payload_size = header.get("payload_size")
    if not isinstance(payload_size, int) or payload_size < 0 or payload_size > MAX_PAYLOAD:
        raise ProtocolError("invalid-payload-size")
    return decode_event(prefix + body + _receive_exact(connection, payload_size))


class SequenceGuard:
    """Accept each event once and report the next missing sequence number."""

    def __init__(self):
        self.next_sequence = 0

    def accept(self, header):
        sequence = header.get("sequence")
        if sequence < self.next_sequence:
            return False
        if sequence > self.next_sequence:
            raise ProtocolError("event-sequence-gap")
        self.next_sequence += 1
        return True

#!/usr/bin/env python3
"""Offline safety tests for the experimental Butterfly Link buffered protocol."""

import binascii
import socket
import struct


MAGIC = b"BLBF"
VERSION = 1
HEADER = struct.Struct("!4sBBBBIHHI")


def encode(generation, flags, transaction, step, payload):
    payload = bytes(payload)
    head = HEADER.pack(MAGIC, VERSION, generation, flags, 0, transaction,
                       step, len(payload), 0)
    crc = binascii.crc32(head[:-4] + payload) & 0xFFFFFFFF
    return head[:-4] + struct.pack("!I", crc) + payload


def decode(frame):
    if len(frame) < HEADER.size:
        raise ValueError("truncated frame")
    magic, version, generation, flags, reserved, transaction, step, length, crc = HEADER.unpack(
        frame[:HEADER.size])
    payload = frame[HEADER.size:]
    if magic != MAGIC or version != VERSION or reserved != 0:
        raise ValueError("invalid header")
    if length != len(payload):
        raise ValueError("invalid payload length")
    expected = binascii.crc32(frame[:HEADER.size - 4] + payload) & 0xFFFFFFFF
    if crc != expected:
        raise ValueError("invalid checksum")
    return generation, flags, transaction, step, payload


def recv_frame(sock):
    header = b""
    while len(header) < HEADER.size:
        part = sock.recv(HEADER.size - len(header))
        if not part:
            raise ConnectionError("peer closed before frame header")
        header += part
    length = HEADER.unpack(header)[7]
    payload = b""
    while len(payload) < length:
        part = sock.recv(length - len(payload))
        if not part:
            raise ConnectionError("peer closed before frame payload")
        payload += part
    return header + payload


class Receiver:
    def __init__(self):
        self.transaction = None
        self.step = -1
        self.committed = False

    def accept(self, frame):
        generation, flags, transaction, step, payload = decode(frame)
        if generation not in (1, 2):
            raise ValueError("unsupported generation")
        if self.transaction is None:
            self.transaction = transaction
        if transaction != self.transaction or step < self.step:
            raise ValueError("stale or mismatched transaction")
        if step == self.step and self.step >= 0:
            return "duplicate"
        self.step = step
        if flags & 1:
            self.committed = True
        return payload


def main():
    frame = encode(2, 0, 7, 0, b"prepared-trade")
    assert decode(frame)[-1] == b"prepared-trade"

    receiver = Receiver()
    assert receiver.accept(frame) == b"prepared-trade"
    assert receiver.accept(frame) == "duplicate"

    commit = encode(2, 1, 7, 1, b"commit")
    assert receiver.accept(commit) == b"commit"
    assert receiver.committed

    try:
        receiver.accept(encode(2, 0, 6, 2, b"wrong transaction"))
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched transaction was accepted")

    corrupt = bytearray(frame)
    corrupt[-1] ^= 0xFF
    try:
        decode(corrupt)
    except ValueError:
        pass
    else:
        raise AssertionError("corrupt frame was accepted")

    try:
        receiver.accept(encode(2, 0, 7, 0, b"stale"))
    except ValueError:
        pass
    else:
        raise AssertionError("stale frame was accepted")

    # Deterministic transport faults: delayed delivery is fine, loss prevents
    # commit, and reordering is rejected without changing accepted state.
    delayed = Receiver()
    prepared = encode(1, 0, 11, 0, b"prepared")
    commit_late = encode(1, 1, 11, 1, b"commit")
    assert delayed.accept(prepared) == b"prepared"
    assert not delayed.committed
    assert delayed.accept(commit_late) == b"commit"
    assert delayed.committed

    dropped = Receiver()
    assert dropped.accept(encode(1, 0, 12, 0, b"prepared")) == b"prepared"
    assert not dropped.committed  # Missing commit must never commit locally.

    reordered = Receiver()
    assert reordered.accept(encode(2, 0, 13, 0, b"step-0")) == b"step-0"
    assert reordered.accept(encode(2, 0, 13, 2, b"step-2")) == b"step-2"
    try:
        reordered.accept(encode(2, 0, 13, 1, b"late-step-1"))
    except ValueError:
        pass
    else:
        raise AssertionError("reordered frame was accepted")
    assert not reordered.committed

    left, right = socket.socketpair()
    try:
        stream_receiver = Receiver()
        left.sendall(encode(2, 0, 21, 0, b"prepared"))
        assert stream_receiver.accept(recv_frame(right)) == b"prepared"
        left.sendall(encode(2, 1, 21, 1, b"commit"))
        assert stream_receiver.accept(recv_frame(right)) == b"commit"
        assert stream_receiver.committed
    finally:
        left.close()
        right.close()

    print("PASS: Butterfly Link buffered framing, validation, duplicate, fault, and commit tests")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest


SOURCE = pathlib.Path(__file__).parents[1] / "projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-link-protocol.py"
SPEC = importlib.util.spec_from_file_location("butterflyos_link_protocol", SOURCE)
PROTOCOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOCOL)


class LinkProtocolTest(unittest.TestCase):
    def test_round_trip_and_sequence(self):
        frame = PROTOCOL.encode_event("session", 0, 1234, "serial-write", b"\x80\x01")
        header, payload = PROTOCOL.decode_event(frame)
        self.assertEqual(header["type"], "serial-write")
        self.assertEqual(payload, b"\x80\x01")
        guard = PROTOCOL.SequenceGuard()
        self.assertTrue(guard.accept(header))
        self.assertFalse(guard.accept(header))

    def test_socket_round_trip(self):
        class Buffer:
            def __init__(self):
                self.data = bytearray()

            def sendall(self, value):
                self.data.extend(value)

            def recv(self, length):
                value = bytes(self.data[:length])
                del self.data[:length]
                return value

        connection = Buffer()
        PROTOCOL.send_event(connection, "session", 1, 5678, "mode", b"\x02")
        header, payload = PROTOCOL.receive_event(connection)
        self.assertEqual(header["sequence"], 1)
        self.assertEqual(payload, b"\x02")

    def test_corruption_is_rejected(self):
        frame = bytearray(PROTOCOL.encode_event("session", 0, 1, "disconnect"))
        frame[-1] ^= 0x01
        with self.assertRaises(PROTOCOL.ProtocolError):
            PROTOCOL.decode_event(bytes(frame))

    def test_sequence_gap_is_rejected(self):
        guard = PROTOCOL.SequenceGuard()
        header, _ = PROTOCOL.decode_event(PROTOCOL.encode_event("session", 2, 1, "mode"))
        with self.assertRaises(PROTOCOL.ProtocolError):
            guard.accept(header)


if __name__ == "__main__":
    unittest.main()

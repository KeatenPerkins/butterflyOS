#!/usr/bin/env python3
"""Tests for extracting bounded raw serial observations from diagnostics."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/butterflyos-link-trace.py"
spec = importlib.util.spec_from_file_location("butterflyos_link_trace", SOURCE)
trace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)


def main():
    line = "[libretro INFO] GBA Serial I/O: BF poll p=1 f=4824 n=3840 peer=0 seq=3839 word=B9A0 reply=0000 sent=16 cnt=601F irq=16384"
    record = trace.parse_line(line, "capture.log", 7)
    assert record["kind"] == "poll"
    assert record["fields"]["word"] == 0xB9A0
    assert record["serial_read_word"] == 0xB9A0
    assert record["serial_write_word"] == 0
    finish = trace.parse_line(
        "BF finish p=0 f=10 n=2 data=B9A0,0000,FFFF,FFFF remote=B9A0 have=1 seq=11",
        "capture.log",
        8,
    )
    assert finish["serial_read_words"] == [0xB9A0, 0, 0xFFFF, 0xFFFF]
    gb_byte = trace.parse_line(
        "[libretro INFO] BFGB byte d=1 n=14 tx=F4 rx=01",
        "capture.log",
        9,
    )
    assert gb_byte["kind"] == "gb-byte"
    assert gb_byte["serial_device"] == 1
    assert gb_byte["serial_tx_byte"] == 0xF4
    assert gb_byte["serial_rx_byte"] == 1
    assert trace.parse_line("ordinary RetroArch line", "capture.log", 10) is None

    recorder = trace.TraceRecorder(max_records=2)
    recorder.add(record)
    recorder.add(finish)
    assert recorder.summary() == {"records": 2, "kinds": {"finish": 1, "poll": 1}}
    try:
        recorder.add(record)
    except trace.TraceError as error:
        assert str(error) == "trace-record-limit"
    else:
        raise AssertionError("trace limit not enforced")
    print("PASS: Butterfly Link diagnostic trace extraction tests")


if __name__ == "__main__":
    main()

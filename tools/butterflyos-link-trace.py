#!/usr/bin/env python3
"""Extract bounded raw Butterfly Link serial traces from RetroArch logs.

The diagnostic core logs GBA 16-bit words, not Gen 1 save sections.  This tool
preserves that distinction: it produces raw, replayable observations that can
be used to map a future adapter, but it never declares a GBA trace to be a
valid Gen 1 payload.
"""

import argparse
import collections
import json
import re
from pathlib import Path


MAX_RECORDS = 4096
EVENT_RE = re.compile(r"\bBF (?P<kind>poll|finish|start|tx|word-change)\b(?P<body>.*)$")
GB_EVENT_RE = re.compile(r"\bBFGB byte\b(?P<body>.*)$")
KV_RE = re.compile(r"(?P<key>[A-Za-z_]+)=(?P<value>[^\s]+)")
HEX_KEYS = frozenset(("word", "reply", "local", "remote", "cnt", "irq", "tx", "rx"))
DEC_KEYS = frozenset(("p", "f", "n", "d", "peer", "seq", "sent", "flushed", "connected", "ack"))


class TraceError(ValueError):
    pass


def _number(key, value):
    base = 16 if key in HEX_KEYS else 10
    if key in HEX_KEYS or key in DEC_KEYS:
        try:
            return int(value, base)
        except ValueError as error:
            raise TraceError("invalid-%s" % key) from error
    return value


def parse_line(line, source, line_number):
    match = EVENT_RE.search(line)
    gb_match = GB_EVENT_RE.search(line)
    if not match and not gb_match:
        return None
    if gb_match:
        fields = {}
        for item in KV_RE.finditer(gb_match.group("body")):
            key = item.group("key")
            value = item.group("value")
            fields[key] = _number(key, value)
        return {
            "source": str(source),
            "line": line_number,
            "kind": "gb-byte",
            "fields": fields,
            "serial_device": fields.get("d"),
            "serial_tx_byte": fields.get("tx"),
            "serial_rx_byte": fields.get("rx"),
        }
    fields = {}
    for item in KV_RE.finditer(match.group("body")):
        key = item.group("key")
        value = item.group("value")
        if key == "data":
            words = value.split(",")
            try:
                fields["words"] = [int(word, 16) for word in words]
            except ValueError as error:
                raise TraceError("invalid-data") from error
            continue
        fields[key] = _number(key, value)
    record = {
        "source": str(source),
        "line": line_number,
        "kind": match.group("kind"),
        "fields": fields,
    }
    if match.group("kind") == "poll":
        if "word" in fields:
            record["serial_read_word"] = fields["word"]
        if "reply" in fields:
            record["serial_write_word"] = fields["reply"]
    elif match.group("kind") == "finish" and "words" in fields:
        record["serial_read_words"] = fields["words"]
    return record


class TraceRecorder:
    def __init__(self, max_records=MAX_RECORDS):
        if not 1 <= max_records <= MAX_RECORDS:
            raise ValueError("invalid-trace-capacity")
        self.max_records = max_records
        self.records = []

    def add(self, record):
        if len(self.records) >= self.max_records:
            raise TraceError("trace-record-limit")
        self.records.append(record)

    def summary(self):
        counts = collections.Counter(record["kind"] for record in self.records)
        return {"records": len(self.records), "kinds": dict(sorted(counts.items()))}


def parse_file(path, max_records=MAX_RECORDS):
    path = Path(path)
    recorder = TraceRecorder(max_records)
    with path.open(encoding="utf-8", errors="replace") as source:
        for line_number, line in enumerate(source, 1):
            record = parse_line(line, path, line_number)
            if record is not None:
                recorder.add(record)
    return recorder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path, nargs="+")
    parser.add_argument("--jsonl", action="store_true")
    parser.add_argument("--max-records", type=int, default=MAX_RECORDS)
    args = parser.parse_args()
    for path in args.log:
        recorder = parse_file(path, args.max_records)
        if args.jsonl:
            for record in recorder.records:
                print(json.dumps(record, sort_keys=True))
        else:
            print(json.dumps({"log": str(path), **recorder.summary()}, sort_keys=True))


if __name__ == "__main__":
    main()

# Butterfly Link: one-core-per-device design

## Why the current prototype is being replaced

The current GBA prototype starts two emulators on each Flip and synchronizes
their serialized state. That gives us a useful proof of concept, but it makes
each device do roughly twice the emulation work and turns every save-state
operation into a timing-sensitive distributed operation. The observed symptoms
(very low frame rate, communication errors, and occasional hangs/coredumps)
are consistent with that architecture. The dual-core launcher and patches
remain available as an experimental reference; they are not the Alpha default.

## Target architecture

Each Flip runs exactly one normal mGBA core and presents the local player's
screen and audio. A small link adapter connects the core's serial/link events
to a peer over a transport. The first transport is TCP on the local network;
the adapter interface must also permit a future USB transport without changing
the emulation or save code.

```
local mGBA core <-> local link adapter <-> framed transport <-> peer adapter <-> peer mGBA core
```

The peer does not receive ROM data or a second video/audio stream. Each player
keeps their own ROM, save, input, video, and audio locally.

## Handshake (protocol version 2)

Before launching a game, the host and joiner exchange:

1. protocol version and transport capabilities;
2. system (`gb`, `gbc`, or `gba`) and ROM identity (SHA-256, byte size,
   extension, and a normalized title);
3. link mode requested by the game/core;
4. save identity (SHA-256 and size), without sending the save itself;
5. a random session nonce and each player's assigned number.

The default policy is exact ROM identity. A future compatibility table may
explicitly allow known revisions, but a filename match alone must never be
accepted. ROMs and saves remain on their originating device.

## Event protocol

Link traffic is bounded, ordered, and acknowledged. Every packet contains:

* protocol version and session nonce;
* monotonically increasing sequence number;
* emulated timestamp/cycle boundary;
* event type (`mode`, `serial-write`, `serial-read`, `transfer-complete`, or
  `disconnect`);
* event payload length and payload;
* checksum (the transport is reliable, but corruption must still fail closed).

The adapter queues only a small, bounded number of events. If the peer falls
behind, the core pauses at a safe link boundary instead of serializing the
whole machine. Duplicate packets are ignored, missing packets request a
replay, and an unrecoverable gap ends the session with a readable error. No
thread may call RetroArch state save/load while a transfer is active.

## Lifecycle and failure behavior

* Host advertises a short-lived session token and waits for one peer.
* Both sides complete the handshake before launching their normal single-ROM
  RetroArch command.
* A clean disconnect sends `disconnect`, flushes the local save, and returns
  to the Butterfly Link screen.
* A lost peer stops link I/O, leaves the local emulator recoverable, and offers
  “save and exit” or “exit without committing”; it must not reboot the device.
* Working saves continue to use `butterflyos-link-save`. Only the local
  player's save is committed after a successful session.

## Implementation phases

1. Add a transport-neutral framed protocol module and host-side unit tests
   (malformed frames, ordering, duplicate/replay, timeout, checksum, and
   handshake rejection).
2. Add a loopback adapter that exercises the protocol without a second device.
3. Add the mGBA single-core adapter at the serial/link boundary. Keep it behind
   an explicit experimental option; normal mGBA and existing GB/GBC linking are
   unchanged.
4. Replace the link-session launcher's dual-ROM command with one ROM and the
   adapter option. Keep the old launcher available only for regression testing.
5. Test GB/GBC first, then same-ROM GBA, then known-compatible cross-title GBA
   pairs. Only after stable two-device tests should the UI expose the feature
   as Alpha functionality.

## Non-goals for this iteration

* no ROM transfer or cloud service;
* no attempt to emulate a physical USB cable yet;
* no cross-generation compatibility promises;
* no full-image rebuild until the loopback and two-device protocol tests pass.

## Acceptance criteria

The redesign is ready for device testing only when one core is visible in the
process list on each Flip, frame rate is comparable to a normal local game,
audio is local and stable, a peer disconnect returns to the UI, and a failed
session cannot overwrite the user's original save.

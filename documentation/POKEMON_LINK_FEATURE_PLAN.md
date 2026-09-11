# ButterflyOS local link feature plan

Status: proposed for Alpha 3; not part of Alpha 2.

## Goal

Give two Miyoo Flip V2 owners a simple, link-cable-like path for trading and
battling in user-supplied Game Boy and Game Boy Color games. ButterflyOS will
not include games, saves, proprietary artwork, or copyrighted game data.

The user-facing feature should use a generic name such as **Pocket Link**.
Game and company names may be used descriptively in compatibility
documentation, with a clear independent-project disclaimer.

## Why this is feasible

The Gambatte libretro core already built into ButterflyOS has network serial
link support compiled in. Its core options expose `Network Server`, `Network
Client`, a network port, and a server IP address. Its source implements a TCP
server/client transport for Game Boy serial data. The first prototype can
therefore wrap existing emulator support rather than emulate the link cable in
a new application.

This is distinct from RetroArch netplay: both devices run their own game and
save while the core sends emulated link-port traffic between them.

## Proposed experience

1. Both devices connect to the same local Wi-Fi network.
2. Open **Apps > Pocket Link** on each device.
3. One player selects **Host**, the other selects **Join**.
4. The host advertises a short session name on the LAN; Join lists discovered
   ButterflyOS devices without requiring an IP address.
5. Each player selects a compatible locally owned game.
6. ButterflyOS checks generation, region/version metadata where known, core,
   network reachability, and save-file safety.
7. Both devices launch Gambatte with temporary per-session overrides.
8. On exit, ButterflyOS restores normal core settings and records a diagnostic
   log containing no game or save data.

An Advanced option may permit manual IP and port entry when discovery fails.

## Compatibility policy

- Phase 1: Game Boy generation-one titles (Red, Blue, and Yellow families).
- Phase 2: Game Boy Color generation-two titles (Gold, Silver, and Crystal
  families).
- Phase 3: explicitly test cross-generation Time Capsule behavior.
- Phase 4: investigate Game Boy Advance separately; Gambatte cannot provide
  GBA link emulation, so this requires a different core or implementation.

Exact ROM hashes should not be required merely to start a session. The app
should identify known revisions by hash when possible, warn about untested or
incompatible combinations, and let advanced users proceed. Successful trading
between different releases must be proven with real two-device tests.

## Safety requirements

- Never copy or transmit ROM files between devices.
- Back up both save files before every session and offer one-button restore.
- Refuse to overwrite a newer save silently.
- Keep link overrides session-local; a crash or reboot must restore ordinary
  single-player launch behavior.
- Detect loss of Wi-Fi/peer and show a clear recovery message.
- Bind the host service only for the active session and use a random available
  high port where the core permits it.

## Implementation milestones

1. **Technical proof:** manually configure host/client overrides on the two
   test Flips and prove one trade or battle over the existing Wi-Fi network.
2. **Reliable launcher:** create temporary overrides, launch both sides, clean
   up on normal exit and crash, and preserve saves.
3. **Discovery:** add lightweight LAN discovery plus manual-IP fallback.
4. **ButterflyOS UI:** add Host, Join, game selection, connection status, and
   readable error screens using the existing theme and controls.
5. **Compatibility suite:** record game revision, pairing, trade, battle,
   reconnect, cancellation, and interrupted-session results.
6. **GBA research:** evaluate available open-source GBA cores independently of
   the stable GB/GBC feature.

## Alpha 2 decision

Do not delay Alpha 2 for this feature. Alpha 2 should remain the clean,
reversible baseline used to test the proof of concept on two devices. Promote
Pocket Link only after a real trade/battle succeeds without corrupting either
save.

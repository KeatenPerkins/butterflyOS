# Butterfly Link

Butterfly Link is an experimental local-network link-cable experience for
user-provided GB/GBC games and saves. ButterflyOS does not provide or transfer
ROMs, BIOS files, or an online matchmaking service.

## Proven prototype

On September 19, 2026, two Miyoo Flip V2 units running the same ButterflyOS
build completed a Pokémon Red/Blue trade. The prototype used SameBoy's
two-system link subsystem synchronized through RetroArch LAN netplay. Each
device controlled one player. Both prepared saves loaded, the trade completed,
and both updated saves were written and verified.

The ButterflyOS SameBoy patch provides native `Game Boy #1 Only` and `Game Boy
#2 Only` presentation modes. Both systems remain emulated for link timing, but
each Flip displays and plays audio from only its assigned system. Dual-link
sessions use 48 kHz audio; ordinary one-system SameBoy operation retains its
upstream audio rate.

## Save-safety backend

`/usr/bin/butterflyos-link-save` owns the save lifecycle. The future graphical
launcher must use this backend instead of writing directly to a library save.

Supported commands:

```text
butterflyos-link-save discover ROM
butterflyos-link-save begin ROM SAVE
butterflyos-link-save status SESSION_ID
butterflyos-link-save commit SESSION_ID [WORKING_SAVE]
butterflyos-link-save abort SESSION_ID
butterflyos-link-save restore SESSION_ID
```

`discover` searches the selected ROM's directory, the configured RetroArch
save tree, the OS-card ROM tree, and the second game-card ROM tree. It resolves
symlinks and reports one entry per physical save. The save adjacent to the
selected ROM is preferred, followed by the OS save tree and then other card
locations. The UI must display the selected card and absolute path whenever
more than one candidate exists.

`begin` creates a private session below:

```text
/storage/.config/butterflyos/link/sessions/SESSION_ID/
```

The session contains:

- a read-only, SHA-256-verified copy of the original save;
- a writable working copy used by the emulator;
- a non-executable manifest containing Base64-encoded paths, hashes, size,
  permissions, timestamp, and storage identity;
- an atomically updated state file.

The original library save is not passed to the emulator. `commit` refuses to
write if the original changed after the session began or if the working save's
size changed. It verifies a same-directory temporary copy, flushes it, renames
it atomically over the selected canonical path, verifies the result, and keeps
a post-session archive. This works for saves physically located on either SD
card, including files reached through the merged-library symlinks.

`abort` never modifies the selected save. `restore` verifies the immutable
pre-session backup, archives the current file, and atomically restores the
original bytes. Backups are retained until an explicit future retention policy
removes them; the launcher must not silently delete the last recovery copy.

## Current automated workflow

- Controller-friendly Host, Join, Restore, Session Status, Cancel, and
  Connection Test screens are implemented. Host waits are cancellable, and
  Join refreshes discovery automatically.
- Host and Join exchange only isolated save working copies, require matching
  ROMs to exist locally on both devices, and launch the proven SameBoy
  two-system subsystem through RetroArch LAN netplay. ROM bytes never cross
  the network.
- Netplay SRAM is explicitly loaded and saved inside the protected session.
  The joining player's authoritative `.netplay/player2.srm` result is selected
  for writeback. Each device asks before atomically committing only its own
  result through `butterflyos-link-save`.

## Remaining MVP work

- Nearby-device discovery and core/protocol compatibility checks are
  implemented, with a manual-IP fallback. The always-on agent is read-only: it
  exposes only hostname, build identity, protocol version, capabilities, and
  the SameBoy core hash when idle. An explicitly started Host session adds an
  expiring random session token and selected-ROM metadata; it accepts no ROM
  transfer.
- Friendlier visual/audio presentation matching ordinary ButterflyOS games
- Recovery behavior for Wi-Fi loss, power loss, and one-sided termination
- Validation across Yellow, Gold, Silver, Crystal, and regional revisions

## Game Boy Advance research

Generation-three GBA linking cannot use the GB/GBC SameBoy implementation.
The pinned mGBA libretro core reports both netplay and subsystem support as
unavailable, while upstream mGBA currently supports local same-computer GBA
linking but not network link-cable transport.

ButterflyOS is therefore prototyping a two-instance mGBA libretro subsystem:

1. each Flip loads both locally owned GBA ROMs and isolated save working
   copies;
2. mGBA's existing `GBASIOLockstepCoordinator` connects the two local virtual
   link ports;
3. RetroArch LAN netplay synchronizes the two players' inputs between Flips;
4. each Flip presents only its assigned GBA screen and audio; and
5. the existing Butterfly Link save-safety layer commits only that device's
   authoritative result.

The initial core implementation is complete: the core registers a two-cartridge
`GBA Link (2 Players)` subsystem with separate save-memory regions, enables
mGBA's real pthread synchronization, loads two GBA core instances, connects
their local SIO ports through mGBA lockstep, and routes the two libretro input
ports independently. The complete patch stack compiles from a clean source
tree for the Miyoo Flip V2. The core-info metadata also advertises subsystem
support.

An isolated no-save test on a Miyoo Flip V2 loaded Ruby and Sapphire, ran both
cores for ten seconds through persistent mGBA core threads, and logged repeated
SIO lockstep acknowledgements without the transfer-state failure seen in the
disposable-thread prototype. This proves local dual-GBA execution and lockstep
on the target hardware, but not yet an in-game trade.

The frontend frame wait is bounded so RetroArch can service a quit request even
when the primary GBA is sleeping in link lockstep. A no-save hardware test then
shut down RetroArch and both persistent core threads cleanly through the normal
signal path in under one second, with no forced termination.

This remains experimental. Player-specific presentation, serialization policy,
save-safety integration, RetroArch netplay validation, real trade testing, and
hardware performance measurements remain before any save-enabled test. The
proven GB/GBC path is unchanged during this work.

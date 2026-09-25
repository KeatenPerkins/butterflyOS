# Butterfly Link diagnostic core 022 — 2026-09-25

Built on patch 021. This adds optional instrumentation, not a transfer timing fix.
The full SD image has not been rebuilt. Both devices use temporary bind mounts
for the diagnostic core and session launcher; these mounts disappear on reboot.

## Enabling and collecting

The updated launcher enables diagnostics for single-core GBA sessions when
`BUTTERFLY_LINK_DIAGNOSTICS=1` or the marker
`/storage/.config/butterflyos/link/diagnostics-enabled` exists. It enables INFO
output and routes it to the session's existing `runtime/launch.log`.

Logs: `/storage/.config/butterflyos/link/sessions/<session-id>/runtime/launch.log`.
The current session ID is in `/storage/.config/butterflyos/link/last-session`.
Look for `BF diag022 enabled` to prove the new core and logging are active.

Capture one Ruby host (.20) / Emerald guest (.17) cable-club attempt. After
reaching "Please wait", leave it for approximately 10 seconds, then collect both
logs. Preserve the session metadata with each log so player roles are clear.

## Instrumentation

- `BF mode`: requested/current SIO mode and connection status.
- `BF state`: SIOCNT, RCNT, and decoded ID, slave, and ready fields.
- `BF start`: local word, sequence, send success, and SIOCNT.
- `BF finish`: four words returned to the game and cached peer word/sequence.
- `BF poll`: peer word, local reply, send byte count, SIOCNT, and IRQ flag.
- `BF idle`: periodic status even if no packets are arriving.
- `BF diag022 end`: event counters when driver deinitialization runs.

Events include the local emulated frame number. Frames across devices are not
synchronized wall-clock timestamps. Logging emits the first 64 events per
category, then every 256th, capped at 512 lines/category for each driver lifetime.
Idle status is considered every 300 frames. Normal sessions leave diagnostics off.
The cap bounds these diagnostic messages, not unrelated RetroArch output. Session
logs remain in their existing per-session directories; no rotation policy changed.

Register clarification: SIOCNT slave is bit 2, ready is bit 3, ID is bits 4–5.
Claude's request incorrectly identified bit 3 as the slave/SD distinction.

## Live files and rollback

Staging directory on each device:
`/storage/.config/butterflyos/link/diagnostics-022/`.

- `mgba_libretro.so`: bound over `/usr/lib/libretro/mgba_libretro.so`.
- `butterflyos-link-session`: bound over `/usr/bin/butterflyos-link-session`.
- `session-before`: original launcher backup.

Diagnostic core SHA-256:
`daab704e047968df3ec965e5f209e5a065d38c13f24e645a849e2e75da60ac7d`.

Close the test before rollback. Unmount the two bind mounts, or reboot. Rename
the `diagnostics-enabled` marker to disable diagnostics on future launches while
keeping the updated launcher. Original ROMs/saves are not altered by deployment.

## Validation

The AArch64 core package compiled successfully (upstream SHA1 compiler warnings
remain). GB/GBC and GBA session protocol tests passed. The GBA test also verified
that the host marker enables the diagnostic environment, verbose logging, and
INFO capture while the guest without a marker retains normal logging.
Hardware log capture is pending the next user-driven test.

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

## Remaining MVP work

- Controller-friendly Host, Join, Restore, and Connection Test screens
- Nearby-device discovery with a manual-IP fallback
- ROM/core/build compatibility checks on both peers
- Coordinated session launch, clean exit, and save ownership exchange
- Recovery behavior for Wi-Fi loss, power loss, and one-sided termination
- Validation across Yellow, Gold, Silver, Crystal, and regional revisions


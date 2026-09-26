# Patch 025 result: stuck at Please wait

Both devices were running core SHA-256
`1d5086c026e2de7e964c286595081c9621d50f84b3349fa9f4e71a1fd14e396c`.
The logs were copied while both games remained open. No ROMs or saves were
modified during diagnosis.

- Guest `.17`: session `20260926T005033Z-131129-29636`.
- Host `.20`: session `20260926T005000Z-131709-4456`.
- Logs: `device-17-launch.log` and `device-20-launch.log` in this directory.

## Evidence and correction to the previous diagnosis

The guest logs many `BF poll` records receiving `B9A0` but always replying
`0000`. There are **no guest BF start or BF finish records** in the capture.
For example, guest poll sequence 5631 still replies 0000 with SIOCNT 601F.
The `irq=16384` field means IRQ is enabled; it does NOT prove an IRQ fired.

The host keeps starting transfers and completing with
`data=B9A0,0000,FFFF,FFFF`. Network traffic is flowing. This is an emulated
serial-transfer failure, not evidence of lost Wi-Fi connectivity.

Patch 025 incorrectly assumed that the guest writes the start bit and therefore
runs `_start` and the generic timer. Emerald's guest does neither here.
`localWord` stays zero and removing PollFrame's completion signal prevents the
guest game from advancing. A zero send word can be valid; the defect is the
missing capture and completion, not the numeric value alone.

The host also uses the generic emulated cable timer, completing before its
network reply arrives and substituting an older cached word. That violates
transfer correspondence and is a plausible cause of the previous transmission
errors. It is not proven to be their only cause.

## Local reproduction

Added `tests/butterflyos-gba-sio-test.c` and its shell runner in the development
checkout. They compile the actual patched `butterfly.c`, `sio.c` and `timing.c`
with mGBA headers and a local socket pair. Logging, GBP and IRQ delivery to a CPU
are stubbed; register handling, scheduling and completion are real. No ROMs or
saves are needed.

The patch-025 driver fails both checks, also verified outside the sandbox:

1. A host request must complete on the guest without any guest start write.
2. Advancing emulated time before a reply arrives must not complete the host.

## Patch 026 prepared

`026-butterflyos-link-matched-transfer-completion.patch`:

- Only the master initiates a transfer and chooses its sequence.
- The guest samples SIOMLT_SEND when the request arrives, replies with the
  same sequence, and completes once through GBASIOMultiplayerFinishTransfer.
- The host completes only upon a reply matching its pending sequence.
- No generic multiplayer completion timer and no cached-word substitution.
- Replies never cause replies. Slots 2 and 3 stay FFFF.
- Stream reads/writes preserve partial packets and remain nonblocking.
- A missing reply times out after 300 poll calls, returning an absent peer
  for that transfer while keeping the connection available for another try.
- Protocol version is now 3: both devices must use the same updated core.

The updated driver passes the two reproduced cases plus changed/zero words,
duplicate/stale/future replies, fragmented reads, timeout, and peer disconnect.
These tests validate transfer semantics, not complete Pokemon gameplay.

## Remaining uncertainty

Polling is still once per emulated video frame. Per-transfer matching adds
network round trips, and the games may require tighter timing or coordinated
emulated time for sustained block exchange. If another live test fails, inspect
matched sequence/word/IRQ progression and throughput; do not reintroduce cached
old words or depend on guest `_start` to hide latency. No full OS rebuild is
needed for the next core-only live test.

## Build and deployment

Patch 026 compiled successfully; the native regression suite also passed when
compiled against the final, build-system-patched source. The compiler reports
the existing SHA-1 stringop-overread warnings; no build errors occurred.

Core SHA-256:
`1cbd7861e15d4bdd2156c7d75428f8d84f0cba4039f36f7d5c5230cd37848f4b`.

Deployed after verifying both RetroArch processes had exited, to
`/storage/.config/butterflyos/link/diagnostics-026/mgba_libretro.so` on both
devices, bind-mounted over `/usr/lib/libretro/mgba_libretro.so`. Both active
hashes match. Diagnostics remain enabled. Patch 025 files remain available
under `diagnostics-025` for rollback. The live bind mounts do not survive a
device reboot; verify the active hash again if either device restarts.

Next manual test: host Ruby on .20, join Emerald on .17, enter the Cable Club
and attempt the trade. Actual trading remains unverified with this patch.

# Deferred-reply review and serial scheduler fix

Reviewed `/home/keaten/Documents/Claude-deferred-reply-fix-for-codex.md` and
`/mnt/nas/ButterflyOS-Claude-Handoff/Claude-patch-026-findings.md`.

## Confirmed launch failure

Both handhelds had Claude's core with SHA-256
`b766391805c69ec6b75d9b7f2622ba8985d61831a9cbe5e2f5e350a2084b0b59`.
The most recent captured launches failed with:

`symbol lookup error: /usr/lib/libretro/mgba_libretro.so: undefined symbol: VFileFOpen`

Guest session: `20260926T015818Z-166153-12291`.
Host session: `20260926T015752Z-166754-7965`.
The local artifact also had unresolved VFileFOpen and three PatchFast symbols.
The latter were an older build-list defect: enabling rewind in patch 002 did
not include its `src/util/patch-fast.c` dependency.

Preserved Claude's source/header/binary before any package clean, under
`/home/keaten/Documents/Butterfly-Link-Diagnostics-027/claude-build-snapshot/`.
Both failed launch logs are in the parent directory. The input document is
unchanged. A Docker invocation alone does not ensure objects were rebuilt;
this build explicitly logged CLEAN and UNPACK before compiling every object.

## Why not adopt post-completion resampling

Claude's implementation completes the guest with word A, lets its IRQ handler
prepare word B for the next transfer, then sends B to the host under the old
sequence. The two endpoints receive different SIOMULTI arrays for one transfer.
The new `payload` regression reproduces this failure against Claude's source.

[mGBA's GBA reference](https://mgba-emu.github.io/gbatek/) describes the receive
registers as containing all participants' outgoing data, including local data,
after a transfer. The local mGBA lockstep implementation likewise captures
shared transfer data before completing. Sampling after guest completion is not
an equivalent timing adjustment.

A zero word alone does not prove a timing bug: Emerald initializes SIOMLT_SEND
to zero. A sample hundreds of frames after a mode switch does not establish
that the register was read between that switch and its next initialization.
We need transition diagnostics and transfer/IRQ progression for that claim.

## Concrete timing limitation addressed

[Emerald's link code](https://raw.githubusercontent.com/pret/pokeemerald/master/src/link.c)
uses nine serial interrupts per established-link frame and checks received
checksums. Waiting for a video-frame callback for each network exchange cannot
service that burst. Adding another full-frame delay makes that limit worse.

Patch 027 adds a nonblocking mTiming poll event every 1024 emulated cycles
(roughly 61 microseconds). Socket work and completion stay on the emulator
thread. Mode changes, reset, and disconnect remove the event as appropriate.
The existing frame callback still maintains timeout and diagnostic counters.
It is not the only place that receives packets anymore. No additional emulator
instance or worker thread is introduced.

The guest's snapshot remains identical in its completion and its response to
the host. Matching sequence checks from patch 026 remain. Mode changes trigger
64-event diagnostic bursts while retaining the overall per-category log cap.

Patch 028 adds `patch-fast.c` to the build sources. The package now links with
`--no-undefined`, so missing internal functions cause a build failure instead
of producing a core that fails later on the device.

## Validation

- Claude's source fails the new payload-consistency regression.
- Patch 026 fails the new within-frame serial-burst regression.
- The rebuilt patch 027/028 source passes both, plus previous tests for
  stale/duplicate replies, zero words, partial reads, timeout and disconnect.
- Nine simulated transfers complete within 18432 emulated cycles on each
  endpoint, without calling the frame polling function. This is an in-process
  socket test, not evidence that real Wi-Fi has sufficient latency.
- Clean package compilation succeeds with `--no-undefined`. Existing SHA-1
  compiler warnings remain; they are unrelated to the missing-symbol failure.

Built core SHA-256:
`66fb7edb51b5dd18a025d72074d354ca3e242cd2ebb6fbb2b01b00ee6b79a92d`.

## Live test and remaining limits

Install path: `/storage/.config/butterflyos/link/diagnostics-027/mgba_libretro.so`,
bind-mounted over `/usr/lib/libretro/mgba_libretro.so`. The former active core
is preserved as `diagnostics-027/previous.so`. These mounts disappear on reboot.
Before binding, use `ctypes.CDLL(path, mode=os.RTLD_NOW)` on each device and check
`retro_api_version() == 1` to resolve every library symbol, without opening a ROM.

Next manual test is host Ruby on .20, join Emerald on .17, then enter Cable Club
and attempt the trade. No ROM or save contents were modified by this work.
Real Wi-Fi round trips may still exceed the game's timing requirements. If so,
coordinating emulated time across devices is the next task; do not fake success
using old words or post-IRQ resampling. The live trade is not yet verified.

Deployment completed on both .17 and .20. Both passed the on-device RTLD_NOW
loader/API check and both active core hashes match the one above. Diagnostics
are enabled. A transient SSH timeout on .20 cleared on retry before activation.

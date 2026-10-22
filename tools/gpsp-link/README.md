# Experimental GBA linking test harness

Current user guidance and known issues are in the
[Bslap guide](../../documentation/BSLAP.md).
The current live launcher is `GBA-Cable-RetroArch-Plain.sh`: separately installed
development RetroArch32, plain gpSP handshake candidate, and Wi-Fi power saving
ON. A communication error on room exit remains accepted as an experimental
limitation. Let one player initiate exit and the other respond to the propagated
dialogue for better observed results; this is not a guaranteed fix.

The sections below preserve earlier experiments and their hashes. They are not
instructions to replace the current launcher or the stable binaries.

## Original RFU diagnostic experiment

This is an isolated development core, not a fix or a release replacement.
Base: gpSP `b0d5d27ae51c23f514974ddffa5760f1e1d05d9b`, plus ButterflyOS's
existing RK3566 Makefile platform patch and `rfu-diagnostics.patch`.
The patch adds at most eight log lines per event category (48 total per process)
for resets, local/remote disconnects, peer expiry and wait errors. Logging can
perturb timing; no timeout constants, scheduling or packet semantics are changed.

Run `python3 tools/gpsp-link/prepare-source.py` once to export the existing cached
source into a fresh `.cache/gpsp-link-tests/diagnostic-core/source` tree and apply
both patches. The existing prepared directory is deliberately not overwritten.
Run `tools/gpsp-link/build-diagnostic-core.sh` in the project's existing build
container with the repository mounted at its original absolute path. Use the
container user mapping `--userns keep-id --user 1000:1000`. This builds only gpSP,
using the existing 32-bit toolchain; it does not rebuild packages or an OS image.

First diagnostic binary SHA-256:
`1683ed12cd2ca050148eb369e0b2cba054da106ac13aaf2bb72a6c60afedcb12`.
ARM32 EABI5 hard-float, linked against libc/libm. The upstream ARM assembly emits
an executable-stack warning already associated with its assembly; this is not a
hardening change. Rebuilt binaries may differ; update the launcher's hash after
verification if rebuilding.

On each development device, the separate core is
`/tmp/cores/gpsp_bfrfu_libretro.so`, in the writable `/storage/cores` overlay.
Its `.info` is copied from the released gpSP metadata. The Tools launcher is
`/storage/.config/modules/GBA Wireless Diagnostic.sh`. Normal GBA launches still
use the released core. Remove these three added files to undo the installation;
do not remove or overwrite the original `gpsp_libretro.so`.

Launch through Tools, not the normal GBA entry. The launcher uses the disposable
Wireless Link Test content, preserves before/after saves and the ordinary launch
log in a unique on-device diagnostic session directory. Hosting is enabled after
launch, and the peer joins through RetroArch's LAN menu as in the baseline test.

Both development devices passed a 120-frame headless load/run/exit smoke check;
RFU probes ran and temporary save-directory redirection left the test saves
unchanged. Null-audio startup errors in that headless check are not evidence of
real-device audio qualification. Interactive controls/audio/netplay and the
teardown failure still need this diagnostic retry. Nothing is merged or published.

## Separate newer Pokémon cable comparison

`prepare-cable-core.py` exports upstream gpSP commit
`5819380c2ffb0900219d700a382ee68c464ebb99` from the local upstream cache and applies
only the existing RK3566 Makefile patch. `build-cable-core.sh`, run in the same
container setup, compiles its 32-bit ARM dynarec core. No RFU diagnostic patch or
new protocol code authored by ButterflyOS is applied to this newer comparison.

Cable binary SHA-256:
`bdb2bba86f2c82e77d4bb00de938a8eee34c7994efe64a90b676d3006969e5e6`.
Installed separately as `/tmp/cores/gpsp_bfcable_libretro.so` plus matching `.info`.
Tools launcher: `GBA Cable Test.sh`. Disposable content:
`/storage/roms/gba/Cable Link Test/Emerald - Cable Test.gba` and adjacent `.srm`.
Both saves are copies of the last fully qualified, cleanly exited diagnostic pair;
wireless-test content stays untouched. The game-specific gpSP options file requests
`gpsp_serial = "mul_poke"`. Use the in-game Cable Club, not the wireless Union Room.

ARM32/ABI/shared-library checks passed. Both devices completed a 120-frame headless
startup/exit with temporary save redirection; original cable-test save hashes were
unchanged and Netpacket registration was present. This is not interactive trade
qualification. Both Wi-Fi adapters remain temporarily in power-save-off mode from
the preceding live probe; restore their normal policy after the experiment.


## Bounded cable diagnostic comparison

After a clean battle, a second room visit/trade failed on room exit. The separate
`prepare-cable-diagnostic-core.py` exports the same pinned newer revision, applies
the existing platform patch and `cable-diagnostics.patch`.
`build-cable-diagnostic-core.sh` builds it in the existing container. The patch
only adds bounded stderr observations (48 messages per category per process)
for reset, handshake/connection transitions, peer-state changes, timeouts and
queue overflow. Logging itself can perturb timing; no protocol fix is claimed.

Core: `/tmp/cores/gpsp_bfcdiag_libretro.so`; SHA-256:
`2fa0370fe23ee523f6602c307b084c8605e8e2c17097ed62d5844acffbb7ff20`.
Both devices passed 120-frame headless startup/exit with temporary save paths,
Netpacket registration and unchanged test-save hashes. Null-audio initialization
errors in that headless check are expected. `GBA-Cable-Diagnostic.sh` is installed
as the existing Tools → GBA Cable Test entry to avoid an extra menu entry; it uses
the existing disposable cable-test save, records unique before/after archives,
and disables automatic state loading/saving. Restore `GBA-Cable-Test.sh` to that
menu path to return to the uninstrumented comparison core. Both cores remain
installed separately from the released core. Interactive retesting is pending.


## RCNT reset candidate

`prepare-cable-reset-core.py` exports the same pinned source and applies the
platform, bounded diagnostic and two-line `cable-rcnt-reset.patch` patches.
`build-cable-reset-core.sh` builds it with version `5819380-bfrcnt1`.
`check-rcnt-reset.py` reproduces the missed GPIO-to-multiplayer reset in the
upstream handler and checks the correction against repeated/no-reset cases.
The causal link to the live error remains unproven.

SHA-256: `0dc8d45295092957d94388c92be634092ed067b9909aa7bfbb084e8770a93c25`.
Installed as `/tmp/cores/gpsp_bfrcnt_libretro.so` with matching info. Both devices
passed 120-frame headless startup with temporary save redirection, Netpacket
registration and unchanged test-save hashes. `GBA-Cable-Reset-Test.sh` now backs
Tools → GBA Cable Test. Previous cores and launcher sources are preserved for
rollback; save content and network policy are unchanged by this deployment.
Interactive testing remains pending.


## Handshake-wait candidate (current live comparison)

`prepare-cable-handshake-core.py` applies the platform and bounded diagnostic
patches plus `cable-handshake-wait.patch` to the same pinned newer source. It
excludes the RCNT correction. `build-cable-handshake-core.sh` sets version
`5819380-bfhand1`. `check-cable-handshake.py` reproduces premature reconnect
against stale host CONNECTED state and checks delayed and batched real handshake
recovery using extracted upstream client update/receive functions.

SHA-256: `3b8eaeb93b14674c922e9aca5cda66b5ddba051b299050c81ecc0aedc2608133`.
Installed as `/tmp/cores/gpsp_bfhand_libretro.so` plus info. Both local devices
passed 120-frame isolated-save startup/exit and Netpacket registration checks;
test-save hashes were unchanged. `GBA-Cable-Handshake-Test.sh` now backs Tools →
GBA Cable Test. No live reliability result yet. Prior candidates remain available
under separate core names and launcher source files for rollback. Auto Resume
remains disabled, with unique session save/log snapshots. Wait behavior has no
new timeout; it relies on real host handshake/reset, so missing or older-session
messages remain a qualification concern. This is an experimental comparison.


Live handshake-candidate result: with the second local device hosting, battle,
trade, another trade and all room exits passed in one session. Both devices saved
and exited cleanly; native final-save inspection succeeded. Captured client
transitions no longer show the rapid stale-host reconnect loop. This is a first
successful repeated-use sequence, not broad reliability qualification. Fresh
save reload and reversed host roles remain pending. See the experimental notes.

Reversed-host follow-up also passed battle, two trades, all room exits and clean saves/exits on both devices. Both host roles now have a successful sequence. Keep this experimental: normal Wi-Fi power-saving policy, uninstrumented build timing, other games and interruption recovery remain unqualified.


## Close-command trace (current live diagnostic)

`prepare-cable-close-trace.py` and `build-cable-close-trace.sh` retain the handshake
candidate and add `cable-close-trace.patch`, without the RCNT correction.
Only READY_CLOSE_LINK and READY_EXIT_STANDBY command metadata is logged at send,
receive and first-word serial delivery; 128 entries maximum per process.
Version: `5819380-bfclose1`; SHA-256:
`771d8626f67f3c7da670b83b1396faf081abe851614a38517a456f0ddaf63e18`.
Installed separately as `/tmp/cores/gpsp_bfclose_libretro.so`, with matching info.
Both local devices passed 120-frame isolated-save startup/exit and Netpacket
registration, with original test saves unchanged. Tools → GBA Cable Test now
uses `GBA-Cable-Close-Trace.sh`. Wi-Fi power saving remains ON. No additional
protocol change is included. Live staggered-exit tracing remains pending.


## Full-word close trace (current live diagnostic)

`prepare-cable-close-words.py` / `build-cable-close-words.sh` add
`cable-close-words.patch` atop the close trace, preserving the handshake candidate.
Bounded BF-WORD snapshots record the next 24 register injections after a close
observation, with a process-wide ceiling of 256. Include checksum, offset, receive
and send registers, SIOCNT/RCNT and IE/IF/IME. These do not prove game IRQ service.
Version `5819380-bfwords1`; SHA-256:
`8264211c676d0be7e606f3c39973ca0072b961ea208717d8d364280e4d56e4eb`.
Separate core `/tmp/cores/gpsp_bfwords_libretro.so` with matching info.
Both devices passed 120-frame isolated-save startup/exit and Netpacket registration,
with original test saves unchanged. Tools → GBA Cable Test now uses
`GBA-Cable-Close-Words.sh`. Live staggered-exit tracing remains pending.


## Current-development RetroArch32 comparison (staged)

Pinned frontend revision: `9e1c1e8ac897625ed75920019f4f62a173a4eedf`.
Downloaded archive SHA-256:
`0d9a7c3acf988fe06f0fc7b27f72ad65adaa8b7e6681fbda48e4f59ac1883f1b`.
ARM32 executable SHA-256:
`556a1d7b09ea280ba06d34ad53347864d6f4288702894cbe104842591bb5da89`.
The upstream version string still reads 1.22.2; commit/archive/binary hashes identify
this development build. Prepare/build and runner-generation scripts are in
`tools/gpsp-link`. The first configure attempt failed because newer configure uses
PKG_CONF_PATH rather than PKG_CONFIG; setting it explicitly resolved dependency
detection. The build retained ARM NEON, Wayland/GLES, PipeWire, udev and networking.

Applied existing OGA preferred-mode, DRM resolution, disabled-search, Wayland
checkerboard and controller-fallback patches. Adapted the localhost-only NetCMD
patch to the current bind-address API. UI sizing/quit labeling, brightness, default
paths and achievement hook/sound patches did not apply cleanly and were not carried
into this scoped comparison. The existing explicit config supplies runtime paths;
these omitted patches are recorded differences, not claimed equivalent behavior.
Patch dry-run results are private in `retroarch-current/patch-results.json`.
No Netplay source logic was patched by ButterflyOS in this frontend comparison.

Installed separately at
`/storage/.config/butterflyos/gpsp-link-tests/retroarch-current/retroarch32`.
A copied live runemu script changes only frontend executable and main config path.
The test launcher snapshots the save, copies the main configuration to a unique
session, disables config saving there, and keeps Auto Resume off. The normal
system frontend is untouched. The same gpSP full-word diagnostic core is retained:
`8264211c676d0be7e606f3c39973ca0072b961ea208717d8d364280e4d56e4eb`.
Wi-Fi power saving remains ON on both. Both devices passed 120-frame headless
startup/exit with temporary save paths, Netpacket registration and unchanged test
save hashes; runtime version and executable hashes were checked on both.
Tools → GBA Cable Test now uses `GBA-Cable-RetroArch-Current.sh`.
Live graphics/audio/controller/Netplay and staggered-exit qualification is pending.
Rollback: reinstall `GBA-Cable-Close-Words.sh` as the module to use the original
system frontend with the same core. No image rebuild or publication occurred.


## Plain handshake core with development frontend (current comparison)

`prepare-cable-handshake-plain.py` / `build-cable-handshake-plain.sh` build the
same pinned gpSP with only platform and handshake-wait patches. No RCNT or BF
logging patches. Protocol source matches the prior candidate exactly after
reversing its diagnostic patches. Version `5819380-bfplain1`; SHA-256:
`1ae51cbbc844f4c9574dbb2dc3853097d9badc53b32057ec84e1577615b91f55`.
Installed separately as `/tmp/cores/gpsp_bfplain_libretro.so` with matching info.
Both devices passed 120-frame startup/exit with the unchanged development frontend,
isolated save paths, Netpacket registration and unchanged test-save hashes.
Tools → GBA Cable Test now uses `GBA-Cable-RetroArch-Plain.sh`, which retains the
separate frontend, temporary config and unique before/after session snapshots.
Wi-Fi power saving remains ON. No stable frontend/core was replaced. Live testing
without the added diagnostic logging is pending. Reinstall
`GBA-Cable-RetroArch-Current.sh` to restore the full-word diagnostic comparison.


### Newer frontend without core diagnostic logging failed

Both actual executable paths were verified as the pinned development frontend,
with the plain handshake candidate and Wi-Fi power saving ON. The second local
device hosted. The user reproduced the communication error after diagnostic
logging was removed. The report did not specify the exact failing room/action
or affected device, so do not infer them. Both emulator processes stayed alive.
TCP remained ESTABLISHED; both endpoints had 36 bytes in their receive queues
at the instant inspected. That snapshot does not establish packet loss, a
transport deadlock or a game-error cause. Private normal logs are under
`.cache/gpsp-link-tests/20261021-retroarch-plain-error`.

This rejects promoting the newer frontend plus handshake candidate as a reliable
fix. Successful instrumented sequences cannot be used to claim an upstream
RetroArch fix. Logging may alter timing, but the experiment does not prove a
specific timing cause. Keep all work on the experimental branch; no stable
RetroArch/core update or full image build is justified by these results alone.
Preserve final session saves/logs after normal exit. Next work should prioritize
a bounded failing full-command trace or an upstream reproduction/report over
additional speculative timeout/ack patches and repeated blind manual trials.


## Bslap controller launcher

The controller UI is now at
`projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-bslap.py`,
with Bslap.sh and Tools metadata/icon. For live tests it is installed under
`/storage/.config/butterflyos/bslap`, using the same separate development frontend
and plain handshake core. See the experimental user guide for hosting, joining,
save paths, restore steps and current game limitations. The launcher owns local
UDP discovery on 55436 and starts RetroArch Netplay on 55435. Discovery identifies
the sender IP, matches backend version and exact ROM hash, and advertises only
when the host frontend is listening. No remote files are received. UI closes its
controller bridge before game startup, then reopens after normal game exit.
Sessions use isolated main/config/core-options and state directories; ordinary
in-game saves remain at the selected ROM's adjacent .srm path with before/after
copies retained. These helpers are experimental and do not rename Blink.


Bslap lobby update: discovery v2 advertises a waiting host; TCP 55437 handles
ROM/backend readiness, host Start, client acknowledgment and frontend readiness.
Games stay closed until both players are ready and the host starts. The joiner
waits until the host frontend is listening before launching. The blank discovery
footer crash was fixed. Five regression tests and a two-device lobby-only handshake
check passed. See the user guide for the updated flow.

# Bslap Gen 1/2 single-instance implementation record

Implemented and qualified for v1.6.0, build 20261027, after development on
`experimental/bslap-gb-netpacket-20261027` and a full rebuilt-image test. Runtime
source is `4ea693e232925b145332986834d6dfbea5924514`. The user approved Gen 1/2,
Gen 3 regression, controller and tool tests on the flashed image and authorized
publication. The dated investigation and intermediate failures below are retained
as development history; their earlier pending/deferred status is superseded by
this outcome. Broader pairing and cross-core RTC limits remain documented.

## Current candidate

- Dedicated `gambatte-bslap-lr`, pinned to
  `466e8b174982b3fdb5a026f60efc51972d1576b0` from Gambatte Netpacket PR #266.
  Installs as `gambatte_bslap_libretro.so`; ordinary Gambatte is untouched.
- Uses existing native RetroArch and its Netpacket API. No kernel changes or
  frontend version update are needed for this candidate. Gen 3 is unchanged.
- One local ROM and working save per device, no subsystem/second emulator,
  no peer save or ROM exchange. Existing host-waits-for-joiner lobby is retained.
- Original SRAM is backed up, results are validated and conflicts rejected before
  return after a clean exit. Historical SRAM trailers are preserved. Adjacent
  Gambatte `.rtc` sidecars are backed up and returned; each file is atomically
  replaced, but SRAM and RTC together are not a power-loss-atomic transaction.
- Initializes serial callbacks, bounds waits to two seconds without permanently disabling a connected peer,
  rejects malformed packets, tags requests/replies with sequence IDs to discard
  late replies, cancels timed-out requests and handles crossed internal clocks.
  It resets stale queues on connection changes and prevents busy
  spinning while waiting. Packet timing and real-game compatibility still need
  qualification; single-byte round trips may remain a network bottleneck.
- Gen 1 selects Gambatte's Special 3 preset; shoulder palette cycling defaults
  off. Gen 2 retains native color rendering. Menu + Start twice uses the existing
  freshly generated launch configuration.
- A manifest containing this core selects it by default **on this experimental
  branch**. For fallback, write `sameboy-dual` to
  `/storage/.config/butterflyos/bslap/gb-backend` on both devices. Write
  `gambatte-netpacket` to switch back. Different modes cannot join a session.
  This setting is independent of ordinary GB/GBC core choices.

## Verification so far

Local Python tests cover single-content routing for host/join in both generations,
local-save isolation, clean-exit result return, clock backups, save/clock conflicts,
invalid clocks and save validation failure. Existing Bslap and SameBoy tests pass.
`tests/bslap-netpacket-serial-test.cpp` exercises the actual patched serial class,
including initialization, request/reply, peer limits, timeout and disconnects.
The normal core and Bslap backend package builds also pass. The packaged core's
SHA-256 is `bb25c333e13fa92565f8c79699bf704709dcea1810f00a57361f3356a1b79ba2`;
the image manifest identifies `bslap-v4-776050f69d21fd34`. The initial candidate on a local test device
loaded all six qualified ROMs and ran 120 headless frames each with unchanged
save files, reporting 32 KiB SRAM and the expected 8-byte Gen 2 RTC interface.
`tests/butterflyos-bslap-netpacket-core-test.py` is a read-only native-core ROM-load,
frame, SRAM and RTC smoke test; it never writes a user save.

The first live candidate passed a Gen 1 trade/battle after a retry, but Gen 2
reported “friend is not ready.” Logs showed that its two-second timeout then
permanently disabled serial callbacks. The v2 candidate makes timeouts recoverable
and adds sequence-tagged request/reply/cancel messages (protocol
`bslap-gambatte-netpacket-v2`). Both devices must be updated together.

The native frontend also redirected the joining player's save into `.netplay`.
The v2 launcher seeds both isolated startup paths and returns the most recently
written client result with its matching RTC sidecar. Startup can log `.netplay`
then switch back after recognizing Netpacket; neither location is assumed to be
the final save destination. Regression tests distinguish the
updated client result from the unchanged seed copy.

The recoverable-timeout candidate connected Crystal and Gold: Gold entered the
trade room while Crystal remained at “Please wait” after saving. Both emulators
were running, both transport peers were connected, neither queue held a request,
and no new timeout was logged. Crystal's serial control was external/waiting
while Gold's transfer was idle. This is an unresolved handshake/timing failure,
not a qualified Gen 2 result.

The current diagnostic build adds bounded INFO traces (up to 512 packet events
and 512 serial-control writes). Create `bslap/serial-trace` beneath the normal
ButterflyOS configuration directory before a session to enable it; remove the
marker for subsequent sessions to disable it. The marker is not installed in an
image. The trace includes emulation frames, serial control values and byte
sequence IDs. Logging may affect timing, so a fix must also pass without tracing.

A subsequent traced Crystal-host/Gold-join attempt completed a trade. The user
reported slower connection steps. Both logs reached their bounded trace caps;
the host logged one recoverable byte timeout and neither logged a disconnect.
This is a successful individual Gen 2 trade, not proof the earlier asymmetric
handshake failure is fixed: this build added tracing, not a new timing fix.
Traces were retained locally, and the live trace markers were removed for the
next sessions. Both games then exited cleanly; both ordinary saves validated,
changed from their backups, and exactly matched their updated session result.
The joiner's root result was updated while its `.netplay` file remained the seed,
confirming why the launcher must consider actual changes in either location.

A fresh, untraced Crystal-host/Gold-join session completed both a trade and battle.
The user reported substantially smoother, more responsive behavior. This is a
subjective live comparison, not a measured FPS/power benchmark. Logs confirmed
zero trace lines, three recoverable serial-byte timeouts on the host, and a
joiner netplay disconnect after the host was no longer running. The successful
run does not erase the earlier asymmetric entry failure. Reverse roles, current
Gen 1 protocol regression tests, repeated staggered entry/exit, RTC persistence,
and the broader pairing/acceptance matrix still need qualification. Do not publish this backend based on
unit tests or a successful core load alone.

## Problem and intended result

The user reports that Gen 1/2 linking works but feels laggier and has poor audio.
Each device currently emulates both linked Game Boys and participates in
RetroArch's normal synchronized netplay. Additional emulation/rollback work is
a plausible contributor, **not a measured diagnosis**. Both emulators had already
exited when initial CPU settings were inspected; idle readings cannot identify
the gameplay bottleneck. Wi-Fi jitter and audio configuration remain possible
contributors.

Investigate one emulated Game Boy per physical device, exchanging serial/link
data rather than running the complete pair on both devices. This resembles the
Gen 3 architecture but cannot reuse its GBA protocol or timing unchanged.

## References to evaluate

1. [Gambatte Netpacket serial implementation, PR #266](https://github.com/libretro/gambatte-libretro/pull/266).
   This was open when reviewed. Audit and pin the actual implementation before
   testing; an open proposal is not a supported upstream feature or proof of
   compatibility with our RetroArch build. Gambatte is the preferred first
   candidate because ordinary GB/GBC gameplay already uses it successfully.
2. [DoubleCherryGB network-link fork](https://github.com/perrello/doublecherryGB-libretro).
   Its documentation describes a single-instance Netpacket mode exchanging only
   link-cable data. Check the code, provenance and hardware performance rather
   than assuming the documented behavior is qualified for ButterflyOS. Audit
   distribution/event assets before considering any packaged build.

Historical TCP-link prototypes are not a qualified fallback for this goal.
Revisit their recorded failures before repeating old approaches. No kernel
change is currently proposed; start with emulator, frontend and launcher work.

## Proposed sequence

1. Record short, repeatable baseline tests of the current SameBoy sessions:
   normal gameplay and active trade/battle, FPS/game speed, CPU frequency/load,
   audio underruns and netplay stalls. Use matching network/power conditions.
2. Keep this work on its separate experimental branch/backend. Preserve the
   working SameBoy launcher and use copied test saves on two local test devices.
   Audit the Netpacket API and serial scheduling before investing in integration.
3. Build a minimal candidate and test Gen 1 first, then Gen 2. Do not make a full
   OS image merely to begin the experiment. Ordinary game defaults stay separate.
4. Compare against the baseline. Stop or revise if packet synchronization causes
   worse stalls, emulation errors, save problems, or no practical improvement.
5. Only integrate into a future image after the criteria below pass. Keep the
   known-working backend available during development.

## Acceptance criteria

- Measurably better or equivalent responsiveness, stable game speed, and clean
  audio on the Flip, including active link-room gameplay.
- Gen 1 Red/Blue/Yellow pairings and Gen 2 Gold/Silver/Crystal pairings: trades,
  battles, host/join reversal, repeated sessions and staggered room exits.
- Save, quit and reload on both devices; ordinary SRAM and Gen 2 RTC survive.
  Reject save conflicts and preserve recovery copies. No ROM transmission.
- Menu + Start twice exits reliably; Bluetooth controls and the existing
  host-waits-for-joiner flow remain usable.
- Gen 1 colorization is deliberately qualified; Gen 2 native colors remain
  correct. Do not assume the SameBoy palette patch applies to another core.
- Clear behavior for disconnects, latency spikes and incompatible backends.
- Gen 3 remains unchanged. Gen 1-to-Gen 2 Time Capsule, internet play and external
  link hardware are separate goals, not implied by this experiment.

The goal is a smoother alternative, not merely a successful connection. No
release date or performance improvement is promised before measurement.


## Gen 1 first-attempt regression still under investigation

The user reproduced a failed first room-entry request followed by a successful
retry with Blue hosting and Yellow joining. Both transport peers remained
connected, their queues were empty afterward, and no serial timeout was logged.
Both endpoints had initiated clocked transfers during the session; initial
clock-role negotiation is a hypothesis, not a confirmed cause. Bounded tracing
was enabled for the next fresh session to capture the first failure before a
retry changes the games' handshake state. This remains a release blocker for
selecting the new backend as the ordinary Bslap default.


### Captured cause and v3 candidate

The fresh first-attempt trace captured one outgoing internal-clock request on
each device, both sending `01` and receiving `01`. Both games then armed external
clocks and waited indefinitely for a clock source. The peer connection remained
up. This confirms a crossed-clock startup race for this reproduced Gen 1 failure.
It does not establish that every previous Gen 2 asymmetry has the same cause.

Protocol `bslap-gambatte-netpacket-v3` also carries the actual byte each emulator
prepared when its external clock was armed. When two internal-clock requests
cross and both have such a prepared byte, the virtual cable consistently gives
the host clock authority and reconciles the exchange with those prepared values.
The algorithm does not assume Pokémon-specific byte values or modify ROMs/saves.
Normal transfers without two prepared external states retain their original
byte exchange. Requests still have sequence IDs and recoverable bounded waits.

`tests/bslap-netpacket-clock-collision-test.cpp` drives two actual serial instances
with both requests in flight. Forty cases cover both host orientations, arbitrary
prepared/current byte values, and ordinary exchanges without prepared states.
The C++98 serial tests, Python launcher/save tests and 60-second discovery tests
also pass. The dedicated core/backend packages build successfully. Both local
live devices have this candidate; first-entry, trade/battle and untraced
repeatability still need live validation before any full-image qualification.


### V3 live results

The user confirmed Gen 1 and Gen 2 work well with the candidate. Logs identify
Blue-host/Yellow-join and Silver-host/Gold-join sessions. All four emulator exits
were clean (status 0), ordinary saves validated and exactly matched an updated
session result. Gen 1 recorded one clock-collision resolution per endpoint and
no serial timeouts, validating that the reproduced first-entry race exercised
the new tie-break. Gen 2 recorded two recoverable byte waits on its host and one
on its joiner, with the user reporting successful play. These checks were traced;
markers have now been removed for a final untraced repeat. Broader game pairings,
role reversals, RTC persistence and the full rebuilt image remain separate
qualification steps. The branch has not been released or merged.


### Local rebuild authorized

After reporting successful Gen 1/2 tests, the user also confirmed the Gen 3
regression test passed and approved committing this branch and rebuilding a local
image. This is not release/publication approval. The rebuilt image must contain
the exact live-tested v3 core and retain the normal emulator binaries. The test
checklist includes first-attempt entry, trade/battle, saved-result reload,
untraced repeats, host-role reversal, RTC and the carried-forward UI changes.

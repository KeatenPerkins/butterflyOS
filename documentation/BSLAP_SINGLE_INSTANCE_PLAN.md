# Next Bslap goal: single-instance Gen 1/2 linking

Recorded October 26, 2026. **Deferred: do not implement in the current build.**
The current local test image comes from `ef48323cc4` and retains SameBoy's
dual-instance Gen 1/2 backend, its Special 3 palette, and the exit-hotkey fix.
This plan does not change that image or its release scope.

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
2. Create a separate experimental branch/backend when work resumes. Preserve the
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

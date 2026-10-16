# Experimental Flip V2 suspend — candidate 2

Local experimental branch, based on stable v1.0.4. Not a stable update and not
published through the updater. The existing stable release stays unchanged.

Candidate 2 integrates the live-tested charging LED, GPU regulator ownership,
Realtek USB power-reference, mountinfo and unused-controller fixes into a complete
image. Lid-close suspend is enabled by default on a fresh test installation.
Tools → Experimental Suspend can disable/re-enable it; the choice persists over
reboots. Detected helper failures persistently disable lid sleep until re-enabled.
The OHCI keyboard-controller experiment is excluded after the reported lockup.
Flash a clean test card and restore games/saves only; do not restore candidate 1's
local module overrides or autostart bind mounts over the packaged candidate 2.


## Candidate changes

- Firmware suspend configuration from Zlyme commit
  `327233b529cab6cce1f022b0543cab6c237ce5cc`: BSP-compatible
  `rockchip,pm-rk3568`, CONFIG_ROCKCHIP_PM_CONFIG=y, mode 0x5ec and GPIO wake 0x10.
  Required firmware-call failures abort suspend rather than silently proceeding.
- `vdd_logic` off during mem suspend, DDR retained; normal RK817 core still owns
  the sleep pin. Existing BL31 v1.45 and bootloader are unchanged.
- Both SD slots restricted to 3.3V high-speed, max 50 MHz, while retaining
  keep-power-in-suspend. Zlyme restricts only slot 1; this first candidate is more
  conservative so neither card requests a shared-rail UHS voltage switch.
- Combo-chip GPIO cut in suspend_late, after ordinary USB suspend; existing
  Bluetooth/Wi-Fi pre/post hooks and radio-stabilization delay are retained.
- Existing serialized device suspend/resume and Wi-Fi suspend-hardening remain.
- Tools → Experimental Suspend provides manual sleep, lid enable/disable and
  diagnostics, with device A/B controls. The normal fake-suspend shortcut remains
  disabled. No desktop/frontend replacement or change to emulator defaults.

## How to test

Start from a backed-up test card on .17. Initially leave the second card out.

1. Boot, check both battery/charging feedback and normal game operation.
2. Open Tools → Experimental Suspend → Save diagnostics.
3. Choose Sleep now, wait briefly, then press power or close/open the lid to wake.
   Confirm the tool returns and audio/input/display recover.
4. Lid sleep is already enabled on a fresh candidate 2 installation. Exit Tools,
   launch a game and close the lid.
   Open it to wake. The original running session should continue from RAM.
   There is no automatic save-state commit in this path: save normally first.
5. Repeat from menus, paused games and active games. Check ordinary saves,
   sound, controls and SD-card access after wake.
6. Shut down, insert a backed-up second game card, and repeat. Open games on
   each card and verify in-game save/reload after waking.
7. Test Wi-Fi and Bluetooth on/off and charging connected/disconnected. Confirm
   charging continues while asleep and percentages/status update after waking.
8. Repeat many cycles before an overnight test. Record sleep duration and
   battery readings; percentages alone are not a calibrated standby-current test.

Lid sleep starts enabled by default. An explicit disable choice or detected
helper failure persists over reboot; re-enable it explicitly in Tools.
While enabled, it pauses the lid auto-shutdown timer. Disable lid sleep to return
to display-only lid handling. If the test helper detects a failure, it attempts
to disable lid sleep; a kernel/storage hang can prevent that cleanup.

## Logs and acceptance

Each cycle creates a distinct directory under
`/storage/.config/butterflyos/suspend-tests/`. It writes before.json and syncs
before sleep, then after.json after returning. A state file without after.json
shows that a successful return was not recorded. Also examine the persistent
journal after a forced reset; successful Linux suspend alone is not acceptance.

The helper probes only actual mounted MMC data filesystems, writes a unique
4 KiB scratch file, verifies its bytes after resume and checks a new synced
write. It never remounts a failed card or edits games/saves. A successful probe
is a narrow check, not exhaustive filesystem validation. Kernel MMC timeout,
card-removal or ext4/I/O errors mean the cycle failed even if the UI recovered.

Candidate acceptance needs stable display/input/audio, correct CPU/DDR scaling,
working radios, charging in sleep, no card disappearance or filesystem errors,
ordinary saves intact, and repeated plus overnight sleep on one and two cards.

Source attribution: Zlyme's kernel patches retain their copyright/license
headers. Its scripts and NextUI are research references; ButterflyOS keeps its
own systemd, PipeWire, frontend and tool implementations.

## Integrated candidate 1 live follow-up: charging LED

The status LED now has `retain-state-suspended`. Pre/post sleep hooks sample the
battery status and apply the existing charging/default LED policy, respecting
LED-off preferences. Only the red status LED is retained; the green power LED
still goes dark during suspend. The first live test requires a device-tree
replacement and reboot. The helper also reads `/proc/self/mountinfo` directly,
without depending on the unavailable `findmnt` utility.

This retains the indication when entering sleep while charging. It does not
make the GPIO an autonomous charger LED: cable changes or charge completion
while deeply asleep may leave the indication stale until wake. No periodic wake
or extra charger wake source is enabled by this change. Test charging while
asleep, cable transitions, full charge, LED-off settings and normal wake.

## GPU regulator reference experiment

Log review found `unbalanced disables for vdd_gpu` in Mali's devicetree power
callbacks. The pinned driver starts runtime PM active and enables clocks at
probe, but previously did not acquire equivalent regulator references. Other
regulator consumers (including OPP) can keep hardware powered, which does not
provide an enable reference owned by kbase. Zlyme pins the same driver revision;
its package has no additional regulator fix. ROCKNIX's RK3326/RK3576 patches
already address the missing initial regulator enable.

RK3566 patch `003-balance-regulator-references.patch` acquires startup regulator
references, unwinds failed probe setup, and tracks each reference owned by kbase.
Runtime idle followed by system suspend cannot release the same reference twice;
failed enable/disable calls do not falsely transfer ownership. Voltage,
frequency and governor policies are unchanged. Host checks compile and execute
the actual patched startup/unwind and runtime helpers with simulated regulator
APIs, including shared consumers and repeated suspend-like sequences. Real
hardware acceptance still requires a cold boot, first sleep, repeated game/menu
sleep, ordinary GPU rendering, and checking fresh logs for regulator/clock errors.
The Realtek, regulatory-query and USB-controller warnings are separate work.

## Realtek USB runtime-PM reference experiment

The Realtek driver unconditionally set `autopm_cnt=1` even when
`usb_autopm_get_interface()` failed. Linux 7.0.2 uses
`pm_runtime_resume_and_get()` here, which rolls back its increment on failure.
The disconnect path subsequently released that nonexistent reference, producing
`Runtime PM usage count underflow`. Patch
`005-balance-usb-autopm-reference.patch` records ownership only after success.
Existing probe error policy, radio timing, and legacy-kernel handling remain.

The host test compiles the actual patched acquire/release blocks and checks
successful and failed acquisitions, other consumers' references, and repeated
teardown. The test module must be verified on .17 with Wi-Fi/BT enabled and
disabled, repeated lid sleeps, reconnection and current-boot warning review.
Do not infer that this fixes the separate nl80211 or xHCI warnings.

## Unused USB controller experiment

The remaining `xHC error in resume, USBSTS 0x401, Reinit` maps through sysfs to
`usb@fd000000`, the unused DWC3 host. Its two root hubs have no downstream USB
devices. The external host connector uses fd800000 EHCI, the RTL8733BU combo
uses fd880000 EHCI, and the lower gadget/charging connector uses fcc00000.
The board descriptions in ButterflyOS and the pinned Zlyme reference both
identify fd000000 as unused. USBSTS 0x401 includes the save/restore error bit;
Linux recovers by reinitializing the controller.

Disable only usb_host1_xhci in the Flip device tree, leaving its PHY definition,
the used USB controllers, charging and radio power policies unchanged. The live
test DTB must differ semantically only in usb@fd000000 status. Hardware acceptance
needs a reboot, repeated deep sleep without that warning, external USB keyboard
or storage access before/after wake, charging, Wi-Fi and Bluetooth. Do not disable
an active external USB controller or suppress the generic xHCI recovery warning.

## External USB keyboard companion test

The first rear-port keyboard/hub attempt produced no enumeration events. The
kernel already includes OHCI platform support, but fd840000 was disabled in the
board DT. Enable usb_host0_ohci, the companion for external fd800000 EHCI, so
low/full-speed keyboards can enumerate. The internal radio's fd8c0000 companion
remains disabled. This missing companion is a plausible keyboard issue, not proof
that it explains the undetected card hub. Test direct keyboard, USB hub/card
reader, reconnect and deep-suspend recovery. Actual input and external USB
connectivity are not accepted until verified on hardware.

The first OHCI-enabled test was followed by a lockup while attempting lid sleep
with a game running. The previous persistent journal survived but ended during
sleep preparation, so the exact hang point is not established. Reject the OHCI
candidate for now: restore only the immediately preceding DTB (SHA-256
9e23eac7518a6893e8856f5c58d2084f01527896f5d61bd67892683939089156),
keep the earlier module/LED fixes, and repeat the previous suspend baseline.
The source explicitly keeps external OHCI disabled pending investigation.

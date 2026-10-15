# Experimental Flip V2 suspend — candidate 1

Local experimental branch, based on stable v1.0.4. Not a stable update and not
published through the updater. The existing stable release stays unchanged.

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
4. Choose Enable lid sleep, exit Tools, launch a game and close the lid.
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

Lid sleep starts disabled after every boot. Enable it again explicitly in Tools.
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

# Next test image — November 4, 2026

All changes are consolidated from the Time Capsule development branch. This is
a local test build, not a published release. No kernel, RetroArch or emulator
core updates are included.

## Included changes

- Wi-Fi uses NetworkManager to enable/disable its radio independently of
  Bluetooth. Network Settings confirms the actual state and saves it. A switch
  callback lifetime fix prevents the menu crash observed during live staging.
- Bslap opens discovery before scanning local games, scans the chosen generation,
  rejects unrelated GBA headers early and reads selected GBA content once during
  preparation. Integrity checks and save backups remain enabled.
- Qualified English Gen 3 ROMs can be selected as raw files or single-ROM ZIPs.
  Full content hashes reject hacks and unsupported revisions. The picker labels
  compressed and uncompressed copies separately.
- Bslap adds native Gen 1 ↔ Gen 2 Time Capsule trading, with opposite-generation
  selection and matching session/backend checks. Story and party restrictions
  remain enforced by the games; cross-generation battles are unavailable.
- After a power-button wake with the lid still closed, lid sleep waits 12 seconds
  before re-suspending. Opening the lid, changing inputs/charging state or
  disabling lid sleep cancels the retry. Existing storage checks, USB-wake
  handling and bounded retry limits remain. After the retry limit, the device
  can remain awake; this is not an unconditional shutdown safeguard.

## Live validation

Wi-Fi toggles and connection checks passed while Bluetooth stayed active.
Selected-generation scan measured 2.77 seconds for ten candidates and ZIP
preparation 0.48 seconds on a development card; these are not end-to-end or
controlled comparative benchmarks.

Time Capsule trades passed Blue/Red/Yellow ↔ Crystal and Gold ↔ Blue.
Blue/Crystal passed both host directions and save/relaunch persistence. Silver
is deferred by user agreement. An early Blue freeze remains unexplained; repeat
connection and save tests on the full image. Gen 3 trade restrictions involving
the National Dex were initially mistaken for a ZIP problem; no ZIP-specific
trade defect was established.

Closed-lid power wake re-suspended after 12 seconds while charging; storage
checks passed. Opening during the grace period canceled re-suspend. Disabling
lid sleep was confirmed after correcting executable permissions on the temporary
live copy; the package already installs the script executable.

## Full-image test checklist

- Wi-Fi off/on with Bluetooth active; saved setting after reboot; actual network
  connection and controller fallback.
- Raw and ZIP Gen 3 host/join, battle/trade, clean exit and ordinary-save retention.
- Time Capsule first connection, opposite host direction, room exit, save and
  Continue persistence; Silver when a suitable test save is available.
- Closed-lid power wake while charging/unplugged, opening within 12 seconds,
  disabled lid sleep with HDMI, normal lid wake and repeated sleep/storage checks.

## Deferred investigations

Long-uptime HDMI/lid recovery and a stuck DRM worker have no root-cause fix.
A later functional HDMI test passed, which does not resolve that older report.
Missing FireRed progress also remains unexplained; recovery evidence was
preserved locally. Neither issue is claimed fixed in this image.

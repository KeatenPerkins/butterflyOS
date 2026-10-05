# ButterflyOS v1.0.1 — audio pacing fix

Maintenance release for **Miyoo Flip V2**, with updater build ID `20261007`.
This ID follows v1.0.0's `20261006`; it is a monotonic update identifier,
independent of the calendar date.

## Fixes

- Corrected the inherited PipeWire audio cycle size that held GB, GBA, and
  NES games near 47 FPS. The user confirmed all three systems returned to
  normal speed after the live configuration fix.
- Removed the ROCKNIX Discord prerequisite and closure warning from GitHub
  bug reports. Reports now ask for butterflyOS version and Miyoo hardware.
- Removed inherited Discord contact links from the issue chooser; support
  questions and feature requests can be submitted directly on GitHub.

## Download or update

Download `ButterflyOS-v1.0.1-Miyoo-Flip-V2.img.gz` for a new installation.
For an existing installation, use **Start → System Settings → Update
ButterflyOS**. Keep at least **3 GB free on the OS card**, connect front-port
power and Wi-Fi, wait for download/verification to finish, then restart the
system to apply the update. Confirm build `20261007` after installation.
See [update instructions](UPDATES.md).

For a quick fix on v1.0.0 without a full OS update, use the separate
[Tools-menu audio hotfix](AUDIO_FPS_HOTFIX.md). Devices `.17` and `.20`
already received this configuration fix directly.

## Validation scope

GB was measured near 47 FPS before the fix and near 60 FPS afterward on
`.17`; increasing CPU/GPU clocks did not resolve the original slowdown.
The user also confirmed GBA and NES work with the corrected audio setting.
The persistent configuration was validated on both devices. The rebuilt
release's artifact checks are recorded separately; the live configuration
checks do not imply the new complete image has been flashed and tested.
PortMaster, Bluetooth audio, and heavier emulators remain useful regression
checks because all audio applications share the smaller processing cycles.

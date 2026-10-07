# ButterflyOS v1.0.2 — storage tools and interface improvements

Stable maintenance release for **Miyoo Flip V2**, with updater build ID
`20261008` (following v1.0.1's `20261007`).

## Where to find RetroAchievements

Open **Settings → Game Settings → RetroAchievements Settings**.
You can also press **Start → Game Settings → RetroAchievements Settings**.
Account settings are available in normal mode; **Advanced Mode is not required**.
Enable RetroAchievements, enter your account username and password, save the
settings, and launch a supported game while connected to Wi-Fi.

The separate statistics browser is now hidden when frontend API credentials
are unavailable, preventing the browser's "Unauthenticated" error. Account
settings and in-game achievements remain available.

## Changes

- **Settings order:** Game Settings is first, Network Settings second.
- **Tools → SD Card Info:** quick capacity, used/free space, filesystem, and
  mount-status information for both cards; update-space information, Refresh,
  and Save Report. Includes the new transparent storage icon.
- **Tools → Format 2nd SD Card:** Butterfly Link-style appearance and device
  controls, with **A to select and B to cancel/back**. Both erase confirmations
  default to Cancel. The target is rechecked before formatting, and formatting
  stops if the second card remains mounted. Existing-card setup, Refresh, and
  Status remain available.
- New OpenBOR and EasyRPG system artwork and an updated Quick Start icon.
- Light blue ButterflyOS SSH banner, corrected hostname, and version/build
  information stamped from the finished image.
- Persistent journal logs sync every 30 seconds. Existing compression,
  storage limits, and retention remain unchanged.
- Installation/update documentation links to the latest stable image and
  matching checksum rather than a fixed release.

Existing FPS/audio fixes and PortMaster support are retained. Performance
settings are unchanged; the temporary performance tester is not included.

## Download or update

For a new installation, download **ButterflyOS-v1.0.2-Miyoo-Flip-V2.img.gz**
and its matching `.sha256` file from this release.

For an existing installation, open **Start → System Settings → Update
ButterflyOS**. Keep at least **3 GB free on the OS card**, connect power and
Wi-Fi, wait for download and verification to finish, and restart to install.
Confirm build **20261008** afterward. Game files, saves, and scraped artwork
on the storage partition are retained by the normal update process.

See [How to update](UPDATES.md#how-to-update) for instructions and older-build
migration requirements. The `.tar` asset is the on-device update package;
the `.img.gz` asset is for flashing a card.

## Validation

The full build and artifact audit passed: image/update checksums, filesystem
checks, matching SYSTEM/KERNEL payloads, packaged tools/artwork and menu changes,
content exclusions, and the package license manifest. All 43 frontend patches
applied to clean source, and 10 automated storage/formatting checks passed.
The test card was flashed while unmounted and verified using direct disk reads;
the user boot-tested the full image, approved the UI, and authorized release.
This is not an exhaustive test of every emulator, port, or peripheral.

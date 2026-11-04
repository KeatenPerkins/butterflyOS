# ButterflyOS v1.7.0 — Time Capsule, connectivity and lid-wake protection

**Release preparation draft — not published.** Locally tested Miyoo Flip V2
image, updater build **20261104**. The public version is proposed as v1.7.0.
The links below continue to serve the currently published release until promotion.

## Download and install

New users: download the OS image and matching SHA-256 checksum from the
[latest stable release](https://github.com/KeatenPerkins/butterflyOS/releases/latest).
Follow [installation and recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including
exporting your device-specific recovery backup. Flashing erases the card.
An already configured device does not need its internal preloader setup repeated.

After this candidate is published, existing users can save and exit games/tools,
then open **Start → System Settings → Update ButterflyOS**. Have at least **3 GB
free on the OS card**, charge to at least **50%**, and keep power connected through
the front USB-C port. Wait for download and verification, then choose **Restart
to Apply Update**. The new build should report **20261104**.

Normal updates retain games, saves, artwork, settings and Bdex collections.
Back up important files first. The update archive and developer/source records
are not extra files needed for SD-card flashing. See [How to update](UPDATES.md).

## Bslap Time Capsule trading

- Adds **Tools → Bslap → Host → Time Capsule** for native Gen 1 ↔ Gen 2 trades.
  Join selects a compatible opposite-generation game. Update both devices
  before using the new mode; matching Bslap backends are required.
- Use the ordinary Trade Center in Gen 1 and the Time Capsule desk in Gen 2.
  The Gen 2 story unlock must be complete. Party members must satisfy the
  games' native rules: Gen 1 species and moves, with no Eggs.
- This is in-game trading, including native trade evolution where applicable;
  it does not add cross-generation battles or require an ESP32/cable adapter.
- Blue/Red/Yellow with Crystal and Blue with Gold passed live tests. Blue/Crystal
  also passed both host directions and save/relaunch persistence. Silver remains
  a follow-up rather than a newly qualified pairing. Full-image Bslap testing
  subsequently passed.

Save normally on both games, leave the room safely and save on both before
exiting either emulator. Built-in controls: **hold Menu and press Start twice**.
See [Bslap](BSLAP.md) for backups and recovery.

## Faster Bslap preparation and Gen 3 ZIP support

- Join begins host discovery before scanning the local library. Hosting asks
  for the generation first and scans relevant system folders.
- Selected GBA data is read once during preparation for validation, hashing and
  ZIP extraction. Unrelated headers are rejected early; launch integrity checks
  and save backups remain enabled.
- Gen 3 accepts raw `.gba` files and ZIPs containing exactly one `.gba` file.
  Keep a matching ordinary `.srm` beside the ROM/ZIP using the same filename stem.
  Picker descriptions distinguish ZIP and uncompressed entries.
- Full ROM hashes now restrict Gen 3 to qualified English releases: Ruby and
  Sapphire revision 2, Emerald, FireRed and LeafGreen revision 1. Hacks and other
  revisions/languages are excluded. Gen 1/2 still require qualified raw ROMs.
  Existing raw and ZIP copies are not automatically deleted or deduplicated.

The user observed improved responsiveness during live testing. This is not a
controlled performance or battery benchmark. Gen 3's National Dex/story trading
restrictions still apply; an initially suspected ZIP trade problem was traced
to those restrictions rather than a proven archive-specific fault.

## Wi-Fi and Bluetooth controls

- Wi-Fi enable/disable synchronizes with NetworkManager and confirms the actual
  radio state in Network Settings. Bluetooth can remain active independently.
- Saves the confirmed toggle state and removes redundant disable operations.
- Fixes a menu callback lifetime problem that caused a crash while toggling
  Wi-Fi during development testing.

One fresh-install connection authenticated but timed out obtaining an IP address;
its retry failed in the Wi-Fi backend. Off/on recovered it, while another local
test device connected first try. That intermittent failure remains unresolved;
these radio/menu fixes are not claimed to fix DHCP or every connection failure.

## Accidental wake protection with the lid closed

With **System Settings → Hardware → Sleep When Lid Closed** enabled, a
power-button wake while the lid remains closed waits about **12 seconds** and
then tries to return to deep sleep. Opening the lid, changing inputs/charging
state or disabling lid sleep cancels the retry. Existing storage checks and
USB wake handling remain in place.

Automatic retries share a limit of three; repeated rapid wakes stop retries.
The device can remain awake after cancellation or an exhausted limit. Confirm
it has returned to sleep before putting it away. This does not create a save
state, shut down the console or guarantee against every accidental wake.
With lid sleep disabled, screen-only blanking remains available for HDMI use.

## Validation and remaining limits

All **670 package tasks**, **41 targeted automated tests** and **18 image checks**
passed. Checks include artifact hashes, decompression, GPT/filesystems, matching
flash/update KERNEL/SYSTEM, committed scripts and executable modes, backend
hashes, and the existing 2/255 brightness floor. Both test cards passed complete
readback verification. The user confirmed Bslap, deep sleep and the remaining
planned radio/ZIP/persistence checks passed on the full image.

No kernel, RetroArch or emulator-core version upgrades are included. Existing
Gen 3 room-exit limits remain: let one player initiate leaving and have the
other respond. An early live-test Blue freeze remains unexplained; later tests
passed. Silver-specific Time Capsule testing, the historical long-uptime HDMI
report and missing FireRed progress investigation remain follow-ups. See
[Known issues](KNOWN_ISSUES.md).

No new end-to-end OTA installation is claimed. Narrow updater packaging,
production-updater validation and final corresponding-source/license/release
asset preparation remain required before publication. Nothing is uploaded by
this documentation change.

Runtime source: `50813bd28c0404e79409c159a23f0adcab7e422c`.
Image SHA-256: `41da169539326faf352739de59f22e051a968fe4b2db8a9ddeb4f03a476501d1`.
The qualified image will retain these exact bytes; later documentation commits
do not change the tested runtime. See [Building](BUILDING.md).

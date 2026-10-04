# ButterflyOS v1.0.0 — first stable release

First stable release for **Miyoo Flip V2 only**, with device/update version
`20261006`. The numeric updater identity is a monotonically increasing build
ID; this release reserves it above v0.2.4's `20261005`.

## Changes since v0.2.4

- Corrected game-selection hints to **Y: Search** and **X: Add/Remove Favorite**.
- Replaced the misleading inherited unofficial-modification warning with
  normal ButterflyOS version confirmation; package validation remains intact.
- Fixed **Restart to Apply / Apply Update** to reboot the whole device.
- Matched the Ports system icon to the PortMaster ship icon in Tools.
- Added matching pixel hardware art for Atari 2600, PC Engine CD, and Sega CD,
  plus distinct cabinets for Arcade, Final Burn Neo, and CPS-I/II/III.
- Added update instructions and refreshed the stable-release documentation.

Includes the earlier menu/wide-screen fixes, centered game art, PortMaster in
normal Tools, grouped-system scraper persistence, confirmed Butterfly Link
Gen II PC-box persistence fix, and corrected ButterflyOS online updating.

## Install or update

For a new installation, download `ButterflyOS-v1.0.0-Miyoo-Flip-V2.img.gz` and
its matching `.sha256`, verify the checksum, and follow [Quick Start](QUICK_START.md).
Images contain no games or proprietary console BIOS files.

For v0.2.4, use **Start → System Settings → Update ButterflyOS**. For v0.2.3,
use **Start → Updates & Downloads → Start Update** (enable Advanced Mode if
hidden). Save and exit games, back up saves/recovery data, connect Wi-Fi and
front-port power, and allow at least **3 GB free on the OS card**. Wait until
download and verification finish, then choose **Start → Quit → Restart System**.
Older menus' Apply Update shortcut only restarts the frontend; use Restart
System to install this release. The installed v1.0.0 shortcut is corrected.
After installation, verify **ButterflyOS 20261006**. See [How to update](UPDATES.md).
Original v0.2.1 installations need the documented migration before online updating.

## Qualification and scope

The user tested each populated system individually, verified PortMaster and
offered games, and reported no remaining UI issues on the preceding build.
Earlier OTA transitions to v0.2.3 and v0.2.4 succeeded on the prepared Flip V2.
The newly generated eight system illustrations are additional source assets;
their packaged paths are checked separately from those prior hardware tests.
The final build audit records exact artifact checks and source revision.

Stable covers the documented Flip V2 feature set; this release does not promise
an LTS support duration or universal game/peripheral compatibility. Demanding
N64, DS, PSP, Dreamcast, and Saturn games vary in performance. Ports requiring
commercial data need the user's own game files. There is no A/B update rollback.
See [known issues](KNOWN_ISSUES.md), [controls](HOTKEYS.md),
[installation/recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md), and
[Butterfly Link](BUTTERFLY_LINK.md) for the remaining limits.

Source, build instructions, and licenses remain available in the `v1.0.0` tag,
[Building](BUILDING.md), [Third-party notices](../THIRD_PARTY_NOTICES.md), and
[source compliance](SOURCE_AND_LICENSE_COMPLIANCE.md).

Exact source revision, hashes, sizes, and final verification will be recorded
in the release audit after the build completes.

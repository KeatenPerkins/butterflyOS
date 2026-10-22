# ButterflyOS v1.4.0 — Bslap live trades and battles

Stable release for **Miyoo Flip V2**, updater build **20261022**.

## Download for SD-card flashing

Download **[the OS image](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.4.0/ButterflyOS-v1.4.0-Miyoo-Flip-V2.img.gz)** and its matching **[SHA-256 checksum](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.4.0/ButterflyOS-v1.4.0-Miyoo-Flip-V2.img.gz.sha256)**.
Follow [installation and recovery](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including exporting your device's recovery backup. Returning users reflashing an OS card do not repeat the internal preloader setup.

The `.tar`, its checksum and `butterflyos-update.json` serve the updater. The license manifest, source bundle and `release-audit.zip` are developer records; they are not needed for flashing. GitHub's Source code archives are not OS images.

## Update an existing installation

Save and exit games and tools. Open **Start → System Settings → Update ButterflyOS**. Wait for download and verification, then choose **Restart to Apply Update**. Have at least **3 GB free on the OS card**, charge to at least **50%**, and keep power connected through the front USB-C port. After installation, check for build **20261022**.

Normal updates retain games, saves, artwork, settings and Bdex collections. Back up important files first; flashing an image erases the card. See [How to update](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/UPDATES.md#how-to-update).

## Bslap: live Pokémon trades and battles

- Open **Tools → Bslap**, alongside Blink and Bdex; Advanced Mode is not required.
- Connect two ButterflyOS devices running this release to the same local network. One chooses Host and a generation/game; the other chooses Join. Both confirm Ready, then the host starts the games.
- Trade and battle within Gen 1 (Red/Blue/Yellow), Gen 2 (Gold/Silver/Crystal), or Gen 3 (Ruby/Sapphire/Emerald/FireRed/LeafGreen), using supported English ROMs and ordinary saves.
- Host and guest remain in the launcher until the session is ready. Gen 1, Gen 2 and Gen 3 appear in that order.
- Session backups, logs and protected save handling support recovery. Gen 1/2 use working-save copies and validate the local result before returning it after a clean exit.
- Gen 3 uses a dedicated newer RetroArch/gpSP pair. Gen 1/2 use the existing native RetroArch and linked SameBoy backend. Normal game launches and emulator defaults are unchanged; this release adds no kernel changes.

Bslap provides live in-game linking. **Blink** remains the save-editing/trading and event tool; **Bdex** remains the collection tool. No ROMs, saves or extracted Pokémon graphics are bundled. See the [Bslap guide](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BSLAP.md) for supported revisions, required files, controls and save recovery.

## Known limitations

- **Gen 3 only:** an intermittent communication error can occur when leaving a link room. Let one player initiate leaving and have the other respond to the resulting dialogue; avoid independently initiating exit on both devices. This gives better results but is not a guaranteed fix. Gen 1/2 passed the reported room-exit tests without this error.
- Same-generation local-network sessions only. Gen 1 ↔ Gen 2 Time Capsule, internet play and ESP32 adapters are not enabled. Compressed ROMs, ROM hacks and other languages are not offered.
- Gen 1/2 require both selected ROMs on both devices. Cross-core real-time-clock persistence is not fully qualified. Ordinary saves are the recovery baseline; do not use old save states to continue a linked session.
- Existing sleep/USB wake and quick lid-reopen limitations remain. See [Known issues](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/KNOWN_ISSUES.md).

## Validation and source

The exact image was rebuilt locally and tested on the local test device. All 669 build steps passed, as did image checksums, GPT and read-only filesystem checks, matching flash/update KERNEL and SYSTEM, packaged backend hashes, frontend visibility, installed-source checks and full card read-back. Eleven targeted Bslap automated tests passed. Reported two-device tests covered trades, battles, ordinary-save persistence, both hosting roles, and multiple Gen 3 game pairings; this is not an exhaustive compatibility matrix.

The tested runtime source is `a6c1655968e3a02de57cb8e0825b76fab5d29ce8`. Subsequent merge and release documentation do not change image bytes. Build prerequisites, exact upstream revisions and patches are documented in [the backend build guide](https://github.com/KeatenPerkins/butterflyOS/blob/v1.4.0/tools/bslap/README.md); the release source bundle preserves the dedicated backend sources and local build scripts. The package-license manifest and audit archive record component and artifact details.

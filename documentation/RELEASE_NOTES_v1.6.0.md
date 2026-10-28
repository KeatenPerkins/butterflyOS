# ButterflyOS v1.6.0 — smoother Bslap linking and expanded Bdex guidance

Stable release for **Miyoo Flip V2**, updater build **20261027**.

## Download for SD-card flashing

Download **[the OS image](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.6.0/ButterflyOS-v1.6.0-Miyoo-Flip-V2.img.gz)** and its matching **[SHA-256 checksum](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.6.0/ButterflyOS-v1.6.0-Miyoo-Flip-V2.img.gz.sha256)**.
Follow [installation and recovery](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including exporting your recovery backup. Reflashing an already configured device does not require repeating its internal preloader setup. **Flashing erases the card.**

The `.tar`, its checksum and `butterflyos-update.json` are for the built-in updater. The license manifest, corresponding-source bundle and `release-audit.zip` are developer records, not extra installation steps. GitHub's Source code archives are not OS images.

## Update an existing installation

Save and exit games and tools. Open **Start → System Settings → Update ButterflyOS**. Have at least **3 GB free on the OS card**, charge to at least **50%**, and keep power connected through the front USB-C port. Wait for download and verification, then choose **Restart to Apply Update**. Check for build **20261027** afterward.

Normal updates retain games, saves, artwork, settings and Bdex collections. Back up important files first. See [How to update](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/UPDATES.md#how-to-update).

## Bslap: Gen 1 and Gen 2 linking

- Gen 1/2 now run **one Game Boy per device**, replacing the previous dual-emulation default. Local testing found trades, battles and gameplay smoother and more responsive. This is a user-observed improvement, not a measured FPS or battery benchmark.
- Each device needs only its own supported ROM and ordinary save. No peer ROM or save is transferred. **Update both devices** before linking; matching Bslap backends are required.
- Fixed a reproduced first-connection clock collision that made both games wait for the other device and required a second attempt. A consistent clock tie-break handles simultaneous requests. Sequence-tagged replies reject stale data, and timed-out bytes allow retries without disabling the session.
- **Join searches for up to 60 seconds** when no host is found, shows a countdown and lets **B cancel**. Available hosts appear promptly. Hosting still waits for the joiner and the host's Start confirmation; no password typing is needed.
- Gen 1 uses **Special 3** for monochrome games. Yellow keeps its native GBC colors; Gen 2 keeps its native colors. Ordinary-game color settings remain separate.
- Bslap refreshes launch-time controller configuration, fixing newly flashed cards retaining Select as the exit hotkey. The built-in exit remains **hold Menu and press Start twice**, across all three generations.
- Gen 1/2 protect the original save during play, validate the updated local result after a clean exit, preserve appended trailers, and back up/return adjacent Gambatte RTC sidecars when available. Updated results are distinguished from unchanged seed copies in either frontend save location.
- The Gen 3 emulator/link binaries are unchanged and passed regression testing. SameBoy remains available as a development fallback for Gen 1/2.

See [Bslap](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BSLAP.md) for save handling and recovery.

## Bdex: where to find, evolve and obtain Pokémon

- **Where to find** now covers supported English Gen 1, Gen 2 and Gen 3 games, including species missing from your collection.
- Adds offline guidance for wild encounters, fishing, Headbutt/Rock Smash where applicable, gifts, eggs, fossils, NPC trades, static encounters and roaming Pokémon, plus evolution and breeding requirements.
- Shows pre-evolution sources, intermediate evolution steps and relevant game/version restrictions. Historical event access is distinguished from ordinary encounters and from Blink's gift/event tools.
- Gen 1 grass/cave and Surfing encounters are still read directly from your ROM. Additional guidance uses a pinned offline reference, with source labels. It does not inspect story progress or alter your ROM, save or collection.
- ROM selection, sprite preparation/refresh and Where to find now search **nested folders on both cards**. Qualified raw ROMs and single-ROM ZIPs work; duplicate paths are suppressed and nested directory symlinks are not followed.

Names and sprites still come from the user's matching ROM. No Pokémon ROMs, saves or sprite caches are bundled. Blink/Bdex copies do not trigger trade evolution; use an actual compatible in-game trade. See [Bdex](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BDEX.md).

## Controllers, palettes and interface

- Blink, Bdex and Bslap follow saved external-controller A/B bindings more consistently, including the tested 8BitDo mapping. Built-in Flip controls retain A Select/B Back.
- In ordinary RetroArch games, the built-in controls and first external controller can both control Player 1. Additional external controllers retain subsequent player assignments. Existing custom remaps can override this; Bslap keeps its separate routing.
- Fixed saved Gambatte colorization from Advanced Game Options, including per-game priority and older setting names. Unrelated core options are preserved.
- Gambatte's **GB Palette Cycling with L/R** is now opt-in and disabled by default, preventing shoulder presses from unexpectedly changing colors. Save/load hotkeys remain separate.
- Both ButterflyOS themes show **X Options** in the game-list footer.
- Installation documentation distinguishes reinstalling from initial preloader setup and explains official Miyoo firmware restoration before low-level recovery where appropriate, with the external Spruce recovery reference.

## Known limitations

The existing Gen 3 room-exit communication issue remains: let one player initiate leaving and have the other respond. This improves results but is not a guaranteed fix. Gen 1/2 can have recoverable waits while the other game is not ready; broader game-pair/host-role and cross-core RTC qualification is not exhaustive. The pre-play Gen 1/2 notice retains development wording in the exact tested image.

Connect controllers before opening the Pokémon tools. Existing sleep/USB wake, quick lid-reopen, battery-estimate and hardware limits remain. See [Known issues](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/KNOWN_ISSUES.md).

## Validation and source

All **670 package tasks** and **17 image checks** passed, including hashes, complete decompression, GPT/filesystems, flash/update payload consistency, exact embedded sources and backend hashes, the retained 2/255 backlight table, both theme labels, and private ROM/save filename exclusions. Both flashed cards matched the complete written image by direct readback.

The user approved the rebuilt image after Bslap Gen 1/2 tests, Gen 3 regression, controller inputs and Blink/Bdex features. Focused automated checks cover two-instance clock collisions in both host orientations, normal byte exchange, timeout recovery, stale replies, save/clock protection, Join search/cancel and nested ROM discovery. These tests do not prove every pairing or peripheral combination.

The release preserves the exact tested image bytes. The narrow updater archive contains the same tested KERNEL/SYSTEM, their checksums and identity metadata, and passes the production updater's manifest/archive validation. A new end-to-end OTA installation was not performed for this release; the previous v1.5.0 OTA test remains a separate historical result.

Runtime source: `4ea693e232925b145332986834d6dfbea5924514`. Later release-documentation commits do not change the image. Image SHA-256: `8532b3eb3cc26a98dded94ca6e3263e657654d42493ca6952af267b255eecbfa`. See [Building](https://github.com/KeatenPerkins/butterflyOS/blob/v1.6.0/documentation/BUILDING.md) and the [Bslap backend guide](https://github.com/KeatenPerkins/butterflyOS/blob/v1.6.0/tools/bslap/README.md) for corresponding source and pinned build inputs.

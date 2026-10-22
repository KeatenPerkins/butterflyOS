# ButterflyOS v1.2.0 — save backups and Bdex

Stable release for **Miyoo Flip V2**, updater build **20261018**.

## Download for SD-card flashing

Download **[ButterflyOS-v1.2.0-Miyoo-Flip-V2.img.gz](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.2.0/ButterflyOS-v1.2.0-Miyoo-Flip-V2.img.gz)** and its matching **[SHA-256 checksum](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.2.0/ButterflyOS-v1.2.0-Miyoo-Flip-V2.img.gz.sha256)**.
Follow [installation and recovery](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including exporting your device's own recovery backup. Returning users reflashing an OS card do not need to repeat the internal preloader setup.

The `.tar` package and `butterflyos-update.json` are for the updater. `release-audit.zip` contains optional developer verification records. The package-license manifest documents bundled components. GitHub's Source code archives are not flashable images.

## Update an existing installation

Save and exit your games and tools. Open **Start → System Settings → Update ButterflyOS**, wait for download and verification, then choose **Restart to Apply Update**. Keep power connected through the front USB-C port, charge to at least 50%, and have at least **3 GB free on the OS card**. After installation, check for build **20261018**.

Normal updates retain games, saves, artwork, settings and Bdex collections. Back up important files first; flashing an image erases the card. See [How to update](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/UPDATES.md#how-to-update).

## Automatic Save Backup

- Opt in under **Start → System Settings → Hardware → Automatic Save Backup**; off by default.
- Copies supported ordinary saves from either SD card to the other. Requires two prepared, writable cards.
- Keeps five verified versions per save and avoids duplicate copies of unchanged files. Saves with matching names on different cards remain separate.
- Leaves at least 10% of the destination card's capacity free; copies wait when the reserve cannot be maintained.
- Starts checking about three minutes after activation, then about every five minutes while awake. Recently modified files wait at least two minutes.
- Restoration is manual. Save states, games, artwork, settings and Bdex databases are excluded.

See [Save Backup and restoring progress](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/SAVE_BACKUPS.md).

## Bdex: Gen 1–3 Pokémon collections

- New **Tools → Bdex**, with separate generation collections, species counts and missing-species browsing.
- Copy all party/PC Pokémon or selected entries from supported saves without changing the originals. Exact native-record duplicates are skipped; distinct Pokémon of the same species remain separate.
- Inspect trainer identity, moves, held items, shiny status and generation-specific attributes.
- Controller-friendly ownership, source-game, type and name filters, sorting and letter navigation. Filters and Web viewer appear near the top of Options.
- Copy exports within each generation, plus Gen 1 → Gen 2 and Gen 2 → Gen 3. Destination checks and protected backups remain in place. These are save edits, not link-cable emulation; no automatic trade evolution is provided.
- Recoverable Trash, confirmed permanent deletion, checked database backups and recovery.
- Shared Blink sprite caches, ZIP-aware supported ROM selection, **Refresh sprites**, cache reconnection and sharp HDMI text.
- New Bdex Tools artwork and browser header; light backgrounds improve Gen 1/2 sprite visibility.

The optional **read-only web viewer** is disabled by default. Enable it in Bdex Options and open the displayed address on the same trusted network. Log in as **bdex** with the current device SSH password. It supports browsing, searching, filtering and inspecting; it cannot edit collections or saves.

Sprites and names come from the user's matching ROMs. No Pokémon ROMs, saves or extracted sprite caches are bundled. Supported English retail revisions are listed in the [Bdex guide](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BDEX.md). Other languages, revisions and hacks are not qualified. Bdex databases need their own backups; Automatic Save Backup does not protect them.

## Blink and documentation

- **Butterfly Link is now named Blink** in Tools and current documentation. Existing launcher/data paths remain compatible.
- Added Bdex usage, import/export, duplicate behavior, Trash, database recovery, web access and compatibility guidance.
- Added save-backup timing, storage requirements and step-by-step manual restoration instructions.

## Validation and limitations

The exact R4 image was rebuilt locally and tested on the local test device. All 668 package steps, image checksums, GPT/FAT/ext4 checks, packaged-source/artwork/service checks and full SD-card read-back verification passed. All 12 ordinary test saves backed up with zero errors and matched their originals. Earlier feature regression checks covered Bdex, the web viewer, sprite refresh and backup behavior, including recurring timer activation.

This does not qualify every species, ROM revision, emulator, save or peripheral. Existing sleep/USB limitations remain: USB power changes briefly wake the device before it returns to sleep with the lid closed; a very quick lid close/open can miss the wake event, remedied by closing and reopening. Native Gen III island events remain excluded pending testing. See [Known issues](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/KNOWN_ISSUES.md).

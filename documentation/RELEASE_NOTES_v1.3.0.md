# ButterflyOS v1.3.0 — Gen III events and gifts

Stable release for **Miyoo Flip V2**, updater build **20261020**.

## Download for SD-card flashing

Download **[ButterflyOS-v1.3.0-Miyoo-Flip-V2.img.gz](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.3.0/ButterflyOS-v1.3.0-Miyoo-Flip-V2.img.gz)** and its matching **[SHA-256 checksum](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.3.0/ButterflyOS-v1.3.0-Miyoo-Flip-V2.img.gz.sha256)**.
Follow [installation and recovery](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including exporting your device's own recovery backup. Returning users reflashing an OS card do not need to repeat the internal preloader setup.

The `.tar` package and `butterflyos-update.json` are for the updater. `release-audit.zip` contains optional developer verification records. The package-license manifest documents bundled components. GitHub's Source code archives are not flashable images.

## Update an existing installation

Save and exit your games and tools. Open **Start → System Settings → Update ButterflyOS**, wait for download and verification, then choose **Restart to Apply Update**. Keep power connected through the front USB-C port, charge to at least 50%, and have at least **3 GB free on the OS card**. After installation, check for build **20261020**.

Normal updates retain games, saves, artwork, settings and Bdex collections. Back up important files first; flashing an image erases the card. See [How to update](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/UPDATES.md#how-to-update).

## Blink: native Gen III island events

Open **Tools → Blink → Local Transfer → Gen 3 → Gen 3 Island Events**. Enable or replay an event, review the preview and explicitly Commit. A verified original backup is retained.

- Emerald: Eon Ticket, MysticTicket, AuroraTicket and Old Sea Map.
- Qualified English FireRed/LeafGreen revision 1: MysticTicket and AuroraTicket.
- Qualified English Ruby/Sapphire revision 2: Eon Ticket, preserving the normal roaming Pokémon.
- Normal story/postgame requirements remain. English Old Sea Map is labeled as an expanded experience; its historical distribution was Japanese.

Save normally and exit before editing, then load the ordinary save rather than a save state. See the [Blink guide](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLY_LINK.md) for ROM requirements and ferry instructions.

## Blink: new generated gift collections

- Six GameCube gifts, including Pikachu, Celebi, Mt. Battle Ho-Oh and XD starter equivalents.
- 48 distinct PCNY adult recipes, with documented variants grouped.
- 24 tenth-anniversary recipes across 23 species.
- 13 regional gifts, including special-move Pikachu variants, National Ribbon Metang, Mew and Jirachi.
- 135 purified Shadow gift equivalents: 49 Colosseum recipes, 83 XD recipes and three expanded English e-Reader equivalents.

These options support the five qualified English retail Gen III games. Gifts use a BLINK trainer identity, recipe-specific shiny policies, ROM-derived data and protected preview/backup/Commit. Purified gifts arrive already purified in a GBA PC box; this does not emulate GameCube linking, Shadow capture or purification. Original distributor identity and RNG are not reproduced. No Pokémon ROMs, saves or extracted sprite caches are bundled.

## Safety and maintenance

- Strengthened Blink stale-save checks before protected copies, swaps and generation conversions; changed saves require fresh preparation.
- Improved Bdex database recovery after an interrupted SQLite write while retaining writer locking and read-only viewer protections.
- Hardened boot-update write/remount checks and destination verification. Failures stop before success/cleanup/reboot and retain the package and diagnostics.
- Bounded suspend diagnostic retention to 20 successful and 10 failed/incomplete sessions plus active logs; suspend behavior is unchanged.
- Corrected shared Gen III shiny-palette offsets for qualified Emerald, Ruby/Sapphire and FireRed ROMs in Blink and Bdex; older caches refresh when the ROM is selected again.
- Updated Bdex artwork and event documentation.

## Validation and limitations

The exact image was rebuilt locally and tested on the local test device. All 668 package steps, image checksums, GPT/FAT/ext4 checks, flash/update payload matching, installed-source and embedded-initramfs checks passed. Full SD-card read-back matched the written image. The user confirmed the full integration checklist, including gifts, an island event, save/reload, Blink/Bdex, save backup, charging, sleep and HDMI.

Automated event, gift and save-safety checks also passed. This is not exhaustive qualification of every recipe/game combination or a new overnight sleep test. Existing USB wake and quick lid-reopen limitations remain. In-place updates are not power-loss-proof; the first update from an older build uses its installed boot updater. See [Known issues](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/KNOWN_ISSUES.md).

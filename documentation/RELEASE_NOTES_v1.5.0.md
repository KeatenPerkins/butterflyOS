# ButterflyOS v1.5.0 — Bdex stats and locations, Blink fixes

Stable release for **Miyoo Flip V2**, updater build **20261023**.

## Download for SD-card flashing

Download **[the OS image](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.5.0/ButterflyOS-v1.5.0-Miyoo-Flip-V2.img.gz)** and its matching **[SHA-256 checksum](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.5.0/ButterflyOS-v1.5.0-Miyoo-Flip-V2.img.gz.sha256)**.
Follow [installation and recovery](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including exporting your recovery backup. Returning users reflashing a card do not repeat the internal preloader setup. **Flashing erases the card.**

The `.tar`, its checksum and `butterflyos-update.json` are for the built-in updater. The license manifest, corresponding-source bundle and `release-audit.zip` are developer records; they are not needed for flashing. GitHub's Source code archives are not OS images.

## Update an existing installation

Save and exit games and tools. Open **Start → System Settings → Update ButterflyOS**. Have at least **3 GB free on the OS card**, charge to at least **50%**, and keep power connected through the front USB-C port. Wait for download and verification, then choose **Restart to Apply Update**. Check for build **20261023** after installation.

Normal updates retain games, saves, artwork, settings and Bdex collections. Back up important files first. See [How to update](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/UPDATES.md#how-to-update).

## Bdex: graphical inspector and Gen 1 locations

- The inspector adds your ROM-derived Pokémon sprite and a radar graph, while retaining the existing Pokémon details and history. **L/R** or **Left/Right** changes between **Summary**, **Stats** and **Details**.
- Graph modes distinguish calculated stats, IVs/DVs and training. Gen 1/2 training uses the original stat-experience scale; it is not a battle stat or modern EV value. Numbers and labeled scales remain visible.
- Gen 1 species now offer **Stored copies** and **Where to find**, including species you do not own. Choose your supported English retail Red, Blue or Yellow ROM to read grass/cave and Surfing locations and levels.
- Raw ROMs and ZIPs containing one ROM work. Fishing, gifts, trades, evolutions and special encounters are not indexed yet. An empty result does not mean the Pokémon is unobtainable; Gen 2/3 location lookup is not included.
- Collection screens redraw correctly after window exposure or display changes. Text continues to render at the output resolution for sharp HDMI display.

Names, sprites, base stats and encounter species come from your matching ROM. No Pokémon ROMs, saves or extracted sprite caches are bundled. See the [Bdex guide](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BDEX.md).

## Blink: save selection, ZIPs and sprite recovery

- Fixed a Gen 1 preview crash caused by blank optional text, which could close the graphical interface and expose the older dialog fallback.
- Save selection shows the trainer first and retains full wrapped filenames, making personal saves easier to distinguish from test saves or long ROM names.
- Gen 1/2 gifts and Crystal event qualification match ZIP ROMs by decompressed contents rather than the ZIP-container hash. Exact supported-ROM qualification remains in place.
- A damaged or unreadable ROM candidate no longer hides a valid matching ROM later in the list.
- Added **Sprites / Refresh Sprites** to Blink's main menu. Choose a generation and matching ROM to rebuild the shared Blink/Bdex sprites and names. No save is required or modified.

See the [Blink guide](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLY_LINK.md).

## Tool controls and minimum brightness

- Corrected **A Select / B Back** in Blink, Bdex and Bslap through native SDL controller input. Duplicate raw joystick events are ignored, so one press cannot open a menu and immediately cancel it.
- Held keyboard confirmations and lingering button presses no longer immediately dismiss the following tool dialog. Saved external-controller mappings load before the built-in Flip-specific mapping.
- Lowered minimum backlight output for dark-room play. The menu still displays **5%**; the tested hardware floor is now **2/255**, retaining the 800 Hz frequency and startup delay. Dimming, lid reopening and full power-off/power-on passed local device testing. The lower 1/255 experiment left the screen dark and is not included.
- Existing emulator defaults and Bslap backends are retained. The kernel was rebuilt for the backlight-table change.

## Known limitations

- Connect an external controller **before opening** Blink, Bdex or Bslap. Connecting another controller while a tool is open currently requires reopening the tool. Arbitrary controllers are not exhaustively qualified.
- Bslap's existing **Gen 3 room-exit communication error** remains: let one player initiate leaving and have the other respond. This improves results but is not a guaranteed fix.
- Existing sleep/USB wake, quick lid-reopen and battery-estimate limitations remain. See [Known issues](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/KNOWN_ISSUES.md).

## Validation and source

The exact image was rebuilt locally and tested on the local test device. All 669 package steps passed. Checks covered image integrity, GPT/filesystems, flash/update payload consistency, embedded source files, backend hashes, the backlight table and complete direct SD-card read-back. Focused regressions covered duplicate input, blank text, save labels, ROM matching and forced sprite repair across all three generations, including 48 raw/ZIP gift comparisons.

A private update from **20261022 → 20261023** passed the installed updater's validation, staging and real reboot installer. Installed KERNEL/SYSTEM and tool hashes matched the tested image. The 41,813-file library inventory and all 31 checked ordinary-save hashes were preserved; the only settings-field change was the last menu visited. This test redirected network requests to a private source; public GitHub discovery was checked separately at publication.

Tested runtime source: `404c29e3af7da12d5552bfa63ce9f696a76010f1`. Later release-documentation commits do not change image bytes. The release includes a package-license manifest, dedicated Bslap corresponding source, and an optional audit archive. Source instructions are in [Building](https://github.com/KeatenPerkins/butterflyOS/blob/v1.5.0/documentation/BUILDING.md) and the [Bslap backend guide](https://github.com/KeatenPerkins/butterflyOS/blob/v1.5.0/tools/bslap/README.md).

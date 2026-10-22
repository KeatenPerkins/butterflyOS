# ButterflyOS v1.1.0 — deep sleep and Gen III gifts

Stable release for **Miyoo Flip V2**, updater build **20261016**.

## Download for SD-card flashing

Download **[ButterflyOS-v1.1.0-Miyoo-Flip-V2.img.gz](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.1.0/ButterflyOS-v1.1.0-Miyoo-Flip-V2.img.gz)** and its matching **[SHA-256 checksum](https://github.com/KeatenPerkins/butterflyOS/releases/download/v1.1.0/ButterflyOS-v1.1.0-Miyoo-Flip-V2.img.gz.sha256)**.
Follow [installation and recovery](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including your device's own preloader backup. Returning users who only reflash an OS card do not need to repeat the internal preloader setup.

The `.tar` package and `butterflyos-update.json` are for the updater. `release-audit.zip` contains optional developer verification records. GitHub's **Source code** archives are not flashable images.

## Update an existing installation

Save and exit games and Butterfly Link. Open **Start → System Settings → Update ButterflyOS**, download and verify the update, then restart the system to install. Keep power connected, battery at least 50%, and at least **3 GB free on the OS card's storage partition**. Check for build **20261016** after installation. See [How to update](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/UPDATES.md#how-to-update).

## Deep sleep and charging

- Deep sleep on lid close is enabled by default on fresh installations. Improvements to SD-card signaling, GPU regulator handling and Wi-Fi power handling address earlier suspend/resume failures.
- **System Settings → Hardware → Sleep When Lid Closed** replaces **Lid-Closed Shutdown** and **Save Game Before Lid Shutdown**. With sleep Off, only the built-in screen turns off; games, networking and HDMI audio continue. The preference persists after reboot.
- Fixed the Hardware menu caching an old setting and unexpectedly turning sleep back on.
- Charging LED behavior is retained during sleep. Connecting or disconnecting charging USB briefly wakes the device; it returns to sleep if the lid remains closed. Opening the lid or using the power button cancels the automatic return.
- The previous lid audio mute/unmute mechanism is removed. Sleep retains the running session in RAM; save games normally before long breaks because losing power loses that session.

## Butterfly Link

- Pokémon inspectors show English move names and Gen II/III held-item names extracted from the user's matching ROM. Older caches refresh as needed.
- Gen I/II sprite extraction accepts ZIPs containing exactly one matching GB/GBC ROM, alongside existing Gen III ZIP support.
- Menus and inspector text render at the active display's resolution for sharper HDMI output while preserving the handheld layout.
- Adds **39 Gen III egg recipes**: 4 Pokémon Box, 15 PokéPark, 10 anniversary options including two shiny Pichu variants, 4 promotional and 6 PCNY Wish eggs.
- Adds five direct-gift gameplay equivalents: **Jirachi, Celebi, Mew, Deoxys and shiny Berry Program Zigzagoon**.
- Gift delivery supports qualified English Emerald, Ruby/Sapphire revision 2 and FireRed/LeafGreen revision 1 ROM/save pairs. Generated equivalents use expanded receiving-game eligibility, not original distribution restrictions.
- Direct gifts use original trainer **BLINK** and a distinct trainer ID for the native fateful-encounter memo. Normal traded-Pokémon obedience/experience rules apply. Eggs retain the recipient's identity and normal hatch information.
- Gift preview, explicit confirmation and protected backups remain in place. No ROMs, BIOS files, personal saves, bundled sprite caches or original distribution Pokémon records are included. Gen III island-event activation remains excluded pending gameplay qualification.

See the [Butterfly Link guide](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/BUTTERFLY_LINK.md) for recipes, supported revisions and save precautions.

## Artwork and documentation

- Updated Restore Stock artwork and transparent controller artwork for Controls Guide.
- Added verified [USB Gadget File Transfer instructions](https://github.com/KeatenPerkins/butterflyOS/blob/butterflyOS-main/documentation/TRANSFERRING_GAMES.md#option-6-usb-file-transfer) for copying games through the front charging/data USB-C port.
- Clear image/checksum links for flashing, with optional developer records grouped into one audit ZIP.
- RetroAchievements remains under **Settings / Start → Game Settings → RetroAchievements**.

## Validation and known limitations

The exact locally rebuilt image passed all 668 package steps, image/filesystem checks, packaged-content checks and complete SD-card read-back verification. User testing passed on the local test device. All three recorded sleep cycles returned successfully; the overnight cycle lasted approximately **8 hours 58 minutes**, with read/write checks passing on both SD cards. HDMI, charging LEDs, USB return-to-sleep, trading and gift testing informed this release; this does not qualify every game/save/peripheral combination.

- USB charging changes briefly wake the device for about 10 seconds before it returns to sleep.
- Very quick lid close/open may miss the wake event. Close and reopen again to wake.
- Rear USB host/keyboard support remains unqualified.
- Wi-Fi transition/regulatory warnings and an earlier isolated display underrun remain recorded; neither prevented the overnight test from passing.
- Battery percentage remains an estimate. No claim of universal battery calibration or suspend reliability is made.

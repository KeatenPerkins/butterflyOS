# ButterflyOS v1.0.4 — controls, battery feedback, themes and Butterfly Link fixes

Stable release for **Miyoo Flip V2**, updater build **20261013**. This is the
exact local rebuild that passed image checks and user-confirmed live tests on the local test device.

## Controls and emulation

- Fixed external Bluetooth controller hotkey conflicts: RetroArch menu, FPS,
  fast-forward and save-state controls. Handheld controls return after disconnect.
- gpSP is the default for the normal GBA category, with clearer gpSP/mGBA choice
  descriptions and corrected default-core generation. Existing system and per-game
  choices remain supported; GBA Hacks and Videos retain their separate defaults.
- Emulator settings and available alternatives are documented in
  [Emulators and performance](EMULATORS_AND_PERFORMANCE.md).

## Battery, brightness and lid behavior

- Battery indicators refresh while the menu is idle, with a two-second polling
  interval and RK817 cable-event refresh and boot-estimate improvements.
  Battery percentage remains an estimate; this does not claim to solve every gauge issue.
- The charging LED stays lit while the driver reports Charging, including above
  97%, and returns to the configured normal indication when charging ends.
- The minimum display setting remains 5%, but now uses a lower PWM level of 3.
  Dimming, lid reopening and a full shutdown/power-on passed device tests.
- **Start → System Settings → Hardware → Lid-Closed Shutdown** now offers
  **1 and 5 minutes**, alongside Off, 15, 30 and 60 minutes. Off remains the default.
- Closing the lid mutes audio; reopening restores the previous mute state.
- **Save Game Before Lid Shutdown** retains its existing protected RetroArch
  auto-save and shutdown behavior. Unsupported games and failed saves defer shutdown.

True suspend remains disabled. Closing the lid turns off the display while the
system remains running until an enabled shutdown timer expires. Suspend research
is separate from this stable release.

## Themes

**User Interface Settings → Theme Set → ButterflyOS White** provides white card
outlines and removes the large butterfly above the home carousel while keeping
the existing layout and artwork. Packaged theme discovery works on fresh cards
and updates. See [theme creation and customization](THEMES.md).

## Butterfly Link

- The Gen III ROM picker filters by supported English game headers, rather than
  filenames, excluding unrelated GBA games. Filenames may be in any language.
- Supported ROMs can be uncompressed `.gba` files or ZIPs containing exactly one
  GBA ROM. Sprite extraction reads the ROM inside the ZIP. `.7z` is not supported.
- Fixed LeafGreen revision-1 sprite extraction.
- Fixed swaps across Gen III save families, including Emerald ↔ LeafGreen.
- B in the Pokémon list returns to box selection; B at box selection cancels.
- Gen I and II gifts/events remain available. The unfinished Gen III island-event
  prototype is excluded from this image pending proper gameplay qualification.

Exit games before editing saves and verify received Pokémon using the ordinary
in-game save, rather than an older save state. See the [Butterfly Link guide](BUTTERFLY_LINK.md).

RetroAchievements remains under **Settings / Start → Game Settings →
RetroAchievements**.

## Install or update

For a fresh card, download **ButterflyOS-v1.0.4-Miyoo-Flip-V2.img.gz** and its
matching `.sha256`. Follow [installation and recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md),
including the device's own preloader backup.

Existing installations: **Start → System Settings → Update & Downloads →
Check for Updates**. Keep sufficient battery charge and free space, wait for the
download and verification, then restart to install. Verify build **20261013**
after reboot. Read [How to update](UPDATES.md#how-to-update) for requirements and
older-build migration. The `.tar` asset is for the updater; flash the `.img.gz`
for a fresh installation.

## Validation

All 668 package steps passed. Image hash/gzip, GPT, FAT/ext4, boot checksums,
image/update payload consistency and packaged content checks passed. All 23
lid-shutdown checks passed; source-level LED and mute-state checks also passed.
The user confirmed the image rebuilt for the local test device passed live testing. No ROMs, BIOS files,
personal saves or generated Pokémon sprite caches are included in release assets.

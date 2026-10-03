# ButterflyOS v0.1.0 Alpha 2

Alpha 2 is the first public alpha release for the Miyoo Flip V2. It remains
test software and is not a stable release.

See [Quick Start](QUICK_START.md) and
[Installation and Recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md) before flashing.
Writing the image erases the selected card. Export your device-specific recovery
backup off-card before reflashing an existing ButterflyOS installation.

## Release record

- Source tag: `v0.1.0-alpha.2` (includes final release documentation)
- Exact image source commit: `39bb3a803bd481b7a610cf2b19509b2c13d39891`
- Image: `ButterflyOS-v0.1.0-alpha.2-Miyoo-Flip-V2.img.gz`
- SHA-256: `24eb2a762b55fb6aae77caf49c5450f3b3f1bf874b5cbc01016469dc0ab3aede`
- Target: Miyoo Flip V2 (`RK3566` / `Miyoo_Flip_V2`)

## Historical September pre-release records

An earlier fully hardware-tested pre-release baseline was built from
commit `f2ea99b` as
`ROCKNIX-RK3566.aarch64-20260912-Miyoo_Flip_V2.img.gz`, SHA-256
`39a3b8ba58992e9c3f7894c93bdfbbb6f8a6dce8ed411821ebc769ae1f19fe06`.
Do not publish that checksum for a later rebuild.

The September 13 regression image was produced as
`ROCKNIX-RK3566.aarch64-20260913-Miyoo_Flip_V2.img.gz`. Its integrity,
filesystem contents, and privacy-sensitive exclusions passed host-side audit.
Its physical test exposed an empty-card Games visibility regression, so it is
not the publishable Alpha 2 binary. The source fix is complete and requires a
replacement image and focused physical test.

## Changes from the internal Alpha 1 baseline

- Removed bundled vendor-derived stock and patched preloader images.
- Setup now validates, backs up, patches, and verifies each device's own
  preloader; exact restoration was tested on a second untouched Flip V2.
- Restored the ROCKNIX Mali stack with its EULA and the upstream mapping change
  that avoids modifying the vendor blob.
- Excluded proprietary DraStic and selected open-source melonDS DS emulation.
- Excluded the unused Art Book Next theme and ZeroTier service from the Flip
  V2 image after package-license review.
- Added an embedded ButterflyOS policy, third-party notice, common-license,
  and exact non-commercial emulator-license bundle.
- Preserved the exact Rockchip `rkbin` license and firmware-input record.
- Added public build, recovery, controls, compatibility, licensing, and known
  issue documentation.
- Added a validated, device-specific recovery-backup export workflow so the
  original preloader can be preserved off-card before reflashing.
- Replaced the unsafe first-boot GPT resize path with a fail-closed Parted
  workflow and verified full storage expansion on physical hardware.
- Added a guided second-game-card tool and a combined game library spanning
  both SD cards, including second-card access through web file transfer.
- Added physically tested standalone Saturn mappings for the built-in controls
  and the 8BitDo controller in Xbox mode.
- Added Games, Favorites, Media, Tools, and Settings home destinations, with
  Start/Main Menu and Select/Shut Down Menu cues.
- Replaced the old cable-emulation Butterfly Link launcher with a save-based
  SDL app: local/remote same-generation trades/copies, ROM-derived sprites,
  local evolution choices, and one-way generation conversions.
- Added unified music/video browsing across both cards and controller-operated
  track selection, automatic next-track playback, and clean stop/return.
- Added display-only lid handling and bounded optional Extended Diagnostics;
  unsafe hardware suspend remains disabled.

This release additionally includes wrapped confirmation/result text,
clearer trade/copy completion wording, save-write hash checks and fresh
timestamps, tighter Start-icon spacing, and Advanced-only Cloud/VPN groups.
ScreenScraper is the default on fresh installations. Linked game-list metadata
is loaded correctly, and scraper network failures produce an error instead of
appearing to succeed. The prior build passed user-confirmed artwork testing;
this image's fresh boot passed, and its packaged ScreenScraper default was
verified independently. All 668 main-image build steps passed.

## Important limitations

- Saturn runs through standalone YabaSanshiro with the restored Mali stack;
  compatibility still varies by game.
- Nintendo DS with the open-source melonDS default passed controls, audio,
  and clean-exit testing on physical hardware. Lid close/open does not suspend
  emulation.
- The Gen II banked-box persistence and converted-name terminator fixes are
  included. Crystal PC-open/save/exit/reopen passed with the corrected helper;
  this does not qualify every save/game revision. Remote Gen II → III copy passed.
- Party transfers, remote trade-evolution prompts, battles, and reverse
  generation conversions are unavailable.
- Bluetooth hotkeys/controller modes and multiplayer have qualification limits;
  see [Controls](HOTKEYS.md).
- No games or proprietary console BIOS files are included.

Read [Quick Start](QUICK_START.md), [Installation and Recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md),
[Controls](HOTKEYS.md), and [Known Issues](KNOWN_ISSUES.md) before installing.

# ButterflyOS v0.1.0 Alpha 2

Alpha 2 is the first public-release candidate for the Miyoo Flip V2. It remains
test software and is not a stable release.

## Release record

- Source tag: `v0.1.0-alpha.2` (create only after qualification)
- Exact image source commit: pending final qualification build
- Image: pending final qualification build
- SHA-256: pending final qualification build
- Target: Miyoo Flip V2 (`RK3566` / `Miyoo_Flip_V2`)

The most recent fully hardware-tested pre-release baseline was built from
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

## Important limitations

- Saturn runs through standalone YabaSanshiro with the restored Mali stack;
  compatibility still varies by game.
- Nintendo DS with the open-source melonDS default passed controls, suspend,
  resume, and clean-exit testing on physical hardware.
- No games or proprietary console BIOS files are included.

Read [Quick Start](QUICK_START.md), [Installation and Recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md),
[Controls](HOTKEYS.md), and [Known Issues](KNOWN_ISSUES.md) before installing.

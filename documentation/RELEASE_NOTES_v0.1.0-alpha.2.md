# ButterflyOS v0.1.0 Alpha 2

Alpha 2 is the first public-release candidate for the Miyoo Flip V2. It remains
test software and is not a stable release.

## Release record

- Source tag: `v0.1.0-alpha.2` (create only after qualification)
- Exact image source commit: `c9d2f0b`
- Image: `ButterflyOS-v0.1.0-alpha.2-Miyoo-Flip-V2.img.gz`
- SHA-256: `ff793369e77b7c41de57a1b53003494a8304ec6a1c64871a6478db21a6e294f1`
- Target: Miyoo Flip V2 (`RK3566` / `Miyoo_Flip_V2`)

## Changes from the internal Alpha 1 baseline

- Removed bundled vendor-derived stock and patched preloader images.
- Setup now validates, backs up, patches, and verifies each device's own
  preloader; exact restoration was tested on a second untouched Flip V2.
- Replaced proprietary Mali userspace libraries with Mesa/Panfrost.
- Excluded proprietary DraStic and selected open-source melonDS DS emulation.
- Preserved the exact Rockchip `rkbin` license and firmware-input record.
- Added public build, recovery, controls, compatibility, licensing, and known
  issue documentation.

## Important limitations

- Saturn acceleration is not currently reliable with Panfrost. See Known
  Issues for the tested emulator behavior.
- Nintendo DS must be requalified with the new open-source default before the
  release candidate is published.
- No games or proprietary console BIOS files are included.

Read [Quick Start](QUICK_START.md), [Installation and Recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md),
[Controls](HOTKEYS.md), and [Known Issues](KNOWN_ISSUES.md) before installing.

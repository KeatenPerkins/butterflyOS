# ButterflyOS v0.1.0 Alpha 2

Alpha 2 is the first public-release candidate for the Miyoo Flip V2. It remains
test software and is not a stable release.

## Release record

- Source tag: `v0.1.0-alpha.2` (create only after qualification)
- Exact image source commit: `2a294a9`
- Image: `ButterflyOS-v0.1.0-alpha.2-Miyoo-Flip-V2.img.gz`
- SHA-256: `a3304b1925e277ddde990bdc652f05ec6bcdc8dc80cd9244ccb0328f39696927`
- Target: Miyoo Flip V2 (`RK3566` / `Miyoo_Flip_V2`)

## Changes from the internal Alpha 1 baseline

- Removed bundled vendor-derived stock and patched preloader images.
- Setup now validates, backs up, patches, and verifies each device's own
  preloader; exact restoration was tested on a second untouched Flip V2.
- Replaced proprietary Mali userspace libraries with Mesa/Panfrost.
- Excluded proprietary DraStic and selected open-source melonDS DS emulation.
- Excluded the unused Art Book Next theme and ZeroTier service from the Flip
  V2 image after package-license review.
- Added an embedded ButterflyOS policy, third-party notice, common-license,
  and exact non-commercial emulator-license bundle.
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

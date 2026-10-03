# ButterflyOS v0.2.1

This October 3 update targets **Miyoo Flip V2**. The user confirmed the flashed
image looks better and works well. It is a follow-up to the public Alpha 2;
the previous image remains available on its original release page.

## Changes

- Fixed persistent scraper metadata for systems grouped under Games. Artwork
  and favorites persisted after the development scrape/reboot test.
- Reduced carousel side margins and adjusted the Start/Main Menu hint spacing
  for widescreen HDMI while preserving its built-in-screen position.
- Added a ButterflyOS-specific updater backend with device/package identity,
  checksum, battery, free-space, and complete-download checks.
- Expanded installation, game-transfer, and Butterfly Link documentation with
  supplied artwork and left/right SD-slot illustrations.

## Installation and updates

Download the `.img.gz` and matching `.sha256` below. Follow
[Quick Start](QUICK_START.md) and [Installation and recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md).
Writing an image erases the selected SD card; preserve saves and the exported
device-specific recovery backup before reflashing.

The online updater is included for testing, but **online installation has not
yet been qualified**. This release intentionally does not publish an update
manifest/package. Existing installations should use the documented reflash
procedure. End-to-end updating will be tested with a subsequent build before
public update packages are offered; see [Updates](UPDATES.md).

## Artifact and verification

- Image source: `8ba1f47590a329ba602a11219ed6fe87d46108cc`.
- Built image: `ROCKNIX-RK3566.aarch64-20261003-Miyoo_Flip_V2.img.gz`.
- Download: `ButterflyOS-v0.2.1-Miyoo-Flip-V2.img.gz`.
- Compressed SHA-256: `d7d855ec41a41018139cf1a1ad58f1d8d077f1b55b3abdebc6b62593bb0e5228`.
- All 668 main-image steps completed; gzip/checksum verification passed.
- Full flashed-image read-back SHA-256:
  `826a1f0a0b2bba268cc1ce1177a6bb35caae4f8cd42fa51c96605db0ed1db5f3`.
- Packaged updater identity is `Miyoo_Flip_V2`, version `20261003`; the packaged
  build ID matches the image source commit above.
- Six updater offline tests passed. Menu patch applicability was checked before
  the successful full build; full update/reboot behavior remains untested.

The existing [features](FEATURES.md), [controls](HOTKEYS.md), and
[known issues](KNOWN_ISSUES.md) continue to apply. No games, BIOS files, saves,
or personal media are supplied with this release.

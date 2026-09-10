# ButterflyOS v0.1.0 Alpha 1

Alpha 1 is the first named, hardware-tested ButterflyOS baseline for the Miyoo
Flip V2. It is intended for careful testers and is not a stable release.

## Release record

- Source tag: `v0.1.0-alpha.1`
- Git commit: `2fe9d6daa0fe4a0b58db5bbee3a3c75d08b85060`
- Image: `ButterflyOS-v0.1.0-alpha.1-Miyoo-Flip-V2.img.gz`
- SHA-256: `56b1721c09a6ac22a8b24f43a6f3b4fb812d86c0bb4c0f48be4328fa13ff9c7a`
- Target: Miyoo Flip V2 (`RK3566` / `Miyoo_Flip_V2`)
- Tester: Keaten Perkins
- Baseline accepted: 2026-09-10

## Highlights

- Reversible, no-disassembly SD-boot onboarding on the tested device
- ButterflyOS console-style theme and pixel system artwork
- Simplified normal interface plus optional Advanced Mode
- Tested built-in and Bluetooth controls with shared Menu-button shortcuts
- Wi-Fi, SSH, Bluetooth audio/controllers, and themed web file transfer
- Game scanning, favorites synchronization, and artwork scraping
- Music, compatible H.264 video, HDMI output, and brightness shortcuts
- Recovery tools remain visible even when Advanced Mode is disabled

## Before installing

Read [Quick Start](QUICK_START.md), [Installation and Recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md),
and [Known Issues](KNOWN_ISSUES.md). The image contains no games or proprietary
console BIOS files.

Public binary distribution remains on hold pending resolution of the preloader
utility/reference-image licensing gate described in Known Issues.

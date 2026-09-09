# ButterflyOS

<p align="center"><img src="artwork/branding/icons/butterflyos-emblem-transparent-1024.png" width="192" alt="ButterflyOS butterfly emblem"></p>

ButterflyOS is a fast, friendly, controller-first operating system for the
Miyoo Flip V2. It is currently in development and is not yet a stable public
release. See the [vision](docs/VISION.md), [roadmap](docs/ROADMAP.md), and
[Alpha 1 checklist](documentation/ALPHA1_RELEASE_CHECKLIST.md).

## Features

- Console-style ButterflyOS interface designed for a 640×480 handheld screen
- Tested defaults and Menu-button shortcuts for classic game systems
- Wi-Fi, Bluetooth controllers and audio, SSH, and themed web file transfer
- Music and compatible video playback
- HDMI video and audio output
- Reversible SD-card boot setup that preserves the internal Miyoo OS
- Beginner-facing settings with optional Advanced Mode

### Media compatibility on Miyoo Flip V2

The RK3566 hardware decoder supports H.264, H.265/HEVC, and VP9. H.264 is the
recommended format for the widest compatibility. AV1 is decoded in software on
this device; low-resolution AV1 may work, but high-resolution or 10-bit AV1 can
skip frames and consume substantially more battery. Container extensions such
as `.mov` do not guarantee smooth playback: high-bitrate or unusually encoded
H.264 files may also skip. Moderate-bitrate H.264/AAC at 480p or 720p is the
current safe target while hardware-decoding coverage is still being validated.

## Project status

Development currently targets only the Miyoo Flip V2. Images do not include
commercial games or proprietary console BIOS files. Users must supply content
they are legally entitled to use.

## Licenses

**ROCKNIX** is a fork of [JELOS](https://github.com/JustEnoughLinuxOS/distribution/), all licenses apply and credit to the JELOS team. 

You are free to:

- Share: copy and redistribute the material in any medium or format
- Adapt: remix, transform, and build upon the material

Under the following terms:

- Attribution: You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- NonCommercial: You may not use the material for commercial purposes.
- ShareAlike: If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

### ROCKNIX Software

Copyright (C) 2024-present [ROCKNIX](https://github.com/ROCKNIX)

Original software and scripts developed by the ROCKNIX are licensed under the terms of the [GNU GPL Version 2](https://choosealicense.com/licenses/gpl-2.0/).  The full license can be found in this project's licenses folder.

### Bundled Works
All other software is provided under each component's respective license.  These licenses can be found in the software sources or in this project's licenses folder.  Modifications to bundled software and scripts by the JELOS team are licensed under the terms of the software being modified.

## Credits

Like any Linux distribution, this project is not the work of one person.  It is the work of many persons all over the world who have developed the open source bits without which this project could not exist.  Special thanks to CoreELEC, LibreELEC, JELOS, and to developers and contributors across the open source community.

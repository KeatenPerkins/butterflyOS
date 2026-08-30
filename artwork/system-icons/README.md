# ButterflyOS system artwork

Original 16-bit-style hardware illustrations for ButterflyOS. These assets
were generated specifically for this project and do not contain manufacturer
logos or wordmarks.

## Runtime names

| File | EmulationStation theme name |
| --- | --- |
| `nes.png` | `nes` |
| `snes.png` | `snes` |
| `gb.png` | `gb` |
| `gba.png` | `gba` |
| `genesis.png` | `genesis`, `megadrive` |
| `psx.png` | `psx` |
| `dreamcast.png` | `dreamcast` |

`source/` contains the full-resolution generated originals. `runtime/`
contains reduced RGBA copies intended for the 640x480 Miyoo Flip V2 display.
`runtime/_default.png` is the temporary generic controller shown when a system
does not have dedicated ButterflyOS artwork yet.

At build time ButterflyOS groups every playable entry in the device-specific
`es_systems.cfg` under `Games`. EmulationStation only adds group folders that
contain recognized ROMs, so an installed emulator configuration alone does not
produce an empty system tile. Entries classified as `System` (Music, Tools,
Screenshots, streaming, and media utilities) remain outside the Games group.

Copyright (C) 2026 Keaten Perkins

SPDX-License-Identifier: GPL-2.0-only

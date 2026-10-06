# ButterflyOS system artwork

Original 16-bit-style hardware illustrations and game-engine artwork for
ButterflyOS. The hardware illustrations were generated specifically for this
project and do not contain manufacturer logos or wordmarks. The portrait
game-engine artwork includes the corresponding software titles.

## Runtime names

| File | EmulationStation theme name |
| --- | --- |
| `nes.png` | `nes` |
| `snes.png` | `snes` |
| `gb.png` | `gb` |
| `gba.png` | `gba` |
| `genesis.png` | `genesis`, `megadrive` |
| `psx.png` | `psx` |
| `openbor.png` | `openbor` |
| `easyrpg.png` | `easyrpg` |
| `ports.png` | `ports` |
| `dreamcast.png` | `dreamcast` |
| `atari2600.png` | `atari2600` |
| `atari7800.png` | `atari7800` |
| `atarilynx.png` | `atarilynx` |
| `gamegear.png` | `gamegear` |
| `gbc.png` | `gbc` |
| `mastersystem.png` | `mastersystem` |
| `msx.png` | `msx` |
| `n64.png` | `n64` |
| `nds.png` | `nds` |
| `neogeo.png` | `neogeo` |
| `ngp.png`, `ngpc.png` | `ngp`, `ngpc` |
| `pcengine.png` | `pcengine` |
| `pcenginecd.png` | `pce-cd`, `pcenginecd` |
| `segacd.png` | `segacd` |
| `arcade.png` | `arcade` |
| `fbneo.png` | `fbneo` |
| `cps1.png`, `cps2.png`, `cps3.png` | `cps1`, `cps2`, `cps3` |
| `psp.png` | `psp` |
| `saturn.png` | `saturn` |
| `wonderswan.png`, `wonderswancolor.png` | `wonderswan`, `wonderswancolor` |

`source/` contains the full-resolution originals. Most `runtime/` assets
are reduced RGBA copies intended for the 640x480 Miyoo Flip V2 display.
OpenBOR and EasyRPG use the supplied 1024x1536 portrait PNGs unchanged,
matching the portrait format used by Ports; the theme scales them to fit.
They were supplied as `Documents/openBOR.png` and `Documents/easyRPG.png`
on 2026-10-05 and installed under lowercase system theme names.
`runtime/_default.png` is the temporary generic controller shown when a system
does not have dedicated ButterflyOS artwork yet.

The Arcade, Final Burn Neo, and CPS assets use distinct original arcade
cabinets: woodgrain, purple, blue, green, and white respectively. They represent
arcade collections rather than replicas of one particular cabinet model.
PC Engine CD shows the console and CD expansion together; Sega CD shows a
Model 1 console and disc-drive base. The build supplies the `pce-cd` filename
alias used by the installed EmulationStation configuration.

At build time ButterflyOS groups every playable entry in the device-specific
`es_systems.cfg` under `Games`. EmulationStation only adds group folders that
contain recognized ROMs, so an installed emulator configuration alone does not
produce an empty system tile. Entries classified as `System` (Music, Tools,
Screenshots, streaming, and media utilities) remain outside the Games group.

Copyright (C) 2026 Keaten Perkins

SPDX-License-Identifier: CC-BY-SA-4.0

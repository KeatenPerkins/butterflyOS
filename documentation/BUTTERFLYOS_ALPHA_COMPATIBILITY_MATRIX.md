# ButterflyOS Alpha Compatibility Matrix

This is the minimum Miyoo Flip V2 Alpha test suite. The selected games are
user-supplied backups used during development; they are not
part of ButterflyOS and must not be distributed with an image.

For every row, verify boot, video, audio, built-in controls, Bluetooth
controls, Menu, save/load state where supported, exit, lid-close/open, and ten
minutes of play. Lid handling is display-only: games continue running, and
hardware suspend must remain disabled. A smoke test is not full compatibility
qualification or proof that all multiplayer/controller combinations work.

| Tier | System | Primary test | Stress or special test | BIOS | Core/emulator | Result |
|---|---|---|---|---|---|---|
| A | NES | FC/Kirby's Adventure (USA).nes | FC/Castlevania III - Dracula's Curse (USA).nes | None | Nestopia | Development smoke test passed |
| A | SNES | SFC/Kirby Super Star (USA).smc | SFC/Star Fox (USA) (Rev 2).smc | None | Snes9x | Development smoke test passed |
| A | Game Boy | GB/Pokemon - Red Version (USA, Europe).gb | GB/Kirby's Dream Land (USA, Europe).gb | None | Gambatte | Development smoke test passed |
| A | Game Boy Color | GBC/Pokemon - Gold Version (USA, Europe).gbc | GBC/Shantae (USA).gbc | None | Gambatte | Development smoke test passed |
| A | Game Boy Advance | GBA/Metroid Fusion (USA, Australia).gba | GBA/Golden Sun - The Lost Age (USA, Europe).gba | Optional | mGBA | Development smoke test passed |
| A | Master System | MS/Sonic The Hedgehog (USA, Europe).sms | MS/R-Type (World).sms | None | Gearsystem | Development smoke test passed |
| A | Game Gear | GG/000 Sonic the Hedgehog 1.gg | GG/000 Sonic The Hedgehog-Triple Trouble.gg | None | Gearsystem | Development smoke test passed |
| A | Genesis/Mega Drive | MD/Sonic the Hedgehog 3 (USA).md | MD/Contra - Hard Corps (USA, Korea).md | None | Genesis Plus GX | Development smoke test passed |
| A | PC Engine | PCE/Bonk's Adventure (USA).pce | PCE/R-Type (USA).pce | None | Beetle PCE Fast | Development smoke test passed |
| A | Nintendo 64 | N64/Super Mario 64.z64 | N64/Mario racing car 64.z64 | None | Mupen64Plus-Next | Passed; brief loading slowdown observed in Mario racing car 64 |
| A | Nintendo DS | NDS/Mario Kart DS (USA) (En,Fr,De,Es,It).zip | NDS/Metroid Prime - Hunters (USA).zip | Recommended | melonDS DS | Open-source replacement passed development controls/audio/exit testing; DraStic excluded |
| A | PlayStation | PS/Castlevania Symphony of the Night.chd | PS/Gran Turismo.chd | Required/recommended | PCSX-ReARMed | Development smoke test passed with user BIOS |
| A | Dreamcast | DC/Crazy Taxi.chd | DC/Ikaruga v1.002 (2002)(ESP)(NTSC)(JP)[!].chd | Required/recommended | Flycast 2021 | Development smoke test passed with user BIOS |
| A | Saturn | SS/NiGHTS into Dreams... (USA, Brazil).chd | SS/Panzer Dragoon II Zwei (USA).chd | Required/recommended | YabaSanshiro | Passed; standalone exit path validated separately |
| A | PSP | PSP/Final Fantasy IV - The Complete Collection (USA) (En,Ja,Fr).iso | PSP/God of War - Chains of Olympis.cso | None | PPSSPP | Development smoke test passed; native PPSSPP menu behavior retained |
| A | Neo Geo | NEOGEO/mslug.zip | NEOGEO/garou.zip | neogeo.zip set dependency | FBNeo | Development smoke test passed with compatible set/BIOS |
| A | Arcade/FBNeo | FBNEO/tetris.zip | FBNEO/aliencha.zip | Set-dependent | FBNeo | Partial: Tetris passed; Alien Challenge must be placed in FBNEO or assigned an FBNeo per-game override |
| B | Atari 7800 | ATARI7800/Food Fight (1987) (Atari).zip | ATARI7800/Ballblazer (1987) (Atari-Lucasfilm).zip | None | ProSystem | Development smoke test passed |
| B | Atari Lynx | LYNX/Chip's Challenge (USA, Europe).zip | LYNX/Raiden (USA) (v3.0).zip | Core-dependent | Handy | Development smoke test passed |
| B | Neo Geo Pocket Color | NGP/Sonic the Hedgehog - Pocket Adventure (World).ngc | NGP/Metal Slug - 2nd Mission (World) (En,Ja).ngc | None | Beetle NGP | Development smoke test passed |
| B | WonderSwan Color | WSC/Kaze no Klonoa - Moonlight Museum (Japan).ws | WSC/Judgement Silversword - Rebirth Edition (Japan) (Rev 4321).wsc | None | Beetle WonderSwan | Development smoke test passed |
| B | PICO-8 | PICO8/Celeste.p8 | PICO8/X-Zero.p8 | Licensed runtime or Fake-08 | PICO-8/Fake-08 | Interface present; full licensed-runtime qualification pending |
| B | EasyRPG | EASYRPG/Zelda Links Awakening | EASYRPG/Resident evil dead arpg | None | EasyRPG Player | Development smoke test passed |
| B | OpenBOR | OPENBOR/Final Fight Gold Champion Edition.pak | OPENBOR/Contra - Locked 'N Loaded.pak | None | OpenBOR | Passed; standalone exit path validated separately |

## Hold until corrected or expanded

The test filenames above are examples, not necessarily the canonical directory
names on the installed image. Follow System Manager's folder guidance; additional
systems inherited from upstream are not automatically ButterflyOS-qualified.

- ATARI2600, CPS2, CPS3, MAME2010, NEOCD, PICO, and several placeholder
  folders contain no usable games.
- MSX needs inspection: its filenames resemble Master System games and should
  not be used as MSX validation yet.
- DOS contains no launchable DOS game in its current root.
- FFMPEG, MUGEN, PORT32, Shoot, and cache/database files are not console
  compatibility targets.
- PC Engine CD, Sega CD, 32X, 3DO, ColecoVision, Intellivision, Atari 2600,
  and other secondary systems need user-owned test content.

## BIOS policy

ButterflyOS must not distribute proprietary console BIOS files. Testers supply
their own dumps. Record each BIOS filename and SHA-256 hash, confirm that the
emulator detects it, and retain the hash—not the BIOS—in the test report.

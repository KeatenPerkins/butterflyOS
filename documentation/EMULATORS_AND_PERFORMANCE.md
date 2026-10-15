# Emulators and performance tuning

ButterflyOS starts with tested defaults, but the best emulator and settings
can vary from game to game. Start with **Auto**, then try a different core or
performance setting if you hear audio skipping, see graphical errors, or want
better fast-forward speed. Keep a change only if it helps your game.

An **emulator core** runs inside RetroArch. A **standalone emulator** runs as
its own application; entries ending in `-sa` mean standalone. Standalone
emulators have their own menus and controls and are not automatically faster.

## Default emulators and alternatives

This table covers common systems on the Miyoo Flip V2. Alternatives are
examples from its emulator menu, not a promise that every game works with them.
Check the [compatibility matrix](BUTTERFLYOS_ALPHA_COMPATIBILITY_MATRIX.md)
for recorded game tests.

| System | Auto default | Alternatives to try |
| --- | --- | --- |
| NES | Nestopia | FCEUmm, QuickNES |
| SNES | Snes9x | Snes9x 2010, Snes9x 2005 Plus |
| Game Boy / Game Boy Color | Gambatte | SameBoy, mGBA |
| Game Boy Advance | gpSP from v1.0.4; mGBA in earlier images | mGBA, gpSP |
| Mega Drive / Genesis | Genesis Plus GX | PicoDrive |
| PC Engine | Beetle PCE Fast | Beetle PCE |
| PlayStation | PCSX-ReARMed 32-bit (`pcsx_rearmed32`) | PCSX-ReARMed 64-bit (`pcsx_rearmed`), DuckStation |
| Nintendo 64 | Mupen64Plus-Next | Other listed Mupen64Plus cores or standalone Mupen64Plus |
| Dreamcast | Flycast 2021 | Flycast core, standalone Flycast |
| Nintendo DS | melonDS DS | Other listed DS emulators; check controls and game compatibility |
| PSP | Standalone PPSSPP | PPSSPP RetroArch core |
| Saturn | Standalone YabaSanshiro | YabaSanshiro RetroArch core |
| Arcade | MAME 2003 Plus | FBNeo or another MAME core matching your ROM set |

The gpSP default applies to the normal GBA category. GBA Hacks and
GBA Video retain mGBA. Existing explicit emulator choices take precedence
over a new default after an update.

## Change a whole system or just one game

For a system, open its game list and press **Select → Advanced System
Options → Emulator**. This selects an emulator for that system.

For one game, open its **Game Options → Advanced Game Options** and change
the emulator there. A game-specific choice overrides the system choice.
The Game Options shortcut follows your frontend control configuration.

These choices are saved across restarts and normal OS updates. Choosing
**Auto** returns to the inherited choice: a game's Auto follows its system,
and a system's Auto follows the image's default emulator.

In the same configuration screen, **System Options** contains **CPU Scaling
Governor** and **GPU Scaling Governor**. Despite the submenu name, settings
opened through an individual game's configuration apply to that game.

## CPU and GPU settings

These control how the hardware changes its clock speed. They do not change
the original console's emulated CPU clock or guarantee full-speed gameplay.

| Setting | What to expect |
| --- | --- |
| CPU Default / inherited | Uses the higher-level policy; the normal system default is ondemand |
| CPU ondemand | Raises and lowers CPU speed with demand; start here |
| CPU performance | Requests the highest allowed CPU speed; may improve demanding games, with more power use and heat |
| CPU powersave | Favors low CPU speed; can slow games and is not a recommended general gaming preset |
| CPU schedutil | Another dynamic governor; test before keeping it |
| GPU Default / auto | Uses the inherited or dynamic GPU policy |
| GPU performance | Requests the highest allowed GPU speed; may help rendering, with more power use and heat |

Change **one setting at a time**. Compare the same gameplay section, then
exit normally and launch again after changing the core or rendering settings.
Per-game overrides are useful when only a few titles need extra performance.

## What our development tests showed

- **GBA:** gpSP maintained 60 FPS and offered much faster fast-forward in
  Gunstar Super Heroes and Tony Hawk's Pro Skater 2. It also used less CPU
  than mGBA in paired Gunstar runs. FireRed in-game saves and same-core save
  states passed live tests. Try mGBA if gpSP has a problem with another game.
- **PlayStation:** both PCSX-ReARMed versions worked in our short Crash
  Bandicoot comparison, with little noticeable difference. We kept the
  existing 32-bit default.
- **Dreamcast:** Crazy Taxi worked better with Flycast 2021 in the tested
  configurations; the other Flycast core and standalone had poor audio.
  CPU Performance improved gameplay from just under 30 FPS to roughly
  34–40 FPS. CPU plus GPU Performance could reach 60 FPS while stationary
  but still dropped into the low 30s while driving. These are game-specific
  observations, not full-speed guarantees or general rankings of Flycast.
- **Nintendo 64:** renderer choices can trade speed for graphical accuracy.
  Our experimental Rice setup produced rendering errors and a crash; it is
  not a recommended replacement for the default.

FPS depends on the game, scene and counter being shown. Not every original
game targets 60 FPS. Also judge gameplay speed, audio and frame pacing;
a higher number alone does not mean the game is working correctly.

## Nintendo 64, Dreamcast and battery use

Demanding N64 and Dreamcast games can use substantially more power than
lighter systems, especially with CPU or GPU Performance selected. For longer
sessions using these settings, **playing plugged in is worth considering**.
If battery runtime matters more, start with the dynamic defaults and use
Performance only for games where it makes a worthwhile difference.

Plugging in does not itself select a faster emulator or enable Performance.
It also cannot fix rendering errors or an emulator compatibility problem.
The device may still fall below full speed even at its maximum clocks.

## Saves when trying another core

Save through the game's own menu before changing cores. Save states generally
require the same core and may also depend on its version. To use an existing
mGBA state after the GBA default changes to gpSP, explicitly select mGBA.

Test a new core with a fresh launch rather than loading another core's state.
In-game save compatibility and save locations can vary too; keep a backup of
important saves and confirm Continue works before committing to a new core.

Options changed directly inside RetroArch may be overridden by ButterflyOS
at launch. Use the ButterflyOS settings menu for options it exposes; persistence
of other RetroArch options depends on that emulator's configuration.

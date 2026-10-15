# Flip V2 emulation tuning audit

Inspected October 9, 2026. ButterflyOS source baseline: `bcf7a8a58f`.
Spruce local reference: `2c5638375c5998ebd7480970bb55e3d2b2629c58`.
This compares checked-out source and the installed development device, not
measured performance between operating systems. No defaults were changed.

## Existing support

| Capability | ButterflyOS finding | Practical implication |
| --- | --- | --- |
| GBA core selection | Installed mGBA, gpSP, VBA-M, VBA Next, Beetle GBA and SkyEmu; mGBA is the menu default | Start by comparing existing mGBA and gpSP |
| 32-bit execution | `retroarch32` is installed; gpSP and `pcsx_rearmed32` are verified ARM32 ELF libraries | ARM32 PS1 support already exists; benchmark before proposing a new userspace |
| Emulator overrides | System and game selectors write separately scoped emulator/core keys in system.cfg | Reuse existing selectors rather than adding another configuration store |
| CPU overrides | `cpugovernor` resolves game, system, system-wide and global fallbacks | Named modes can map onto existing override infrastructure |
| GPU overrides | `gpuperf` resolves the same launch hierarchy | CPU and GPU policies are already separate |
| Frequency floors | Governor helpers set CPU/DMC governors, without per-game CPU min/max frequency controls | A tested frequency-floor policy would be a new feature |
| Normal exit | Launch boosts CPU/DMC for setup and cleanup, then restores the configured system governor; GPU/thread restoration is also present | Verify restoration live, including abnormal exits, before adding profiles |

Device .17 at idle reported CPU `ondemand`, minimum 408 MHz, maximum 1800 MHz;
available governors were ondemand, powersave, performance and schedutil.
This is an idle snapshot, not evidence of gameplay frame pacing or efficiency.

## Where the current UI puts the controls

The game-list options menu exposes **Advanced System Options**, containing an
emulator/core selector and **System Options** with CPU and GPU governor controls.
Game Options exposes **Advanced Game Options** for the same configuration
screen at game scope. These entries are not themselves gated by
`ButterflyAdvancedMode` in the inspected source. The word “Advanced” is therefore
also a discoverability issue, not evidence that the feature is absent.

The hardware settings screen also contains default CPU/GPU governor controls.
The per-game governor choice inherits higher-level settings when no override
is saved. Actual menu placement and controller navigation should be confirmed
on-device before changing labels or writing a user-facing walkthrough.

Relevant ButterflyOS source:

- `projects/ROCKNIX/packages/rocknix/profile.d/001-functions`: settings lookup.
- `projects/ROCKNIX/packages/rocknix/profile.d/099-freqfunctions`: CPU, GPU and DMC helpers.
- `projects/ROCKNIX/packages/rocknix/sources/scripts/runemu.sh`: bitness, launch and cleanup.
- `projects/ROCKNIX/packages/emulators/libretro/{mgba-lr,gpsp-lr}/package.mk`: pinned core revisions/build paths.
- Built frontend `GuiMenu.cpp`, `GuiGamelistOptions.cpp`, `GuiGameOptions.cpp`: selectors and menu visibility.

## What the Spruce source actually does

The inspected Spruce GBA JSON defaults to gpSP, offers mGBA/gpSP and
Smart/Performance/Overclock, and sets `scaling_min_freq` to 816 MHz.
The launcher reads JSON selections and per-game overrides. The Smart helper
waits ten seconds before applying that policy. Flip Smart uses ondemand,
408–1800 MHz as the device defaults and cores 0–1; GBA supplies its higher
816 MHz floor. Flip Performance uses a 1800 MHz ceiling; the declared
Overclock ceiling is 1992 MHz. These are source settings, not validation that
all modes are supported or useful in ButterflyOS.

The variable named `GPU_GOVENOR_DIR` points at DMC on the inspected Flip
configuration. Do not read its values as measured Mali GPU tuning.

The earlier broad comparison's description of `.opt` files as CPU launch
profiles does not match this inspected version: launch policies are in
`Emu/*/config.json`; RetroArch `.opt` files hold core options.

Pinned Spruce references:

- [GBA configuration](https://github.com/spruceUI/spruceOS/blob/2c5638375c5998ebd7480970bb55e3d2b2629c58/Emu/GBA/config.json)
- [Flip hardware policies](https://github.com/spruceUI/spruceOS/blob/2c5638375c5998ebd7480970bb55e3d2b2629c58/spruce/scripts/platform/Flip.cfg)
- [Launch policy and overrides](https://github.com/spruceUI/spruceOS/blob/2c5638375c5998ebd7480970bb55e3d2b2629c58/spruce/scripts/emu/lib/general_functions.sh)
- [CPU policy helpers](https://github.com/spruceUI/spruceOS/blob/2c5638375c5998ebd7480970bb55e3d2b2629c58/spruce/scripts/platform/device_functions/utils/cpu_control_functions.sh)

## First comparison: GBA

Two user-owned games and the user's GBA BIOS were copied from .20 for .17:
Gunstar Super Heroes (USA) and Tony Hawk's Pro Skater 2 (USA, Europe).
The .17 GBA folder was empty and the BIOS absent before preparation. Local
asset hashes and the device menu inventory are preserved under
`Documents/ButterflyOS-Emulation-Audit-20261009/`; no ROMs or BIOS enter Git.

1. Refresh game lists. Use the system options emulator selector to choose
   RetroArch mGBA. Keep CPU ondemand and all other settings fixed.
2. Test a repeatable gameplay section for five minutes, noting full-speed FPS,
   audio, controls and rendering. Briefly check fast-forward headroom in that
   same section. FPS during a normal capped run alone cannot rank efficiency.
3. Exit normally. Verify idle CPU/DMC policy restoration. Switch to gpSP and
   repeat using a fresh launch and the same section; do not load an mGBA state
   into gpSP. These copies contain no imported personal saves.
4. Repeat with the second game. If both are stable, collect longer paired
   runs using the existing local-only performance recorder (five-second
   samples, consistent brightness/radios, unplugged, comparable charge).
5. Only after the core comparison, change one policy at a time: ondemand
   versus performance, then a separately implemented/tested frequency floor
   if evidence warrants it. Restore mGBA/AUTO and inherited governor settings
   afterward unless the user chooses to retain a game override.

The old recorder measures utilization, clocks and driver-derived electrical
readings, not FPS, frame-time percentiles or audio underruns. Capture those
observations separately. Battery estimates remain under investigation; do not
claim a battery-life improvement from one short run or percentage changes.

## Proposed next implementation

Keep the existing defaults. First confirm both launch paths and restoration
live. Then improve the existing settings flow with clear descriptions and
named modes, retaining expert governor controls. Balanced may map to the
current dynamic policy; Performance to existing performance helpers. A
Battery Saver policy needs gameplay and power evidence before shipping:
the raw powersave governor selects low frequency and is not automatically a
safe full-speed emulation preset. Frequency floors, overclocking, disabling
cores and copying Spruce memory settings should each be separate experiments.

The 32-bit PS1 comparison and current/new Flycast comparison can follow using
installed options where possible. No emulator winner is established here.

## Initial GBA live results

The user tested Gunstar and Tony Hawk with gpSP: solid 60 FPS at normal speed,
roughly 260 FPS in fast-forward, and clean music. Default mGBA in Gunstar
was approximately 59 FPS, with fast-forward around 61 FPS and occasional
55 FPS observations. These are user observations, not frame-time captures.

Paired fifteen-minute Gunstar recordings used ondemand, identical observed
brightness, Wi-Fi enabled and no charger. In the matched 120–850-second
window, mGBA averaged 43.2% total CPU busy, 1747 MHz and 57.8°C; gpSP averaged
32.5%, 1303 MHz and 53.0°C. Driver-derived power was 5.04 W versus 4.36 W,
approximately 14% lower in the gpSP run. Different gameplay and charge levels,
sequential run order and uncalibrated power readings limit that comparison.
The mGBA menu tail was excluded using top-process presence as a heuristic.

Pokémon FireRed (USA, Europe), revision 1, was copied without personal saves
for compatibility testing. The user confirmed gpSP in-game save, normal exit,
fresh launch and Continue worked, then confirmed manual save-state creation,
exit, fresh launch and same-core state loading worked.

These results support improving the visibility of gpSP as a faster optional
GBA choice. They do not establish broad game compatibility, cross-core state
compatibility, or a precise battery-runtime improvement. Keep mGBA as the
current default until a separate default-change decision. Original recordings,
matched comparison and live observations are retained in the local audit folder.

## Approved GBA default change

After these live results, the user requested gpSP as the normal GBA default
on Miyoo Flip V2. The emulator generator now marks gpSP as the single default
for `gba` on that subdevice, with mGBA retained as an explicit alternative.
Other devices and the untested `gbah`/`gbav` categories retain existing defaults.
Explicit system and game emulator choices remain authoritative; the change
applies to inherited defaults. Existing mGBA save states require choosing
mGBA to load them; no save-state conversion is performed.

The GBA selector uses readable gpSP/mGBA labels, describes the speed option
and fallback, and shows which core Auto selects. Game-scope Auto reflects
an explicit system selection if present. Selector values and configuration paths
are unchanged. Generator checks verified the Flip gpSP default and retained
mGBA defaults for another RK3566 target and AMD64.

The updated selector compiled and linked successfully. A reversible live
test on .17 passed checksum checks and frontend startup. The temporary
frontend and system-list mounts disappear on reboot; the source changes
remain for the next build. User verification of the new menu is pending.

The user subsequently confirmed the GBA default and selector work live.

## Initial PS1 comparison

Crash Bandicoot was tested with the existing default ARM32 PCSX-ReARMed and
the AArch64 PCSX-ReARMed alternative. Both active cores were verified from
process mappings. Each recording lasted five minutes, excluding its first
minute, with ondemand, matching observed brightness and no charger.

Average CPU busy was 36.9% versus 37.3%; sampled CPU frequency 1339 versus
1405 MHz; driver-derived discharge power 4.52 versus 4.86 W (32-bit first).
The user reported no graphics/audio issues with 32-bit and little noticeable
difference with 64-bit, and chose to keep the existing 32-bit default.

No PS1 configuration change is required. The small CPU-load difference and
short sequential tests do not establish a broad performance or battery-life
advantage. Gameplay, charge level, ordering and uncalibrated power readings
limit the comparison. Raw records and analysis remain in the local audit folder.

## Emulator setting persistence check

On .17, the user selected mGBA for the GBA system and gpSP specifically for
Gunstar. Both scoped choices were verified in `system.cfg`. Active library
mappings confirmed Gunstar used gpSP and Tony Hawk inherited mGBA. After a
normal reboot, both settings remained saved and both launches again resolved
to the expected core. Menu CPU ondemand and GPU/DMC simple_ondemand matched
the configured dynamic defaults after exit and reboot.

This verifies emulator choice persistence and precedence on this device.
It does not exercise every RetroArch option, OS-update persistence, or a
forced-performance-to-menu governor transition. Temporary frontend/system-list
mounts correctly disappeared on reboot. Restore test overrides to Auto after
testing; reapply the next-build system list before checking the gpSP Auto default.

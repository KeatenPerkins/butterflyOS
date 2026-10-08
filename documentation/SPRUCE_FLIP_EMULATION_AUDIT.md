# SpruceOS and ButterflyOS: Flip emulation audit

Audited October 8, 2026. This is a development audit and proposed roadmap, not a performance ranking.

ButterflyOS already packages most of the emulator families recommended in the supplied comparison. The useful work is validating defaults, investigating specific upstream optimizations, improving controls and explaining alternatives. Spruce offers valuable examples of that integration. Its broader selection does not establish higher FPS or lower power consumption on the Flip V2.

## Scope and reproducibility

- Spruce reference: `/home/keaten/Documents/spruceOS-reference`, shallow sparse checkout of **v4.5.2**, commit `2c5638375c5998ebd7480970bb55e3d2b2629c58`. Selected launcher/UI/configuration files and emulator binaries were downloaded; bundled game and BIOS directories were excluded.
- Wiki reference: `/home/keaten/Documents/spruceOS-wiki-reference`, commit `7cd3752dcad3d552f6bc8e9af2b8048dccaa88ce`. The wiki is independently versioned and may describe a different software generation.
- ButterflyOS reference: actual SYSTEM payload from local test build **20261010**, source commit `29d1a8c521` plus the recorded uncommitted installation documentation and lid shutdown changes. Image SHA-256: `81384a555e0c5a88d451c55989d2f61c920b80239440d070e9bb8e28a9dc63cb`.
- Audit artifacts: `/home/keaten/Documents/ButterflyOS-Releases/emulator-audit-20261008/`. `binary-inventory.json` records SHA-256, ELF architecture, build IDs where available, dependencies and compiler comments for 21 selected binaries. `benchmark-results-template.csv` provides a results schema.
- Public releases checked: [Spruce v4.5.2](https://github.com/spruceUI/spruceOS/releases/tag/v4.5.2) and [ButterflyOS v1.0.2](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.0.2). The ButterflyOS binary findings below describe the local test image, not a separate extraction of public v1.0.2. Pending full-screen launch UI and optional lid save/shutdown must not be described as already published.

No Spruce emulator was executed. No device configuration, firmware or emulator default was changed by this audit. Packaged presence, configured availability and successful gameplay are distinct findings.

## Verification of the supplied comparison

| Claim | Audit result | Practical consequence |
| --- | --- | --- |
| Spruce uses vendor Linux on the Flip; ButterflyOS supplies a ROCKNIX-derived image | Confirmed. Spruce's Flip platform configuration targets vendor firmware `20250627233124` and documents kernel 5.10.160 for its modules. | Binaries and drivers need platform-specific integration; copying a working binary does not guarantee equivalent behavior. |
| Spruce's current emulator profiles use `.opt` files | Outdated as a description of the current principal launcher. Release configuration uses `Emu/<system>/config.json`, `menuOptions`, device selection and per-game overrides. | Study the current resolver rather than reproducing the older wiki mechanism. |
| ButterflyOS needs ARM32 support to test PCSX-ReARMed | Incorrect for the audited image. `retroarch32` and ELF32 `pcsx_rearmed32_libretro.so` are packaged, and `pcsx_rearmed32` is the PS1 default. | Benchmark an existing feature. No new ARM32 userspace is required for this experiment. |
| ButterflyOS needs gpSP added | Incorrect for the audited image. gpSP is packaged, listed for GBA and routed through RetroArch32. | Compare mGBA with existing gpSP before considering another build. |
| ButterflyOS needs standalone Mupen64Plus and Rice added | Incorrect for the audited image. Both are packaged, with standalone renderer options. Rice was also already tried live and produced colored artifacts followed by a lockup. | Treat this as a rendering/stability investigation, not a simple missing-package task. |
| ButterflyOS has only Flycast 2021 | Incomplete. The image includes Flycast 2021, newer Flycast libretro and standalone Flycast. | Compare the available variants before adding another package or changing the default. |
| ButterflyOS lacks per-game performance settings | Incorrect as a general claim. Its launcher resolves a per-game CPU governor and supports per-game emulator/core settings; ES exposes governor settings. | A simpler preset interface could improve usability, but should reuse the existing setting hierarchy. |
| ButterflyOS needs save-before-shutdown functionality | Outdated relative to current development. Optional, verified RetroArch autosave followed by normal shutdown has been implemented and tested with Crystal. | Extend coverage carefully; this is not yet an all-emulator Game Switcher. |
| Spruce is definitively faster/more efficient | Unverified. No matched device benchmark was supplied or performed here. | Use repeatable gameplay and power measurements before drawing performance conclusions. |

## The actual differences that matter

### PlayStation

ButterflyOS defaults to **32-bit PCSX-ReARMed** and offers its 64-bit counterpart. Spruce v4.5.2's PS configuration defaults to **64-bit RetroArch with PCSX-ReARMed**, while offering 32-bit RetroArch and standalone PCSX-ReARMed. Spruce's [v4.2.0 release notes](https://github.com/spruceUI/spruceOS/releases/tag/v4.2.0) do document adding a Flip 32-bit option for PS1 performance; that does not mean it remains the selected default.

ButterflyOS's recipe pins PCSX-ReARMed to `228c14e10e9a8fae0ead8adf30daad2cdd8655b9`, applies optimization flags and packages the ARM build with a `32` suffix. Selected binary architecture was verified directly. Exact Spruce source revisions and complete compiler flags were not established from the packaged binaries.

Start with our existing 32/64 paths. Standalone PCSX-ReARMed is an additional candidate if a measurable problem remains. Test memory-card saves, multidisc changes, hotkeys and resume as well as frame pacing.

### Game Boy Advance

ButterflyOS selects **mGBA**, with **ELF32 gpSP** available. Spruce selects **gpSP**, and its inspected `cores64/gpsp_libretro.so` is **ELF64**. This is a real architecture difference, so a comparison based only on the name gpSP misses an important variable.

Our gpSP recipe pins `b0d5d27ae51c23f514974ddffa5760f1e1d05d9b`. A version number in release notes does not prove identical source, flags or dynarec behavior. Test normal speed, fast-forward headroom, RTC, save persistence, achievements and audio. Keep mGBA as the baseline while measuring whether gpSP earns a documented performance option or default change.

### Nintendo 64

ButterflyOS defaults to **Mupen64Plus-Next**, with other libretro cores and standalone Mupen64Plus listed. Its SYSTEM contains the standalone executable, core library, Rice, GLideN64 and Glide64mk2 plugins. Spruce's Flip configuration instead selects **`km_ludicrousn64_2k22_xtreme_amped`** under 64-bit RetroArch, with Performance CPU mode. Standalone is an alternative, not the selected general default in that configuration.

Spruce's standalone wrapper provides an in-game overlay, renderer selection, configuration rereading on restart, controller integration and viewport handling. Its renderer resolver falls back to Rice when no stored selection is present. These are useful integration examples; the viewport branch for panels wider than 4:3 is not itself a fix for our 640×480 Flip artifacts.

The most useful next source audit is the provenance and patch set behind Spruce's selected N64 core, its standalone renderer builds and the exact SDL/EGL/GLES presentation path. The selected KM core was identified in configuration but was not part of the 21-binary extraction. A filename cannot establish what patches it contains. Find the corresponding source/build instructions before attempting a ButterflyOS-native build.

Reproduce our previous Rice defect with logging and compare GLideN64 at native resolution. Vary one renderer or synchronization setting at a time. Do not promote a configuration that appears faster but corrupts graphics or locks the device.

### Dreamcast

ButterflyOS selects **Flycast 2021**, with modern Flycast libretro and standalone available. Spruce's Flip config selects **Flycast libretro**, with 2021, 2024 and standalone alternatives.

Our modern Flycast recipes pin `5aa091fde632fb332c8d8c34e280d62dc951954c`. Recipe pins describe intended source; binary hashes identify the actual cached build. They are not a substitute for recording runtime version and renderer when testing.

Compare existing choices first. Vulkan build options, loader files or Mali libraries do not establish that a particular emulator is actually using a working Vulkan path. Record the renderer from a real launch. Compare visual correctness, frame pacing and audio, then decide whether 2021 should remain the default or be a compatibility fallback.

### Nintendo DS

ButterflyOS selects **melonDS DS**. Spruce's Flip-specific menu selects **DSperate**, even though its generic `default_emulator` field still says DraStic-original. Device-specific resolution matters.

[DSperate](https://github.com/beebono/DSperate) has its own public source and GPLv3 license. Its upstream documentation describes ARM recompilers and handheld controls. This makes it a plausible native-build experiment rather than a reason to bundle DraStic. Current upstream features may differ from the version packaged with Spruce v4.5.2; pin a tested revision before integration.

Spruce's wrapper also illustrates required integration: SDL controller mappings, screen layout shortcuts, separate save/state paths and a Flip-specific SDL library workaround. ButterflyOS's image lists standalone melonDS but the inspected filesystem listing contains its launcher without an obvious standalone executable; listed choices should be checked for usability instead of assumed to work.

A DSperate trial should begin with a ButterflyOS-native build and isolated saves on .17. Validate stylus movement, tapping, swapping screens, microphone substitute, battery saves and clean exit. Do not automatically load another emulator's states.

### CPU, memory and power policies

Spruce's Flip configuration defines Smart, Performance and Overclock modes, with CPU ceilings of 1.8 GHz for Smart/Performance and 1.992 GHz for Overclock. Smart declares two online cores and per-system minimum frequencies; actual launch behavior needs runtime verification. GBA declares an 816 MHz minimum; PS1, N64 and Dreamcast declare 1.008 GHz.

Importantly, its variable labeled `GPU_GOVENOR_DIR` points at `/sys/class/devfreq/dmc`: the dynamic memory controller. Those settings must not be presented or copied as GPU clock settings. Hardware paths and driver behavior differ between the vendor environment and ButterflyOS.

ButterflyOS already resolves `cpugovernor` by system and ROM and provides separate CPU/DMC and GPU helpers. Audit the applied frequencies and restoration on exit before adding presets. A Battery Saver/Balanced/Performance interface is useful only if backed by measured policies. Avoid adding an adaptive frequency daemon before proving that ordinary governor tuning is insufficient.

Battery percentage is currently known to jump after shutdown/restart on our devices. It is unsuitable as the sole basis for emulator efficiency claims. Use a validated current/voltage interface or controlled external measurements, with comparable charge state and charger conditions.

### Saves, resume and lifecycle behavior

Spruce has integrated Game Switcher handling and architecture-dependent save/state directories. Its launch functions bind separate 32/64 directories for selected cores. That is evidence of attention to compatibility, not proof that all states are portable or that separating every battery save is the right design for ButterflyOS.

Its shutdown script handles several emulator families and includes process-kill fallbacks. ButterflyOS's current lid feature conservatively verifies a RetroArch autosave before normal exit and waits if that cannot be completed. Preserve that integrity guarantee when adding standalone handlers.

Add a paused-game lid shutdown test, because Spruce's latest release specifically fixed autosave behavior for paused emulators. Also check achievement Hardcore restrictions, core changes, failed saves, storage exhaustion and older state restoration. Our successful Crystal test establishes that game's flow, not universal emulator coverage.

## Recommended development sequence

| Order | Work | Effort and acceptance criteria |
| --- | --- | --- |
| 1 | Establish .17 baseline and a usable emulator inventory | Small tooling/documentation task. Record actual core, architecture, version, renderer and applied CPU settings. Confirm every offered choice launches or remove unavailable choices. |
| 2 | Benchmark existing PS1 32/64 and GBA mGBA/gpSP | Low integration effort; testing is the main work. Same game revision and scene, repeat runs, no save regressions. Document practical differences before changing defaults. |
| 3 | Compare existing Dreamcast variants | Moderate testing effort. Choose defaults from frame pacing, compatibility and exit/resume reliability, not version numbers alone. |
| 4 | Investigate N64 core patches and reproduce Rice defects | Moderate to substantial work. Establish source provenance, build natively, collect defect/crash logs and validate multiple games. Keep per-game alternatives where needed. |
| 5 | Trial DSperate on .17 | Moderate native-build and controls work, potentially more if display integration needs changes. Keep melonDS DS as fallback until tested. |
| 6 | Present curated profiles and strengthen lifecycle coverage | Reuse ES per-game settings. Clear labels, predictable defaults, reset-to-default behavior and reliable save/resume across the supported emulator set. Full Game Switcher would be a separate larger feature. |

A mature release process should include a repeatable compatibility matrix, regressions after emulator updates, actual build inventories and clear explanations for users. Optional in-device emulator version information and a compact diagnostic export would make tester reports much more actionable. These are ongoing practices; one package migration cannot establish equal maturity.

## Benchmark protocol

Use .17 for experiments. Start with the current ButterflyOS image and preserve a known-good configuration. Spruce head-to-head tests should use a separate, documented boot setup rather than installing its launcher over ButterflyOS. Keep recovery requirements explicit when changing operating systems.

Match ROM and BIOS hashes, region, resolution, renderer options, audio settings, brightness, Wi-Fi and charger state. Run the same reproducible scene after warm-up at least three times. Keep emulation tests separate from longer battery runs.

Measure emulated speed against the console's expected timing. N64 games may legitimately render at 20 or 30 FPS; a 60 Hz display or VI counter does not prove 60 game FPS. Record displayed counter meaning before calculating frame-time percentiles. If a reliable frame-time stream is unavailable, mark p99/1% metrics unavailable rather than deriving them from a coarse FPS number. Record audio underruns only when a source actually exposes them.

Suggested coverage: PS1 a routine 3D title plus a demanding title; GBA a Pokémon RTC/save test plus a demanding graphics scene; N64 Mario 64, Mario Kart 64, Ocarina of Time and at least one harder title such as GoldenEye or Perfect Dark; Dreamcast Crazy Taxi and Ikaruga; DS one touch-heavy title and one 3D title. Use locally owned games and avoid distributing their contents with benchmark artifacts.

For every candidate, test in-game save reload, state save/load where supported, controller hotkeys, pause/resume, frontend return and the applicable lid behavior. Prefer a reproducible artifact or failing scene over a general report that an emulator feels faster.

## Source map

Pinned Spruce sources:

- [Flip hardware policy](https://github.com/spruceUI/spruceOS/blob/v4.5.2/spruce/scripts/platform/Flip.cfg)
- [PS configuration](https://github.com/spruceUI/spruceOS/blob/v4.5.2/Emu/PS/config.json), [GBA configuration](https://github.com/spruceUI/spruceOS/blob/v4.5.2/Emu/GBA/config.json), [N64 configuration](https://github.com/spruceUI/spruceOS/blob/v4.5.2/Emu/N64/config.json), [Dreamcast configuration](https://github.com/spruceUI/spruceOS/blob/v4.5.2/Emu/DC/config.json), [DS configuration](https://github.com/spruceUI/spruceOS/blob/v4.5.2/Emu/NDS/config.json)
- [Current launch resolver](https://github.com/spruceUI/spruceOS/blob/v4.5.2/spruce/scripts/emu/lib/general_functions.sh), [N64 wrapper](https://github.com/spruceUI/spruceOS/blob/v4.5.2/spruce/scripts/emu/lib/mupen_functions.sh), [DSperate wrapper](https://github.com/spruceUI/spruceOS/blob/v4.5.2/spruce/scripts/emu/lib/dsperate_functions.sh)
- [Architecture-specific saves](https://github.com/spruceUI/spruceOS/blob/v4.5.2/spruce/scripts/emu/lib/ra_functions.sh), [shutdown handling](https://github.com/spruceUI/spruceOS/blob/v4.5.2/spruce/scripts/save_poweroff.sh), [license](https://github.com/spruceUI/spruceOS/blob/v4.5.2/LICENSE)

ButterflyOS source locations:

- `projects/ROCKNIX/packages/rocknix/sources/scripts/runemu.sh`: emulator dispatch and per-game governor resolution.
- `projects/ROCKNIX/packages/rocknix/profile.d/099-freqfunctions`: frequency-policy helpers.
- `projects/ROCKNIX/packages/emulators/libretro/{pcsx_rearmed-lr,gpsp-lr,flycast-lr}/package.mk`: source pins and compilation/package behavior.
- `projects/ROCKNIX/packages/emulators/standalone/`: Mupen64Plus/Flycast launch and build integration.
- `projects/ROCKNIX/packages/ui/emulationstation/patches/056-butterflyos-fullscreen-save-state-manager.patch` and `057-butterflyos-lid-save-and-shutdown.patch`: pending/current development UI integration.
- `projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-lid-shutdown`: conservative autosave/normal shutdown handling.

Spruce's top-level license includes noncommercial terms; component licenses vary. Use it as an integration reference and obtain emulator patches from their upstream source/build projects with their own licenses. Do not assume the entire packaged tree can be copied under an emulator's license.

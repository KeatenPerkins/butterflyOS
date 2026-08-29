# ButterflyOS vision

ButterflyOS is a fast, friendly, controller-first ROCKNIX derivative for the
Miyoo Flip V2. It should feel like a dedicated game console: quick to start,
easy to understand, and dependable without requiring familiarity with Linux or
RetroArch.

## Target user

ButterflyOS is for Miyoo Flip V2 owners who want to add their legally obtained
games and start playing with minimal setup. Routine use must not require a
keyboard, terminal, knowledge of Linux paths, or manual emulator configuration.

## Core principles

1. **Console first.** Common actions use clear language, large controller-friendly
   controls, and predictable navigation.
2. **Fast by default.** Startup, shutdown, menus, and game launching should feel
   immediate. Background services must justify their cost.
3. **Tested defaults.** ButterflyOS chooses a supported emulator, mappings, video
   settings, and performance profile for each system.
4. **Automatic performance.** Lightweight systems conserve power; demanding
   systems receive the CPU and GPU performance they need. Per-game overrides are
   available without making tuning a prerequisite.
5. **Safe customization.** Advanced controls remain available, but are separated
   from the normal console experience and can be reset without losing games or
   saves.
6. **Friendly ownership.** Adding games, checking BIOS files, managing storage,
   updating, backing up, and recovering should be understandable without Linux
   terminology.
7. **Legal distribution.** ButterflyOS distributes only software, firmware
   replacements, and support data whose licenses permit redistribution. Users
   provide proprietary games and BIOS files.
8. **Maintainable inheritance.** Remain close enough to ROCKNIX to benefit from
   upstream hardware, kernel, emulator, and security work while keeping
   ButterflyOS-specific behavior isolated and documented.

## Product experience

The default interface centers on five destinations:

- Games
- Favorites
- Recent
- Applications
- Settings

Settings use user-facing concepts such as Wi-Fi, Bluetooth, Display, Audio,
Controls, Storage, Game Systems, Updates, and About. Linux services, governors,
core names, logs, SSH, and detailed RetroArch options belong in an optional
Advanced mode.

The first release ships tested emulator cores in the read-only system image so
initial setup works offline and every installation starts from known versions.
A Game Systems screen enables or hides systems; a future catalog may deliver
optional ports, themes, experimental emulators, and updates.

## BIOS policy

ButterflyOS does not ship proprietary console BIOS files. It should provide a
controller-friendly BIOS manager which:

- identifies the files needed by enabled systems;
- reports missing, incorrectly named, and checksum-mismatched files;
- explains where users should copy their own files;
- recognizes valid alternatives where an emulator supports them; and
- never offers unauthorized firmware downloads.

## Performance model

ButterflyOS builds on ROCKNIX's existing per-system and per-game governor
support. The normal experience automatically selects one of these product-level
profiles:

- **Battery Saver** for lightweight systems
- **Balanced** for most systems
- **Performance** for demanding systems
- **Custom** for an explicit per-game override

These names describe user intent. Their CPU, GPU, memory, thermal, and emulator
settings may evolve as measurements on real Miyoo Flip V2 hardware improve.

## Success

ButterflyOS succeeds when a new owner can flash an image, add games and any
required BIOS files, navigate entirely with the built-in controls, and reliably
play without learning that the device is running Linux.

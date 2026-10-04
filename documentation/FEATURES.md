# ButterflyOS v0.2.1 features

ButterflyOS is a hardware-tested Miyoo Flip V2 release focused on a clean,
controller-first experience.

This lists development capabilities, not a guarantee for every game or
controller. See [current build status](CURRENT_BUILD_STATUS.md) for changes
awaiting the next image and [known issues](KNOWN_ISSUES.md) for open failures.

## Console interface

<img src="assets/tools.png" alt="ButterflyOS Tools icon" width="96">

- ButterflyOS boot, shutdown, menu, and tool branding
- Synthwave pixel-art home screen and system artwork
- Games, Favorites, Media, Tools, and Settings home destinations
- Tools also remains accessible through the Start main menu; Settings opens
  that same main menu
- Systems shown only when recognized games are present
- `FC`/`nes` and `SFC`/`snes` ROM-folder aliases
- Larger status indicators for time, battery, Wi-Fi, Bluetooth, charging, and
  connected controller count
- Simplified normal mode with optional Advanced Mode
- PortMaster available from Tools for browsing and installing game ports
  (included in v0.2.4; Flip V2 game compatibility testing is pending)

## Games and controls

- Preinstalled emulator cores and tested defaults for classic systems
- Built-in Menu-button shortcuts for exit, Quick Menu, save/load states,
  state-slot selection, fast-forward, rewind, FPS, and brightness
- Controller-friendly Bluetooth Menu-button capture, test, and reset;
  shortcut layouts depend on the controller and launch path
- Persistent Bluetooth controller reconnection
- Automatic return to built-in Player 1 controls after controller disconnect
- Favorites synchronized between EmulationStation and RetroArch without
  duplicate entries
- Game-art scraping; provider availability and filename matches affect results
- Combined game library across the ButterflyOS card and an optional second SD
  card, with internal-card files taking precedence over duplicate names

## Connectivity and files

- Friendly Wi-Fi selection and password entry
- SSH with a user-selected password and `butterflyos` hostname
- Bluetooth controllers and Bluetooth audio
- ButterflyOS-themed authenticated web file transfer for games, BIOS, music,
  videos, saves, and all storage
- Second-card files exposed through the same web transfer interface
- Samba/SFTP support inherited from the ROCKNIX base

## Media and display

- File browsing for music and video
- Controller-operated MPV audio playback with a ButterflyOS now-playing view
- Compatible H.264 video playback
- HDMI video and audio output
- Return to the internal 640×480 display after HDMI disconnection
- On-the-fly brightness adjustment with M+Up and M+Down
- Safe display-only lid handling: closing blanks the LCD backlight and opening
  restores it without suspending the CPU, GPU, storage, networking, or game

## Setup and recovery

- Stock-OS launcher for no-disassembly ButterflyOS onboarding
- Read-only boot safety check
- Verified SD-multiboot installation
- Stock Miyoo OS remains available when the ButterflyOS card is removed
- Guided restoration of stock boot behavior
- Validated export of the device-specific recovery backup before SD reflashing
- System Manager, Quick Start, and Controls Guide available on the device
- Controller-operated **Format 2nd SD Card** tool for second-slot detection,
  status, exFAT formatting, folder creation, and library refresh

## Butterfly Link

<img src="assets/butterfly-link.png" alt="Butterfly Link app icon" width="96">

- SDL interface operated with D-pad, A/Start, and B/Menu
- Save discovery on both SD cards; party preview and PC-box transfers
- Same-generation local and same-Wi-Fi remote trade/copy for Gen I, II, and III
- Gen I → II copies with Time Capsule conversion
- Gen II → III one-way copies; the source is unchanged and held items are cleared
- Local optional evolution prompts for supported trade evolutions, including
  eligible copies; remote evolution prompts are not yet implemented
- ROM-derived, per-ROM cached sprites and supported name/detail lookup;
  Gen I/II sprites have a light backing for visibility
- Backup copies retained before replacing selected original saves

This app manipulates save files; it does not provide in-game cable sessions,
battles, party transfers, Gen II → I conversion, or Gen III → II conversion.
See [Butterfly Link](BUTTERFLY_LINK.md) for supported games, workflow, and limits.

ButterflyOS does not include commercial games or proprietary console BIOS
files. See [Known Issues](KNOWN_ISSUES.md) for Alpha limitations.

# ButterflyOS v0.1.0 Alpha 2 features

Alpha 2 is a hardware-tested Miyoo Flip V2 candidate focused on a clean,
controller-first experience.

## Console interface

- ButterflyOS boot, shutdown, menu, and tool branding
- Synthwave pixel-art home screen and system artwork
- Games, Favorites, Media, Apps, and Settings destinations
- Systems shown only when recognized games are present
- `FC`/`nes` and `SFC`/`snes` ROM-folder aliases
- Larger status indicators for time, battery, Wi-Fi, Bluetooth, charging, and
  connected controller count
- Simplified normal mode with optional Advanced Mode

## Games and controls

- Preinstalled emulator cores and tested defaults for classic systems
- Built-in Menu-button shortcuts for exit, Quick Menu, save/load states,
  state-slot selection, fast-forward, rewind, FPS, and brightness
- Controller-friendly Bluetooth Menu-button capture, test, and reset
- Persistent Bluetooth controller reconnection
- Automatic return to built-in Player 1 controls after controller disconnect
- Favorites synchronized between EmulationStation and RetroArch without
  duplicate entries
- Game-art scraping
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
- Controller-operated Prepare Game Card tool for safe second-slot detection,
  status, exFAT formatting, folder creation, and library refresh

ButterflyOS does not include commercial games or proprietary console BIOS
files. See [Known Issues](KNOWN_ISSUES.md) for Alpha limitations.

# ButterflyOS features

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
- Correct game-list hints: **Y: Search**, **X: Add/Remove Favorite**
- Matching system art for Atari 2600, PC Engine CD, Sega CD, and distinct
  Arcade, Final Burn Neo, and CPS-I/II/III cabinets
- Systems shown only when recognized games are present
- `FC`/`nes` and `SFC`/`snes` ROM-folder aliases
- Larger status indicators for time, battery, Wi-Fi, Bluetooth, charging, and
  connected controller count
- Simplified normal mode with optional Advanced Mode
- PortMaster available from Tools for browsing and installing game ports
  (installation and offered games passed user testing on the Flip V2)

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

## Online updates

- **Start → System Settings → Update ButterflyOS** in normal mode
- Device-specific package and checksum verification before installation
- Restart to Apply reboots the device after verification
- See [How to update](UPDATES.md#how-to-update) for space and power requirements

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
- Optional **System Settings → Hardware → Lid-Closed Shutdown** timer: Off
  (default), 15, 30, or 60 minutes. Opening the lid cancels the countdown;
  changing the setting or rebooting starts a fresh countdown. The optional
  **Save Game Before Lid Shutdown** setting verifies a fresh RetroArch auto-save
  before normal exit and shutdown, backs up the previous auto-save and leaves
  numbered slots unchanged. Both settings default to Off. Updates, failed saves
  and unsupported active games/tools delay shutdown. Save in-game regularly.

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
- Gen II → III one-way copies; the source is unchanged. Version 1.0.3 preserves
  verified held-item equivalents; unmatched items are cleared on the copy
- Local optional evolution prompts for supported trade evolutions, including
  eligible copies; remote evolution prompts are not yet implemented
- ROM-derived, per-ROM cached sprites and supported name/detail lookup;
  Gen I/II sprites have a light backing for visibility
- Backup copies retained before replacing selected original saves
- From v1.0.3: a separate Stadium Gifts group with Amnesia Psyduck and eight
  generated Gym Leader Castle gift equivalents
- From v1.0.3: generated level-5 Mew, Surfing/Flying Pikachu, Dragon Rage Magikarp,
  and Pay Day Fearow/Rapidash gifts for verified
  English Red/Blue/Yellow ROM revisions, with PC-slot preview and backed-up Commit

From v1.0.3: **Local transfer → Gen 2 → Crystal Events** enables or replays
Crystal's native GS Ball/Celebi quest with a reviewed, backed-up Commit.
Enable and Replay passed user testing on .17; the normal Kurt wait is retained.
The Gen 2 menu also adds **Gen 2 Gifts** (Mew) and **Stadium 2 Gifts**
(Baton Pass Farfetch'd and Earthquake Gligar), with Pokémon preview and protected
Commit. Automated save checks pass, and all three gifts passed user testing in
Crystal on .17. **Mystery Eggs** adds fifteen special-move egg recipes, all confirmed working
in Crystal by user testing on .17. Preview shows the hatchling. **Crystal Events → Odd Egg** adds native replay, **Gen 2 Gifts**
adds Celebi for Gold/Silver, and **PCNY Gifts** offers 104 special-move eggs
and 16 shiny adult gifts. All 120 PCNY gifts and the split egg/adult menu passed
user testing in Crystal on .17. See the
[PCNY checklist](BUTTERFLY_LINK_GEN2_PCNY_CHECKLIST.md) for additions and limits. Odd Egg delivery/replay and the Celebi gift in Gold passed user testing
on .17. Silver Celebi and broader Gold/Silver gift gameplay still
need qualification.

This app manipulates save files; it does not provide in-game cable sessions,
battles, party transfers, Gen II → I conversion, or Gen III → II conversion.
See [Butterfly Link](BUTTERFLY_LINK.md) for supported games, workflow, and limits.

ButterflyOS does not include commercial games or proprietary console BIOS
files. See [Known Issues](KNOWN_ISSUES.md) for compatibility limitations.

# ButterflyOS features

ButterflyOS is a hardware-tested Miyoo Flip V2 release focused on a clean,
controller-first experience.

This lists development capabilities, not a guarantee for every game or
controller. See [current build status](CURRENT_BUILD_STATUS.md) for the exact
tested image and [known issues](KNOWN_ISSUES.md) for open failures.

## Live Pokémon trades and battles with Bslap

Available from **v1.4.0**, build **20261022**.

- Open **Tools → Bslap** alongside Blink and Bdex, without Advanced Mode.
- Host or join another ButterflyOS device on the same local network. Both
  players confirm readiness before the host starts the games.
- Trade and battle within Gen 1, Gen 2 or Gen 3 using supported English games.
  Each player controls their own game. No cable or ESP32 adapter is required.
- Per-session ordinary-save backups and logs. Gen 1/2 use working-save copies
  and validate the local result before returning it after a clean exit.
- Gen 3 can show a communication error on room exit. Let one player initiate
  leaving; this gives better results but is not a guaranteed fix. Gen 1/2 passed
  testing without that issue.
- The dedicated newer RetroArch/gpSP pair is used only for Bslap Gen 3. Normal
  gameplay keeps its existing frontend and cores; no kernel changes are needed.

See [Bslap setup, recovery and limitations](BSLAP.md). No games, saves or Pokémon
assets are bundled. Time Capsule trading and internet play are not included.

## Save protection and Bdex

Available from v1.2.0, rebuilt locally and tested on the local test device.

- [Automatic Save Backup](SAVE_BACKUPS.md): opt in under System Settings →
  Hardware. Copies supported ordinary saves from each SD card to the other,
  keeps five versions and leaves 10% free. Requires two prepared writable cards;
  save states and Bdex databases are excluded. Restoration is manual.
- [Bdex](BDEX.md): Tools collection browser for supported Gen 1–3 Pokémon saves,
  all/marked party and PC imports, exact-duplicate filtering, inspector,
  same-generation and supported forward copy exports, Trash and database recovery.
- Bdex **Refresh sprites** rebuilds matching ROM-derived artwork and repairs cache
  references; the optional read-only web viewer uses the root SSH password.
- From v1.5.0, Bdex's inspector adds sprites and generation-aware stat graphs.
  Gen 1 **Where to find** reads grass/cave and Surfing locations from a matching
  supported Red, Blue or Yellow ROM; other encounter types are not indexed yet.
- Names and sprites come from the user's matching ROMs. No Pokémon ROMs, saves
  or extracted sprite caches are bundled. See the guides for compatibility,
  cross-generation conversion and backup limitations.

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
- USB Gadget File Transfer (MTP) through the front charging/data USB-C port
- Samba/SFTP support inherited from the ROCKNIX base

## Media and display

- File browsing for music and video
- Controller-operated MPV audio playback with a ButterflyOS now-playing view
- Compatible H.264 video playback
- HDMI video and audio output
- Return to the internal 640×480 display after HDMI disconnection
- On-the-fly brightness adjustment with M+Up and M+Down
- Lower minimum brightness from v1.5.0 for dark-room use; the minimum menu
  setting remains 5%.
- **System Settings → Hardware → Sleep When Lid Closed**: enabled by default.
  Closing the lid suspends to RAM; opening wakes the device. Disable it to turn
  off only the built-in display while games, networking and HDMI audio continue.
  The preference persists across reboots. A detected suspend failure disables
  lid sleep until it is explicitly re-enabled.
- Lid-Closed Shutdown and Save Game Before Lid Shutdown are retired in v1.1.0. Closing the lid no longer starts a shutdown timer or changes audio mute.

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

## Blink

From v1.3.0, qualified English Gen III games support protected native island
event enable/replay and expanded GameCube, PCNY, tenth-anniversary, regional
and purified Shadow gift equivalents. See the [Blink guide](BUTTERFLY_LINK.md)
for game revisions, story requirements and generation/shiny policies.

<img src="assets/butterfly-link.png" alt="Blink app icon" width="96">

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
Enable and Replay passed user testing on the local test device; the normal Kurt wait is retained.
The Gen 2 menu also adds **Gen 2 Gifts** (Mew) and **Stadium 2 Gifts**
(Baton Pass Farfetch'd and Earthquake Gligar), with Pokémon preview and protected
Commit. Automated save checks pass, and all three gifts passed user testing in
Crystal on the local test device. **Mystery Eggs** adds fifteen special-move egg recipes, all confirmed working
in Crystal by user testing on the local test device. Preview shows the hatchling. **Crystal Events → Odd Egg** adds native replay, **Gen 2 Gifts**
adds Celebi for Gold/Silver, and **PCNY Gifts** offers 104 special-move eggs
and 16 shiny adult gifts. All 120 PCNY gifts and the split egg/adult menu passed
user testing in Crystal on the local test device. See the
[PCNY checklist](BUTTERFLY_LINK_GEN2_PCNY_CHECKLIST.md) for additions and limits. Odd Egg delivery/replay and the Celebi gift in Gold passed user testing
on the local test device. Silver Celebi and broader Gold/Silver gift gameplay still
need qualification.

This app manipulates save files; it does not provide in-game cable sessions,
battles, party transfers, Gen II → I conversion, or Gen III → II conversion.
See [Blink](BUTTERFLY_LINK.md) for supported games, workflow, and limits.

ButterflyOS does not include commercial games or proprietary console BIOS
files. See [Known Issues](KNOWN_ISSUES.md) for compatibility limitations.

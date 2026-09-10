# ButterflyOS roadmap

This roadmap defines outcomes rather than fixed release dates. Hardware testing
is performed on a Miyoo Flip V2 before a milestone is considered complete.

## Milestone 0: Bootable foundation

Status: **Alpha 1 baseline complete; remaining hardware qualification tracked**

- Reproducible Miyoo Flip V2 ROCKNIX build
- Working SD-card boot path and display initialization
- ButterflyOS boot branding
- Navigable EmulationStation interface
- Documented baseline commit and recovery point
- Validate every built-in button, analog control, audio output, rumble, battery
  reporting, charging, Wi-Fi, Bluetooth, both card slots, lid behavior, suspend,
  resume, and shutdown after the replacement shell is installed

Alpha 1 established the bootable and controller-tested baseline. Rumble,
dedicated lid/suspend regression, controlled battery-runtime measurement, and
qualification on a second untouched device remain open.

## Milestone 1: Console shell prototype

- Create a ButterflyOS EmulationStation theme with large, readable targets
- Organize the default experience around Games, Favorites, Recent,
  Applications, and Settings
- Hide unused systems and advanced entries by default
- Establish consistent button prompts, confirmation dialogs, and terminology
- Add a controller-friendly Menu/hotkey capture and test workflow that supports
  joystick buttons as well as Guide/Menu keys exposed through evdev
- Provide a deliberate switch into and out of Advanced mode
- Test the complete normal workflow without a keyboard

Acceptance: a first-time user can discover games, launch one, change basic
settings, and shut down without encountering Linux or RetroArch terminology.

## Milestone 2: Guided setup and system management

- Add a controller-friendly first-boot guide
- Let users enable or hide supported game systems
- Create the expected ROM folders automatically
- Explain SD-card and network-based file transfer in plain language
- Add a BIOS status screen backed by known filenames and checksums
- Offer safe reset actions for system, core, and per-game settings

Acceptance: after copying legally obtained content, the interface clearly shows
what is ready, what is missing, and how to correct it.

## Milestone 3: Tested emulation defaults

- Define the supported core and default configuration for each visible system
- Validate controls, aspect ratio, scaling, latency, save behavior, and exit flow
- Keep the built-in controls available as player 1 when a Bluetooth controller
  disconnects during a game, with automatic and visible player reassignment
- Separate verified systems from experimental systems
- Record known limitations and game-specific exceptions
- Keep emulator versions pinned to the image release

Acceptance: verified systems launch with sensible settings and require no
RetroArch configuration for normal play.

## Milestone 4: Automatic performance profiles

- Measure performance, temperature, power draw, and stability on real hardware
- Map systems to Battery Saver, Balanced, or Performance defaults
- Apply and restore profiles cleanly around every game session
- Add a simple per-game override and an Advanced custom mode
- Protect the device with conservative thermal and frequency limits

Acceptance: lightweight systems avoid needless power use, demanding systems get
appropriate performance, and leaving a game always restores the console's
normal profile.

## Milestone 5: Appliance reliability

- Finalize lid-close, suspend, resume, low-battery, and safe-shutdown behavior
- Preserve saves and settings across updates
- Add backup, restore, and factory-reset workflows
- Detect common storage corruption and configuration failures
- Provide useful graphical errors with an optional diagnostic export

Acceptance: expected interruptions do not lose saves, and a nontechnical user
can recover from common problems without a shell.

## Milestone 6: Updates and first public release

- Document source, licenses, build instructions, supported hardware, and credits
- Produce signed or checksummed full images and incremental updates
- Define stable, testing, and development release channels
- Test fresh installation, upgrade, rollback, and recovery
- Publish a concise user guide and troubleshooting guide

Acceptance: another owner can independently install, use, update, and recover
ButterflyOS on the supported Miyoo Flip V2 revision.

## Flagship feature: Butterfly Link

Create a game-focused application that recreates the handheld link-cable
experience between two Miyoo Flip V2 systems over a direct or local wireless
connection. The initial target is legitimate user-provided copies of the
mainline GB/GBC monster-trading games, followed by compatible GBA titles.

### Alpha-era feasibility work

- Identify an emulator/core whose serial-link implementation can be bridged
  reliably between two separate devices
- Prototype discovery, pairing, connection health, and synchronized launch on
  two Flip V2 test units
- Determine which game regions, revisions, ROM hacks, save formats, and core
  versions can interoperate safely
- Verify that failed connections never corrupt or overwrite either player's
  save; make automatic pre-session save backups mandatory
- Keep the prototype behind an Experimental or Advanced switch and exclude it
  from the Alpha 1 acceptance criteria

### GB/GBC release scope

- Provide a controller-only **Butterfly Link** application with **Host** and
  **Join** choices and plain-language status messages
- Discover nearby ButterflyOS devices on the same network, with an IP/manual
  connection fallback
- Match compatible games and emulator versions before launch; explain a
  mismatch instead of attempting an unsafe session
- Support trading and battling in Red, Blue, Yellow, Gold, and Silver first,
  then test Crystal and regional/revision variants separately
- Launch both games into a synchronized link session and return cleanly to the
  normal game library afterward
- Preserve each user's normal saves and create recoverable backups before and
  after every session
- Document that ButterflyOS supplies no games, copyrighted firmware, or
  online matchmaking service

Acceptance: two clean ButterflyOS devices can discover one another, establish
a stable session, trade and battle using supported user-provided games, retain
valid saves after disconnects, and recover the pre-session saves after an
interrupted or failed transfer.

### Later GBA scope

- Investigate link support and performance for Ruby, Sapphire, Emerald,
  FireRed, and LeafGreen
- Add GBA only after GB/GBC sessions are reliable; do not assume the GB/GBC
  transport, timing, save handling, or emulator architecture will transfer
  unchanged
- Explore direct device-to-device setup only after local-network operation is
  dependable and easy to diagnose

## Deferred until after the first stable release

- Support for additional handheld models
- A network catalog for optional ports, themes, and experimental emulators
- Cloud accounts or online save synchronization
- Major divergence from the ROCKNIX build system
- Shipping any proprietary games or BIOS firmware

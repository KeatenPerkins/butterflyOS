# ButterflyOS roadmap

This roadmap defines outcomes rather than fixed release dates. Hardware testing
is performed on a Miyoo Flip V2 before a milestone is considered complete.

## Milestone 0: Bootable foundation

Status: **bootable baseline complete; hardware validation in progress**

- Reproducible Miyoo Flip V2 ROCKNIX build
- Working SD-card boot path and display initialization
- ButterflyOS boot branding
- Navigable EmulationStation interface
- Documented baseline commit and recovery point
- Validate every built-in button, analog control, audio output, rumble, battery
  reporting, charging, Wi-Fi, Bluetooth, both card slots, lid behavior, suspend,
  resume, and shutdown after the replacement shell is installed

## Milestone 1: Console shell prototype

- Create a ButterflyOS EmulationStation theme with large, readable targets
- Organize the default experience around Games, Favorites, Recent,
  Applications, and Settings
- Hide unused systems and advanced entries by default
- Establish consistent button prompts, confirmation dialogs, and terminology
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

## Deferred until after the first stable release

- Support for additional handheld models
- A network catalog for optional ports, themes, and experimental emulators
- Cloud accounts or online save synchronization
- Major divergence from the ROCKNIX build system
- Shipping any proprietary games or BIOS firmware

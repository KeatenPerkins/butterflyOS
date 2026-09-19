# ButterflyOS roadmap

This roadmap defines outcomes rather than fixed release dates. Hardware testing
is performed on a Miyoo Flip V2 before a milestone is considered complete.

## Milestone 0: Bootable foundation

Status: **Alpha 2 public-release candidate; remaining limitations tracked**

- Reproducible Miyoo Flip V2 ROCKNIX build
- Working SD-card boot path and display initialization
- ButterflyOS boot branding
- Navigable EmulationStation interface
- Documented baseline commit and recovery point
- Validate every built-in button, analog control, audio output, rumble, battery
  reporting, charging, Wi-Fi, Bluetooth, both card slots, lid behavior, suspend,
  resume, and shutdown after the replacement shell is installed

Alpha 1 established the bootable baseline. Alpha 2 has completed qualification
on a second untouched device. Rumble, dedicated lid/suspend regression, and
controlled battery-runtime measurement remain open known limitations.

### September 19 stability and crash-forensics sprint

The September 16 live diagnostic setup and verification are documented in
`~/Documents/miyoo-flip-crash-logging-setup.md`. Preserve a copy of its scripts
and collect its second-card logs before reflashing or repairing/reformatting the
card. Treat the 512 MiB journal and 2 GiB Wi-Fi debug capture as temporary
development instrumentation, not public-release defaults.

The safe development baseline now disables both hardware suspend and ROCKNIX
fake suspend on the Miyoo Flip. Closing the lid is intentionally inert until a
ButterflyOS-specific display/backlight-only handler passes extended lid cycling
and storage-integrity testing. Do not restore deep suspend on this hardware:
captured failures show `mmc0` timing out and disappearing on resume, followed by
an aborted `/storage` ext4 journal.

- Verify that the live persistent journal, rolling snapshots, EmulationStation
  archive, RetroArch log, boot history, and Wi-Fi capture still work; import a
  reviewed, smaller, bounded version into source so diagnostics survive future
  images without depending on hand-installed autostart files.
- Enable and validate kernel `pstore`/`ramoops` only after selecting a safe,
  non-overlapping RK3566 reserved-memory region from the actual memory map.
  Include console capture, confirm records survive a controlled panic/reboot,
  and document how exported diagnostics redact private network information.
- Make USB autosuspend policy explicit for the internal RTL8733BU Wi-Fi/BT
  device as defensive hygiene, and run controlled long-sleep A/B tests with
  Wi-Fi enabled versus fully powered off. Twelve hours and three observed
  resumes showed clean Wi-Fi re-enumeration on EHCI bus 4, so Wi-Fi is no
  longer the leading suspect. Do not misattribute the repeatable empty-xHCI
  controller reinitialization warning to the separate EHCI Wi-Fi path.
- Investigate the reproducible Mali suspend-path warning `unbalanced disables
  for vdd_gpu`. It occurs through the out-of-tree `mali_kbase` power-management
  callbacks and is the strongest current lead for display/resume instability.
  Compare the driver/kernel pairing, regulator ownership and enable/disable
  balance; preserve the complete call trace in the diagnostic record.
- Evaluate a conservative approximately 256 MiB LZ4 zram swap configuration on
  the 1 GiB device. Measure memory pressure, latency, CPU cost, thermals, and
  emulator performance before making it a default.
- Define watchdog policy deliberately. Enable a runtime hardware watchdog and
  consider `oops=panic` only after ramoops is proven, then test clean shutdown,
  userspace failure, kernel oops, and hard-hang recovery separately.
- Run a read-only `fsck.exfat` on the second game card before any repair. Decide
  whether user interoperability requires exFAT or whether ext4 should be an
  optional reliability-focused format. Never keep the only crash evidence on
  an unjournaled card without plain-text/rotated fallbacks.
- Keep core dumps disabled by default on the constrained handheld. Reconsider
  only a tightly capped, opt-in development mode.
- Review lower-priority boot/runtime noise: BFQ udev timing, the sixaxis unit
  naming warning, unused BlueZ SAP/BNEP profiles, repeated `nmbd` WORKGROUP
  conflicts, and Mali-kbase/kernel version-skew warnings.
- Provide a development logging mode that can drop `quiet` or raise kernel log
  level without making verbose boot output the normal end-user experience.
- Make RetroArch Thumbnails the effective scraper for existing installations,
  not only clean defaults. Hide or repair ArcadeDB while its hardcoded HTTP
  endpoint/redirect behavior is broken and document that it is arcade-focused.
  Improve user-visible handling of exact-name misses (region/revision tags,
  `FireRed`/`LeafGreen`, and enhanced/compatibility tags) without renaming ROMs
  or breaking correspondingly named save files. Keep account-requiring IGDB
  optional and never ship user API secrets.

Acceptance: an induced test failure leaves bounded, readable previous-boot
evidence; long-sleep testing can distinguish GPU/display, Wi-Fi/USB, storage,
OOM, userspace, watchdog, and kernel-panic failure classes; normal builds do
not impose excessive SD wear or multi-gigabyte logging.

## Milestone 1: Console shell prototype

- Create a ButterflyOS EmulationStation theme with large, readable targets
- Organize the default experience around Games, Favorites, Recent,
  Applications, and Settings
- Hide unused systems and advanced entries by default
- Establish consistent button prompts, confirmation dialogs, and terminology
- Preserve the level-filled battery icon while charging and render a separate,
  legible lightning-bolt overlay or adjacent indicator
- Add a controller-friendly Menu/hotkey capture and test workflow that supports
  joystick buttons as well as Guide/Menu keys exposed through evdev
- Provide a deliberate switch into and out of Advanced mode
- Test the complete normal workflow without a keyboard

Acceptance: a first-time user can discover games, launch one, change basic
settings, and shut down without encountering Linux or RetroArch terminology.

## Milestone 2: Guided setup and system management

- Remove Tailscale, rclone, and Syncthing from the Flip base image after the
  completed network/cloud audit. Retain the tested Web File Transfer, SSH/SCP,
  and rsync workflows; reconsider advanced services only as maintained optional
  packages with explicit onboarding and security guidance.

### Alpha 2 release gate: device-local preloader patching

Replace the Alpha 1 bundled stock and patched preloader images with a workflow
that derives everything from the preloader already installed on the user's own
Miyoo Flip V2:

Implementation status: the device-local patcher, exact backup, verifier,
exact-only restore path, and off-card export workflow are implemented. The full
physical round trip passed on two Flip V2 devices. The remaining gate is the
final rebuilt-image audit and release packaging.

- Read the device's original 2 MiB preloader without distributing a vendor
  preloader image.
- Recognize and validate supported preloader structures before modifying data.
- Save an exact device-specific backup and SHA-256 manifest to the SD card
  before any internal write.
- Export the validated backup in a portable archive so users can preserve it
  on another physical device before reflashing the SD card.
- Reread and verify the saved backup independently.
- Apply only the documented SD-multiboot patch locally on the device.
- Validate the generated image structurally and refuse unknown revisions.
- Check model, SoC, flash geometry, bad blocks, and battery/external power.
- Write, read back, and compare the patched preloader byte-for-byte.
- Attempt automatic rollback if patched-image verification fails.
- Make Restore Stock Miyoo Boot use only the verified backup from that same
  device; never substitute a generic stock image silently.
- Attribute and comply with the license of any adapted patching implementation.
- Complete install, card/no-card boot, restore, and reinstall testing on both
  the primary device and a second untouched Miyoo Flip V2.

Acceptance: the public image contains no stock or prepatched vendor preloader
binary, installation produces a verified personal recovery copy before any
write, and restoration returns the exact original bytes.

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
  from the Alpha 2 acceptance criteria

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

- Add a game-audio mute shortcut and a controller-first background-music
  overlay so users can browse and control their own music while a game is
  running. Keep game and music volume independent, restore audio state on exit,
  and avoid interfering with emulator hotkeys or save-state input.
- Support for additional handheld models
- A network catalog for optional ports, themes, and experimental emulators
- Cloud accounts or online save synchronization
- Major divergence from the ROCKNIX build system
- Shipping any proprietary games or BIOS firmware

# ButterflyOS v1.8.0 — Grid and Video views, faster Pokémon linking

Stable release for **Miyoo Flip V2**, build **20261106**.

## Download and install

Download the OS image and matching SHA-256 checksum from the [latest stable release](https://github.com/KeatenPerkins/butterflyOS/releases/latest). Follow [installation and recovery](BUTTERFLYOS_INSTALL_AND_RECOVERY.md), including exporting the device-specific recovery backup. Flashing erases the card; an already configured device does not need its internal preloader setup repeated.

Existing users can update through **Start → System Settings → Update ButterflyOS**. Save and exit games first, keep at least 3 GB free on the OS card, charge to at least 50%, and keep power connected through the front USB-C port. Wait for download and verification, then choose **Restart to Apply Update**. Updates retain games, saves, artwork, settings and Bdex collections; back up important files first.

## Interface and themes

- Both ButterflyOS themes now have a centered, adaptive two-row Grid layout. It adjusts the number of columns for handheld, widescreen and ultrawide displays, fits artwork without stretching, highlights the selected card, and shows its title below the grid.
- Grid Size Override is available in Advanced Mode. Automatic adapts to the display; existing fixed global and per-system choices are preserved when using the regular settings menu.
- Video view now uses the same styled game-list layout. System folders retain their console artwork; individual games can play silent video previews, with artwork shown when a preview is unavailable.
- The user confirmed Grid, Video, HDMI sizing and the other UI changes passed testing on the local test devices.

## Blink and Bslap

- Blink now recognizes valid Crystal ROMs inside single-ROM ZIP archives in its event menus by checking the ROM contents.
- Bslap accepts qualified single-ROM ZIPs for Gen 1 and Gen 2 with the default Gambatte backend, including Time Capsule. Raw and ZIP copies can link together. Multiple-ROM, malformed, oversized, modified and unsupported ROMs are rejected; the development SameBoy fallback still requires raw files.
- Bslap caches ROM qualification for unchanged files and rejects unrelated Game Boy headers early, reducing repeated library scans. Full ROM validation still occurs before launch.
- Filtering bind-mounted patch files out of suspend card probes prevents a false probe failure from disabling lid sleep.
- The user confirmed Blink, Bslap, lid sleep and UI/UX testing passed on the test image.

## Updater

The update screen now shows animated writing, read-back verification and finalization stages instead of appearing stuck at 100% while data is written. The on-screen update flow itself was not separately verified during this test cycle; the installed boot updater will display these stages when applying a later update.

## Validation and limits

The local image passed 64 targeted automated tests and 20 image checks, including artifact checksums, decompression, partition/filesystem checks, matching flash/update payloads, embedded updater contents and queued source changes. Both test SD cards passed full read-back verification. User hardware testing confirmed UI/UX, Blink, Bslap and lid sleep.

Build **20261106** from source commit `1661cf148382f0b2f2e0edfb1f4a0aa45381b5a8`. This image is built for the Miyoo Flip V2. Read [Known Issues](KNOWN_ISSUES.md) and the individual guides for compatibility limits.

# Current build and test status

Reviewed: 2026-10-05.

## Pending v1.0.1 changes

- The audio pacing fix has been confirmed live for GB, GBA, and NES.
- RetroAchievements account settings are exposed in normal mode at
  **Start → Game Settings → RetroAchievements Settings**, including builds
  without frontend API credentials. Login and unlocking need tester verification.
- SSH logins use a cyan ButterflyOS block-letter wordmark,
  followed by the existing version and build details.
- The earlier local v1.0.1 image predates this menu change and must be rebuilt.
  The bundled rebuild and release verification are in progress. See
  [release notes](RELEASE_NOTES_v1.0.1.md).

## First stable release: v1.0.0

- Published [v1.0.0 stable release](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.0.0),
  marked Latest and not a prerelease; device/updater identity: `20261006`.
- All nine uploaded asset sizes and GitHub SHA-256 digests matched the verified
  local files. The downloaded public update manifest matched.
- The prepared .20 device updater check returned `20261006`; download and
  installation were left for the user to initiate.
- Target: Miyoo Flip V2 only.
- The user completed system-by-system checks, verified PortMaster, and found
  no additional UI issues on the v0.2.4 testing baseline.
- The release adds corrected X/Y hints, proper update reboot, normal update
  confirmation, Ports icon matching, and eight dedicated system artworks.
- Binary source: `efcc19513baa5ea2b756b619fe81196873e8aebc`; build completed with all
  668 steps passing. Image/update checksums and filesystem/content checks passed.
- Image SHA-256: `8b167f25ebba69ff24e5904f4c99068b6b5eb2b357905905a24aabc3d661ecaa`.
- Update SHA-256: `a223780485543e05d8a6fb4f6aaf0d6e0c6e582181a2167b30b2fe30dbfdbb66`.
- Earlier hardware tests are not represented as testing the exact new binary;
  its warning/reboot changes and new artwork still need an installed-device check.
- See [the exact artifact audit](PUBLIC_RELEASE_AUDIT.md#october-4-2026-first-stable-release-v100).
- See [v1.0.0 release notes](RELEASE_NOTES_v1.0.0.md) and
  [release procedure](RELEASE_PROCEDURE.md).

The sections below are historical build and testing records.

## Published v0.2.1

- Image source: `8ba1f47590a329ba602a11219ed6fe87d46108cc`.
- Asset: `ButterflyOS-v0.2.1-Miyoo-Flip-V2.img.gz`.
- SHA-256: `d7d855ec41a41018139cf1a1ad58f1d8d077f1b55b3abdebc6b62593bb0e5228`.
- Full build and compressed-image checks passed. Full SD read-back hash matched.
- User confirmed the narrower carousel/HDMI hint layout looks better and works.
- Scraper persistence fix and ButterflyOS updater are included. Online updating
  awaits a subsequent-build test; no update manifest is published yet.
- See [v0.2.1 release notes](RELEASE_NOTES_v0.2.1.md).

## Published Alpha 2 baseline

- Image source: `39bb3a803bd481b7a610cf2b19509b2c13d39891`.
- Asset: `ButterflyOS-v0.1.0-alpha.2-Miyoo-Flip-V2.img.gz`.
- SHA-256: `24eb2a762b55fb6aae77caf49c5450f3b3f1bf874b5cbc01016469dc0ab3aede`.
- All 668 main-image steps passed; image integrity and filesystem checks passed.
- The user confirmed the flashed image boots successfully. The preceding image
  passed scraper/artwork testing; this rebuild adds the fresh-install
  ScreenScraper default, confirmed in the packaged SYSTEM filesystem.
- See [release notes](RELEASE_NOTES_v0.1.0-alpha.2.md) and the October 2 section
  of [the artifact audit](PUBLIC_RELEASE_AUDIT.md). This remains test software.

The sections below retain historical development evidence. References there
to pending rebuilds describe earlier candidates, not the release above.

## October 3 scraper fix included in v0.2.1

Patch 043 fixes scraper metadata persistence for console systems grouped under
Games, flushes completed scrape batches, and preserves dirty recovery entries
until merged into the main game list. The frontend package compiled and was
deployed live on .17. Existing artwork links were recovered for 1,505 games and
passed loaded-metadata/sample-image checks across two frontend restarts.
A fresh full-SNES scrape wrote persistent metadata for 388 games. The user
confirmed artwork and favorites remained after reboot. The successful October 3
image includes the fix. See
[ScreenScraper details](SCREENSCRAPER.md#october-3-grouped-system-persistence-fix).

## Current test image

- Image: `ROCKNIX-RK3566.aarch64-20261002-Miyoo_Flip_V2.img.gz`
- Compressed-image SHA-256:
  `5db66e6a010360bba1351be1649b1dce8fda3db780807e40b842056191b62847`
- Used on two Miyoo Flip V2 test devices.
- Rebuilt October 2; all 668 image steps passed. This image includes the Gen II
  banked-PC-box persistence fix and the Gen I/II text-terminator fix that
  prevented Crystal's PC from opening after some converted transfers.
- It also includes ScreenScraper using the release developer credentials. The
  frontend identifies itself as ButterflyOS and uses one thread when a personal
  ScreenScraper account is not configured. It has not yet been flashed or
  hardware-tested; the prior live frontend update was tested successfully.
- Built from a development working tree; it is not an immutable release tag
  or proof of clean-checkout reproducibility.

The current app is **Butterfly Link**, implemented as a save-transfer tool.
The old link-cable/netplay launcher has been removed from the installed
Butterfly Link workflow.

## Hardware observations

- Local same-generation trades/copies and generation-aware sprite browsing
  passed user testing for supported Gen I, II, and III saves.
- Local Gen I → II and Gen II → III transfers passed development tests;
  these do not qualify every game revision or save combination.
- Remote same-generation trade and copy passed two-device user testing.
- Remote Gen II → III copy passed two-device user testing on October 2.
- Remote Yellow → Crystal copy generated a valid-looking prepared save with
  Pikachu in box 1, slot 3. The joiner logged a commit; after launching Crystal,
  the live save no longer contained Pikachu. The cause was reproduced: the
  helper edited the active PC box but did not flush it to the banked box that
  the game reloads on Continue. The Gen II writer is now corrected in source
  and deployed live; a real-game save/exit/reopen retest is still required.

## Changes included in this image

- Long Butterfly Link notices and confirmation filenames wrap to rendered
  screen width; long notices can be scrolled with Up/Down.
- Clear trade/copy completion messages explain which original save changed
  and that backups were retained. A short input guard prevents accidental
  dismissal of the result screen.
- Local and remote commits use fresh save timestamps and verify written
  SHA-256 values. A failed hash check attempts restoration from the backup.
  These checks do not prove that an emulator will preserve the result after
  loading a state or selecting a redundant save block.
- Start icon moves closer to its Main Menu label.
- Network Settings hides the inherited Cloud Services and VPN Services
  groups unless Advanced Mode is enabled. Hiding these controls does not
  qualify the services or reintroduce excluded packages.

Local socket simulations passed approved and cancelled Gen I → II and
Gen II → III copies. Save-commit checks passed byte verification, fresh
timestamps, backup retention, and rollback after an injected hash mismatch.
The layout was checked at 640×480; Python syntax, theme XML, and patch
application checks passed. These are workstation checks, not final-image
hardware qualification.

## New changes deployed live and included in the current image

- Onboarding package 2.6.10 flushes the edited Gen II active box to its banked
  storage before every copy, swap, Time Capsule conversion, and evolution write.
- Converted Gen I/II nicknames and original-trainer names now use the game's
  required 0x50 text terminator. The initial persistence fix exposed malformed
  converted names when opening Crystal's PC (white screen). Crystal on .17
  was repaired from the session backup, preserving the copied Pikachu; the
  in-game PC-open/save/exit/reopen retest passed with the prior live helper;
  the same code is now in the current image.
- Regression test: `tests/butterflyos-gen2-box-persistence-test.py`. All 48
  cases pass on the workstation and on .17 using private fixtures; the old
  helper fails the same test. It checks both SRAM banks and simulates Continue's
  banked-box load and validates occupied-box name terminators. The real
  Crystal PC-open/save/exit/reopen retest has also passed on the live helper.
- Live helper SHA-256:
  `25b60281206c9c9403f18ec56920baba70a16d858ab103849d73fb4089b6a06e`.
  It is bind-mounted over `/usr/bin/butterflyos-save-trade` on .20 and .17.
  The override disappears on reboot; its source code is included in the
  current image. Original helpers and live replacement are retained under
  `/storage/.config/butterflyos/save-trade/helpers/`.

## Before publication

The October 2 flashed-device test exposed missing artwork and misleading scrape
completion after DNS failures. The live regular-game-list workaround restored
artwork and was confirmed by the user. Frontend patches 041 and 042 stage the
linked-list reader fix and scraper failure/retry feedback. They are not in the
image identified above; see `SCREENSCRAPER.md`. A replacement build and focused
test are required before publishing an image.

- Confirm ScreenScraper in this image after flashing: scrape a game, restart
  the frontend, switch HDMI on and off, and verify artwork remains. See
  [ScreenScraper setup and verification](SCREENSCRAPER.md).

1. Build from a recorded, committed source revision.
2. Recheck the exact image, package/license manifest, and private-content
   exclusions; publish its own checksum rather than an older image's checksum.
3. Retest installation/recovery, games, media, networking, hotkeys, and both
   SD cards on that image.
4. Retest remote Gen I → II copy, including opening the destination game,
   examining the PC, saving, exiting, and reopening it.
5. Confirm the documented built-in and Bluetooth hotkeys on that image;
   their shoulder-button layouts currently differ in source.
6. Replace the pending release fields and GitHub repository placeholder.

## Limits confirmed during documentation review

- Gen III Trade rejects different save-format families; Gen III Copy does not.
- Remote transfer does not yet offer the local evolution prompt.
- Menu capture does not learn all other controller button codes.
- A remote transaction is not an all-or-nothing operation across both devices;
  an interruption between commits needs inspection and recovery from backups.
- Older package manifests and image audits need regeneration/repetition rather
  than being described as final checks of this candidate.

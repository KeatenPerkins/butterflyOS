# Current build and test status

Reviewed: 2026-10-06.

The user authorized committing/pushing the pending changes and starting the next
full Miyoo Flip V2 aarch64 build with updater ID `20261008`. Publication remains
pending the image audit and device validation.

## Next-build scope and readiness review

- Include the SSH branding/hostname corrections, supplied OpenBOR/EasyRPG and
  Quick Start artwork, 30-second journal sync, RetroAchievements browser gate,
  new SD Card Info tool with its supplied transparent icon, and the
  graphical Format 2nd SD Card conversion. Settings puts Game Settings first
  and Network Settings second, ahead of optional RetroAchievements entries.
- Performance experiments are complete for this review. The user chose to
  retain current performance settings and archive the temporary tester and its
  six completed recordings on the local PC. The tester and logs are not part
  of the OS build; no CPU/GPU/memory/audio/wireless tuning is staged.
- All 43 EmulationStation patches apply in sequence to a clean upstream source
  checkout. Four SD-card storage edge cases and script/package syntax checks
  pass. The graphical helper's bridge-key, selection, and cancellation logic
  checks pass; physical A/B controls and SD Card Info layout still need a
  device check.
- SD Card Info and Format 2nd SD Card have prepared graphical conversions. Quick
  Start, Controls Guide, System Manager, diagnostics, and recovery conversions
  remain future work. The performance tester is excluded from that work.
- The next image still requires a full build, fresh artifact audit, and device
  smoke checks before stable publication. Its updater identity must advance
  beyond `20261007`. `.17` is being kept on its existing release for a direct
  update that skips the intermediate release.

## Pending SD Card Info tool

- SD Card Info is the first tool converted to the Butterfly Link graphical
  style. Its shared UI helper reuses the existing Link renderer and controller
  bridge, with A to select and B to go back. A themed dialog fallback uses the
  same controller profile. Physical-button and graphical device testing remain
  pending; Format 2nd SD Card also uses the shared graphical helper.
- Tools → SD Card Info shows both card capacities, filesystem space used and
  available, mount/read-only status, filesystem type, and combined available
  space. It reports the OS-card space used for updates separately.
- The tool reads filesystem counters, mount information, and sysfs without
  scanning ROM folders. It handles an absent or unmounted second card without
  reporting the OS filesystem's free space as second-card capacity.
- SD Card Info uses the supplied `sdSpace.png` artwork as its dedicated menu icon.
- Controller-operated Refresh and Save Report actions need no keyboard.
  Normal-mode Tools visibility is included in the frontend patch.
- Source/package changes are prepared for the next build. No OS rebuild or
  tuning changes have been made; `.20` performance testing is unaffected.
- The reporter ran on `.17` in about 0.86 seconds and matched `df`: 21.4 GiB
  available on the OS card and 14.5 GiB on the second card. Four automated
  storage edge-case checks, launcher/package syntax, frontend patch application,
  and XML registration passed. Controller UI testing is still pending.

## Pending Format 2nd SD Card appearance and controls

- The existing Tools entry uses the shared Butterfly Link graphical renderer
  and controller bridge: A selects and B cancels or returns.
- Existing-card setup, library refresh, status, and exFAT formatting still use
  the original shell backend. Both erase confirmations remain mandatory, with
  Cancel selected by default. The target identity is checked again after the
  confirmations; formatting stops if the partition remains mounted.
- The progress screen warns against powering off or removing either card.
  The dialog fallback uses the Link theme and input profile too.
- Automated checks exercise cancellation at each confirmation, target-check
  failure, and successful protocol completion with mocked disk commands.
  A backed-up preview is installed in the existing Tools entry on `.20`.
  Its SDL renderer, fonts, and controller bridge initialized successfully;
  the read-only status check reported no second card present. The user
  approved the live appearance. Physical A/B confirmation and formatting a
  disposable card remain validation items.
  No live card was formatted; the next full build is now authorized.

## Pending Settings menu order

- In the full Settings menu, Game Settings appears first and Network Settings
  second when networking is supported. Remaining options retain their order.
- Existing callbacks, icons, capability checks, and restricted-mode visibility
  are preserved. This change requires rebuilding EmulationStation; the live
  `.20` preview only changes the Format 2nd SD Card tool.

## Pending RetroAchievements stats-browser correction

- The advanced Game Settings stats-browser entry now requires frontend API
  support, matching the existing main-menu entry. Builds without the separate
  API credentials no longer expose a browser that returns "Unauthenticated".
- Player account settings and in-game achievements remain available. The user
  confirmed that Pokémon Crystal on `.20` logs in and loads its achievements.
- This source fix requires the next EmulationStation rebuild and OS release;
  no live device or released image has been changed.

## Pending crash-log durability improvement

- Miyoo Flip V2 image assembly sets journald's disk sync interval to 30 seconds,
  including builds that reuse the systemd package cache. Existing compression,
  10 MB storage target, and seven-day retention are unchanged.
- This reduces the window of unsynced journal entries during a forced reboot;
  it cannot guarantee the final messages survive a hard lockup or power loss.
- No device setting or released image has been changed. Performance validation
  on the Flip is pending the next build.

## Pending system artwork

- Quick Start uses the new supplied `quickStart.png` artwork for its Tools
  menu icon. The image is preserved unchanged.
- OpenBOR and EasyRPG have dedicated supplied portrait artwork, mapped to
  the `openbor` and `easyrpg` theme names. The originals are preserved under
  `artwork/system-icons/source/` and included in the runtime artwork directory.
- Theme package version `0.1.8` picks up the new assets on the next rebuild.
  No image rebuild or device installation has been performed for this change.

## Pending SSH branding corrections

- Use explicit light-blue RGB color for the login wordmark instead of the
  terminal's named cyan palette color.
- Stamp the SSH banner version/build details during final image assembly so
  cached package metadata cannot disagree with the updater build number.
- Apply the saved ButterflyOS hostname directly; transient-only hostnamed
  changes were overridden by the inherited static ROCKNIX hostname on `.20`.
- `.20` has a temporary live banner/hostname preview without a reboot. Its
  banner now shows `20261007`. The preview lasts until reboot; permanent
  source changes still require a future image build and release.

## Bundled v1.0.1 maintenance release

- Published [v1.0.1](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.0.1)
  as Latest stable. All nine uploaded assets passed checksum/size verification;
  `.17` discovers build `20261007` without initiating installation.

- Public version `v1.0.1`; updater build ID `20261007`; Miyoo Flip V2 only.
- Includes the confirmed GB/GBA/NES audio pacing fix, normal-mode
  **Start → Game Settings → RetroAchievements Settings**, and a cyan
  ButterflyOS SSH wordmark with existing version/build details.
- Full rebuild and host artifact checks passed. The packaged menu and banner
  match the rebuilt source; all three changes are included in the same image.
- The user updated `.20` and confirmed Pokémon Crystal logs in to
  RetroAchievements and loads its achievement set. Unlocking is not yet
  confirmed. The live FPS fix was confirmed before the full rebuild.
- See [release notes](RELEASE_NOTES_v1.0.1.md) and
  [exact artifact audit](PUBLIC_RELEASE_AUDIT.md#october-5-2026-bundled-maintenance-release-v101).

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

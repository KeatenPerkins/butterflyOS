# Current build and test status

Reviewed: 2026-10-20.

## Local test build 20261020 — changes since v1.2.0

Built locally from runtime source `78e4f5f5da758cce309d2d853cabcf48e1c238a0`,
onboarding package **2.6.49**. All 668 package steps completed. Final-image
checks passed: compressed-image/update SHA-256, gzip integrity, GPT, read-only
FAT/ext4 checks, matching flash/update KERNEL and SYSTEM payloads, rebuilt
initramfs embedded in KERNEL with updater verification/failure handling and
BusyBox applets, exact installed Python sources, all gift catalogs/submenus,
and ROM/save exclusion checks (standard GZDoom PK3 engine resources accounted
for separately).

Image: `ROCKNIX-RK3566.aarch64-20261020-Miyoo_Flip_V2.img.gz`.
SHA-256: `d117a0eee1fd62c85e53bf2b46a155ee615b03a2eb571171d66f5ccbe3aea9a4`.

**Local-device checklist passed; not published.** The user confirmed the rebuilt
image passed boot/storage, all new Blink menu groups, representative gift
preview/Cancel/Commit and save/reload, Metang's National Ribbon, Mew battle
obedience, a native island event, ordinary Blink transfer, Bdex/web viewer,
second-card Save Backup, game launch/audio/hotkeys, charging indication, lid
sleep/resume, HDMI and shutdown/reboot. These are reported integration checks,
not an exhaustive test of every gift on every game or a new overnight sleep test.
Documentation-only commits after the runtime revision do not change image bytes.
The following changes are included:

- **Blink Purified Shadow Gifts:** 135 recipes in three groups: Colosseum
  (49 including two Suicune move sets), XD (83), Colosseum e-Reader (3).
  National Ribbon, documented purified moves, source-specific shiny policy,
  XD fateful flag and zero-IV e-Reader equivalents. GBA gift delivery only;
  capture/purification gameplay is not emulated. Automated checks passed 5,940
  recipe/layout/game combinations and 675 protected commits across five games
  (24 record layouts in Emerald; five representative layouts in each other
  game), plus shiny candidates, exact ribbon bits, zero IVs and menu routes.
  Regional regression (1,560 combinations/65 commits) and 11 safety tests passed.
  Source fixture saves remained unchanged. Live installation and hashes verified
  on the local test device. The user confirmed the purified gifts working;
  specific recipe/game/ribbon/battle/save checks were not enumerated, so this
  is not an exhaustive per-recipe/per-game qualification.
- **Blink Regional Gifts:** 13 distinct generated campaign equivalents, with
  non-shiny policies, Metang National Ribbon and Mew obedience flag. Existing
  protected preview/backup/Commit applies. Automated checks passed 1,560
  recipe/layout/game combinations and 65 protected commits across five games,
  including exact ribbon/fateful bits and shiny rejection. The 720-combination
  GameCube regression and 11 safety tests also passed. Live files and hashes
  verified on the local test device. The user confirmed the current gifts working.
- **Blink 10th Anniversary Gifts:** 24 distinct recipes across 23 species,
  including Fly/standard Pikachu, grouping regional campaign duplicates. All
  level 70, non-shiny, no held item, BLINK identity and protected Commit.
  Automated checks passed 2,880 recipe/layout/game combinations and 120
  protected commits across all five games, plus forced shiny rejection and
  controller menu routing. Original fixture saves were preserved. Live files
  and hashes verified on the local test device. The user confirmed the current gifts working.
- **Blink PCNY Adult Gifts:** all 48 distinct recipes from the 50-entry reference
  catalog, grouping two duplicate recipes. Alternate levels/moves are labeled;
  original twelve options retain their order. BLINK identity, no held item,
  non-shiny generation and protected Commit. Automated checks passed 5,760
  recipe/layout/game combinations and 240 protected commits across all five
  qualified games, including forced shiny rejection and menu routing. Original
  fixture saves remained unchanged. Live installation and file hashes verified
  on the local test device. The user confirmed the current gifts working. See the
  complete PCNY checklist.
  These confirmations are local-device reports, not exhaustive per-game matrices.
- **Blink GameCube Gifts:** six generated reward equivalents: Pikachu, Ageto
  Celebi, Ho-Oh, and the three XD starters. Automated validation passed 720
  gift/layout/game combinations and 30 protected commits. The user confirmed all
  six gifts and saving working on the local test device. Existing preview and
  backup protections apply.
- **Blink native Gen III island events:** Emerald Eon Ticket (Southern Island),
  MysticTicket (Navel Rock), AuroraTicket (Birth Island), and Old Sea Map (Faraway
  Island). Qualified English FireRed/LeafGreen revision 1 supports MysticTicket
  and AuroraTicket. Qualified English Ruby/Sapphire revision 2 also supports
  Eon Ticket; the user confirmed both native encounters working. Normal postgame travel
  requirements remain intact.
- **Enable and Replay:** isolated preparation, explicit Commit, verified original
  backups and changed-save refusal. Replay preserves existing Pokemon and resets
  only the selected island event; MysticTicket resets both island encounters.
  Southern Island replay preserves the normal roaming Pokemon. Old Sea Map is
  labeled as an expanded English experience of a Japanese-only distribution.
- **Normal event menu:** Blink → Local Transfer → Gen 3 → Gen 3 Island Events;
  no development marker is required in the next image.
- **Blink save protection:** copies, swaps and generation conversions verify their
  source/destination fingerprints during preparation and before commit, with a
  second check after backups. Missing fingerprints require fresh preparation.
- **Bdex database recovery:** SQLite can recover an interrupted transaction before
  the usual database-integrity and snapshot checks; the exclusive writer lock and
  read-only backup/browser access remain in place.
- **Safer boot-time updates:** write/remount checks and destination verification;
  failure stops before success/cleanup/reboot and retains the package and log.
  Required initramfs comparison utilities are enabled. This still uses in-place
  replacement and does not add A/B slots; the first installation runs the old
  installed updater.
- **Bounded suspend diagnostics:** retain 20 previous successful cycles and 10
  failed/incomplete cycles plus the active cycle, without changing sleep behavior.
- **Updated Bdex artwork:** latest image for Tools, the browser viewer and docs.
- **Documentation and regression coverage:** safety-review implementation notes,
  updated native-event plan and recorded local-device results.

Validation: the user reported all six Emerald/LeafGreen event paths working and
confirmed a completed-event replay. FireRed has automated coverage only. Event
checks include 280 game/event/rotation/action combinations, exact mutation bounds,
native-reader validation, ZIP ROMs and protected UI Cancel/Commit; the normal-menu
entry is also tested. Six on-device prepared-save checks and two story-refusal
checks passed without changing the source saves. The safety fixes have host
regressions; the rebuilt image subsequently passed the reported local-device checklist above.

See [event implementation and testing](BUTTERFLY_LINK_GEN3_EVENTS_PLAN.md) and
[safety fixes](CODE_REVIEW_FIXES_20261020.md).

## v1.2.0 stable release

- Public version **v1.2.0**, updater build **20261018**, Miyoo Flip V2.
- Exact image: locally rebuilt R4 from source `8eecb5e28c620b2076eff1ff52de67653bbc3c8c`. Subsequent release documentation does not change its bytes.
- Adds opt-in cross-card Save Backup, Bdex Gen 1–3 collections, read-only browser access, sprite refresh/repair, new Bdex artwork and Blink display naming.
- All 668 package steps, GPT/FAT/ext4, image/update consistency, source/artwork/service checks and full card read-back passed.
- User approved the final image after testing on the local test device. All 12 ordinary test-save backups matched their originals with zero errors.
- Earlier feature regression checks passed: 75 Bdex, 13 Save Backup, 7 web viewer and 2 refresh checks, plus a real-systemd recurring-timer lifecycle test. These supplement, rather than replace, final-image device testing.
- Automatic backups and the browser viewer remain off by default. Bdex databases need separate backups; save states are excluded from ordinary Save Backup.
- Unfinished Gen III island-event prototypes remain excluded. Supported ROM profiles and inherited suspend/USB limitations remain documented.
- See [release notes](RELEASE_NOTES_v1.2.0.md), [Bdex](BDEX.md), [Save Backup](SAVE_BACKUPS.md) and [known issues](KNOWN_ISSUES.md).

## v1.1.0 stable release

- Public version **v1.1.0**, updater build **20261016**, Miyoo Flip V2 only.
- Exact tested image built from `7c3d4c994725ee1d71ab85f039cfac97251494cf`.
  Release commits update documentation/packaging records without rebuilding.
- Includes deep lid sleep, charging LEDs and charger-wake retry; persistent sleep
  toggle; ROM-derived inspector names, GB/GBC ZIP support, sharp HDMI text;
  39 Gen III egg recipes and five direct gifts; updated Tools artwork.
- All 668 package steps, GPT/FAT/ext4, image/payload checks and full card read-back
  passed. User approved long-term testing on the local test device. Three sleep
  cycles passed both-card read/write probes; overnight sleep lasted 8h58m.
- Wi-Fi transition/regulatory and isolated display diagnostics remain tracked.
  Gen III island events and rear USB keyboard support remain unqualified.
- See [v1.1.0 release notes](RELEASE_NOTES_v1.1.0.md),
  [Known issues](KNOWN_ISSUES.md), and [How to update](UPDATES.md#how-to-update).

## v1.0.3 stable release

- Public version `v1.0.3`; updater identity `20261010`; Miyoo Flip V2 only.
  Embedded build source: `29d1a8c521d26bf8d0a9d49b45d2466e96ad98f8` plus
  the captured source changes, committed without further binary changes as
  `5580326cf6`. Release source/provenance records explain that equivalence.
- Full build exited 0. GPT/FAT/ext4, image checksums, SYSTEM/KERNEL checksums,
  image/update payload equality, packaged event scripts, enabled lid service,
  save helper and frontend labels passed. Complete raw-card read-back matched.
  The user confirmed all live tests passed and authorized stable publication.
- Published as [Latest stable](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.0.3).
  All ten uploaded asset sizes/GitHub SHA-256 digests matched, and the public
  update manifest matched. `.20` on `20261007` discovered `20261010` through
  the production updater's read-only check. No download, install or reboot was
  initiated; discovery alone does not qualify a completed version-skipping update.
- Includes Gen I gifts and Stadium equivalents; Gen II Mew/Celebi, Stadium 2
  gifts, fifteen Mystery Eggs, 104 PCNY eggs and 16 shiny adult gifts; native
  Crystal Celebi and Odd Egg enable/replay; verified Gen II → III held-item
  equivalents; full-screen Save State Manager with artwork and recent states;
  optional lid timer and verified RetroArch save-before-shutdown; and illustrated
  installation/recovery explanations. Both lid settings default to Off.
- Release rechecks passed: 23 lid tests, 180 Gen I gift/save cases, 5,824 Gen II
  gift/family/box cases, 24 Odd Egg and 32 Celebi quest checks. The production
  updater accepts the narrow release archive and manifest. Original fixtures
  remain unchanged. Known Issues retains unqualified game/event combinations.
- The published updater uses only the tested SYSTEM/KERNEL payloads and their
  metadata/checksums, excluding the full build archive's extra bootloader files.
  Required working space is 2,839,361,744 bytes; recommend at least 3 GB free.
- Emulator defaults, performance tuning and battery reporting are unchanged.
  The Spruce audit is research documentation, not an emulator migration.
- [Release notes](RELEASE_NOTES_v1.0.3.md) explain the new menus and options.

## v1.0.2 stable release

- Public version `v1.0.2`; updater identity `20261008`; Miyoo Flip V2 only.
  Binary source: `4db62112ad358dc290f47c4cbe6fd157e0e6afb4`.
- Full build exited 0. Image/update consistency, checksums, GPT/FAT/ext4,
  packaged tools/artwork, frontend binary correspondence, content exclusions,
  and license manifest checks passed. All 43 frontend patches apply to clean
  source, and all 10 automated storage/formatting checks pass.
- The 32 GB test card was reflashed with both partitions confirmed unmounted
  through the host desktop disk service. Complete direct-I/O read-back SHA-256
  matched the audited image. The user boot-tested the full image, approved the
  UI, and authorized stable publication. Published as
  [Latest stable](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.0.2).
  All nine uploaded asset sizes/GitHub SHA-256 digests matched, and the public
  update manifest matched. The local test device discovered `20261008` with a read-only check;
  no device download, installation, or reboot was initiated.
- Includes SD Card Info and the Format 2nd SD Card graphical conversion using
  Blink's renderer/controls; Game Settings first and Network Settings
  second; RetroAchievements statistics-browser API gate; 30-second journal sync;
  supplied OpenBOR/EasyRPG, Quick Start, and transparent storage artwork; and
  light-blue SSH banner, final build stamps, and corrected hostname setup.
- RetroAchievements account settings remain outside Advanced Mode at
  **Settings / Start → Game Settings → RetroAchievements Settings**.
- [Release notes](RELEASE_NOTES_v1.0.2.md) and
  [SD Card Info instructions](SD_CARD_INFO.md) document these changes.
- The temporary performance tester and six completed recordings are archived
  on the PC and excluded from the build. Performance settings are unchanged.
- Quick Start, Controls Guide, System Manager, diagnostics, and recovery
  graphical conversions remain future work. The performance tester is excluded.
- This is not exhaustive emulator/peripheral validation. The local test device remains on its
  older release for a separate update test that skips the intermediate version.

## Bundled v1.0.1 maintenance release

- Published [v1.0.1](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.0.1)
  as Latest stable. All nine uploaded assets passed checksum/size verification;
  The local test device discovers build `20261007` without initiating installation.

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
deployed live on the local test device. Existing artwork links were recovered for 1,505 games and
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

The current app is **Blink**, implemented as a save-transfer tool.
The old link-cable/netplay launcher has been removed from the installed
Blink workflow.

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

- Long Blink notices and confirmation filenames wrap to rendered
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
  converted names when opening Crystal's PC (white screen). Crystal on the local test device
  was repaired from the session backup, preserving the copied Pikachu; the
  in-game PC-open/save/exit/reopen retest passed with the prior live helper;
  the same code is now in the current image.
- Regression test: `tests/butterflyos-gen2-box-persistence-test.py`. All 48
  cases pass on the workstation and on the local test device using private fixtures; the old
  helper fails the same test. It checks both SRAM banks and simulates Continue's
  banked-box load and validates occupied-box name terminators. The real
  Crystal PC-open/save/exit/reopen retest has also passed on the live helper.
- Live helper SHA-256:
  `25b60281206c9c9403f18ec56920baba70a16d858ab103849d73fb4089b6a06e`.
  It is bind-mounted over `/usr/bin/butterflyos-save-trade` on .20 and the local test device.
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

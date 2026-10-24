# Current build and test status

Reviewed: 2026-10-23.

## Published v1.5.0: build 20261023

- Runtime source `404c29e3af7da12d5552bfa63ce9f696a76010f1`, onboarding
  package 2.6.57. All 669 image-package steps passed, including the kernel
  rebuild for the 2/255 brightness floor. Delivered files match the source;
  the boot DTB is byte-identical to the working live 2/255 test candidate.
- Image/update checksums, filesystem checks, source identity, tool/backend
  payloads and full direct SD read-back passed. Raw-image SHA-256:
  `4952f8d9ccc83d2702bb533e4fa3426ff62956f2e028309cb0ad412c595cb9af`.
  The user reported all fresh-image checks passed on the local test device,
  including controls, brightness and the original Blink regression scenario.
- Private OTA qualification passed from build 20261022 to 20261023 using
  the installed updater's validation/staging and real reboot installer.
  Only network requests were redirected through a temporary private source;
  public GitHub release discovery was not exercised or changed.
- After OTA, KERNEL, SYSTEM and all four checked tool/UI files exactly match
  this candidate. The live backlight floor is 2/255, staging/downloads are
  cleaned up, the normal updater is restored, and no services failed.
- Before/after library inventories match: 41,813 file names/sizes/links and
  all 31 ordinary save-file hashes. Six other saved configuration/database
  files retain their hashes. EmulationStation's only changed settings field
  is LastSystem (Tools to Favorites); user preferences are preserved.
- Private verification, flash reports and the manual checklist are in
  `.cache/test-build-20261023-404c29e3af/`; OTA inventory, backups and results
  are in `.cache/ota-private-20261023/`.
- Published as [v1.5.0](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.5.0),
  Latest stable, after all eight uploaded asset sizes and GitHub SHA-256
  digests matched the verified local files. Public production-updater discovery
  returned build 20261023 and the matching official release manifest; this
  publication check did not initiate another download or installation.

## Included in v1.5.0: Blink review and controller follow-up

- Blink, Bdex and Bslap now use mapped SDL input for their native menus.
  Ignore the duplicate raw joystick events emitted for mapped controllers;
  one physical A/B press must produce one action. Ignore keyboard repeats
  across screen transitions. Blink A/B behavior passed live user testing.
- Load saved SDL controller mappings before applying the two built-in Flip
  GUID overrides. Controllers must currently be connected before opening
  these tools; connecting another controller while a tool is open requires
  reopening it. External-controller testing remains a separate hardware check.
- Gift-ROM matching skips an unreadable candidate and continues searching
  for the exact matching decompressed ROM digest. A damaged ZIP previously
  hid a valid matching ROM later in the list; that failure was reproduced.
- The Blink refresh row displays **Sprites** on the left and **Refresh Sprites**
  on the right, preserving its existing internal action and routing.
- Review checks passed: eight SDL input/mapping/label regressions, four
  blank-text/save-label regressions, two Bdex refresh regressions, 48 raw/ZIP
  gift comparisons, invalid-ZIP matching, and forced damaged-sprite repair
  across Gen 1/2/3. Refresh opens no saves; fixture ROM hashes stayed unchanged.
- These follow-up fixes are included in onboarding package 2.6.57 and the
  qualified local image above.

## Included in v1.5.0: lower minimum brightness

- Keep the menu minimum at 5%, but lower its backlight lookup-table value
  from PWM 3/255 to 2/255. The 800 Hz frequency and 20 ms startup delay stay
  unchanged; index zero still turns the backlight off.
- The live device-tree test confirmed 2/255 in the running kernel. The user
  reported successful dimming, lid reopening and full power-off/power-on
  checks on the local test device. Testing 1/255 left the screen dark, so
  2/255 is the tested floor for this device.
- Restored the 2/255 boot table and normal brightness after the 1/255 test.
  The rebuilt image and private OTA installation both delivered the 2/255
  table; the user confirmed brightness operation on the fresh image.

## Superseded initial candidate: build 20261023

- Built the complete Flip image from runtime source
  `99717919eab6c5dd5964606f33dbd8ad044b95c8`, onboarding package 2.6.53.
  All 669 main-image package steps passed after rebuilding the required
  compatibility packages. This candidate is not a published stable release.
- Delivered-image verification passed: flash/update checksums, complete gzip
  integrity, GPT CRCs, read-only FAT/ext4 checks, matching KERNEL/SYSTEM payloads,
  embedded source commit, exact Blink/Bdex files and encounter metadata,
  controller/repaint fixes, Bslap backend hashes and Tools visibility, and
  exclusion of ROM/save filenames. Normal RetroArch32/gpSP hashes are unchanged.
- Flashed the backed-up 32 GB development card and verified all 2,198,863,872
  image bytes by reading the card back. Raw-image SHA-256:
  `252c934bfb06ea1df70120beaf4bde25aafe73f4ba5caff64a8add522549850c`.
- Private build/flash reports and the previous card files are in
  `.cache/bdex-build-20261023/`. This initial image failed physical-control
  testing and was superseded by the qualified candidate documented above.

## Included in v1.5.0: Bdex Gen 1 encounter lookup

- Gen 1 species now offer Stored copies / Where to find, including species
  with no stored copies. Choose a qualified English retail Red, Blue or Yellow
  ROM (raw or single-ROM ZIP) to read grass/cave and Surfing locations/levels.
- Gen 2/3 navigation stays unchanged. Fishing, gifts, trades, evolutions and
  special encounters are explicitly excluded; no-result text avoids claiming
  that a species cannot be obtained. No live game/progress tracking yet.
- Encounter reader validates the entire map-pointer alias structure and ROM
  content checksum before decoding; no filenames used as proof of game/version.
- Seven encounter/navigation/control tests pass, including all three private original
  ROM ZIPs and corrupt/ambiguous table rejection. Inspector and collection
  regressions also pass. Package 2.6.53 includes reader and layout metadata.
- Temporarily installed on the local test device and Bdex reopened. On-device
  decoding passed for all three original ZIPs; all seven checked Gen 1 saves
  and collection databases retained their hashes. The user confirmed the
  corrected controls and location lookup working on the local test device.
- Live follow-up: Gen 1 could show a black screen while its process remained
  alive. Clear the render target explicitly and request a collection redraw
  after SDL window exposure/resize events. Verified the actual Wayland output
  with before/after screenshots; the fixed display shows the collection and
  sprites, and redraw activity settles. Window-event regression test passes.
- Follow-up physical-button report: original Flip SDL pad mappings used the
  opposite A/B layout. Tool-local overrides for the two built-in pad GUIDs now
  use physical A to confirm and B to cancel, for the keyboard bridge and native
  SDL input. Shared controller databases/emulator mappings are unchanged;
  external pad mappings are preserved. The user confirmed the live correction.
- Included in local test candidate 20261023; not published yet.

## Included in v1.5.0: Bdex graphical inspector

- Summary, Stats and Details pages retain all previous inspector fields/history
  while adding the ROM-derived sprite, radar graph and numeric stat values.
  L/R or Left/Right changes pages; Up/Down changes graph mode or scrolls Details.
- Read-only calculations distinguish Gen 1's five stats, Gen 2's shared Special
  DV/stat experience, and Gen 3 IVs/EVs/nature/Shedinja. Graphs label their mode
  and scale; current-level stat ceilings are shared rather than per-Pokémon.
- GB/GBC cache version 8 and Gen 3 version 6 include ROM-derived base stats;
  older caches offer explicit ROM refresh without reimporting Pokémon. No base
  stat tables, sprites, ROMs or user records are bundled in source.
- Known-value stat/rounding and page-navigation tests passed. Existing Bdex
  tests passed (37 safety tests with three private-fixture tests skipped,
  two refresh tests, seven viewer tests). Forced cache rebuild/repair regressions
  passed for all three generations. Actual stored Gen 1/2/3 Pokémon were rendered
  at 640×480 and 1280×960; all three collection database hashes stayed unchanged.
- The inspector is installed live on the local test device. Training mode is
  explicitly labeled as training counters, not battle stats. The user accepted
  the inspector after live testing. First included in onboarding package 2.6.52;
  retained in package 2.6.53 and local test candidate 20261023. Not published yet.

## Included in v1.5.0: Blink preview and GB/GBC ZIP handling

- Add **Refresh Sprites** to Blink's main menu. Choose a generation and a
  checksum-qualified English ROM, then force a rebuild of the shared sprite/name
  cache. Raw and single-ROM ZIP inputs use existing readers. No save is required
  or opened; missing ROMs and cancellation return safely.
  Menu routing and forced damaged-sprite repairs passed for all three
  generations. The live action rebuilt all 151 Blue sprites and names from
  the original ZIP on the local test device; its ROM and all 16 adjacent saves
  retained their checksums.
- Show trainer names first and retain full wrapped filenames in gift-save
  selection. Long original ROM filenames previously hid trainer identities
  behind a 58-character truncation, making personal saves hard to distinguish
  from development saves. Gen 1 local selection also puts the trainer first.
- Skip empty text lines in the shared SDL renderer. A Gen 1 party preview with
  no optional level/nature text previously exited to the dialog fallback with
  `Text has zero width`. The old failure and corrected path were reproduced
  using the local test device's SDL libraries, without changing saves.
- Hash decompressed GB/GBC ROM contents for gift/cache matching. Gen 1/2 gift
  generation and Crystal event validation now use the existing bounded,
  single-ROM ZIP reader, retaining exact retail ROM checksum qualification.
  The previous paths hashed/read the ZIP container and rejected valid games.
- Match gift ROMs against the cache's `rom_content_sha256`, with a fallback
  for older manifests. GB/GBC ZIP caches retain a container hash for their
  directory identity; comparing that with the ROM-content hash wrongly
  reported a missing match after a successful sprite-cache rebuild.
  The local test device's personal Blue save passed the full original-ZIP,
  native gift preparation, sprite-preview and Cancel path with its original
  save checksum unchanged. Six raw/ZIP routing regressions also cover this
  distinction through the Gen 1/2 gift menus.
- Three blank-text regressions and 48 raw/ZIP gift equivalence comparisons
  passed, along with six ROM digest checks, modified-ROM refusals, Crystal ROM
  qualification and ambiguous-ZIP refusal. The 11 Bslap regressions passed.
- Live checks on the local test device generated all 45 Gen 1 game/gift
  combinations from the original ZIPs, qualified Gen 2 ZIPs, staged and discarded
  a gift into a populated PC box, and inspected Crystal events through its ZIP.
  The inspected source saves remained unchanged.
- Fixes introduced in onboarding package 2.6.51 are retained in 2.6.53 and local test candidate 20261023.
  Live test patches use temporary bind mounts and do not survive a reboot.
  These changes are not in the published v1.4.0 image.

## Stable v1.4.0, build 20261022: Bslap

The user reported all tests passed on the previous candidate with the live
frontend fix. Rebuilt the complete image from runtime commit
`a6c1655968e3a02de57cb8e0825b76fab5d29ce8`, onboarding package 2.6.50.
All 669 package steps completed. The Bslap normal-Tools allowlist patch is now
compiled into the delivered frontend; Advanced Mode and the live hotfix are not
required. Bslap appears alongside Blink and Bdex. The Gen 3-only room-exit
limitation remains documented.

Delivered-image checks passed: gzip/SHA-256 integrity, GPT CRCs, read-only FAT/ext4
checks, matching flash/update KERNEL and SYSTEM, source commit, all four backend
hashes, exact Bslap scripts/module/icon, generation order, Gen 3-only warning,
unchanged normal RetroArch32/gpSP, ROM/save filename exclusion, and exact rebuilt
frontend package with the Bslap visibility fix.

Flash image: `ROCKNIX-RK3566.aarch64-20261022-Miyoo_Flip_V2.img.gz`.
SHA-256: `e8897c0bf99590117c63bafb8d6c917c374d7d02889c30dfbc165c50446f069d`.
Update archive: `ROCKNIX-RK3566.aarch64-20261022.tar`.
SHA-256: `3109b617d3dba28fbf6a094d261d8bd4f636bd637dbf47b9c2e9e723a30738d9`.

The 32 GB development card was backed up, flashed, flushed and completely
read-back verified against this corrected image. The private backup includes
its test ROMs, twelve saves and available Bslap session data.
**Fresh-image device testing passed.** The user confirmed the corrected flashed
image passes testing, including the normal-Tools visibility check that motivated
this rebuild. The live frontend hotfix is not needed on this image.
Published as **[v1.4.0](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.4.0)**, Latest stable. All eight uploaded asset sizes and GitHub SHA-256 digests
match the verified local files. Public latest-release discovery and the downloaded
updater manifest advertise build **20261022**. The narrow published updater archive
repackages the tested KERNEL/SYSTEM unchanged; its SHA-256 is
`ef6ab714171357eea747a1ca73f285016f26e55e5fc3dac6669608d4a1e62771`.
Release documentation and the merge commit do not change the delivered image.
See [Bslap](BSLAP.md) and [v1.4.0 release notes](RELEASE_NOTES_v1.4.0.md).

## Stable release v1.3.0, build 20261020 — changes since v1.2.0

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

**Published as [v1.3.0](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.3.0), Latest stable.**
All seven uploaded asset sizes and GitHub SHA-256 digests match the local
verified files. Public latest-release discovery and the downloaded updater
manifest were checked; the manifest advertises build **20261020**.

**Local-device checklist passed.** The user confirmed the rebuilt
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

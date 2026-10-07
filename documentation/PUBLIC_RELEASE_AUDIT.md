# ButterflyOS public-release audit

This records technical release checks. It is not legal advice.

The dated sections below apply only to their recorded images. Later rebuilds
require fresh checks; none of these records proves universal compatibility.

## October 6, 2026 maintenance release candidate: v1.0.2

- Candidate approved by the user after boot-testing the full image. GitHub
  draft upload and asset verification are in progress; publication is authorized.
- Binary source: `4db62112ad358dc290f47c4cbe6fd157e0e6afb4`.
- Build: `CUSTOM_VERSION=20261008 make docker-RK3566-Miyoo-Flip-V2-aarch64`;
  exit 0. EmulationStation was explicitly cleaned before the full build.
- Image: `ButterflyOS-v1.0.2-Miyoo-Flip-V2.img.gz`, 1271244940 bytes.
  SHA-256: `0eca31c520928abe97d1d157ec59d1bd2f0a5579830154343be5cff574f8c2f4`.
- Update: `ButterflyOS-Miyoo-Flip-V2-20261008.tar`, 1285447680 bytes.
  SHA-256: `a605022a596aba3f2356bfee7f1b29b24f7c00b9a1876e8dec04d37e3b0e077c`.
- Image SHA-256/gzip, GPT/FAT/ext4, first-boot scaffold and resize marker,
  SYSTEM/KERNEL MD5s, image/update payload equality, archive membership,
  manifest identity/sizes/checksum, and content filename exclusions passed.
- Packaged SD Card Info reporter/UI, shared graphical helper, Format 2nd SD
  Card launcher/backend/UI, and all new artwork match committed source bytes.
  Journal interval is 30 seconds; SSH banner uses explicit light-blue RGB with
  the final updater identity. Hostname initialization matches corrected source.
- Installed EmulationStation matches the rebuilt package. Source verification
  confirms the Settings order, normal SD Card Info visibility, normal-mode
  RetroAchievements account settings, and stats-browser API capability gate.
- PortMaster support, 512-sample PipeWire defaults, and 86 notice/license files
  remain present. The package license manifest has no unresolved definitions.
- All 43 frontend patches applied to clean source; 10 automated storage and
  mocked-formatting safety checks passed. No real disk is touched by those tests.
- Final flash verification: the confirmed-unmounted test card matched all
  2198863872 raw-image bytes using direct-I/O SHA-256:
  `d0e3efc9f978ff8047cf2725e9655b847070deba28c8647eb7382c04125a7950`.
  The user approved the full image after boot testing. This does not establish
  exhaustive emulator/peripheral or version-skipping-update coverage.
- Updater working space: 2839320784 bytes; recommend at least 3 GB free on
  the OS card. The temporary performance tester is excluded; no tuning changed.
- Uploaded audit records retain the exact binary source; later documentation
  commits do not change that source identity.

## October 5, 2026 bundled maintenance release: v1.0.1

- Published as Latest stable, with no draft/prerelease flag. All nine uploaded
  asset sizes and GitHub SHA-256 digests matched local verified files. The public
  update manifest matched, and `.17` returned `20261007` from its update check.
  No device download, installation, or reboot was initiated.

- Binary source: `886a8696d438ef9ec428de72c68ca48e63a51418`; updater build ID `20261007`.
- Build: `CUSTOM_VERSION=20261007 make docker-RK3566-Miyoo-Flip-V2-aarch64`.
  Exit 0; all 668 package steps passed. EmulationStation and the system package
  were cleaned and rebuilt to include the menu and SSH branding changes.
- Image: `ButterflyOS-v1.0.1-Miyoo-Flip-V2.img.gz`, 1265376106 bytes.
  SHA-256: `76e51ebb54454a212025b8cc852630ff58d6ae64f48ccb1db861eb27dc0137a2`.
- Update: `ButterflyOS-Miyoo-Flip-V2-20261007.tar`, 1279580160 bytes.
  SHA-256: `4abae08fd3d435ec974435abac7e411ac409ba49dd8e6bffa41183371927909d`.
- Image SHA-256, gzip integrity, GPT, FAT, and ext4 checks passed. STORAGE has
  the empty first-boot scaffold and resize marker. Image and narrow update
  contain matching SYSTEM/KERNEL and verified MD5s; manifest identity, sizes,
  archive members, and SHA-256 passed.
- Packaged PipeWire defaults match the committed 512-sample default/min/max.
  SSH MOTD matches the cyan ButterflyOS wordmark and retains build details.
- RetroAchievements normal-mode settings and launcher option names are present
  in rebuilt source; the installed EmulationStation matches that rebuilt package.
  Frontend browser/indexing retains its API credential requirement.
- PortMaster launcher/runtime and 86 license/notice files are retained.
  Filename exclusions found no ROMs, saves, personal BIOS collections, private
  SSH identities, known_hosts, authorized keys, or device backups. The package
  license manifest has no unresolved target package definitions.
- Updater working space: 2827579600 bytes; recommend at least
  3 GB free on the OS card.
- Hardware limits: the user confirmed live GB/GBA/NES speed after the audio fix.
  This exact full image has not been installed on hardware. RetroAchievements
  account login/unlocking and Bluetooth/PortMaster audio regression checks remain
  tester tasks; host checks are not represented as device qualification.
- Release assets include build-verification.json and build-environment.txt.
  Later documentation commits do not change the recorded binary source.

## October 5, 2026 superseded local v1.0.1 candidate

This audio-only candidate was not published. It predates the RetroAchievements
menu and SSH banner changes; its hashes do not identify the bundled release.

- Binary source: `96666f1199eddda88f0db52db32ed0cfd5df3835`; updater build ID `20261007`.
- Build: `CUSTOM_VERSION=20261007 make docker-RK3566-Miyoo-Flip-V2-aarch64`.
  Exit 0; all 668 package steps completed using existing source/package caches.
- Image: `ButterflyOS-v1.0.1-Miyoo-Flip-V2.img.gz`, 1265374886 bytes.
  SHA-256: `ca90b4c57267013d842f99b75a57bcee77d9a44613a62e66844abd142e9ed4d0`.
- Update: `ButterflyOS-Miyoo-Flip-V2-20261007.tar`, 1279580160 bytes.
  SHA-256: `67b032dbcadc8d4b342115366416ce598c0b8ebbc4c7a936b2e2c4cb2151125b`.
- Generated checksum, gzip integrity, GPT, FAT, and ext4 checks passed.
  STORAGE retains only the empty first-boot scaffold and resize marker.
- Image and narrow update contain matching SYSTEM/KERNEL and embedded MD5s.
  Update manifest identity, sizes, members, and SHA-256 were verified.
- The exact SYSTEM contains the corrected 512-sample default/minimum/maximum
  PipeWire setting, identical to the committed source. PortMaster launcher
  and runtime assets and 86 ButterflyOS license/notice files are retained.
- Filename exclusions found no ROMs, saves, personal BIOS directory, private
  SSH identities, authorized keys, known_hosts, or device backups.
- License manifest regenerated from all target packages with no unresolved
  package definitions. The packaged EmulationStation binary is unchanged
  from v1.0.0; no new scraper credential integration was introduced.
- Required updater working space: 2827579600 bytes;
  continue recommending at least 3 GB free on the OS card.
- Device qualification: live GB measured around 47 FPS before the fix and
  60 FPS afterward. The user confirmed GB, GBA, and NES work with the fix.
  Both device configurations were validated; .17 was subsequently reverted
  at the user's request to test the published Tools installer. The new full
  image has passed host checks but has not yet been installed on hardware.
- Full check records are supplied as build-verification.json. The release
  tag includes later issue-template/hotfix instruction and audit documentation
  commits; the recorded binary source above remains unchanged.

## October 4, 2026 first stable release: v1.0.0

- Binary source: `efcc19513baa5ea2b756b619fe81196873e8aebc`. The release tag also includes later
  final audit documentation; the recorded binary source remains unchanged.
- Device: Miyoo Flip V2 only; updater identity: `20261006`.
- Build: `CUSTOM_VERSION=20261006 make docker-RK3566-Miyoo-Flip-V2-aarch64`.
  Exit 0; all 668 package steps completed. Existing package/source caches were
  reused; clean-checkout and bit-for-bit reproducibility were not retested.
- Container digest: `sha256:43dac3d6d7e59801b7797bf06b970c7c056d97185d19cb909d502ce8ded754ed`.
- Image: `ButterflyOS-v1.0.0-Miyoo-Flip-V2.img.gz`, 1265374844 bytes.
  SHA-256: `8b167f25ebba69ff24e5904f4c99068b6b5eb2b357905905a24aabc3d661ecaa`.
- Update: `ButterflyOS-Miyoo-Flip-V2-20261006.tar`, 1279580160 bytes.
  SHA-256: `a223780485543e05d8a6fb4f6aaf0d6e0c6e582181a2167b30b2fe30dbfdbb66`.
- Generated image checksum, gzip integrity, GPT, FAT, and ext4 checks passed.
  GPT verification reported no problems. STORAGE contains only `lost+found`
  and `.please_resize_me` in addition to directory entries.
- Image and update contain matching SYSTEM and KERNEL. Embedded MD5 records,
  update manifest, device/version identity, archive members, sizes, and SHA-256
  validation passed using the current updater's verification routines.
- Extracted SYSTEM has the exact source build ID, current updater and theme,
  corrected X/Y hints, PortMaster runtime/launcher, matching Ports/Tools ship
  icon, and all eight new system illustrations. The `pce-cd` alias resolves.
- Packaged EmulationStation includes ButterflyOS update/restart labels and
  the device marker; the recorded source includes warning/reboot patches 048/049.
- Mali g29p1 vendor-library SHA-256 matches the upstream build input:
  `605e3a5caf1be62bb48d97b1168434257355d56db5e3be9b515cfa742c173118`. The packaged EULA is identical to its build input.
- The target manifest resolves all 549 packages. The image retains 86
  ButterflyOS license/notice files. Previously reviewed non-commercial cores
  remain; Art Book Next, ZeroTier, and the DraStic program remain excluded.
- Filename/content scans found no game ROMs, proprietary console BIOS files,
  test media, private SSH keys, Wi-Fi connection profiles, device-specific
  preloader images/recovery archives, or plaintext private scraper credentials.
  The two inherited Anbernic RG DS DraStic stop/continue shell helpers are not
  the DraStic program. Markdown documentation is not Mega Drive ROM content.
- Online update working-space requirement: 2827579600 bytes
  (about 2.83 GB); recommend at least 3 GB free on the OS card.
- Hardware baseline: the user completed individual checks of the 30 populated
  system/arcade groups, verified PortMaster offered-game installation/play,
  and reported no further UI issues. Earlier v0.2.3/v0.2.4 OTA installations
  succeeded on the prepared Flip V2. These observations apply to the preceding
  device build. The exact v1.0.0 image has passed host-side checks; its new
  warning/reboot behavior and artwork still need an installed-device check.

Publication: v1.0.0 was published as Latest without draft/prerelease flags.
All nine release asset sizes and GitHub SHA-256 digests matched local files;
the downloaded public manifest matched. The prepared .20 device discovered
`20261006`. No download or installation was initiated during discovery testing.
Upload verification is recorded with the release assets. Stable is the
maintainer's designation for the documented Flip V2 scope, not universal game
compatibility or an LTS support promise.

## October 2, 2026 public Alpha 2 artifact

- Image source: `39bb3a803bd481b7a610cf2b19509b2c13d39891`.
- Compressed SHA-256: `24eb2a762b55fb6aae77caf49c5450f3b3f1bf874b5cbc01016469dc0ab3aede`.
- All 668 main-image steps passed. Gzip integrity and checksum checks passed.
- The exact compressed image was decompressed; read-only FAT and ext4 checks
  passed. STORAGE contains only `lost+found` and `.please_resize_me`.
- SYSTEM extracted from that image matches its embedded MD5 record.
- The installed Mali vendor binary matches its upstream build input byte-for-byte;
  the full included EULA also matches. Wrapper modifications do not change it.
- The SYSTEM contains 86 ButterflyOS license/notice files. The package inventory
  was regenerated from this build's completed job log.
- No ROMs, save files, test music/video, SSH host keys, private credential JSON,
  device recovery backups, DraStic binary, or ZeroTier executable were found in
  the filesystem filename scan. Developer credentials are deliberately included
  in obfuscated client form; this is not cryptographic secrecy.
- The user confirmed this flashed image works. The preceding image passed
  scraper/artwork testing; this rebuild's packaged default selects ScreenScraper.
- The final SD read-back check was cancelled; it is not claimed as passed.
- Historical install/restore and broader gameplay tests remain the qualification
  baseline; a complete two-device suite was not repeated after this default-only
  change. This release is labelled an alpha, not stable.

## Alpha 2 candidate policy

- Target only `RK3566/Miyoo_Flip_V2`.
- If the ROCKNIX Mali stack is included, retain its complete EULA and use the
  upstream mapping fix without modifying the vendor blob.
- Do not bundle DraStic without independently verified redistribution terms.
- Retain open-source melonDS and DeSmuME Nintendo DS options.
- Never bundle games, proprietary console BIOS files, user credentials, or
  device-specific preloader/recovery data.
- Publish images as release assets, never as files tracked in Git.

## September 11, 2026 preliminary image inspection

The Panfrost qualification image was decompressed and both partitions were
inspected before preparation of the final clean Alpha 2 build.

- GPT contained a `BUTTERFLYOS` FAT system partition and a blank ext4 storage
  partition.
- Storage contained only `lost+found` and `.please_resize_me`.
- `SYSTEM.md5` matched the extracted SquashFS `SYSTEM` file.
- Setup contained the expected device-local installer, preloader patcher,
  manifests, artwork, and BaseOS license.
- No game/BIOS/test-media files, Wi-Fi profiles, SSH host/private keys,
  personal network names, test-device IP addresses, or preloader backups were
  found.
- No proprietary `libmali` userspace library or SONAME was found. Panfrost
  Mesa libraries and the open kernel driver/firmware were present.

## September 11, 2026 final Alpha 2 image inspection

The exact image built from commit `c9d2f0b` was decompressed and audited:

- Image SHA-256: `ff793369e77b7c41de57a1b53003494a8304ec6a1c64871a6478db21a6e294f1`.
- FAT and ext4 filesystem checks completed without errors.
- The storage filesystem contained only `lost+found` and
  `.please_resize_me`, as expected for first-boot expansion.
- No user games, test media, Wi-Fi credentials, SSH private/host keys,
  personal identifiers, test IP addresses, or device backups were found.
- No `libmali` file or linkage was found.
- DraStic is absent from the package manifest and emulator configuration.
  Two generic ROCKNIX suspend-helper filenames for the unrelated Anbernic RG
  DS mention DraStic, but contain no DraStic program or library.
- The generated package-license inventory resolved all 549 target packages to
  build metadata; this does not replace the manual license review below.

That candidate passed a Miyoo Flip V2 hardware smoke test, including Nintendo
DS gameplay, built-in and Bluetooth controls, audio, quick menu, save/load
state, exit hotkey, and relaunch using the open-source melonDS DS default.

## September 11, 2026 post-review Alpha 2 image inspection

The exact image built from commit `2a294a9` incorporates the package review,
removals, and embedded notices:

- Compressed image SHA-256:
  `a3304b1925e277ddde990bdc652f05ec6bcdc8dc80cd9244ccb0328f39696927`.
- All 251 compatibility-build and 666 main-image steps completed with zero
  failures.
- FAT and ext4 filesystem checks passed, `SYSTEM.md5` matched, the FAT label
  remained `BUTTERFLYOS`, and storage remained pristine.
- Art Book Next, ZeroTier, libmali, DraStic, private keys, Wi-Fi profiles, and
  user content were absent from the exact filesystem inventory.
- The image contains the ButterflyOS theme and 86 release policy, common
  license, and exact component-notice files under
  `/usr/share/butterflyos/licenses`.
- The refreshed manifest contains 546 target packages and resolves every one
  to build metadata.

This exact post-review image requires one final focused hardware smoke test
before tagging and publication.

## September 12, 2026 fail-safe resize baseline

The post-review image was rebuilt after replacing the target-incompatible
`sgdisk` first-boot path with a fail-closed GNU Parted workflow:

- Exact source commit: `f2ea99b`.
- Image: `ROCKNIX-RK3566.aarch64-20260912-Miyoo_Flip_V2.img.gz`.
- Compressed image SHA-256:
  `39a3b8ba58992e9c3f7894c93bdfbbb6f8a6dce8ed411821ebc769ae1f19fe06`.
- All 666 main-image package stages completed with zero failures.
- The pristine FAT and ext4 filesystems passed read-only checks, `SYSTEM.md5`
  matched, and a complete SD-card readback matched the decompressed image.
- The embedded resize script was extracted independently and confirmed to
  check both kernel-reported and on-disk GPT partition sizes before touching
  the ext4 filesystem, retaining its retry marker until successful completion.
- Physical first boot repaired the backup GPT, expanded the storage partition
  and filesystem to 27.6 GiB, removed the retry marker only after success, and
  left zero failed systemd units.
- Wi-Fi, SSH, Bluetooth controls and audio, built-in controls and hotkeys,
  controller fallback, HDMI, media, games, and open-source melonDS Nintendo DS
  operation passed physical testing. Saturn remains the documented Panfrost
  exception.

The recovery-export source change intentionally makes this a tested baseline,
not the final publishable binary. The final Alpha 2 image requires a new exact
commit, checksum, filesystem/privacy scan, and focused hardware test.

## September 12, 2026 final recovery-export candidate

The exact image built from commit
`b7d83bb5c8e509e541587983cc8c13dbbbf7a47a` incorporates the qualified
onboarding flow and the user-facing recovery-backup export:

- Image: `ROCKNIX-RK3566.aarch64-20260912-Miyoo_Flip_V2.img.gz`.
- Compressed image SHA-256:
  `15768d411c68254e4c7d0f8363eac98e4ad9ee7b4789cd7afde2abe021f91386`.
- All 251 compatibility and 666 main-image jobs completed successfully.
- Gzip integrity and the generated SHA-256 sidecar passed.
- The FAT label is `BUTTERFLYOS`; `SYSTEM.md5` matches the extracted SYSTEM;
  and the FAT and pristine ext4 storage filesystems passed read-only checks.
- Storage contains only `lost+found` and `.please_resize_me` before first boot.
- The packaged recovery export launcher and implementation are present.
- No games, console BIOS files, test media, Wi-Fi profiles, SSH private or host
  keys, device recovery backups, or test-network identifiers were found.
- Proprietary libmali, Art Book Next, ZeroTier, and the DraStic program are
  absent. Two generic upstream suspend-helper filenames for the unrelated
  Anbernic RG DS remain but contain no DraStic program or library.
- Mesa Panfrost/Panthor drivers and the embedded ButterflyOS license and notice
  set are present.

This exact image still requires its focused physical-device smoke test before
the immutable release tag and public upload.

Its September 12 physical test passed first-boot expansion, Wi-Fi, SSH,
Bluetooth and built-in controls, game and media playback, hotkeys, HDMI video,
and normal frontend operation. That test exposed three small release fixes:
Media was hidden while empty, RetroArch audio remained routed to disconnected
HDMI, and ROCKNIX's synthetic PICO-8 `Splore.png` launcher appeared without
user content. The fixes were verified live where possible and require one final
regression build. A single post-suspend LCD line artifact cleared after an HDMI
display reinitialization, did not coincide with a Panfrost fault or timeout,
and could not be reproduced.

## September 13, 2026 final Alpha 2 regression image

The three release-test regressions were corrected and rebuilt from exact source
commit `e21bad08684982c2490435b9582ba8454e161223`:

- Image: `ROCKNIX-RK3566.aarch64-20260913-Miyoo_Flip_V2.img.gz`.
- Compressed image SHA-256:
  `0db1250f51cafa57ddcbbfac545781ecbe57c83040127dc8fc55f2c1761dee81`.
- All 251 compatibility and 666 main-image jobs completed with zero failures.
- Gzip integrity and the generated SHA-256 sidecar passed.
- The FAT volume is labeled `BUTTERFLYOS`; its embedded `SYSTEM.md5` matches
  the exact SYSTEM payload.
- The pristine ext4 storage filesystem passed read-only checking and contains
  only `lost+found` and `.please_resize_me`.
- Exact SquashFS inspection confirmed the PipeWire RetroArch default and the
  HDMI-disconnect path that disables the HDMI profile and restores the
  internal sink.
- Media is packaged to remain visible when empty. PICO-8/Fake-08 support
  remains, while the synthetic `Splore.png` autostart hook is absent.
- No games, BIOS files, test media, libmali, Art Book Next, ZeroTier, or
  DraStic program were found. Mesa Panfrost and the ButterflyOS license set are
  present.

This image requires only the focused physical regression test before tagging:
empty Media visibility, absence of the synthetic PICO tile, internal game
audio, HDMI video/audio, internal display/audio restoration after unplugging
HDMI, game relaunch audio, and normal shutdown/boot.

The physical empty-card test found that Media remained visible but the
ButterflyOS Games group anchor was filtered because its pristine storage path
did not yet exist. Creating that path live restored the intended Games card.
The source fix now exempts both `mplayer` and `games` from the empty-system
filter and passed an isolated EmulationStation rebuild. This image must not be
tagged; one replacement build and focused test are required.

## Manual license review

The generated package manifest is an inventory, not a legal conclusion.
The flagged entries were reviewed against their exact build sources. Findings,
corrections, removal impacts, and the free-release policy are recorded in
`PACKAGE_LICENSE_REVIEW_ALPHA2.md`. This technical review is not legal advice.

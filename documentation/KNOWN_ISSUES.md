# ButterflyOS known issues

Keep backups of
games, saves, BIOS files, and any device-specific recovery data.

Based on the Alpha 2/v0.2.x qualification and October 4 system-by-system,
PortMaster, and interface testing. See
[current build status](CURRENT_BUILD_STATUS.md) for the exact image and test record.
Historical checks do not qualify every game or save combination.

## Distribution licensing gate

Alpha 1 bundled vendor-derived stock and patched preloader images and therefore
remains an internal artifact. Alpha 2 removes both images. It reads, validates,
backs up, patches, and verifies the preloader from the user's own device and
retains the BaseOS-derived patcher's MIT notice.

The full device-local install and byte-exact restore round trip passed on a
second untouched Flip V2. The clean image containing the runtime-dependency
fixes then repeated the full workflow without live intervention. The Alpha 2
candidate excludes proprietary DraStic. The restored ROCKNIX Mali stack carries
its EULA and uses the upstream no-blob-modification mapping fix. Distribution
checks for the October 2 artifact and refreshed package inventory are recorded
in [the public-release audit](PUBLIC_RELEASE_AUDIT.md). The stable designation covers the documented Flip V2 scope; compatibility
still depends on the game and peripheral.

## Installation and recovery

- The complete device-local setup/restore round trip passed on the primary test
  unit and on a second previously untouched Flip V2.
- Restore uses only the exact backup captured from that specific device. It has
  no bundled or generic fallback image.
- The clean image containing commits `8e09035` and `075b3f0` passed the final
  no-intervention install/check/restore regression.
- Interrupted low-level setup may require RK3566 USB MASKROM recovery and, as a
  last resort, opening the shell to use the internal MASKROM button.
- Miyoo Flip V1 and other handheld models are unsupported.

## Hardware qualification

- Hardware and ROCKNIX fake suspend are disabled on the Flip safety baseline.
  The Suspend selector and Suspend System action are hidden so the unsafe
  `mem` mode cannot be re-enabled through the GUI. Closing the lid turns off
  only the LCD backlight; opening restores it without changing the selected
  brightness. Games, audio, networking, and the rest of the system continue
  running while closed. This favors stability and filesystem safety over
  maximum standby battery life.
- A September 15 overnight test left HDMI and power connected to a powered-off
  4K television. After returning to the handheld display, the Games interface
  became malformed and the device stopped responding to the frontend, ping,
  and SSH. A forced restart recovered it, both filesystems checked clean, and
  the issue has not yet been reproduced. The affected build kept its journal
  only in RAM, so it could not establish whether this was a DRM/GPU or broader
  kernel stall.
- The diagnostic baseline keeps a compressed journal capped at 10 MiB and
  seven days. It also records HDMI connector/EDID changes, Wi-Fi state,
  EmulationStation liveness, and whether the previous boot ended cleanly in
  `/storage/.config/system/logs/butterflyos-health.previous`.
- The September 19 stability build also reserves 256 KiB for `ramoops`. Kernel
  panic/oops and console records recovered by systemd are copied into bounded
  archives below `/storage/.config/system/logs/pstore/` on the next boot.
- Normal logging is compressed and capped at 10 MiB with seven-day retention.
  Advanced Mode exposes an opt-in **Extended Diagnostics** tool. Its one-minute
  and five-minute snapshots use two 4 MiB logs with two rotations each (about
  24 MiB maximum), do not record passwords, and remain available after the
  collector is switched off. Ramoops archival retains at most eight records.
- Large early diagnostic captures were development-only and are not intended
  for release images. Use the bounded Extended Diagnostics tool instead.
- One post-suspend test showed horizontal/vertical pixel-line corruption on the
  internal LCD. HDMI connect/disconnect reinitialized the panel and restored
  the image; logs contained no Panfrost fault or timeout, and the issue did not
  reproduce. Treat this as an open display-resume observation.
- Rumble remains unverified.
- Long-duration battery-runtime, charging, and low-battery behavior need
  controlled measurement. Battery percentage reporting was corrected during
  development testing.
- Bluetooth Player 1 fallback depends on device-disconnect detection and is not
  literally instantaneous on every controller.
- Native built-in hotkeys and the tested external/fallback handler differ in
  shoulder-button assignments. Menu capture does not learn all raw controller
  event codes; arbitrary Bluetooth controllers and four-player ordering remain
  unqualified. See [Controls](HOTKEYS.md).

## Emulation

- The restored ROCKNIX Mali stack passed rendering and gameplay checks for the
  interface, HDMI hotplug, N64, Nintendo DS, PlayStation, PSP, Dreamcast, and
  Saturn. Brief sub-second N64 stalls occurred during initial game startup and
  then smoothed out.
- Standalone YabaSanshiro ran Saturn smoothly after correcting its generated
  Flip controller map. The tested built-in and 8BitDo Xbox-mode mappings are
  now included in source and require confirmation on the final rebuild.
- Alpha 2 replaces DraStic with open-source melonDS for Nintendo DS. Its
  performance, controls, and clean exit passed physical testing;
  compatibility can still vary by game.
- Arcade games require ROM sets compatible with the selected core. A game that
  does not launch is not necessarily an emulator failure.
- Standalone emulators do not all provide RetroArch hotkeys. YabaSanshiro and
  OpenBOR support the Alpha clean-exit gesture; PPSSPP retains native behavior.
- Performance and compatibility vary for demanding N64, Dreamcast, Saturn,
  Nintendo DS, and PSP games.
- Rewind is not supported or enabled everywhere.
- Proprietary BIOS files are never included and must be supplied legally by the
  user.

## Media

- H.264/AAC at moderate 480p or 720p bitrates is the recommended video target.
- AV1 is software-decoded and demanding AV1, high-bitrate MOV, and unusual
  10-bit encodes may skip badly.
- The current audio now-playing screen is functional but remains a UI-polish
  target.
- HDMI/hotplug and media behavior passed development tests, but long-duration
  external-display use and every video codec/profile are not qualified.

## Butterfly Link

- Gen I event gifts are included from v1.0.3, with generated
  level-5 Mew, Surfing/Flying Pikachu, Dragon Rage Magikarp and Pay Day
  Fearow/Rapidash for verified English Red/Blue/Yellow ROM
  revisions. Save reload, box persistence, full-box refusal, backups and cancel
  checks pass; Yellow's beach minigame still needs an in-game test. Stadium
  gifts are also included as level-5 equivalents; they do
  not reproduce historical distribution metadata.
- Crystal GS Ball Enable/Replay is included from v1.0.3.
  Automated save/checksum, backup, cancellation, ROM qualification and Pokémon
  preservation checks pass. Enable and Replay passed user testing on .17 through
  delivery, Kurt and the shrine encounter; Kurt's timer was manually cleared for
  testing. The tool retains the normal wait.
- Gen II Mew and Stadium 2 Farfetch'd/Gligar gifts are included from v1.0.3.
  All fourteen PC boxes across Gold/Silver/Crystal pass automated checks,
  including native reload, backups, cancellation and full/occupied refusal.
  All three gifts passed user testing in Crystal on .17. Actual Gold/Silver
  gameplay remains unqualified. All fifteen documented Japanese Mystery Egg
  recipes are implemented and all fifteen passed user testing in Crystal
  on .17. Native Odd Egg delivery and replay also passed user testing.
  Celebi passed user testing in Gold, including save/reload persistence.
  All 104 PCNY eggs, 16 shiny adult gifts and the split menu passed user testing
  in Crystal on .17. Silver Celebi awaits gameplay qualification.
  The incomplete non-shiny Suicune recipe is unavailable; Gen III events are
  pending. See the [PCNY checklist](BUTTERFLY_LINK_GEN2_PCNY_CHECKLIST.md).

- The current app performs save-based transfers; it does not provide cable
  emulation, battles, or party transfers.
- Same-generation local/remote trade and copy passed user testing. Remote
  Gen II → III copy also passed; source saves are unchanged and held items cleared.
- Version 1.0.3 adds verified Gen II → III held-item equivalents. All 256 item
  IDs have automated mapping coverage. Another 150 disposable-save transfers
  across Gold/Silver/Crystal and all five Gen III games passed reload/item checks,
  with originals unchanged. The new preservation behavior still needs in-game
  testing. Releases through v1.0.2 clear held items on cross-generation copies.
- Local evolution prompts are implemented for supported rules. Remote
  evolution prompts, complete Everstone/held-item rules, and arbitrary ROM
  hacks/languages are not qualified.
- Gen II → I and Gen III → earlier-generation conversion are unavailable.
- Gen III Trade currently requires the same save-format family (Ruby/Sapphire,
  Emerald, or FireRed/LeafGreen). Cross-family Gen III Copy is implemented;
  cross-family Trade is refused by the helper.
- Remote final commits occur separately. A late disconnect can leave a
  one-sided result; retain session backups and inspect both saves.
- The current UI does not offer a one-button recovery browser for every
  retained session. Never restore an unrelated save over a game by filename alone.

## Updates and interface

- Grouped-system scraper persistence is corrected. Artwork and favorites
  survived reboot during user testing.
- Online updating passed the v0.2.3 and v0.2.4 device transitions. v1.0.0
  corrects the misleading unofficial-modification warning and makes Restart
  to Apply reboot the whole device. There is no A/B rollback; see [Updates](UPDATES.md).
- Reflashing erases the device-specific recovery backup stored on the card.
  Use **Export Recovery Backup** and download the result to another
  physical device before writing a new image.
- Some inherited Advanced Mode screens retain ROCKNIX terminology and are not
  intended for beginner workflows.
- The wider-screen menu layout was corrected. No additional UI issues were
  found in the latest user tests; every display resolution is not qualified.
- The current source derives Wi-Fi state from NetworkManager and applies
  settings immediately. Use the keyboard's on-screen Enter to submit passwords.
  Historical GUI/password issues should be reported with logs if they recur.
- The release hides untested Cloud/VPN groups unless Advanced Mode is on.
  Their appearance does not establish a supported cloud/VPN workflow.

Report issues with the ButterflyOS version, device revision, controller model,
system/emulator, steps to reproduce, and whether the problem survives a reboot.

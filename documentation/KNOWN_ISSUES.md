# ButterflyOS v0.1.0 Alpha 2 known issues

Alpha software may contain defects and can change incompatibly. Keep backups of
games, saves, BIOS files, and any device-specific recovery data.

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
remains on hold until the final image, refreshed package audit, and post-build
hardware smoke test are complete.

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

- Lid-close/open suspend and resume need a dedicated regression test.
- A September 15 overnight test left HDMI and power connected to a powered-off
  4K television. After returning to the handheld display, the Games interface
  became malformed and the device stopped responding to the frontend, ping,
  and SSH. A forced restart recovered it, both filesystems checked clean, and
  the issue has not yet been reproduced. The affected build kept its journal
  only in RAM, so it could not establish whether this was a DRM/GPU or broader
  kernel stall.
- The next diagnostic build keeps a compressed journal capped at 10 MiB and
  seven days. It also records HDMI connector/EDID changes, Wi-Fi state,
  EmulationStation liveness, and whether the previous boot ended cleanly in
  `/storage/.config/system/logs/butterflyos-health.previous`.
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

## Emulation

- The restored ROCKNIX Mali stack passed rendering and gameplay checks for the
  interface, HDMI hotplug, N64, Nintendo DS, PlayStation, PSP, Dreamcast, and
  Saturn. Brief sub-second N64 stalls occurred during initial game startup and
  then smoothed out.
- Standalone YabaSanshiro ran Saturn smoothly after correcting its generated
  Flip controller map. The tested built-in and 8BitDo Xbox-mode mappings are
  now included in source and require confirmation on the final rebuild.
- Alpha 2 replaces DraStic with open-source melonDS for Nintendo DS. Its
  performance, controls, suspend/resume, and clean exit passed physical testing;
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

## Updates and interface

- There is not yet a tested ButterflyOS online-update channel or rollback
  workflow. Reflashing remains the Alpha upgrade method.
- Reflashing erases the device-specific recovery backup stored on the card.
  Use **Export ButterflyOS Recovery Backup** and download the result to another
  physical device before writing a new image.
- Some inherited Advanced Mode screens retain ROCKNIX terminology and are not
  intended for beginner workflows.
- Broad theme polishing for external display resolutions is deferred until the
  handheld interface and behavior are stable.
- Network settings in the September 15 failure became inconsistent with the
  active NetworkManager connection. The next build derives the Wi-Fi switch
  from live state, refuses empty SSID requests, and retains the last working
  profile until replacement credentials authenticate successfully.

Report issues with the ButterflyOS version, device revision, controller model,
system/emulator, steps to reproduce, and whether the problem survives a reboot.

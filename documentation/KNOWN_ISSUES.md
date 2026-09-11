# ButterflyOS v0.1.0 Alpha 1 known issues

Alpha software may contain defects and can change incompatibly. Keep backups of
games, saves, BIOS files, and any device-specific recovery data.

## Distribution licensing gate

Alpha 1 bundled vendor-derived stock and patched preloader images and therefore
remains an internal artifact. Alpha 2 removes both images. It reads, validates,
backs up, patches, and verifies the preloader from the user's own device and
retains the BaseOS-derived patcher's MIT notice.

The full device-local install and byte-exact restore round trip passed on a
second untouched Flip V2. Public distribution remains on hold until the new
runtime-dependency fixes pass once more from a clean image and the final binary
and license audit is complete.

## Installation and recovery

- The complete device-local setup/restore round trip passed on the primary test
  unit and on a second previously untouched Flip V2.
- Restore uses only the exact backup captured from that specific device. It has
  no bundled or generic fallback image.
- The clean image containing commits `8e09035` and `075b3f0` still needs the
  final no-intervention install/check/restore regression.
- Interrupted low-level setup may require RK3566 USB MASKROM recovery and, as a
  last resort, opening the shell to use the internal MASKROM button.
- Miyoo Flip V1 and other handheld models are unsupported.

## Hardware qualification

- Lid-close/open suspend and resume need a dedicated regression test.
- Rumble remains unverified.
- Long-duration battery-runtime, charging, and low-battery behavior need
  controlled measurement. Battery percentage reporting was corrected during
  development testing.
- Bluetooth Player 1 fallback depends on device-disconnect detection and is not
  literally instantaneous on every controller.

## Emulation

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
- Some inherited Advanced Mode screens retain ROCKNIX terminology and are not
  intended for beginner workflows.
- Broad theme polishing for external display resolutions is deferred until the
  handheld interface and behavior are stable.

Report issues with the ButterflyOS version, device revision, controller model,
system/emulator, steps to reproduce, and whether the problem survives a reboot.

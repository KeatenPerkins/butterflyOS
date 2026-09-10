# ButterflyOS v0.1.0 Alpha 1 known issues

Alpha software may contain defects and can change incompatibly. Keep backups of
games, saves, BIOS files, and any device-specific recovery data.

## Distribution licensing gate

The guided Flip V2 boot setup currently bundles low-level preloader utilities
and reference images pinned from the maintained Miyoo Flip reference project.
That project licenses its documentation and scripts under GPLv2, but identifies
third-party components as separately licensed. That does not establish
redistribution rights for the stock and patched vendor preloader binaries.
Public distribution of the Alpha 1 binary image is therefore on hold until
those binaries are replaced or their redistribution rights are established.

Alpha 2 will replace both bundled preloader images with device-local patching:
ButterflyOS will read, validate, back up, patch, and verify the preloader from
the user's own device. This is intended to remove the binary redistribution
question and provide exact device-specific restoration.

## Installation and recovery

- The complete setup/restore round trip passed on the primary test unit, but a
  second untouched Miyoo Flip V2 has not completed qualification.
- The bundled stock preloader restores tested stock boot behavior, but exact
  byte-for-byte restoration is not guaranteed for every unknown factory
  preloader revision.
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

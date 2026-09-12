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
public candidate also excludes proprietary Mali userspace libraries
and DraStic. Distribution remains on hold until the final clean image,
package-license audit, and post-build hardware smoke test are complete.

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
- Rumble remains unverified.
- Long-duration battery-runtime, charging, and low-battery behavior need
  controlled measurement. Battery percentage reporting was corrected during
  development testing.
- Bluetooth Player 1 fallback depends on device-disconnect detection and is not
  literally instantaneous on every controller.

## Emulation

- The Miyoo Flip V2 Panfrost qualification build passed initial rendering and
  performance checks for the interface, HDMI hotplug, N64, Nintendo DS,
  PlayStation, PSP, and Dreamcast. Brief sub-second N64 stalls occurred during
  initial game startup and then smoothed out.
- Saturn via standalone YabaSanshiro remains a Panfrost qualification
  exception. During the September 11, 2026 Sonic R test it did not accept game
  controls and produced Panfrost GPU page faults followed by a scheduler
  timeout. YabaSanshiro-libretro restored controls but ran severely slowly and
  produced continuous GPU scheduler timeouts. A real Saturn BIOS, native
  resolution, disabled compute shaders, frameskip, and CPU tessellation did not
  correct it. Test a genuinely different Saturn core/backend before treating
  the open GPU migration as fully qualified.
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

Report issues with the ButterflyOS version, device revision, controller model,
system/emulator, steps to reproduce, and whether the problem survives a reboot.

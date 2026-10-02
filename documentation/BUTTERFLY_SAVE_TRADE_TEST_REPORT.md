# ButterflyOS Save Trade Prototype Test Report

This is a historical September 29–30 prototype report. Its UI/network limits
do not describe the current app. See [Butterfly Link](BUTTERFLY_LINK.md) and
[current build status](CURRENT_BUILD_STATUS.md) for subsequent implementation
and hardware observations.

Date: 2026-09-29
Branch: `butterfly-save-trade-prototype`

## Package validation

- PKSav builds for the RK3566 aarch64 target.
- The onboarding package builds with the new native helper and experimental
  Tools menu wrapper.
- PKSav's MIT license is installed at
  `/usr/share/licenses/pksav/LICENSE.txt` and is listed in
  `THIRD_PARTY_NOTICES.md`.
- Shell syntax and `git diff --check` pass.

## Read-only device inspection

The new helper was copied to the test device at `192.168.1.20` under `/tmp`
only. It was run read-only against the existing saves:

- Ruby: Gen III, Ruby/Sapphire save type, two party Pokémon, zero boxed
  Pokémon.
- Emerald: Gen III, Emerald save type, three party Pokémon, 413 occupied box
  slots.

The Sapphire/Ruby device at `192.168.1.17` was also confirmed to contain its
expected saves. No original save was written during this test.

The device root is read-only during normal operation, so the full Tools menu
was not installed live. The package contains the menu wrapper; it will be
tested after a normal image build rather than remounting the live root.

## Generation I and II reader validation

Date: 2026-09-30

The helper was rebuilt as a package-only test and copied to the writable
ButterflyOS module area. It only performed `inspect` reads; no save was
written.

- Red, Blue, and Yellow parse as Generation I. Their current test saves have
  party Pokémon but zero occupied PC-box slots.
- Gold, Silver, and Crystal parse as Generation II. Each currently has two
  party Pokémon and zero occupied PC-box slots.
- Crystal exposed a PKSav format-detection defect: a failed Gold/Silver
  checksum probe left an invalid-error value in place after a successful
  Crystal probe. ButterflyOS adds a narrow package patch that clears that
  stale error. Gold, Silver, and Crystal now complete inspection successfully.

The live UI must still be rebuilt before it receives this corrected helper.

## Disposable swap test

Two copies of the Emerald save were used as working inputs. A box-slot swap
produced two valid output saves, and the original source copy's SHA-256 stayed
unchanged. PKSav recalculated the written save data successfully.

The same copy-only test was repeated on disposable files on `192.168.1.20`.
Box 0 slot 0 (species 1) and box 0 slot 1 (species 2) were exchanged in the
two output files, while both disposable inputs retained SHA-256
`5056bdc3d6283e22e06b1e9a80c0dd68fe30cfe2a2fec6437a82aece6be7a9fa`.

## Current limits

The UI is intentionally experimental. The helper can inspect Generation I,
II, and III saves, but the on-device UI requires the next image build and
generation-specific write testing before Gen I/II transfers are enabled.
Transfers are PC-box-only; the current Gen I/II test saves have no boxed
Pokémon, so they correctly cannot enter a transfer flow yet. It does not
emulate a link cable or transfer files between devices.

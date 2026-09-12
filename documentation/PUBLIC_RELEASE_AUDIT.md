# ButterflyOS public-release audit

This records technical release checks. It is not legal advice.

## Alpha 2 candidate policy

- Target only `RK3566/Miyoo_Flip_V2`.
- Use Mesa/Panfrost; do not bundle proprietary `libmali` userspace libraries.
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

## Manual license review

The generated package manifest is an inventory, not a legal conclusion.
The flagged entries were reviewed against their exact build sources. Findings,
corrections, removal impacts, and the free-release policy are recorded in
`PACKAGE_LICENSE_REVIEW_ALPHA2.md`. This technical review is not legal advice.

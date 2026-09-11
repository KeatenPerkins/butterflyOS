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

The final Alpha 2 image must repeat these checks after DraStic exclusion and
must receive a hardware smoke test before publication.

## Manual license review still required

The generated package manifest is an inventory, not a legal conclusion.
Entries declared `Non-commercial`, `Unknown`, `Not declared`, `CUSTOM`,
`proprietary`, or `nonfree` require review against their upstream source and
the actual files installed in the final image. ButterflyOS being free resolves
neither missing license declarations nor all definitions of commercial use.

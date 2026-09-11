# ButterflyOS source and license compliance

This is the release procedure for a downloadable ButterflyOS binary image. It
is an engineering checklist and not legal advice.

## Corresponding source

For every published image:

1. Record the exact ButterflyOS Git commit and immutable tag.
2. Publish all ButterflyOS modifications, build scripts, configuration,
   patches, and preferred source forms used to build the image.
3. Record every fetched component's name, version or revision, source URL,
   archive hash, and declared license.
4. Preserve a source archive or dependable mirror for GPL-covered components;
   do not rely solely on an unpinned moving upstream branch.
5. Put clear source instructions beside the binary download and keep the
   corresponding source available for the period required by each license.
6. Verify that a clean checkout plus documented prerequisites can reproduce the
   device-specific build.

The Alpha 1 image was built from commit
`2fe9d6daa0fe4a0b58db5bbee3a3c75d08b85060` and has SHA-256
`56b1721c09a6ac22a8b24f43a6f3b4fb812d86c0bb4c0f48be4328fa13ff9c7a`.
Documentation commits after that baseline must not be represented as the exact
binary source revision.

## Release contents

Before publishing:

- Include the project license, component licenses, copyright notices, and
  `THIRD_PARTY_NOTICES.md`.
- Include DraStic's archived redistribution grant if DraStic remains present.
- Complete review of every package labeled `unknown`, `nonfree`, `proprietary`,
  `custom`, or `Non-commercial`.
- Scan the final filesystem and boot partition, not only source package files.
- Confirm no ROMs, user BIOS files, credentials, Wi-Fi profiles, SSH host keys,
  personal recovery backups, logs, or test media entered the image.
- Confirm all visible primary branding is ButterflyOS and retain appropriate
  upstream attribution separately.
- Publish the image checksum and verify it after upload.

## ButterflyOS-owned material

New ButterflyOS scripts currently use GPL-2.0-or-later identifiers where they
interact with the GPL-derived distribution. Original system artwork identifies
Keaten Perkins as copyright holder and uses CC-BY-SA-4.0 in its artwork README.

The copyright holder selected the following policy in
`BUTTERFLYOS_LICENSE.md`:

- Original ButterflyOS software: GPL-2.0-or-later
- General original artwork and documentation: CC BY-SA 4.0
- Official ButterflyOS name, emblem, and wordmark: rights retained with
  explicit permission for unmodified official releases, reviews, screenshots,
  documentation, and truthful identification

## Project identity

Public pages and images should state:

> ButterflyOS is an independent community project. It is not affiliated with
> or endorsed by Miyoo, ROCKNIX, Nintendo, Sega, Sony, or any other platform
> owner.

Use third-party names only as needed to identify compatibility or provide
attribution. Do not use their logos to suggest an official relationship.

## Current release blockers

- Physically qualify Alpha 2's device-local preloader patching and exact restore
  workflow on the second untouched Miyoo Flip V2. The development package no
  longer contains the Alpha 1 stock or prepatched images.
- Complete the Rockchip `rkbin` binary-notice review.
- Complete the Mali `g29p1` userspace binary-notice review.
- Generate and review the complete final-image package/license manifest.

The Alpha 1 manifest has now been generated and resolves all 554 target package
names to source definitions. Manual upstream-license review remains necessary
for the entries it flags as noncommercial, unknown, nonfree, proprietary,
custom, or not declared.

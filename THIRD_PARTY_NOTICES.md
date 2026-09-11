# ButterflyOS third-party notices

ButterflyOS is a Linux distribution assembled from independently licensed
components. This document records important notices for the Miyoo Flip V2
Alpha 1 image. It is a release-audit aid, not a replacement for the license
text shipped with each component.

## ROCKNIX, JELOS, and LibreELEC

ButterflyOS is derived from ROCKNIX and inherits work from JELOS and LibreELEC.
Original ROCKNIX software and scripts are identified by the project as GNU GPL
version 2. Individual inherited components remain under their respective
licenses. Copyright notices, source history, and license files must be retained.

ROCKNIX branding and images are separately licensed under Creative Commons
Attribution-NonCommercial-ShareAlike 4.0. ButterflyOS uses its own primary
identity and does not claim endorsement by ROCKNIX.

- ROCKNIX: https://github.com/ROCKNIX/distribution
- JELOS: https://github.com/JustEnoughLinuxOS/distribution
- LibreELEC: https://github.com/LibreELEC/LibreELEC.tv

## Miyoo Flip reference scripts

The Alpha 1 onboarding package pins files from:

- Project: Miyoo Flip Mainline Linux Reverse Engineering
- Maintainer: Zetarancio and contributors
- Revision: `4f32de5bae58cad07c54b5fb8450fc00385f4260`
- Source: https://github.com/Zetarancio/Miyoo-Flip-Mainline-Linux-Reverse-Engineering

That project identifies documentation and scripts as GPLv2 and says
third-party components retain their own licenses. This covers the referenced
shell scripts but does not establish rights to redistribute the vendor-derived
`preloader-stock.img` and `preloader-patched.img` binaries.

**Release status:** Alpha 1 remains unsuitable for public binary distribution.
The Alpha 2 development package no longer fetches or installs either image; it
patches a verified copy read from the user's own device.

The Alpha 2 device-local patch algorithm is derived from apommel's BaseOS work:
https://github.com/apommel/baseos-my355. BaseOS is MIT licensed. Any ButterflyOS
adaptation must preserve its copyright and MIT permission notice.

## DraStic

DraStic is proprietary software. The package includes `LICENSE.txt` and
`LICENSE.pdf`, which archive a redistribution grant from its creator, Exophase.
Those records must remain in the image and corresponding release archive.

- Package source record: `projects/ROCKNIX/packages/emulators/standalone/drastic-sa/package.mk`
- Installed notices: `/usr/config/drastic/LICENSE.txt` and `LICENSE.pdf`

## Rockchip boot firmware (`rkbin`)

The RK3566 bootloader build uses binary firmware from Rockchip's `rkbin`
repository. Rockchip's license grants rights to use, copy, and distribute the
software, subject to its restrictions and preservation of its notices. The
exact upstream license is retained as
`licenses/LicenseRef-Rockchip-rkbin.txt` and is copied into the release license
bundle by the image build.

- Source: https://github.com/rockchip-linux/rkbin
- ButterflyOS package revision: `74213af1e952c4683d2e35952507133b61394862`
- Source archive SHA-256:
  `b565faeab846950262c07e6debbd6519ea9e7f34943dbb305b9cea6b1026e11a`
- BL31 input: `bin/rk35/rk3568_bl31_v1.45.elf`
  (`76634f10e535bbe981fb9132fd6815a71586cc1b96aae1159bec6797579e5b9f`)
- DDR/TPL input: `bin/rk35/rk3568_ddr_1056MHz_v1.23.bin`
  (`20e4bb076847bd019fcdeb7bdc15bd249890f07ecc76e9937101f22e50950982`)

**Audit status:** redistribution terms reviewed and exact license retained.
The precise firmware inputs incorporated into the final U-Boot artifact are
listed above and must also remain in each per-release binary manifest.

## Arm Mali userspace libraries

The inherited RK3566 configuration can include proprietary/nonfree Mali-G52
userspace libraries from the JeffyCN mirror used by ROCKNIX. ButterflyOS
excludes these libraries for the Miyoo Flip V2 and uses Mesa/Panfrost instead.

- Source: https://github.com/JeffyCN/mirrors
- ButterflyOS package revision: `4233031d818e97a19e8a9cdbbd5c15795ededd93`

**Audit status:** the Miyoo Flip V2 Panfrost-only image was rebuilt and scanned;
no `libmali` package tree, proprietary Mali userspace filename, or `libmali`
SONAME reference was found. Device performance testing is still required before
this issue can be closed.

## Linux firmware

Device firmware is distributed under file-specific terms recorded by the
Linux firmware project or the applicable vendor. Preserve the firmware license
notices and do not describe all firmware as GPL merely because it is loaded by
the Linux kernel.

## Emulator cores, applications, libraries, fonts, and shaders

The image contains hundreds of additional packages under GPL, LGPL, BSD, MIT,
Apache, public-domain, noncommercial, and component-specific terms. The build
tree's `licenses/` directory and package `PKG_LICENSE` declarations are the
authoritative starting points. A generated per-release manifest must accompany
the public image; this preliminary notice does not replace it.

ButterflyOS distributes no commercial games and no proprietary console BIOS
collection. Users supply content they are legally entitled to use.

The Alpha 1 build metadata marks 11 included emulator cores as
`Non-commercial`: `fbalpha2012-lr`, `fbalpha2019-lr`, `fbneo-lr`,
`genesis-plus-gx-lr`, `genesis-plus-gx-wide-lr`, `smsplus-gx-lr`, `snes9x-lr`,
`snes9x2002-lr`, `snes9x2005_plus-lr`, `snes9x2010-lr`, and
`supersnes9x-lr`. A free release must retain their notices. Any later sale,
paid-access model, or other commercial distribution requires a separate review
or replacement/removal of affected cores.

See `documentation/ALPHA1_PACKAGE_LICENSE_MANIFEST.md` for all 554 target
packages recorded from the completed Alpha 1 build. The manifest also flags 37
packages with incomplete metadata, three marked unknown, one nonfree package,
one proprietary package, and two custom declarations for manual review. These
labels are leads for review; package metadata can itself be incomplete or
incorrect and does not supersede an upstream license.

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

**Release status:** unresolved for Alpha 1 binary distribution. Alpha 2 will
remove both images and patch a verified copy read from the user's own device.

The multiboot technique credits apommel's BaseOS work:
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
repository and labels it `nonfree`. Before a public image is published, retain
the upstream notices and document the exact revision and binary files included
in the generated Miyoo Flip V2 U-Boot image.

- Source: https://github.com/rockchip-linux/rkbin
- ButterflyOS package revision: `74213af1e952c4683d2e35952507133b61394862`

**Audit status:** redistribution terms and required notices need final review.

## Arm Mali userspace libraries

The RK3566 image includes proprietary/nonfree Mali-G52 userspace libraries from
the JeffyCN mirror used by ROCKNIX. They are necessary for the selected GPU
stack and are separate from the open-source wrapper/build scripts.

- Source: https://github.com/JeffyCN/mirrors
- ButterflyOS package revision: `4233031d818e97a19e8a9cdbbd5c15795ededd93`

**Audit status:** locate, preserve, and review the vendor redistribution terms
for the exact `g29p1` binaries before public release.

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

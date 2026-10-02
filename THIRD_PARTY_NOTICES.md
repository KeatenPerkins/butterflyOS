# ButterflyOS third-party notices

ButterflyOS is a Linux distribution assembled from independently licensed
components. This document records important notices for the Miyoo Flip V2
Alpha 2 image. It is a release-audit aid, not a replacement for the license
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

DraStic is proprietary software. Although it is available in the inherited
ROCKNIX source tree, ButterflyOS excludes it from Miyoo Flip V2 public images
because the project does not currently retain independently verified evidence
that the redistribution grant covers this release. Open-source melonDS cores
and the standalone melonDS emulator remain available.

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

The RK3566 configuration includes Mali-G52 userspace libraries from the
JeffyCN mirror used by ROCKNIX. The accompanying EULA permits use, copying, and
distribution subject to its terms and must accompany redistributed binaries.
ButterflyOS uses the upstream ROCKNIX mapping fix that avoids modifying the
vendor blob.

- Source: https://github.com/JeffyCN/mirrors
- ButterflyOS package revision: `4233031d818e97a19e8a9cdbbd5c15795ededd93`

**Audit status:** the EULA and no-blob-modification source changes are present.
The restored stack passed physical gameplay testing, including Saturn. The
final rebuilt image must be checked for the EULA and unmodified blob before
publication.

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

The Alpha 2 source review found 10 included emulator cores with genuine
non-commercial terms: `fbalpha2012-lr`, `fbalpha2019-lr`, `fbneo-lr`,
`genesis-plus-gx-lr`, `genesis-plus-gx-wide-lr`, `snes9x-lr`,
`snes9x2002-lr`, `snes9x2005_plus-lr`, `snes9x2010-lr`, and
`supersnes9x-lr`. A free release must retain their notices. Any later sale,
paid-access model, or other commercial distribution requires a separate review
or replacement/removal of affected cores.

`smsplus-gx-lr`, `px68k-lr`, and `xmil-lr` were previously mislabeled; their
exact source contains GPLv2, GPLv2, and BSD-style licenses respectively. The
full technical review is recorded in
`documentation/PACKAGE_LICENSE_REVIEW_ALPHA2.md`.

ButterflyOS is freely downloadable and is not conditioned on payment or a
donation. Art Book Next and ZeroTier are excluded from the public Flip V2
configuration beginning with the post-review Alpha 2 candidate.

## PKSav

The Butterfly Link save-transfer helper uses PKSav, a portable C
library for reading and writing Pokémon save files. PKSav is distributed under
the MIT license; its complete license text is shipped with the image under
`/usr/share/licenses/pksav/LICENSE.txt`.

- Source: https://github.com/savaughn/pksav
- ButterflyOS use: read-only inspection and copy-based save transactions
- ButterflyOS does not distribute game ROMs or save files.

## Game Boy sprite-cache decoder

The optional Generation I/II Butterfly Link sprite-cache decoder is adapted
from Andrew Ekstedt's `pokemon-sprites-rby` project, under BSD-2-Clause:

- Source: https://github.com/magical/pokemon-sprites-rby
- Pinned reference revision: `36966acd74c2a93e3bc583e7aa6786b6eba8c8e4`
- ButterflyOS use: decode front sprites only from a ROM the user already owns;
  no Pokémon graphics are included in the image.

The decoder source retains its attribution and the image already ships the
BSD-2-Clause license text in its license bundle.

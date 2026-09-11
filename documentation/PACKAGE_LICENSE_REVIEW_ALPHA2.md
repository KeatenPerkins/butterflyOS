# ButterflyOS Alpha 2 flagged-package review

Reviewed September 11, 2026 against the exact source trees used by build
`c9d2f0b`. This is a technical compliance review, not legal advice.

## Outcome

The manifest's 30 flags do not represent 30 unresolved redistribution
problems:

- 15 are open-source packages whose ROCKNIX metadata was absent or inaccurate.
- 2 are essential aggregate/ButterflyOS packages with source available in this
  repository.
- 1 is Rockchip firmware with an express redistribution grant.
- 11 have genuine non-commercial terms.
- 1 unused network service, ZeroTier, should be excluded to avoid unnecessary
  licensing and attack surface.

The safest practical Alpha 2 policy is to keep the important non-commercial
emulation cores in a free, no-payment-required image, reproduce their full
licenses and source, and do not solicit donations specifically in exchange for
the image. Before monetization or project-linked donations, obtain legal advice
or move those cores to an optional third-party installer.

## Recommended removals

| Package | Reason | User-visible effect | Approx. unpacked saving |
|---|---|---|---:|
| `es-theme-art-book-next` | Not selected by ButterflyOS; CC BY-NC-SA alternate theme adds branding and attribution surface | Removes the optional Art Book Next theme. The ButterflyOS theme and normal interface remain. There is less fallback if the ButterflyOS theme is damaged. | 44 MB |
| `zerotier-one` | No ButterflyOS UI or tested use case; current source contains mixed MPL and source-available sections, although the built agent appears to use the MPL portion | Advanced SSH users cannot join a ZeroTier virtual network from the handheld. Ordinary Wi-Fi, SSH, web transfer, Bluetooth, and LAN features are unaffected. | 1.5 MB |

Removing these changes the release image, so it requires a rebuild and a short
boot/UI/network regression test. Compressed-image savings will be smaller than
the unpacked numbers.

## Optional size reductions—not required for licensing

These are genuinely non-commercial but redistributable without charge. Removing
only redundant variants reduces size while retaining the main system:

| Package | Effect if removed | Approx. unpacked saving |
|---|---|---:|
| `fbalpha2012-lr` | Removes an older arcade fallback core; FBNeo and MAME remain | 21 MB |
| `fbalpha2019-lr` | Removes another older arcade fallback; FBNeo and MAME remain | 42 MB |
| `genesis-plus-gx-wide-lr` | Removes experimental widescreen Genesis support; normal Genesis Plus GX and PicoDrive remain | 12 MB |
| `snes9x2002-lr` | Removes a low-accuracy fallback intended for very weak hardware | 0.8 MB |
| `snes9x2005_plus-lr` | Removes an older performance fallback | 0.7 MB |
| `snes9x2010-lr` | Removes another older SNES fallback | 1.9 MB |
| `supersnes9x-lr` | Removes a Super Game Boy/SNES fallback; may reduce special SGB compatibility | 2.3 MB |

Do not remove the following defaults merely to simplify licensing without first
selecting and testing replacements:

- `fbneo-lr`: default CPS1/CPS2/CPS3, FinalBurn, and Neo Geo core. MAME is an
  alternative, but performance and ROM-set compatibility would change.
- `genesis-plus-gx-lr`: important default-quality Genesis, Master System, Game
  Gear, and Sega CD emulation. PicoDrive can replace much of it, but not with
  identical compatibility.
- `snes9x-lr`: the tested SNES default. Open-source alternatives exist, but may
  be slower or behave differently on RK3566.

`smsplus-gx-lr` does not actually need removal: its exact source includes GPLv2,
not a non-commercial license. It is tiny and provides another Master System/
Game Gear option.

## Genuine non-commercial packages retained in the candidate

| Package group | Exact-source finding | Release consequence |
|---|---|---|
| FB Alpha 2012/2019 and FBNeo | Free source/binary redistribution is granted, but sale, rental, or seeking monetary profit is forbidden; modified source and the verbatim license must be public | Fine for a genuinely free download with notices/source. Treat project-linked donations cautiously. Never bundle ROMs. |
| Genesis Plus GX and GX Wide | Redistribution is allowed, but builds may not be sold or used in commercial products/activities; modified builds require complete source | Fine for a free image with complete source and license. Donations/commercial sponsorship need separate review. |
| Snes9x family | Binary/source distribution is allowed for non-commercial purposes; license calls it personal-use freeware and defines several commercial uses | Fine for free testing/distribution with the license. Do not charge for or promote a paid product with the image. |
| Art Book Next | CC BY-NC-SA with attribution/share-alike requirements | Legally usable in a free distribution if obligations are met, but removal is cleaner because ButterflyOS does not use it. |

## False alarms cleared from exact source

| Package | Verified terms | Effect if unnecessarily removed |
|---|---|---|
| `emuscv-lr` | GPLv3 | Loses Super Cassette Vision emulation |
| `enet` | MIT-style | May break applications that use the ENet networking library |
| `flycast-lr` | GPLv2 | Loses the primary RetroArch Dreamcast/Naomi core |
| `freej2me-lr` | GPLv3 plus included BSD-style ASM terms | Loses Java ME game support |
| `jaxe-lr` | MIT | Loses CHIP-8/S-CHIP/XO-CHIP support provided by JAXE |
| `libspeexdsp` | BSD-style | Breaks EasyRPG audio processing dependency |
| `mojozork-lr` | zlib-style | Loses Z-machine interactive-fiction support from MojoZork |
| `openbor` | BSD-style | Loses OpenBOR games |
| `opusfile` | BSD-style | May break Opus decoding consumers |
| `px68k-lr` | GPLv2 file present | Loses the default Sharp X68000 core |
| `smsplus-gx-lr` | GPLv2 file present | Loses an optional Master System/Game Gear core |
| `wildmidi` | GPLv3 player/LGPLv3 library | Breaks EasyRPG MIDI dependency |
| `xmil-lr` | BSD-style file present | Loses Sharp X1 emulation |

`libxmp-lite` includes an MIT-style grant in its exact README and sources.
The downloaded `rclone` binary also has an open upstream license, but its
current binary-package recipe does not preserve
the upstream license alongside the installed payload. Fix the recipes and
notices rather than treating removal as legally necessary. Removing
`libxmp-lite` would break EasyRPG module-audio support. Removing `rclone` would
remove command-line/cloud backup capability and save about 61 MB unpacked; the
controller-facing rclone tools are already hidden on the Flip V2.

## Essential special cases

- `modules` is marked `custom` in metadata, but its package and scripts carry
  ROCKNIX GPL-2.0 identifiers and contain the ButterflyOS recovery, controls,
  quick-start, and system-manager tools. Do not remove it. Correct its metadata
  and retain source/notices.
- `network` is a virtual aggregate rather than a separately copyrighted
  executable. Removing it would remove NetworkManager, Wi-Fi, SSH, Avahi, and
  other network facilities. Review its component packages, not the aggregate.
- `rkbin` contains boot firmware needed by the RK3566 platform. Its exact
  license expressly permits use, copying, distribution, and source
  modification, while forbidding reverse engineering and removal of notices.
  Keep the unmodified firmware and its full license.

## Actions required before publication

1. Remove Art Book Next and ZeroTier for the Miyoo Flip V2 configuration.
2. Correct inaccurate/missing package-license metadata where exact source
   establishes the terms.
3. Install the relevant license and attribution texts into the release notices.
4. Publish the exact modified source and build scripts. For copyleft and
   non-commercial cores requiring complete source, do not rely solely on links
   that could disappear.
5. Keep Alpha 2 freely downloadable without payment or donation gates.
6. Rebuild, repeat the clean-image audit, and smoke-test ButterflyOS theme,
   Wi-Fi, SSH, web transfer, SNES, Genesis, arcade, and recovery.

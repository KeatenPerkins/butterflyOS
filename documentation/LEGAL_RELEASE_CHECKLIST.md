# ButterflyOS public-release legal checklist

## Project and source

- [x] Exact binary source commit recorded (`c9d2f0b`); immutable tag pending
- [ ] Corresponding source and build instructions published beside the image
- [ ] Source dependency URLs, revisions, hashes, and licenses recorded
- [ ] GPL/LGPL license texts and copyright notices retained
- [ ] Clean-checkout build procedure verified

## Binary and firmware audit

- [x] Bundled stock and prepatched vendor preloaders removed
- [x] Device-local preloader patcher license and attribution retained
- [x] Rockchip `rkbin` redistribution terms reviewed and notices included
- [x] Miyoo Flip V2 rebuilt and scanned without Mali `g29p1` userspace blobs
- [x] DraStic excluded from the ButterflyOS Miyoo Flip V2 public configuration
- [x] Every Alpha 2 package flagged `unknown`, `nonfree`, `proprietary`,
      `custom`, `Not declared`, or `Non-commercial` reviewed; findings and
      impacts recorded in `PACKAGE_LICENSE_REVIEW_ALPHA2.md`
- [x] Final boot and system filesystems scanned for unintended binaries and
      private content

## Content and privacy

- [x] No games, proprietary user BIOS files, or test media included
- [x] No Wi-Fi credentials, SSH host keys, passwords, logs, or personal data
- [x] No device-specific preloader backup or recovery data included
- [ ] Required firmware and font notices retained

## Branding

- [x] ButterflyOS code, artwork, documentation, and identity policy selected by
      its copyright holder and recorded in `BUTTERFLYOS_LICENSE.md`
- [ ] ROCKNIX branding removed or used in compliance with CC BY-NC-SA 4.0
- [x] Upstream ROCKNIX/JELOS/LibreELEC attribution retained
- [x] Independent-project/non-endorsement disclaimer added

## Release page

- [ ] Image and checksum uploaded as release assets, not committed to Git
- [ ] Alpha status and Miyoo Flip V2-only scope displayed prominently
- [ ] Install, recovery, hotkey, known-issues, and source links included
- [ ] SHA-256 verified after downloading the published asset
- [ ] Donation language reviewed separately from download access

# ButterflyOS public-release legal checklist

Historical package reviews and image scans are supporting evidence, not
approval of a later image. Items referring to the final artifact remain open
until its exact source revision and binary have been checked together.

## Project and source

- [ ] Exact binary source commit and immutable tag recorded after final rebuild
- [ ] Corresponding source and build instructions published beside the image
- [ ] Source dependency URLs, revisions, hashes, and licenses recorded
- [ ] GPL/LGPL license texts and copyright notices retained
- [ ] Clean-checkout build procedure verified

## Binary and firmware audit

- [x] Bundled stock and prepatched vendor preloaders removed
- [x] Device-local preloader patcher license and attribution retained
- [x] Rockchip `rkbin` redistribution terms reviewed and notices included
- [ ] Final Miyoo Flip V2 image checked for the complete Mali EULA and verified
      to use the unmodified `g29p1` vendor blob
- [x] DraStic excluded from the ButterflyOS Miyoo Flip V2 public configuration
- [ ] Final package inventory checked against the previously reviewed `unknown`, `nonfree`, `proprietary`,
      `custom`, `Not declared`, or `Non-commercial` reviewed; findings and
      impacts recorded in `PACKAGE_LICENSE_REVIEW_ALPHA2.md`
- [ ] Final boot and system filesystems scanned for unintended binaries and
      private content

## Content and privacy

- [ ] Final image contains no games, proprietary user BIOS files, or test media
- [ ] Final image contains no Wi-Fi credentials, SSH host keys, passwords, logs, or personal data
- [ ] Final image contains no device-specific preloader backup or recovery data
- [ ] Required firmware and font notices rechecked in the final rebuilt image

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

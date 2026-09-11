# ButterflyOS public-release legal checklist

## Project and source

- [ ] Exact binary source commit and immutable release tag recorded
- [ ] Corresponding source and build instructions published beside the image
- [ ] Source dependency URLs, revisions, hashes, and licenses recorded
- [ ] GPL/LGPL license texts and copyright notices retained
- [ ] Clean-checkout build procedure verified

## Binary and firmware audit

- [x] Bundled stock and prepatched vendor preloaders removed
- [x] Device-local preloader patcher license and attribution retained
- [x] Rockchip `rkbin` redistribution terms reviewed and notices included
- [x] Miyoo Flip V2 rebuilt and scanned without Mali `g29p1` userspace blobs
- [ ] DraStic redistribution-grant records retained
- [ ] Every `unknown`, `nonfree`, `proprietary`, `custom`, and
      `Non-commercial` package reviewed
- [ ] Final boot and system filesystems scanned for untracked binaries

## Content and privacy

- [ ] No games, proprietary user BIOS files, or test media included
- [ ] No Wi-Fi credentials, SSH host keys, passwords, logs, or personal data
- [ ] No device-specific preloader backup or recovery data included
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

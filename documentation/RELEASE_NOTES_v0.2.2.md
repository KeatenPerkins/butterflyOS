# ButterflyOS v0.2.2 — Miyoo Flip V2 online-update test

This release supplies the first online-update test package for v0.2.1.
End-to-end installation qualification is pending the device test.

- Fix Start menu frames on widescreen HDMI displays using the artwork's native
  16-pixel corners.
- Apply `CUSTOM_VERSION` consistently to image names, OS identity, and updater
  identity.
- Support older squashfs-tools in the update-package builder.

The system was assembled from `c2e56b71975178ca577ce2f828b35b2e8dd16853`.
The packaging compatibility fix is `310ddc0c32`; it changes the host builder,
not the installed system. Update identity `20261004` was explicitly assigned
on October 3 to allow testing from installed build `20261003`, reserving the
October 4 build number.

The archive passed the installed updater's manifest/archive validators,
size and SHA-256 checks, and internal checksums. Extracted SYSTEM files matched
the menu theme and updater source; the Flip V2 device tree and version stamps
were verified. The six offline updater tests passed.

The release must be a regular GitHub release for the installed updater to
discover it; draft and prerelease releases are skipped. This visibility does
not mean online installation has completed hardware qualification.

Use **Start → Updates & Downloads → Start Update** on a v0.2.1 Flip V2.
Back up important saves and keep front-port power connected. After installation,
verify version `20261004`, widescreen menus, games, saves, artwork, and settings.
The tested v0.2.1 full image remains the installation/recovery image.

Update archive SHA-256:

```text
0327287bb93ed787026b2cea1a6b29642df2f94e89cf7f4635cf5cd9c4fb13d7
```

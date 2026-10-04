# ButterflyOS v0.2.3 — corrected online-update test

The first v0.2.2 download passed verification, but installation failed before
OS replacement: the installed initramfs required `ROCKNIX` in the staged archive
filename and deleted `ButterflyOS-20261004.tar`. v0.2.2 is now a prerelease and
is skipped by the updater.

v0.2.3 includes:

- Legacy-compatible staging as `ROCKNIX-ButterflyOS-YYYYMMDD.tar`.
- A rebuilt kernel whose boot installer accepts dated ButterflyOS archives as
  well as inherited release names, retaining checksum/hardware checks.
- ButterflyOS branding in the update progress title.
- The native 16-pixel menu frame corners for widescreen HDMI displays.

Source commit: `decc735c84050296a691f8879b2bbc47a37436a7`.
Build identity: `20261004`, reserved for this test. The failed package did not
install that version, so this build remains newer than installed `20261003`.

All seven offline updater tests pass. The finished archive passed size,
SHA-256, manifest, device identity, and internal checksum validation. Extracted
files matched the corrected updater, rebuilt menu executable, and theme. The
Flip device tree and updated filename rule in the kernel's generated initramfs
were checked. End-to-end installation qualification is still pending.

The original v0.2.1 updater needs the staging fix for this initial transition.
On test device `192.168.1.20`, the corrected script was copied to
`/storage/.config/butterflyos-update-test` and bind-mounted over
`/usr/bin/butterflyos-update` for the current session. It disappears on reboot;
the new installed SYSTEM includes the permanent fix. Other v0.2.1 installations
should wait for qualification and documented migration instructions.

For the prepared test device, keep front-port power connected and use
**Start → Updates & Downloads → Start Update**. After reboot, verify version
`20261004`, widescreen menus, games, saves, artwork, and settings.
The normal-mode System Settings entry is deferred until installation succeeds.

Archive SHA-256:

```text
3289e24966c2e09cddfaa4e662571304e86665bc979102230a39c1282317d3f6
```

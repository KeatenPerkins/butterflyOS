# ButterflyOS updates

## How to update

These instructions apply to installations with the corrected ButterflyOS
updater, including v0.2.3 and newer. Older v0.2.1 installations need the
migration fix described under [Current status](#current-status).

### Before downloading

- Save and exit any running game or Butterfly Link session.
- Back up important saves and export your device's recovery backup.
- Connect to Wi-Fi, charge the battery to **at least 50%**, and connect power
  through the **front USB-C port**. Keep the device powered throughout the update.
- Have **at least 3 GB free on the ButterflyOS SD card's storage
  partition**. This means unused space, not the card's total capacity. Free
  space on a second game card does not count toward this requirement.

Update downloads are typically about **1.3 GB**, with about **3 GB free** needed
for downloading and installation. Exact requirements vary by release; check
the [latest release notes](https://github.com/KeatenPerkins/butterflyOS/releases/latest). The updater
calculates the requirement from the download size plus unpacked size plus
256 MiB of working space and requests more space when needed. It also checks
that the update fits the separate boot partition before starting.

### Download and verify

1. Open the update menu:
   - **v0.2.4 or newer:** **Start → System Settings → Update ButterflyOS**.
   - **v0.2.3:** **Start → Updates & Downloads → Start Update**. Enable
     **Advanced Mode** in User Interface Settings if that menu is hidden.
2. Check the offered version against the updater build identity in the
   [latest release notes](https://github.com/KeatenPerkins/butterflyOS/releases/latest).
   Confirm the download.
3. **Wait for the entire package to download and verify.** The device downloads
   the OS update automatically; you do not need to copy or flash an SD-card
   image. Download time depends on Wi-Fi and server speed and can take several
   minutes or longer. The display may show status text without a percentage.
4. Wait for **Update is ready / Reboot to apply**. Finding an update or finishing
   its download does not install it; the package must pass verification first.
   Do not restart while downloading or verifying. If an error appears, resolve
   it and retry instead of proceeding to installation.

v0.2.3 and v0.2.4 may show **Unofficial system modifications detected** when
asking for confirmation. This is an inherited warning about the `community`
build label, not a check of your files. Confirm the expected ButterflyOS
version; the updater still verifies the official package. v1.0.0 removes this misleading warning.

### Restart to install

1. Once the verified update is ready, choose **Start → Quit → Restart System**
   and confirm. Use **Restart System**, which reboots the whole device.
   **Restart EmulationStation** only restarts the menu and does not install
   the update. The update menu's Apply Update / Restart to Apply shortcut in
   v0.2.3 and v0.2.4 also only restarts the menu; this is corrected in v1.0.0.
2. The device shows an update progress screen during startup. **Keep power
   connected and leave the OS card inserted** while it works through the steps.
   Wait for installation and startup to finish; do not interrupt them.
3. Check the version at the bottom of the Start menu. It should match the
   updater build identity in the release notes for the update you installed.
   Check your games, saves, favorites, artwork, and settings before resuming
   normal use.

The update replaces OS files and is intended to retain games, saves, media,
and settings. It does not reformat the storage partition. Keep backups:
preservation has been checked on one prepared test-device transition, and
broader testing is still pending. A power interruption while replacing boot
files can require a backed-up reflash to recover.

If the version stays unchanged, check that the package was verified and that
you used **Restart System**. If no update is offered, your installed build may
already be current. Do not delete staged update files or reflash simply to
retry a failed download; read the error and resolve its cause first.

## Current status

The [latest stable release](https://github.com/KeatenPerkins/butterflyOS/releases/latest) includes a
fresh-install image, its matching checksum, and an online update package.
Its release notes record the public version, updater build identity, changes,
and validation. See [current build status](CURRENT_BUILD_STATUS.md) for
published builds and changes awaiting the next image.

### Older-build compatibility


The ButterflyOS-specific updater is included from **v0.2.1**. The prepared
Flip V2 test device successfully installed **v0.2.3** online. Broader hardware
qualification is still pending; original v0.2.1 installations need the migration
fix described below. The first Alpha 2 image's inherited updater must not be
used to install a generic ROCKNIX release.

The v0.2.2 test failed at the inherited boot installer's archive filename gate;
it is now a prerelease and is skipped. The corrected v0.2.3 package uses build
identity `20261004` and includes both a legacy-compatible staging name and an
updated boot filename rule. The prepared .20 device successfully installed and
rebooted into `20261004`, retained all 42 pre-recorded files under `/storage/roms`,
and was not offered the same update again. The original v0.2.1 updater needs a
staging fix before this transition; the new installed SYSTEM contains the fix
permanently. Broader acceptance testing is still pending. See
[v0.2.3 release notes](RELEASE_NOTES_v0.2.3.md) for validation and migration details.

**v0.2.4** uses build identity `20261005` and adds
**Start → System Settings → Update ButterflyOS**, available without Advanced
Mode, along with menu polish and PortMaster in Tools. Installed v0.2.3 still
uses **Updates & Downloads** to install it. See
[v0.2.4 release notes](RELEASE_NOTES_v0.2.4.md).

The update confirmation in v0.2.3 and v0.2.4 can show "Unofficial system
modifications detected" because the inherited ROCKNIX interface classifies
`community` builds that way. It does not inspect files for modifications.
v1.0.0 uses the normal version confirmation for ButterflyOS; package
identity, size, and checksum validation remain unchanged.

This is **not an A/B updater**: loss of power during replacement of boot files
can leave an unbootable card. Recovery may require backing up readable storage
on a computer and reflashing. Internal NAND/preloader changes are not an online
update feature; install/restore remains a separate explicit process.

## Release rules and safety checks

- Only the official `KeatenPerkins/butterflyOS` GitHub repository is queried.
- Draft/prerelease releases and releases without `butterflyos-update.json` are
  skipped. Publishing an installation image alone does not enable updates.
- Updates target Miyoo Flip V2, aarch64, and identify themselves as ButterflyOS.
- Build versions use `YYYYMMDD`; same-date updates and downgrades are refused.
  Publish update builds on distinct dates. Stable/nightly/force selections from
  the inherited interface are not honored by this updater.
- The archive contains only an identity file, SYSTEM/KERNEL, and their checksums.
  Links, path traversal, extra files, and mismatched identity are rejected.
- Incomplete downloads remain outside `/storage/.update`, so a reboot cannot
  install a partial download. A validated archive is staged by atomic rename.
- A concurrent updater, existing staged update, insufficient space, or low/
  unreadable battery state blocks staging.
- HTTPS and hashes protect transport/integrity; this first implementation has
  **no independent signed-release verification**. Protect the GitHub account.

## Publishing an update package

The next full build must include the updater and device/version stamps under
`/usr/share/butterflyos/`. Image assembly stamps the current build date even
when packages came from cache. Rebuild the `rocknix` package when first adding
the updater to an existing build tree.

Use the completed build's matching SYSTEM and KERNEL, not files from different
builds. Image assembly deletes raw `.system`/`.kernel` outputs during cleanup,
so run a release build and extract its matching pair from the generated `.tar`.
With `unsquashfs` installed on the build computer:

```sh
mkdir -p /path/to/build-output
tar -xf target/<image-name>.tar -C /path/to/build-output <image-name>/target
python3 scripts/butterflyos-update-package.py \
  --system /path/to/build-output/<image-name>/target/SYSTEM \
  --kernel /path/to/build-output/<image-name>/target/KERNEL \
  --tag <release-tag> \
  --output /path/to/new-update-output-directory
```

The builder reads identity/version stamps directly from SYSTEM. Upload its
`.tar`, `.tar.sha256`, and `butterflyos-update.json` together to that release.
Only promote the release out of prerelease status after qualification. The full
`.img.gz` remains available for first installs and recovery.

## Acceptance checklist before enabling public updates

- Verify the GUI calls the ButterflyOS updater, never the ROCKNIX endpoint.
- Test discovery/no-update/error feedback and user confirmation.
- Reject wrong device, corrupt archive, low battery, and insufficient storage.
- Interrupt downloads and reboot: no partial update should be installed.
- Install between two dated builds and verify kernel/system/device-tree boot.
- Compare games, saves, favorites, artwork, settings, Wi-Fi, SSH, second-card
  files, and the exact-device recovery backup before and after.
- Verify installed version matches the package and no repeat update is offered.
- Test failed-install recovery on a spare card/device; do not advertise rollback.

Offline tests: `python3 tests/butterflyos-update-test.py`.

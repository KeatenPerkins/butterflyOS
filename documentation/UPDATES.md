# ButterflyOS updates

## Current status

The ButterflyOS-specific updater is **implemented in source but not yet included
in a published image or qualified on hardware**. Existing Alpha 2 installations
still require a backed-up reflash. Do not use their inherited update option to
install a generic ROCKNIX release.

## Planned user experience

Once an updater-enabled image and a newer qualified update package are released:

1. Save and exit any running game or Butterfly Link session.
2. Back up important saves and export your device's recovery backup.
3. Connect to Wi-Fi, charge to at least 50%, and connect front-port power.
4. Enable Advanced Mode if Updates & Downloads is hidden. Open
   **Start → Updates & Downloads → Start Update**.
5. Confirm the offered version. The updater downloads the official ButterflyOS
   package and checks its size, SHA-256, device identity, and internal checksums.
6. Restart when the verified package is ready. Do not remove the OS card or
   disconnect power during installation.
7. After boot, check your games, saves, settings, and artwork.

The inherited boot installer replaces OS-card kernel/system files and updates
SD boot device trees. It does not reformat the storage partition. Games, saves,
media, settings, and artwork are intended to remain intact. This preservation
still needs an end-to-end device test before public availability.

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

Use the completed build's matching `.system` and `.kernel` files, not files from
different builds. With `unsquashfs` installed on the build computer:

```sh
python3 scripts/butterflyos-update-package.py \
  --system target/<image-name>.system \
  --kernel target/<image-name>.kernel \
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

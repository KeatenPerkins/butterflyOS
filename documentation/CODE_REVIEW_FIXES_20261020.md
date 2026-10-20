# Safety review fixes for the next test image

Implemented after the October 20 focused review:

- The boot installer checks boot-partition remounts and image writes, reads back
  written files for comparison, and checks boot-file updater failures. On failure
  it stops installation, retains the staged package and `install-error.log` under
  `/storage/.update`, and opens the boot diagnostic shell. Exiting that shell
  does not continue cleanup or announce a successful update. The initramfs enables
  the comparison and bounded-read utilities used by these checks.
- Bdex startup allows SQLite to recover a hot rollback journal while holding the
  existing exclusive writer lock, then performs the normal integrity and snapshot
  checks. Validation opens existing files without creating missing databases.
  Backup validation and web viewing remain read-only.
- Blink ordinary copies, swaps, and generation conversions retain input hashes
  during preparation and reject inputs that change during preparation or before
  commit. Originals are checked again after creating backups. Gifts and save
  events also require their destination fingerprint at commit; old sessions with
  missing fingerprints must be prepared again.
- Suspend diagnostics retain the latest 20 completed successful cycles and 10
  failed/incomplete cycles, plus the active cycle. Manual reports and unrelated
  directories are untouched. Retention runs before a new cycle records its data.

The first update installing these changes still runs through the previously
installed boot updater. In-place boot-file replacement remains vulnerable to a
power loss; these changes detect failures and preserve recovery material but do
not provide A/B update slots. Blink hash checks do not lock out unrelated external
save writers, and a two-save swap is still not atomic across both files.

Host validation: 81 passed, 3 optional Bdex fixture cases skipped. This includes
11 new regression tests covering interrupted database recovery, stale Blink
copies/swaps/conversions/gifts/events, failed or incorrect image writes,
installation stopping before cleanup/reboot, and diagnostic retention. Existing
Bdex, sprite refresh, update staging, Save Backup, and simulated suspend suites
also passed. Shell syntax and Git whitespace checks passed.

Before release, test a full image on the local test device: successful update,
Bdex reopen/import/export, Blink copy/swap/gift, and lid sleep/wake. No image was
built or deployed as part of this code change.

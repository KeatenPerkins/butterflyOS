# Save Backup and Pokémon Bank plans

Recorded October 18, 2026. Historical design and qualification record; the user
guides are [Save Backup](SAVE_BACKUPS.md) and [Bdex](BDEX.md).

**Current status:** both features passed the user's local device test checklist.
The full 20261018 image passed its build/integrity checks. A final local rebuild
is authorized with the updated Bdex artwork and the live-tested Refresh sprites
option. No public release has been authorized by this record.

## Butterfly Save Backup — initial implementation

Automatic backups are **off by default**. The menu location is
**Start → System Settings → Hardware → Automatic Save Backup**.

With two prepared, writable SD cards present:

- Copy ordinary save files from each card to the **other card**. This gives each
  original a copy on a physically separate card.
- Store copies outside the games directory, under
  `ButterflyOS Save Backups/<source-card UUID>/<system>/<original filename>/`.
  Each original filename becomes a directory containing dated, SHA-256-identified
  `.backup` files. To restore manually, copy a chosen snapshot back under the
  original filename while the game is closed; preserve the current save first.
- Keep saves with identical names on different cards independently. Never select
  a winner by modification date, merge progress, or overwrite either original.
  Card UUIDs keep histories separate when cards are swapped.
- Check every five minutes, starting three minutes after timer activation
  (boot or enabling the option). Files must have
  been unchanged for at least two minutes. Recheck file identity, size and
  timestamps during reading; skip files that changed during the read.
- Detect content changes by SHA-256, rather than relying on dates. Keep up to five
  versions of each save. Verify and flush a new copy before pruning old versions.
- Leave at least **10% of the destination card's total capacity available** after
  a copy. If space is insufficient, skip the copy and retain existing backups.
  This reserve applies to both cards.
- Require distinct, mounted SD partitions with supported writable filesystems
  and a `roms` directory. Skip mirrored symlinks. Never create a backup on an
  absent card's empty mountpoint.
- Disabling stops future copies and retains existing backups. No automatic restore
  or synchronization back to game saves.

Initial scope: nonempty `.srm`, `.sav`, `.rtc`, `.eep`, `.fla`, `.sra`, `.mcr`,
`.mcd` files up to 32 MiB within each physical card's `roms` tree. BIOS, hidden
folders, screenshots, artwork and `savestates` folders are excluded. Save states,
standalone-emulator saves outside `roms`, and game-specific directory saves are
**not covered yet**. A file snapshot is not emulator-aware validation: save and
exit the game before depending on a backup, particularly for multi-file saves.
Backups protect against a card failure, not loss of the entire device.

Development commands: `butterflyos-save-backup.py enable`, `disable`, `status`,
`run`. `status` reports the last pass's copied/unchanged/skipped/space-reserve/error
counts. Service details are available through
`journalctl -u butterflyos-save-backup.service`.

Completed checks and remaining work:

- [x] Backend, periodic service, off-by-default settings patch and package wiring.
- [x] Local tests: duplicate names, backward/equal source timestamps, retention,
  insufficient space, failed verification, symlink exclusions, absent/duplicate
  mounts, and disabled operation.
- [x] Compile/test the settings switch on the local test device in the
  rebuilt image: enable/disable, leave/reopen the menu, reboot, and verify that
  disabled operation creates no new backups while retaining existing ones.
- [x] Add user documentation for backup behavior and manual restoration.
- [x] Verify real ext4/exFAT cross-card copies, same-name separation, five-version
  retention, unchanged-file detection, original-save hashes, enable/disable and
  automatic timer activation on the local test device.
- [x] Verify automatic backups after fresh in-game saves.
- [ ] Verify removal/reinsertion, swapping cards, reboot persistence, and backups
  after Blink edits.
- [ ] Measure scan duration and power impact with a large game collection.
- [ ] Audit remaining standalone-emulator save locations and multi-file formats.
- [ ] Future improvement: controller-friendly status/restore interface. The
  current release uses the documented manual restoration process.

## Bdex (Pokémon Bank) — Gen 1–3 implemented and live-tested

- Separate tool that copies Pokémon from selected Gen 1–3 save files into an
  off-game collection; original saves remain intact.
- Preserve full native Pokémon records, generation, trainer identity and source
  provenance. Do not deduplicate solely by species or personality value.
- Browse by generation/species; show shiny status where applicable, moves, held
  items, eggs, and a clearly defined missing-species checklist.
- Reuse Blink's validated save-reading and copy-to-PC-box paths for
  exporting to supported games. Preserve existing generation-transfer rules.
- Use user-provided matching ROMs for assets; bundle no ROMs, saves or sprite
  caches. Define egg and cross-generation collection counting explicitly.
- Back up the database consistently using SQLite's backup API if SQLite is
  chosen; never copy a live database file blindly.

## Pokémon Bank local web viewer — implemented, live endpoint checks passed

- Optional, read-only, password-protected local-network viewer, off by default.
- View the same collection and detail fields from a browser on the same network.
- No save editing, Pokémon import/export, or database mutation through web routes.
- Device must be awake and connected. Load artwork only when needed; stop the
  service when disabled. Authentication, rejected write methods and private-file boundaries pass local tests.

The local device test checklist passed for Save Backup, Bdex Gen 1–3 and the
read-only web viewer. The new Refresh sprites action also passed live testing.
Full-image integration passed in 20261018; the final rebuild includes the
subsequent artwork and refresh changes. Collection data lives in `/storage/bdex`.
Ordinary Save Backup does not include it. Shared ROM caches are separate,
rebuildable user data; no ROMs, saves or extracted caches are bundled.

The following qualification notes describe the earlier development setup, before
the complete image replaced the private helper/service overrides.

### Live-test qualification — October 18, 2026

The local test device runs stable build `20261016`, with a writable 56 GiB ext4
OS partition and 58.2 GiB exFAT game partition. Both have more than 10% free.
Disposable same-name files were tested in both directions; each retained five
verified versions, and an unchanged rerun skipped the copy. Test files were removed.
All four ordinary saves found on the OS card were then backed up and verified by
SHA-256. Original hashes remained unchanged. No existing ordinary saves were found
on the second card. An automatic follow-up pass skipped all four unchanged saves
with zero errors; the five-minute timer is active. Full save inventory took about
0.42 seconds. This does not establish worst-case scan or power cost.

The device lacks `findmnt`; the helper now reads `/proc/self/mountinfo` directly.
Local tests cover that parser, including escaped paths and read-only mount flags.

For this test only, the helper lives under
`/storage/.config/butterflyos/save-backup/live-test/`, with service/timer overrides
in `/storage/.config/system.d/`. Backups are enabled on the test device; the
packaged feature remains off by default. The new Hardware switch requires a
frontend rebuild and has not been tested on the device yet. Remove the local
service/timer overrides before qualifying the packaged units, so they do not
mask a future installed version. Private hashes and reports are stored locally
under `Documents/ButterflyOS-Save-Backup-Live-Test`, outside the repository.

The follow-up in-game test also passed: automatic runs discovered a new
Castlevania: Aria of Sorrow save and a changed Pokémon Emerald save. All five
current saves match their latest backups by SHA-256. Emerald has two distinct
versions, and its baseline snapshot is preserved. A later pass skipped all five
unchanged saves with zero errors. The private report is `after-game-test.json`
in the local live-test directory.

### Bdex identity policy — updated October 18, 2026

Exact native-record duplicates are blocked across all save files, games, cards
and slots, including duplicates within one selection and copies in Trash. The
earlier option to override duplicate rejection was removed. Distinct native records of a species remain
separate. Existing prototype duplicates are consolidated only after a checked
backup, keeping the oldest active copy (or oldest trashed copy) and its combined
history. A SQLite unique index enforces the rule. This supersedes the earlier
proposal to allow intentional exact-copy imports.

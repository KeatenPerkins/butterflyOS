# Save backups and restoring progress

**Next release feature; not included in the v1.1.0 stable download.** Backend,
menu and live device checks have passed. The next image includes this feature;
both cards are required and the setting remains off by default.

## Turn automatic backups on or off

Open **Start → System Settings → Hardware → Automatic Save Backup**.
The feature is **off by default**. Turn it on to start keeping backup copies.
Turning it off keeps the backups you already have.

You need two prepared SD cards, both mounted and writable. If you need to prepare
the second card, see [Quick Start](QUICK_START.md#optional-second-game-card).
Formatting a card erases it; do not format a card that already contains files
you want to keep. **Tools → SD Card Info** shows each card's space and mount status.

## How it works

The OS card is the card ButterflyOS boots from. The second card is the optional
game card. Each card's saves are copied to the **other card**, keeping originals
and backups on separate cards:

| Original save location | Backup location |
| --- | --- |
| OS card | Second card → `ButterflyOS Save Backups` |
| Second card | OS card → `ButterflyOS Save Backups` |

The feature checks for changes every five minutes while the device is awake,
starting about three minutes after boot or enabling the option. It skips files changed within the last
two minutes. **Save inside your game, exit the game, and leave the Flip awake
for about eight minutes** to allow the next check to finish. Backups do not run
while the device is asleep or powered off. It does not save your current game
for you.

- Keeps up to **five versions per save file**. Unchanged files do not create
  extra versions. A new copy is verified before older versions are removed.
- Leaves at least **10% of the destination card's total capacity free**. If there
  is not enough space, it skips that copy and keeps existing backups. This rule
  applies to both cards.
- If the second card is absent or either card is read-only, it waits until both
  cards are usable. It does not require Wi-Fi or an online account.
- If the same game has saves on both cards, **both are backed up separately**.
  It never chooses a winner by date, merges progress, or restores over a save
  automatically.

The first version covers ordinary `.srm`, `.sav`, `.rtc`, `.eep`, `.fla`, `.sra`,
`.mcr`, and `.mcd` files within each card's `roms` folder, up to 32 MiB per file.
Empty files, hidden folders, BIOS and save-state folders are skipped. **Save
states are not backed up**, and some standalone emulators store saves outside
these locations. Games, artwork and settings are not included. Save normally
and exit before relying on a backup; copying a file cannot validate your
in-game progress or guarantee consistency across a game's multiple save files.

Keep important backups on a PC or another drive too. Two cards in one device
cannot protect against losing the whole device, and formatting a card erases
any backup stored on it.

## Find a backup

The folder layout is:

```text
ButterflyOS Save Backups/
  <source-card ID>/
    gba/
      My Game.srm/
        <version-number>-<checksum>.backup
```

The source-card ID identifies the card the original came from. It keeps saves
separate when cards are swapped. The system folders match the original save's
location under `roms`; any additional subfolders are preserved too.

The long filenames distinguish versions and identify their contents. Within
one save's folder, sorting filenames from largest to smallest puts the newest
backup first. You can also use the file browser's modified-date column. Each
`.backup` file contains the original save data; it is **not a ZIP archive**.

For Windows users, the easiest way to reach both cards is
[Web File Transfer](TRANSFERRING_GAMES.md#option-1-web-file-transfer):

1. Connect the Flip and your computer to the same network. Set a device password
   and enable Web File Transfer under **Settings → Network Settings**.
2. Open its displayed address in a browser. Log in as `root` with your device
   password.
3. Choose **All Storage**. For backups of second-card saves, open
   `ButterflyOS Save Backups`. For backups of OS-card saves, open
   `games-external` → `ButterflyOS Save Backups`.
4. Open the source-card ID, system folder, and original save filename folder.
   Download the version you want to restore.

You can also use [SFTP](TRANSFERRING_GAMES.md#option-4-sftp-or-scp-over-ssh):
OS-card backups are at `/storage/ButterflyOS Save Backups/`; second-card backups
are at `/storage/games-external/ButterflyOS Save Backups/`.

If using a card reader instead, shut the Flip down fully before removing a card.
Windows normally reads an exFAT second card, but cannot read the OS card's ext4
STORAGE partition directly. Do not accept a Windows prompt to format it. USB
Gadget File Transfer exposes the ROMs folder, so use the web interface or SFTP
to reach backup folders outside it.

## Restore a save

Restore is manual in this first version. For example, to restore `My Game.srm`:

1. **Exit the game completely** and close Blink if it is open. Leave
   the Flip at its main menu. Turn Automatic Save Backup off temporarily.
2. Download the current `My Game.srm` to a safe folder on your PC before
   replacing it. Keep this copy separate from the backup you want to restore.
3. Download your chosen `.backup` file. Rename this downloaded copy to the
   **exact original save filename**, including its extension: `My Game.srm`.
   Do not leave `.backup` on the end or change `.srm` to `.sav`.
4. Upload the renamed file to the original save's folder on the correct card.
   For an OS-card GBA save, that is typically **Games → gba**, or
   `/storage/roms/gba/`. For a second-card save, use **Second Game Card → gba**,
   or `/storage/games-external/roms/gba/`. Preserve any subfolders shown in the
   backup path. Replace the existing file only after keeping the PC copy.
5. Launch the game using **Start Game**, rather than resuming an old save state
   or auto-save state. Then use the game's own Continue/Load option and check
   your progress. A save state can bring back older progress and later overwrite
   the restored in-game save.
6. Once you are satisfied, turn Automatic Save Backup back on if desired.

Some games have companion files, such as `.rtc` clock data. Preserve the current
copies and restore the appropriate companion backups too when needed. Versions
are kept per file, not as a coordinated snapshot of all files for a game.

If both cards have the same game/save name, select the card containing the save
you intend to use. The combined game library gives OS-card duplicates priority;
restoring a second-card copy does not make the game use it instead.

If the game does not see the save, check the filename, extension, destination
card, and selected emulator. Use the same game revision and core where possible.
A gamelist refresh does not convert saves or load a restored file into a game
that is already running.

## If no backup appears

Check that the option is enabled, both cards are writable, and both have enough
free space. Save and exit the game, keep the device awake for about eight
minutes, and check again. A file with unchanged contents does not create another
version. Unsupported save formats or locations need a separate manual backup.

## Bdex is backed up separately

This feature copies supported ordinary game-save files. It does **not** copy
Bdex's collection databases, their archived source snapshots or sprite caches.
In Bdex, use **Options → Database backup** for each generation and download the
completed backups to a PC. See [Bdex backup and recovery](BDEX.md#back-up-or-recover-the-collection).

A game-save backup and a Bdex backup restore different things: restoring a game
save changes that game's progress, while recovering a Bdex database changes the
stored collection. Neither automatically updates the other.

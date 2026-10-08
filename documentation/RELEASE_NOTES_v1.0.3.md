# ButterflyOS v1.0.3 — Butterfly Link events and safer lid shutdown

Stable release for **Miyoo Flip V2**, with updater build ID **20261010**.
This is the exact local image approved after smoke checks and live device tests.

## Butterfly Link

Open **Tools → Butterfly Link → Local transfer**, then choose **Gen 1** or
**Gen 2**. Games are listed first, with the applicable gifts and events below.
Exit your game before editing its save, choose a free PC-box slot, review the
preview, and use Commit to apply a change with a backup.

- **Gen 1 Gifts:** Mew, Surfing/Flying Pikachu, Dragon Rage Magikarp, and
  Pay Day Fearow/Rapidash, for qualified English Red/Blue/Yellow revisions.
- **Stadium Gifts:** Amnesia Psyduck and eight Gym Leader Castle gift equivalents.
- **Crystal Events:** enable or replay the native GS Ball/Celebi quest, or
  replay the native Odd Egg delivery. The Celebi quest retains Kurt's normal wait.
- **Gen 2 Gifts:** Mew, plus Celebi for Gold/Silver; Crystal uses its native quest.
- **Stadium 2 Gifts:** Baton Pass Farfetch'd and Earthquake Gligar.
- **Mystery Eggs:** fifteen special-move egg recipes delivered as eggs to hatch.
- **PCNY Gifts:** separate menus for 104 special-move eggs and 16 shiny adult gifts.
- **Gen II → III copies** preserve held items with verified Gen III equivalents.
  Unmatched items are cleared on the destination copy. The original Pokémon
  and item remain unchanged.

Gifts are generated equivalents using the player's trainer identity; they do
not reproduce every historical distribution field. Transfers use PC-box Pokémon
and edit saves; they do not emulate a cable or provide battles. Sprites are
derived from the user's matching ROM. No Pokémon ROMs, saves or sprite cache
are bundled. See the [Butterfly Link guide](BUTTERFLY_LINK.md) for compatibility
and event details.

## Game launch and save states

The **Save State Manager** now uses the full screen, with the game name and
available cover art at the top. Start Game and the applicable auto-save choice
have room for readable labels. The three newest save states appear first;
older states remain accessible through More Save States.

## Optional lid shutdown

Open **Start → System Settings → Hardware**:

- **Lid-Closed Shutdown:** Off by default, or 15, 30 or 60 minutes. Opening the
  lid cancels the timer. Closing the lid still blanks the display rather than
  entering hardware suspend.
- **Save Game Before Lid Shutdown:** Off by default. When enabled for a
  supported RetroArch session, the timer requests an auto-save, verifies it,
  exits the game normally, and uses the normal shutdown path to save metadata.
  The previous auto-save is backed up; numbered save slots are unchanged.

If saving fails, an update is in progress, or a game/tool cannot use this save
flow, shutdown waits. Unsupported standalone emulators remain running. Continue
using normal in-game saves; save states are not guaranteed to survive core changes.

## Installation and recovery

The installation and Quick Start guides now begin with an illustrated
**ATTENTION** section explaining the preloader, why setup changes boot behavior,
and why users should export their recovery backup to a PC before reflashing.
Restoring the original preloader is strongly recommended when switching to
another operating system that may expect Miyoo's original boot arrangement.

RetroAchievements remains at **Settings / Start → Game Settings →
RetroAchievements Settings**, outside Advanced Mode. Existing FPS/audio fixes,
PortMaster support, game artwork and storage tools are retained. Emulator
defaults and battery reporting are unchanged in this release.

## Download or update

For a new installation, download **ButterflyOS-v1.0.3-Miyoo-Flip-V2.img.gz** and
its matching `.sha256` file. Read the
[installation and recovery guide](BUTTERFLYOS_INSTALL_AND_RECOVERY.md) first.

For an existing installation, open **Start → System Settings → Update
ButterflyOS**. Keep at least **3 GB free on the OS card**, connect power and
Wi-Fi, wait for download and verification to finish, then restart to install.
Confirm build **20261010** afterward. Normal updates retain games, saves and
scraped artwork on the storage partition. Reflashing a card erases it, so export
recovery files and back up personal files first.

See [How to update](UPDATES.md#how-to-update) for detailed instructions and
older-build migration requirements. The `.tar` asset is the on-device update
package; the `.img.gz` asset is for flashing a card.

## Validation

The full build exited successfully. Checks passed for image/update hashes,
GPT/FAT/ext4, SYSTEM/KERNEL checksums and matching payloads, updater identity,
packaged event scripts, enabled lid service, AArch64 save helper and new menu
labels. The flashed card matched the complete raw image on read-back, and the
user approved the full build after live testing. The captured source changes
match the committed source; the promoted image bytes are unchanged.

All 23 lid-shutdown checks pass. Butterfly Link save/event checks and recorded
live tests cover the implemented gifts and Crystal flows. This does not qualify
every ROM revision, emulator or achievement mode. Silver Celebi, Yellow's beach
minigame and in-game held-item conversion retain the limits recorded in
[Known Issues](KNOWN_ISSUES.md).

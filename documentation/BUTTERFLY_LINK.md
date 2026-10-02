# Butterfly Link

Butterfly Link copies or exchanges Pokémon between selected emulator save files.
Open **Tools → Butterfly Link**, from the home screen or **Start → Tools**.
Use the D-pad to navigate, **A/Start** to select, and **B/Menu** to go back.

It works locally on one Flip or between two Flips on the same Wi-Fi network.
It edits saves; it does not launch games, emulate a cable, or provide battles.
Older netplay and USB-link plans describe historical experiments.

Keep an independent backup, exit the emulator before opening Butterfly Link,
and do not have the same save open in another application during a transfer.

## Supported games and transfer directions

Known English retail layouts are supported for Red, Blue, Yellow; Gold, Silver,
Crystal; and Ruby, Sapphire, Emerald, FireRed, LeafGreen. Other languages,
ROM hacks, and unrecognized revisions are not generally qualified.

| Source → destination | Local | Remote Wi-Fi | Limits |
|---|---|---|---|
| Gen I → Gen I | Trade or copy | Trade or copy | PC-box Pokémon |
| Gen II → Gen II | Trade or copy | Trade or copy | PC-box Pokémon |
| Gen III → Gen III | Trade or copy | Trade or copy | PC-box Pokémon; Trade requires matching save-format families |
| Gen I → Gen II | Copy | Copy, qualification pending | Time Capsule conversion; remote Yellow → Crystal persistence failure under investigation |
| Gen II → Gen III | Copy | Copy | One-way conversion; held items cleared |
| Gen II → Gen I | Unavailable | Unavailable | No reverse Time Capsule conversion |
| Gen III → earlier generations | Unavailable | Unavailable | No reverse conversion |

The current Gen III Trade helper refuses different save-format families:
Ruby/Sapphire, Emerald, and FireRed/LeafGreen are separate families. Thus
Ruby ↔ Sapphire and FireRed ↔ LeafGreen can trade, while Ruby ↔ Emerald
Trade is refused. Gen III Copy does not have that same-format restriction.
Do not interpret the table as qualification of every Gen III game pairing.

Gen II → III is a Butterfly Link conversion, not an original-game cable feature.
Compatible identity/training data is converted; generation-specific fields need
newly derived values. **All held items are currently cleared**, even if a Gen III
counterpart exists. The app rejects Pokémon it cannot identify safely from the
source ROM. It does not provide an unrestricted species, move, or item editor.

**Trade** exchanges two boxed Pokémon and changes both saves. **Copy** adds the
source Pokémon to a free destination PC slot; only the destination changes.
Party Pokémon are preview-only. Gen I/II copies append to the next valid empty
position in the selected box.

Use ordinary battery saves (`.srm` or `.sav`), not emulator save states.
Save through the game's own menu and exit cleanly before a transfer. To check
the result, load the game's saved progress rather than an older emulator state,
which can contain older save data.

## Local workflow

1. Choose **Local Transfer** and a generation or cross-generation copy mode.
2. Choose the source save and check its game, trainer, and card location.
3. Choose its matching ROM if prompted; the app prepares or reuses a sprite/name cache.
4. Browse the party/boxes, open a PC box, and select a Pokémon.
5. Choose Trade or Copy where available.
6. Choose the compatible destination save and its Pokémon for Trade, or a free PC box for Copy.
7. If offered, choose whether the eligible Pokémon should evolve.
8. Review the protected copies and confirm the action, or cancel.
9. Read the completion result and inspect the destination game's PC.

The normal flow commits at final confirmation. There is no extra main-menu
Commit step after a successful transfer.

## Remote workflow

1. Connect both Flips to the same Wi-Fi and open Butterfly Link; SSH is not required.
2. The sender chooses **Remote Transfer → Host**, then a transfer mode.
3. The other device chooses **Remote Transfer → Join** and selects the host.
4. The host accepts the request and selects its save, boxed Pokémon, and action.
5. The joiner chooses its compatible save and receiving Pokémon or free PC box.
6. Both devices approve the review before prepared saves are committed.
7. Read the results on both devices and check the destination game(s).

Save working copies cross the LAN; **ROMs do not**. Each device needs the
matching ROM for its own selected save, not its friend's ROM. Equal ROM hashes
are not required. Guest-network isolation or blocked local broadcasts can
prevent discovery. This save-transfer UI has no manual-IP entry.

Local evolution prompts are not implemented in the remote workflow.
Remote trade evolution must not be advertised as automatic.

## Evolution and artwork

Local transfers, including eligible copies, can offer **Keep / Evolve** for
supported trade evolutions such as Kadabra, Machoke, Graveler, and Haunter.
Selected held-item rules exist where compatible ROM-derived item names are
available; every trade evolution and Everstone rule is not yet qualified.
Evolution edits the protected destination copy. Recognized ordinary species
names update; player-assigned nicknames are preserved.

Sprites are extracted from the user's matching ROM and cached by its SHA-256.
Unknown layouts are refused. Gen I front sprites are monochrome; Gen II/III
can show normal/shiny artwork. Gen I/II sprites have a light-grey backing.
Some move/item details may retain numeric IDs when name lookup is unavailable.
No Pokémon sprite cache, ROM, or save is bundled in the image.

## Backups and failure handling

Working copies and pre-commit backups remain under:

```text
/storage/.config/butterflyos/save-trade/sessions/
```

The UI log is:

```text
/storage/.config/butterflyos/logs/butterfly-link.log
```

Copy important saves off-device before reflashing; backups on the OS card are
erased too. There is no one-button transaction-recovery browser in the current app.

Cancellation before commit leaves originals unchanged. Remote commits occur
separately on each device; interruption after one commit can leave a one-sided
result. Inspect both saves and preserve session backups before repeating a trade.

The October 2 rebuild verifies the committed file hash and uses fresh timestamps.
These checks do not establish that loading an emulator state or an in-game
redundant save block will preserve the file. In the October 2 Yellow → Crystal
remote test, the prepared file contained Pikachu and the joiner logged a commit,
but Crystal's live save no longer contained it after the game ran. The cause was
an edited active PC box that had not been synchronized to the banked box the
game loads on Continue. Opening the PC after the initial fix exposed a second
format error: converted names lacked the game's required 0x50 terminator.
Both source fixes pass expanded regression tests and are deployed live, but
need an in-game PC-open/persistence retest and the next image.
Same-generation remote trade/copy and remote Gen II → III
copy passed user testing. See [current build status](CURRENT_BUILD_STATUS.md).

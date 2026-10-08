# Butterfly Link

<img src="assets/butterfly-link.png" alt="Butterfly Link app icon" width="128">

## What is Butterfly Link?

Butterfly Link is ButterflyOS's built-in Pokémon **save-transfer application**.
It lets you select Pokémon from an existing game's PC boxes and copy or exchange
them with another compatible save, without entering the game's Cable Club.
The receiving Pokémon is available when you next load the destination game's
saved progress and open its PC.

You can use it between two saves on **one Flip**, or between **two Flips over
local Wi-Fi**. It is not an emulator or live multiplayer service: it does not
simulate a link cable, require both games to be running, or support battles.
No internet service or SSH login is required for its remote-transfer workflow.

### What can it do?

- **Trade:** exchange one boxed Pokémon from each save. Both saves change.
- **Copy:** add a boxed Pokémon to the receiving save while keeping the source
  Pokémon. The receiving box needs space; no Pokémon needs to be sent back.
- **Local transfers:** select both saves on the same device. Saves may be on
  the OS card or a mounted second game card.
- **Remote transfers:** host or join a session on the same Wi-Fi network, select
  compatible saves on the two devices, and approve the transfer on both.
- **Same-generation transfers:** trade or copy within Gen I, Gen II, or Gen III,
  subject to the compatibility restrictions below.
- **Cross-generation copies:** copy Gen I Pokémon into Gen II, or convert and
  copy Gen II Pokémon into Gen III. These are one-way copies, not exchanges.
- **Optional local trade evolutions:** choose Keep or Evolve for supported
  Pokémon when the app offers it. Remote transfers do not offer this prompt.
- **Browse your collection:** preview party Pokémon and PC boxes, with sprites
  and available Pokémon details such as level, moves, nature, and held item.
  Available fields and name lookup vary by generation and ROM.
- **Prepare protected working copies:** review a transfer before confirming it,
  with pre-commit backups retained for troubleshooting or manual recovery.

### What does it need?

- A supported game's ordinary in-game save (`.srm` or `.sav`). Emulator save
  states are not supported input files.
- Your matching, legally obtained ROM for sprite/name extraction and conversion
  checks. ButterflyOS does not include Pokémon games, artwork, or saves.
- Pokémon stored in PC boxes. Party Pokémon can be viewed but cannot currently
  be traded or copied directly; deposit them in a box and save first.
- For remote transfers, another Flip running a compatible Butterfly Link build
  and reachable on the same local Wi-Fi network.

For example, you can copy a boxed Pikachu from Yellow into Crystal without
removing it from Yellow, or exchange boxed Pokémon between Ruby and Sapphire.
You cannot copy a Gen III Pokémon back into Gold, or use Butterfly Link to battle
a friend. It is not a general-purpose Pokémon editor.

### Gen I event gifts (next build; unreleased)

The Gen 1 menu lists detected game saves first. Select a game for the normal
trade/copy flow; Gen 1 Gifts and Stadium Gifts appear below the game list.

Open **Tools → Butterfly Link → Local transfer → Gen 1 → Gen 1 Gifts** to add a generated level-5
Mew, Surfing/Flying Pikachu, Dragon Rage Magikarp, or Pay Day Fearow/Rapidash
to a free PC slot. This first version accepts only the
verified English retail Red, Blue and Yellow ROM revisions; other revisions,
languages and modified ROMs are refused.

Exit the game and make an independent backup first. Select the destination
save, gift and free PC slot, review the preview, then choose **Add Gift**.
All six gifts arrive at level 5. Pay Day replaces Rapidash's fourth starting
move, Growl; the other special moves use an empty starting-move slot.
Cancel leaves the original unchanged. Commit retains a pre-write backup and
refuses a save that changed after preparation. Load the game and withdraw the
gift from the selected box.

These are generated equivalents using your trainer identity, not replicas of
original official distributions. Data and artwork come from your matching ROM;
no donor records or Pokémon game assets are bundled. No story flags or map
encounters are changed. Yellow's Surfing Pikachu uses the player identity
required by its beach checks, but the minigame still needs an in-game test.
The next build also provides **Local transfer → Gen 1 → Stadium Gifts**: Amnesia
Psyduck, Bulbasaur, Charmander, Squirtle, Hitmonlee, Hitmonchan, Eevee, Omanyte
and Kabuto. These also arrive at level 5 with your trainer identity and
ROM-derived starting moves; Psyduck additionally knows Amnesia. They do not
reproduce Stadium distribution levels, original trainer metadata or all
historical movesets, and do not mark Stadium challenges as completed.
See the [event inventory and validation notes](BUTTERFLY_LINK_GEN1_EVENTS_PLAN.md).

### Gen II event gifts (next build; unreleased)

The **Local transfer → Gen 2** menu lists game saves first, then **Gen 2 Gifts**,
**Stadium 2 Gifts**, **Crystal Events**, **Mystery Eggs** and **PCNY Gifts**. Gen 2 Gifts offers a generated level-5
Mew with Pound. For Gold/Silver saves it also offers a level-5 Celebi with
Leech Seed, Confusion, Heal Bell and Recover. Crystal retains its native
Celebi quest rather than this boxed gift. Stadium 2 Gifts offers level-5 Farfetch'd with Baton Pass,
Swords Dance, Agility and Slash holding Gold Berry, and Gligar with Earthquake,
Poison Sting, Counter and Wing Attack holding MysteryBerry.

**Mystery Eggs** offers fifteen actual egg recipes, beginning with AncientPower
Bulbasaur, Crunch Charmander, Submission Totodile, Night Shade Hoothoot and Sing Pichu. Add one to
a free PC slot, withdraw it and walk with it in your party to hatch it normally.
The preview shows the hatchling. Hatch counters come from your ROM; DVs are
random, including the normal shiny chance. Eggs are not registered in the
Pokédex before hatching, and Blink requires hatching before transfer selection.
The user confirmed all fifteen egg recipes work in-game in Crystal on .17. These are generated equivalents, rather than
an emulation of the Japanese distribution hardware.
The additions are Petal Dance Psyduck, Chikorita, Pichu, Cleffa, Igglybuff and
Smoochum; Swift Cleffa; Belly Drum Wooper; Encore Phanpy; and Metronome Smoochum.
Campaign repeats share one recipe; distinct special moves remain separate choices.
See the [documented campaign recipes](https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_event_Pok%C3%A9mon_distributions_in_Generation_II).

These are player-owned generated equivalents, not original distribution records.
The hatched gifts use your trainer name/ID, random DVs, no stat experience,
initial friendship and ROM-derived names, growth rates and move PP. Eggs use
the native hatch counter in place of initial friendship. Only the qualified English
retail Gold, Silver and Crystal revisions are accepted. No Stadium completion
flags or story progress are changed.

Exit the game, select the gift and a free PC box, review the Pokémon preview,
then explicitly **Add Gift**. The writer appends to the next empty slot and
refuses occupied/full boxes. Cancel leaves the original unchanged; Commit
retains a verified original backup and refuses a save changed since preparation.
Both SRAM box representations are updated when adding to the current box;
native primary/backup checksums and gift Pokédex bits are maintained.

Automated gift checks cover all fourteen boxes across all three games. The user
confirmed all three gifts work in Crystal on .17. Gold/Silver have automated
and disposable-save device coverage. The Celebi gift passed user testing in
Gold on .17, including withdrawal and save/reload persistence; Silver Celebi
and broader Gold/Silver gift gameplay still need qualification.

### PCNY gifts (catalog expansion; unreleased)

**Local transfer → Gen 2 → PCNY Gifts** now offers 104 actual eggs and 16 shiny adult gifts.
The first batch includes:
Zap Cannon Squirtle, Growth Eevee, Lovely Kiss Snorlax, Hydro Pump Dratini and
Double-Edge Cyndaquil. Review the hatchling, choose a free PC slot and confirm
Add Gift; withdraw and hatch in-game. These are player-owned generated
special-move equivalents. They retain the user's preferred random DVs and
natural shiny chance rather than recreating the historical machine's enhanced
shiny odds. Specifically named shiny adult gifts are guaranteed shiny and use
their documented levels, rather than being eggs. The documented PCNY recipes are implemented except the incomplete non-shiny
Suicune entry; overlapping Mystery Egg recipes
are already offered separately. The first fifteen PCNY eggs passed user testing in Crystal on .17, including
hatching, special moves and save/reload. The second batch was:

| Egg | Special move |
| --- | --- |
| Igglybuff | Mimic |
| Elekid | Pursuit |
| Magby | Faint Attack |
| Tyrogue | Rage |
| Sentret | Dizzy Punch |
| Ledyba | Barrier |
| Spinarak | Growth |
| Chinchou | Light Screen |
| Natu | Safeguard |
| Marill | Dizzy Punch |

The third batch adds ten recipes, all confirmed working by user testing in
Crystal on .17:

| Egg | Special move |
| --- | --- |
| Pichu | Dizzy Punch |
| Pichu | Scary Face |
| Cleffa | Scary Face |
| Igglybuff | Scary Face |
| Marill | Hydro Pump |
| Marill | Scary Face |
| Sudowoodo | Substitute |
| Hoppip | Agility |
| Wooper | Scary Face |
| Elekid | Dizzy Punch |

The remaining documented catalog adds 79 eggs and 16 shiny adults, all
confirmed working by user testing in Crystal on .17. Choose **Special-Move Eggs** (104 recipes) or **Shiny Adult Gifts**
(16 recipes). New eggs append after the first 25 within the egg list. See the [remaining-gift test checklist](BUTTERFLY_LINK_GEN2_PCNY_CHECKLIST.md)
for every addition, levels, testing steps and catalog coverage.

[Historical recipe catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_PCNY_event_Pok%C3%A9mon_distributions_in_Generation_II).

### Crystal Odd Egg replay (unreleased)

Use **Local transfer → Gen 2 → Crystal Events → Odd Egg**. If you have not
received the Odd Egg, Blink reports that it is already available and makes no
save changes. Otherwise review and confirm Replay, then load the ordinary
in-game save and speak to the Day-Care Man **inside** the Day Care on Route 34,
south of Goldenrod, with a free party slot. Save states can restore the old flag.
If the man is outside with an ordinary breeding egg, collect that egg first.
The tool refuses replay while that breeding egg is waiting.

Replay clears only the received-event bit and updates its backup and checksums.
Existing eggs, Pokemon, items, breeding progress and Celebi quest state remain
unchanged. The qualified retail ROM supplies the dialogue, egg choice, Dizzy
Punch movesets, shiny odds and hatching. No donor egg records are bundled.
Automated preservation and protected-Commit checks pass. Native Odd Egg
delivery and replay also passed user testing on .17.
[Native Day-Care script](https://github.com/pret/pokecrystal/blob/master/maps/DayCare.asm).

### Crystal Celebi quest (next build; unreleased)

Open **Local transfer → Gen 2 → Crystal Events**. The development version offers
**Enable** for a quest that has not started and **Replay** to restart its native
GS Ball delivery, Kurt and shrine sequence. Replay keeps existing Pokémon,
including a previously caught Celebi. This accepts only the qualified English
retail Crystal revision; Gold, Silver and modified ROMs are refused.

Save outside Goldenrod Pokémon Center, Azalea Town, Kurt's house and Ilex Forest,
then exit the game. Finish and collect any apricorn work first. Choose the save
and action, review the current quest state, then explicitly **Commit**. Cancel
leaves the original unchanged. Commit retains an original backup and refuses
a save that changed since preparation.

Load the ordinary in-game save rather than a save state. Enter Goldenrod Pokémon
Center and leave through its front door to receive the GS Ball. Take it to Kurt
and follow the game's normal timing and quest progression to Ilex Forest.
The tool changes verified quest state; the game supplies the dialogue,
animation and encounter. It bundles no ROM content or Pokémon records.

Enable and Replay both passed user testing on .17: Goldenrod delivery, Kurt
progression and the shrine encounter. Kurt's waiting timer was cleared manually
for testing; the normal next-day wait is retained in the tool. Automated save,
backup, cancellation and preservation tests also pass. All fifteen documented Japanese Mystery Egg species/moveset recipes are
implemented and passed user testing in Crystal on .17. Odd Egg delivery and
replay also passed user testing. Gold/Silver Celebi and the documented PCNY gifts
are implemented; Celebi passed the user
PC/save/reload test in Gold on .17. All 104 PCNY eggs, 16 shiny adult gifts and the split egg/adult menu passed
user testing in Crystal on .17. Silver Celebi still needs gameplay qualification. Non-shiny Suicune lacks documented recipe data; Gen III events
are not yet implemented.
See [Gen II event scope and validation](BUTTERFLY_LINK_GEN2_EVENTS_PLAN.md).

## Opening Butterfly Link

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
| Gen I → Gen II | Copy | Copy | Time Capsule conversion; banked-box/name fixes included, not every save pairing qualified |
| Gen II → Gen III | Copy | Copy | One-way conversion; verified held-item equivalents preserved in the next build |
| Gen II → Gen I | Unavailable | Unavailable | No reverse Time Capsule conversion |
| Gen III → earlier generations | Unavailable | Unavailable | No reverse conversion |

The current Gen III Trade helper refuses different save-format families:
Ruby/Sapphire, Emerald, and FireRed/LeafGreen are separate families. Thus
Ruby ↔ Sapphire and FireRed ↔ LeafGreen can trade, while Ruby ↔ Emerald
Trade is refused. Gen III Copy does not have that same-format restriction.
Do not interpret the table as qualification of every Gen III game pairing.

Gen II → III is a Butterfly Link conversion, not an original-game cable feature.
Compatible identity/training data is converted; generation-specific fields need
newly derived values. **The next build preserves verified Gen III held-item
equivalents.** Items without a verified equivalent are cleared on the destination
copy. Existing releases through v1.0.2 clear all held items. In every version,
the original Gen II Pokémon and its held item remain unchanged.

The mapping uses explicit item IDs, never the same numeric ID across generations.
Most shared items keep their identity (for example, Leftovers, Everstone and
Metal Coat). Renamed berries use the following equivalents:

| Gen II | Gen III |
| --- | --- |
| Berry | Oran Berry |
| Gold Berry | Sitrus Berry |
| PSNCureBerry | Pecha Berry |
| PRZCureBerry | Cheri Berry |
| Burnt Berry | Rawst Berry |
| Ice Berry | Aspear Berry |
| Bitter Berry | Persim Berry |
| Mint Berry | Chesto Berry |
| MiracleBerry | Lum Berry |
| MysteryBerry | Leppa Berry |

TMs are matched by their taught move, not their TM number. Gen-II-only items
(including Berserk Gene, apricorn balls, Pink Bow and Polkadot Bow), mail,
unsupported TMs, HMs, key items and unused/invalid item IDs are cleared. The tool
does not substitute a merely similar item for a missing one.

Item IDs were checked against the [Gen II reference tables](https://github.com/pret/pokecrystal/blob/master/constants/item_constants.asm)
and the [Gen III reference tables](https://github.com/pret/pokeemerald/blob/master/include/constants/items.h),
including Ruby/Sapphire and FireRed/LeafGreen agreement for mapped IDs. These
tables target the supported retail games; arbitrary ROM hacks are not qualified.
The app rejects Pokémon it cannot identify safely from the source ROM. It does
not provide an unrestricted species, move, or item editor.

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

Remote Yellow → Crystal transfers passed testing, including opening the PC,
saving, exiting, and reopening the game. Same-generation remote trade/copy and
remote Gen II → III copy also passed user testing.
See [current build status](CURRENT_BUILD_STATUS.md).

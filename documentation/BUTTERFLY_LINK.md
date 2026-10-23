# Blink

<img src="assets/butterfly-link.png" alt="Blink app icon" width="128">

**Menu name in the next release: Tools → Blink.** Earlier releases show
**Tools → Butterfly Link**. The existing guide URL remains unchanged.

## What is Blink?

Blink (previously named Butterfly Link) is ButterflyOS's built-in Pokémon **save-transfer application**.
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
  Available fields vary by generation and ROM. v1.1.0 includes these
  inspector improvements:
  The inspector shows English move names for supported Gen I, II, and III
  ROMs. Names are extracted locally from your matching ROM; older sprite-only
  caches are refreshed when needed. Unknown move IDs retain a numeric label.
  Gen II/III held items also show ROM-derived English names on a separate
  inspector line. Unknown items retain their numeric label; Gen I has no held
  items.
- **Prepare protected working copies:** review a transfer before confirming it,
  with pre-commit backups retained for troubleshooting or manual recovery.

### Shared sprite-cache improvement (v1.3.0)

Version 1.3.0 corrects Gen III shiny-palette offsets for Emerald,
Ruby/Sapphire revision 2 and FireRed revision 1. These shared-cache fixes apply
to Blink and Bdex. An older cache rebuilds when its ROM is selected
again; sprite/name data continues to come from the user's ROM.

### What does it need?

**ROM language support:** Blink currently supports the qualified
English ROMs listed below. French, Spanish, German, Italian and Japanese ROM
versions are not supported at this time. A ROM's filename can be in any language;
the GBA ROM picker checks its internal game code, not its filename. Renaming a
non-English ROM does not make it supported. This restriction applies to Butterfly
Link, not to playing those games in an emulator.

From v1.1.0, Gen I/II ROM selection also supports `.zip` archives containing exactly one
`.gb` or `.gbc` ROM. Sprites and move names are read directly from the archive;
manual extraction is unnecessary. Archives with multiple ROMs are rejected.

From v1.0.4, the ROM picker supports uncompressed `.gba` files and `.zip`
archives containing exactly one supported GBA ROM. It reads the game's header
inside the archive; unrelated games are excluded. Sprite generation reads the
ROM directly from the ZIP without extracting archive paths to disk. `.7z`
archives are not supported by this picker yet. LeafGreen revision-1 sprite extraction and swaps between Gen III save families
(including Emerald and LeafGreen) are also fixed in v1.0.4. Press B while
browsing a PC box to return to box selection.

- A supported game's ordinary in-game save (`.srm` or `.sav`). Emulator save
  states are not supported input files.
- Your matching, legally obtained ROM for sprite/name extraction and conversion
  checks. ButterflyOS does not include Pokémon games, artwork, or saves.
- Pokémon stored in PC boxes. Party Pokémon can be viewed but cannot currently
  be traded or copied directly; deposit them in a box and save first.
- For remote transfers, another Flip running a compatible Blink build
  and reachable on the same local Wi-Fi network.

For example, you can copy a boxed Pikachu from Yellow into Crystal without
removing it from Yellow, or exchange boxed Pokémon between Ruby and Sapphire.
You cannot copy a Gen III Pokémon back into Gold, or use Blink to battle
a friend. It is not a general-purpose Pokémon editor.

### Gen I event gifts (v1.0.3)

The Gen 1 menu lists detected game saves first. Select a game for the normal
trade/copy flow; Gen 1 Gifts and Stadium Gifts appear below the game list.

Open **Tools → Blink → Local transfer → Gen 1 → Gen 1 Gifts** to add a generated level-5
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
Version 1.0.3 also provides **Local transfer → Gen 1 → Stadium Gifts**: Amnesia
Psyduck, Bulbasaur, Charmander, Squirtle, Hitmonlee, Hitmonchan, Eevee, Omanyte
and Kabuto. These also arrive at level 5 with your trainer identity and
ROM-derived starting moves; Psyduck additionally knows Amnesia. They do not
reproduce Stadium distribution levels, original trainer metadata or all
historical movesets, and do not mark Stadium challenges as completed.
See the [event inventory and validation notes](BUTTERFLY_LINK_GEN1_EVENTS_PLAN.md).

### Gen II event gifts (v1.0.3)

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
The user confirmed all fifteen egg recipes work in-game in Crystal on the local test device. These are generated equivalents, rather than
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
confirmed all three gifts work in Crystal on the local test device. Gold/Silver have automated
and disposable-save device coverage. The Celebi gift passed user testing in
Gold on the local test device, including withdrawal and save/reload persistence; Silver Celebi
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
are already offered separately. The first fifteen PCNY eggs passed user testing in Crystal on the local test device, including
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
Crystal on the local test device:

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
confirmed working by user testing in Crystal on the local test device. Choose **Special-Move Eggs** (104 recipes) or **Shiny Adult Gifts**
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
delivery and replay also passed user testing on the local test device.
[Native Day-Care script](https://github.com/pret/pokecrystal/blob/master/maps/DayCare.asm).

### Crystal Celebi quest (v1.0.3)

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

Enable and Replay both passed user testing on the local test device: Goldenrod delivery, Kurt
progression and the shrine encounter. Kurt's waiting timer was cleared manually
for testing; the normal next-day wait is retained in the tool. Automated save,
backup, cancellation and preservation tests also pass. All fifteen documented Japanese Mystery Egg species/moveset recipes are
implemented and passed user testing in Crystal on the local test device. Odd Egg delivery and
replay also passed user testing. Gold/Silver Celebi and the documented PCNY gifts
are implemented; Celebi passed the user
PC/save/reload test in Gold on the local test device. All 104 PCNY eggs, 16 shiny adult gifts and the split egg/adult menu passed
user testing in Crystal on the local test device. Silver Celebi still needs gameplay qualification.
Non-shiny Suicune lacks documented recipe data.
See [Gen II event scope and validation](BUTTERFLY_LINK_GEN2_EVENTS_PLAN.md).

### Gen III native island events (v1.3.0)

Native island events are available from v1.3.0. Open **Local Transfer → Gen 3 → Gen 3 Island
Events** and select a save, matching qualified ROM, event, and **Enable** or
**Replay**. Review the preview and choose **Commit**; a verified original backup
is kept. Save normally and exit the game before using this feature. Afterward,
load the ordinary in-game save rather than Auto Resume or a save state.

- **Emerald:** Eon Ticket/Southern Island (Latias or Latios), MysticTicket/Navel
  Rock (Lugia and Ho-Oh), AuroraTicket/Birth Island (Deoxys puzzle), and Old Sea
  Map/Faraway Island (Mew chase). Use the Lilycove City ferry.
- **FireRed/LeafGreen revision 1:** MysticTicket and AuroraTicket. Use the
  Vermilion City ferry. These and Emerald require the qualified English ROMs.
- **Ruby/Sapphire revision 2:** Eon Ticket/Southern Island. Ruby encounters Latias;
  Sapphire encounters Latios. Use the Lilycove City ferry. This extension has
  automated coverage and user-confirmed native encounters on the local test device.
- Normal postgame ferry requirements are preserved. Ruby/Sapphire key items use
  their own unencrypted save layout; the normal roaming Pokemon is kept.

Replay keeps previously caught Pokemon and resets only the selected island's
encounters; MysticTicket replay resets both Ho-Oh and Lugia. Save away from event
islands before using Enable or Replay. Southern Island replay preserves the normal
roaming Pokemon. Old Sea Map is an expanded English experience: the historical
distribution was Japanese-only.

All six Emerald/LeafGreen event paths and a completed-event replay passed reported
user testing on the local test device. FireRed has automated coverage only. A full
rebuilt-image test remains before release. See the
[Gen III event checklist and testing status](BUTTERFLY_LINK_GEN3_EVENTS_PLAN.md).

### Gen III direct gifts (v1.1.0)

**Local Transfer → Gen 3 → Gen 3 Gifts** adds already-hatched Pokémon directly
to an empty PC slot in any of the five qualified English Gen III games.

| Gift equivalent | Level | Moves | Held item | Shiny policy |
| --- | --- | --- | --- | --- |
| Jirachi, Wishmaker/Channel gameplay recipe | 5 | Wish, Confusion, Rest | Ganlon or Salac Berry, randomly chosen | Normal chance |
| Celebi, PokéPark 2006 recipe | 30 | Heal Bell, Safeguard, AncientPower, Future Sight | None | Never |
| Mew, MYSTRY/Aura recipe | 10 | Pound, Transform | None | Never |
| Deoxys, SPACE C/DOEL recipe | 70 | Cosmic Power, Recover, Psycho Boost, Hyper Beam | None | Never |
| Shiny Zigzagoon, Berry Program recipe | 5 | Tackle, Growl, Tail Whip | Liechi Berry | Guaranteed |

These are **generated English equivalents**, with original trainer **BLINK**,
a trainer ID distinct from the recipient, and random IVs. This selects the
normal **fateful encounter** memo for new direct gifts in the supported games.
They count as traded Pokémon for normal obedience and experience rules. Eggs
retain the recipient trainer and their normal in-game hatch information. They do not reproduce distributor identities, original records or
historical RNG correlations; Jirachi's normal shiny chance is not a reproduction
of the bonus disc's constrained shiny seeds. Duplicate campaigns with the same
gameplay recipe are grouped. Celebi uses the PokéPark level-30 recipe in this
batch, not the level-10 Ageto recipe. Deoxys uses the destination game's native
form and stats. Mew and Deoxys receive their fateful-encounter/obedience bit.

Save normally, exit the game, select a destination and matching ROM, choose the
gift and an empty PC slot, inspect the preview, then choose **Add Gift**. The
existing protected Commit and backup process applies. Withdraw the Pokémon,
check its level, moves and item, try a battle, then save and reload normally.
User testing of the gift workflow passed on the local test device; automated validation covers all 25 gift/game combinations. This does not establish exhaustive gameplay qualification for every destination. No story, ticket, Pokédex or event flags are changed. Giving
Zigzagoon or Jirachi does **not** repair the Ruby/Sapphire berry-clock glitch.

References: [primary numeric gift recipes](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs),
[bonus-disc gifts and Jirachi berries](https://bulbapedia.bulbagarden.net/wiki/List_of_game-based_Pok%C3%A9mon_distributions_in_Generation_III),
[Liechi Berry distribution](https://bulbapedia.bulbagarden.net/wiki/Liechi_Berry).

### Purified Shadow gifts (v1.3.0)

Open **Blink → Local Transfer → Gen 3 → Purified Shadow Gifts**, then choose
Colosseum (49 recipes/48 species, including two Suicune move sets), XD (83),
or Colosseum e-Reader (three expanded English equivalents). Gifts arrive already
purified in an empty PC slot with the National Ribbon, trainer BLINK and no held
item. Colosseum gifts have normal shiny chance; XD gifts cannot be shiny.
The e-Reader trio has zero IVs. All five qualified English Gen III games are
supported with the existing preview, verified backup and Commit protections.

Capture and purification take place in Colosseum/XD and are not recreated by
Blink. GBA games receive ordinary Pokemon with purified moves, not Shadow
state, Shadow moves or the dark Lugia model. Original GameCube identity, RNG,
met data, capture balls and purification EXP are not reproduced.
See the [complete moves and gameplay checklist](BUTTERFLY_LINK_GEN3_SHADOW_CHECKLIST.md).
The user confirmed the purified gifts working on the local test device. Individual recipes, destination games and ribbon/battle/save checks were not enumerated; this is not an exhaustive per-recipe/per-game qualification.

### Regional gifts (v1.3.0)

Open **Blink → Local Transfer → Gen 3 → Regional Gifts** for 13 generated
English equivalents: three Pikachu move sets, Meowth, Refresh Metang, Sunday
Wobbuffet, the three Hadou Regis, level-30 Mew, Mitsurin Celebi, and level-5/30
Jirachi. All are non-shiny with no held item and trainer BLINK. Metang includes
the National Ribbon. Duplicate campaigns share an option; original distributor
identity and historical RNG are not reproduced. All five qualified English
Gen III ROM/save pairs use the existing protected preview, backup and Commit.

See the [full levels, moves and gameplay checklist](BUTTERFLY_LINK_GEN3_REGIONAL_CHECKLIST.md).
The user confirmed the current gifts working on the local test device. This does not establish an exhaustive per-gift/per-game test matrix.

### Tenth-anniversary gifts (v1.3.0)

Open **Blink → Local Transfer → Gen 3 → 10th Anniversary Gifts**. Choose from
24 distinct recipes across 23 species, including Pikachu with Fly and standard
Pikachu. Duplicate regional campaigns are grouped. All arrive already hatched
at level 70, non-shiny, with no held item and trainer BLINK. The five qualified
English Gen III games are supported, using the existing preview, backup and
Commit flow. Normal traded-Pokemon obedience rules apply. Original distributor
identities, language variants and historical RNG are not reproduced.

See the [complete recipe and gameplay checklist](BUTTERFLY_LINK_GEN3_TENTH_ANNIVERSARY_CHECKLIST.md).
The user confirmed the current gifts working on the local test device. This does not establish an exhaustive per-gift/per-game test matrix.

### PCNY adult gifts (v1.3.0)

Open **Blink → Local Transfer → Gen 3 → PCNY Adult Gifts**. All **48 distinct
adult recipes** from the numeric reference catalog are implemented. Its 50
campaign entries include two duplicate recipes, which are grouped. The original
twelve options remain first; the final 36 are appended. Alternate levels and
move sets are labeled separately, with complete moves shown in the preview.
See the [complete recipe and gameplay checklist](BUTTERFLY_LINK_GEN3_PCNY_CHECKLIST.md).

All are non-shiny, have no held item, and use BLINK as their original trainer.
They arrive already hatched in an empty PC slot. The five qualified English
Gen III games are supported as expanded destinations; historical PCNY adult
distributions targeted Ruby/Sapphire. Preview, backups, Commit and changed-save
refusal apply. Original distributor identity and RNG are not reproduced.
The user confirmed the current gifts working on the local test device. This does not establish an exhaustive per-gift/per-game test matrix.

### GameCube gifts (v1.3.0)

Open **Blink → Local Transfer → Gen 3 → GameCube Gifts**. Choose a save
and matching ROM, then preview and commit a gift into an empty PC slot.
All five qualified English Gen III games are supported.

| Gift equivalent | Level | Distinctive content | Shiny policy |
| --- | --- | --- | --- |
| Bonus-disc Pikachu | 10 | Light Ball; ThunderShock, Growl, Tail Whip, Thunder Wave | Never |
| Ageto Celebi | 10 | Confusion, Recover, Heal Bell, Safeguard | Never |
| Mt. Battle Ho-Oh | 70 | Recover, Fire Blast, Sunny Day, Swift | Never |
| XD Chikorita | 5 | AncientPower, Tackle, Growl, Frenzy Plant | Normal chance |
| XD Cyndaquil | 5 | Reversal, Tackle, Leer, Blast Burn | Normal chance |
| XD Totodile | 5 | Crunch, Scratch, Leer, Hydro Cannon | Normal chance |

These use BLINK as the original trainer and the same protected backup/Commit
workflow as other direct gifts. They are generated equivalents: no GameCube
disc, challenge completion, original distributor identity or historical RNG is
recreated. Normal shiny chance is 1 in 8,192. Automated checks cover all six
recipes across all five games. The user confirmed all six gifts and ordinary
in-game saving working on the local test device; this does not establish a
complete gameplay matrix across all five destination games.

References: [Colosseum recipes](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/Encounters3RSE.cs),
[XD recipes](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/Encounters3XD.cs).

### Gen III egg game support (v1.1.0)

All 39 egg options are available for these qualified English retail revisions:
Emerald, Ruby/Sapphire revision 2, and FireRed/LeafGreen revision 1. Both raw
ROMs and ZIPs containing one matching ROM work. Other languages, revisions and
ROM hacks remain unsupported by the egg writer; it checks the full ROM hash.

These are generated equivalents with expanded game eligibility, independent of
the historical distribution's receiving-game restrictions. Each egg uses the
selected destination game's ROM data, trainer identity, origin ID and save
layout. No story flags or Pokédex unlocks are changed. Normal game restrictions
on later evolution still apply. Emerald has gameplay coverage for the earlier
batches; PCNY eggs and the newly added destination games need live hatch and
save/reload confirmation.

### Gen III Box eggs (v1.1.0)

**Local Transfer → Gen 3 → Gen 3 Box Eggs** offers four generated egg
equivalents for the qualified English Gen III ROM/save pairs below:

| Egg | Special move |
| --- | --- |
| Swablu | False Swipe |
| Zigzagoon | ExtremeSpeed |
| Skitty | Pay Day |
| Pichu | Surf |

Save normally and exit the game first. Choose your destination save, select a matching ROM
(ZIP works), choose an egg and a free PC slot, review the hatchling, then confirm
**Add Gift**. A backup is kept. Load the ordinary in-game save rather than an
older auto-save/state; withdraw the Egg and walk with it to hatch normally at
level 5. Verify the special move, then save and reload normally.

These eggs use your trainer identity, random personality/IVs and ROM-derived
hatch counters. They do not unlock islands, advance story progress, recreate
Pokémon Box deposit rewards or represent original distribution records.
The user confirmed all four eggs working in Emerald on the local test device.
Hatching and save/reload in the other games still need gameplay confirmation. See the [event plan](BUTTERFLY_LINK_GEN3_EVENTS_PLAN.md)
and [documented egg recipes](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs).

### Gen III PokéPark eggs (v1.1.0)

**Local Transfer → Gen 3 → PokéPark Eggs** adds 15 generated egg equivalents
for the qualified English Gen III ROM/save pairs. They use the same protected preview,
free-slot selection, backup and Commit flow as the Box eggs. All hatch normally
at level 5; no League progress or event-island access is needed.

| Egg | Notable moves |
| --- | --- |
| Psyduck | Water Sport, Mud Sport |
| Pichu | Follow Me |
| Igglybuff | Tickle |
| Corsola | Mud Sport |
| Taillow | FeatherDance |
| Surskit | Mud Sport |
| Whismur | Teeter Dance |
| Skitty | Rollout |
| Plusle | Water Sport |
| Minun | Mud Sport |
| Spoink | Uproar |
| Spinda | Sing |
| Cacnea | Encore |
| Corphish | Water Sport |
| Wynaut | Tickle |

These follow the documented 2005 Wonder Card species/move recipes, with your
trainer identity, random personality/IVs, no held item and the modern
fateful-encounter flag. They are generated equivalents, not original event
records; distributor scripts, Wonder Cards and event RNG are not recreated.
Duplicate delivery methods are grouped into one recipe per species. The
[full move recipes](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs)
are the reference. The user confirmed all 15 eggs working on the local test device.

### Gen III anniversary eggs (v1.1.0)

**Local Transfer → Gen 3 → Anniversary Eggs** offers eight recipes and two
separately labeled guaranteed-shiny Pichu variants for the qualified English Gen III games:

| Egg | Special move | Shiny policy |
| --- | --- | --- |
| Pichu | Teeter Dance | Normal chance |
| Pichu | Wish | Normal chance |
| Ralts | Charm | Normal chance |
| Ralts | Wish | Normal chance |
| Absol | Spite | Normal chance |
| Absol | Wish | Normal chance |
| Bagon | Iron Defense | Normal chance |
| Bagon | Wish | Normal chance |
| Shiny Pichu | Teeter Dance | Guaranteed |
| Shiny Pichu | Wish | Guaranteed |

The original 2003 anniversary distributions targeted Japanese Ruby. These are
explicitly **expanded English Gen III equivalents**, using your trainer
identity, the documented complete move recipes and random IVs. They do not
recreate Japanese event records, distribution RNG or the distributor's trainer.
The two shiny variants choose a personality that is shiny for your trainer ID;
the other eight retain the normal shiny chance.

Use the same preview, protected Commit and ordinary hatch/save/reload steps as
the other eggs. All hatch at level 5 with no held item and normal ROM-derived
hatch counters. The user confirmed all ten entries working on the local test device.
[Anniversary recipe reference](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs).

### Gen III promotional eggs (v1.1.0)

**Local Transfer → Gen 3 → Promotional Eggs** offers Oddish with Leech Seed,
Meowth with Petal Dance, Poliwag with Sweet Kiss and Bellsprout with Teeter Dance.
These are expanded English Gen III equivalents of the 2004 Japanese
FireRed/LeafGreen campaign, not original event records or distribution RNG.
They use your trainer identity, random IVs and the normal shiny chance.
All hatch at level 5 without held items. Use the same free-slot preview,
protected Commit, backup and ordinary hatch/save/reload process as the other eggs.
The user confirmed all four promotional eggs working on the local test device.
[Recipe reference](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs).

### Gen III PCNY Wish eggs (v1.1.0)

**Local Transfer → Gen 3 → PCNY Wish Eggs** offers six eggs. Each knows Wish:

| Pokémon | Second special move |
| --- | --- |
| Farfetch’d | Yawn |
| Drowzee | Belly Drum |
| Exeggcute | Sweet Scent |
| Lickitung | Heal Bell |
| Chansey | Sweet Scent |
| Kangaskhan | Yawn |

These are expanded English Gen III equivalents of the 2004–2005 FireRed/LeafGreen
PCNY campaign, not original event records or distribution RNG. They use your
trainer identity, random IVs and the normal shiny chance. All hatch at level 5
without held items. Use a free PC slot, preview and protected Commit, then hatch
and save/reload normally. Gameplay qualification is pending on the local test device.
[Recipe reference](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs).

## Opening Blink

Blink copies or exchanges Pokémon between selected emulator save files.
Open **Tools → Blink**, from the home screen or **Start → Tools**.
Use the D-pad to navigate, **A/Start** to select, and **B/Menu** to go back.

It works locally on one Flip or between two Flips on the same Wi-Fi network.
It edits saves; it does not launch games, emulate a cable, or provide battles.
Older netplay and USB-link plans describe historical experiments.

Keep an independent backup, exit the emulator before opening Blink,
and do not have the same save open in another application during a transfer.

## Supported games and transfer directions

Known English retail layouts are supported for Red, Blue, Yellow; Gold, Silver,
Crystal; and Ruby, Sapphire, Emerald, FireRed, LeafGreen. Other languages,
ROM hacks, and unrecognized revisions are not generally qualified.

| Source → destination | Local | Remote Wi-Fi | Limits |
|---|---|---|---|
| Gen I → Gen I | Trade or copy | Trade or copy | PC-box Pokémon |
| Gen II → Gen II | Trade or copy | Trade or copy | PC-box Pokémon |
| Gen III → Gen III | Trade or copy | Trade or copy | PC-box Pokémon; cross-family conversion supported from v1.0.4 |
| Gen I → Gen II | Copy | Copy | Time Capsule conversion; banked-box/name fixes included, not every save pairing qualified |
| Gen II → Gen III | Copy | Copy | One-way conversion; verified held-item equivalents preserved from v1.0.3 |
| Gen II → Gen I | Unavailable | Unavailable | No reverse Time Capsule conversion |
| Gen III → earlier generations | Unavailable | Unavailable | No reverse conversion |

From v1.0.4, Gen III trades support conversion between Ruby/Sapphire,
Emerald and FireRed/LeafGreen save families, including the tested Emerald ↔
LeafGreen pairing. Both trade and copy retain save validation and protected
backups. This does not qualify every game/save pairing.

Gen II → III is a Blink conversion, not an original-game cable feature.
Compatible identity/training data is converted; generation-specific fields need
newly derived values. **Version 1.0.3 preserves verified Gen III held-item
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

### Move and held-item names (v1.1.0)

When you browse party Pokémon or select a Pokémon in a PC box, the inspector
shows English move names for supported Gen I, II and III games instead of
labels such as `Move #10`. Gen II and III also show the held item's English
name on a separate line, or **No held item** when empty. Gen I has no held items.

Select the matching English ROM if prompted. Blink reads the names
and sprites locally from your ROM and refreshes older caches when needed;
the first preparation can take a moment. Gen I/II ZIP archives containing
exactly one `.gb` or `.gbc` ROM now work directly, alongside the existing
Gen III ZIP support. You do not need to unzip them manually.

Unknown move or item IDs retain a numeric label rather than guessing a name.
This is a display improvement; inspecting a Pokémon does not change its moves,
held item or save. Gen II → III copies retain the conversion rules described
above. No complete move/item name tables are bundled in the image.

Live checks of move and held-item names passed on the local test device.

## Remote workflow

1. Connect both Flips to the same Wi-Fi and open Blink; SSH is not required.
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

### Refresh Sprites (next release after v1.4.0)

If sprites are missing or damaged, open **Tools → Blink → Refresh Sprites**.
Choose **Gen 1**, **Gen 2** or **Gen 3**, then select the supported matching ROM.
Raw ROMs and ZIP archives containing one ROM are supported. Wait for
**Sprites Refreshed**, then return to your transfer or gift workflow. Repeat
for another game if needed; a save file is not required to refresh artwork.

This forcibly rebuilds the selected ROM's shared sprites and names rather than
reusing an existing cache. Blink and Bdex can reuse that cache. Game saves and
Pokémon records are unchanged. Refresh an open web-viewer page to reload images.
Bdex's own Refresh Sprites also repairs collection references; use that option
if stored Bdex copies still point to an older cache after changing ROM files.
This menu option is available in live testing and the next image, not v1.4.0.

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


## Live trading and battling

[Bslap](BSLAP.md) provides live same-generation trades and battles between two
ButterflyOS devices on the same local network. It is separate from Blink save
editing and Bdex collection storage, and is included in the next image.

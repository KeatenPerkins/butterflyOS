# Butterfly Link: Gen II event scope

Reviewed October 7, 2026. Crystal GS Ball Enable/Replay is implemented locally
for a live development test on .17. Automated save-state, checksum, native
reload, backup, conflict, Cancel, RTC and Pokémon-preservation tests pass.
Enable and Replay also passed user testing on .17 through Goldenrod delivery,
Kurt progression and the shrine encounter. Kurt's timer was cleared manually
to speed testing; the tool retains the game's normal wait. Initial Gen II Mew
and Stadium 2 gifts are now implemented locally. No event code is released in
a public image yet.
Gen I gifts and their menu were committed in `baa7351221`.

The .17 live patch passed disposable-save Enable, Replay, protected Commit,
backup and native reload checks. The separate playable
`Pokemon Crystal - Event Test` copy was subsequently updated with the user's
.20 progress for gameplay testing. Both quest actions passed that testing.
The menu discovers it under **Local Transfer → Gen 2 → Crystal Events**.
The live patch is temporary until a new image includes the package changes.

## Initial implementation

Use **Local Transfer → Gen 2**, with detected saves listed first, followed by
Gen 2 Gifts and Stadium 2 Gifts, matching the tested Gen 1 layout.

| Group | First presets | Operation |
| --- | --- | --- |
| Gen 2 Gifts | Mew | Generate a player-owned boxed gift; leave story flags alone |
| Stadium 2 Gifts | Baton Pass Farfetch'd, Earthquake Gligar | Generate boxed equivalents with the special move |
| Crystal Events, priority | Enable / replay GS Ball → Celebi quest | Enable native delivery and quest progression; replay is separately confirmed |

The Gen II [regional catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_European_language_event_Pok%C3%A9mon_distributions_in_Generation_II)
includes Mew and Celebi distributions. The [Stadium 2 reward catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_game-based_Pok%C3%A9mon_distributions_in_Generation_II)
identifies Farfetch'd with Baton Pass and Gligar with Earthquake. As with Gen I,
generated equivalents must not be described as original official distributions.
The initial writer uses player OT, random DVs, ROM-derived growth/move PP,
zero stat experience and level 5. Mew starts with Pound and no item. Farfetch'd
has Baton Pass/Swords Dance/Agility/Slash and Gold Berry; Gligar has
Earthquake/Poison Sting/Counter/Wing Attack and MysteryBerry. These two movesets
and berries match the documented Stadium 2 reward recipes. They remain generated
player-owned equivalents. All fourteen boxes across all three families pass
automated gift tests, native copy/reload, occupied/full-box refusal, RTC
preservation, ROM qualification and protected prepare/Commit/backup/Cancel.
The user confirmed all three gifts work in Crystal on .17. Actual Gold/Silver
gameplay remains unqualified; their automated and disposable-save device checks
pass. The random-DV behavior, including its natural shiny chance, is the user's
preferred behavior; no forced-shiny selector is requested.

Celebi should be received through Crystal's native event whenever supported,
following the user preference recorded October 7. Direct boxed Celebi delivery
is not the primary implementation. Crystal Events should appear below game
saves in the Gen 2 menu, with eligibility restricted to the qualified Crystal
ROM/save pair. Gen 2 and Stadium 2 gift generation remain separate actions.

## Additional inventory

Gen II is substantially larger than the six Gen I promotional gift families.
Group by distinct species/special move rather than campaign location or date.

- Japanese Mystery Egg campaigns include special-move gifts such as
  AncientPower Bulbasaur, Crunch Charmander, Submission Totodile, Night Shade
  Hoothoot and Sing Pichu. This is an initial inventory, not the whole catalog.
  [Japanese distribution catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_event_Pok%C3%A9mon_distributions_in_Generation_II).
- PCNY distributions include many special-move and shiny variants. Review and
  de-duplicate the complete catalog separately before expanding the recipe list;
  the historical catalog itself notes gaps in surviving information.
  [PCNY inventory](https://bulbapedia.bulbagarden.net/wiki/List_of_PCNY_event_Pok%C3%A9mon_distributions_in_Generation_II).
- Crystal's native Odd Egg delivery and replay passed user testing on .17. The overseas
  retail game already offers it normally; Japanese Mobile System delivery and
  the VC Celebi trigger differ from the targeted English retail games.
  [In-game event inventory](https://bulbapedia.bulbagarden.net/wiki/List_of_in-game_event_Pok%C3%A9mon_in_Generation_II).

## Remaining batches and egg qualification

The user requested the remaining Gen II events in small batches and prefers
actual eggs and native quest experiences. The first Mystery Egg batch implements
AncientPower Bulbasaur, Crunch Charmander, Submission Totodile, Night Shade
Hoothoot and Sing Pichu. Their documented level-5 movesets are numeric recipes;
names, PP, growth and hatch counters are read from qualified user ROMs.
The species list uses the native egg marker while the record retains the
hatchling species. Its friendship byte stores hatch cycles. No Pokédex flags
are set before hatching. Native hatching updates species/name, trainer identity,
friendship and Pokédex normally. The preview shows the hatchling, and transfer
selection refuses unhatched eggs. Gold/Silver/Crystal tests cover all fourteen
boxes, native copy/reload preserving the egg marker, protected Commit/Cancel,
random-DV shiny interpretation and Gen II → III egg refusal. The first five
eggs (fifteen egg/family combinations) also pass protected prepare, native
inspection, Commit, backup and repeat-Commit refusal on disposable .17 saves.
The temporary .17 UI and native helper patch is installed. The user confirmed
the first five eggs work in-game on .17 on October 7. The remaining ten recipes
are now implemented locally using the same native egg flow, with Fast growth
support for Cleffa and Igglybuff. The complete writer passes 756 gift/family/box
cases, including native box copy/reload and original preservation. All 45
egg/family combinations pass protected prepare, native inspection, Commit,
backup and repeat-Commit refusal on disposable .17 saves. The expanded
temporary UI patch is installed and verified on .17. The user subsequently
confirmed the remaining ten eggs work in-game as well. All fifteen Mystery Egg
recipes have passed user testing in Crystal on .17.

The three Japanese campaigns contain **15 distinct species/moveset recipes
across 12 species** when repeated campaign recipes are combined. The second
batch adds the remaining ten recipes: Petal Dance Psyduck,
Chikorita, Pichu, Cleffa, Igglybuff and Smoochum; Swift Cleffa; Belly Drum
Wooper; Encore Phanpy; and Metronome Smoochum.

Later batches remain pending:

1. Non-shiny Suicune remains unavailable because its catalog level/moves are
   missing; all 120 implemented PCNY gifts passed user testing in Crystal.
2. Qualify the direct level-5 Celebi gift in Silver gameplay; Gold passed user
   testing on .17, including save/reload persistence.

## Odd Egg, Gold/Silver Celebi and PCNY batch 1

Odd Egg replay is implemented locally. Primary constants assemble to
`EVENT_GOT_ODD_EGG = 830`; flat SRAM bit `0x2667 & 0x40` is mirrored at
`0x1867`. Only that bit and both native checksums are changed. The native
Day-Care script provides the actual egg; party-full handling and its random
selection/shiny behavior remain in-game. A waiting ordinary breeding egg is
refused using `wDayCareMan` bit 6 at flat SRAM `0x2a83`, derived from RAM
`wPokemonData = dcd7`, `wDayCareMan = def5`, and SRAM `sPokemonData = a865`.
No Day-Care Pokemon, egg, progress or object flags are changed. Never-received
saves are already eligible and need no modification. Twenty-four state/neighbor
bit tests preserve every unrelated byte, party/box records and Celebi quest
status, alongside checksum, backup, Cancel, RTC and native reload checks.

Gold/Silver now have a generated level-5 Celebi gift with Leech Seed, Confusion,
Heal Bell and Recover, no held item and random DVs. The writer refuses this
preset for Crystal and the UI hides it there in favor of the native quest.
All fourteen PC boxes in both save families pass automated gift qualification.

The first PCNY group adds real eggs for Zap Cannon Squirtle, Growth Eevee,
Lovely Kiss Snorlax, Hydro Pump Dratini and Double-Edge Cyndaquil, using complete
level-5 movesets from the documented catalog. Slow growth is now supported for
Snorlax and Dratini. Hatch counters, names, PP and growth remain ROM-derived.
The random-DV policy is retained; these are special-move equivalents, not an
exact reproduction of historical PCNY enhanced shiny odds or campaign records.
The full gift suite now passes 994 gift/family/box cases and preview/Cancel
checks, including native egg copy/reload and protected original backups.
All seventeen new gift/family combinations and one Odd Egg replay pass
protected preparation, native inspection, Commit, verified backup and repeated
Commit refusal on disposable .17 saves; source fixtures stay unchanged. The
expanded temporary menu is installed on .17, along with separate Gold/Silver
Event Test copies. The user confirmed native Odd Egg delivery and replay work
perfectly on .17. The user also confirmed the Celebi gift works in Gold
following the PC withdrawal and save/reload test. The first
five PCNY eggs were subsequently confirmed working in Crystal by the user,
including hatching, special moves and save/reload. Silver Celebi remains
pending separate gameplay qualification. At installation the Crystal save had not yet
received its first Odd Egg; Blink correctly reported the original delivery
already available before replay became necessary.

Primary references: [Day-Care delivery](https://github.com/pret/pokecrystal/blob/master/maps/DayCare.asm),
[native Odd Egg generator](https://github.com/pret/pokecrystal/blob/master/engine/events/odd_egg.asm),
[game-supplied egg table](https://github.com/pret/pokecrystal/blob/master/data/events/odd_eggs.asm).
Recipes: [PCNY catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_PCNY_event_Pok%C3%A9mon_distributions_in_Generation_II).

Native hatch reference: [original breeding and hatch code](https://github.com/pret/pokecrystal/blob/master/engine/pokemon/breeding.asm).
No ROMs, extracted sprites, donor saves or premade Pokémon records are bundled.

## PCNY batch 2

Ten more actual egg recipes are implemented: Mimic Igglybuff, Pursuit Elekid,
Faint Attack Magby, Rage Tyrogue, Dizzy Punch Sentret, Barrier Ledyba, Growth
Spinarak, Light Screen Chinchou, Safeguard Natu and Dizzy Punch Marill. All use
complete documented level-5 movesets, no held item, random DVs and ROM-derived
hatch cycles, names, PP and growth. The PCNY menu keeps the first five choices
first, then appends these ten. Recipes are distinct from the existing Japanese
Mystery Eggs; all remain generated player-owned equivalents.

The expanded suite passes 1,414 gift/family/box cases, native box copy/reload,
occupied/full refusal, exact change boundaries, RTC, qualification, protected
Commit/Cancel and original preservation. All thirty new egg/family combinations
also pass native inspection, protected preparation/Commit, verified backup and
repeat-Commit refusal on disposable .17 saves, with fixture originals unchanged.
Uploaded files match local SHA-256 hashes. The expanded temporary menu is now
activated and verified on .17, retaining executable permission and the first
five recipes before the ten additions. Native hatching and move/save/reload
testing of the ten additions was confirmed successful by the user in Crystal
on .17, including hatching, special moves and save/reload.

## Crystal GS Ball state

Adding a GS Ball alone is insufficient for the whole quest. Primary game code
shows that Goldenrod's delivery sets the permission to give the ball to Kurt;
Kurt consumes it, uses his work timer and later sets the forest-restless state;
the shrine checks that state and possession of the ball before starting a
level-30 Celebi battle. The encounter consumes the ball and changes event state.

Read and classify the existing save first: not started, ball delivered, Kurt
examining it, returned/ready, or encounter already completed. **Enable event** preserves an in-progress
quest. **Replay event** is a separate operation with a clear preview and explicit
Commit: reset only the verified Celebi quest state needed to receive the GS Ball
again, and retain previously caught Celebi, other Pokemon, Pokedex progress and
unrelated events. Do not overwrite unrelated Kurt/apricorn work; require that
work to finish before rearming the full quest when the native timer is shared.
Preserve the native delivery → Kurt → shrine sequence, and support only
verified ROM/save revisions after the SRAM event,
engine flag, item pocket, timer and backup locations are qualified.

Primary references: [Goldenrod delivery](https://github.com/pret/pokecrystal/blob/master/maps/GoldenrodPokecenter1F.asm),
[Kurt's handling](https://github.com/pret/pokecrystal/blob/master/maps/KurtsHouse.asm),
[shrine script](https://github.com/pret/pokecrystal/blob/master/maps/IlexForest.asm),
[event definitions](https://github.com/pret/pokecrystal/blob/master/constants/event_flags.asm).

The primary save code documents `sGSBallFlag` at SRAM `01:be3c`, its backup at
`01:be44`, and the available value `0x0b`. These correspond to flat save offsets
`0x3e3c` and `0x3e44`; these are now verified for the qualified English Crystal
layout. The original game restores
and backs up this flag separately from the main player-data checksum. Exact
revision validation and quest-state validation are required before using it.
[Original save code](https://github.com/pret/pokecrystal/blob/master/engine/menus/save.asm).

RAM symbols were assembled from primary source commit
`3bc8daa4173e96a7f4011dad3922eb6fa5dad5c6`.
The editor validates matching primary/backup player data and both native
checksums before staging changes. Primary data spans `0x2009..0x2b82` with
checksum at `0x2d0d`; backup data spans `0x1209..0x1d82` with checksum at
`0x1f0d`. It preserves optional appended RTC data and all party/PC records.

Replay tests must cover a never-started quest, each intermediate quest stage,
a completed catch, an encounter completed without catching, an unrelated
active apricorn job, saves inside quest maps, Cancel and repeated replay.
Verify all reset bits against native scripts and mirror both save copies.
Test the actual Goldenrod delivery, Kurt dialogue/timer, shrine animation and
level-30 encounter in-game before advertising replay as supported.

## Save and packaging requirements

- Match a SHA-256-qualified English Gold/Silver/Crystal ROM to the save family.
  GS and Crystal use different SRAM offsets; Japanese, Korean, VC and hacks
  need separate qualification.
- Gen II boxed records are 32 bytes, with direct National Dex species IDs,
  held item, moves, OT ID, experience, five stat-experience fields, DVs, PP,
  friendship, Pokerus, caught data and level. Do not reuse Gen I's 33-byte format.
- Append only to a free PC slot; retain occupied records, native 0x50 name
  terminators, active/banked boxes, Pokedex flags and mirrored save checksums.
- Reuse the tested working-copy, preview, explicit Commit, original fingerprint
  and verified-backup flow. Keep original saves unchanged on failure or Cancel.
- Qualify egg list markers, friendship/hatch counter and shiny DVs separately
  before adding eggs or a shiny option. A shiny appearance must follow native DV
  rules, rather than a cosmetic toggle.
- Ship code and numeric recipes only. Names, sprites, move PP and growth data
  must come from user ROMs. No ROMs, donor saves, prebuilt records or extracted
  assets in the repository or release.

Verified private ROM hashes collected read-only for the first fixture set:

| ROM | SHA-256 |
| --- | --- |
| Gold | `fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e` |
| Silver | `72b190859a59623cbef6c49d601f8de52c1d2331b4f08a8d2acc17274fc19a8c` |
| Crystal | `fdcc3c8c43813cf8731fc037d2a6d191bac75439c34b24ba1c27526e6acdc8a2` |

Qualification tests must cover all three families, both SRAM banks, repeat
append/box switching, full boxes, experience/level/PP, names, player identity,
Pokedex bits, checksums, backup/Cancel/conflict refusal and unchanged originals.
Then test PC withdrawal, in-game save, exit and reload on .17. Actual quest
unlock testing is a separate requirement from boxed gift generation.

## PCNY batch 3

The user confirmed all ten batch-2 eggs working. The third batch adds ten actual
eggs: Dizzy Punch Pichu, Scary Face Pichu/Cleffa/Igglybuff/Marill/Wooper,
Hydro Pump Marill, Substitute Sudowoodo, Agility Hoppip and Dizzy Punch Elekid.
Recipes use complete documented level-5 movesets, no held item and random DVs.
Names, move PP, growth and hatch cycles come from the user's qualified ROM.
These remain generated player-owned equivalents with natural shiny odds;
no ROM assets or premade Pokémon records are shipped. Entries append after
previous PCNY batches. The user confirmed all ten batch-3 eggs working in
Crystal on .17.

Validation passed: 1,834 gift/family/box cases locally, with native reload,
checksums, exact change boundaries, RTC, occupied/full refusal, protected
Commit/Cancel and original preservation. All thirty new egg/family cases passed
native inspection, protected Commit, verified backup and repeat-Commit refusal
on disposable .17 saves. Fixture originals remain unchanged. Local/uploaded
SHA-256 hashes match. The executable live menu was activated on .17 and its
25 PCNY choices verified. The user subsequently confirmed batch 3 working
in Crystal on .17 using the hatch, special-move and save/reload test process.

## Remaining documented PCNY catalog

An inventory of all 136 catalog entries identifies 120 PCNY menu recipes
(104 eggs and 16 shiny adults), 14 identical recipes in Mystery Eggs, Celebi
covered by Gold/Silver's gift and Crystal's native quest, and one incomplete
non-shiny Suicune entry. The latter remains unavailable without verified data.
The final expansion adds 79 eggs and 16 shiny adults. Adults use documented
levels (5, 40, 50 or 70), full movesets and guaranteed native shiny DVs. Eggs
retain random DVs/natural shiny odds. All use player ownership and qualified
ROM-derived names, growth and PP; no donor records or ROM assets are shipped.
The user confirmed these 95 additions working in Crystal on .17. All 104 PCNY
eggs and 16 shiny adult gifts are now user-qualified there. See the [test checklist](BUTTERFLY_LINK_GEN2_PCNY_CHECKLIST.md).

Validation passes 5,824 gift/family/box cases across Gold, Silver and Crystal,
including native reload, exact change boundaries, checksums, RTC, occupied/full
refusal, original preservation and both egg/adult preview cancellation paths.
All 285 new gift/family combinations also passed protected preparation/Commit,
verified backup, native inspection, shiny checks and repeat-Commit refusal on
disposable .17 saves. Fixture originals are unchanged. Uploaded/local SHA-256
hashes match. The executable UI is now activated on .17 and verified to expose
104 eggs and 16 shiny adult gifts. The user subsequently confirmed all remaining
gift checks passed in Crystal on .17.

## PCNY menu categories

At the user's request PCNY Gifts now opens two choices: Special-Move Eggs
(104 recipes) and Shiny Adult Gifts (16). Category selection precedes save
selection. Cancelling there does not start a session or touch a save. Each
list retains its recipe order, and previews use the corresponding egg/adult
title. Focused workflow checks across Gold, Silver and Crystal passed:
each category contains only its corresponding recipes, egg/adult preview
titles are correct, preview cancellation preserves the original save, and
cancelling category selection never requests a save or starts preparation.
The executable UI is activated on .17; live category labels and cancellation
were verified. The user subsequently confirmed the split menu and all gift
checks passed in Crystal on .17.

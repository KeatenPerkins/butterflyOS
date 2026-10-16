# Butterfly Link: Gen III event checklist

Researched October 9, 2026; implementation status updated October 16, 2026.
All 39 planned egg entries are implemented across five qualified English Gen III
games. Five direct gift equivalents are now being qualified on the local test
device. Native island events remain deferred until suitable LeafGreen/Emerald
story progress is available. The AuroraTicket prototype is excluded from the
image/menu pending gameplay qualification. No Gen III event feature is publicly
released; existing Gen III transfers are separate.

Prefer native encounters and hatchable eggs, as with Gen II. Group repeated
campaigns by distinct gameplay experience or species/moveset, while preserving
meaningful regional differences. This is a scope checklist, not a completed
inventory of every regional distribution recipe.

## Batch 1: native island events

| Action | Games with native support | Experience | Qualification |
| --- | --- | --- | --- |
| Eon Ticket | Ruby, Sapphire, Emerald | Southern Island encounter with Latias or Latios | Ruby has Latias, Sapphire has Latios; Emerald depends on the chosen roaming Pokémon. Emerald historically received the ticket through record mixing. |
| MysticTicket | FireRed, LeafGreen, Emerald | Navel Rock encounters with Lugia and Ho-Oh | Verify ticket, travel flags and each encounter independently. |
| AuroraTicket | FireRed, LeafGreen, Emerald | Birth Island puzzle and Deoxys encounter | Historical distributions excluded Japanese Emerald; distinguish native capability from historical eligibility. |
| Old Sea Map | Emerald | Faraway Island chase and Mew encounter | Official distribution was for Japanese Emerald only. Any other-language unlock must be labeled an expanded experience. |

Each action needs separate **Enable** and, where safely supported, **Replay**.
Adding a key item alone is not a sufficient implementation. Retain normal story
requirements and let the game generate the encounter. Do not reset unrelated
legendaries, roaming status, story progression or existing Pokémon.

Sources: [Eon Ticket](https://bulbapedia.bulbagarden.net/wiki/Eon_Ticket),
[MysticTicket](https://bulbapedia.bulbagarden.net/wiki/Mystic_Ticket),
[AuroraTicket](https://bulbapedia.bulbagarden.net/wiki/AuroraTicket),
[Old Sea Map](https://bulbapedia.bulbagarden.net/wiki/Old_Sea_Map).
Technical starting point: [Emerald harbor scripts](https://github.com/pret/pokeemerald/blob/master/data/maps/LilycoveCity_Harbor/scripts.inc).
These references establish feasibility targets, not qualified save offsets.

## Batch 2: core gift families

- [ ] Jirachi: Wishmaker and Channel; then Japanese campaign variants.
- [ ] Celebi: Ageto bonus-disc gift; then other documented distributions.
- [ ] Mew: documented direct gifts, separate from Faraway Island.
- [ ] Deoxys: documented direct gifts, separate from Birth Island.
- [ ] Shiny Berry Program Update Zigzagoon. Delivering the gift and repairing
  Ruby/Sapphire's clock problem are separate operations; do not imply one fixes
  the other.

For each recipe, verify level, moves, item, language, nature/gender restrictions,
shiny policy and identity policy before implementation. Preserve the established
generated-equivalent approach unless exact distribution emulation is explicitly
designed and tested. Never describe a generated equivalent as an original
official event Pokémon. Shiny eligibility varies by distribution.

References: [game-based distribution catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_game-based_Pok%C3%A9mon_distributions_in_Generation_III),
[PKHeX Gen III gift definitions](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs).

## Batch 3: eggs

- [x] Pokémon Box: False Swipe Swablu — implemented for Emerald; user testing passed.
- [x] Pokémon Box: ExtremeSpeed Zigzagoon — implemented for Emerald; user testing passed.
- [x] Pokémon Box: Pay Day Skitty — implemented for Emerald; user testing passed.
- [x] Pokémon Box: Surf Pichu — implemented for Emerald; user testing passed.
- [ ] Wish Egg distributions: enumerate all documented recipes and eligibility
  from the regional catalogs and primary encounter definitions before choosing
  batches. Do not confuse PCNY adult Wish gifts with egg distributions.
- [x] PokéPark 2005 eggs: 15 generated equivalents implemented for Emerald;
  automated checks pass and the user confirmed all 15 working on the local test device.
  The 15 recipes are listed
  in the [user guide](BUTTERFLY_LINK.md#gen-iii-poképark-eggs-development-test-batch).
- [x] Japanese 2004 promotional eggs: four expanded English Emerald equivalents
  implemented; user confirmed all four working on the local test device.
- [x] Pokémon Center fifth-anniversary eggs: eight recipes and two guaranteed-shiny
  Pichu variants implemented as expanded English Emerald equivalents of Japanese
  Ruby distributions. User confirmed all ten working; see the
  [user guide](BUTTERFLY_LINK.md#gen-iii-anniversary-eggs-development-test-batch).

Deliver real eggs, leaving normal hatching to the game. Test special-move
retention, hatch identity, Pokédex behavior and save/reload. The four Box eggs
are a bounded first egg batch.

The first development batch is under **Local Transfer → Gen 3 → Gen 3 Box
Eggs**. Initially Emerald-only, egg delivery now also supports the qualified
English Ruby/Sapphire revision 2 and FireRed/LeafGreen revision 1 ROM/save pairs. These are
generated equivalents with the recipient's trainer identity, random personality
and IVs, the four documented level-5 move recipes, no held item, and normal
ROM-derived hatch counters. They do not emulate Pokémon Box deposit rewards,
distribution RNG, or original distribution records. No League progress is needed.
These four new destination games require live hatch/save/reload confirmation.

Automated checks passed on disposable saves on the local test device: all four
recipes across all 24 record orders, independent native-reader validation, a
record spanning two PC sectors, occupied-slot/corrupt-save/wrong-ROM refusal,
original preservation, exclusive output, cancellation, verified backup/Commit,
changed-after-preview refusal and repeated-Commit refusal. ZIP cache matching
also passed. The user subsequently confirmed all four eggs working on the local test device.

The generator stages a new save, refuses occupied slots and damaged saves,
and changes only one PC record plus its active-sector checksum(s). Existing
party, PC entries, story, Pokédex, older save slot and auxiliary records are
preserved. The existing preview, cancel, source fingerprint and backed-up Commit
flow controls installation. Withdraw the Egg and hatch it normally; confirm its
special move and ordinary in-game save/reload before marking a recipe qualified.

Sources: [Box bonus eggs](https://bulbapedia.bulbagarden.net/wiki/List_of_game-based_Pok%C3%A9mon_distributions_in_Generation_III#Pok%C3%A9mon_Box_Bonus_Eggs),
[PCNY catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_PCNY_event_Pok%C3%A9mon_distributions_in_Generation_III),
[primary gift/egg definitions](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs).

## Batch 4: GameCube reward equivalents

- [ ] Colosseum bonus-disc Pikachu.
- [ ] Colosseum Mt. Battle Ho-Oh.
- [ ] XD Mt. Battle Chikorita with Frenzy Plant.
- [ ] XD Mt. Battle Cyndaquil with Blast Burn.
- [ ] XD Mt. Battle Totodile with Hydro Cannon.
- [ ] Assess other distinctive XD rewards and purified special-move Pokémon
  separately; the full Shadow Pokémon roster would substantially expand scope.

These would be boxed reward equivalents for GBA saves, similar to Stadium gifts.
They would not unlock or recreate the GameCube challenges themselves.

Sources: [bonus-disc catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_game-based_Pok%C3%A9mon_distributions_in_Generation_III),
[Colosseum](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Colosseum),
[XD rewards](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_XD).

## Batch 5: regional collections

- [ ] PCNY gifts, grouped by distinct species and special moves.
- [ ] Tenth-anniversary gift collections.
- [ ] Japanese promotional gifts, including special-move Pikachu and other
  documented campaign Pokémon.
- [ ] Other European/American regional variants with meaningful differences.

Before implementing each collection, produce a sourced recipe table. Record
uncertain or incomplete historical entries and leave them unavailable until
enough information exists. Campaign names alone do not establish a complete
recipe. Do not claim the collection is exhaustive until regional inventories
have been reconciled.

## Optional later scope

Review documented e-Reader berries, decorations and trainer content separately;
they require different handling from gifts and built-in encounters. Do not bundle
official card scans, downloaded scripts or distributor binaries.

Exclude Altering Cave encounter changes from the historical-event list: the
planned distribution never occurred. Ordinary obtainable gifts, starters,
fossils and story encounters are not missing promotional events.
[Altering Cave history](https://bulbapedia.bulbagarden.net/wiki/Changing_Cave).

## Implementation and testing gate

Use the menu flow **Local Transfer → Gen 3**, detected saves first, followed by
**Gen 3 Events**, **Gen 3 Gifts**, **Event Eggs**, and **GameCube Gifts** as each
group becomes qualified. Filter choices by the selected qualified ROM/save.

Keep protected preview, explicit Commit, backup, Cancel and conflict refusal.
Account for Gen III save-section rotation and checksums. Verify exact change
boundaries, existing party/boxes, occupied/full refusal, native reload and
in-game save persistence. Use disposable saves before personal saves. Replay
must explain that it permits another encounter and cannot undo a prior capture.

Keep original implementation code and numeric recipes in the build; read needed
game data and sprites from the user's qualified ROM. Do not bundle ROMs, saves,
extracted sprites or premade event Pokémon records. Exact eligibility, offsets,
gift generation and language support remain engineering work.

The first implementation is **AuroraTicket in FireRed**, because the user has
a postgame FireRed save available. Eon Ticket can follow once an Emerald test
save is ready. Test native travel, encounter, capture, save/reload and Replay
independently.

## AuroraTicket implementation status

The helper qualifies English FireRed revision 1 by SHA-256
`729041b940afe031302d630fdbe57c0c145f3f7b6d9b8eca5e98678d0ca4d059`.
The menu lists FireRed-named FRLG-family saves under
**Local Transfer → Gen 3 → Gen 3 Events → AuroraTicket / Deoxys**.
LeafGreen, other revisions and Emerald are not qualified by this implementation.
The save layout itself is shared by FRLG; the matching ROM and filename are
required, rather than claiming the save uniquely identifies its originating ROM.

Enable inserts the ticket using the save's encrypted quantity, sets receipt and
Birth Island travel flags, and preserves encounter state. Finished encounters
require explicit Replay. Replay clears the fought/flew-away/shown/awakened flags,
resets the two puzzle variables and restores initial object visibility. Both
actions require completed-game/Rainbow Pass travel and refuse saves located on
Birth Island or its harbor. They do not advance story requirements.

The writer validates complete save sectors, native checksums and uniform counters,
selects the latest slot using native counter rules, and preserves the older slot,
PC storage, party, Pokédex, Hall of Fame and all unrelated bytes. Damaged,
incomplete, duplicate-ID or ambiguous-counter saves are refused. Only changed
current-slot sectors receive updated checksums. Output creation is exclusive;
the original is untouched until the established protected Commit makes its
verified backup. No Wonder Card or original distributor script is installed.

`tests/butterflyos-gen3-event-test.py` passes 28 rotation/action combinations,
independent checksum verification, exact change-boundary checks, encrypted
quantities, original preservation, older-slot preservation, counter rollover,
full/duplicate pocket refusal, ineligible progress/maps, wrong ROM, corrupt-save
refusal, staged Cancel, changed-after-preview refusal, backup and repeated Commit
refusal. Fixtures derive from a private save and are not distributed.

On the local test device, the existing native save reader accepts both prepared Enable and Replay
fixtures as FRLG saves. Trainer/party/box inspection is identical before and
after each action. This is format qualification, not an in-game encounter test.
Only disposable fixtures were uploaded, outside the ROM/save directories.
The production helper and menu changes remain local source changes for now.

The current FireRed save on the local test device is early-game and correctly fails the postgame
gate. Gameplay testing needs a separate copy of the user's island-ready save:
Enable, ferry travel from Vermilion, puzzle, encounter/capture, in-game save/reload,
then Replay with prior Pokémon preserved. Start Game must load the ordinary save,
not an old save state or Auto Resume.

## PokéPark development batch validation

The shared egg generator now contains 19 recipes: four Box eggs and 15 PokéPark
2005 equivalents. All 456 recipe/record-order combinations passed native-reader
validation on disposable saves on the local test device. Checks include native
save/record checksums, exact write boundaries, moves and PP, egg bits, trainer
identity, ROM hatch counters and the PokéPark modern fateful-encounter flag.
Sector-crossing records, occupied-slot/corrupt-save/wrong-ROM refusal, exclusive
output, original preservation, cancellation, verified backup/Commit and
changed-after-preview/repeated-Commit refusal also pass. In-game testing is
complete for the four Box eggs and 15 PokéPark eggs, as confirmed by the user.

## Anniversary development batch validation

Eight anniversary recipes and two guaranteed-shiny Pichu variants are staged as
expanded English Emerald equivalents of the Japanese Ruby gifts. All 696
recipe/record-order combinations across the 29 Box, PokéPark and anniversary
entries passed the native save reader, including explicit shiny detection for
both guaranteed-shiny variants. Shiny generation was checked against multiple
trainer IDs and random inputs; ordinary recipes retain their random personality.
Six automated test groups also cover recipe/menu parity, move PP, egg flags,
trainer identity, sector boundaries, occupied/corrupt/wrong-ROM refusal,
exclusive output and original preservation, ZIP matching and protected
Cancel/backup/Commit/changed-save/repeated-Commit behavior. In-game testing of
the ten anniversary entries passed on the local test device, confirmed by the user.

## Promotional development batch validation

The four 2004 promotional egg equivalents are implemented for English Emerald.
All 792 recipe/record-order combinations across 33 entries passed the native
save reader on the local test device. Six automated test groups passed,
including complete promotional recipes, menu parity, fateful flags, PP,
checksums, original preservation and protected preview/backup/Commit behavior.
The user confirmed all four eggs working on the local test device.


## PCNY Wish egg development batch

Six expanded English Emerald equivalents of the FRLG PCNY Wish campaign are
implemented: Farfetch’d/Yawn, Drowzee/Belly Drum, Exeggcute/Sweet Scent,
Lickitung/Heal Bell, Chansey/Sweet Scent and Kangaskhan/Yawn. Each also knows
Wish. They retain the protected empty-slot preview and backup/Commit flow.
Gameplay qualification is pending on the local test device.

All 936 recipe/record-order combinations across 39 egg entries passed the
native reader on the local test device. All six automated test groups passed,
including exact PCNY movesets, fateful flags, menu parity, checksums, original
preservation and protected preview/backup/Commit behavior. The live frontend
and gift helper executable permissions were verified before handoff.


## Expanded egg destination support

All 39 recipes now support the qualified English Emerald, Ruby/Sapphire revision
2 and FireRed/LeafGreen revision 1 ROMs. Full-ROM hashes select the family-specific
sector lengths, ROM tables and origin IDs. The CLI refuses mismatched save
families. Writes remain limited to one empty PC record and its sector checksum(s).
Historical distribution restrictions are explicitly relaxed for these generated
equivalents. No ROM text, sprites, event records or saves are bundled.
New destination games still require live hatching and save/reload confirmation.

Automated validation passed on separate copies of all five games' saves:
936 recipe/order combinations for Emerald, plus all 39 recipes in each of Ruby,
Sapphire, FireRed and LeafGreen (1,092 combinations total). Each game's six test
groups passed, covering PP, species, egg flags, origin game, level-5 experience,
shiny policy, exact write boundaries, crossing a PC-sector boundary, corrupt and
occupied-slot refusal, exclusive output, ZIP matching and protected
Cancel/backup/Commit behavior. A further 16 cross-family ROM/save combinations
were refused without output or source-save changes. These checks do not replace
live hatching and save/reload qualification in the four new destination games.


The user confirmed the expanded cross-game egg delivery working on the local
test device. The specific destination and complete per-game hatch/save/reload
matrix were not reported, so this confirmation is not a claim that all 39 eggs
were individually hatched in all five games.

The implemented egg catalog covers the documented distinct recipes in PKHeX's
Gen III Eggs collection: four Box, eight anniversary recipes plus two shiny
Pichu variants, four 2004 promotional, six PCNY Wish and fifteen PokéPark entries.
Duplicate distribution methods are grouped rather than offered as duplicate eggs.


## First direct-gift batch

Implemented five generated English equivalents across the five qualified games:
Jirachi (Wishmaker/Channel shared recipe), Celebi (PokéPark 2006 level 30), Mew
(MYSTRY/Aura shared recipe), Deoxys (SPACE C/DOEL shared recipe), and guaranteed
shiny Berry Program Zigzagoon. See the user guide for complete levels, moves,
held-item choices and shiny policies. Ageto Celebi, other distinctive variants,
GameCube rewards and regional collections remain planned; this is not a complete
direct-gift catalog. Original trainer/event records and distribution RNG are not
reproduced. No story flags, ticket state or berry-clock repair is performed.
Gameplay qualification is pending on the local test device.

First direct-gift automated validation passed on separate save copies: 600
combinations (five gifts × 24 encrypted record layouts × five games) accepted by
the native reader. Independent decoding verified species, level experience,
ROM-derived PP/friendship/nickname, held items, non-egg bits, origin game,
fateful bits and exact write boundaries. All 25 gift/game pairs passed the actual
UI prepare/backup/Commit path and repeated-Commit refusal. Shiny policies passed
multiple trainer IDs and random inputs, including forced non-shiny collisions.
Six existing egg regression groups also passed (all 39 egg recipes, one layout
each, plus sector-boundary, shiny, corruption and protected-flow checks).
Original fixture saves remained unchanged. Live frontend and gift helper
executable permissions were verified. In-game gift qualification remains pending.

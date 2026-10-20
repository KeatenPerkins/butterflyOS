# Gen III tenth-anniversary gift checklist

Open **Blink → Local Transfer → Gen 3 → 10th Anniversary Gifts**.
There are 24 distinct gameplay recipes across 23 species, including Pikachu
with Fly and the standard Pikachu move set. Regional campaigns with identical
species, level and moves are grouped. The numeric reference snapshot covers
91 anniversary campaign entries; this is coverage against that reference,
not a claim of exhaustive reconstruction of historical distribution records.

All gifts arrive already hatched at level 70, non-shiny, with no held item.
These are generated English equivalents with trainer BLINK and a trainer ID
distinct from the recipient. All five qualified English Gen III ROM/save
pairs are supported. Normal traded-Pokemon obedience rules still apply.
Original distributor identities, regional languages and distribution RNG are
not reproduced. No ROM, save, sprite cache or original gift record is bundled.
Ho-Oh's recipe also appears under GameCube Gifts; either option produces the
same gameplay equivalent.

## Testing

Save normally and exit the game. Choose the destination and matching ROM,
then select a gift and empty PC slot. Review the preview before Commit.
Verified backups, cancellation and changed-save refusal use the existing
protected flow. Withdraw each gift to check species, level and moves, then
save/reload normally. Use ordinary in-game saves for qualification.
The user confirmed the current gifts working on the local test device. This does not establish an exhaustive per-gift/per-game test matrix.

| Gift | Level | Moves |
| --- | --- | --- |
| BULBASAUR | 70 | SWEET SCENT, GROWTH, SOLARBEAM, SYNTHESIS |
| CHARIZARD | 70 | WING ATTACK, SLASH, DRAGON RAGE, FIRE SPIN |
| BLASTOISE | 70 | PROTECT, RAIN DANCE, SKULL BASH, HYDRO PUMP |
| PIKACHU - FLY | 70 | THUNDERBOLT, THUNDER, LIGHT SCREEN, FLY |
| PIKACHU - STANDARD | 70 | THUNDERBOLT, AGILITY, THUNDER, LIGHT SCREEN |
| ALAKAZAM | 70 | FUTURE SIGHT, CALM MIND, PSYCHIC, TRICK |
| ARTICUNO | 70 | AGILITY, MIND READER, ICE BEAM, REFLECT |
| ZAPDOS | 70 | AGILITY, DETECT, DRILL PECK, CHARGE |
| MOLTRES | 70 | AGILITY, ENDURE, FLAMETHROWER, SAFEGUARD |
| DRAGONITE | 70 | AGILITY, SAFEGUARD, WING ATTACK, OUTRAGE |
| TYPHLOSION | 70 | QUICK ATTACK, FLAME WHEEL, SWIFT, FLAMETHROWER |
| ESPEON | 70 | PSYBEAM, PSYCH UP, PSYCHIC, MORNING SUN |
| UMBREON | 70 | FAINT ATTACK, MEAN LOOK, SCREECH, MOONLIGHT |
| RAIKOU | 70 | QUICK ATTACK, SPARK, REFLECT, CRUNCH |
| ENTEI | 70 | FIRE SPIN, STOMP, FLAMETHROWER, SWAGGER |
| SUICUNE | 70 | GUST, AURORA BEAM, MIST, MIRROR COAT |
| TYRANITAR | 70 | THRASH, SCARY FACE, CRUNCH, EARTHQUAKE |
| LUGIA | 70 | RECOVER, HYDRO PUMP, RAIN DANCE, SWIFT |
| HO-OH | 70 | RECOVER, FIRE BLAST, SUNNY DAY, SWIFT |
| CELEBI | 70 | ANCIENTPOWER, FUTURE SIGHT, BATON PASS, PERISH SONG |
| BLAZIKEN | 70 | BLAZE KICK, SLASH, MIRROR MOVE, SKY UPPERCUT |
| ABSOL | 70 | DOUBLE TEAM, SLASH, FUTURE SIGHT, PERISH SONG |
| LATIAS | 70 | MIST BALL, PSYCHIC, RECOVER, CHARM |
| LATIOS | 70 | LUSTER PURGE, PSYCHIC, RECOVER, DRAGON DANCE |

## Source

[Primary numeric anniversary recipes](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs)
cover the regional anniversary, Party of the Decade and Journey Across America
campaigns. The snapshot in `tests/fixtures/butterflyos-gen3-tenth-anniversary-catalog.json`
records the source hash and distinct recipes. The tests require exact recipe
coverage and independently check encrypted records and native save reads.

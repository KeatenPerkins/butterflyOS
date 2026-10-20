# Gen III PCNY adult gift checklist

All 48 distinct species/level/move recipes from the reference catalog are
implemented. Its 50 campaign entries include two duplicate recipes, grouped
into a single option each. This is completeness against that reference catalog,
not a claim that every historical distribution has been reconstructed.

Open **Blink → Local Transfer → Gen 3 → PCNY Adult Gifts**. The original twelve
options remain first; the final 36 follow them. Variant names distinguish moves
or levels. Preview shows the complete moves before Commit.

These are generated English equivalents using trainer BLINK, no held item,
non-shiny personalities and the destination ROM's data. They arrive already
hatched in an empty PC slot. All five qualified English Gen III games are
supported as expanded destinations; historical adult PCNY gifts targeted
Ruby/Sapphire. Existing preview, backup, Cancel and changed-save protections
apply. No original distributor identities, RNG correlations or campaigns are
recreated. No ROM, save, sprite or premade Pokemon record is bundled.

## Gameplay checklist

For each option, check species, level and moves after withdrawing it. Save
normally and reload. Test ordinary battle use where practical. The user confirmed the current gifts working on the local test device; this
does not establish an exhaustive per-gift/per-game test matrix. Automated
validation is recorded in the current build status. Use a save with enough empty PC space for your test.

| Gift / variant | Level | Moves |
| --- | --- | --- |
| PIKACHU | 50 | THUNDERBOLT, AGILITY, THUNDER, LIGHT SCREEN |
| GLOOM | 50 | SLEEP POWDER, ACID, MOONLIGHT, PETAL DANCE |
| STARYU | 50 | MINIMIZE, LIGHT SCREEN, COSMIC POWER, HYDRO PUMP |
| SEADRA - ICE BEAM | 45 | DRAGON RAGE, HYDRO PUMP, TWISTER, ICE BEAM |
| FLYGON - FLAMETHROWER | 45 | SAND TOMB, CRUNCH, DRAGONBREATH, FLAMETHROWER |
| ALTARIA - FLAMETHROWER | 45 | AERIAL ACE, DRAGONBREATH, DRAGON DANCE, FLAMETHROWER |
| SEADRA - LEER | 45 | DRAGON RAGE, HYDRO PUMP, TWISTER, LEER |
| ALTARIA - ICE BEAM | 45 | TAKE DOWN, DRAGONBREATH, DRAGON DANCE, ICE BEAM |
| SALAMENCE - THRASH | 50 | PROTECT, DRAGONBREATH, THRASH, FLY |
| SHEDINJA | 50 | SPITE, CONFUSE RAY, SHADOW BALL, GRUDGE |
| CACTURNE | 50 | FAINT ATTACK, SPIKES, NEEDLE ARM, COTTON SPORE |
| SHUPPET | 25 | SCREECH, NIGHT SHADE, CURSE, SPITE |
| DUSKULL - LV 25 | 25 | DISABLE, FORESIGHT, ASTONISH, CONFUSE RAY |
| EXPLOUD - LV 50 | 50 | STOMP, HYPER VOICE, SHADOW BALL, ROAR |
| EXPLOUD - LV 100 | 100 | ROAR, SHADOW BALL, BRICK BREAK, HYPER VOICE |
| AGGRON - LV 50 | 50 | TAUNT, IRON TAIL, PROTECT, METAL CLAW |
| AGGRON - LV 100 | 100 | IRON TAIL, DRAGON CLAW, ICE BEAM, DOUBLE-EDGE |
| WAILORD - LV 50 | 50 | WATER PULSE, BLIZZARD, REST, WATER SPOUT |
| WAILORD - LV 100 | 100 | BLIZZARD, WATER SPOUT, EARTHQUAKE, HYDRO PUMP |
| CRAWDAUNT - LV 50 | 50 | DIG, BUBBLEBEAM, CRABHAMMER, SWORDS DANCE |
| CRAWDAUNT - LV 100 | 100 | TOXIC, CRABHAMMER, HAIL, GUILLOTINE |
| ALTARIA - REFRESH | 45 | TAKE DOWN, DRAGONBREATH, DRAGON DANCE, REFRESH |
| FLYGON - SCREECH | 45 | SAND TOMB, CRUNCH, DRAGONBREATH, SCREECH |
| SEADRA - LV 32 | 32 | SMOKESCREEN, LEER, WATER GUN, TWISTER |
| SALAMENCE - SCARY FACE | 50 | PROTECT, DRAGONBREATH, SCARY FACE, FLY |
| GARDEVOIR - LV 35 | 35 | TELEPORT, CALM MIND, PSYCHIC, IMPRISON |
| TROPIUS - LV 30 | 30 | RAZOR LEAF, STOMP, SWEET SCENT, WHIRLWIND |
| HOUNDOUR - LV 5 | 5 | LEER, EMBER |
| MAREEP - LV 5 | 5 | TACKLE, GROWL |
| SEVIPER - LV 30 | 30 | POISON TAIL, SCREECH, GLARE, CRUNCH |
| ABSOL - SPITE | 35 | RAZOR WIND, BITE, SWORDS DANCE, SPITE |
| ABSOL - WISH | 35 | RAZOR WIND, BITE, SWORDS DANCE, WISH |
| AZURILL - LV 5 | 5 | SPLASH, CHARM |
| WYNAUT - LV 5 | 5 | SPLASH, CHARM, ENCORE |
| HUNTAIL - LV 20 | 20 | WHIRLPOOL, BITE, SCREECH |
| GOREBYSS - LV 20 | 20 | WHIRLPOOL, CONFUSION, AGILITY |
| KINGDRA - LV 35 | 35 | SMOKESCREEN, LEER, WATER GUN, TWISTER |
| ZANGOOSE - LV 18 | 18 | LEER, QUICK ATTACK, SWORDS DANCE, FURY CUTTER |
| SEVIPER - LV 18 | 18 | WRAP, LICK, BITE, POISON TAIL |
| MILOTIC - LV 35 | 35 | WATER PULSE, TWISTER, RECOVER, RAIN DANCE |
| SABLEYE - LV 18 | 18 | FORESIGHT, NIGHT SHADE, ASTONISH, FURY SWIPES |
| MAWILE - LV 18 | 18 | ASTONISH, FAKE TEARS, BITE, SWEET SCENT |
| CRADILY - LV 40 | 40 | ACID, INGRAIN, CONFUSE RAY, AMNESIA |
| ARMALDO - LV 40 | 40 | WATER GUN, METAL CLAW, PROTECT, ANCIENTPOWER |
| MACHAMP - LV 30 | 30 | KARATE CHOP, SEISMIC TOSS, FORESIGHT, REVENGE |
| GOLEM - LV 30 | 30 | ROCK THROW, MAGNITUDE, SELFDESTRUCT, ROLLOUT |
| LUDICOLO - LV 20 | 20 | ASTONISH, GROWL, ABSORB, NATURE POWER |
| SHIFTRY - LV 20 | 20 | POUND, HARDEN, GROWTH, NATURE POWER |

## Reference

[Numeric recipe catalog](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Resources/legality/wild/Gen3/encounter_pcny.pkl)
and [decoder / non-shiny policy](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Templates/Gen3/Gifts/EncounterGift3NY.cs).
The numeric snapshot is kept in `tests/fixtures/butterflyos-gen3-pcny-catalog.json`;
tests require exact coverage of every distinct recipe.

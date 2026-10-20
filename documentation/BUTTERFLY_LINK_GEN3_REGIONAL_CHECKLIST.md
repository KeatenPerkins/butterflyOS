# Gen III regional gift checklist

Open **Blink → Local Transfer → Gen 3 → Regional Gifts**.
The 13 additions cover distinct regional gameplay recipes from the primary
reference. Identical campaigns are grouped: GW/Sapporo Pikachu, ROCKS/Festa
Metang, and the non-shiny level-5 Japanese Jirachi campaigns share options.
Existing level-10 Mew, level-30 Celebi, and shiny Berry Program Zigzagoon remain
in Gen 3 Gifts. This is a bounded recipe collection, not a claim that every
regional event has been reconstructed.

All 13 arrive already hatched, non-shiny, with no held item and trainer BLINK.
Level-5 Jirachi differs from the existing Wishmaker/Channel equivalent in its
shiny/item policy. Mitsurin Celebi has Leech Seed instead of the Ageto gift's
Confusion. Metang has the National Ribbon. Mew retains the modern fateful /
obedience flag required by the supported games.

These are generated English equivalents for all five qualified English Gen III
ROM/save pairs. Original distributor identities, Japanese text, eligibility and
historical RNG are not reproduced. Normal traded-Pokemon obedience rules apply.
No ROM, save, sprite cache or original gift record is bundled.

## Test procedure

Save normally and exit the game. Select a destination and matching ROM, then
choose a gift and empty PC slot. Review the preview before Commit. Existing
verified backups, cancellation and changed-save refusal apply. Check species,
level and moves in-game; check Metang's ribbon and Mew's battle use. Save/reload
normally. The user confirmed the current gifts working on the local test device. This does not establish an exhaustive per-gift/per-game test matrix.

| Gift | Level | Moves |
| --- | --- | --- |
| JIRACHI - LV 5 | 5 | WISH, CONFUSION, REST |
| PIKACHU - ANA FLY | 10 | FLY, THUNDERSHOCK, TAIL WHIP, THUNDER WAVE |
| MEOWTH - POKEPARK | 5 | SCRATCH, GROWL |
| PIKACHU - SURF | 10 | THUNDERSHOCK, GROWL, THUNDER WAVE, SURF |
| PIKACHU - GW FLY | 10 | GROWL, TAIL WHIP, THUNDER WAVE, FLY |
| METANG - REFRESH | 30 | TAKE DOWN, CONFUSION, METAL CLAW, REFRESH |
| WOBBUFFET - SUNDAY | 5 | COUNTER, MIRROR COAT, SAFEGUARD, DESTINY BOND |
| REGIROCK - HADOU | 40 | CURSE, SUPERPOWER, ANCIENTPOWER, HYPER BEAM |
| REGICE - HADOU | 40 | CURSE, SUPERPOWER, ANCIENTPOWER, HYPER BEAM |
| REGISTEEL - HADOU | 40 | CURSE, SUPERPOWER, ANCIENTPOWER, HYPER BEAM |
| MEW - LV 30 | 30 | POUND, TRANSFORM, MEGA PUNCH, METRONOME |
| CELEBI - MITSURIN | 10 | LEECH SEED, RECOVER, HEAL BELL, SAFEGUARD |
| JIRACHI - LV 30 | 30 | WISH, PSYCHIC, HELPING HAND, REST |

## References

[Primary regional recipe definitions](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/Legality/Encounters/Data/Gen3/EncountersWC3.cs).
The numeric snapshot is in `tests/fixtures/butterflyos-gen3-regional-catalog.json`.
[Native ribbon / fateful fields](https://github.com/pret/pokeemerald/blob/master/include/pokemon.h)
are independently checked after record decryption.

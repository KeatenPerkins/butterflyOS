# Butterfly Link: Gen I event feasibility

Research reviewed October 7, 2026. The first implementation is local and
unreleased: six level-5 gifts (Mew, Surfing/Flying Pikachu, Dragon Rage Magikarp, and
Pay Day Fearow/Rapidash) for three verified English
retail Red, Blue and Yellow ROM revisions. Other revisions, languages, ROM hacks
and Virtual Console patches are refused until qualified. A separate Stadium
Gifts menu now adds nine level-5 reward equivalents.
Gen II and III require their own event inventories and save-format review.

## Event inventory

The historical catalogs list many regional campaigns. Grouping them by the
actual gift avoids implementing dozens of nearly identical distribution flows.
Exact historical original-trainer names, IDs, DVs and catch-rate bytes vary;
several distributions have incomplete surviving documentation.

| Gift family | Historical examples | Proposed save operation | Feasibility |
| --- | --- | --- | --- |
| Mew | CoroCoro, Space World, Toys R Us, Nintendo tours; later Virtual Console distributions | Construct a gift record and append it to a free PC slot | Feasible; no event ROM or donor save required |
| Pikachu with Surf | Nintendo 64 promotion, CoroCoro, Battle Tour, Nintendo Power | Gift, with an optional separately confirmed move-learning operation for an eligible existing Pikachu | Feasible; Yellow's minigame needs additional trainer-identity checks |
| Pikachu with Fly | CoroCoro promotions | Gift with the special move | Feasible as a generated equivalent; historical Japanese-language authenticity is outside the initial English-only scope |
| Magikarp with Dragon Rage | Tamamushi University | Gift with the special move | Same generated-equivalent approach |
| Fearow with Pay Day | Pokemon Stamp campaign | Gift with the special move | Same generated-equivalent approach |
| Rapidash with Pay Day | Pokemon Stamp campaign | Gift with the special move | Same generated-equivalent approach |

History references: [Japanese distribution catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_event_Pok%C3%A9mon_distributions_in_Generation_I)
and [European-language distribution catalog](https://bulbapedia.bulbagarden.net/wiki/List_of_European_language_event_Pok%C3%A9mon_distributions_in_Generation_I).
These catalogs identify gaps in historical metadata; they are not proof that
every historical record can be reconstructed exactly. Nintendo also documented
an actual [Virtual Console Mew distribution](https://www.nintendo.com/en-gb/News/2016/November/Nintendo-UK-s-Pokemon-Festival-A-Pokemon-Sun-Pokemon-Moon-launch-celebration--1152793.html).

Stadium rewards are a separate group: Amnesia Psyduck, plus
Bulbasaur, Charmander, Squirtle, Hitmonlee, Hitmonchan, Eevee, Omanyte and Kabuto.
These are game rewards, not time-limited distribution events. Generated gifts
would not establish that the player completed Stadium's challenges.
[Reward inventory](https://bulbapedia.bulbagarden.net/wiki/List_of_game-based_Pok%C3%A9mon_distributions_in_Generation_I).

## Gen I unlocks

The reviewed distribution families deliver Pokemon records. They do not require
the ticket/island-unlock workflow used by some later-generation events. Adding
a Mew gift does not create a new Mew encounter or alter the game's map scripts.

Yellow's surfing minigame is a specific exception worth supporting and testing.
Its game code checks for a party Pikachu with Surf and matching player trainer
ID/name, then derives its surfing-Pikachu state. An arbitrary foreign-trainer
event Pikachu should not be advertised as sufficient. A player-owned generated
gift or a confirmed Surf change to an eligible existing Pikachu is a plausible
route; the player would withdraw the gift into the party and visit the beach.
The Virtual Console version uses a different entrance check.
[Party check](https://github.com/pret/pokeyellow/blob/master/engine/pikachu/pikachu_status.asm)
and [beach script](https://github.com/pret/pokeyellow/blob/master/scripts/SummerBeachHouse.asm).

## Build-content approach

Ship original generator/save-editing code, a small numeric recipe catalog, and
ButterflyOS artwork. Read species and move names, sprites, base stats, growth
rates, initial/level-up moves and PP from the user's matching ROM at runtime.
Read player trainer identity from the selected save. Derived caches remain local
and must never be copied into release assets or the repository.

Do not bundle ROM fragments, distribution ROMs, extracted artwork/audio,
prebuilt Pokemon records, event donor saves or scanned promotional material.
The GB cache resolves names, sprites and species IDs. The new generator reads
base stats, types, catch-rate bytes, initial moves, growth rates and move PP
from the verified ROM. It generates random DVs and zero stat experience, and
the native helper appends the record using the player's trainer identity.

This is a design for **no bundled Pokemon game assets**, not a claim of zero
Pokemon IP or a legal clearance. Pokemon names/references are already present
in Butterfly Link. Gifts must be identified as generated equivalents; verified
historical recreation, where possible, would be a separate feature. The tool
must not label generated gifts as original official distributions.

## First implementation and validation

Mew and Surfing Pikachu use the player's trainer identity. Mew starts with
Pound; Pikachu starts with ThunderShock, Growl and Surf. Both arrive at level 5.
The other four distribution gift families are now implemented too. Special
moves fill a free starting-move slot; Rapidash already has four starting moves,
so Pay Day replaces Growl. Magikarp uses the slow growth formula from its ROM
data. These level-5 gifts do not reproduce historical levels or distribution OT
metadata. The Stadium group adds Amnesia Psyduck and the eight Castle gift species.
All are generated at level 5 with player OT and ROM-derived starting moves.
This does not reconstruct historical Stadium levels, OT, catch-rate variants
or every reward moveset.
Keep Stadium rewards separate. Start locally; remote gift delivery is not
needed for the user's ability to receive a gift in their own save.

Use the existing matching-ROM requirement, protected working copies, free-slot
selection, explicit preview/Commit and pre-write backups. Update the chosen
box's count, species list, terminator, names and record, synchronize active and
banked box data as required, and update checksums and the appropriate Pokedex
seen/owned state. Do not reset story flags or revive completed encounters.

Tests need to cover supported game revisions, correct species/level/experience,
types/catch-rate byte/DVs/stat experience, move IDs and PP, native text encoding,
full boxes, save reloads, backup/cancel behavior and unchanged unrelated records.
Validate that no derived ROM content enters packaging. Test Yellow's minigame
in the actual game with a withdrawn player-owned Surfing Pikachu before claiming
the unlock works. Reject unsupported languages and ROM layouts explicitly.

Automated validation passed 180 gift/save reload cases across Red, Blue and
Yellow, plus repeated gifts after switching boxes. Checks include player OT,
experience, move PP, native name terminators, active/banked PC persistence,
bank and individual box checksums, Pokedex flags, occupied-slot refusal,
mismatched/modified ROM refusal, existing-output protection, backups,
full-box/malformed-record refusal, concurrent-save-change refusal and both
preview/confirmation cancellation paths.
Private fixture ROMs and saves remain unchanged. Yellow's beach minigame has
not yet been validated in-game.

The first PC-box change also initializes unused SRAM box headers, matching the
game's own [save/box initialization workflow](https://github.com/pret/pokered/blob/master/engine/menus/save.asm).
Original active-box records are retained.

The expanded generator uses the verified [Magikarp](https://github.com/pret/pokered/blob/master/data/pokemon/base_stats/magikarp.asm), [Fearow](https://github.com/pret/pokered/blob/master/data/pokemon/base_stats/fearow.asm) and [Rapidash](https://github.com/pret/pokered/blob/master/data/pokemon/base_stats/rapidash.asm) ROM layouts and [move IDs](https://github.com/pret/pokered/blob/master/constants/move_constants.asm). Stats, types, growth rates and PP are still extracted from the user ROM.

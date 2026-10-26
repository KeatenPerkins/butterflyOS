# Bdex acquisition guide: sources and validation

The pending post-20261026 build extends the device's Where to find action across
Gen 1–3. It never edits a game, save or collection. No build/release is implied by
this source change; live UI validation and a subsequent image test are required.

## Data boundaries

- Gen 1 grass/cave and Surfing records continue to be decoded from the qualified
  user's ROM by `butterflyos-bdex-locations.py`.
- Other acquisition records (including Gen 2/3 encounters) are offline reference
  facts. They are not presented as extracted from the user's ROM. A full-ROM
  SHA-256 allowlist identifies the selected game and supported revision first.
- Evolution tables are compiled separately for each generation/game family from
  pret's original-game research, not from modern-generation evolution rules.
- Shipped JSON contains numerical species IDs, acquisition methods, location
  labels, levels, conditions and evolution parameters. Names/sprites still come
  from the user's shared ROM cache. Original game dialogue and ROMs are absent.

## Pinned references

Encounter facts use [PokéAPI's CSV data](https://github.com/PokeAPI/pokeapi/tree/2bf639e5572812a67d2b94903fdcb9d095f5aeb2/data/v2/csv)
at `2bf639e5572812a67d2b94903fdcb9d095f5aeb2`. The exact files are enumerated by
`CSV_INPUTS` in the generator. Its BSD-3-Clause license and attribution are in
`licenses/pokeapi.txt` and shipped in the image's ButterflyOS license directory.

Evolution references:

| Project | Revision | Evolution table |
| --- | --- | --- |
| [pokered](https://github.com/pret/pokered) | `171e2c204f9c1ff8e577ca387a4bbb009e130843` | `data/pokemon/evos_moves.asm` |
| [pokeyellow](https://github.com/pret/pokeyellow) | `31b7c2ea2ba6c8c64ed083723fbaa8cbb74669cb` | `data/pokemon/evos_moves.asm` |
| [pokegold](https://github.com/pret/pokegold) | `fc702b6d922aecce274782d68bba8639936a1182` | `data/pokemon/evos_attacks.asm` |
| [pokecrystal](https://github.com/pret/pokecrystal) | `5c877ef55197039c9676e8e3eec6d254b1c40fe8` | `data/pokemon/evos_attacks.asm` |
| [pokeruby](https://github.com/pret/pokeruby) | `5784633ce4ef7ade1a7f2d2d0c288e3d5e6cdd7f` | `src/data/pokemon/evolution.h` |
| [pokeemerald](https://github.com/pret/pokeemerald) | `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` | `src/data/pokemon/evolution.h` |
| [pokefirered](https://github.com/pret/pokefirered) | `ce6406d8c2eaf46d543c8a2606de0c3cb1951982` | `src/data/pokemon/evolution.h` |

Historical runtime restrictions are also checked against the corresponding
`src/pokemon.c` / evolution routines. The generator's output includes input-file
SHA-256 hashes and source revisions. Upstream data changes do not silently affect
an installed device; the guide makes no network requests.

## Corrections and qualifications

- Friendship threshold is **220**, rather than a newer generation's threshold.
  Gen 2 day is 04:00–17:59 and night 18:00–03:59. In R/S/E the evolution windows
  are 12:00–23:59 and 00:00–11:59. FR/LG disable time-of-day evolution.
- FR/LG's tables retain Eevee time-of-day entries even though the engine disables
  them. The guide explains trading to R/S/E rather than claiming local evolution.
- FR/LG non-Kanto evolutions require the National Pokédex. Breeding uses Four
  Island; cross-region trades require Celio's Network Machine quest.
- The reference's FR/LG beast records incorrectly use a second Elite Four win
  as a prerequisite. The displayed guide instead identifies Celio's completed
  Network Machine quest and the starter-dependent beast.
- Crystal's Virtual Console Celebi record is not displayed as a normal encounter
  for the qualified original retail ROM. The original event restriction and
  Blink's separate quest activation are explained.
- Emerald's Old Sea Map distribution was Japanese; ticket islands require both
  their access item and event flags. They are labelled as historical events.
- Wurmple's branch cannot be changed by switching time. Shedinja needs an empty
  party slot. The original Gen 3 `CreateShedinja` routines do not require a spare
  Poké Ball; the later-generation ball requirement must not be applied here.
- Breeding facts use numerical family relationships and Gen 3 incense exceptions.
  They do not imply that the required parents or Ditto are locally obtainable.

This guide intentionally does not claim exhaustive walkthrough coverage. NPC
trade entries provide locations/methods, not every requested exchange. Encounter
conditions and one-time/story choices should be checked against actual gameplay
when testing. An empty entry never establishes that a species is unobtainable.

## Regenerate on the development PC

```sh
python3 tools/bdex-build-acquisition.py --download \
  .cache/bdex-acquisition \
  projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-bdex-acquisition.json
python3 tests/butterflyos-bdex-acquisition-test.py
python3 tests/butterflyos-bdex-locations-test.py
```

Omit `--download` to regenerate from the already downloaded pinned inputs. Input
CSV/source files stay in `.cache`, outside the packaged image.

## Live spot checks

1. Gen 1: Alakazam/Machamp trade evolution; Raichu in Yellow; a fishing species;
   a fossil, gift, NPC trade, legendary and version-exclusive evolution family.
2. Gen 2: Steelix/Slowking held-item trades; Espeon/Umbreon time windows; all
   Tyrogue branches; baby breeding; Crystal Celebi's historical restriction.
3. Gen 3: FR/LG versus R/S/E Eevee; Feebas/Milotic; Wurmple; Shedinja;
   Sea/Lax Incense eggs; starter-dependent beasts; ticket islands.
4. Missing species can open the guide without importing a save. Cancel ROM
   selection, use a ZIP, return with B, and repeat with Bluetooth/HDMI.

The automated checks render every species in every game (3,136 combinations),
exercise the historical exceptions above, and verify content-based qualification.
Gameplay accuracy is distinct from successful rendering and remains part of live
spot testing.

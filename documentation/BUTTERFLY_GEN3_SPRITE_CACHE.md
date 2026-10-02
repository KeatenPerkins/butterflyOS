# Butterfly Save Trade: Gen III sprite cache

This extractor reference belongs to the current **Butterfly Link** app.
Its user guide covers all three generations and their current limitations:
[Butterfly Link](BUTTERFLY_LINK.md).

ButterflyOS does not ship Pokémon artwork. The Save Trade tool can extract
front sprites and normal/shiny palettes from a user's own Gen III `.gba` ROM.
The extractor writes PNGs under:

```text
/storage/.config/butterflyos/save-trade/sprite-cache/<ROM-SHA256>/
```

Each cache contains a `manifest.json`, `front/` sprites, and `front-shiny/`
sprites. The ROM's complete SHA-256 and extractor version are recorded in the
manifest. A later launch returns a cache hit without reading or rewriting the
sprite files. Changing the ROM, including using a ROM hack with the same GBA
header code, creates a separate cache automatically.

The current extractor handles the English retail Ruby, Sapphire, Emerald,
FireRed, and LeafGreen layouts present in the project test set, including
revision-specific Ruby/Sapphire and FireRed tables. Emerald's additional front
animation frame is preserved as `*-frame2.png`; the first frame remains the
stable UI image.

Gen III shiny status is determined from the Pokémon's personality value and
original trainer ID in the save. The Save Trade inspect protocol reports
`shiny=yes` or `shiny=no` for party and boxed records, allowing the UI to select
the matching cached palette without modifying the ROM or save.

This is intentionally a user-storage cache rather than an image bundled in the
OS image. It keeps the distribution free of game artwork and leaves the user's
ROM as the source of the displayed assets.

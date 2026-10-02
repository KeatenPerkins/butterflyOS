# ButterflyOS Save Trade

**Historical plan (superseded).** The staging and network-disabled statements
below record the initial prototype, not current features. The installed app is
now called Butterfly Link; use [its current guide](BUTTERFLY_LINK.md) and
[current build status](CURRENT_BUILD_STATUS.md). Retain this document as design
history rather than installation or testing instructions.

Status: protected one-device, same-generation PC-box transfer is staged for
Generation I, II, and III. It has not yet been included in a new image or
tested on hardware. Network transfer remains disabled.

## Sprite preview and cache

Butterfly Link includes a full-screen SDL sprite-preview browser. It presents
the selected save's boxed Pokémon in a readable list and renders the selected
front sprite in a dedicated lower preview pane. Cache creation is an explicit
user action: the image includes extractors but contains no Pokémon artwork.

- Gen I cache: English retail Red, Blue, and Yellow; monochrome front sprites.
- Gen II cache: English retail Gold, Silver, and Crystal; normal and shiny
  front sprites.
- Gen III cache: supported English retail Ruby, Sapphire, Emerald, FireRed,
  and LeafGreen layouts; normal and shiny front sprites.

Each cache is keyed to the SHA-256 of the user-provided ROM under
`/storage/.config/butterflyos/save-trade/sprite-cache/`. Unknown ROM layouts
fail without creating a cache, rather than risking incorrect artwork. The
preview browser is deliberately separate from transfer commit until the full
SDL selection flow replaces the remaining terminal-dialog selection screens.

## Goal

Provide a reliable, link-like way to move Pokémon between two Miyoo Flip V2
devices without emulating the Game Boy Advance cable protocol. The feature
operates on user-selected emulator save files and never needs to copy ROMs.

## First milestone

The first implementation is a local, offline same-generation box-Pokémon
transfer helper. It accepts explicit save files and PC-box slots, creates
output copies, validates the saves, then swaps or copies the complete Pokémon
records through PKSav. PKSav recalculates the generation-specific checksums.
Input saves are never written by the helper.

The command is intentionally narrow: party slots, cross-generation conversion,
trade evolution, and network transport come later. Restricting the first step
to boxed Pokémon makes the write operation easy to audit and test. Gen I/II
copy appends only to the next valid PC-box position, preserving the original
contiguous box layout. Gen I-to-II transfer is deliberately unavailable until
the Generation II save loader is repaired and the conversion is independently
verified in-game. It is not safe to copy a raw PC record: Generation I and II
use different record layouts and species indexes.

## Planned Time Capsule conversion rules

Butterfly Link will model the original Gen I/II **Time Capsule** rules rather
than treating a cross-generation request as an unrestricted save edit.

- **Gen I -> Gen I:** valid boxed Pokémon can be swapped or copied.
- **Gen I -> Gen II:** a valid Gen I boxed Pokémon can be copied. Butterfly
  Link will convert its Gen I species index through the Time Capsule table,
  preserve compatible identity/training data, carry the Gen I catch rate into
  the Gen II held-item byte, and initialize Gen II-only fields safely.
- **Gen II -> Gen I:** a copy or swap is allowed only for one of the original
  151 species with a fully Gen I-compatible move set. Gen II-only species,
  eggs, and Gen II-only moves are rejected with an explanation; Butterfly Link
  must never silently alter a Pokémon to force compatibility.
- A cross-generation **swap** is available only when both directions pass those
  checks. A one-way **copy** remains available when only Gen I -> Gen II is
  compatible.
- Conversion is performed only in working output copies, then validated before
  the existing backup and atomic commit/rollback process may run.

The first version remains PC-box-only. Party transfers, trade-evolution rules,
and cross-save Gen I/II writes stay disabled until converted outputs have been
opened and verified in their destination games.

The **Butterfly Link** Tools entry now provides generation-aware save
discovery, protected local Gen I/II/III box-swap/copy preparation, and a
separate commit action. The commit action creates verified backups before
replacing either selected save and attempts rollback if the second replacement
fails. It is not yet a two-device network feature and should not be presented
as working cable emulation.

## Next feature: Trade Evolution Assistant

Trade evolution is a planned extension of a **Swap**, not of Copy. Since
Butterfly Link edits saves rather than running a cable session, it must model
the evolution deliberately and visibly:

1. After both boxed Pokémon are selected, Butterfly Link checks the incoming
   Pokémon on each side for that generation's trade-evolution rule.
2. It presents each eligible evolution, for example `Kadabra -> Alakazam`,
   with an explicit **Evolve / Keep unevolved** choice. This is equivalent to
   allowing or cancelling the normal in-game evolution animation.
3. The review screen includes the selected choice before the user commits.
   The existing verified backup and rollback process remains mandatory.
4. The helper changes only the receiving working save, preserves Pokémon
   identity data (OT, personality/shiny state, IVs, EVs, moves, and level),
   recalculates derived data/checksums, and verifies the result before commit.

Initial scope is same-generation Gen I, II, and III boxed swaps. It includes
ordinary trade evolutions, plus Gen II/III held-item evolutions where the real
game supports them. Held evolution items are consumed; an Everstone suppresses
evolution where applicable. Cross-generation conversion, party transfers, and
automatic evolution after Copy remain out of scope. Every supported evolution
must be tested in its original game after the save is written.

## Planned user flow

1. The user opens **Butterfly Link > Save Trade** on each device.
2. Each device selects a local ROM/save pair. The app displays the exact card,
   path, save size, and checksum and creates a restore point.
3. The devices exchange only save metadata and a list of selectable Pokémon.
   ROM files never cross the connection.
4. Each player selects a Pokémon and reviews the proposed exchange.
5. Both players confirm the same transaction ID.
6. Each device writes an isolated working save, verifies it, and atomically
   commits it to the selected original path. A disconnect or mismatch leaves
   the original untouched and exposes a one-button restore.

## Safety rules

- Never modify a library save until both sides confirm.
- Keep a pre-trade backup and a post-trade copy.
- Refuse to overwrite a save that changed after selection.
- Require compatible generation/game rules before transfer.
- Reject malformed, empty, duplicate, or out-of-range Pokémon records.
- Make the first public version box-only and mark it experimental.

## Engine choice

PKSav is a small, dependency-free C library under the MIT license. Its
upstream documents complete support for Generation I, Generation II, and Game
Boy Advance save files. It is a better fit for this device than embedding a
large desktop-oriented editor. ButterflyOS will preserve the upstream license
and attribution and will not copy PKForge's UI or code.

## Staged implementation

1. Local Gen I/II/III box swap/copy helper and workstation tests.
2. Save discovery/backup UI integration on one Flip.
3. Test same-generation Gen I/II workflows with real user-owned saves.
4. Replace the remaining terminal-dialog transfer selection/confirmation flow
   with the full SDL interface, including the lower sprite preview.
5. Add and test the Trade Evolution Assistant for same-generation boxed swaps.
6. Two-device metadata and transaction protocol over the existing ButterflyOS
   LAN transport, with no emulator launch.
7. Gen I/II adapters for any later cross-generation work.
8. Party-slot support, cross-game rules, and optional bank storage.
9. Revisit true cable emulation only if a concrete user need remains.

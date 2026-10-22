# ButterflyOS vision

ButterflyOS is an open-source, ROCKNIX-based operating system built to make a
handheld feel like a dedicated game console: approachable, controller-friendly,
and dependable without requiring Linux or RetroArch knowledge.

The current released and hardware-tested target is the **Miyoo Flip V2**.
Support for additional Miyoo hardware is a future possibility, dependent on
access to devices, technical information and physical testing. Shared branding
or a similar chipset alone does not establish compatibility.

## What guides development

- **Simple everyday use.** Finding games, changing common settings, adding files
  and updating should have clear instructions and predictable controls.
- **Tested defaults with room to customize.** Games should start with sensible
  emulator and control settings. Users can choose themes, alternative emulators
  and per-system or per-game settings without making tuning a prerequisite.
- **Protect saves and recovery.** Verify important writes, retain recovery
  information, explain destructive operations and make backups understandable.
  Backup features supplement the user's own copies; they cannot guarantee
  recovery from every interruption or hardware failure.
- **Measure before changing.** Judge performance, power use and reliability on
  real hardware. Keep resource use modest and experimental changes separate
  until testing supports a release.
- **Clear limits.** Document supported games and hardware, known problems and
  workarounds. Distinguish a working default from a guarantee for every game.
- **Responsible distribution.** Users provide their own games and proprietary
  BIOS files. Keep licenses, source revisions and build modifications available;
  do not bundle Pokémon ROMs, saves or extracted sprite caches.
- **Maintainable foundations.** Build on ROCKNIX and upstream emulator work,
  keeping ButterflyOS changes documented and avoiding unnecessary divergence.

## A connected Pokémon experience

Three complementary tools extend the games without replacing ordinary play:

- **Bslap** provides live same-generation trades and battles between two
  supported devices on a local network.
- **Blink** edits supported saves for transfers, generated gifts and qualified
  native event experiences.
- **Bdex** stores a collection outside the games, supports compatible copy
  exports and offers an optional read-only local web viewer.

They use the user's own files. Their generation, ROM and save requirements are
part of the product, rather than details users should have to discover by trial
and error.

Success means an owner can install safely, add games, play, manage saves and
recover from common problems using clear documentation and device controls.
See [Features](../documentation/FEATURES.md) for released capabilities and the
[roadmap](ROADMAP.md) for priorities and possible future work.

# ButterflyOS roadmap

Reviewed **October 22, 2026**, following **v1.4.0**, build **20261022**.
This page describes direction, not release dates or commitments. Future work
requires implementation and testing before it becomes a supported feature.
The currently released and hardware-tested target is **Miyoo Flip V2**.

## Released

- **Console interface and customization:** controller-operated menus, readable
  save-state selection, themes and instructions for creating custom themes.
- **Emulation and controls:** tested emulator defaults, gpSP as the normal GBA
  default, saved system/game overrides and Bluetooth hotkey improvements.
- **Power and display:** tested deep lid sleep, charging indication, lower
  minimum brightness and a screen-only lid option for HDMI use. Battery readings
  and sleep/peripheral edge cases still have documented limitations.
- **Storage and recovery:** device-local preloader backup/export and restore,
  game-transfer documentation including USB Gadget File Transfer, SD Card Info,
  and optional second-card ordinary-save backups with restore instructions.
- **Updates and diagnostics:** online full-image updates, retained user data
  during normal updates, checksummed downloads and bounded persistent logs.
- **Blink:** supported Gen 1–3 save trades/copies, compatible forward-generation
  copies, gifts and qualified Gen 3 island-event enable/replay options.
- **Bdex:** Gen 1–3 collections, duplicate protection, filters, compatible copy
  exports, sprite refresh and an optional read-only local web viewer.
- **Bslap, introduced in v1.4.0:** live same-generation local-network trades and
  battles for supported English Gen 1, Gen 2 and Gen 3 games, with session save
  safeguards and a dedicated Gen 3 backend isolated from normal game launches.

These are summaries, not universal compatibility guarantees. See
[Features](../documentation/FEATURES.md),
[release notes](../documentation/RELEASE_NOTES_v1.4.0.md) and
[current build status](../documentation/CURRENT_BUILD_STATUS.md) for scope and
recorded validation.

## Current priorities

1. **Maintain release reliability.** Investigate reproducible reports, protect
   saves and recovery paths, and validate installation, updates, normal game
   launches, sleep/resume, storage and HDMI when related code changes.
2. **Follow up on Bslap limitations.** Track the intermittent Gen 3 room-exit
   communication error, broaden game-pair testing as needed and qualify Gen 1/2
   real-time-clock persistence across cores. Letting one player initiate room
   exit is the current Gen 3 workaround, not a confirmed fix.
3. **Improve everyday guidance.** Keep installation, transfers, backups,
   emulator choices and the three Pokémon tools understandable to new users.
   Update documentation alongside behavior changes.
4. **Tune from evidence.** Continue targeted emulator, controller, battery and
   charging investigations when useful data or reproducible problems are
   available. Avoid replacing working defaults solely because a component is
   newer or another system uses it.

These are maintenance priorities, not a claim that each item has an active
implementation or a scheduled release. Open hardware and software limitations
remain in [Known issues](../documentation/KNOWN_ISSUES.md).

## Possible future work

- **Background music during games (maybe):** play the user's Media music while
  optionally muting game audio, with controller controls for pause/resume,
  previous/next track and separate music volume. Investigate audio sharing,
  hotkey conflicts, sleep/output changes and performance before committing to
  implementation. No work or release is scheduled.
- **Additional Miyoo devices:** assess hardware samples and documentation,
  then establish device-specific builds, safe recovery and physical validation.
  No additional model is promised or supported by this roadmap.
- **Broader Bslap linking:** evaluate Gen 1 ↔ Gen 2 Time Capsule trading and
  other link activities separately. Internet play and external link adapters
  are outside the current released scope.
- **More guided management:** consider clearer BIOS status, diagnostic export
  and recovery workflows where they reduce the need for terminal access.
- **Further interface polish:** improve translations, accessibility, navigation
  and customization based on user feedback and device testing.
- **Measured emulator alternatives:** evaluate specific cores or settings when
  there is a plausible compatibility, performance or battery benefit. Do not
  assume a newer emulator is faster or promote experiments without testing.

The named Battery Saver/Balanced/Performance policy layer from the original
vision is not a released unified feature. Current CPU/GPU governor and emulator
choices are documented in [Emulators and performance tuning](../documentation/EMULATORS_AND_PERFORMANCE.md).
This roadmap also makes no LTS support-period commitment.

## Development history

The [October 2 roadmap](history/ROADMAP_20261002.md) preserves the alpha milestones
and early crash investigations as historical records. Its disabled-suspend
instructions and unimplemented-feature descriptions are superseded by current
release documentation. Detailed implementation plans are supporting development
records, not promises of future work.

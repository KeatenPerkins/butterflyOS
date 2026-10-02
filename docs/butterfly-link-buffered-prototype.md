# Butterfly Link buffered-trade prototype

Historical emulator-link research. This does not describe the installed
save-transfer Butterfly Link app. See [the current user guide](../documentation/BUTTERFLY_LINK.md).

## Goal

Prototype Pokémon Gen 1/2 trading without making the GBA serial bus depend on
round-trip Wi-Fi timing. Each emulator keeps its local cable timing; the network
exchanges a validated trade transaction at safe game checkpoints.

## Proposed flow

1. Both players enter the Cable Club normally.
2. The local link adapter performs a short preparation exchange and records the
   player/trade payload needed by the game.
3. Each side sends a framed transaction to its peer:
   - protocol version
   - generation and game-region identifiers
   - ROM/save identity metadata (not the ROM itself)
   - transaction ID and monotonic step
   - payload length, checksum, and payload
4. The receiver validates the frame and Pokémon data before accepting it.
5. Both sides exchange an explicit commit acknowledgment.
6. The local adapter supplies the prepared response bytes to the game and lets
   the normal trade sequence finish.
7. A disconnect before commit aborts and restores the protected save copy.

The current offline prototype includes a conservative Gen 1 structural
validator. It checks the fixed `0x0A + 0x1A2 + 0xC5` section layout, party and
species-slot consistency, active Pokémon levels, and a commit digest. It does
not yet apply a region-specific species/move table or modify save data.

The serial collector now accepts ordered `serial-read` events and an explicit
`transfer-complete` boundary. It ignores local writes for payload assembly,
rejects sequence gaps, duplicate completion data, overlong traces, and events
after completion, then passes the resulting sections through the validator.

The development trace extractor can parse the existing bounded `BF poll`,
`BF start`, `BF finish`, and related diagnostic lines into raw JSONL records.
Those records preserve GBA 16-bit words for replay and mapping; they are not
treated as Gen 1 payloads until a game-specific adapter proves the conversion.

SameBoy's two-console link callbacks can be instrumented with the opt-in
`002-butterflyos-gen1-serial-trace.patch`. With
`BUTTERFLY_LINK_GB_TRACE=1`, it records at most 4096 transmitted/received byte
pairs per virtual console as `BFGB byte` lines. The AArch64 core compiled
successfully in the existing build tree; it has not been deployed to either
Flip and is not part of the current image.

## Safety rules

- Never write an incoming payload directly into the user's original save.
- Require matching generation and compatible protocol versions.
- Reject stale, duplicate, malformed, or out-of-order transaction frames.
- Commit only after both peers acknowledge the same transaction ID and step.
- Keep a recoverable pre-session save backup.

## Scope

Gen 1/2 is the first target. Gen 3 remains a separate project because its link
protocol and multiboot/wireless behavior are substantially different.

The open-source `PokemonGB_Online_Trades_and_Battles` project is an architectural
reference for synchronized and buffered modes and its sanity checks. Its source
and license must be reviewed before any code is reused. DoubleCherryGB is another
reference for virtual link-device behavior and Gen 1/2 network trading.

## Test milestones

1. Offline frame/transaction loopback tests.
2. Two-process LAN transaction tests with packet delay, duplication, and loss.
3. Synthetic link-register tests independent of Pokémon ROMs.
4. Gen 1 payload safety tests with protected saves.
5. Map real emulator serial bytes into the validated Gen 1 payload sections.
6. Gen 1 trade with protected saves.
7. Gen 2 trade and trade-evolution verification.
8. Only then consider enabling the adapter in a ButterflyOS build.

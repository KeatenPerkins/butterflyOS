# Bslap: live Pokémon trades and battles

<img src="assets/bslap.png" alt="Bslap arena icon" width="144">

Available from **v1.4.0**, build **20261022**.

Bslap appears in the normal Tools menu alongside Blink and Bdex; Advanced Mode
is not required. Open **Tools → Bslap** to trade or battle between two ButterflyOS
devices on the same local network. Each player controls their own game. Blink remains the
separate save-editing tool; Bdex stores your collection outside the games.

The next local test build replaces Gen 1/2 dual emulation with a dedicated
single-instance Gambatte Netpacket backend. Each device runs its own game, with
no peer ROM or save exchange. The previous SameBoy backend remains available as
a development fallback. See the [test plan](BSLAP_SINGLE_INSTANCE_PLAN.md) for
qualification status; this change has not yet been published.

## Supported games

- **Gen 1:** English Red, Blue and Yellow.
- **Gen 2:** English Gold, Silver and Crystal.
- **Gen 3:** English Ruby, Sapphire, Emerald, FireRed and LeafGreen.

Choose two games from the same generation. Gen 1/2 ROMs must match the English
revisions already qualified for Blink; Gen 3 is identified by its English game
header. Compressed ROMs, ROM hacks and other languages are not currently offered.
A valid ordinary `.srm` save must be beside each selected ROM. No ROMs, saves,
Pokémon graphics or extracted game data are included with ButterflyOS.

Gen 1 ↔ Gen 2 Time Capsule trading is not currently enabled. The original games
support cross-generation trades through the Time Capsule, but not battles.
Internet play and GB-Link/ESP32 hardware are outside the current feature.

## Host and join

1. Save and exit any running games. Connect both devices to the same local
   network. Guest Wi-Fi or client isolation can prevent discovery.
2. On one device, open **Tools → Bslap → Host**, choose **Gen 1**, **Gen 2** or
   **Gen 3**, then select the game. Read the save notice and choose **Ready**.
   Stay in the waiting lobby; the game stays closed.
3. On the other device, open **Bslap → Join**, select the host and a compatible
   game, read the notice and choose **Ready**.
4. When the host shows **Both Players Ready**, choose **Start** on the host.
   Both games launch automatically. Choose **Continue** to load the ordinary
   save, then use the upstairs Pokémon Center Cable Club for a trade or battle.
   Gen 3 uses the cable rooms, rather than the wireless Union Room.
5. Save normally in both games after finishing and leaving the room. For Gen 1/2,
   save on **both games before either player exits**. Exit both games with the
   normal emulator-exit hotkey to return to Bslap. On the Flip's built-in
   controls, the default is **hold Menu and press Start twice**. This applies to
   Gen 1, Gen 2 and Gen 3, whether hosting or joining. Save in-game first.

Bslap uses the controller configuration generated for the current launch. The
next build fixes an ordering bug where a newly flashed card could retain the
initial Select hotkey in its Bslap session even though normal games used Menu.
Bluetooth controllers retain their configured hotkeys; connect them before
launching the session.

In the next build, Bslap's Gen 1 sessions select Gambatte's **Special 3** for
monochrome Game Boy rendering. Red/Blue use this palette; Yellow retains its
native GBC colors through automatic hardware selection. Gen 2 rendering and
normal-game Gambatte choices are unchanged. Both devices need matching Bslap
backends. The single-instance backend includes a clock-collision tie-break for
the first link request, sequence-tagged replies and recoverable byte waits.
The full rebuilt image still needs device testing.

B cancels a waiting lobby. Hosting does not start a game before the other player
is ready and the host chooses Start. No passwords or ROM data are exchanged.

The games’ own requirements still apply: have enough party Pokémon, satisfy
story/Pokédex restrictions and avoid incompatible Pokémon or moves. A game
refusing an ineligible trade is different from a connection error.

## Gen 3 known issue: leaving the room

Gen 3 can show a communication error when leaving the Trade Center or Colosseum.
For better results, **let only one player initiate leaving**. On the other device,
respond to the exit dialogue that follows. Avoid independently starting the exit
sequence on both devices. This improves results but does not guarantee success.

An exit error does not prove a trade was saved or lost. Check the ordinary saves
after restarting. Keep backups of important saves.

**This warning applies to Gen 3 only.** Gen 1 and Gen 2 use a different link
implementation and passed user testing without this room-exit error or crashes.

## Saves, backups and recovery

Every session has a unique folder:

`/storage/.config/butterflyos/bslap/sessions/<session>/`

It contains `session.json`, `before.srm`, `after.srm` when available, configuration
and launch logs. Automatic save states are disabled; use normal in-game saves.

**Gen 3:** gpSP links the independent games directly. In-game saves update each
selected ROM’s adjacent `.srm`; Bslap preserves before/after copies.

**Gen 1/2 in the next local build:** each device runs only its own selected ROM
and a local working save. Only serial-link messages cross the LAN. The original
save stays untouched during play. After a clean emulator exit, the validated
result is returned to its original path, unless the original save or clock
changed independently. Failed or conflicting results remain in the session
folder for recovery. Working files are under `content/local.srm`; the joining
frontend can also use `content/.netplay/local.srm`. The launcher distinguishes
an updated result from an unchanged seed copy. Existing appended save trailers
are preserved. Adjacent Gambatte `.rtc` sidecars are backed up as `before.rtc`
and returned when available. Save and RTC files are replaced individually;
the pair is not an atomic transaction if power is lost during return.

The earlier SameBoy backend runs both games on each device and exchanges
working save copies on TCP 55438. In that fallback mode both ROMs must exist
on both devices; the host owns `player1.srm` and the joiner owns `player2.srm`.
SameBoy RTC files remain in its session. Cross-core clock persistence is not
fully qualified; keep the session backups.

To restore the original backup:

1. Exit both games and Bslap.
2. Copy the current ordinary save somewhere safe.
3. Read the original save path in `session.json` and copy that session’s
   `before.srm` back to that exact path. If that session has `before.rtc`, restore
   it to the same game's adjacent `.rtc` path as well.
4. Open the game and choose Continue, rather than loading an older state.

For a failed Gen 1/2 session, preserve the entire folder before attempting
recovery. Do not copy the other player’s working save over your own.

## Validation and implementation

User testing passed Gen 1 and Gen 2 trades/battles and the tested Gen 3 game pairs,
including Ruby/Sapphire/Emerald, FireRed/LeafGreen, and FireRed or LeafGreen with
Emerald. This is not an exhaustive every-game, every-host-role matrix. The Gen 3
room-exit limitation remains. Final-image testing is separate from live staging.

Bslap packages its dedicated ARM32 RetroArch/gpSP pair separately from normal
emulator defaults. The next local build uses native RetroArch with its dedicated
Gambatte Netpacket core for Gen 1/2, retaining native SameBoy as a fallback.
Installed hashes are checked against `/usr/share/bslap/backend.json`.
Local discovery uses UDP 55436; lobby readiness uses TCP 55437; gameplay uses
55435. Only the SameBoy fallback uses the temporary save exchange on TCP 55438.

Build inputs and reproduction notes are in
[the backend build guide](../tools/bslap/README.md).


### Join search in the next build

Join keeps looking for a compatible host for up to **60 seconds** when none is
found, with an on-screen countdown. Press **B** to cancel and return to Bslap.
Hosts appear promptly once discovered; you do not need to wait the full minute
when a compatible host is already available.

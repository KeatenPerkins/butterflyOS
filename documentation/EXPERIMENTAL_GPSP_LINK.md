# Experimental GBA multiplayer development notes

Branch: `experimental/gpsp-link-20261021`, based on stable source `fe7d04e62e`.
This is the October gpSP plan, not the older September custom mGBA/SIO prototype.
No kernel changes are required. A separately installed development RetroArch32
and newer gpSP are now being evaluated; the stable image remains unchanged.

## Current status and accepted known issue

Development may continue with the room-exit error documented as an experimental
limitation. Trades, battles, ordinary save persistence and repeated activities
have passed local testing, but reliable room exit has not been established.
The current live comparison uses the newer frontend with the plain handshake
candidate and normal Wi-Fi power saving enabled. Earlier sections below record
historical experiments, not the current installation instructions.

**Known issue: communication error when leaving a link room.** The user has
observed better results when only one player initiates leaving and the other
responds to the propagated exit dialogue. Independently initiating exit on both
devices can trigger the error, including with the newer frontend and diagnostic
logging removed. This workflow improves observed results; it is not a guaranteed
fix. Save normally on both games after returning safely outside the room.

See [Bslap guide](BSLAP.md) for the
current user-facing scope, exit guidance and remaining integration work. Keep
this feature on the experimental branch; accepting the limitation does not
qualify it for the stable release or authorize publishing an image.

## First live test

Both development devices report build 20261020 and matching binaries:

- RetroArch32 SHA-256: `2905e5bc0e24a97800cf2ff26aa851eb1f1f569d643457bcfa25862fd081c521`.
- gpSP SHA-256: `7c062b444f4ee2db949f5d6250f4d0dcd5f34f02f6f6bf7b5c31435f23de9978`.
- Current pinned gpSP: `b0d5d27ae51c23f514974ddffa5760f1e1d05d9b`.
- Current pinned RetroArch: `bdba046fa6766380bc2457532f38e589df769aaf`.

Disposable content is staged on each card at:
`/storage/roms/gba/Wireless Link Test/Emerald - Wireless Test.gba`, with an adjacent
ordinary `.srm` save. Both start from the same event-test fixture; each device has
its own physical copy. Original library and PC saves remain untouched.
A game-specific gpSP `.opt` requests `gpsp_serial = "rfu"`.
Verify the running core, active option and effective save path before playing.

Start with normal launches, then use RetroArch host/join on the same LAN.
Require separate local player control and independent saves. Milestones:
connect, discover the partner in Emerald's wireless facilities, complete a trade,
save/reload both results, battle, normal exit, disconnect recovery. These tests
have not yet passed. Log transport/core errors before expanding the work.

Keep the released core intact. If existing wireless support has a concrete
blocker, evaluate a separately built newer 32-bit gpSP with explicit Pokémon
cable mode. Do not combine the older mGBA patch stack with this experiment.

## Reference projects

- [GBLink Netplay Bridge](https://github.com/GB-Link/gblink-netplay-bridge):
  RetroArch/gpSP interoperability; `src/engine/mpk1.ts` and netplay client code.
- [gpSP core options](https://github.com/libretro/gpsp/blob/master/libretro/libretro_core_options.h):
  newer revisions expose both RFU and Pokémon cable modes; our pinned revision
  exposes RFU but lacks the explicit Pokémon cable mode.
- [ESP32 Switch bridge](https://github.com/GB-Link/GB-Link-Switch-LDN): later
  hardware interoperability reference. Neither ESP32 nor GB-Link hardware is
  needed for the first two-device emulator test.

## First live result — October 21, 2026

Both test games launched normally with RetroArch32/gpSP. Launch logs confirmed
RFU game-specific options, Netpacket registration and saves redirected into the
separate Wireless Link Test directory. Host was enabled on the first local test
device via RetroArch's local UDP command; the second joined through LAN discovery.
Both logs confirmed host/player 1 and client/player 2, with no disconnection
reported at the observed milestone. Initial connection ping was about 192–203 ms.
UPnP/public-internet mapping failed, but the direct LAN connection succeeded.

The user confirmed Union Room interaction working and reached the trade screen.
Completed trade, independent save persistence, battle and interruption recovery
remain unverified at this point. Both on-disk test saves still matched the starting
fixture SHA-256 at this observation; this does not rule out changes in emulator RAM.
No replacement core, kernel change or custom full image was required.

First actual trade attempt failed with an in-game communication error on the host.
Both RetroArch processes remained running and the TCP session remained established;
neither log reported a netplay disconnect. Both disk save hashes still matched the
starting fixture. A subsequent 12-ping check in each direction had no loss, with
averages 5.781 ms and 6.586 ms (maximum 14.593 ms); this does not measure conditions
at the precise failure instant. Wi-Fi power saving was on on both devices.
The core compiles RFU diagnostics out unless RFU_DEBUG is defined, so existing
logs do not identify the emulated adapter failure. No successful trade claimed.
Raw private test logs are retained under `.cache/gpsp-link-tests/` (not committed).

For retry 2, both emulators were closed normally and each first-attempt save was
preserved on its device and in the private local test cache. Normal emulator exit
flushed changes to both saves, so the earlier matching disk hashes were only a
mid-session observation. The user located the communication error during the
trade sequence; animation progress is not otherwise instrumented.

The second device now uses a separate existing Emerald fixture with a different
trainer ID and three party Pokémon; the original starter fixtures have zero party
Pokémon and were unsuitable for immediate trading. Sector checksums/family layout
and the native save inspector passed. ROM, gpSP, RetroArch and RFU settings remain
unchanged. The first device retains its existing disposable working save. Relaunch
using the ordinary save, not an auto-resume state.

Retry 2 initially hit Emerald's trade-eligibility checks: the earlier-progress
second save lacks National Dex (flag 0x896 clear; variable 0x4046 zero). Most first
save party members were non-Hoenn species. Emerald's src/trade.c blocks giving a
non-Hoenn species to a partner without National Dex. A Hoenn-eligible pairing was
requested. The user then reported a completed trade after selecting appropriate
regional Pokémon. This is the first reported completed trade in the current gpSP
experiment; independent on-disk results and ordinary-save reload remain to verify.
No emulator replacement, kernel change or Wi-Fi setting change was made.

After the completed trade, leaving the room produced another in-game communication
error on the first device. RetroArch/TCP still remained connected. With both
emulators left running, the pre-flush disk saves were backed up and the local
`SAVE_FILES` command returned OK on both endpoints. Native inspection then passed:
the first device had Torchic personality 2286830441 (from the second fixture), and
the second had Kyogre personality 3918605425. Both post-flush files were retained
separately on-device. Thus the trade reached valid on-disk saves despite the later
exit error; ordinary reload and reliable session teardown still need testing.

## Diagnostic retry prepared

The user confirmed both traded Pokémon persisted after reopening. The exit error
remains unqualified and the original identical-save test's communication failure
has not been attributed to trainer identity. A fresh upstream comparison at gpSP
`5819380c2ffb0900219d700a382ee68c464ebb99` found no confirmed fix in the relevant
RFU disconnect/expiry/wait-timeout paths. Newer core cable mode remains a separate
possible experiment; no upstream upgrade was installed.

A separate diagnostic build of our pinned core is now installed on both test
cards, with bounded RFU error/teardown probes and a Tools launcher. No original
core or normal game entry was replaced. ARM32 build/ELF/dependency checks and
120-frame headless smoke checks passed on both devices; RFU probes fired and
original test save hashes stayed unchanged. These checks do not qualify actual
UI/audio or a linked session. See [diagnostic tools](../tools/gpsp-link/README.md).

### First passing diagnostic session

The user completed one trade, left both rooms without errors, saved in-game and
exited normally. Both RetroArch processes were closed. The session archives show
Kyogre personality 3918605425 back on the first device and Torchic personality
2286830441 back on the second, consistent with exchanging the previous trade back.
Both saves passed native inspection and before/after files passed strict section
checksums and Emerald-family validation. Before/after saves and logs are archived
privately in `.cache/gpsp-link-tests/20261021-diagnostic-pass`.

The second device logged a game-requested RFU local disconnect, and the first
logged remote disconnect and the corresponding wait-disconnected response. No
wait-timeout or peer-expiry probes were logged in this run. Normal emulator exit
logged SRAM writes to the disposable test paths. This does not establish that the
intermittent error is fixed: diagnostics intentionally change no RFU protocol or
timeout policy, but logging and build differences can affect timing. Repeat tests,
role reversal, battle, and interruption recovery remain outstanding. Reload of
these particular post-session saves still requires user confirmation.

The user reopened both diagnostic games and confirmed the traded Pokémon remain.
Ordinary-save reload therefore passed for the first clean diagnostic session.
The next controlled test reverses RetroArch roles: second device hosts, first joins.

### Reversed-role retry: post-trade standby

With the second device hosting RetroArch, the user reported prolonged post-trade
communication standby. Both RetroArch processes answered GET_STATUS as PLAYING,
TCP remained established, and five-ping samples in each direction had no loss
(~5 ms means). No RFU wait-timeout/peer-expiry/disconnect trace was captured at
that point. This is not sufficient to identify the application's wait condition.
Wi-Fi power saving was temporarily disabled on both devices as a single-variable
live probe; no persistent boot policy was changed. Recovery has not been confirmed.

Both test saves were backed up and SAVE_FILES returned OK on both. Inspection
showed Wingull personality 3149050902 on the first device and Kyogre personality
3918605425 on the second, consistent with the trade reaching both saves despite
standby. Records are retained under `.cache/gpsp-link-tests/20261021-reversed-role-standby`.
Whether both screens show standby or a remaining confirmation prompt is pending.

Both screens were confirmed to show communication standby. A brief debugger attach
was attempted and detached on both; optimized/LTO local symbols prevented typed
inspection. This intervention can affect timing and is part of the test record.
A subsequent read-only /proc/PID/mem probe, guarded by the exact diagnostic binary
hash and ELF mappings/symbol offsets, observed:

- first device: RFU client state 3, wait-event comstate 8, command 0x25,
  empty receive slots;
- second device: RFU host state 1, command receive comstate 2, command 0x26,
  client slot 0 present and two 16-byte receive entries, TTL 0.

These asynchronous snapshots demonstrate active adapter state but do not establish
which game or transport handshake failed. No fix was applied to those states.
The user still reported both screens at standby after Wi-Fi power saving was
disabled. The next proposed comparison is a separately named newer gpSP core's
explicit Pokémon cable backend (`mul_poke`), using separate disposable content,
leaving this RFU evidence and the released core intact. It is not yet built or
installed. Close games normally before replacing any test save or starting that
comparison. Temporary Wi-Fi power-saving policy needs restoration after testing.

## Newer cable-backend comparison staged

A separate upstream gpSP core at `5819380c2ffb0900219d700a382ee68c464ebb99`
was built with the established RK3566 platform adaptation and 32-bit toolchain.
It includes the explicit `mul_poke`/MPK1 Pokémon cable backend referenced by GBLink.
It does not contain a claimed RFU fix and has not replaced the release or RFU
cores. Core hash, provenance and rollback locations are in the tools README.

Both test devices now have Tools → GBA Cable Test with their own copied ROM/save
pair and game-specific cable options. The saves come from the last complete clean
session, not the later stalled session. Both passed native save inspection and
120-frame headless startup/exit checks without modifying their staged saves.
Actual controller/audio/link trade/exit/save-reload results remain pending.

### First cable-backend session passed

With the first local device hosting, the user completed a trade, left the Cable
Club without an error, saved normally and exited both games. Both processes were
closed and both logs recorded SRAM writes to the separate cable-test paths.
Inspection found Wingull personality 3149050902 on the first device and Kyogre
personality 3918605425 on the second, consistent with the exchanged pair. Native
inspection and strict section-checksum/family validation passed for both before
and after saves. Local private session archives are under
`.cache/gpsp-link-tests/20261021-cable-pass`.

No gameplay error or crash was reported for this session. Existing soft-filter
initialization failures and public UPnP mapping warnings remain in the launch
logs; they did not prevent this direct LAN trade. Connection-time ping was 21–31 ms.
Wi-Fi power saving remains temporarily disabled, unlike the original RFU baseline;
this pass therefore does not isolate a core/backend effect from network policy.
Post-exit reload, opposite RetroArch host roles, battles and repeated/interrupted
session behavior are still outstanding for the cable backend.

### Fresh-start cable session with reversed host roles passed

The initial reopen was found to load Auto Resume states. Both experimental
launchers now pass `-state_slot 0 -autosave 0` to disable automatic state loading
and saving for these tests. Existing state files are preserved. Earlier reopen
observations must not be treated as proof of an ordinary-save reload.

After exiting and relaunching, both logs contained no state-loading entry and
both generated configurations explicitly disabled automatic state loading/saving.
With the second local device hosting, the user completed a trade, left the room,
saved normally and exited to Tools on both devices without an error. Both emulator
processes exited, both logs recorded successful SRAM writes and launcher exit 0,
and native save inspection succeeded. The first device now has Wurmple personality
479038433; the second has Seviper personality 821669395. UPnP public port mapping
failed on the host, but direct LAN connection succeeded at 32–34 ms.

Private before/after saves and logs are archived under
`.cache/gpsp-link-tests/20261021-cable-reverse-pass`. A subsequent ordinary-save
reload confirmation, battles and repeat/interruption tests remain outstanding.
Wi-Fi power saving remains temporarily disabled; no stable core was replaced.

### Cable battle and room exit passed

Both games were relaunched without Auto Resume; native inspection still found
the previously traded identities in their ordinary saves. With the second local
device hosting again, the user completed a battle and left the room on both
devices without an error, remaining in-game. Both emulator processes remained
running and the RetroArch TCP connection remained established, which is expected
while Netplay is still active. The logs show connection-time ping of 9–10 ms and
no new link errors; the host again reported the unrelated public UPnP mapping
failure. This is a user-observed battle pass, not a protocol-level battle trace.
Repeated same-session room entry and interruption recovery remain unqualified.

### Repeated room use failed after battle

Without restarting after the successful battle, the user entered another trade.
The trade completed according to the user, but the first local device displayed
a communication error when leaving the room. Both emulator processes remained
alive and both TCP endpoints still reported ESTABLISHED when inspected. Both
had 36 bytes queued for transmission at that instant; this single snapshot does
not establish packet loss or a transport root cause. Wi-Fi power saving was off
on both. No corresponding link error was emitted to the ordinary core logs.
Copies of those logs are under the private cache directory
`20261021-cable-repeat-error`. No SRAM flush or process termination was requested
during this capture. The cable backend is therefore not qualified as reliable
for repeated room use; the earlier fresh-session successes do not resolve this.


Both games subsequently exited normally with successful SRAM writes and launcher
exit status 0. Final before/after saves and logs were archived. A separately named
bounded cable diagnostic core is now installed, startup-checked on both devices,
and selected by Tools → GBA Cable Test. No protocol behavior was intentionally
changed; live repeat testing remains pending. See the tools README for provenance,
hash and rollback.


### Instrumented battle followed by trade passed in user testing

The user completed a battle, then a trade, and confirmed both games left the
trade room without an error, remaining in-game. Both diagnostic cores were still
running and TCP remained established when inspected. Logs are archived privately
under `.cache/gpsp-link-tests/20261021-cable-diagnostic-pass`.

The logs contain repeated client handshake/connected transitions, nonempty
host receive queues at re-handshakes, and peer timeouts after serial activity
stops. No queue-full event was recorded. These events occurred in a successful
run, so they alone cannot identify the previous failure. Timeout after leaving
a room may simply reflect the game no longer exchanging serial data. The host
also recorded an earlier RetroArch client disconnect/reconnect during this
launch; this is not proof of an entirely uninterrupted Netplay session.
Some handshake/connected logging reached its per-category cap, limiting later
visibility. The instrumentation changes logging only, and this pass does not
establish a fix or reliable repeat-session behavior. Final in-game saves and
clean exit have not yet been requested for this diagnostic session.


The user then exited both games to Tools. Both emulator processes were gone,
both logs recorded successful SRAM writes and launcher exit status 0, and both
final saves passed native inspection. The archive now includes before/after
saves and final logs. Final parties contain Torchic/Luvdisc on the first local
device and Kyogre/Rayquaza on the second. This closes the diagnostic session as
a user-observed battle/trade/room-exit pass with clean save-file writes, not as
a proven protocol repair. The next investigation should compare reset and
re-handshake handling rather than repeatedly asking for the same unmodified test.


## RCNT mode-transition candidate

Source inspection found `write_rcnt()` passed the old RCNT value as SIOCNT and
used the old RCNT for both mode calculations. A GPIO-to-multiplayer transition
can therefore skip `serialproto_reset()`. The candidate computes modes from the
actual SIOCNT and the respective old/new RCNT values. No handshake thresholds,
queue handling, packet format or networking policy are changed.

`tools/gpsp-link/check-rcnt-reset.py` compiles the actual extracted upstream
handler against register stubs: GPIO-to-multiplayer reset fails upstream and
passes with the correction. Repeated multiplayer writes, GPIO-to-normal and
entering/remaining in GPIO also pass with the candidate. This establishes a
local register-mode defect, not that it caused the observed live error.

Separate prepare/build scripts produce the same pinned newer core plus the
bounded diagnostic patch and `cable-rcnt-reset.patch` under the private
`cable-reset-candidate` cache tree. Live qualification is pending. Compare a fresh
battle followed by trade/room exit, then repeated room use, keeping the same
network conditions and normal-save startup. Do not combine speculative queue or
handshake changes with this first candidate.

The reset candidate built successfully, passed isolated-save 120-frame startup on both local devices and is now selected by Tools → GBA Cable Test. Test-save hashes remained unchanged during startup checks. Live comparison remains pending.


### RCNT candidate failed live battle-room exit

Both launches were verified to use `gpsp_bfrcnt` without Auto Resume, with the
second local device hosting. The user observed different remote-player positions
between screens in the room, completed a battle, then received a connection
error when leaving the battle room, before the planned trade/repeat visits.
The affected device was not specified in this report. This is a failure of the
candidate, not evidence that the correction caused a regression: the baseline
already fails intermittently and no failure-rate comparison exists.

Both emulator processes remained alive, both TCP endpoints were ESTABLISHED
with 36 queued transmit bytes at inspection, and Wi-Fi power saving remained off.
Host logs show re-handshakes with 14–22 queued peer packets, followed by connected
state reported with offset 5. Client logs show repeated handshake/connected
transitions. Similar transitions were present in the prior successful run;
these are investigative leads, not a demonstrated cause. Different character
positions may reflect delayed remote updates and do not prove whole-emulator
lockstep desynchronization (this transport exchanges link packets between
independent games). Private live logs are archived under
`.cache/gpsp-link-tests/20261021-cable-reset-error`. No forced SRAM flush or game
termination was performed during capture. Keep the register correction isolated
as a validated unit defect; do not promote it as a live communication fix.


## Client handshake acknowledgment candidate

Inspection of the rapid client re-handshake/connected loops found that local
handshake detection leaves the host's previously received CONNECTED status
intact. The next client update can therefore synthesize MASTER_HANDSHAKE from
that old status without observing a new host handshake. The targeted candidate
adds an internal wait flag after locally detecting a restart, cleared only by
observing host HANDSHAKE or a full serial reset. Receive-side observation handles
HANDSHAKE and CONNECTED arriving in the same batch. It does not alter MPK1 packet
format, queue policy or timing constants.

`check-cable-handshake.py` compiles the actual upstream client update/receive
functions against register and transport stubs. Upstream fails by reconnecting
against stale host status; the candidate passes delayed-host, real-handshake,
subsequent-data and batched-receive cases. This is not a complete link protocol
simulation or proof that the observed live failure is solved. Late messages from
an older handshake cannot be fully distinguished without protocol epochs.

The isolated build uses the pinned newer source plus bounded diagnostics and
`cable-handshake-wait.patch`, deliberately excluding the RCNT correction for a
single-change comparison against the prior diagnostic baseline. Prepare/build
scripts are in `tools/gpsp-link`; the private build tree is
`.cache/gpsp-link-tests/cable-handshake-candidate`. Both prior candidate games
were confirmed exited cleanly, and their final session files were archived.

The handshake-wait core built and passed isolated-save startup/exit checks on both devices. Tools → GBA Cable Test now selects it; live testing remains pending. Prior cores remain separate and released cores are untouched.


### First handshake-wait battle/trade passed

Both launches were verified to use `gpsp_bfhand` without Auto Resume. With the
second local device hosting, the user completed battle then trade and explicitly
confirmed leaving both rooms without an error, remaining in-game. Both processes
and the TCP connection were alive at capture; transmit queues were empty.
Private live logs are under `.cache/gpsp-link-tests/20261021-handshake-pass`.
Client reconnect observations now have intervening host HANDSHAKE/CONNECTED
announcements rather than the rapid stale-status reconnect loop seen earlier.
Host re-handshake queue observations are typically 1–2 packets in this capture,
versus 14–22 in the failed RCNT-candidate capture; these are observations under
different live timing, not controlled performance measurements. Peer timeouts
still occur after serial activity stops. No broad reliability claim is warranted
from this first successful candidate session; repeated visits and reversed host
roles remain to be qualified. Final save/exit has not yet been requested.


The user completed another trade and room exit in the same uninterrupted game
session, saved normally and exited both games to Tools. Both emulator processes
were gone; both logs recorded successful SRAM writes and launcher exit 0. Native
save inspection succeeded, with Kyogre/Rayquaza on the first local device and
Torchic/Luvdisc on the second. Final before/after saves and logs are archived in
the same private handshake-pass directory. This qualifies one observed sequence
of battle, trade, repeated trade, all room exits and clean save/exit with the
handshake candidate, with the second device hosting. Fresh ordinary-save reload
and reversed host roles are the next focused checks. Released cores are unchanged.


### Reversed-host handshake candidate sequence passed

Both games reloaded using the handshake candidate without Auto Resume; native
save inspection still found the prior session's saved parties. With the first
local device hosting, the user reported the requested battle, trade, second trade
and all room exits ran without errors, then saved and exited to Tools. Both
processes were gone, logs recorded successful SRAM writes and launcher exit 0,
and native final-save inspection passed. Final parties remained Kyogre/Rayquaza
and Torchic/Luvdisc, consistent with two swaps returning the party selection.
Private before/after saves and final logs are archived under
`.cache/gpsp-link-tests/20261021-handshake-reverse-pass`.

The handshake candidate has now passed one battle/two-trade sequence with each
host role. This is meaningful live evidence, not exhaustive compatibility or
interruption qualification. Wi-Fi power saving remains temporarily disabled;
normal network policy, uninstrumented timing, additional games/save families and
reconnect/interruption recovery still need evaluation before stable integration.


## Wi-Fi power-saving comparison staged

With both games exited, the temporary `iw ... power_save off` probe override
was removed by setting power saving on for both WLAN interfaces and verifying
the reported state. No persistent NetworkManager/boot configuration was changed.
Keep the same instrumented handshake candidate for this round to isolate the
network-policy variable; the uninstrumented build comparison comes afterward.
Live power-save-on qualification is pending.


### Staggered Colosseum exit reproduces failure

With the first local device hosting and Wi-Fi power saving verified ON on both,
the user deliberately progressed its exit dialogue first while leaving the
second device's dialogue untouched. Once the first showed Please Wait, the user
advanced the second device's dialogue, which then displayed a communication
error. Prior successful exits had been confirmed at roughly the same time on
both devices. This establishes a useful user-observed staggered-exit reproduction,
not an isolated cause: Wi-Fi policy also differs from earlier passing sessions.

Both handshake-candidate processes remained alive and the RetroArch TCP link
remained ESTABLISHED. Host send queue was empty; client had 36 queued transmit
bytes at capture. Logs show the candidate's host-confirmed handshake transitions
rather than the earlier rapid stale-status reconnect loop. Peer timeout events
also occur in this run, but the bounded logs have emulated tick timestamps only;
they cannot precisely align a particular timeout with the user's dialogue delay.
No forced SRAM flush, game exit or restart was requested during capture. Private
logs are under `.cache/gpsp-link-tests/20261021-staggered-exit-error`.

The handshake change is therefore insufficient for robust room exit. Next
qualification must explicitly separate near-simultaneous and deliberately
staggered confirmations under the same Wi-Fi policy, in both directions. The
four-second serial-peer expiry and synthesized client IRQ/data behavior during
one-sided dialogue are investigation targets; do not just lengthen timeouts
without determining whether real disconnect handling would regress. Synchronous
button pressing must not become an undocumented requirement or a claimed fix.


## Close-command trace staged after staggered failure

Both games exited normally after the staggered-exit failure; final before/after
saves and logs were archived with that session. No running emulator remained.

Inspection of pret/pokeemerald `src/link.c` shows `LinkCB_WaitCloseLink` waits
until every player's READY_CLOSE_LINK flag is received. `LinkVSync` can flag
slave lag after more than ten VBlanks without a serial interrupt, independently
of gpSP's four-second peer expiry. Therefore extending that expiry is not yet
justified. Sources downloaded read-only into the private cache from:
https://github.com/pret/pokeemerald/blob/master/src/link.c
https://github.com/pret/pokeemerald/blob/master/include/link.h

The new diagnostic retains the handshake-wait candidate and adds bounded
`BF-CLOSE` observations for READY_CLOSE_LINK (0x5FFF) and READY_EXIT_STANDBY
(0x2FFE): packet send, receive and first-word delivery into each game's serial
registers. Logs include local monotonic timestamps, emulated ticks and queue/state
metadata, with a total limit of 128 close-command observations per process.
No Pokemon payload is printed. No timeout, command or data-queue behavior is
changed. Local monotonic times are not synchronized across devices; use event
ordering and per-device elapsed times, not raw cross-device timestamp subtraction.

Prepare/build scripts and `cable-close-trace.patch` are under `tools/gpsp-link`.
The comparison remains experimental. Next live test: complete a battle, advance
the host exit dialogue first, leave the client untouched until the host waits,
then advance the client. Preserve both games if the error recurs.

The close trace passed isolated-save startup/exit on both devices and is now selected by Tools → GBA Cable Test. Both Wi-Fi interfaces still report power saving ON. Live reproduction remains pending.


### Close-command trace reproduced staggered-exit failure

The user reproduced the communication error with both close-trace cores still
running. Logs are archived privately under
`.cache/gpsp-link-tests/20261021-close-trace-error`.
Host sent READY_CLOSE_LINK (5FFF); client received it and delivered its first word
into the serial registers about 2 ms after receive. No client 5FFF send or local
delivery was recorded, and no host receive of client 5FFF was recorded. Earlier
READY_EXIT_STANDBY (2FFE) messages were sent/received/delivered in both directions.
The close trace was far below its 128-entry cap. These observations narrow the
failure beyond simple loss of the host's close announcement, but first-word
serial delivery does not prove a complete command was accepted by the game.

Host 5FFF send: local monotonic 14867.008; client receive 14987.618, first-word
delivery 14987.620. The clocks have different uptime offsets and must not be
subtracted across devices. Connection-time ping was 190–203 ms with Wi-Fi power
saving on. No protocol fix or timeout extension follows from this capture alone.
Next inspect the client's full command/checksum consumption and game-side error
reason before altering close acknowledgment logic. Never synthesize a player's
exit confirmation merely to make the close handshake complete.


### Remaining diagnostic distinction

Further game-source inspection: `SerialCB` processes complete command words via
`DoRecv` and sets game-side checksum/receive-queue errors independently of the
network/core queues. `LinkMain1` reports hardware, checksum, game-queue, master-lag,
invalid-ID and slave-lag error bits. `LinkVSync`'s ten-frame check is only one
possible error route; no captured evidence yet identifies which bit fired.
Therefore READY_CLOSE_LINK first-word delivery alone cannot establish acceptance.

A next diagnostic should record completion of all eight delivered words and the
following checksum transfer, plus whether serial IRQs remain enabled/serviced
while the other player waits. It should distinguish emulator injection from game
consumption. Prefer bounded snapshots around close commands, not all payload
traffic, and do not invent or automatically echo player close acknowledgments.
No further protocol patch was applied during this inspection.


## Full-word close diagnostic

The previous close-trace games have exited; final session files were archived.
The next isolated build adds `cable-close-words.patch` to the same diagnostic
baseline. After a 5FFF close-command observation it records up to 24 serial
transfer register snapshots, capped at 256 total per process. Each snapshot
contains the four receive registers, local send register, synthesized checksum,
frame offset, SIOCNT/RCNT and IE/IF/IME interrupt control registers. It logs
emulator register injection, not proof of game IRQ service or command acceptance.
It does not change timeout, IRQ scheduling, packet format or acknowledgment logic.
These observations should cover delivery of all eight command words and the
next checksum transfer; a trace reset or interruption can itself truncate that
window and must be reported rather than interpreted as a completed command.
Prepare/build scripts and launcher are kept separate for reproducibility/rollback.

The full-word diagnostic built and passed isolated-save startup/exit on both devices with unchanged test-save hashes. It is now selected by Tools → GBA Cable Test; live reproduction is pending.


### First full-word staggered exit passed

The user reported a successful staggered Colosseum exit, remaining in-game.
Both full-word diagnostic processes were alive. Private logs are under
`.cache/gpsp-link-tests/20261021-words-staggered-pass`.
Unlike the previous failing capture, this trace contains client 5FFF local
serial delivery and send, followed by host receive/delivery. Client snapshots
show all eight close-command words and a subsequent checksum transfer of 5FFF;
host snapshots similarly show the returned command and its checksum. Client
SIOCNT/IE later disable serial interrupts as the user exits, while the emulator
continues synthetic transfer snapshots; that is an observation, not yet a
proposed behavior change. It does not itself prove an error, since this run passed.

Host sends 5FFF at local monotonic 15524.956 and receives client 5FFF at 15525.534,
about 0.578 seconds later. This does not measure the user's entire exit dialogue
delay; device clocks differ and only same-device deltas are meaningful. Instrumentation
may perturb timing. No protocol correction was added since the earlier failing
close trace, so this is a successful control, not evidence of a new fix. Repeat
with a deliberate measured wait under unchanged conditions before drawing a
conclusion about delay sensitivity. Final save/exit is still pending.


The user could not reproduce the error on the requested additional staggered-exit
attempt (instructions requested a ten-second wait; the exact observed wait was
not independently measured). Updated logs were archived. This adds a successful
observation but cannot establish a fix: this build adds logging only relative to
the previously failing handshake candidate. Logging overhead remains a confound.
Repeated manual trials with the same instrumentation have diminishing diagnostic
value. Preserve this session, then compare against the existing less-instrumented
handshake candidate under the same Wi-Fi power-saving and deliberate-delay policy.


### Full-word session closed and comparison reviewed

Both games exited normally, launcher exit 0, and final before/after save files
and logs were archived. Across the full-word session, the trace contains three
bidirectional close exchanges (including one before the first captured report).
The failing simpler trace has only host 5FFF send and client receive/first-word
delivery, with no client close reply. Thus the first visible divergence remains
the absent client reply; the available failing trace lacks the full-word/IRQ
snapshots required to determine why. Successful full-word logs cannot establish
what the game consumed in the earlier failed run.

The last two host-first successful exchanges have host send-to-client-reply
receive intervals of 0.578 and 0.394 seconds. A requested ten-second user pause
therefore cannot be assumed to equal a ten-second interval between those protocol
messages: the dialogue wait and protocol close announcement are different events.
Do not characterize these as controlled ten-second close-handshake delay tests.
No additional fix is justified by this comparison alone, and no stable integration
or publication was performed. Keep the full-word diagnostic available for a future
failure capture; avoid another speculative timeout/acknowledgment patch.


## Upstream version audit (2026-10-21)

GitHub API verification: gpSP master remains
5819380c2ffb0900219d700a382ee68c464ebb99 (2026-09-19), the same upstream revision
used by all newer experimental cores. The release gpSP recipe remains pinned to
b0d5d27ae51c23f514974ddffa5760f1e1d05d9b. No newer master core is available to
solve this simply by updating gpSP.

RetroArch recipe is bdba046fa6766380bc2457532f38e589df769aaf, dated 2026-06-06,
marked v1.22.2 plus fixes. GitHub latest official release is still v1.22.2;
current development master is 9e1c1e8ac897625ed75920019f4f62a173a4eedf.
Recent Netplay-specific development includes packet-playing-client restrictions,
deferred host setup, and input bounds. Those are relevant reasons to consider
an isolated newer RetroArch comparison, not evidence of a known room-exit fix.
The broad compare API result is truncated (250 commits/300 files), so it must
not be treated as an exhaustive Netplay audit. Recent path-specific commit
history was fetched separately and cached privately.

gpSP serial_proto.c explicitly approximates supported game protocols rather
than emulating all cable transactions faithfully. Resolving a remaining error
may require larger upstream protocol work rather than a small ButterflyOS fix.
The live evidence does not exclude RetroArch transport/timing issues merely
because TCP remains established. A controlled newer RetroArch32 comparison,
keeping the same core and network settings, is preferable to further speculative
core patches. No new RetroArch binary was built or deployed during this audit.


## Current-development RetroArch32 comparison (staged)

Pinned frontend revision: `9e1c1e8ac897625ed75920019f4f62a173a4eedf`.
Downloaded archive SHA-256:
`0d9a7c3acf988fe06f0fc7b27f72ad65adaa8b7e6681fbda48e4f59ac1883f1b`.
ARM32 executable SHA-256:
`556a1d7b09ea280ba06d34ad53347864d6f4288702894cbe104842591bb5da89`.
The upstream version string still reads 1.22.2; commit/archive/binary hashes identify
this development build. Prepare/build and runner-generation scripts are in
`tools/gpsp-link`. The first configure attempt failed because newer configure uses
PKG_CONF_PATH rather than PKG_CONFIG; setting it explicitly resolved dependency
detection. The build retained ARM NEON, Wayland/GLES, PipeWire, udev and networking.

Applied existing OGA preferred-mode, DRM resolution, disabled-search, Wayland
checkerboard and controller-fallback patches. Adapted the localhost-only NetCMD
patch to the current bind-address API. UI sizing/quit labeling, brightness, default
paths and achievement hook/sound patches did not apply cleanly and were not carried
into this scoped comparison. The existing explicit config supplies runtime paths;
these omitted patches are recorded differences, not claimed equivalent behavior.
Patch dry-run results are private in `retroarch-current/patch-results.json`.
No Netplay source logic was patched by ButterflyOS in this frontend comparison.

Installed separately at
`/storage/.config/butterflyos/gpsp-link-tests/retroarch-current/retroarch32`.
A copied live runemu script changes only frontend executable and main config path.
The test launcher snapshots the save, copies the main configuration to a unique
session, disables config saving there, and keeps Auto Resume off. The normal
system frontend is untouched. The same gpSP full-word diagnostic core is retained:
`8264211c676d0be7e606f3c39973ca0072b961ea208717d8d364280e4d56e4eb`.
Wi-Fi power saving remains ON on both. Both devices passed 120-frame headless
startup/exit with temporary save paths, Netpacket registration and unchanged test
save hashes; runtime version and executable hashes were checked on both.
Tools → GBA Cable Test now uses `GBA-Cable-RetroArch-Current.sh`.
Live graphics/audio/controller/Netplay and staggered-exit qualification is pending.
Rollback: reinstall `GBA-Cable-Close-Words.sh` as the module to use the original
system frontend with the same core. No image rebuild or publication occurred.


### Newer frontend repeated staggered exits passed in first live session

Actual running executable paths were verified on both devices to point to the
separate development RetroArch32, with unchanged full-word core and Wi-Fi power
saving ON. The first local device hosted. The user tried multiple staggered exits
and could not reproduce the communication error. Live logs contain three host
5FFF sends, three client 5FFF receives/deliveries/sends and three host
receives/deliveries of the replies. Both game processes remained running. Public
UPnP mapping failed on the host, but direct LAN gameplay succeeded.

Private live logs are under
`.cache/gpsp-link-tests/20261021-retroarch-current-pass`. This is encouraging
frontend-comparison evidence, not a proven specific RetroArch fix: the previous
frontend also had intermittent successful sequences and this is not a randomized
or repeated matched comparison. Do not call the prior in-game communication error
an OS/emulator process crash. Final save/exit, reversed host roles and removing
diagnostic logging remain to be qualified for the newer frontend.


### Newer frontend reversed-host live pass

Both running executable paths were verified as the development frontend before
starting the second local device as host. With Wi-Fi power saving still ON, the
user reported the requested battle/trade and staggered exits also worked. Logs
contain two complete bidirectional 5FFF close exchanges, with host receive and
serial delivery of both client replies. Both game processes remained running at
capture. Private live logs are under
`.cache/gpsp-link-tests/20261021-retroarch-reverse-pass`.
The public UPnP warning remains unrelated to successful direct LAN connection.
Final save/exit is pending for this reversed-host session. The development
frontend has now passed observed staggered exits with either host role, but
this alone does not identify a particular upstream fix or prove reliability.
Next compare the same handshake candidate without bounded diagnostic logging,
keeping this frontend and Wi-Fi policy unchanged.


## Uninstrumented handshake comparison staged

Both development frontend games exited normally after the reversed-host pass;
final session files were archived. Separate `prepare-cable-handshake-plain.py`
and `build-cable-handshake-plain.sh` export the same pinned gpSP revision with
only the RK3566 platform adaptation and handshake-wait patch. No RCNT correction
or BF diagnostics are included. Reversing the word/close/general diagnostic
patches from the previous core's serial_proto.c yields a byte-identical protocol
source to this plain candidate. The extracted-client handshake regression check
still passes. Keep the development frontend and Wi-Fi power saving ON to isolate
removal of core diagnostic logging. Live qualification is pending.

The plain core built, passed isolated-save startup/exit with the development frontend on both devices and is selected by Tools → GBA Cable Test. Wi-Fi power saving is still ON. Interactive qualification remains pending.


### Newer frontend without core diagnostic logging failed

Both actual executable paths were verified as the pinned development frontend,
with the plain handshake candidate and Wi-Fi power saving ON. The second local
device hosted. The user reproduced the communication error after diagnostic
logging was removed. The report did not specify the exact failing room/action
or affected device, so do not infer them. Both emulator processes stayed alive.
TCP remained ESTABLISHED; both endpoints had 36 bytes in their receive queues
at the instant inspected. That snapshot does not establish packet loss, a
transport deadlock or a game-error cause. Private normal logs are under
`.cache/gpsp-link-tests/20261021-retroarch-plain-error`.

This rejects promoting the newer frontend plus handshake candidate as a reliable
fix. Successful instrumented sequences cannot be used to claim an upstream
RetroArch fix. Logging may alter timing, but the experiment does not prove a
specific timing cause. Keep all work on the experimental branch; no stable
RetroArch/core update or full image build is justified by these results alone.
Preserve final session saves/logs after normal exit. Next work should prioritize
a bounded failing full-command trace or an upstream reproduction/report over
additional speculative timeout/ack patches and repeated blind manual trials.


## Refined exit reproduction: independent initiation versus propagated exit

The user clarified that one player initiating an exit and letting it propagate
to the other has not produced the observed error. Failures have occurred when
both players independently try to leave. This refines the reproduction; do not
rewrite earlier cases as proven simultaneous-exit races or assume all staggered
confirmations represent the same script path. Earlier instructions mixed exit
initiation, propagated dialogue acknowledgment and protocol close confirmation.

Read-only inspection of pret/pokeemerald `src/overworld.c` supports distinct
paths: HandleLinkPlayerKeyInput runs RunTerminateLinkScript for an idle local
player when any remote player is EXITING_ROOM, while QueueExitLinkRoomKey sends
a local EXIT_ROOM key and waits for all players to reach EXITING_ROOM before
running EventScript_DoLinkRoomExit. Tile-event/script processing precedes that
idle-player propagation check. These observations make competing exit-script
progression and ordering worth examining, but do not establish the actual failed
state or justify injecting/suppressing a player's commands in the emulator.
Source: https://github.com/pret/pokeemerald/blob/master/src/overworld.c

Next tests must record which player independently starts leaving and whether the
other merely responds to a propagated exit prompt. Treat single-initiator exit as
a user-observed working workflow, not a qualified universal workaround or fix.
The plain-core/development-frontend failure remains unresolved and experimental.
No further core/frontend change was applied on this clarification.


## Bslap launcher implemented for live testing

The live multiplayer feature is now named Bslap. Blink retains its current
save-transfer name and behavior. The supplied Documents/bslap.png is installed
as the Tools icon and kept in the experimental source tree. The Bslap UI uses
ToolUI, shared with Blink/Bdex, including scaling and A/B controls.

The launcher offers Host/Join, ROM selection, local UDP discovery, exact-ROM and
backend matching, an exit-issue note before launch, save validation and unique
before/after session archives. First scope is uncompressed English Emerald
identified by BPEE header, with an adjacent .srm save. In-game saves update that
ordinary save; backup and restore behavior are documented in the user guide.
Host/join flags are passed as argv to the separate frontend via an isolated copy
of the system runner. No shell or keyboard IP entry is needed. The current test
core/frontend hashes and Wi-Fi policy are unchanged.

A startup check exposed that core_options_path alone still allowed RetroArch to
write the normal per-core gpSP.opt. The launcher now forces global_core_options
with an explicit session-local options file, disables game options and automatic
overrides, and uses a temporary main/append config. Rechecks confirmed saves and
options were redirected into the sandbox and cable mode was mul_poke. Original
test-save hashes stayed unchanged. This correction is for launcher isolation,
not an asserted communication-error fix.

Three host-side tests cover ROM-header filtering/deduplicated mounts, discovery
message validation, and isolated frontend argv/config routing. Both devices
passed sandboxed frontend-wrapper startup/exit with Netpacket registration.
A discovery-only LAN test found the first local device from the second.
The actual UI was launched on both devices; a screenshot from the first confirms
the shared layout. Controller-driven complete host/join gameplay through Bslap
and Tools-icon visibility after list refresh remain user qualification tasks.
The package/menu entries are staged on the experimental branch; image backend
packaging and a full image build have not been performed. No publication occurred.


### Bslap lobby correction

The first user-driven launcher attempt exposed two launcher defects: Host
launched immediately rather than waiting for the joining player, and Join
crashed in the shared renderer because the discovery progress footer was empty
(`RuntimeError: Text has zero width`). The host game subsequently exited normally;
the client app crash was a UI rendering failure, not an in-game link error.

Bslap now uses discovery protocol v2 and a separate TCP readiness lobby on 55437.
Host stays in the UI while the client selects a matching ROM and sends readiness.
Only then does Host expose Start. Host Start is acknowledged by the client before
launching the host game. The client remains in its lobby until the host's actual
RetroArch listener is ready, then launches automatically. B cancels lobby setup;
fragmented, oversized, malformed, cancelled and disconnected lobby messages are
handled without launching an unready session. Discovery only advertises the lobby,
not an already running game. The progress footer is now nonempty.

Five regression checks pass, including blocking Start before peer readiness and
fragmented-message handling. A real LAN lobby check between both devices confirmed
ready/start/ack/go ordering without either emulator running. It also confirmed the
host was discoverable while no game was running. No emulator/core/Wi-Fi changes
were made. Corrected apps were reinstalled; full UI-driven gameplay remains to
be retested. User documentation reflects Ready -> both ready -> host Start.


### Corrected Bslap lobby passed user-driven live testing

The user confirmed the corrected launcher flow worked well. This is the first
user-driven Bslap UI/lobby launch pass, distinct from prior direct Cable Test
launches. The exact activities, save/exit and reload results were not specified
in this report, so do not extend that confirmation to those milestones.
Next scope is the full Gen 3 game-pair matrix: Ruby, Sapphire, Emerald, FireRed
and LeafGreen, including same-title and cross-title pairs, both host roles,
ordinary save persistence, native trade-eligibility restrictions and the known
room-exit workflow. The present launcher still offers only English Emerald.
Gen 1/2 would require their own suitable emulator/link backend and independent
qualification; ease of implementation has not been established by this GBA work.

Follow-up log inspection confirmed both Bslap-launched games exited with runner status 0 and successful SRAM writes to their selected ordinary-save paths. Host/client connection used Bslap nicknames. In-game save progression and reload persistence remain user qualification items.


### English Ruby/Sapphire cross-game launcher staging — 2026-10-22

The user confirmed the second local device successfully hosted Bslap. Discovery
version 3 now advertises the game header and permits English AXVE/AXPE/BPEE
pairs instead of requiring identical ROM hashes. Backend identifiers must still
match. RetroArch netpacket mode accepts differing content CRCs with a warning.
Six launcher regression tests pass, including all nine RSE compatibility pairs.
Ruby/Sapphire versus Emerald live results remain pending; this does not qualify
other languages, FireRed/LeafGreen or remove the known room-exit error.


### Ruby ↔ Emerald live result — 2026-10-22

The user confirmed trading and battling worked between Ruby and Emerald through
Bslap. Host direction, ordinary-save reload and room-exit details were not
separately reported for this pass. Sapphire ↔ Emerald remains pending. The
known intermittent room-exit communication error remains documented.


### Sapphire ↔ Emerald live result — 2026-10-22

The user clarified Sapphire ↔ Emerald had also already passed trading and
battling, with no issues reported. No additional repeat was requested. Host
direction and ordinary-save reload were not separately reported. This successful
session does not remove the previously observed intermittent room-exit issue.


### Ruby/Sapphire pass and FR/LG staging — 2026-10-22

The user confirmed Ruby ↔ Sapphire works well, following the trade/battle test
workflow. Bslap now accepts English FireRed (BPRE) and LeafGreen (BPGE),
including all 25 header combinations across the five games. Six launcher tests
pass. Separate FR/LG ROM/save copies were staged for live qualification; these
pairs are not yet qualified. No backend, kernel or stable-launch changes.


### FR/LG cross-game live results — 2026-10-22

The user confirmed FireRed ↔ LeafGreen worked, then explicitly confirmed both
LeafGreen ↔ Emerald and FireRed ↔ Emerald worked as well, following the requested
trade/battle/save workflow. Individual host directions and ordinary-save reloads
were not separately reported. FireRed/LeafGreen versus Ruby/Sapphire remain
untested. These passes do not remove the known intermittent room-exit issue.


### Gen 2 then Gen 1 scope — 2026-10-22

The user chose to stop the current Gen 3 matrix and proceed to Gen 2 ↔ Gen 2,
then Gen 1 ↔ Gen 1. Integrated the earlier SameBoy host/player1 and guest/player2
strategy into Bslap, separately from gpSP. Discovery v4 rejects mixed generations.
Installed native SameBoy c8564b65 and RetroArch f1ff8a00 match on both devices.
Ten targeted tests and native standalone/paired startup checks pass. Paired
Netplay assigned players 1/2 and wrote each subsystem SRAM correctly. Headless
audio-driver/UPnP messages are not proof of live audio failure; real audio,
controls, trading/battling and persistence remain to be tested. No new kernel,
frontend/core build, full image, commit or stable release was made.


### Gen 2 user pass; Gen 1 staging — 2026-10-22

The user reported all Gen 2 functionality worked great and requested Gen 1
testing next. Exact Gen 2 pairings were not itemized. Reordered Host generations
to Gen 1, Gen 2, Gen 3 and replaced the Bslap icon with the updated Documents PNG.
Staged separate Red/Blue/Yellow ROM/save copies for live Gen 1 testing.


### Gen 1 user pass and warning scope — 2026-10-22

The user confirmed all Gen 1 tests passed. They explicitly clarified that Gen 1
and Gen 2 room exits did not crash or show the known Gen 3 communication error.
Scoped the launcher warning, menu label, post-session text and user guide to
Gen 3. These successful tests do not claim every possible pair is qualified.

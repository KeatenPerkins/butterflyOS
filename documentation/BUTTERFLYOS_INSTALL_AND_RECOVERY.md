# ButterflyOS installation and recovery

ButterflyOS aims to require no disassembly during normal installation or
removal. Opening the Miyoo Flip and pressing its MASKROM button is a last-resort
recovery method, not an onboarding step.

## Intended installation experience

1. Write the device-specific ButterflyOS image to a microSD card.
2. Leave the original Miyoo system installed internally and start it with the
   ButterflyOS card in the right-hand slot.
3. Open **Apps**, then open **ButterflyOS Setup**.
4. Read the no-write warning screen. Open **ButterflyOS Setup** a second time
   within five minutes to confirm.
5. The bootstrap temporarily erases only the internal 2 MiB preloader and
   restarts. The prepared card should then boot ButterflyOS.
6. In ButterflyOS, open **Tools → ButterflyOS Boot Check**. This is read-only.
7. If every safety gate passes, open
   **Tools → Enable ButterflyOS SD Boot** and confirm the write.

The finished behavior is:

| State at power-on | Result |
|---|---|
| Compatible ButterflyOS card inserted | ButterflyOS boots from microSD |
| Card removed | Internal stock Miyoo system boots |

The install action verifies the board and SoC, NAND geometry, bad-block state,
battery or charger state, image structure, and DRAM blob before writing. It
backs up the current preloader, verifies the write, retries, and attempts to
roll back a failed verification.

The bootstrap is deliberately not automatic. It requires two separately
launched confirmations from stock. The second step inside ButterflyOS is also
manual.

## Returning to stock boot

While ButterflyOS still boots, open
**Tools → Restore Stock Miyoo Boot** and confirm. The utility validates the
known stock image, backs up the current contents, writes the stock preloader,
and verifies its readback. ButterflyOS SD multiboot is then disabled and the
internal Miyoo system boots normally.

This restores stock *behavior*. It is not yet guaranteed to restore the exact
preloader bytes originally supplied on every unit. Stock does not expose the
preloader through its Linux MTD layout, and the software bootstrap cannot
currently save an exact per-unit copy before erasing it. The bundled stock
image is byte-identical to the tested ButterflyOS unit and the maintained Flip
reference image, but more than one stock SPL build is known to exist.

Exact byte-for-byte reversal on an untested unit therefore remains a release
qualification item. It requires either a safe stock-side preloader reader or a
validated catalog of every supported stock preloader revision.

## Recovery if the bootstrap is interrupted

After the temporary erase and before multiboot is installed, the device is in
SD-only boot mode:

- With a valid ButterflyOS card, it boots from that card.
- Without a card, it normally exposes the RK3566 USB MASKROM recovery mode.
- If USB MASKROM is not detected automatically, opening the shell and using
  the internal MASKROM button remains the final recovery path.

The immutable SoC bootrom and MASKROM implementation are not stored in the SPI
NAND region modified by ButterflyOS.

## Public-release gates

Do not describe onboarding as generally supported until all of these have been
tested on physical hardware:

- The stock launcher discovers `App/ButterflyOS Setup` on the ButterflyOS boot
  partition.
- Both confirmation launches behave correctly and a single launch writes
  nothing.
- The card boots after the temporary erase.
- The read-only ButterflyOS Boot Check passes.
- Multiboot installation verifies successfully.
- Stock boots with the card removed.
- ButterflyOS boots with the card inserted.
- Restore Stock Miyoo Boot verifies successfully.
- Stock and SurwishOS boot after restoration.
- A second software-only ButterflyOS installation succeeds.

Until this round trip passes, the workflow is experimental.

## Third-party release note

The low-level preloader utilities are pinned to revision
`4f32de5bae58cad07c54b5fb8450fc00385f4260` of the maintained Miyoo Flip
reference project and checksum-verified during the build. That repository does
not currently declare a top-level software license. Permission or a clearly
compatible license must be established before distributing those utility files
and bundled preloader images in a public ButterflyOS release.

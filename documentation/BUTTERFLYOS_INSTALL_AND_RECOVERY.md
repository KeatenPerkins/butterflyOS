# ButterflyOS installation and recovery

ButterflyOS aims to require no disassembly during normal installation or
removal. Opening the Miyoo Flip and pressing its MASKROM button is a last-resort
recovery method, not an onboarding step.

## Intended installation experience

1. Write the device-specific ButterflyOS image to a microSD card.
2. Leave the original Miyoo system installed internally. Put the ButterflyOS
   card in the **left-hand slot**, then start the stock Miyoo system.
3. Open **Apps**, then open **ButterflyOS Setup**.
4. Read the no-write warning screen. Open **ButterflyOS Setup** a second time
   within five minutes to confirm.
5. The bootstrap temporarily erases only the internal 2 MiB preloader and then
   powers the device off. Do not remove power or the card while it is working.
6. After shutdown, move the ButterflyOS card from the left-hand slot to the
   **right-hand slot**, then power on. The prepared card boots ButterflyOS.
7. In ButterflyOS, open **Tools → ButterflyOS Boot Check**. This is read-only.
8. If every safety gate passes, open
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
launched confirmations from stock within five minutes. The first launch writes
nothing internally. The persistent step inside ButterflyOS is also manual.

## Slot summary

| Part of setup | Slot |
|---|---|
| Run **ButterflyOS Setup** from stock Apps | Left-hand slot |
| Boot and use ButterflyOS | Right-hand slot |
| Boot the stock Miyoo system after setup | Remove the ButterflyOS card |

## Returning to stock boot

For an exact device-specific restoration, place these two files on the
ButterflyOS storage partition before opening the restore tool:

```text
butterflyos-recovery/preloader-original.img
butterflyos-recovery/preloader-original.img.sha256
```

The image must be exactly 2 MiB. The checksum file begins with its 64-character
SHA-256 value, in the same format produced by `sha256sum`. If both files are
present and valid, ButterflyOS labels the restore source **EXACT DEVICE
BACKUP**, displays its verified hash, and passes that explicit image to the
low-level restoration utility.

If either file is present but the pair is incomplete, the size is wrong, or
the checksum differs, restoration stops without writing. It does not silently
fall back to the generic stock image while a broken personal backup exists.

While ButterflyOS still boots, open
**Tools → Restore Stock Miyoo Boot** and confirm. The utility validates the
selected image, backs up the current contents, writes the stock preloader, and
verifies its readback. ButterflyOS SD multiboot is then disabled and the
internal Miyoo system boots normally.

Without a verified device-specific backup, this restores stock *behavior*. It
is not guaranteed to restore the exact preloader bytes originally supplied on
every unit. Stock does not expose the preloader through its Linux MTD layout,
and the software bootstrap cannot currently save an exact per-unit copy before
erasing it. The bundled stock image is byte-identical to the tested
ButterflyOS unit and the maintained Flip reference image, but more than one
stock SPL build is known to exist.

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

- The stock launcher discovers `App/ButterflyOS_Setup` on the ButterflyOS boot
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

The complete round trip passed on the primary ButterflyOS Flip V2 test unit on
2026-09-01. A clean-image test and a second untouched Flip V2 remain Alpha 1
release-qualification gates.

## Third-party release note

The low-level preloader utilities are pinned to revision
`4f32de5bae58cad07c54b5fb8450fc00385f4260` of the maintained Miyoo Flip
reference project and checksum-verified during the build. That repository does
not currently declare a top-level software license. Permission or a clearly
compatible license must be established before distributing those utility files
and bundled preloader images in a public ButterflyOS release.

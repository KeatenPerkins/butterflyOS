# ButterflyOS installation and recovery

ButterflyOS aims to require no disassembly during normal installation or
removal. Opening the Miyoo Flip and pressing its MASKROM button is a last-resort
recovery method, not an onboarding step.

## Intended installation experience

1. Write the device-specific ButterflyOS image to a microSD card.
2. Leave the original Miyoo system installed internally. Put the ButterflyOS
   card in the **left-hand slot**, then start the stock Miyoo system.
3. Open **Apps**, then open **ButterflyOS Setup**.
4. The first launch performs a read-only compatibility check, derives a patch
   from this unit's own preloader, and saves an exact verified backup to
   `butterflyos-recovery/` on the card. It does not write internal storage.
5. Open **ButterflyOS Setup** a second time within five minutes. The installer
   repeats every check, patches only the SPL device tree, verifies the write by
   reading it back, and powers off. Do not remove power or the card while it is
   working.
6. After shutdown, move the ButterflyOS card from the left-hand slot to the
   **right-hand slot**, then power on. The prepared card boots ButterflyOS.
7. In ButterflyOS, open **Tools → ButterflyOS Boot Check**. This is read-only.

The finished behavior is:

| State at power-on | Result |
|---|---|
| Compatible ButterflyOS card inserted | ButterflyOS boots from microSD |
| Card removed | Internal stock Miyoo system boots |

The installer verifies the board and SoC, exact MTD identity and size, NAND
geometry, battery or charger state, both IDB copies, and all four embedded
SHA-256 values. It verifies that DDR firmware and SPL executable code remain
unchanged, saves the device's exact original preloader and checksum before any
erase, verifies readback, retries, and restores the original after failure.
Unknown, damaged, and already-modified structures are refused.
The first public Alpha additionally uses an explicit SHA-256 allowlist of stock
preloader revisions qualified on real hardware. A structurally valid but new
revision is reported for review and is not written automatically.

The bootstrap is deliberately not automatic. It requires two separately
launched confirmations from stock within five minutes. The first launch writes
nothing internally. The second launch performs the persistent change.

## Slot summary

| Part of setup | Slot |
|---|---|
| Run **ButterflyOS Setup** from stock Apps | Left-hand slot |
| Boot and use ButterflyOS | Right-hand slot |
| Boot the stock Miyoo system after setup | Remove the ButterflyOS card |

## Returning to stock boot

The stock-side installer creates these files on the ButterflyOS FAT boot
partition before changing internal storage. ButterflyOS mounts that partition
at `/flash`:

```text
butterflyos-recovery/preloader-original.img
butterflyos-recovery/preloader-original.img.sha256
```

The image must be exactly 2 MiB. The checksum file begins with its 64-character
SHA-256 value, in the same format produced by `sha256sum`. If both files are
present and valid, ButterflyOS labels the restore source **EXACT DEVICE
BACKUP**, displays its verified hash, and passes that explicit image to the
low-level restoration utility.

If either file is missing, the size is wrong, or the checksum differs,
restoration stops without writing. There is no generic fallback image.

While ButterflyOS still boots, open
**Tools → Restore Stock Miyoo Boot** and confirm. The utility validates the
selected image, proves that the installed preloader is the patch derived from
that original, writes the exact original, and verifies its readback. ButterflyOS
SD multiboot is then disabled and the
internal Miyoo system boots normally.

Restore is therefore byte-for-byte identical to what that specific device held
before installation. Without the verified device-specific pair, ButterflyOS
refuses to restore.

## Recovery if installation is interrupted

The installer keeps both original and derived images in RAM and retries a
failed write three times. If patched readback cannot be verified, it writes the
exact original back and verifies that readback. An interruption during the
brief erase/write window may still require RK3566 USB MASKROM recovery. If USB
MASKROM is not detected automatically, opening the shell and using the internal
MASKROM button remains the final recovery path.

The immutable SoC bootrom and MASKROM implementation are not stored in the SPI
NAND region modified by ButterflyOS.

## Public-release gates

Do not describe onboarding as generally supported until all of these have been
tested on physical hardware:

- The stock launcher discovers `App/ButterflyOS_Setup` on the ButterflyOS boot
  partition.
- The first launch passes its full dry run, saves an exact verified backup, and
  writes nothing internally.
- The second launch derives, writes, and verifies the device-local patch.
- The read-only ButterflyOS Boot Check passes.
- Stock boots with the card removed.
- ButterflyOS boots with the card inserted.
- Restore Stock Miyoo Boot verifies successfully.
- Stock and SurwishOS boot after restoration.
- A second software-only ButterflyOS installation succeeds.

The complete round trip passed on the primary ButterflyOS Flip V2 test unit on
2026-09-01. On 2026-09-10, a second previously untouched Flip V2 completed the
device-local install, ButterflyOS/card boot, stock/no-card boot, exact restore,
and stock/card boot sequence. Independent readback after restoration matched
that unit's archived factory backup byte-for-byte. See
[`ALPHA2_ONBOARDING_QUALIFICATION.md`](ALPHA2_ONBOARDING_QUALIFICATION.md).

Qualification exposed two missing runtime interfaces. Both operations refused
before writing, and permanent fixes were package-tested. A clean rebuilt image
containing those fixes must complete the same sequence without live
intervention before public release.

## Third-party release note

The device-tree patch algorithm is derived from apommel's BaseOS implementation
and retains its MIT copyright and permission notice. ButterflyOS ships the
patch description and safety scripts, but no stock or prepatched Miyoo
preloader image. The Alpha 1 image remains an internal artifact; this workflow
has passed physical Alpha 2 qualification, with one clean-image regression
remaining before public release.

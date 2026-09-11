# ButterflyOS Alpha 1 Quick Start

ButterflyOS v0.1.0 Alpha 1 supports the **Miyoo Flip V2 only**. It is test
software, not a stable release. Back up saves and other important files before
testing it.

## What you need

- A Miyoo Flip V2
- A reliable microSD card and card reader
- The Miyoo Flip V2 ButterflyOS `.img.gz` release file
- Its matching `.sha256` file
- A computer capable of writing disk images

ButterflyOS does not contain games or proprietary console BIOS files.

## Verify the download

Keep the image and checksum file in the same directory. On Linux, run:

```sh
sha256sum -c ButterflyOS-v0.1.0-alpha.1-Miyoo-Flip-V2.img.gz.sha256
```

The result must say `OK`. If it does not, delete the download and obtain it
again. Windows users can compare the value reported by `Get-FileHash` in
PowerShell with the value inside the `.sha256` file.

## Write the card

Use a graphical image writer such as Raspberry Pi Imager, balenaEtcher, or
another tool that accepts compressed `.img.gz` images.

1. Insert the microSD card.
2. Select the ButterflyOS `.img.gz` image.
3. Select the microSD card as the destination.
4. Check the destination capacity and model carefully. Writing the image
   erases the selected drive completely.
5. Write and verify the image, then eject the card safely.

The card initially contains a 2 GiB `BUTTERFLYOS` partition and a small
`STORAGE` partition. The storage partition expands automatically on first boot.

## First-time device setup

ButterflyOS uses a reversible SD-boot setup while leaving the stock Miyoo OS
installed internally.

1. Put the prepared card in the **left-hand slot**.
2. Boot the stock Miyoo OS and open **Apps → ButterflyOS Setup**.
3. Read the warning. Launch **ButterflyOS Setup** a second time within five
   minutes to confirm.
4. Do not remove power or the card while the setup runs.
5. After the device powers off, move the card to the **right-hand slot**.
6. Boot ButterflyOS and allow first-boot initialization to finish.
7. Open **Tools → ButterflyOS Boot Check**.

If the stock OS does not detect the card or does not initially show
**ButterflyOS Setup**, shut down normally, wait until fully powered off, reseat
the card in the left slot, and cold boot again. This was occasionally necessary
on both qualification devices. Never reseat the card while powered on. If it
remains intermittent, stop and test or replace the card before running Setup.

Afterward, the device boots ButterflyOS when its card is inserted and boots the
stock Miyoo OS when the card is removed. Read the complete
[installation and recovery guide](BUTTERFLYOS_INSTALL_AND_RECOVERY.md) before
starting, especially the current exact-restoration and licensing caveats.

## Add games and BIOS files

Copy legally obtained games into `STORAGE/roms/<system>`. Common aliases such
as `roms/FC` and `roms/SFC` are recognized alongside `roms/nes` and
`roms/snes`.

Place user-supplied BIOS files in `STORAGE/roms/bios`. Open **Tools → System
Manager** to see which systems are ready and which BIOS files are missing.

If files are copied while ButterflyOS is running, open the game settings and
choose **Update Gamelists**. Systems appear only when recognized games are
present.

## Network transfer

Open **Settings → Network Settings**, set the SSH password, and then enable
Wi-Fi, SSH, or Web File Transfer as needed. The web page explains that the
login name is `root`; use the password set on the device.

## Safe shutdown

Use **Start → Quit → Shut Down System** and wait for the device to power off
before removing the card. See [Controls and hotkeys](HOTKEYS.md) for in-game
exit and save-state shortcuts.

# ButterflyOS Alpha 2 Quick Start

ButterflyOS v0.1.0 Alpha 2 supports the **Miyoo Flip V2 only**. It is test
software, not a stable release. Back up saves and other important files before
testing it.

Read [current build status](CURRENT_BUILD_STATUS.md) before testing. Download
the image and matching checksum from the
[Alpha 2 release](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v0.1.0-alpha.2).

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
sha256sum -c ButterflyOS-v0.1.0-alpha.2-Miyoo-Flip-V2.img.gz.sha256
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

`BUTTERFLYOS` is the FAT boot partition; `STORAGE` is ext4 user storage. Windows
and macOS do not normally mount ext4 without additional tools. Do not accept a
computer's prompt to format an unfamiliar partition. Use Web File Transfer
after booting the Flip, or mount the data partition on a Linux computer.

## First-time device setup

ButterflyOS uses a reversible SD-boot setup while leaving the stock Miyoo OS
installed internally.

This is for a stock Flip V2 that has not already had ButterflyOS SD boot enabled.
Keep the device adequately charged; use the front charging port for external
power. The rear USB port is not the charging port.

1. Put the prepared card in the **left-hand slot**.
2. Boot the stock Miyoo OS and open **Apps → ButterflyOS Setup**.
3. Read the warning. Launch **ButterflyOS Setup** a second time within five
   minutes to confirm.
4. Do not remove power or the card while the setup runs.
5. After the device powers off, move the card to the **right-hand slot**.
6. Boot ButterflyOS and allow first-boot initialization to finish.
7. Open **Tools → ButterflyOS Boot Check**. Tools is on the home screen and
   also in the Start main menu.
8. Open **Tools → Export Recovery Backup**, then download the
   resulting archive and `.sha256` file to another computer. Do this before
   ever reflashing the ButterflyOS card.

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

Copy legally obtained games into `STORAGE/roms/<system>` (shown on-device as
`/storage/roms/<system>`). Common aliases such
as `roms/FC` and `roms/SFC` are recognized alongside `roms/nes` and
`roms/snes`.

Place user-supplied BIOS files in `STORAGE/roms/bios`. Open **Tools → System
Manager** to see which systems are ready and which BIOS files are missing.

If files are copied while ButterflyOS is running, open the game settings and
choose **Update Gamelists**. Systems appear only when recognized games are
present.

Use a matching basename for ordinary game saves: for example,
`Pokemon - Gold Version (USA, Europe).gbc` and
`Pokemon - Gold Version (USA, Europe).srm`. Emulator save states are separate
from in-game/battery saves. See [Butterfly Link](BUTTERFLY_LINK.md) before
transferring Pokémon.

## Optional second game card

ButterflyOS can combine games stored on the OS card with games on a second SD
card. With ButterflyOS on the right, the game card goes in the left slot.
Power off before inserting or removing it. Open **Tools → Format 2nd SD
Card**. Despite its name, the tool can inspect a compatible card, keep existing
files and create the expected folders, or
format it as exFAT after two destructive-action confirmations.

Add games beneath `roms/<system>` on that card and choose **Update Gamelists**.
Games from both cards appear together. If both cards contain a file with the
same system and filename, the OS-card copy takes precedence. The second card is
also available as **Second Game Card** in Web File Transfer.

exFAT is the recommended second-card format. The mounting code also supports
FAT32, NTFS, ext4, and btrfs, but these alternatives have not all received the
same hardware testing. The OS card remains the image's FAT+ext4 layout.

## Add music and videos

On the OS card, use `STORAGE/media/Music` and `STORAGE/media/Videos`.
The Music/Videos links in Web File Transfer select these folders for you.
On a second card, use `roms/music` and `roms/videos`; library refresh includes
those files under Media. Older OS-card `roms/music` and `roms/videos` files
are imported into the `media` folders during refresh.

Media remains available even when empty. Refresh after uploads if new files
are not yet listed. H.264/AAC at moderate 480p/720p bitrates is the recommended
video target; a `.mov` or `.mkv` extension alone does not guarantee smooth playback.

## Network transfer

Open **Settings → Network Settings**, enable Wi-Fi, choose **Select Wi-Fi Network**,
and enter the network password. Submit with the keyboard's on-screen Enter
button; B is a back/cancel control, not a substitute for submitting the value.

Choose **Set SSH Password** and submit the new device password before enabling
SSH or Web File Transfer. In Web File Transfer, open the displayed web address
on another device on the same network. The login name is `root` and the
password is the one you set; do not assume a development test password.

For SSH, use `ssh root@<device-IP>` with the IP shown in Network Settings.
The default hostname is `butterflyos`; two Flips can share that default, so use
their displayed IPs when connecting to more than one. Local hostname resolution
depends on your network. Bluetooth controllers are managed in
**Settings → Controller & Bluetooth Settings**.

## Safe shutdown

Use **Select → Shut Down System**, or **Start → Quit → Shut Down System**,
and wait for the device to power off
before removing the card. See [Controls and hotkeys](HOTKEYS.md) for in-game
exit and save-state shortcuts.

Closing the lid blanks the LCD but does not suspend the game or system.
Use shutdown for long breaks; the CPU and networking continue drawing power
with the lid closed.

## Updating a test installation

There is no qualified ButterflyOS online updater yet. A whole-card reflash
erases games, saves, settings, and the recovery backup on that card. Export the
device recovery archive and separately back up all user files first. The SD-boot
change stays in the device's internal preloader; do not reinstall it merely
because you rewrote the OS card. Restore the correct device's recovery folder
to the new boot partition as described in the installation guide.

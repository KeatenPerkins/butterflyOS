# How to transfer games to ButterflyOS

<img src="assets/games-controller.png" alt="ButterflyOS Games controller icon" width="128">

You can use a web browser, an SD-card reader, SMB file sharing, or SSH-based
tools. Web File Transfer is the easiest starting point for most users. Only
copy games and BIOS files you are entitled to use; ButterflyOS does not supply them.

## Before copying

Finish the OS card's first boot first: ButterflyOS expands its storage partition
and creates the folders. Do not interrupt that process.

Put games in the folder for their system, not directly in the top-level ROMs
folder. These paths refer to the running device:

| Content | OS-card destination | Second-card destination |
| --- | --- | --- |
| Game Boy | `/storage/roms/gb/` | `roms/gb/` |
| Game Boy Color | `/storage/roms/gbc/` | `roms/gbc/` |
| Game Boy Advance | `/storage/roms/gba/` | `roms/gba/` |
| NES / Famicom | `/storage/roms/nes/` | `roms/nes/` |
| SNES / Super Famicom | `/storage/roms/snes/` | `roms/snes/` |
| PlayStation | `/storage/roms/psx/` | `roms/psx/` |
| BIOS files | `/storage/roms/bios/` | Use the OS-card BIOS folder |
| Music | `/storage/media/Music/` | `roms/music/` |
| Videos | `/storage/media/Videos/` | `roms/videos/` |

`FC` and `SFC` aliases are also recognized, but `nes` and `snes` are recommended
when creating new folders. Keep multi-file disc games together, including their
cue sheets and referenced tracks. Supported game formats depend on the emulator.
Use **Tools → System Manager** for system readiness and missing BIOS checks.

After transferring, choose **Update Gamelists** in the game settings to refresh
the library. Games on both cards appear together; when the system and filename
are identical, the OS-card copy takes precedence.

## Option 1: Web File Transfer

1. Open **Settings → Network Settings** and enable Wi-Fi.
2. Choose **Select Wi-Fi Network**, select your network, and enter its password.
   Submit using the keyboard's on-screen Enter button; B cancels/backtracks.
3. Choose **Set SSH Password**, enter a device password, and submit it with
   on-screen Enter. This is a separate password from your Wi-Fi password.
4. Enable **Web File Transfer**. Open its displayed web address on a computer
   or phone connected to the same local network.
5. When asked to log in, the account name is `root`; the password is the device
   password you just set. “Root” is the device's administrator account.
6. Choose **Games**, open the appropriate system folder, and upload your files.
   **Second Game Card** writes to the second card instead. **Music**, **Videos**,
   and **BIOS** select the corresponding OS-card folders.
7. Refresh the library after uploads finish.

You do not need to enable SSH just to use the web interface. Enable file-transfer
services only on a trusted network; do not forward their ports to the internet.

## Option 2: Remove the SD card and copy with a computer

1. After first boot has finished, use **Select → Shut Down System** and wait
   until the device has powered off. Closing the lid is not shutdown.
2. Remove the card and insert it into a computer's card reader.
3. Open its data partition and copy games into `roms/<system>`.
4. Safely eject the card, put it back in the powered-off Flip, and boot.
5. Refresh the library if your new files are not listed.

The OS card has two partitions: a small boot partition and an **ext4** data
partition named **STORAGE**. Copy user files to STORAGE, not the boot partition.
Linux normally reads ext4 directly. Windows and macOS do not normally read it
without additional software. If your computer offers to format the OS card,
cancel: formatting would destroy the installation.

For Windows/macOS, network transfers or an **exFAT second card** are simpler.
With the OS card in the right slot, the second card goes in the left slot.
**Tools → Format 2nd SD Card** can inspect/prepare a card or format it as exFAT;
formatting erases its contents and requires confirmation. See
[Quick Start](QUICK_START.md#optional-second-game-card). Always power off before
inserting or removing either card.

## Option 3: SMB network file sharing

Enable **Enable Samba** under **Other Network Services** in Network Settings.
Use the device IP shown there; `192.168.1.20` below is only an example.

- Windows: enter `\\192.168.1.20\games-roms` in File Explorer's address bar.
- macOS: Finder → Go → Connect to Server, then enter
  `smb://192.168.1.20/games-roms` and connect as Guest.
- Linux: open `smb://192.168.1.20/games-roms` in a file manager supporting SMB.

Open the system folder and copy games into it. For a mounted second card, use
the `games-external` share, then its `roms/<system>` folder.

The current Samba shares allow guest access; they do not use your SSH password
for authentication. Some Windows installations block guest SMB connections.
If that happens, use Web File Transfer or SFTP rather than weakening your
computer's security settings. Disable Samba when it is not needed.

## Option 4: SFTP or SCP over SSH

Set your device password as described above, then enable **Enable SSH** in
Network Settings. In an SFTP-capable file-transfer app, use:

- Protocol: **SFTP**, not FTP.
- Host: the device's displayed IP address.
- Port: **22**.
- Username: **root**.
- Password: your device password.

Browse to `/storage/roms/<system>` and upload. A mounted second card is available
under `/storage/games-external/roms/<system>`.

From a computer terminal, SCP can copy an individual file:

```sh
scp "/path/to/My Game.gba" root@192.168.1.20:/storage/roms/gba/
```

Replace the example source path and IP. On first connection, SSH asks you to
trust the device's host key. After a reflash the key can change; verify that you
are connecting to your own device before replacing the saved key.

## Option 5: rsync over SSH for large or repeated transfers

With SSH enabled and rsync installed on your computer, run:

```sh
rsync -rt --info=progress2 -e ssh "/path/to/SNES/" root@192.168.1.20:/storage/roms/snes/
```

The trailing slash on `SNES/` copies the folder's contents into `snes/` rather
than creating another nested folder. Rerun the same command after an interruption;
rsync skips unchanged files. Add `--dry-run` to preview the transfer first.

This command can replace changed files with the same names, but does not delete
destination-only files. Do not add `--delete` unless you deliberately want a
mirror that removes files from the device. Prefer copying only game files, not
an old library's `gamelist.xml`, artwork metadata, or save directories.

## Protect your saves

Back up existing saves before replacing or importing them. Do not overwrite a
save while its game or Butterfly Link is running. Save filenames generally
need to match their ROM's basename; save states and in-game saves are different
formats. See [Quick Start](QUICK_START.md#add-games-and-bios-files) and
[Butterfly Link](BUTTERFLY_LINK.md) for save-transfer guidance.

USB-C cables alone are not a documented PC file-transfer method for this release.
Use one of the methods above rather than assuming a port exposes SD-card storage.

# Audio fix for games stuck near 47 FPS

ButterflyOS v1.0.0 inherited a PipeWire audio-buffer setting that can hold
GB, GBA, and NES games near 47 FPS. Changing the audio cycle size restores
normal speed. All three systems were confirmed working by device testing.

## Install the hotfix

1. Download `ButterflyOS-v1.0.0-Audio-Fix.zip` from the
   [v1.0.0 release](https://github.com/KeatenPerkins/butterflyOS/releases/tag/v1.0.0).
2. Unzip it on your computer.
3. Copy `ButterflyOS Audio Fix.sh` into the hidden `.config/modules/` folder on your
   main OS card's **STORAGE** partition. You can also copy it over the network
   to `/storage/.config/modules/`. After copying over the network, run
   `chmod +x "/storage/.config/modules/ButterflyOS Audio Fix.sh"` over SSH
   so the Tools menu can launch it.
4. Enable **Start → User Interface Settings → Advanced Mode**. The v1.0.0
   Tools menu hides newly added scripts in normal mode.
5. Refresh the game list if needed, open **Tools**, and launch
   **ButterflyOS Audio Fix**. You can turn Advanced Mode off afterward.
6. Return to your games and confirm normal speed. If the tool requests a
   restart, save and exit your games, then restart the whole device.

The download contains no games or BIOS files and does not reflash the card.
It installs a small configuration override that survives reboot. Running it
again is safe. Devices `.17` and `.20` already have this fix installed.

The v1.0.0 image and built-in updater package retain their original contents;
this is a separate hotfix. Future OS builds include the corrected default.

## Technical details and recovery

The hotfix sets PipeWire's default, minimum, and maximum audio quantum to 512
samples. At 48 kHz this is a 10.7 ms cycle, below a 60 Hz video frame, compared
with the inherited 1024-sample minimum (21.3 ms). It leaves CPU/GPU clocks
unchanged. Other audio applications share this setting; PortMaster and
Bluetooth audio should be included in further testing.

Installed configuration:

    /storage/.config/pipewire/pipewire.conf.d/99-butterflyos-game-audio.conf

To undo this hotfix, remove that file and restart the device. If an older
file at that exact path was replaced, its first backup is saved alongside
it as `99-butterflyos-game-audio.conf.before-audio-fix`; restore that file
before restarting.

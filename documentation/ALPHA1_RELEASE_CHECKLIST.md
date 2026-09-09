# ButterflyOS Alpha 1 release checklist

This checklist qualifies a freshly built Miyoo Flip V2 image. Do not substitute
a manually patched development card for the clean-image test.

## Build and image contents

- [ ] Build completes from a clean checkout at the recorded commit.
- [ ] The compressed image has a published SHA-256 checksum.
- [ ] FAT partition contains `SYSTEM`, `SYSTEM.md5`, and
      `App/ButterflyOS_Setup/`.
- [ ] The setup directory contains valid manifests, polished normal/selected
      icons, both instruction screens, and both shell utilities.
- [ ] `SYSTEM.md5` matches the SYSTEM file in the final image.
- [ ] Both image filesystems pass read-only filesystem checks.

## Untouched-device onboarding

- [ ] Stock Apps discovers **ButterflyOS Setup** from the left-hand slot.
- [ ] First launch shows the safety screen and returns after about 20 seconds.
- [ ] First launch writes no internal storage.
- [ ] Second launch requires a separate launch within five minutes.
- [ ] All 16 temporary preloader erase blocks report success.
- [ ] Device powers off and tells the user to move the card to the right slot.
- [ ] ButterflyOS boots from the right-hand slot.
- [ ] Read-only **ButterflyOS Boot Check** completes and presents a result.
- [ ] **Enable ButterflyOS SD Boot** verifies its full read-back.

## Reversible behavior

- [ ] Card in right-hand slot boots ButterflyOS.
- [ ] No card boots the internal stock Miyoo OS.
- [ ] Charger-while-off behavior remains functional after multiboot install.
- [ ] **Restore Stock Miyoo Boot** verifies its full read-back.
- [ ] After restoration, stock boots with no card and ignores the ButterflyOS
      card as expected.
- [ ] Software-only onboarding can be repeated after restoration.

## Basic Alpha smoke test

- [ ] First boot initialization completes without ROCKNIX-branded instructions.
- [ ] Second boot is materially faster than first boot.
- [ ] Home menu, clock, and battery indicator fit the 640×480 display.
- [ ] Main Menu identifies the system as ButterflyOS without ROCKNIX or
      Batocera product branding; upstream attribution remains available in the
      documentation and license information.
- [ ] Advanced Mode is off on a fresh install and normal Tools shows only Quick
      Start, Controls Guide, and System Manager.
- [ ] Enabling Advanced Mode immediately reveals recovery and technical Tools,
      Game Collection Settings, Updates & Downloads, and advanced controls in
      Game, User Interface, Sound, and System Settings.
- [ ] Disabling Advanced Mode hides those entries again without changing games,
      saves, or previously selected settings.
- [ ] Game lists use the reclaimed bottom area without the legacy button-help
      bar.
- [ ] NES and SNES systems appear only when their ROM folders contain games.
- [ ] One NES game and one SNES game launch, save state, load state, and exit.
- [ ] Favoriting and unfavoriting the current game from either EmulationStation
      or RetroArch produces one matching Favorites entry, never a duplicate.
- [ ] Shutdown completes cleanly and filesystems remain clean on the next boot.
- [x] Wi-Fi connects and reconnects after reboot.
- [ ] The device is reachable over SSH as `butterflyos` (or
      `butterflyos.local` where mDNS is supported) after networking starts.
- [ ] Web File Transfer explains where to set the device password, defines the
      `root` username in plain language, and authenticates with that password.
- [ ] Games, BIOS, Music, Videos, Saves, and All Storage open the same themed,
      authenticated upload browser; All Storage shows the storage root instead
      of reopening the landing page.
- [ ] With Bluetooth enabled and a controller connected, Controller Settings
      shows Set, Test, and Reset Controller Menu Button actions.
- [ ] Pressing the chosen button three times saves it; Test detects it; during
      a RetroArch game one press opens and closes the Quick Menu.
- [ ] Menu-button capture shows both `1/3` through `3/3` progress and a visible
      30-second countdown; Test shows a 15-second countdown and ends immediately
      when the saved button is detected.
- [ ] The external Menu-button shortcuts match the built-in M-button layout:
      Start twice exits, X toggles FPS, R2/L2 saves/loads, R1/L1 toggles fast
      forward/rewind, and Right/Left changes the state slot.
- [ ] The saved Menu-button mapping still works after reboot and Bluetooth
      reconnection.
- [ ] If the Player 1 Bluetooth controller is switched off during a RetroArch
      game, the built-in controls immediately take over Player 1 without
      restarting the game.
- [ ] Game-art scraper downloads and displays at least one image.
- [ ] Media lists both `Music` and `Videos` when supported files are present.
- [ ] H.264 video displays through MPV and exits cleanly with device controls.
- [ ] Test moderate-bitrate H.264/AAC at 480p and 720p and record whether MPV
      uses RK3566 hardware decoding; high-bitrate MOV and AV1 are known to skip.
- [ ] Live HDMI connection selects a sharp native output mode without rebooting.
- [ ] Disconnecting HDMI restores a sharp, correctly fitted 640×480 handheld
      interface without rebooting the device.
- [ ] After three idle seconds, HDMI menu CPU use falls without delaying the
      first controller input or making the clock/status indicators stale.
- [ ] Shutdown uses ButterflyOS branding and never displays Batocera artwork.

## Release record

Record the following with the test results:

- Git commit:
- Image filename:
- Image SHA-256:
- SD card make/model/capacity:
- Flip V2 firmware/hardware identifier:
- Tester and date:
- Known issues:

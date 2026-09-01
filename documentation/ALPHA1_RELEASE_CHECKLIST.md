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
- [ ] NES and SNES systems appear only when their ROM folders contain games.
- [ ] One NES game and one SNES game launch, save state, load state, and exit.
- [ ] Shutdown completes cleanly and filesystems remain clean on the next boot.
- [ ] Wi-Fi connects and reconnects after reboot.
- [ ] Game-art scraper downloads and displays at least one image.

## Release record

Record the following with the test results:

- Git commit:
- Image filename:
- Image SHA-256:
- SD card make/model/capacity:
- Flip V2 firmware/hardware identifier:
- Tester and date:
- Known issues:

# Alpha 2 onboarding qualification

This record covers the device-local Miyoo Flip V2 SD-boot installer introduced
for ButterflyOS Alpha 2. No stock or prepatched Miyoo preloader image is
included in the ButterflyOS package.

## Untouched-device round trip

Tested on a second, previously untouched Miyoo Flip V2 on 2026-09-10:

- The stock OS discovered `App/ButterflyOS_Setup` from the left SD slot.
- The first stage performed a dry run and saved an exact 2 MiB device backup
  without writing internal storage.
- Backup SHA-256:
  `dfdd7d20d6fd3beb18350dcf8fa58740b40b4baaf39467d45076f949053a2922`
- The second stage derived, wrote, and readback-verified the device-local patch.
- Derived and installed patch SHA-256:
  `ed10591f62ae0b8845ac9bd6cf80c896a2b172d32c7c4ef6564d305e8662c13d`
- ButterflyOS booted from the right SD slot.
- Removing the card booted the internal stock OS.
- Restore accepted only the exact device backup, completed on its first write
  attempt, and verified the restored readback.
- A separate read after restoration matched the archived factory backup
  byte-for-byte.
- With the ButterflyOS card still in the right slot after restoration, the
  device ignored it and booted the stock OS as expected.
- Both qualification devices occasionally required a powered-off card reseat
  and cold reboot before the stock OS detected the card or refreshed the Setup
  app. The end-user recovery procedure is documented in the installation guide.

The device's backup, checksum, and setup logs were also archived off-card under
`~/Documents/ButterflyOS-device-backups/flip-v2-dfdd7d20/` on the development
workstation. That private recovery material must never enter a release image or
source archive.

## Safe failures found during qualification

Two missing runtime interfaces were found in the candidate image:

1. `xxd` was absent, so Boot Check refused before modifying anything.
2. ROCKNIX provides BusyBox `flash_eraseall`, not `flash_erase`, so Restore
   refused before erasing or writing anything.

Both failures demonstrated the intended fail-closed behavior. The current
preloader was independently hashed after each refusal and remained unchanged.
The permanent fixes are commits `8e09035` and `075b3f0`; each package build
completed successfully.

## Clean-image regression

Clean regression candidate built successfully from source commit
`2464bffbf7b6b4096d201aa1a9850ee72737f4d9`:

- Image: `ROCKNIX-RK3566.aarch64-20260911-Miyoo_Flip_V2.img.gz`
- SHA-256:
  `e1331546bbebd9b00225059307f14383f3054f14806434dd41a2085b26af4483`
- All 675 main-system steps and all 255 compatibility-root steps completed
  with zero failures.
- The compressed image passed both `gzip -t` and its generated SHA-256
  manifest.
- The staged system contains the ARM64 `xxd` binary and the recovery script's
  `flash_eraseall` fallback. It contains no bundled stock or patched preloader
  image.

The freshly rebuilt image containing both fixes completed the following on
physical hardware with no SSH or live file changes:

- install from stock;
- run ButterflyOS Boot Check successfully;
- verify ButterflyOS/card and stock/no-card boot behavior;
- restore the exact device backup successfully;
- stock boot with the ButterflyOS card still inserted after restoration.

The Alpha 2 onboarding and exact-restore workflow is therefore qualified on the
tested Miyoo Flip V2 preloader revision. SurwishOS regression and one additional
software-only reinstall remain useful compatibility checks, but are not needed
to establish that the clean installer and exact restore work as designed.

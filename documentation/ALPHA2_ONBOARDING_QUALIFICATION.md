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

## Remaining clean-image regression

Before calling the Alpha 2 onboarding package release-qualified, repeat the
following using a freshly rebuilt image containing both fixes, with no SSH or
live file changes:

- install from stock;
- run ButterflyOS Boot Check successfully;
- verify ButterflyOS/card and stock/no-card boot behavior;
- restore the exact device backup successfully;
- verify stock boot with the card still inserted;
- optionally verify SurwishOS after restoration;
- perform one additional software-only ButterflyOS reinstall.

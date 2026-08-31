# Miyoo Flip V2 bring-up

ButterflyOS targets the Miyoo Flip V2 with the RK3566
`Miyoo_Flip_V2` image variant. This variant uses the shared RK3566 Specific
U-Boot and selects `device_trees/rk3566-miyoo-flip.dtb` in the generated
`extlinux/extlinux.conf`.

Build only this variant with:

```sh
make RK3566-Miyoo-Flip-V2
```

The standard `make RK3566` target continues to build all configured RK3566
variants. `IMAGE_SUBDEVICE=Miyoo_Flip_V2` is an opt-in build filter and rejects
unknown subdevice names before compilation begins.

Do not use the RK3566 `Specific` image unchanged for a Flip. That multi-device
image defaults to `rk3566-powkiddy-x55.dtb`; on the tested Flip V2 it produced
an incorrectly initialized display. Selecting the Miyoo Flip device tree gave
a correct boot logo, completed startup, working EmulationStation navigation,
and persistent GPIO controller configuration.

## Multiboot preloader

Booting from microSD required the maintained Miyoo Flip multiboot preloader in
the device's SPI NAND. Back up and verify the original 2 MiB preloader before
writing anything. Keep the backup off the test card.

Hashes from the first tested unit:

- Original preloader SHA-256:
  `dfdd7d20d6fd3beb18350dcf8fa58740b40b4baaf39467d45076f949053a2922`
- Installed multiboot preloader SHA-256:
  `ed10591f62ae0b8845ac9bd6cf80c896a2b172d32c7c4ef6564d305e8662c13d`
- Installed multiboot preloader MD5:
  `c2009762b1704d5ed2ebbfa4346e6ecc`

The installed image was read back immediately and compared byte-for-byte with
the candidate. The original preloader was independently read twice and both
copies matched. A full SPI NAND backup was not possible with the tested USB
loader because reads at and above 32 MiB returned synthetic `0xcc` data; do not
represent concatenated reads from that loader as a full recovery image.

The preloader modification is device-level and survives SD-card changes. With
no SD card inserted, the tested device continued to boot its internal stock OS.
Restoring the independently verified original 2 MiB preloader is the rollback
path.

The current guided, no-disassembly onboarding design and its exact-reversal
limitations are documented in
[`BUTTERFLYOS_INSTALL_AND_RECOVERY.md`](../BUTTERFLYOS_INSTALL_AND_RECOVERY.md).

## Image validation status

First complete device-specific build:

- Build date: 2026-08-28
- Image: `ROCKNIX-RK3566.aarch64-20260828-Miyoo_Flip_V2.img.gz`
- Image SHA-256:
  `069c51b1b7f07be089b17f13203a3d25e7b1d13cd1da314db046ef51d5b05768`
- The generated `extlinux/extlinux.conf` selects
  `FDT /device_trees/rk3566-miyoo-flip.dtb`.
- The generated image contains `Miyoo_Flip_V2_uboot.bin`.
- The compressed image passed `gzip -t` and its generated SHA-256 manifest.

Verified on physical Miyoo Flip V2 hardware:

- SD multiboot reaches the kernel and userspace
- Boot logo and LCD output are correctly rendered
- EmulationStation completes first-run configuration
- D-pad and face-button navigation work
- Normal software shutdown works
- First boot completes storage initialization successfully
- A subsequent cold boot is substantially faster and reaches the UI normally

Deferred until the test unit's replacement hinge and shell are installed:

- Full button, shoulder, trigger, and analog-stick mapping
- Lid-close and lid-open behavior
- Speaker, headphones, and volume controls
- Rumble
- Wi-Fi and Bluetooth
- Charging, battery percentage, and suspend/resume
- Emulator launch, hotkeys, performance, and thermal behavior

Avoid powered testing with a loose LCD or partially assembled spring-contact
components.

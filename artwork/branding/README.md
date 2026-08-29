# ButterflyOS branding assets

The approved ButterflyOS identity uses a geometric white butterfly above a
cyan-to-blue-to-violet-to-magenta wordmark on a pure black background.

## Production files

- `master/butterflyos-logo-master-black-1448x1086.png` is the approved,
  full-resolution raster master.
- `master/butterflyos-logo-master-transparent.png` is a deterministic
  background extraction of the approved master.
- `icons/butterflyos-emblem-transparent-1024.png` is the butterfly-only icon.
- `splash/butterflyos-boot-640x480.png` is the production Miyoo Flip V2 boot
  screen.
- `splash/butterflyos-shutdown-640x480.png` is the matching shutdown screen.

The initramfs uses a lossless RGB PPM copy of the boot splash at
`projects/ROCKNIX/packages/tools/rocknix-splash/files/`. It is installed only
for the `Miyoo_Flip_V2` image variant. Other ROCKNIX image variants retain the
upstream vector splash fallback.

## Palette

- Background: `#000000`
- Emblem: `#FFFFFF`
- Wordmark progression: cyan, electric blue, violet, magenta, warm pink

Do not regenerate production derivatives from a previously resized image.
Always begin with the full-resolution master.

# Building ButterflyOS from source

These instructions build the Miyoo Flip V2 image from a clean ButterflyOS
checkout. The build uses Podman and the pinned ROCKNIX build container.

The public source repository is available. The Alpha 2 image source revision is
`39bb3a803bd481b7a610cf2b19509b2c13d39891`; the `v0.1.0-alpha.2` tag also
includes final release documentation. Current image/test status is recorded in
[CURRENT_BUILD_STATUS.md](CURRENT_BUILD_STATUS.md).

## Host requirements

- A Linux x86-64 host
- Git, GNU Make, Podman, gzip, and SHA-256 utilities
- At least 100 GB of free workspace and a reliable internet connection

## Build

```sh
git clone https://github.com/KeatenPerkins/butterflyOS.git
cd butterflyOS
git checkout butterfly-save-trade-prototype
make docker-RK3566-Miyoo-Flip-V2-aarch64
```

This branch is the development snapshot, not an immutable release. For a
published image, use its recorded source tag instead. Do not build a public
release from an uncommitted working tree.

The aarch64 target builds the Flip production image. The target without the
`-aarch64` suffix additionally builds the compatibility ARM image. A clean
first build can need substantially more than 100 GB as sources and caches grow.

The compressed image is written under `target/` with a name beginning
`ROCKNIX-RK3566.aarch64-` and ending `-Miyoo_Flip_V2.img.gz`.

## Verify

```sh
sha256sum target/*Miyoo_Flip_V2.img.gz
git status --short
```

Compare the result with the checksum published beside the release. The exact
source commit, image name, and checksum are recorded in the release notes.

No game ROMs or proprietary console BIOS files are required to build the OS and
none belong in the source tree or release image.

# Building ButterflyOS from source

These instructions build the Miyoo Flip V2 image from a clean ButterflyOS
checkout. The build uses Podman and the ROCKNIX build container. The stable build used the container digest
recorded below; the Makefile default `latest` tag can change.

The first stable release is `v1.0.0`, with updater build identity `20261006`.
Its exact binary source is `efcc19513baa5ea2b756b619fe81196873e8aebc`;
the release tag also includes final build/audit documentation. See
[CURRENT_BUILD_STATUS.md](CURRENT_BUILD_STATUS.md) and the release notes for
artifact hashes and verification limits.

## Host requirements

- A Linux x86-64 host
- Git, GNU Make, Podman, gzip, and SHA-256 utilities
- At least 100 GB of free workspace and a reliable internet connection

## Build

```sh
git clone https://github.com/KeatenPerkins/butterflyOS.git
cd butterflyOS
git checkout efcc19513baa5ea2b756b619fe81196873e8aebc
CUSTOM_VERSION=20261006 make docker-RK3566-Miyoo-Flip-V2-aarch64 \
  DOCKER_IMAGE=ghcr.io/rocknix/rocknix-build@sha256:43dac3d6d7e59801b7797bf06b970c7c056d97185d19cb909d502ce8ded754ed
```

Use the recorded binary source revision to rebuild a published image. The
release tag may include later documentation changes. Do not build a public
release from an uncommitted working tree.

The published stable build reused the existing package/source cache. A full
clean-checkout rebuild and bit-for-bit reproducibility comparison were not
repeated. Custom version `20261006` is the reserved updater identity; do not
publish a second, different update with the same identity.

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

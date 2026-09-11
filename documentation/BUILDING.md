# Building ButterflyOS from source

These instructions build the Miyoo Flip V2 image from a clean ButterflyOS
checkout. The build uses Podman and the pinned ROCKNIX build container.

## Host requirements

- A Linux x86-64 host
- Git, GNU Make, Podman, gzip, and SHA-256 utilities
- At least 100 GB of free workspace and a reliable internet connection

## Build

```sh
git clone https://github.com/OWNER/butterflyos.git
cd butterflyos
git checkout v0.1.0-alpha.2
make docker-RK3566-Miyoo-Flip-V2
```

Replace `OWNER` with the final GitHub organization or username. Do not build a
public release from an uncommitted working tree.

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

# Bslap image backend

The `bslap-backend` package installs the exact live-tested ARM32 binaries at
`/usr/libexec/bslap/retroarch32` and
`/usr/lib/libretro/gpsp_bslap_libretro.so`, plus a matching core-info alias.
It leaves normal RetroArch/gpSP untouched. Stripping is disabled for this package
so the tested binary hashes remain unchanged. Native RetroArch, the dedicated Gambatte Netpacket core and SameBoy fallback
come from their dependency packages. Their completed package hashes are
recorded alongside the dedicated pair in `/usr/share/bslap/backend.json`.
The manifest-derived backend ID also prevents incompatible builds joining.

## Reconstructing the dedicated inputs

These binaries are build outputs, not committed binary blobs. Packaging requires
the verified local cache and fails clearly if it is missing or differs. It does
not silently download or accept replacement binaries. On a fresh checkout:

1. Use the existing RK3566 ARM32 toolchain/sysroot and ROCKNIX build container.
2. Obtain RetroArch source revision
   `9e1c1e8ac897625ed75920019f4f62a173a4eedf` as the GitHub source tarball at
   `.cache/gpsp-link-tests/retroarch-current/source.tar.gz`. Its expected SHA-256
   is `0d9a7c3acf988fe06f0fc7b27f72ad65adaa8b7e6681fbda48e4f59ac1883f1b`.
3. Run `python3 tools/gpsp-link/prepare-retroarch-current.py`, then
   `bash tools/gpsp-link/build-retroarch-current.sh` inside the build container.
   This applies the explicitly listed local frontend patches; it does not
   replace the stable RetroArch package.
4. Clone `https://github.com/libretro/gpsp` into `.cache/gpsp-link-upstream`,
   ensuring revision `5819380c2ffb0900219d700a382ee68c464ebb99` is available.
   Run `python3 tools/gpsp-link/prepare-cable-handshake-plain.py`, then
   `bash tools/gpsp-link/build-cable-handshake-plain.sh` in the same container.
   This applies the RK3566 platform patch and `cable-handshake-wait.patch` only.
5. Compare against `ARTIFACTS` in `stage-backend.py`. The tested outputs are
   frontend `556a1d7b09ea280ba06d34ad53347864d6f4288702894cbe104842591bb5da89`
   and gpSP `1ae51cbbc844f4c9574dbb2dc3853097d9badc53b32057ec84e1577615b91f55`.

Compiler versions, build paths and embedded frontend build timestamps can change
binary hashes. A rebuilt binary that differs requires intentional review, renewed
testing and a checksum update, rather than bypassing verification. The current
image uses the previously tested outputs. Source patches and revision details
remain in `tools/gpsp-link` and `documentation/EXPERIMENTAL_GPSP_LINK.md` as
historical development records; those diagnostic launchers are not installed.

RetroArch is GPL-3.0-or-later, gpSP and Gambatte GPL-2.0-only, and SameBoy MIT. Keep the pinned
upstream source revisions and local patches available with redistributed builds.

## Build and verification

The Flip onboarding package depends on `bslap-backend` for aarch64 images.
The normal full image target includes it. `stage-backend.py` reads completed
native dependency packages, stages the dedicated pair, and creates the manifest.
After assembly, verify every manifest hash against the actual image, the Bslap
scripts/module/icon, and normal emulator binaries. No user ROM/save fixtures are
installed. Run both targeted Bslap test scripts before building, then test the
flashed image on both devices, including a reboot and ordinary-save reload.


## Single-instance Gen 1/2 experiment (October 27)

See [the experiment plan](../../documentation/BSLAP_SINGLE_INSTANCE_PLAN.md).
This branch adds `gambatte-bslap-lr` to the backend dependencies and records its
completed package hash in the manifest. The ordinary Gambatte binary is not
replaced. The core source is GPL-2.0-only, pinned to
`McDjuady/gambatte-libretro@466e8b174982b3fdb5a026f60efc51972d1576b0`.
The package's `001-bounded-serial-peer.patch` includes the safety fixes and
optional shoulder palette cycling adapted to this older source revision.
No distribution ROMs or game data are included.

Build just this package before considering a full image. Run the Python Bslap
and Netpacket tests. Compile `tests/bslap-netpacket-serial-test.cpp` together with
the patched `libgambatte/libretro/netplay_serial.cpp`, using C++98,
`-DHAVE_NETWORK -DHAVE_STDINT_H` and the core's `libgambatte/src`,
`libgambatte/include`, `libgambatte/libretro` and
`libgambatte/libretro-common/include` include directories. This test runs without
ROMs and checks the real serial implementation, including its two-second timeout.
On a development device, the Python native-core smoke test accepts `--core`,
`--rom` and optional `--save`. Run it with no emulator open. It reads ROM/SRAM
and runs 120 headless frames; it does not save or overwrite files.

The native frontend and sameboy fallback remain installed and are hash-checked.
Use the `gb-backend` setting documented in the plan to compare both modes. Both
peers need matching manifests and selected Game Boy backends. Trade, battle,
repeated room entry/exit, save/reload, RTC, controls and audio are mandatory live
tests before considering this candidate for release.

Prepare the live-test bundle with:

```sh
python3 tools/bslap/prepare-netpacket-live.py \
  --build build.ROCKNIX-RK3566.aarch64 \
  --out .cache/bslap-single-instance-live-20261027
```

Copy its `live-test.tar` to each development device, extract into
`/storage/.config/butterflyos/bslap-single-instance-test`, then run the extracted
`activate.py` with no game open. It checks the installed native frontend and
fallback hashes, then temporarily binds the launcher and test manifest. Reopen
Bslap on both devices. Reboot restores the image's original launcher/backend;
the staged test files remain available for later activation. Activation is for
matching development images; it deliberately fails if installed dependencies
differ. No ROM or save files are included in the bundle.

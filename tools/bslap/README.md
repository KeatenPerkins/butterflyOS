# Bslap image backend

The `bslap-backend` package installs the exact live-tested ARM32 binaries at
`/usr/libexec/bslap/retroarch32` and
`/usr/lib/libretro/gpsp_bslap_libretro.so`, plus a matching core-info alias.
It leaves normal RetroArch/gpSP untouched. Stripping is disabled for this package
so the tested binary hashes remain unchanged. Native SameBoy and RetroArch come
from their existing dependency packages. Their completed package hashes are
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

RetroArch is GPL-3.0-or-later, gpSP GPL-2.0-only and SameBoy MIT. Keep the pinned
upstream source revisions and local patches available with redistributed builds.

## Build and verification

The Flip onboarding package depends on `bslap-backend` for aarch64 images.
The normal full image target includes it. `stage-backend.py` reads completed
native dependency packages, stages the dedicated pair, and creates the manifest.
After assembly, verify every manifest hash against the actual image, the Bslap
scripts/module/icon, and normal emulator binaries. No user ROM/save fixtures are
installed. Run both targeted Bslap test scripts before building, then test the
flashed image on both devices, including a reboot and ordinary-save reload.

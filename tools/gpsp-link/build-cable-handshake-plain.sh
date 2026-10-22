#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/../.." && pwd)
source_dir="$root/.cache/gpsp-link-tests/cable-handshake-plain/source"
toolchain="$root/build.ROCKNIX-RK3566.arm/toolchain/bin/armv8a-rocknix-linux-gnueabi"
test -f "$source_dir/Makefile"
make -C "$source_dir" platform=RK3566 clean
make -C "$source_dir" GIT_VERSION=\"5819380-bfplain1\" -j4 platform=RK3566 CC="$toolchain-gcc-15.2.0" CXX="$toolchain-g++-15.2.0" AR="$toolchain-ar"
file "$source_dir/gpsp_libretro.so"
sha256sum "$source_dir/gpsp_libretro.so"

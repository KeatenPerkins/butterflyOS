#!/bin/bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/../.." && pwd)
source_dir="$root/.cache/gpsp-link-tests/diagnostic-core/source"
toolchain="$root/build.ROCKNIX-RK3566.arm/toolchain/bin/armv8a-rocknix-linux-gnueabi"
test -f "$source_dir/rfu.c"
make -C "$source_dir" platform=RK3566 clean
make -C "$source_dir" GIT_VERSION=\"b0d5d27-bfrfu1\" -j4 platform=RK3566 CC="$toolchain-gcc-15.2.0" CXX="$toolchain-g++-15.2.0" AR="$toolchain-ar"
file "$source_dir/gpsp_libretro.so"
sha256sum "$source_dir/gpsp_libretro.so"

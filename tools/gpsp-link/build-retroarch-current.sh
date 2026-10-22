#!/bin/bash
# Build only the isolated ARM32 frontend; never install into the OS image.
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/../.." && pwd)
build_root="$root/.cache/gpsp-link-tests/retroarch-current"
toolchain="$root/build.ROCKNIX-RK3566.arm/toolchain"
sysroot="$toolchain/armv8a-rocknix-linux-gnueabi/sysroot"
export PATH="$toolchain/bin:$PATH"
export CC="$toolchain/bin/armv8a-rocknix-linux-gnueabi-gcc-15.2.0"
export CXX="$toolchain/bin/armv8a-rocknix-linux-gnueabi-g++-15.2.0"
export AR="$toolchain/bin/armv8a-rocknix-linux-gnueabi-ar"
export PKG_CONFIG="$toolchain/bin/pkg-config"
export PKG_CONF_PATH="$PKG_CONFIG"
export PKG_CONFIG_LIBDIR="$sysroot/usr/lib/pkgconfig:$sysroot/usr/share/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$sysroot"
export CFLAGS='-march=armv8-a+crc -mtune=cortex-a55 -mabi=aapcs-linux -Wno-psabi -Wa,-mno-warn-deprecated -mfloat-abi=hard -mfpu=neon-fp-armv8 -Wall -pipe -O2 -fomit-frame-pointer -DNDEBUG -DUDEV_TOUCH_SUPPORT'
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-L$sysroot/usr/lib32 -Wl,--as-needed -fuse-ld=bfd"
cd "$build_root/source"
./configure --host=armv8a-rocknix-linux-gnueabi --disable-qt --enable-alsa \
  --enable-udev --disable-opengl1 --disable-x11 --enable-zlib --enable-freetype \
  --disable-discord --disable-vg --disable-sdl --enable-sdl2 --enable-kms \
  --enable-ffmpeg --enable-neon --enable-wayland --enable-opengles \
  --enable-opengles3 --enable-opengles3_1 --disable-opengl --enable-vulkan \
  --enable-vulkan_display
make -j6 HAVE_UPDATE_ASSETS=0 HAVE_LIBRETRODB=1 HAVE_BLUETOOTH=0 \
  HAVE_NETWORKING=1 HAVE_ZARCH=1 HAVE_QT=0 HAVE_LANGEXTRA=1
file retroarch
sha256sum retroarch

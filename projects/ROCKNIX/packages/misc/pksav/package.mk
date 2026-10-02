# SPDX-License-Identifier: MIT
# Copyright (C) 2026 ButterflyOS contributors

PKG_NAME="pksav"
PKG_VERSION="master"
PKG_LICENSE="MIT"
PKG_SITE="https://github.com/savaughn/pksav"
PKG_URL="${PKG_SITE}/archive/refs/heads/master.tar.gz"
PKG_SHA256="6247df95be1fcafd8ae6f96ee74755751ac6342c4b0953e5f34e2dcc958952ed"
PKG_DEPENDS_TARGET="toolchain"
PKG_LONGDESC="Small, portable Pokémon save parsing and editing library"
PKG_TOOLCHAIN="cmake"

# ButterflyOS uses the library from a small native save-transfer helper. Keep
# the dependency self-contained and install the headers into the target
# sysroot so that helper can be cross-compiled by the onboarding package.
PKG_CMAKE_OPTS_TARGET="-DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
                       -DPKSAV_STATIC=ON \
                       -DPKSAV_ENABLE_TESTS=OFF \
                       -DPKSAV_ENABLE_DOCS=OFF"

# The upstream CMake install list omits this public Gen III header even though
# pokemon.h includes it. Keep the target sysroot complete for consumers.
post_makeinstall_target() {
  mkdir -p "${SYSROOT_PREFIX}/usr/include/pksav/gen3"
  cp -a "${PKG_BUILD}/include/pksav/gen3/ribbons.h" \
        "${SYSROOT_PREFIX}/usr/include/pksav/gen3/"
  mkdir -p "${INSTALL}/usr/share/licenses/pksav"
  cp -a "${PKG_BUILD}/LICENSE.txt" \
        "${INSTALL}/usr/share/licenses/pksav/"
}

# SPDX-License-Identifier: GPL-2.0-only
PKG_NAME="gambatte-bslap-lr"
PKG_VERSION="466e8b174982b3fdb5a026f60efc51972d1576b0"
PKG_LICENSE="GPL-2.0-only"
PKG_SITE="https://github.com/McDjuady/gambatte-libretro"
PKG_URL="${PKG_SITE}/archive/${PKG_VERSION}.tar.gz"
PKG_DEPENDS_TARGET="toolchain"
PKG_LONGDESC="Isolated single-instance Gambatte Netpacket backend for Bslap testing"
PKG_TOOLCHAIN="make"
make_target() {
  make -f Makefile.libretro
}

makeinstall_target() {
  mkdir -p ${INSTALL}/usr/lib/libretro
  cp gambatte_libretro.so ${INSTALL}/usr/lib/libretro/gambatte_bslap_libretro.so
}

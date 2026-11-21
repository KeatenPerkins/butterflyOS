# SPDX-License-Identifier: GPL-2.0-or-later
PKG_NAME="butterflyos-apps"
PKG_VERSION="0.1.1"
PKG_LICENSE="GPL-2.0-or-later"
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain Python3 openssl SDL2 SDL2_ttf dejavu"
PKG_TOOLCHAIN="manual"
PKG_LONGDESC="Signed optional Tools catalog and atomic app updates"
makeinstall_target() {
  install -Dm755 ${PKG_DIR}/sources/btools.py ${INSTALL}/usr/bin/btools
  mkdir -p ${INSTALL}/usr/share/butterflyos/apps ${INSTALL}/usr/config/modules
  install -m 0644 ${PKG_DIR}/config/* ${INSTALL}/usr/share/butterflyos/apps/
  mkdir -p ${INSTALL}/usr/lib/systemd/system
  install -m 0644 ${PKG_DIR}/system.d/* ${INSTALL}/usr/lib/systemd/system/
}
post_install() {
  enable_service butterflyos-bdex-web.service
}

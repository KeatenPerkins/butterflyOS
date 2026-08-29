# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 Keaten Perkins

PKG_NAME="es-theme-butterflyos"
PKG_VERSION="0.1.0"
PKG_LICENSE="GPL-2.0-only"
PKG_SITE="https://github.com/KeatenPerkins/butterflyOS"
PKG_URL=""
PKG_LONGDESC="ButterflyOS controller-first EmulationStation theme"
PKG_TOOLCHAIN="manual"

makeinstall_target() {
  mkdir -p ${INSTALL}/usr/share/themes/${PKG_NAME}
  cp ${PKG_DIR}/files/theme.xml ${INSTALL}/usr/share/themes/${PKG_NAME}/
  cp -R ${PKG_DIR}/files/assets ${INSTALL}/usr/share/themes/${PKG_NAME}/
  cp ${ROOT}/artwork/branding/master/butterflyos-logo-master-transparent.png \
    ${INSTALL}/usr/share/themes/${PKG_NAME}/assets/butterflyos-logo.png
}

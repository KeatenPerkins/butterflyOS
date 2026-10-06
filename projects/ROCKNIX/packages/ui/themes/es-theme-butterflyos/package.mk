# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 Keaten Perkins

PKG_NAME="es-theme-butterflyos"
PKG_VERSION="0.1.8"
PKG_LICENSE="GPL-2.0-only"
PKG_SITE="https://github.com/KeatenPerkins/butterflyOS"
PKG_URL=""
PKG_LONGDESC="ButterflyOS controller-first EmulationStation theme"
PKG_TOOLCHAIN="manual"

makeinstall_target() {
  mkdir -p ${INSTALL}/usr/share/themes/${PKG_NAME}
  cp ${PKG_DIR}/files/theme.xml ${INSTALL}/usr/share/themes/${PKG_NAME}/
  cp -R ${PKG_DIR}/files/assets ${INSTALL}/usr/share/themes/${PKG_NAME}/
  # System artwork is maintained as original ButterflyOS source art and
  # installed separately so it can be shared by future system views.
  cp -R ${ROOT}/artwork/system-icons/runtime \
    ${INSTALL}/usr/share/themes/${PKG_NAME}/assets/systems
  ln -sf genesis.png \
    ${INSTALL}/usr/share/themes/${PKG_NAME}/assets/systems/megadrive.png
  ln -sf pcenginecd.png \
    ${INSTALL}/usr/share/themes/${PKG_NAME}/assets/systems/pce-cd.png
  cp ${ROOT}/artwork/branding/master/butterflyos-logo-master-transparent.png \
    ${INSTALL}/usr/share/themes/${PKG_NAME}/assets/butterflyos-logo.png
}

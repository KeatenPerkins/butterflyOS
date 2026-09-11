# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

PKG_NAME="butterflyos-flip-onboarding"
PKG_VERSION="2.0.1"
PKG_LICENSE="GPL-2.0-or-later AND MIT"
PKG_SITE="https://github.com/apommel/baseos-my355"
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain dialog xxd"
PKG_LONGDESC="ButterflyOS guided Miyoo Flip multiboot setup and recovery tools"
PKG_TOOLCHAIN="manual"

makeinstall_target() {
  mkdir -p "${INSTALL}/usr/share/butterflyos/flip-preloader"
  cp -a "${PKG_DIR}/sources/preloader-installer/manage.sh" \
        "${PKG_DIR}/sources/preloader-installer/patch-preloader.sh" \
        "${PKG_DIR}/sources/preloader-installer/fdtpatch.awk" \
        "${PKG_DIR}/sources/preloader-installer/BASEOS_LICENSE" \
        "${INSTALL}/usr/share/butterflyos/flip-preloader/"

  mkdir -p "${INSTALL}/usr/config/modules/images"
  cp -a "${PKG_DIR}/sources/ButterflyOS Boot Check.sh" \
        "${PKG_DIR}/sources/Restore Stock Miyoo Boot.sh" \
        "${INSTALL}/usr/config/modules/"
  cp -a "${ROOT}/artwork/branding/icons/butterflyos-emblem-transparent-1024.png" \
        "${INSTALL}/usr/config/modules/images/butterflyos-boot.png"
  cp -a "${PKG_DIR}/sources/images/butterflyos-boot.svg" \
        "${INSTALL}/usr/config/modules/images/"

  mkdir -p "${INSTALL}/usr/share/butterflyos"
  cp -a "${PKG_DIR}/sources/flip-onboarding.sh" \
        "${PKG_DIR}/sources/flip-onboarding.gptk" \
        "${INSTALL}/usr/share/butterflyos/"

  mkdir -p "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup"
  cp -a "${PKG_DIR}/sources/stock-bootstrap/launch.sh" \
        "${PKG_DIR}/sources/stock-bootstrap/config.json" \
        "${PKG_DIR}/sources/stock-bootstrap/icon.png" \
        "${PKG_DIR}/sources/stock-bootstrap/icon_sel.png" \
        "${PKG_DIR}/sources/stock-bootstrap/first-run.png" \
        "${PKG_DIR}/sources/stock-bootstrap/second-run.png" \
        "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/"
  cp -a "${PKG_DIR}/sources/preloader-installer/install.sh" \
        "${PKG_DIR}/sources/preloader-installer/patch-preloader.sh" \
        "${PKG_DIR}/sources/preloader-installer/fdtpatch.awk" \
        "${PKG_DIR}/sources/preloader-installer/BASEOS_LICENSE" \
        "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/"

  chmod 0755 "${INSTALL}/usr/config/modules/ButterflyOS Boot Check.sh" \
             "${INSTALL}/usr/config/modules/Restore Stock Miyoo Boot.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-onboarding.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-preloader/manage.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-preloader/patch-preloader.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/launch.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/install.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/patch-preloader.sh"
}

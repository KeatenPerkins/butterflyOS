# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

PKG_NAME="butterflyos-flip-onboarding"
PKG_VERSION="2.0.4"
PKG_LICENSE="GPL-2.0-or-later AND MIT"
PKG_SITE="https://github.com/apommel/baseos-my355"
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain dialog xxd fbalpha2012-lr fbalpha2019-lr \
                    fbneo-lr genesis-plus-gx-lr genesis-plus-gx-wide-lr \
                    snes9x-lr snes9x2002-lr snes9x2005_plus-lr \
                    snes9x2010-lr supersnes9x-lr"
PKG_LONGDESC="ButterflyOS guided Miyoo Flip multiboot setup and recovery tools"
PKG_TOOLCHAIN="manual"

makeinstall_target() {
  # Keep the project policy, audit notice, common license texts, and the exact
  # non-commercial emulator licenses beside the binaries they govern.
  mkdir -p "${INSTALL}/usr/share/butterflyos/licenses/components"
  cp -a "${ROOT}/BUTTERFLYOS_LICENSE.md" \
        "${ROOT}/THIRD_PARTY_NOTICES.md" \
        "${INSTALL}/usr/share/butterflyos/licenses/"
  cp -a "${ROOT}"/licenses/*.txt \
        "${INSTALL}/usr/share/butterflyos/licenses/"
  cp -a "$(get_build_dir fbalpha2012-lr)/docs/license.txt" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/fbalpha2012.txt"
  cp -a "$(get_build_dir fbalpha2019-lr)/src/license.txt" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/fbalpha2019.txt"
  cp -a "$(get_build_dir fbneo-lr)/src/license.txt" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/fbneo.txt"
  cp -a "$(get_build_dir genesis-plus-gx-lr)/LICENSE.txt" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/genesis-plus-gx.txt"
  cp -a "$(get_build_dir genesis-plus-gx-wide-lr)/LICENSE.txt" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/genesis-plus-gx-wide.txt"
  cp -a "$(get_build_dir snes9x-lr)/LICENSE" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/snes9x.txt"
  cp -a "$(get_build_dir snes9x2002-lr)/src/copyright.h" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/snes9x2002.txt"
  cp -a "$(get_build_dir snes9x2005_plus-lr)/copyright" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/snes9x2005-plus.txt"
  cp -a "$(get_build_dir snes9x2010-lr)/LICENSE.txt" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/snes9x2010.txt"
  cp -a "$(get_build_dir supersnes9x-lr)/LICENSE" \
        "${INSTALL}/usr/share/butterflyos/licenses/components/supersnes9x.txt"

  mkdir -p "${INSTALL}/usr/share/butterflyos/flip-preloader"
  cp -a "${PKG_DIR}/sources/preloader-installer/manage.sh" \
        "${PKG_DIR}/sources/preloader-installer/patch-preloader.sh" \
        "${PKG_DIR}/sources/preloader-installer/fdtpatch.awk" \
        "${PKG_DIR}/sources/preloader-installer/BASEOS_LICENSE" \
        "${INSTALL}/usr/share/butterflyos/flip-preloader/"

  mkdir -p "${INSTALL}/usr/config/modules/images"
  cp -a "${PKG_DIR}/sources/ButterflyOS Boot Check.sh" \
        "${PKG_DIR}/sources/Export ButterflyOS Recovery Backup.sh" \
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
             "${INSTALL}/usr/config/modules/Export ButterflyOS Recovery Backup.sh" \
             "${INSTALL}/usr/config/modules/Restore Stock Miyoo Boot.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-onboarding.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-preloader/manage.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-preloader/patch-preloader.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/launch.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/install.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/patch-preloader.sh"
}

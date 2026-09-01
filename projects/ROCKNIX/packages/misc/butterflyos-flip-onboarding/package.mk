# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

PKG_NAME="butterflyos-flip-onboarding"
PKG_VERSION="4f32de5bae58cad07c54b5fb8450fc00385f4260"
PKG_LICENSE="unknown"
PKG_SITE="https://github.com/Zetarancio/Miyoo-Flip-Mainline-Linux-Reverse-Engineering"
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain dialog"
PKG_LONGDESC="ButterflyOS guided Miyoo Flip multiboot setup and recovery tools"
PKG_TOOLCHAIN="manual"

makeinstall_target() {
  local upstream="${PKG_BUILD}/upstream"
  local raw="https://raw.githubusercontent.com/Zetarancio/Miyoo-Flip-Mainline-Linux-Reverse-Engineering/${PKG_VERSION}/preloader-stock-rocknix/App/apommel-multiboot"

  mkdir -p "${upstream}"
  wget -q -O "${upstream}/launch.sh" "${raw}/launch.sh"
  wget -q -O "${upstream}/preloader-patched.img" "${raw}/preloader-patched.img"
  wget -q -O "${upstream}/preloader-stock.img" "${raw}/preloader-stock.img"
  wget -q -O "${upstream}/erase-preloader.sh" \
    "https://raw.githubusercontent.com/Zetarancio/Miyoo-Flip-Mainline-Linux-Reverse-Engineering/${PKG_VERSION}/preloader-stock-rocknix/App/PreloaderEraser/launch.sh"

  echo "120ef557effebb16dc92547bb3d0d6306a2f06e2b25b2ef0d73f0d211174b476  ${upstream}/launch.sh" | sha256sum -c -
  echo "ed10591f62ae0b8845ac9bd6cf80c896a2b172d32c7c4ef6564d305e8662c13d  ${upstream}/preloader-patched.img" | sha256sum -c -
  echo "dfdd7d20d6fd3beb18350dcf8fa58740b40b4baaf39467d45076f949053a2922  ${upstream}/preloader-stock.img" | sha256sum -c -
  echo "a65c5503a1d3a59e1a6c948647a055072ece1ac9e84740157c54aaa0c811d1ce  ${upstream}/erase-preloader.sh" | sha256sum -c -

  mkdir -p "${INSTALL}/usr/share/butterflyos/flip-preloader"
  cp -a "${upstream}/launch.sh" \
        "${upstream}/preloader-patched.img" \
        "${upstream}/preloader-stock.img" \
        "${INSTALL}/usr/share/butterflyos/flip-preloader/"

  mkdir -p "${INSTALL}/usr/config/modules/images"
  cp -a "${PKG_DIR}/sources/ButterflyOS Boot Check.sh" \
        "${PKG_DIR}/sources/Enable ButterflyOS SD Boot.sh" \
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
  cp -a "${upstream}/erase-preloader.sh" \
        "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/"

  chmod 0755 "${INSTALL}/usr/config/modules/ButterflyOS Boot Check.sh" \
             "${INSTALL}/usr/config/modules/Enable ButterflyOS SD Boot.sh" \
             "${INSTALL}/usr/config/modules/Restore Stock Miyoo Boot.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-onboarding.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-preloader/launch.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/launch.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/erase-preloader.sh"
}

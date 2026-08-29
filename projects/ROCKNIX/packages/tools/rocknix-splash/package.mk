# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 ROCKNIX (https://github.com/ROCKNIX)

PKG_NAME="rocknix-splash"
PKG_VERSION="9d295bcb74be2282e32c6b614efbea6036974ba8"
PKG_LICENSE="GPL"
PKG_SITE="https://rocknix.org"
PKG_URL="https://github.com/ROCKNIX/${PKG_NAME}/archive/${PKG_VERSION}.tar.gz"
PKG_DEPENDS_INIT="toolchain"
PKG_LONGDESC="ROCKNIX splash screen application"

post_makeinstall_init() {
  if [ "${IMAGE_SUBDEVICE}" = "Miyoo_Flip_V2" ]; then
    mkdir -p ${INSTALL}/usr/share/butterflyos
    cp ${PKG_DIR}/files/butterflyos-boot-640x480.ppm \
      ${INSTALL}/usr/share/butterflyos/boot.ppm
  fi
}

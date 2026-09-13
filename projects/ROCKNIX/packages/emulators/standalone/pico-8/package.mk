# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2023 JELOS (https://github.com/JustEnoughLinuxOS)

PKG_NAME="pico-8"
PKG_VERSION="95cb4d4f28e1743c6a7f3c0266049f68b2134b60"
PKG_LICENSE="GPLv2"
PKG_SITE=""
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain SDL2"
PKG_LONGDESC="PICO-8 Fantasy Console"
PKG_TOOLCHAIN="manual"

if [ ! "${OPENGL}" = "no" ]; then
  PKG_DEPENDS_TARGET+=" ${OPENGL} glu libglvnd"
fi

if [ "${OPENGLES_SUPPORT}" = yes ]; then
  PKG_DEPENDS_TARGET+=" ${OPENGLES}"
fi

makeinstall_target() {
  mkdir -p ${INSTALL}/usr/bin
  cp ${PKG_DIR}/sources/start_pico8.sh ${INSTALL}/usr/bin
  chmod 0755 ${INSTALL}/usr/bin/start_pico8.sh

  # ROCKNIX normally creates a synthetic Splore.png launcher in the ROM
  # directory. ButterflyOS keeps Games limited to content the user supplied,
  # while retaining PICO-8/Fake-08 support for legally obtained cartridges.
  if [ "${IMAGE_SUBDEVICE}" != "Miyoo_Flip_V2" ]; then
    mkdir -p ${INSTALL}/usr/lib/autostart/common
    cp ${PKG_DIR}/sources/autostart/common/* ${INSTALL}/usr/lib/autostart/common
    chmod 0755 ${INSTALL}/usr/lib/autostart/common/*
  fi
}

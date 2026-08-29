# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2023 JELOS (https://github.com/JustEnoughLinuxOS)

PKG_NAME="es-themes"
PKG_LICENSE="GPLv2"
PKG_SITE="https://rocknix.org"
PKG_DEPENDS_TARGET="es-theme-art-book-next"

if [ "${IMAGE_SUBDEVICE}" = "Miyoo_Flip_V2" ]; then
  PKG_DEPENDS_TARGET+=" es-theme-butterflyos"
fi
PKG_SECTION="virtual"
PKG_LONGDESC="EmulationStation themes package."

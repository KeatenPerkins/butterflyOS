# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2023 JELOS (https://github.com/JustEnoughLinuxOS)

PKG_NAME="es-themes"
PKG_LICENSE="GPLv2"
PKG_SITE="https://rocknix.org"
if [ "${IMAGE_SUBDEVICE}" = "Miyoo_Flip_V2" ]; then
  # ButterflyOS ships only its own audited theme on the Flip V2. Art Book Next
  # remains available to other ROCKNIX targets.
  PKG_DEPENDS_TARGET="es-theme-butterflyos"
else
  PKG_DEPENDS_TARGET="es-theme-art-book-next"
fi
PKG_SECTION="virtual"
PKG_LONGDESC="EmulationStation themes package."

# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2023 JELOS (https://github.com/JustEnoughLinuxOS)

PKG_NAME="gamesupport"
PKG_LICENSE="GPLv2"
PKG_SITE="https://rocknix.org"
PKG_SECTION="virtual"
PKG_LONGDESC="Game support software metapackage."

PKG_GAMESUPPORT="sixaxis rocknix-hotkey jstest-sdl gamecontrollerdb sdljoytest sdltouchtest control-gen sdl2text"

# The Miyoo Flip V2 has no touchscreen; omit both the tester and the on-screen
# touchscreen keyboard rather than merely hiding their launchers.
if [ "${IMAGE_SUBDEVICE}" = "Miyoo_Flip_V2" ]; then
  PKG_GAMESUPPORT="${PKG_GAMESUPPORT// sdltouchtest/}"
fi

case ${DEVICE} in
  RK3326|S922X|SM6115|SM8250|SM8550|SM8650|SM8750)
    PKG_GAMESUPPORT+=" mangohud"
    ;;
esac

# rocknix-touchscreen-keyboard requires sway
[[ "${WINDOWMANAGER}" = "swaywm-env" && "${IMAGE_SUBDEVICE}" != "Miyoo_Flip_V2" ]] && PKG_GAMESUPPORT+=" rocknix-touchscreen-keyboard"

PKG_DEPENDS_TARGET="${PKG_GAMESUPPORT}"

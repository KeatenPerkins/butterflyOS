# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024-present ROCKNIX (https://github.com/ROCKNIX)

PKG_NAME="modules"
PKG_VERSION="1.2"
PKG_LICENSE="GPL-2.0-only"
PKG_SITE=""
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain"
PKG_LONGDESC="OS Modules Package"
PKG_TOOLCHAIN="manual"

case ${DEVICE} in
  RK3399|RK3588|SM8250|SM8550|SM8650|SM8750|SM6115)
    PKG_DEPENDS_TARGET+=" gamepadtester qterminal"
    ;;
esac

if [ "${IMAGE_SUBDEVICE}" = "Miyoo_Flip_V2" ]; then
  PKG_DEPENDS_TARGET+=" butterflyos-flip-onboarding"
else
  PKG_DEPENDS_TARGET+=" rclone commander"
fi

makeinstall_target() {
  mkdir -p ${INSTALL}/usr/config/modules
    cp -rf ${PKG_DIR}/sources/* ${INSTALL}/usr/config/modules
}

post_makeinstall_target() {
  case ${DEVICE} in
    SM8650|SM8750) rm -f ${INSTALL}/usr/config/modules/*32bit* ;;
  esac

  if [[ "${INSTALLER_SUPPORT}" != "yes" || "${DISPLAYSERVER}" != "wl" ]]; then
    rm -f ${INSTALL}/usr/config/modules/Install*
  fi

  if [ "${IMAGE_SUBDEVICE}" != "Miyoo_Flip_V2" ]; then
    rm -f "${INSTALL}/usr/config/modules/ButterflyOS Boot Check.sh" \
          "${INSTALL}/usr/config/modules/Enable ButterflyOS SD Boot.sh" \
          "${INSTALL}/usr/config/modules/Export ButterflyOS Recovery Backup.sh" \
          "${INSTALL}/usr/config/modules/Restore Stock Miyoo Boot.sh" \
          "${INSTALL}/usr/config/modules/images/butterflyos-boot.svg"
    xmlstarlet ed --inplace \
      -d '/gameList/game[path="./ButterflyOS Boot Check.sh"]' \
      -d '/gameList/game[path="./Enable ButterflyOS SD Boot.sh"]' \
      -d '/gameList/game[path="./Export ButterflyOS Recovery Backup.sh"]' \
      -d '/gameList/game[path="./Restore Stock Miyoo Boot.sh"]' \
      -d '/gameList/game[path="./SD Card Info.sh"]' \
      "${INSTALL}/usr/config/modules/gamelist.xml"
  else
    # Hide generic ROCKNIX utilities that do not apply to the non-touchscreen,
    # low-power Flip V2. Their heavy runtime packages are excluded separately.
    for module in \
      "Start M8C.sh" "Test Touchscreen.sh" "GPcal.sh" \
      "commander.sh" "cloud_backup.sh" "cloud_restore.sh" \
      "Start 32bit Retroarch.sh" \
      "Install ROCKNIX.sh" "Start AetherSX2.sh" "Start Azahar.sh" \
      "Start CEMU.sh" "Start Dolphin.sh" "Start RPCS3.sh" \
      "Start Vita3K.sh" "Start Xemu.sh" \
      "Install Steam.sh" "Uninstall Steam.sh" \
      "Install Heroic Games Launcher.sh" "Uninstall Heroic Games Launcher.sh" \
      "Scan Heroic Games.sh"; do
      rm -f "${INSTALL}/usr/config/modules/${module}"
      xmlstarlet ed --inplace \
        -d "/gameList/game[path='./${module}']" \
        "${INSTALL}/usr/config/modules/gamelist.xml"
    done
    rm -f "${INSTALL}/usr/config/modules/images/rclone-backup.svg" \
          "${INSTALL}/usr/config/modules/images/rclone-restore.svg"
  fi
}

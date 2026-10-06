# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

PKG_NAME="butterflyos-flip-onboarding"
PKG_VERSION="2.6.12"
PKG_LICENSE="GPL-2.0-or-later AND MIT"
PKG_SITE="https://github.com/apommel/baseos-my355"
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain dialog SDL2 SDL2_ttf dejavu xxd Python3 pksav fbalpha2012-lr fbalpha2019-lr \
                    fbneo-lr genesis-plus-gx-lr genesis-plus-gx-wide-lr \
                    snes9x-lr snes9x2002-lr snes9x2005_plus-lr \
                    snes9x2010-lr supersnes9x-lr"
PKG_LONGDESC="ButterflyOS guided Miyoo Flip multiboot setup and recovery tools"
PKG_TOOLCHAIN="manual"

make_target() {
  cd "${PKG_BUILD}"
  ${CC} ${CFLAGS} ${CPPFLAGS} -I${SYSROOT_PREFIX}/usr/include \
    -o butterflyos-save-trade \
    "${PKG_DIR}/sources/butterflyos-save-trade.c" \
    -L${SYSROOT_PREFIX}/usr/lib -Wl,-Bstatic -lpksav -Wl,-Bdynamic -lm
}

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
        "${PKG_DIR}/sources/Butterfly Link.sh" \
        "${PKG_DIR}/sources/Extended Diagnostics.sh" \
        "${PKG_DIR}/sources/SD Card Info.sh" \
        "${PKG_DIR}/sources/Export ButterflyOS Recovery Backup.sh" \
        "${PKG_DIR}/sources/Prepare Game Card.sh" \
        "${PKG_DIR}/sources/Restore Stock Miyoo Boot.sh" \
        "${INSTALL}/usr/config/modules/"
  cp -a "${ROOT}/artwork/branding/icons/butterflyos-emblem-transparent-1024.png" \
        "${INSTALL}/usr/config/modules/images/butterflyos-boot.png"
  mkdir -p "${INSTALL}/usr/share/butterflyos"
  cp -a "${PKG_DIR}/sources/flip-onboarding.sh" \
        "${PKG_DIR}/sources/flip-onboarding.gptk" \
        "${PKG_DIR}/sources/game-card-ui.sh" \
        "${PKG_DIR}/sources/save-trade.gptk" \
        "${PKG_DIR}/sources/save-trade.dialogrc" \
        "${PKG_DIR}/sources/save-trade-ui.sh" \
        "${INSTALL}/usr/share/butterflyos/"
  mkdir -p "${INSTALL}/usr/bin"
  cp -a "${PKG_DIR}/sources/butterflyos-game-card" \
        "${PKG_DIR}/sources/butterflyos-gb-sprite-cache.py" \
        "${PKG_DIR}/sources/butterflyos-save-trade-sdl.py" \
        "${PKG_DIR}/sources/butterflyos-gen3-sprite-cache.py" \
        "${PKG_BUILD}/butterflyos-save-trade" \
        "${PKG_DIR}/sources/butterflyos-extended-diagnostics" \
        "${PKG_DIR}/sources/butterflyos-health-monitor" \
        "${PKG_DIR}/sources/butterflyos-sd-card-info" \
        "${PKG_DIR}/sources/butterflyos-tool-ui.py" \
        "${PKG_DIR}/sources/butterflyos-sd-card-info-sdl.py" \
        "${PKG_DIR}/sources/butterflyos-game-card-sdl.py" \
        "${PKG_DIR}/sources/butterflyos-lid-backlight" \
        "${INSTALL}/usr/bin/"

  mkdir -p "${INSTALL}/usr/lib/systemd/system/var-log.mount.d"
  cp -a "${PKG_DIR}/system.d/butterflyos-health-monitor.service" \
        "${PKG_DIR}/system.d/butterflyos-extended-diagnostics.service" \
        "${PKG_DIR}/system.d/butterflyos-lid-backlight.service" \
        "${INSTALL}/usr/lib/systemd/system/"
  cp -a "${PKG_DIR}/system.d/var-log.mount.d/butterflyos.conf" \
        "${INSTALL}/usr/lib/systemd/system/var-log.mount.d/"

  # Keep the Flip's OS-card SD controller (dwmmc_rockchip fe2b0000.mmc) always-on
  # so its broken runtime-PM resume path cannot drop mmcblk0 mid-run. Flip-only;
  # the second-card controller (fe2c0000.mmc) is excluded by the KERNEL match.
  mkdir -p "${INSTALL}/usr/lib/udev/rules.d"
  cp -a "${PKG_DIR}/udev.d/10-butterflyos-mmc0-runtimepm.rules" \
        "${INSTALL}/usr/lib/udev/rules.d/"

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
             "${INSTALL}/usr/config/modules/Butterfly Link.sh" \
             "${INSTALL}/usr/config/modules/Extended Diagnostics.sh" \
             "${INSTALL}/usr/config/modules/SD Card Info.sh" \
             "${INSTALL}/usr/config/modules/Export ButterflyOS Recovery Backup.sh" \
             "${INSTALL}/usr/config/modules/Prepare Game Card.sh" \
             "${INSTALL}/usr/config/modules/Restore Stock Miyoo Boot.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-onboarding.sh" \
             "${INSTALL}/usr/share/butterflyos/game-card-ui.sh" \
             "${INSTALL}/usr/share/butterflyos/save-trade-ui.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-preloader/manage.sh" \
             "${INSTALL}/usr/share/butterflyos/flip-preloader/patch-preloader.sh" \
             "${INSTALL}/usr/bin/butterflyos-game-card" \
             "${INSTALL}/usr/bin/butterflyos-gb-sprite-cache.py" \
             "${INSTALL}/usr/bin/butterflyos-save-trade-sdl.py" \
             "${INSTALL}/usr/bin/butterflyos-gen3-sprite-cache.py" \
             "${INSTALL}/usr/bin/butterflyos-save-trade" \
             "${INSTALL}/usr/bin/butterflyos-extended-diagnostics" \
             "${INSTALL}/usr/bin/butterflyos-health-monitor" \
             "${INSTALL}/usr/bin/butterflyos-sd-card-info" \
             "${INSTALL}/usr/bin/butterflyos-tool-ui.py" \
             "${INSTALL}/usr/bin/butterflyos-sd-card-info-sdl.py" \
             "${INSTALL}/usr/bin/butterflyos-game-card-sdl.py" \
             "${INSTALL}/usr/bin/butterflyos-lid-backlight" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/launch.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/install.sh" \
             "${INSTALL}/usr/share/butterflyos/stock-bootstrap/App/ButterflyOS_Setup/patch-preloader.sh"
}

post_install() {
  enable_service storage-log.service
  enable_service var-log.mount
  enable_service butterflyos-extended-diagnostics.service
  enable_service butterflyos-health-monitor.service
  enable_service butterflyos-lid-backlight.service
}

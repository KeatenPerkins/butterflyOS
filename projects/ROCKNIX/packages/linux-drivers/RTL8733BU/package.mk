# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024-present ROCKNIX (https://github.com/ROCKNIX)

PKG_NAME="RTL8733BU"
# Pinned one commit before the branch tip on purpose. RK3566 builds Linux 7.0.2
# (projects/ROCKNIX/packages/linux/package.mk), and tip commit 6821d54 rewires
# cfg80211_ops to wireless_dev-based wrappers for the 7.1 MLO signature change,
# which will not compile against 7.0.2. This commit already carries the static
# Kbuild and the Kconfig USB/CFG80211 fix, and still uses the net_device ops
# that 7.0.2 expects. Move to the tip only when the device moves to 7.1.
PKG_VERSION="c46aa25e237cb43f33390cf58eee5c69d9b32883"
PKG_LICENSE="GPL"
PKG_SITE="https://github.com/Awesome-Embedded-Learning-Studio/rtl8733bu-linux-driver"
PKG_URL="${PKG_SITE}/archive/${PKG_VERSION}.tar.gz"
PKG_LONGDESC="RTL8733BU driver (wirenboard base, in-tree Kbuild port)"
PKG_TOOLCHAIN="make"
PKG_IS_KERNEL_PKG="yes"

pre_make_target() {
  unset LDFLAGS

  # The Flip has one physical RTL8733BU radio.  The vendor driver's concurrent
  # mode creates a second station (wlan1) on the same wiphy; iwd then races the
  # two stations during autoconnect and can crash.  Keep AP/P2P support, but
  # expose only the primary wlan0 interface.
  sed -i 's/ -DCONFIG_CONCURRENT_MODE / /' Makefile
}

# This fork replaces the upstream 2803-line multi-chip Makefile with a static
# Kbuild whose only entry point is obj-$(CONFIG_RTL8733BU) += 8733bu.o, so the
# build has to go through the kernel's own module path with that symbol set.
# Chip options now live in the fork's ccflags-y rather than in make variables.
make_target() {
  kernel_make -C $(kernel_path) M=${PKG_BUILD} CONFIG_RTL8733BU=m modules
}

makeinstall_target() {
  mkdir -p ${INSTALL}/$(get_full_module_dir)/kernel/drivers/net/wireless
    cp *.ko ${INSTALL}/$(get_full_module_dir)/kernel/drivers/net/wireless
}

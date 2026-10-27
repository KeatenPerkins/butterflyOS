# SPDX-License-Identifier: GPL-2.0-or-later
PKG_NAME="bslap-backend"
PKG_VERSION="1.0.3"
PKG_ARCH="aarch64"
PKG_LICENSE="GPL-3.0-or-later AND GPL-2.0-only AND MIT"
PKG_SITE="https://github.com/libretro"
PKG_URL=""
PKG_DEPENDS_TARGET="toolchain Python3:host retroarch sameboy-lr gambatte-bslap-lr core-info"
PKG_LONGDESC="Pinned Bslap link backends, isolated from normal emulator defaults"
PKG_TOOLCHAIN="manual"
# This package records hashes of the native RetroArch/SameBoy dependencies.
# Recreate the manifest when their recipes/patches or staging code change.
PKG_NEED_UNPACK="$(get_pkg_directory retroarch) $(get_pkg_directory sameboy-lr) $(get_pkg_directory gambatte-bslap-lr) ${ROOT}/tools/bslap"
# Preserve exactly the binaries used in live qualification and their checksums.
PKG_BUILD_FLAGS="-strip"

makeinstall_target() {
  python3 "${ROOT}/tools/bslap/stage-backend.py" --install "${INSTALL}" --build "${BUILD}"
}

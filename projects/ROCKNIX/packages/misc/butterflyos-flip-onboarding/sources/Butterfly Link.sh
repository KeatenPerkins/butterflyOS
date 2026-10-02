#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile
log_dir="/storage/.config/butterflyos/logs"
log_file="${log_dir}/butterfly-link.log"
mkdir -p "${log_dir}"
if [[ "${BUTTERFLY_LINK_UI:-sdl}" != "dialog" && -x /usr/bin/butterflyos-save-trade-sdl.py ]]; then
  printf '\n[%s] Butterfly Link started\n' "$(date -u +%FT%TZ)" >> "${log_file}"
  /usr/bin/butterflyos-save-trade-sdl.py >> "${log_file}" 2>&1
  status=$?
  printf '[%s] Butterfly Link exited with status %s\n' "$(date -u +%FT%TZ)" "${status}" >> "${log_file}"
  # 127 means SDL/SDL_ttf/font initialization was unavailable.  Preserve the
  # existing dialog UI as a reliable fallback on unusual builds or displays.
  [[ ${status} -ne 127 ]] && exit "${status}"
fi
exec /usr/share/butterflyos/save-trade-ui.sh

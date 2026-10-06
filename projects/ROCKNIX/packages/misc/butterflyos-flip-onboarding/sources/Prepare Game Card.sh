#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile
if [[ -x /usr/bin/butterflyos-game-card-sdl.py ]]; then
  /usr/bin/butterflyos-game-card-sdl.py
  status=$?
  [[ "$status" -ne 127 ]] && exit "$status"
fi
exec /usr/share/butterflyos/game-card-ui.sh

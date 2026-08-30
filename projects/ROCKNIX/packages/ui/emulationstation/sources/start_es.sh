#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2024 ROCKNIX (https://github.com/ROCKNIX)

### setup is the same
. $(dirname $0)/es_settings

# Accept common ROM-folder names used by other handheld distributions. Only
# rename when ButterflyOS's canonical destination does not already exist, so
# existing libraries are never merged or overwritten automatically.
for ROM_ALIAS in FC:nes SFC:snes; do
  ROM_SOURCE="/storage/roms/${ROM_ALIAS%%:*}"
  ROM_DESTINATION="/storage/roms/${ROM_ALIAS##*:}"
  if [ -d "${ROM_SOURCE}" ] && [ ! -e "${ROM_DESTINATION}" ]; then
    mv "${ROM_SOURCE}" "${ROM_DESTINATION}"
  fi
done

# Keep the frontend responsive without pinning every RK3566 core at its
# highest operating point. Emulator launch profiles may override this.
ondemand

emulationstation --log-path /var/log --no-splash

#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2024 ROCKNIX (https://github.com/ROCKNIX)

### setup is the same
. $(dirname $0)/es_settings

# Accept common ROM-folder names used by other handheld distributions. New
# installs expose both names as the same directory. Existing libraries are
# consolidated without overwriting files that share a name.
for ROM_ALIAS in FC:nes SFC:snes; do
  ROM_SOURCE="/storage/roms/${ROM_ALIAS%%:*}"
  ROM_DESTINATION="/storage/roms/${ROM_ALIAS##*:}"
  if [ -d "${ROM_SOURCE}" ] && [ ! -e "${ROM_DESTINATION}" ]; then
    mv "${ROM_SOURCE}" "${ROM_DESTINATION}"
  fi

  mkdir -p "${ROM_DESTINATION}"

  if [ -d "${ROM_SOURCE}" ] && [ ! -L "${ROM_SOURCE}" ]; then
    while IFS= read -r -d '' ROM_FILE; do
      ROM_RELATIVE="${ROM_FILE#"${ROM_SOURCE}/"}"
      ROM_TARGET="${ROM_DESTINATION}/${ROM_RELATIVE}"
      if [ ! -e "${ROM_TARGET}" ]; then
        mkdir -p "$(dirname "${ROM_TARGET}")"
        mv "${ROM_FILE}" "${ROM_TARGET}"
      fi
    done < <(find "${ROM_SOURCE}" -type f -print0)

    # Remove directories emptied by the safe move. Conflicting files stay in
    # place rather than being overwritten or deleted.
    find "${ROM_SOURCE}" -depth -type d -empty -delete
  fi

  if [ ! -e "${ROM_SOURCE}" ]; then
    ln -s "${ROM_DESTINATION}" "${ROM_SOURCE}"
  fi
done

# Keep the frontend responsive without pinning every RK3566 core at its
# highest operating point. Emulator launch profiles may override this.
ondemand

emulationstation --log-path /var/log --no-splash

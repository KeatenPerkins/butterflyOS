#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2024 ROCKNIX (https://github.com/ROCKNIX)

# Rebuild ButterflyOS's combined OS-card/second-card index immediately before
# every EmulationStation scan. This makes Update Gamelists discover files added
# to either card through SSH, the web transfer tool, or a desktop computer.
if [ -x /usr/bin/butterflyos-game-card ]; then
  /usr/bin/butterflyos-game-card refresh >/dev/null 2>&1 || true
fi

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

# A 1080p HDMI menu otherwise keeps both EmulationStation and Sway rendering
# continuously while nothing changes. Use the frontend's event-driven idle
# mode by default on the Flip, while respecting any mode the user selected.
ES_SETTINGS="/storage/.emulationstation/es_settings.cfg"
if grep -qa "Miyoo Flip" /proc/device-tree/model 2>/dev/null && \
   [ -f "${ES_SETTINGS}" ] && \
   ! grep -q 'name="PowerSaverMode"' "${ES_SETTINGS}"; then
  sed -i '/<\/config>/i\  <string name="PowerSaverMode" value="enhanced" />' \
    "${ES_SETTINGS}"
fi

# The horizontal ButterflyOS home screen intentionally omits EmulationStation's
# tiny button legend. Besides reclaiming space, this removes its orphaned glyphs
# when the legend has no labels to display. Migrate existing installations too.
if [ -f "${ES_SETTINGS}" ] && \
   ! grep -q 'name="ShowHelpPrompts"' "${ES_SETTINGS}"; then
  sed -i '/<\/config>/i\  <bool name="ShowHelpPrompts" value="false" />' \
    "${ES_SETTINGS}"
fi

# One console-style media library. EmulationStation supplies folder browsing;
# MPV selects its audio or video playback path from the file extension.
mkdir -p /storage/media/Music /storage/media/Videos

# Refresh development-era system lists that predate the unified Media entry.
# Preserve the user's old list once for diagnosis; emulator selections and
# per-game settings live elsewhere and are not affected by this repair.
ACTIVE_SYSTEMS="/storage/.config/emulationstation/es_systems.cfg"
IMAGE_SYSTEMS="/usr/config/emulationstation/es_systems.cfg"
if [ -f "${ACTIVE_SYSTEMS}" ] && [ -f "${IMAGE_SYSTEMS}" ] && \
   ! grep -q '<name>mplayer</name>' "${ACTIVE_SYSTEMS}"; then
  cp -p "${ACTIVE_SYSTEMS}" "${ACTIVE_SYSTEMS}.before-butterfly-media"
  cp -p "${IMAGE_SYSTEMS}" "${ACTIVE_SYSTEMS}"
fi

# Consolidate the legacy top-level music directory used by early test images.
if [ -d /storage/music ]; then
  while IFS= read -r -d '' MEDIA_FILE; do
    MEDIA_RELATIVE="${MEDIA_FILE#/storage/music/}"
    MEDIA_TARGET="/storage/media/Music/${MEDIA_RELATIVE}"
    if [ ! -e "${MEDIA_TARGET}" ]; then
      mkdir -p "$(dirname "${MEDIA_TARGET}")"
      mv "${MEDIA_FILE}" "${MEDIA_TARGET}"
    fi
  done < <(find /storage/music -type f -print0)
  find /storage/music -depth -type d -empty -delete
fi

# Development images briefly used the singular directory name to work around
# EmulationStation treating every folder named "videos" as scraped artwork.
# Consolidate it without overwriting an identically named user file.
if [ -d /storage/media/Video ] && [ ! -L /storage/media/Video ]; then
  while IFS= read -r -d '' MEDIA_FILE; do
    MEDIA_RELATIVE="${MEDIA_FILE#/storage/media/Video/}"
    MEDIA_TARGET="/storage/media/Videos/${MEDIA_RELATIVE}"
    if [ ! -e "${MEDIA_TARGET}" ]; then
      mkdir -p "$(dirname "${MEDIA_TARGET}")"
      mv "${MEDIA_FILE}" "${MEDIA_TARGET}"
    fi
  done < <(find /storage/media/Video -type f -print0)
  find /storage/media/Video -depth -type d -empty -delete
fi

emulationstation --log-path /var/log --no-splash

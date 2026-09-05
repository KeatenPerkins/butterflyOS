#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile
set_kill set "mpv"
systemctl start mpv

FBWIDTH="$(fbwidth)"
FBHEIGHT="$(fbheight)"
if [[ ${FBWIDTH} -ge ${FBHEIGHT} ]]; then
  RES="${FBWIDTH}x${FBHEIGHT}"
else
  RES="${FBHEIGHT}x${FBWIDTH}"
fi

/usr/bin/mpv \
  --fullscreen \
  --geometry="${RES}" \
  --vo=wlshm \
  --force-window=yes \
  --audio-display=external-first \
  --cover-art-file=/usr/share/themes/es-theme-butterflyos/assets/butterflyos-logo.png \
  --osd-level=3 \
  --osd-align-x=center \
  --osd-align-y=center \
  --osd-font-size=24 \
  '--osd-msg1=${media-title}' \
  --input-gamepad=yes \
  --input-ipc-server=/tmp/mpvsocket \
  "${1}"

systemctl stop mpv

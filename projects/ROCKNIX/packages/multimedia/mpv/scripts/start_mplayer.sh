#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2020-present redwolftech
# Copyright (C) 2023 JELOS (https://github.com/JustEnoughLinuxOS)

. /etc/profile

# Use the lightweight ButterflyOS now-playing view for audio. Video keeps the
# hardware-decoding MPV path below.
case "${1,,}" in
  *.aac|*.ac3|*.dts|*.eac3|*.flac|*.m4a|*.mka|*.mp3|*.ogg|*.opus|*.wav|*.wma|*.wv)
    exec /usr/bin/start_audio_player.sh "${1}"
  ;;
esac

set_kill set "mpv"
systemctl start mpv

FBWIDTH="$(fbwidth)"
FBHEIGHT="$(fbheight)"

if [[ ${FBWIDTH} -ge ${FBHEIGHT} ]]; then
  RES="${FBWIDTH}x${FBHEIGHT}"
else
  RES="${FBHEIGHT}x${FBWIDTH}"
fi

/usr/bin/mpv --fullscreen --geometry=${RES} --hwdec=auto-safe --input-gamepad=yes --input-ipc-server=/tmp/mpvsocket "${1}"
systemctl stop mpv
exit 0

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

# PipeWire can leave HDMI as its automatic default after a monitor has been
# unplugged.  Choose the output that matches the display currently in use so
# audio does not silently disappear into an inactive HDMI sink.
if wlr-randr 2>/dev/null | awk '
    /^(DP|HDMI|DisplayPort)-/ { external=1; next }
    /^[A-Za-z]/ { external=0 }
    external && /Enabled: yes/ { found=1 }
    END { exit !found }
'; then
  AUDIO_DEVICE="pipewire/alsa_output._sys_devices_platform_hdmi-sound_sound_card0.stereo-fallback"
else
  AUDIO_DEVICE="pipewire/alsa_output._sys_devices_platform_rk817-sound_sound_card1.HiFi__Headphones__sink"
fi

/usr/bin/mpv \
  --fullscreen \
  --geometry="${RES}" \
  --vo=wlshm \
  --force-window=yes \
  --audio-device="${AUDIO_DEVICE}" \
  --audio-display=embedded-first \
  --cover-art-file=/usr/share/themes/es-theme-butterflyos/assets/butterflyos-logo.png \
  --osc=no \
  --osd-level=1 \
  --script=/usr/bin/butterfly_now_playing.lua \
  --input-gamepad=yes \
  --input-ipc-server=/tmp/mpvsocket \
  "${1}"

systemctl stop mpv

#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

. /etc/profile
if [[ -x /usr/bin/butterflyos-sd-card-info-sdl.py ]]; then
  /usr/bin/butterflyos-sd-card-info-sdl.py
  status=$?
  [[ "$status" -ne 127 ]] && exit "$status"
fi
# Keep a themed dialog fallback if graphical initialization is unavailable.
[[ -f /usr/share/butterflyos/save-trade.dialogrc ]] && export DIALOGRC=/usr/share/butterflyos/save-trade.dialogrc
REPORTER=/usr/bin/butterflyos-sd-card-info
REPORT=$(mktemp /tmp/butterflyos-sd-card-info.XXXXXX) || exit 1
CONTROLLER_PID=
cleanup() {
  if [[ -n "$CONTROLLER_PID" ]]; then
    kill "$CONTROLLER_PID" 2>/dev/null || true
    wait "$CONTROLLER_PID" 2>/dev/null || true
  fi
  rm -f "$REPORT"
  clear
}
trap cleanup EXIT
/usr/bin/control-gen_init.sh >/dev/null 2>&1 || true
if [[ -f /storage/.config/gptokeyb/control.ini && -f /usr/share/butterflyos/flip-onboarding.gptk ]]; then
  source /storage/.config/gptokeyb/control.ini
  get_controls
  /usr/bin/gptokeyb -c /usr/share/butterflyos/save-trade.gptk >/dev/null 2>&1 &
  CONTROLLER_PID=$!
fi
while true; do
  if ! python3 "$REPORTER" >"$REPORT" 2>&1; then
    dialog --title 'SD Card Info' --msgbox "Unable to read card information.\n$(cat "$REPORT")" 16 64
    break
  fi
  dialog --title 'SD Card Info - D-pad to scroll' --exit-label Back --textbox "$REPORT" 22 68
  choice=$(dialog --stdout --title 'SD Card Info' --cancel-label Close --menu 'Choose an action. Refresh collects new space information.' 13 62 2 refresh 'Refresh information' save 'Save this report') || break
  if [[ "$choice" == save ]]; then
    DEST=/storage/.config/system/sd-card-reports
    TARGET="$DEST/sd-card-info-$(date +%Y%m%d-%H%M%S)-$$.txt"
    if mkdir -p "$DEST" && cp "$REPORT" "$TARGET"; then
      dialog --title 'SD Card Info' --msgbox "Report saved:\n$TARGET" 12 64
    else
      dialog --title 'SD Card Info' --msgbox 'Unable to save the report. Check OS-card space and mount status.' 12 64
    fi
  fi
done

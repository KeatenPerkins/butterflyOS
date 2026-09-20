#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

. /etc/profile

MARKER=/storage/.config/butterflyos/extended-diagnostics.enabled
LOG_DIR=/storage/.config/system/extended-diagnostics
CONTROLLER_CONFIG=/usr/share/butterflyos/flip-onboarding.gptk
CONTROLLER_PID=

cleanup() {
  if [[ -n "${CONTROLLER_PID}" ]]; then
    kill "${CONTROLLER_PID}" 2>/dev/null || true
    wait "${CONTROLLER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

start_controller_input() {
  /usr/bin/control-gen_init.sh >/dev/null 2>&1 || true
  if [[ -f /storage/.config/gptokeyb/control.ini && -f "${CONTROLLER_CONFIG}" ]]; then
    source /storage/.config/gptokeyb/control.ini
    get_controls
    /usr/bin/gptokeyb -c "${CONTROLLER_CONFIG}" >/dev/null 2>&1 &
    CONTROLLER_PID=$!
  fi
}

start_controller_input

if [ -f "${MARKER}" ]; then
  dialog --title "ButterflyOS Extended Diagnostics" \
    --yesno "Extended diagnostics are ON.\n\nTurn them off? Existing logs will be kept in:\n${LOG_DIR}" 13 58
  if [ $? -eq 0 ]; then
    rm -f "${MARKER}"
    systemctl stop butterflyos-extended-diagnostics.service
    dialog --title "ButterflyOS Extended Diagnostics" \
      --msgbox "Extended diagnostics are now OFF.\n\nExisting logs were kept for review." 10 54
  fi
else
  dialog --title "ButterflyOS Extended Diagnostics" \
    --yesno "Extended diagnostics are OFF.\n\nEnable bounded one-minute system snapshots? Logs rotate automatically and use no more than about 25 MiB. No passwords are recorded." 14 58
  if [ $? -eq 0 ]; then
    mkdir -p "$(dirname "${MARKER}")" "${LOG_DIR}"
    touch "${MARKER}"
    systemctl start butterflyos-extended-diagnostics.service
    dialog --title "ButterflyOS Extended Diagnostics" \
      --msgbox "Extended diagnostics are now ON.\n\nRun this tool again to turn them off." 10 54
  fi
fi

clear

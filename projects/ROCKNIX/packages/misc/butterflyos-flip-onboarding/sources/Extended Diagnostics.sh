#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

. /etc/profile

MARKER=/storage/.config/butterflyos/extended-diagnostics.enabled
LOG_DIR=/storage/.config/system/extended-diagnostics

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

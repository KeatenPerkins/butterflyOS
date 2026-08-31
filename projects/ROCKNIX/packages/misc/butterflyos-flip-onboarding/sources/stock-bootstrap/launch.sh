#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CARD_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
CONFIRM_FILE="$SCRIPT_DIR/.erase-confirmation"
CONFIRM_SECONDS=300

clear 2>/dev/null || printf '\033[2J\033[H'
echo "============================================================"
echo "                   BUTTERFLYOS SETUP"
echo "============================================================"
echo

model=$(tr -d '\000' </proc/device-tree/model 2>/dev/null)
compatible=$(tr '\000' '\n' </proc/device-tree/compatible 2>/dev/null)
if ! echo "$model" | grep -qi miyoo || ! echo "$compatible" | grep -q rk3566; then
  echo "STOPPED: This installer is only for an RK3566 Miyoo Flip."
  echo "Detected model: ${model:-unknown}"
  sleep 12
  exit 1
fi

if [ ! -s "$CARD_ROOT/SYSTEM" ]; then
  echo "STOPPED: The ButterflyOS SYSTEM file is missing from this card."
  echo "Reflash the official ButterflyOS image and try again."
  sleep 12
  exit 1
fi

battery=
for supply in /sys/class/power_supply/*; do
  [ -r "$supply/capacity" ] || continue
  battery=$(cat "$supply/capacity" 2>/dev/null)
  case "$battery" in *[!0-9]*|'') battery= ;; esac
  [ -n "$battery" ] && break
done

powered=0
for supply in /sys/class/power_supply/*; do
  [ -r "$supply/online" ] || continue
  [ "$(cat "$supply/online" 2>/dev/null)" = 1 ] && powered=1
done

if [ "$powered" -ne 1 ] && { [ -z "$battery" ] || [ "$battery" -lt 50 ]; }; then
  echo "STOPPED: Connect the charger or charge the battery above 50%."
  echo "Battery reported: ${battery:-unknown}%"
  sleep 12
  exit 1
fi

now=$(date +%s)
confirmed=0
if [ -r "$CONFIRM_FILE" ]; then
  then=$(cat "$CONFIRM_FILE" 2>/dev/null)
  case "$then" in *[!0-9]*|'') then=0 ;; esac
  age=$((now - then))
  [ "$age" -ge 0 ] && [ "$age" -le "$CONFIRM_SECONDS" ] && confirmed=1
fi

if [ "$confirmed" -ne 1 ]; then
  echo "NO CHANGES WILL BE MADE ON THIS SCREEN."
  echo
  echo "ButterflyOS must temporarily disable the internal boot"
  echo "preloader so this prepared SD card can start once."
  echo
  echo "After ButterflyOS starts, open Tools and choose:"
  echo "  Enable ButterflyOS SD Boot"
  echo
  echo "That finishes reversible multiboot setup:"
  echo "  card inserted  -> ButterflyOS"
  echo "  card removed   -> original Miyoo system"
  echo
  echo "Recovery remains available through USB MASKROM. Opening the"
  echo "case and pressing the recovery button is a last resort only."
  echo
  echo "To confirm, wait for this screen to close, then launch"
  echo "ButterflyOS Setup a SECOND time within five minutes."
  echo
  echo "$now" >"$CONFIRM_FILE"
  sync
  sleep 20
  exit 0
fi

rm -f "$CONFIRM_FILE"
sync

echo "SECOND CONFIRMATION ACCEPTED."
echo
echo "Do not power off. The device will restart into ButterflyOS."
echo "If ButterflyOS does not start, connect the device to a PC for"
echo "USB MASKROM recovery. The SoC bootrom itself is not modified."
echo
sleep 5

exec sh "$SCRIPT_DIR/erase-preloader.sh"

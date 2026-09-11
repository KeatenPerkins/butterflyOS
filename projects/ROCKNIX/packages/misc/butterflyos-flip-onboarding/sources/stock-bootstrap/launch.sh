#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CARD_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
CONFIRM_FILE="$SCRIPT_DIR/.install-confirmation"
CONFIRM_SECONDS=300
LOG_FILE="$SCRIPT_DIR/setup-last.log"

show_screen() {
  image=$1
  SCREEN_PID=
  if [ -x /usr/bin/fbdisplay ] && [ -r "$image" ]; then
    /usr/bin/fbdisplay "$image" >/dev/null 2>&1 &
    SCREEN_PID=$!
  fi
}

exec >>"$LOG_FILE" 2>&1
echo
echo "=== ButterflyOS Setup $(date 2>/dev/null || echo unknown-time) ==="
echo "script=$0"
echo "script_dir=$SCRIPT_DIR"
echo "card_root=$CARD_ROOT"
echo "uid=$(id -u 2>/dev/null || echo unknown)"

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
  echo "ButterflyOS will inspect this device's own boot preloader,"
  echo "save an exact verified backup, and prepare a patched copy."
  echo
  echo "The second launch installs the device-local patch:"
  echo "  card inserted  -> ButterflyOS"
  echo "  card removed   -> original Miyoo system"
  echo
  echo "Unknown or modified preloaders are refused. The DDR firmware,"
  echo "SPL program, and stock OS remain exactly as this unit shipped."
  echo
  echo "To confirm, wait for this screen to close, then launch"
  echo "ButterflyOS Setup a SECOND time within five minutes."
  echo
  echo "Running the read-only compatibility check now..."
  if ! BUTTERFLYOS_DRY_RUN=1 CARD="$CARD_ROOT" \
      sh "$SCRIPT_DIR/install.sh"; then
    echo
    echo "STOPPED: This device did not pass the compatibility check."
    echo "Nothing was written to internal storage. See:"
    echo "  butterflyos-recovery/install-last.log"
    sleep 20
    exit 1
  fi
  echo "$now" >"$CONFIRM_FILE"
  sync
  show_screen "$SCRIPT_DIR/first-run.png"
  sleep 20
  [ -n "$SCREEN_PID" ] && kill "$SCREEN_PID" 2>/dev/null
  echo "CHECK PASSED: exact backup saved; internal storage unchanged."
  exit 0
fi

rm -f "$CONFIRM_FILE"
sync

echo "SECOND CONFIRMATION ACCEPTED."
echo
echo "Do not power off. The device will shut down after the patched"
echo "preloader has been written and read back successfully."
echo
show_screen "$SCRIPT_DIR/second-run.png"
sleep 5

if CARD="$CARD_ROOT" sh "$SCRIPT_DIR/install.sh"; then
  echo
  echo "SUCCESS: exact backup and patched readback both verified."
  echo "After shutdown, move the card to the RIGHT slot and power on."
  sync
  sleep 8
  poweroff
  exit 0
fi

echo
echo "INSTALLATION STOPPED. Do not remove power until you have read:"
echo "  butterflyos-recovery/install-last.log"
sleep 30
exit 1

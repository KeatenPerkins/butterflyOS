#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

set -u

TITLE="ButterflyOS Boot Setup"
SOURCE_DIR=/usr/share/butterflyos/flip-preloader
WORK_DIR=/storage/.config/butterflyos/flip-preloader
RECOVERY_DIR=/storage/butterflyos-recovery
DEVICE_BACKUP="$RECOVERY_DIR/preloader-original.img"
DEVICE_BACKUP_SUM="$DEVICE_BACKUP.sha256"
CONTROLLER_CONFIG=/usr/share/butterflyos/flip-onboarding.gptk
if [[ -f /storage/.config/butterflyos/flip-onboarding.gptk ]]; then
  CONTROLLER_CONFIG=/storage/.config/butterflyos/flip-onboarding.gptk
fi
CONTROLLER_PID=

stop_controller_input() {
  if [[ -n "$CONTROLLER_PID" ]]; then
    kill "$CONTROLLER_PID" 2>/dev/null || true
    wait "$CONTROLLER_PID" 2>/dev/null || true
  fi
}

start_controller_input() {
  /usr/bin/control-gen_init.sh >/dev/null 2>&1 || true
  if [[ -f /storage/.config/gptokeyb/control.ini && -f "$CONTROLLER_CONFIG" ]]; then
    # control.ini supplies the correct controller for this device. The mapping
    # turns the built-in controls into the keyboard input expected by dialog.
    source /storage/.config/gptokeyb/control.ini
    get_controls
    ${GPTOKEYB} "dialog" -c "$CONTROLLER_CONFIG" &
    CONTROLLER_PID=$!
  fi
}

trap stop_controller_input EXIT INT TERM
start_controller_input

show_message() {
  dialog --clear --title "$TITLE" --msgbox "$1" 18 64 < /dev/tty > /dev/tty 2> /dev/tty
}

ask_user() {
  dialog --clear --title "$TITLE" --yes-label "Continue" --no-label "Cancel" \
    --yesno "$1" 20 68 < /dev/tty > /dev/tty 2> /dev/tty
}

model=$(tr -d '\000' </proc/device-tree/model 2>/dev/null || true)
compatible=$(tr '\000' '\n' </proc/device-tree/compatible 2>/dev/null || true)
if [[ "$model" != *Miyoo* || "$compatible" != *rk3566* ]]; then
  show_message "This utility is only for the RK3566 Miyoo Flip.\n\nDetected model: ${model:-unknown}\n\nNothing was changed."
  exit 1
fi

mkdir -p "$WORK_DIR"
for file in launch.sh preloader-patched.img preloader-stock.img; do
  if [[ ! -f "$SOURCE_DIR/$file" ]]; then
    show_message "A required setup file is missing:\n\n$file\n\nNothing was changed."
    exit 1
  fi
  if [[ ! -f "$WORK_DIR/$file" ]] || ! cmp -s "$SOURCE_DIR/$file" "$WORK_DIR/$file"; then
    cp -f "$SOURCE_DIR/$file" "$WORK_DIR/$file"
  fi
done
chmod 700 "$WORK_DIR/launch.sh"

case "${ACTION:-}" in
  check)
    if ! ask_user "Run the ButterflyOS boot safety check?\n\nThis read-only check identifies the current boot preloader and verifies whether this device passes every safety gate.\n\nIt does not erase or write internal storage.\n\nA / Start: Continue\nB / Back: Cancel"; then
      clear
      exit 0
    fi
    sh "$WORK_DIR/launch.sh" backup
    ;;
  install)
    if ! ask_user "Enable automatic SD boot on this Miyoo Flip?\n\nWITH a compatible ButterflyOS card: ButterflyOS boots.\nWITHOUT the card: the original Miyoo system boots.\n\nThis writes only the internal 2 MiB boot preloader. The tool checks the device, flash geometry, bad blocks, battery, and DRAM data; makes a backup; verifies the write; and attempts rollback if verification fails.\n\nDo not power off during this operation."; then
      clear
      exit 0
    fi
    sh "$WORK_DIR/launch.sh" install
    ;;
  restore)
    restore_image=
    restore_description="KNOWN STOCK IMAGE\nNo verified device-specific backup was found. This restores stock behavior, but may not reproduce the exact SPL revision originally installed on every unit."

    if [[ -e "$DEVICE_BACKUP" || -e "$DEVICE_BACKUP_SUM" ]]; then
      if [[ ! -f "$DEVICE_BACKUP" || ! -f "$DEVICE_BACKUP_SUM" ]]; then
        show_message "The device-specific recovery backup is incomplete.\n\nExpected both:\n$DEVICE_BACKUP\n$DEVICE_BACKUP_SUM\n\nNothing was changed. Restore the missing file or remove the incomplete pair before trying again."
        exit 1
      fi

      expected_sha=$(awk 'NR == 1 { print tolower($1) }' "$DEVICE_BACKUP_SUM")
      actual_sha=$(sha256sum "$DEVICE_BACKUP" 2>/dev/null | awk '{ print tolower($1) }')
      backup_size=$(wc -c <"$DEVICE_BACKUP" | tr -d ' ')
      if [[ ! "$expected_sha" =~ ^[0-9a-f]{64}$ || \
            "$actual_sha" != "$expected_sha" || \
            "$backup_size" != 2097152 ]]; then
        show_message "The device-specific recovery backup failed validation.\n\nExpected SHA-256:\n${expected_sha:-invalid manifest}\n\nActual SHA-256:\n${actual_sha:-unreadable}\n\nSize: ${backup_size:-unknown} bytes (expected 2097152)\n\nNothing was changed. The generic image will not be selected silently while a broken personal backup is present."
        exit 1
      fi

      restore_image="$DEVICE_BACKUP"
      restore_description="EXACT DEVICE BACKUP\nUsing preloader-original.img from the ButterflyOS recovery folder.\nVerified SHA-256: $actual_sha"
    fi

    if ! ask_user "Restore stock Miyoo boot behavior?\n\nRESTORE SOURCE:\n$restore_description\n\nButterflyOS SD multiboot will be disabled. The internal Miyoo system will boot normally, even with the ButterflyOS card inserted.\n\nThe image is validated again by the low-level utility, the current preloader is backed up, and the write is verified.\n\nDo not power off during this operation."; then
      clear
      exit 0
    fi
    if [[ -n "$restore_image" ]]; then
      sh "$WORK_DIR/launch.sh" restore "$restore_image"
    else
      sh "$WORK_DIR/launch.sh" restore
    fi
    ;;
  *)
    show_message "Unknown boot setup action. Nothing was changed."
    exit 1
    ;;
esac

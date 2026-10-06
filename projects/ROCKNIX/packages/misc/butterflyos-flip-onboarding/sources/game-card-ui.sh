#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins

set -u

TITLE="ButterflyOS Game Card"
DEVICE=/dev/mmcblk1
PARTITION=/dev/mmcblk1p1
MOUNT=/storage/games-external
INDEXER=/usr/bin/butterflyos-game-card
CONTROLLER_CONFIG=/usr/share/butterflyos/save-trade.gptk
GRAPHICAL_BACKEND=0
[[ "${1:-}" == --graphical-backend ]] && GRAPHICAL_BACKEND=1
[[ -f /usr/share/butterflyos/save-trade.dialogrc ]] && export DIALOGRC=/usr/share/butterflyos/save-trade.dialogrc
CONTROLLER_PID=

stop_controller_input() {
  if [[ -n "${CONTROLLER_PID}" ]]; then
    kill -9 "${CONTROLLER_PID}" 2>/dev/null || true
    wait "${CONTROLLER_PID}" 2>/dev/null || true
  fi
}

start_controller_input() {
  /usr/bin/control-gen_init.sh >/dev/null 2>&1 || true
  if [[ -f /storage/.config/gptokeyb/control.ini && -f "${CONTROLLER_CONFIG}" ]]; then
    source /storage/.config/gptokeyb/control.ini
    get_controls
    /usr/bin/gptokeyb -c "${CONTROLLER_CONFIG}" >/dev/null 2>&1 &
    CONTROLLER_PID=$!
  fi
}

# The graphical frontend owns input and rendering; the backend retains all
# card checks and both erase confirmations. Each request requires a reply.
ui_request() {
  local reply
  printf 'UI_%s\t%s\n' "$1" "$(printf '%b' "$2" | base64 -w 0)"
  IFS= read -r reply || return 1
  [[ "$reply" == yes ]]
}

message() {
  if [[ "$GRAPHICAL_BACKEND" == 1 ]]; then
    ui_request MESSAGE "$1"
    return
  fi
  dialog --clear --title "${TITLE}" --msgbox "$1" 18 62 \
    </dev/tty >/dev/tty 2>/dev/tty
}

confirm() {
  if [[ "$GRAPHICAL_BACKEND" == 1 ]]; then
    ui_request CONFIRM "$1"
    return
  fi
  dialog --clear --title "${TITLE}" --yes-label "Continue" --no-label "Cancel" \
    --defaultno --yesno "$1" 20 66 </dev/tty >/dev/tty 2>/dev/tty
}

device_size() {
  awk '$4=="mmcblk1" {printf "%.1f GiB", $3 / 1048576}' /proc/partitions
}

safety_check() {
  local storage_source device_path external_source
  storage_source=$(awk '$2=="/storage" {print $1}' /proc/mounts)
  device_path=$(readlink -f /sys/class/block/mmcblk1/device 2>/dev/null || true)
  external_source=$(awk -v mountpoint="${MOUNT}" '$2==mountpoint {print $1}' /proc/mounts)

  [[ "${storage_source}" == /dev/mmcblk0p* ]] || {
    message "SAFETY CHECK FAILED\n\nThe OS-card identity is unexpected. Nothing was changed."
    return 1
  }
  # An already-mounted card is authoritative too. Some launches briefly race
  # sysfs device-link settlement even though the valid partition is mounted.
  [[ "${external_source}" == "${PARTITION}" ]] ||
    [[ -b "${DEVICE}" && -b "${PARTITION}" && "${device_path}" == *fe2c0000.mmc* ]] || {
    message "NO SECOND CARD FOUND\n\nPower off normally, insert a card in the second slot, then try again."
    return 1
  }
  [[ "${DEVICE}" != "${storage_source%p*}" ]] || {
    message "SAFETY CHECK FAILED\n\nThe selected card appears to contain ButterflyOS. Nothing was changed."
    return 1
  }
}

mount_card() {
  local fstype
  mkdir -p "${MOUNT}"
  mountpoint -q "${MOUNT}" && return 0
  [[ -b "${PARTITION}" ]] || return 1
  fstype=$(blkid -o value -s TYPE "${PARTITION}" 2>/dev/null || true)
  case "${fstype}" in
    exfat|vfat|fat|fat32|ext4|btrfs)
      mount -t "${fstype}" -o rw,noatime "${PARTITION}" "${MOUNT}"
      ;;
    ntfs)
      mount -t ntfs3 -o rw,noatime "${PARTITION}" "${MOUNT}"
      ;;
    *) return 1 ;;
  esac
}

create_library() {
  local dir
  mkdir -p "${MOUNT}/roms"
  for dir in bios dreamcast gb gba gbc mame2003plus music n64 nds nes \
             psp psx saturn savestates snes videos; do
    mkdir -p "${MOUNT}/roms/${dir}"
  done
  sync
  "${INDEXER}" refresh >/tmp/butterflyos-game-card-result 2>&1
}

prepare_existing() {
  safety_check || return
  if ! mount_card; then
    message "UNSUPPORTED CARD\n\nButterflyOS supports exFAT, FAT32, NTFS, ext4, and btrfs game cards.\n\nUse Erase and Format to prepare this card."
    return
  fi
  if ! touch "${MOUNT}/.butterflyos-write-test" 2>/dev/null; then
    message "CARD IS NOT WRITABLE\n\nNothing was changed. Check the card for filesystem errors."
    return
  fi
  rm -f "${MOUNT}/.butterflyos-write-test"
  create_library
  message "GAME CARD READY\n\nExisting files were preserved. Missing ButterflyOS folders were created and external games were indexed.\n\nRun Update Gamelists to refresh the library."
}

format_card() {
  local partitions
  safety_check || return
  confirm "ERASE SECOND CARD?\n\nTarget: ${DEVICE}\nSize: $(device_size)\n\nEVERYTHING on the second card will be permanently erased. The ButterflyOS card will not be touched." || return 0
  confirm "FINAL CONFIRMATION\n\nErase the entire second card and format it as exFAT?\n\nThis cannot be undone." || return 0

  # Recheck the target after the user has read both confirmation screens.
  safety_check || return
  if [[ "$GRAPHICAL_BACKEND" == 1 ]]; then
    ui_request PROGRESS "Preparing the second card...\n\nDo not power off or remove either card." || return
  else
    dialog --clear --title "${TITLE}" --infobox \
      "Preparing the second card...\n\nDo not power off or remove either card." 9 58 \
      </dev/tty >/dev/tty 2>/dev/tty
  fi

  "${INDEXER}" cleanup >/dev/null 2>&1 || true
  umount "${MOUNT}" 2>/dev/null || true
  umount "${PARTITION}" 2>/dev/null || true
  if awk -v target="${PARTITION}" '$1==target {found=1} END {exit !found}' /proc/mounts; then
    message "CARD IS IN USE\n\nThe second card could not be unmounted. Close games and transfers, then try again. Nothing was formatted."
    return 1
  fi

  partitions=$(awk '$4 ~ /^mmcblk1p[0-9]+$/ {count++} END {print count+0}' /proc/partitions)
  if [[ "${partitions}" != 1 || ! -b "${PARTITION}" ]]; then
    parted -s "${DEVICE}" mklabel gpt >/tmp/butterflyos-game-card-format.log 2>&1 &&
      parted -s "${DEVICE}" mkpart primary 1MiB 100% >>/tmp/butterflyos-game-card-format.log 2>&1
    partprobe "${DEVICE}" >>/tmp/butterflyos-game-card-format.log 2>&1 || true
    udevadm settle
  fi

  if [[ ! -b "${PARTITION}" ]] || ! mkfs.exfat -n BUTTERFLY "${PARTITION}" \
      >>/tmp/butterflyos-game-card-format.log 2>&1; then
    message "FORMAT COULD NOT FINISH\n\nPower off normally, start ButterflyOS again, and rerun this tool.\n\nNo OS-card data was touched."
    return
  fi

  sync
  if ! fsck.exfat -n "${PARTITION}" >>/tmp/butterflyos-game-card-format.log 2>&1 ||
     ! mount_card; then
    message "FORMAT VERIFICATION FAILED\n\nDo not use this game card yet. The OS card was not touched."
    return
  fi

  create_library
  message "GAME CARD READY\n\nThe second card is now exFAT, labeled BUTTERFLY, and contains the standard library folders.\n\nUse web transfer, network sharing, or a computer to add files."
}

show_status() {
  local text
  safety_check || return
  text=$("${INDEXER}" status 2>&1)
  message "SECOND GAME CARD\n\n${text}\n\nOS-card files have priority when both cards contain the same relative filename."
}

if [[ "$GRAPHICAL_BACKEND" == 1 ]]; then
  case "${2:-}" in
    prepare) prepare_existing ;;
    format) format_card ;;
    refresh)
      safety_check && mount_card && create_library &&
        message "LIBRARY REFRESHED\n\nGames and media from both cards are now available. Run Update Gamelists if the menu was already open."
      ;;
    status) show_status ;;
    *) exit 2 ;;
  esac
  exit $?
fi

trap stop_controller_input EXIT INT TERM
start_controller_input

while true; do
  choice=$(dialog --clear --title "${TITLE}" --cancel-label "Close" \
    --menu "Add storage without replacing the games already on your ButterflyOS card." \
    19 68 5 \
    prepare "Use existing card and keep its files" \
    format "Erase card and format as recommended exFAT" \
    refresh "Refresh games from both cards" \
    status "Show second-card status" \
    close "Return to Tools" \
    </dev/tty 2>&1 >/dev/tty) || break

  case "${choice}" in
    prepare) prepare_existing ;;
    format) format_card ;;
    refresh)
      safety_check && mount_card && create_library &&
        message "LIBRARY REFRESHED\n\nGames and media from both cards are now available. Run Update Gamelists if the menu was already open."
      ;;
    status) show_status ;;
    close) break ;;
  esac
done

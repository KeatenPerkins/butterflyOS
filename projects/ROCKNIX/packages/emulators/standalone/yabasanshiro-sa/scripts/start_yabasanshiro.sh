#!/bin/bash

# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2021-present Shanti Gilbert (https://github.com/shantigilbert)
# Copyright (C) 2023 JELOS (https://github.com/JustEnoughLinuxOS)

# Source predefined functions and variables
. /etc/profile
set_kill set "-9 yabasanshiro"

ROM_DIR="/storage/roms/saturn/yabasanshiro"
CONFIG_DIR="/storage/.config/yabasanshiro"
SOURCE_DIR="/usr/config/yabasanshiro"
BIOS_BACKUP="/storage/roms/bios/yabasanshiro"
SAVESTATE_DIR="/storage/roms/savestates/saturn/yabasanshiro/"

if [ ! -d "${ROM_DIR}" ]
then
  mkdir -p "${ROM_DIR}"
fi

if [ ! -d "${BIOS_BACKUP}" ]
then
  mkdir -p "${BIOS_BACKUP}"
fi

if [ ! -d "${CONFIG_DIR}" ]
then
  mkdir -p "${CONFIG_DIR}"
fi

if [ ! -d "${SAVESTATE_DIR}" ]
then
  mkdir -p "${SAVESTATE_DIR}"
fi

if [ ! -e "${CONFIG_DIR}/input.cfg" ]
then
  rm -f ${CONFIG_DIR}/keymapv2.json

  # Handle inputplumber platforms first
  if [[ "${HW_DEVICE}" =~ RK3576|SM6115|SM8550|SM8650|SM8750|SM8250 ]]; then
    GAMEPAD="'Sony Interactive Entertainment DualSense Wireless Controller'"
  else
    # Check for js0, else fall back to joypad
    if grep -q "js0" /proc/bus/input/devices; then
      GAMEPAD="'$(grep -b4 js0 /proc/bus/input/devices | awk 'BEGIN {FS="\""}; /Name/ {printf $2}')'"
    else
      GAMEPAD="'$(grep -b4 joypad /proc/bus/input/devices | awk 'BEGIN {FS="\""}; /Name/ {printf $2}')'"
    fi
  fi

  GAMEPADCONFIG=$(xmlstarlet sel -t -c "//inputList/inputConfig[@deviceName=${GAMEPAD}]" -n /storage/.emulationstation/es_input.cfg)

  MAPPING_FILE="/usr/config/yabasanshiro/devices/keymapv2_$(eval echo $GAMEPAD).json"
  if [ -e "${MAPPING_FILE}" ]; then
    cp ${MAPPING_FILE} ${CONFIG_DIR}/keymapv2.json
  fi

  if [ ! -z "${GAMEPADCONFIG}" ]
  then
    cat <<EOF >${CONFIG_DIR}/input.cfg
<?xml version="1.0"?>
<inputList>
${GAMEPADCONFIG}
</inputList>
EOF
  fi
fi

# YabaSanshiro does not derive a usable map for the Flip's built-in pad or the
# tested 8BitDo Xbox-mode controller. Install the hardware-qualified map on
# every launch so a stale first-launch file cannot leave Saturn without input.
# SDL assigns the first connected controller index 0 and the built-in pad index
# 1. With no external controller, rewrite the built-in entry as player/index 0.
if grep -q "Miyoo Flip" /proc/device-tree/model 2>/dev/null
then
  FLIP_MAPPING="${SOURCE_DIR}/devices/keymapv2_miyoo_flip.json"
  if grep -q 'Name="Xbox One S Controller"' /proc/bus/input/devices
  then
    cp -f "${FLIP_MAPPING}" "${CONFIG_DIR}/keymapv2.json"
  else
    jq '.player1 = .player2
        | .player1.DeviceID = 0
        | .["0_retrogame_joypad_19009b4d4b4800000111000000010000"] =
            .["1_retrogame_joypad_19009b4d4b4800000111000000010000"]
        | del(.player2,
              .["0_Xbox One S Controller_0300003e5e040000e002000000006800"],
              .["1_retrogame_joypad_19009b4d4b4800000111000000010000"])' \
      "${FLIP_MAPPING}" > "${CONFIG_DIR}/keymapv2.json"
  fi
fi

BIOS=""
GAME=$(echo "${1}"| sed "s#^/.*/##")
PLATFORM=$(echo "${2}"| sed "s#^/.*/##")
USE_BIOS=$(get_setting use_hlebios "${PLATFORM}" "${GAME}")
if [ ! "${USE_BIOS}" = 1 ]
then
  USE_BIOS=$(get_setting use_hlebios "${PLATFORM}")
fi

if [ "$USE_BIOS" = 1 ]
then
  for BIOS in saturn_bios.bin sega_101.bin mpr-17933.bin mpr-18811-mx.ic1 mpr-19367-mx.ic1 stvbios.zip
  do
    BIOS=$(find /storage/roms/bios -name ${BIOS} -print 2>/dev/null)
    if [ ! -z "${BIOS}" ]
    then
      BIOS="-b ${BIOS}"
      break
    fi
  done
fi

if [ ! -e "${CONFIG_DIR}/${GAME}.config" ]
then
  cp -f ${SOURCE_DIR}/.config "${CONFIG_DIR}/${GAME}.config"
fi

#Set the cores to use
CORES=$(get_setting "cores" "${PLATFORM}" "${GAME}")
if [ "${CORES}" = "little" ]
then
  EMUPERF="${SLOW_CORES}"
elif [ "${CORES}" = "big" ]
then
  EMUPERF="${FAST_CORES}"
else
  ### All..
  unset EMUPERF
fi

echo "Command: yabasanshiro -r 2 -i "${1}" ${BIOS}" >>/var/log/exec.log 2>&1
${EMUPERF} yabasanshiro -r 2 -i "${1}" ${BIOS} >>/var/log/exec.log 2>&1 &
emulator_pid=$!
printf '%s\n' "${emulator_pid}" > /tmp/butterflyos-standalone-hotkeys
trap 'rm -f /tmp/butterflyos-standalone-hotkeys; kill "${emulator_pid}" 2>/dev/null' EXIT INT TERM
wait "${emulator_pid}" ||:
rm -f /tmp/butterflyos-standalone-hotkeys
trap - EXIT INT TERM

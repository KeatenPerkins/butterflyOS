#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile

rom_count() {
  local rom_dir="$1"

  if [ ! -d "${rom_dir}" ]; then
    echo 0
    return
  fi

  find "${rom_dir}" -maxdepth 1 -type f \
    ! -name '.*' ! -name 'gamelist.xml' 2>/dev/null | wc -l
}

core_status() {
  if [ -f "/usr/lib/libretro/$1" ]; then
    echo "Ready"
  else
    echo "Core unavailable"
  fi
}

NES_GAMES=$(rom_count /storage/roms/nes)
SNES_GAMES=$(rom_count /storage/roms/snes)

MESSAGE="ButterflyOS preconfigures supported systems for you.
You do not need to configure RetroArch or download cores.

NINTENDO ENTERTAINMENT SYSTEM
Status: $(core_status nestopia_libretro.so)
Recommended core: Nestopia
Games found: ${NES_GAMES}
ROM folder: /storage/roms/nes
BIOS: Not required

SUPER NINTENDO
Status: $(core_status snes9x_libretro.so)
Recommended core: Snes9x
Games found: ${SNES_GAMES}
ROM folder: /storage/roms/snes
BIOS: Not required

Systems appear under Games after compatible game files are added.
Advanced emulator settings remain available from the game menu."

text_viewer -w -t "ButterflyOS System Manager" -m "${MESSAGE}"

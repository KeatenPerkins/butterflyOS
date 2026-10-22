#!/bin/bash
# Local development launcher; uses disposable saves and a separately named core.
set -euo pipefail
rom='/storage/roms/gba/Cable Link Test/Emerald - Cable Test.gba'
save="${rom%.gba}.srm"
core='/tmp/cores/gpsp_bfwords_libretro.so'
expected='8264211c676d0be7e606f3c39973ca0072b961ea208717d8d364280e4d56e4eb'
if pidof retroarch32 retroarch >/dev/null 2>&1; then
  echo 'Exit the running game before starting a diagnostic session.'
  exit 1
fi
test -s "$rom" && test -s "$save" && test -s "$core"
printf '%s  %s\n' "$expected" "$core" | sha256sum -c -
root='/storage/.config/butterflyos/gpsp-link-tests'
mkdir -p "$root"
session=$(mktemp -d "$root/cable-words-$(date +%Y%m%d-%H%M%S)-XXXXXX")
cp "$save" "$session/before.srm"
finish() {
  cp "$save" "$session/after.srm" || true
  cp /storage/.cache/log/exec.log "$session/exec.log" || true
}
trap finish EXIT
/usr/bin/runemu.sh "$rom" -Pgba --core=gpsp_bfwords --emulator=retroarch --controllers= -state_slot 0 -autosave 0

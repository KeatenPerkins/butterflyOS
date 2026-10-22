#!/bin/bash
# Local development launcher; uses disposable saves and a separately named core.
set -euo pipefail
rom='/storage/roms/gba/Cable Link Test/Emerald - Cable Test.gba'
save="${rom%.gba}.srm"
core='/tmp/cores/gpsp_bfrcnt_libretro.so'
expected='0dc8d45295092957d94388c92be634092ed067b9909aa7bfbb084e8770a93c25'
if pidof retroarch32 retroarch >/dev/null 2>&1; then
  echo 'Exit the running game before starting a diagnostic session.'
  exit 1
fi
test -s "$rom" && test -s "$save" && test -s "$core"
printf '%s  %s\n' "$expected" "$core" | sha256sum -c -
root='/storage/.config/butterflyos/gpsp-link-tests'
mkdir -p "$root"
session=$(mktemp -d "$root/cable-reset-$(date +%Y%m%d-%H%M%S)-XXXXXX")
cp "$save" "$session/before.srm"
finish() {
  cp "$save" "$session/after.srm" || true
  cp /storage/.cache/log/exec.log "$session/exec.log" || true
}
trap finish EXIT
/usr/bin/runemu.sh "$rom" -Pgba --core=gpsp_bfrcnt --emulator=retroarch --controllers= -state_slot 0 -autosave 0

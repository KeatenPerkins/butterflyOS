#!/bin/bash
# Local development launcher; uses disposable saves and a separately named core.
set -euo pipefail
rom='/storage/roms/gba/Cable Link Test/Emerald - Cable Test.gba'
save="${rom%.gba}.srm"
core='/tmp/cores/gpsp_bfplain_libretro.so'
expected='1ae51cbbc844f4c9574dbb2dc3853097d9badc53b32057ec84e1577615b91f55'
if pidof retroarch32 retroarch >/dev/null 2>&1; then
  echo 'Exit the running game before starting a diagnostic session.'
  exit 1
fi
test -s "$rom" && test -s "$save" && test -s "$core"
printf '%s  %s\n' "$expected" "$core" | sha256sum -c -
root='/storage/.config/butterflyos/gpsp-link-tests'
mkdir -p "$root"
session=$(mktemp -d "$root/retroarch-plain-$(date +%Y%m%d-%H%M%S)-XXXXXX")
frontend="$root/retroarch-current/retroarch32"
printf '%s  %s\n' '556a1d7b09ea280ba06d34ad53347864d6f4288702894cbe104842591bb5da89' "$frontend" | sha256sum -c -
cp "$save" "$session/before.srm"
cp /storage/.config/retroarch/retroarch.cfg "$session/retroarch.cfg"
echo 'config_save_on_exit = "false"' >> "$session/retroarch.cfg"
export BF_RA_TEST_CONFIG="$session/retroarch.cfg"
finish() {
  cp "$save" "$session/after.srm" || true
  cp /storage/.cache/log/exec.log "$session/exec.log" || true
}
trap finish EXIT
"$root/retroarch-current/runemu.sh" "$rom" -Pgba --core=gpsp_bfplain --emulator=retroarch --controllers= -state_slot 0 -autosave 0

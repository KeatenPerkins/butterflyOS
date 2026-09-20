#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

set -euo pipefail

ROOT=$(mktemp -d /tmp/butterfly-link-save-test.XXXXXX)
trap 'rm -rf -- "$ROOT"' EXIT

STORAGE=$ROOT/storage
EXTERNAL=$STORAGE/games-external
INTERNAL=$STORAGE/roms
RETRO=$STORAGE/.config/retroarch/saves
STATE=$STORAGE/.config/butterflyos/link
TOOL=${1:-$(dirname "$0")/../projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-link-save}

mkdir -p "$INTERNAL/gb" "$EXTERNAL/roms/gb" "$RETRO/SameBoy"
printf 'red-rom-test' >"$INTERNAL/gb/Pokemon Red.gb"
printf 'blue-rom-test' >"$EXTERNAL/roms/gb/Pokemon Blue.gb"
printf 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' >"$INTERNAL/gb/Pokemon Red.srm"
printf 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB' >"$EXTERNAL/roms/gb/Pokemon Blue.srm"

run_tool() {
  BUTTERFLY_LINK_STORAGE_ROOT="$STORAGE" \
  BUTTERFLY_LINK_EXTERNAL_ROOT="$EXTERNAL" \
  BUTTERFLY_LINK_INTERNAL_ROM_ROOT="$INTERNAL" \
  BUTTERFLY_LINK_RETROARCH_SAVE_ROOT="$RETRO" \
  BUTTERFLY_LINK_STATE_ROOT="$STATE" \
    bash "$TOOL" "$@"
}

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

# The save adjacent to the selected ROM is the automatic default.
discovery=$(run_tool discover "$INTERNAL/gb/Pokemon Red.gb")
grep -Fq $'selected=yes\tlocation=OS_CARD' <<<"$discovery" || fail "OS-card adjacent save was not selected"
grep -Fq 'path='"$INTERNAL/gb/Pokemon Red.srm" <<<"$discovery" || fail "discovery omitted Red save"

# A merged-library symlink must not produce a second copy of one physical save.
ln -s "$EXTERNAL/roms/gb/Pokemon Blue.srm" "$INTERNAL/gb/Pokemon Blue.srm"
discovery=$(run_tool discover "$EXTERNAL/roms/gb/Pokemon Blue.gb")
[[ $(grep -c '^selected=' <<<"$discovery") -eq 1 ]] || fail "symlinked save was duplicated"
grep -Fq $'location=GAME_CARD' <<<"$discovery" || fail "game-card location was not identified"

# Begin creates verified, isolated copies and commit atomically writes only the
# selected original.
begin_output=$(run_tool begin "$INTERNAL/gb/Pokemon Red.gb" "$INTERNAL/gb/Pokemon Red.srm")
session_id=$(sed -n 's/^session_id=//p' <<<"$begin_output")
working=$(sed -n 's/^working_save=//p' <<<"$begin_output")
backup=$(sed -n 's/^backup=//p' <<<"$begin_output")
[[ -n "$session_id" && -f "$working" && -f "$backup" ]] || fail "session files missing"
before_sha=$(sha256sum "$backup" | awk '{print $1}')
printf 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC' >"$working"
run_tool commit "$session_id" >/dev/null
[[ $(<"$INTERNAL/gb/Pokemon Red.srm") == CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC ]] || fail "commit did not update selected save"
[[ $(sha256sum "$backup" | awk '{print $1}') == "$before_sha" ]] || fail "immutable backup changed"
grep -qx COMMITTED "$STATE/sessions/$session_id/state" || fail "commit state missing"

# Restore validates the original backup, archives the current save, and puts
# the exact pre-session bytes back.
run_tool restore "$session_id" >/dev/null
[[ $(<"$INTERNAL/gb/Pokemon Red.srm") == AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA ]] || fail "restore did not recover original"
grep -qx RESTORED "$STATE/sessions/$session_id/state" || fail "restore state missing"
compgen -G "$STATE/sessions/$session_id/pre-restore-*" >/dev/null || fail "pre-restore archive missing"

# A save changed by another process after begin must never be overwritten.
conflict_output=$(run_tool begin "$INTERNAL/gb/Pokemon Red.gb" "$INTERNAL/gb/Pokemon Red.srm")
conflict_id=$(sed -n 's/^session_id=//p' <<<"$conflict_output")
conflict_working=$(sed -n 's/^working_save=//p' <<<"$conflict_output")
printf 'DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD' >"$conflict_working"
printf 'EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE' >"$INTERNAL/gb/Pokemon Red.srm"
if run_tool commit "$conflict_id" "$conflict_working" >/dev/null 2>&1; then
  fail "commit overwrote a concurrently changed save"
fi
[[ $(<"$INTERNAL/gb/Pokemon Red.srm") == EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE ]] || fail "conflict changed original"
run_tool abort "$conflict_id" >/dev/null

# Manual selection cannot escape the approved OS/game-card save trees.
printf 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF' >"$ROOT/outside.srm"
if run_tool begin "$INTERNAL/gb/Pokemon Red.gb" "$ROOT/outside.srm" >/dev/null 2>&1; then
  fail "outside save path was accepted"
fi

printf 'PASS: Butterfly Link save safety tests\n'

#!/bin/bash
# Exercise the real XML generator, including defaults appended after alternatives.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PROJECT_DIR="${ROOT}/projects"
PROJECT=ROCKNIX
DEVICE=RK3566
IMAGE_SUBDEVICE=Miyoo_Flip_V2
SYSTEM_COMMAND=''
source "${ROOT}/distributions/ROCKNIX/config/functions"
add_emu_doc() { :; }
add_system_doc() { :; }
TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT
for POSITION in first middle last; do
  ESTMP="${TEST_ROOT}/${POSITION}"
  case "$POSITION" in
    first) CORES='gpsp mgba vbam' ;;
    middle) CORES='mgba gpsp vbam' ;;
    last) CORES='mgba vbam gpsp' ;;
  esac
  for CORE in $CORES; do
    DEFAULT=false
    [ "$CORE" != gpsp ] || DEFAULT=true
    add_emu_core gba retroarch "$CORE" "$DEFAULT"
  done
  add_es_system gba
  COUNT=$(xmlstarlet sel -t -v 'count(//core[@default="true"])' "$ESTMP/gba.tmp")
  NAME=$(xmlstarlet sel -t -v '//core[@default="true"]' "$ESTMP/gba.tmp")
  [ "$COUNT" = 1 ] && [ "$NAME" = gpsp ]
done
echo 'Real XML generator: one gpSP default at first, middle and last positions passed.'

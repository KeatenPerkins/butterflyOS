#!/bin/sh
# Usage: sh tests/butterflyos-gba-sio-test.sh /path/to/patched/mgba/source
set -eu
ulimit -c 0
mgba_source=${1:?supply the patched mGBA source directory}
test_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
test_build=$(mktemp -d /tmp/butterfly-gba-sio-test.XXXXXX)
driver_source=${2:-$mgba_source}
cc -std=c99 -D_GNU_SOURCE -DMINIMAL_CORE=2 -DM_CORE_GBA -DM_CORE_GB \
    -ffunction-sections -fdata-sections -Wl,--gc-sections \
    -I"$driver_source/include" -I"$mgba_source/include" -I"$mgba_source/src" \
    "$test_dir/butterflyos-gba-sio-test.c" \
    "$driver_source/src/gba/sio/butterfly.c" \
    "$mgba_source/src/gba/sio.c" "$mgba_source/src/core/timing.c" \
    -o "$test_build/sio-test"
printf 'Test executable: %s\n' "$test_build/sio-test"
"$test_build/sio-test"
"$test_build/sio-test" master-delay

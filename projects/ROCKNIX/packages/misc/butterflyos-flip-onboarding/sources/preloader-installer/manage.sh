#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
# Verify or restore the exact device-local preloader backup from ButterflyOS.
set -u

MODE=${1:-check}
BACKUP=${2:-/flash/butterflyos-recovery/preloader-original.img}
SUM=$BACKUP.sha256
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LOG=/storage/butterflyos-recovery/${MODE}-last.log
SIZE=2097152
mkdir -p /storage/butterflyos-recovery
: >"$LOG" || exit 1
log() { echo "$*"; echo "$(date '+%H:%M:%S') $*" >>"$LOG" 2>/dev/null || true; }
die() { log "STOPPED: $*"; exit 1; }

case "$MODE" in check|restore) ;; *) die "unsupported action: $MODE" ;; esac
[ "$(id -u)" -eq 0 ] || die "must run as root"
model=$(tr -d '\000' </proc/device-tree/model 2>/dev/null)
compat=$(tr '\000' ' ' </proc/device-tree/compatible 2>/dev/null)
echo "$model" | grep -qi miyoo || die "not a Miyoo Flip: ${model:-unknown}"
echo "$compat" | grep -qi rk356 || die "not an RK356x device: ${compat:-unknown}"

MTD=
for name in preloader spl; do
  if [ -c "/dev/mtd/by-name/$name" ]; then MTD=$(readlink -f "/dev/mtd/by-name/$name"); break; fi
  node=$(grep "\"$name\"" /proc/mtd 2>/dev/null | head -n1 | cut -d: -f1)
  [ -n "$node" ] && [ -c "/dev/$node" ] && { MTD=/dev/$node; break; }
done
[ -n "$MTD" ] || die "preloader MTD partition not found"
line=$(grep "^${MTD##*/}:" /proc/mtd 2>/dev/null)
[ "$(echo "$line" | awk '{print $2}')" = 00200000 ] || die "preloader MTD is not exactly 2 MiB"
sys=/sys/class/mtd/${MTD##*/}
[ "$(cat "$sys/writesize" 2>/dev/null)" = 2048 ] || die "unexpected NAND page size"
[ "$(cat "$sys/erasesize" 2>/dev/null)" = 131072 ] || die "unexpected NAND erase size"

[ -f "$BACKUP" ] && [ -f "$SUM" ] || die "exact device backup or checksum is missing"
expected=$(awk 'NR==1 {print tolower($1)}' "$SUM")
case "$expected" in *[!0-9a-f]*|'') die "backup checksum is invalid" ;; esac
[ "${#expected}" -eq 64 ] || die "backup checksum is not SHA-256"
[ "$(wc -c <"$BACKUP")" -eq "$SIZE" ] || die "backup is not exactly 2 MiB"
[ "$(sha256sum "$BACKUP" | cut -c1-64)" = "$expected" ] || die "backup checksum mismatch"

patched=/tmp/butterflyos-expected-patched.img
current=/tmp/butterflyos-current-preloader.img
AWK_SCRIPT=$HERE/fdtpatch.awk sh "$HERE/patch-preloader.sh" "$BACKUP" "$patched" >>"$LOG" 2>&1 ||
  die "saved original has an unsupported preloader structure"
reader=$MTD
[ -c "${MTD}ro" ] && reader=${MTD}ro
dd if="$reader" of="$current" bs=2048 count=1024 2>>"$LOG" || die "could not read current preloader"
[ "$(wc -c <"$current")" -eq "$SIZE" ] || die "current preloader read is incomplete"
current_sha=$(sha256sum "$current" | cut -c1-64)
patched_sha=$(sha256sum "$patched" | cut -c1-64)
log "exact original: $expected"
log "expected patch: $patched_sha"
log "currently read: $current_sha"

if [ "$MODE" = check ]; then
  if [ "$current_sha" = "$patched_sha" ]; then
    log "CHECK PASSED: device-local ButterflyOS patch is installed"
    log "Nothing was written to internal storage."
    exit 0
  fi
  [ "$current_sha" = "$expected" ] && die "exact stock preloader is installed; SD boot patch is not enabled"
  die "current preloader matches neither the exact backup nor its derived patch"
fi

[ "$current_sha" = "$patched_sha" ] || die "refusing restore from an unexpected current preloader state"
capacity=0; online=0
for p in /sys/class/power_supply/*/capacity; do [ -r "$p" ] && capacity=$(cat "$p" 2>/dev/null) && break; done
case "$capacity" in ''|*[!0-9]*) capacity=0 ;; esac
for p in /sys/class/power_supply/*/online; do [ -r "$p" ] && [ "$(cat "$p" 2>/dev/null)" = 1 ] && online=1; done
[ "$capacity" -ge 50 ] || [ "$online" = 1 ] || die "battery is ${capacity}% and charger is offline"
command -v flash_erase >/dev/null 2>&1 || die "flash_erase is unavailable"
command -v nandwrite >/dev/null 2>&1 || die "nandwrite is unavailable"

n=1
while [ "$n" -le 3 ]; do
  log "restore attempt $n"
  flash_erase "$MTD" 0 0 >>"$LOG" 2>&1
  nandwrite -p "$MTD" "$BACKUP" >>"$LOG" 2>&1
  rm -f "$current"
  dd if="$reader" of="$current" bs=2048 count=1024 2>>"$LOG"
  if [ "$(sha256sum "$current" 2>/dev/null | cut -c1-64)" = "$expected" ]; then
    log "RESTORE PASSED: exact original readback verified"
    sync
    exit 0
  fi
  n=$((n + 1))
done
die "restore readback did not verify; keep power connected and use MASKROM recovery"

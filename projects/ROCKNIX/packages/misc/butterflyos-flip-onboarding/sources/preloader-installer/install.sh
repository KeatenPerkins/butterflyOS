#!/bin/sh
# ButterflyOS device-local preloader installer.
# Patch algorithm derived from BaseOS by Aurélien Pommel (MIT); see
# BASEOS_LICENSE. ButterflyOS safety wrapper copyright (C) 2026 Keaten Perkins,
# GPL-2.0-or-later.
set -u

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CARD=${CARD:-$(pwd)}
CARD=$(CDPATH= cd -- "$CARD" 2>/dev/null && pwd -P) || exit 1
FATMNT=/tmp/butterflyos-recovery-fat
OUTDIR=$CARD
MTD=${MTD:-/dev/mtd5}
MIN_BATTERY=50

CARDDEV=$(awk -v d="$CARD" '$2 == d { print $1; exit }' /proc/mounts)
case "$CARDDEV" in
  /dev/mmcblk*p*)
    for part in "${CARDDEV%p*}"p*; do
      blkid "$part" 2>/dev/null | grep -q 'TYPE="vfat"' || continue
      mkdir -p "$FATMNT"
      if mount -t vfat "$part" "$FATMNT" 2>/dev/null; then OUTDIR=$FATMNT; fi
      break
    done
    ;;
esac
RECOVERY_DIR=$OUTDIR/butterflyos-recovery
mkdir -p "$RECOVERY_DIR" || exit 1
LOG=$RECOVERY_DIR/install-last.log

log() { echo "$*"; echo "$(date '+%H:%M:%S') $*" >>"$LOG" 2>/dev/null || true; }
finish() {
  rc=${1:-0}
  sync
  mountpoint -q "$FATMNT" 2>/dev/null && umount "$FATMNT"
  return "$rc" 2>/dev/null || exit "$rc"
}
fail() { log "STOPPED: $*"; finish 1; exit 1; }

: >"$LOG" || exit 1
log "=== ButterflyOS device-local preloader installer $(date) ==="
if [ "${BUTTERFLYOS_DRY_RUN:-0}" = 1 ]; then log "mode: dry run"; else log "mode: write"; fi

[ "$(id -u)" -eq 0 ] || fail "installer must run as root"
model=$(tr -d '\000' </proc/device-tree/model 2>/dev/null)
compat=$(tr '\000' ' ' </proc/device-tree/compatible 2>/dev/null)
echo "$model" | grep -qi miyoo || fail "device model is not a Miyoo Flip: ${model:-unknown}"
echo "$compat" | grep -qi rk356 || fail "SoC is not RK356x: ${compat:-unknown}"

spl_line=$(grep '"spl"' /proc/mtd 2>/dev/null | head -n1)
[ -n "$spl_line" ] || fail "stock firmware does not expose an spl MTD partition"
[ "${spl_line%%:*}" = mtd5 ] || fail "spl is ${spl_line%%:*}, expected mtd5"
[ -c "$MTD" ] || fail "$MTD is unavailable"
size_hex=$(echo "$spl_line" | awk '{print $2}')
[ "$size_hex" = 00200000 ] || fail "spl size is $size_hex, expected 00200000"
[ -c "${MTD}ro" ] || fail "read-only ${MTD}ro device is unavailable"

sys=/sys/class/mtd/${MTD##*/}
[ "$(cat "$sys/writesize" 2>/dev/null)" = 2048 ] || fail "unexpected NAND page size"
[ "$(cat "$sys/erasesize" 2>/dev/null)" = 131072 ] || fail "unexpected NAND erase size"
if command -v mtdinfo >/dev/null 2>&1; then
  bad=$(mtdinfo "$MTD" 2>/dev/null | grep -i 'bad blocks' | head -n1 | tr -dc '0-9')
  [ -z "$bad" ] || [ "$bad" = 0 ] || fail "preloader contains $bad bad block(s)"
fi

capacity=
for p in /sys/class/power_supply/*/capacity; do
  [ -r "$p" ] && capacity=$(cat "$p" 2>/dev/null) && break
done
case "$capacity" in ''|*[!0-9]*) capacity=0 ;; esac
online=0
for p in /sys/class/power_supply/*/online; do
  [ -r "$p" ] && [ "$(cat "$p" 2>/dev/null)" = 1 ] && online=1
done
[ "$capacity" -ge "$MIN_BATTERY" ] || [ "$online" = 1 ] || fail "battery is ${capacity}% and charger is offline"
log "hardware gates passed; battery ${capacity}%, charger online=$online"

orig=/tmp/butterflyos-preloader-original.img
patched=/tmp/butterflyos-preloader-patched.img
readback=/tmp/butterflyos-preloader-readback.img
dd if="${MTD}ro" of="$orig" bs=2048 count=1024 2>>"$LOG" || fail "could not read the preloader"
[ "$(wc -c <"$orig")" -eq 2097152 ] || fail "preloader read was not exactly 2 MiB"
before=$(sha256sum "$orig" | cut -c1-64)
log "original SHA-256: $before"
case "$before" in
  dfdd7d20d6fd3beb18350dcf8fa58740b40b4baaf39467d45076f949053a2922)
    log "recognized qualified stock preloader revision"
    ;;
  *)
    fail "unknown stock preloader revision $before; send install-last.log to the ButterflyOS project for review"
    ;;
esac

AWK_SCRIPT=$HERE/fdtpatch.awk sh "$HERE/patch-preloader.sh" "$orig" "$patched" >>"$LOG" 2>&1 ||
  fail "preloader structure is unsupported or already modified; nothing was written"
after=$(sha256sum "$patched" | cut -c1-64)
log "patched SHA-256:  $after"

backup=$RECOVERY_DIR/preloader-original.img
backup_sum=$backup.sha256
cp "$orig" "$backup" || fail "could not save the device backup"
printf '%s  %s\n' "$before" "preloader-original.img" >"$backup_sum" || fail "could not save backup checksum"
sync
[ "$(sha256sum "$backup" | cut -c1-64)" = "$before" ] || fail "backup on SD did not verify"
log "verified exact device backup: $backup"

if [ "${BUTTERFLYOS_DRY_RUN:-0}" = 1 ]; then
  log "DRY RUN PASSED: no internal storage was written"
  finish 0
  exit 0
fi

command -v flash_erase >/dev/null 2>&1 || fail "flash_erase is unavailable"
command -v nandwrite >/dev/null 2>&1 || fail "nandwrite is unavailable"
n=1
while [ "$n" -le 3 ]; do
  log "write attempt $n"
  flash_erase "$MTD" 0 0 >>"$LOG" 2>&1
  nandwrite -p "$MTD" "$patched" >>"$LOG" 2>&1
  rm -f "$readback"
  dd if="${MTD}ro" of="$readback" bs=2048 count=1024 2>>"$LOG"
  if [ "$(sha256sum "$readback" 2>/dev/null | cut -c1-64)" = "$after" ]; then
    log "SUCCESS: patched preloader readback verified"
    finish 0
    exit 0
  fi
  log "patched readback mismatch"
  n=$((n + 1))
done

log "write verification failed; restoring the exact original"
n=1
while [ "$n" -le 3 ]; do
  flash_erase "$MTD" 0 0 >>"$LOG" 2>&1
  nandwrite -p "$MTD" "$orig" >>"$LOG" 2>&1
  rm -f "$readback"
  dd if="${MTD}ro" of="$readback" bs=2048 count=1024 2>>"$LOG"
  if [ "$(sha256sum "$readback" 2>/dev/null | cut -c1-64)" = "$before" ]; then
    log "original restored and verified"
    finish 1
    exit 1
  fi
  n=$((n + 1))
done
log "CRITICAL: original could not be restored; keep power connected and use MASKROM recovery"
finish 1
exit 1

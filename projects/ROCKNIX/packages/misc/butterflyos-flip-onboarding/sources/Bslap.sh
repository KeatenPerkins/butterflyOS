#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
. /etc/profile
log_dir=/storage/.config/butterflyos/logs
mkdir -p "$log_dir"
if [ ! -f /usr/share/bslap/backend.json ] && [ -f /storage/.config/butterflyos/bslap/butterflyos-bslap.py ]; then
  exec /usr/bin/python3 /storage/.config/butterflyos/bslap/butterflyos-bslap.py >> "$log_dir/bslap.log" 2>&1
fi
exec /usr/bin/python3 /usr/bin/butterflyos-bslap.py >> "$log_dir/bslap.log" 2>&1

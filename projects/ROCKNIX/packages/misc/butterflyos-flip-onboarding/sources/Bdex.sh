#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
. /etc/profile
log_dir=/storage/.config/butterflyos/logs
mkdir -p "$log_dir"
exec /usr/bin/butterflyos-bdex-sdl.py >> "$log_dir/bdex.log" 2>&1

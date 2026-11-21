#!/bin/sh
. /etc/profile
# One browser per device, including launches from the Tools menu.
exec 9>/run/butterflyos-files.lock
flock -n 9 || exit 0
files=/usr/share/butterflyos/files
[ -f "$files/main.py" ] || files=/storage/.config/butterflyos-tests/files
exec /usr/bin/python3 "$files/main.py"

#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile
sudo -n env ACTION=install /usr/share/butterflyos/flip-onboarding.sh
rc=$?
if [[ "$rc" -ne 0 ]]; then
  mkdir -p /storage/butterflyos-recovery
  printf '%s SD Boot launcher exited with code %s\n' "$(date '+%F %T')" "$rc" \
    >/storage/butterflyos-recovery/sd-boot-launch-error.log
fi
exit "$rc"

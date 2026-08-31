#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile
ACTION=check
export ACTION
exec /usr/share/butterflyos/flip-onboarding.sh

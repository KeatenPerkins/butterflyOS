#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2024 ROCKNIX (https://github.com/ROCKNIX)

### setup is the same
. $(dirname $0)/es_settings

# Keep the frontend responsive without pinning every RK3566 core at its
# highest operating point. Emulator launch profiles may override this.
ondemand

emulationstation --log-path /var/log --no-splash

#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile

MESSAGE="BUTTERFLYOS IN-GAME CONTROLS

Hold Menu, then press:

Start        Clean exit and create resume point
Select       Open RetroArch Quick Menu
L2           Load manual save state
R2           Create manual save state
Left/Right   Select save-state slot
R1           Toggle fast-forward
L1           Rewind when enabled for that system
X            Toggle FPS display

SAVE PROTECTION
Reopening a cleanly exited game automatically resumes it.
Manual save states keep a rolling history of the latest 10 states.

The Menu button by itself is reserved for a future quick-switch feature."

text_viewer -w -t "ButterflyOS Controls" -m "${MESSAGE}"

#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile

MESSAGE="BUTTERFLYOS IN-GAME CONTROLS

Press Menu alone to open or close the RetroArch Quick Menu.

Hold Menu, then press:

Start twice  Clean exit and create resume point
L2           Load manual save state
R2           Create manual save state
Left/Right   Select save-state slot
R1           Toggle fast-forward
L1           Rewind when enabled for that system
X            Toggle FPS display
Up/Down      Adjust screen brightness

SAVE PROTECTION
Reopening a cleanly exited game automatically resumes it.
Manual save states keep a rolling history of the latest 10 states.

Standalone emulators may use their own menus and shortcuts."

text_viewer -w -t "ButterflyOS Controls" -m "${MESSAGE}"

#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later

. /etc/profile

MESSAGE="WELCOME TO BUTTERFLYOS

ButterflyOS is a friendly gaming system built on ROCKNIX.

ADD GAMES
Open the STORAGE partition on a computer or connect over the network.
Place NES games in roms/nes or roms/FC.
Place SNES games in roms/snes or roms/SFC.

REFRESH
From the Games screen, open Game Settings and choose Update Gamelists after adding games while the device is running.

PLAY
Choose Games, select a system, then select a game.
ButterflyOS uses tested, preconfigured cores where available.

LEAVE A GAME
Hold Menu and press Start for a clean exit.
A clean exit creates an automatic resume point.

POWER OFF
Use Start, Quit, then Shut Down System before removing power or the SD card.

See Controls Guide and System Manager in Tools for more help."

text_viewer -w -t "ButterflyOS Quick Start" -m "${MESSAGE}"

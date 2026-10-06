#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Butterfly Link-style frontend for the existing second-card backend."""
import base64
import os
import selectors
import subprocess
import sys
import time
from pathlib import Path

import importlib.util


def confirm(ui, text):
    offset = 0
    while True:
        maximum = ui.frontend.draw_message(
            'FORMAT SECOND SD CARD', text,
            'A Review choice    B Cancel    UP/DOWN Scroll', offset)
        action = ui.action()
        if action == 'back':
            return False
        if action == 'select':
            return ui.menu('CONFIRM SECOND CARD', [
                ('Cancel', 'Keep the card and return to Tools'),
                ('Continue', 'Proceed with the action described above')], selected=0) == 1
        if action == 'up':
            offset = max(0, offset - 1)
        elif action == 'down':
            offset = min(maximum, offset + 1)
        if action is None:
            time.sleep(0.01)


def run_backend(ui, action, backend=Path('/usr/share/butterflyos/game-card-ui.sh')):
    # Only the shell backend touches disks. It requests both confirmations and
    # waits for explicit replies before reaching its formatting commands.
    if action not in ('prepare', 'format', 'refresh', 'status'):
        raise ValueError('Unknown card action')
    ui.frontend.draw_message('SECOND SD CARD', 'Checking the second card...',
                             'Please wait', 0)
    with subprocess.Popen(['/bin/bash', str(backend), '--graphical-backend', action],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, bufsize=0) as process:
        output = []
        buffered = b''
        reported = False
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        try:
            while True:
                if b'\n' not in buffered:
                    if not selector.select(timeout=0.02):
                        # Keep SDL responsive during indexing/formatting. Cancellation
                        # is offered before destructive work, never halfway through it.
                        ui.action()
                        continue
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        if buffered:
                            output.append(buffered.decode('utf-8', errors='replace'))
                        break
                    buffered += chunk
                    continue
                raw, buffered = buffered.split(b'\n', 1)
                line = raw.decode('utf-8', errors='replace')
                kind, separator, payload = line.rstrip('\n').partition('\t')
                if separator and kind in ('UI_MESSAGE', 'UI_CONFIRM', 'UI_PROGRESS'):
                    text = base64.b64decode(payload, validate=True).decode('utf-8')
                    accepted = True
                    if kind == 'UI_CONFIRM':
                        accepted = confirm(ui, text)
                    elif kind == 'UI_MESSAGE':
                        reported = True
                        ui.message('SECOND SD CARD', text)
                    else:
                        ui.frontend.draw_message('PREPARING SECOND CARD', text,
                                                 'Please wait', 0)
                    process.stdin.write(b'yes\n' if accepted else b'no\n')
                    process.stdin.flush()
                else:
                    output.append(line.rstrip('\n'))
            status = process.wait()
            if status and not reported:
                ui.message('CARD ACTION STOPPED', '\n'.join(output[-12:]) or
                           'The card action could not finish. Return to Tools and try again.')
        finally:
            selector.close()
            process.stdin.close()


def main():
    ui = None
    try:
        path = Path(__file__).with_name('butterflyos-tool-ui.py')
        spec = importlib.util.spec_from_file_location('butterfly_tool_ui', path)
        common = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(common)
        ui = common.ToolUI('Format 2nd SD Card')
    except Exception as error:
        print('Game-card graphical initialization failed: ' + str(error), file=sys.stderr)
        return 127
    try:
        items = [('Keep files', 'Set up an existing card without erasing it'),
                 ('Format', 'Erase the second card and format it as exFAT'),
                 ('Refresh', 'Refresh games from both cards'),
                 ('Status', 'Show second-card status'),
                 ('Close', 'Return to Tools')]
        selected = 0
        while True:
            chosen = ui.menu('SECOND SD CARD', items, selected)
            if chosen is None or chosen == 4:
                return 0
            selected = chosen
            run_backend(ui, ('prepare', 'format', 'refresh', 'status')[chosen])
    finally:
        ui.close()


if __name__ == '__main__':
    sys.exit(main())

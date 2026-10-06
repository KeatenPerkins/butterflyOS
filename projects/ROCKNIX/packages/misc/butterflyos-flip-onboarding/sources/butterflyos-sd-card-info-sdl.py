#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Keaten Perkins
"""Controller-operated SD Card Info using the Butterfly Link visual style."""
import datetime
import importlib.machinery
import importlib.util
from pathlib import Path
import sys


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def overview(info, report):
    parts = []
    for card in report['cards']:
        parts.append(card['title'].upper())
        if 'available_bytes' in card:
            parts.append('Available: ' + info.size(card['available_bytes']))
            parts.append('Used: ' + info.size(card['used_bytes']) + ' of ' + info.size(card['total_bytes']))
        elif card['mounted']:
            parts.append('Mounted; space information unavailable')
        else:
            parts.append('Inserted but not mounted' if card['present'] else 'No card detected')
        parts.append('')
    parts.append('Combined available: ' + info.size(report['combined_available_bytes']))
    return '\n'.join(parts)


def main():
    root = Path(__file__).resolve().parent
    ui = None
    try:
        common = load('butterfly_tool_ui', root / 'butterflyos-tool-ui.py')
        info = load('butterfly_sd_card_reporter', root / 'butterflyos-sd-card-info')
        ui = common.ToolUI('SD Card Info')
    except Exception as error:
        print('SD Card Info graphical initialization failed: ' + str(error), file=sys.stderr)
        return 127
    try:
        report = info.collect()
        ui.message('SD CARD INFO', overview(info, report))
        selected = 0
        items = [('Overview', 'Space available on both cards'),
                 ('OS card', 'Capacity, space, filesystem and mount status'),
                 ('Game card', 'Second-card capacity and mount status'),
                 ('Updates', 'Space available for OS updates'),
                 ('Refresh', 'Collect new space information'),
                 ('Save', 'Save a text report to the OS card'),
                 ('Close', 'Return to Tools')]
        while True:
            chosen = ui.menu('SD CARD INFO', items, selected)
            if chosen is None or chosen == 6:
                return 0
            selected = chosen
            if chosen == 0:
                ui.message('SD CARD INFO', overview(info, report))
            elif chosen in (1, 2):
                card = report['cards'][chosen - 1]
                single = dict(report, cards=[card])
                text = info.render(single).split('Combined available:', 1)[0]
                ui.message(card['title'].upper(), text.split('\n\n', 1)[1].strip())
            elif chosen == 3:
                text = info.render(report).split('OS UPDATE SPACE\n', 1)[1]
                ui.message('OS UPDATE SPACE', text)
            elif chosen == 4:
                report = info.collect()
                ui.message('SPACE REFRESHED', overview(info, report))
            elif chosen == 5:
                directory = Path('/storage/.config/system/sd-card-reports')
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
                    path = directory / ('sd-card-info-' + stamp + '.txt')
                    path.write_text(info.render(report))
                    ui.message('REPORT SAVED', str(path))
                except OSError as error:
                    ui.message('UNABLE TO SAVE REPORT', str(error))
    finally:
        ui.close()


if __name__ == '__main__':
    sys.exit(main())

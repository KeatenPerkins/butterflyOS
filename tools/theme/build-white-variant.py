#!/usr/bin/env python3
"""Render white card borders from existing SVG sources (requires rsvg-convert)."""
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'projects/ROCKNIX/packages/ui/themes/es-theme-butterflyos'
BASE = PACKAGE / 'files'
OUTPUT = PACKAGE / 'white-files'


def main():
    OUTPUT.mkdir(exist_ok=True)
    theme = (BASE / 'theme.xml').read_text()
    theme, count = re.subn(r'    <image name="butterfly-brand" extra="true">.*?</image>\n', '', theme, flags=re.S)
    assert count == 1
    (OUTPUT / 'theme.xml').write_text(theme)
    # Keep the SVG geometry and embedded original artwork. Re-render cards
    # rather than recoloring arbitrary pixels in existing PNG images.
    cards = {'card.svg': 'card.png', 'menu/games.svg': 'menu/games.png',
             'menu/tools.svg': 'menu/tools.png', 'menu/media.svg': 'menu/media.png',
             'menu/auto-favorites.svg': 'menu/auto-favorites.png',
             'menu/settings.svg': 'menu/settings-card.png'}
    with tempfile.TemporaryDirectory(prefix='butterfly-white-theme-') as directory:
        staging = Path(directory) / 'assets'
        shutil.copytree(BASE / 'assets', staging)
        for svg, png in cards.items():
            text = (staging / svg).read_text()
            text = re.sub(r'stroke="(?!none")[^"]+"', 'stroke="#ffffff"', text)
            (staging / svg).write_text(text)
            target = OUTPUT / 'assets' / svg
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
            with (BASE / 'assets' / png).open('rb') as handle:
                width, height = struct.unpack('>II', handle.read(24)[16:24])
            subprocess.run(['rsvg-convert', '-w', str(width), '-h', str(height),
                            '-o', str(OUTPUT / 'assets' / png), str(staging / svg)], check=True)
    print('Generated ButterflyOS White theme and six white-border cards.')


if __name__ == '__main__':
    main()

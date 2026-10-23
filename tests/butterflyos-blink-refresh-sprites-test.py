#!/usr/bin/env python3
"""Refresh sprites through Blink using private ROMs; never open a game save."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-save-trade-sdl.py'
spec = importlib.util.spec_from_file_location('blink_refresh_test', SOURCE)
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom_root', type=Path)
    args = parser.parse_args()
    # Confirm the actual main-menu action routes into refresh and returns normally.
    menu = ui.PAGES['main'][2]
    index = next(i for i, item in enumerate(menu) if item[0] == 'refresh-sprites')
    front = Mock()
    front.next_key.side_effect = [ui.KEY_DOWN] * index + [ui.KEY_RETURN, ui.KEY_ESCAPE]
    with patch.object(ui, 'SDLFrontEnd', return_value=front), \
            patch.object(ui, 'start_controller', return_value=None), \
            patch.object(ui, 'refresh_sprites') as refresh, patch.object(ui, 'debug'), \
            patch.object(ui.time, 'sleep'):
        assert ui.main() == 0
        refresh.assert_called_once_with(front)
    with patch.object(ui, 'choose_list', return_value=None), \
            patch.object(ui, '_rom_candidates') as candidates:
        ui.refresh_sprites(front)
        candidates.assert_not_called()
    with patch.object(ui, 'choose_list', return_value=0), \
            patch.object(ui, '_rom_candidates', return_value=[]), \
            patch.object(ui, 'notice') as notice:
        ui.refresh_sprites(front)
        assert notice.call_args.args[1] == 'MATCHING ROM NEEDED'
    with tempfile.TemporaryDirectory() as folder:
        for generation, name in [(1, 'Blue.gb'), (2, 'Crystal.gbc'), (3, 'Emerald.gba')]:
            rom = next(args.rom_root.rglob(name))
            before = hashlib.sha256(rom.read_bytes()).hexdigest()
            with patch.object(ui, 'STATE_ROOT', folder), \
                    patch.object(ui, '_rom_candidates', return_value=[str(rom)]), \
                    patch.object(ui, '_find_saves', side_effect=AssertionError('Refresh read saves')), \
                    patch.object(ui, 'notice') as notice:
                with patch.object(ui, 'choose_list', side_effect=[generation - 1, 0]):
                    ui.refresh_sprites(front)
                assert notice.call_args.args[1] == 'SPRITES REFRESHED'
                sprite = next((Path(folder) / 'sprite-cache' / before / 'front').glob('*.png'))
                original = sprite.read_bytes()
                sprite.write_bytes(b'broken sprite')
                with patch.object(ui, 'choose_list', side_effect=[generation - 1, 0]):
                    ui.refresh_sprites(front)
                assert sprite.read_bytes() == original
                assert notice.call_args.args[1] == 'SPRITES REFRESHED'
            assert hashlib.sha256(rom.read_bytes()).hexdigest() == before
    print('PASS: menu routing, cancellation, missing ROM, and forced damaged-sprite repair for Gen 1/2/3; ROMs unchanged and no saves opened.')


if __name__ == '__main__':
    main()

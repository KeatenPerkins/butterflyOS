#!/usr/bin/env python3
"""Compare raw and ZIP gift/event inputs using a private ROM fixture directory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'


def load(filename):
    spec = importlib.util.spec_from_file_location(filename, SOURCES / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom_root', type=Path)
    args = parser.parse_args()
    ui = load('butterflyos-save-trade-sdl.py')
    gen1 = load('butterflyos-gen1-gift.py')
    gen2 = load('butterflyos-gen2-gift.py')
    crystal = load('butterflyos-crystal-event.py')
    count = 0
    with tempfile.TemporaryDirectory() as folder:
        for generation, names, module in [(1, ['Red', 'Blue', 'Yellow'], gen1),
                                          (2, ['Gold', 'Silver', 'Crystal'], gen2)]:
            for name in names:
                extension = '.gb' if generation == 1 else '.gbc'
                raw = next(args.rom_root.rglob(name + extension))
                before = hashlib.sha256(raw.read_bytes()).hexdigest()
                zipped = Path(folder) / (name + '.zip')
                with zipfile.ZipFile(zipped, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('readme.txt', 'Not a ROM')
                    archive.write(raw, 'nested/' + raw.name)
                assert ui.rom_cache_digest(generation, str(zipped)) == before
                # Exercise the full gift routing with the real ZIP reader and
                # cache metadata whose container/content hashes are different.
                cache = Path(folder) / (name + '-cache')
                cache.mkdir()
                (cache / 'manifest.json').write_text(json.dumps({
                    'rom_sha256': hashlib.sha256(zipped.read_bytes()).hexdigest(),
                    'rom_content_sha256': before}))
                fake_save = ('/private/' + name + '.srm', 'PLAYER', name, [])
                prepare_name = 'prepare_gen%d_gift' % generation
                unreadable = Path(folder) / ('broken-' + name + '.zip')
                unreadable.write_bytes(b'not a ZIP archive')
                with patch.object(ui, 'notice'), \
                        patch.object(ui, 'choose_save', return_value=fake_save), \
                        patch.object(ui, 'ensure_sprite_cache', return_value=str(cache)), \
                        patch.object(ui, '_rom_candidates', return_value=[str(unreadable), str(zipped)]), \
                        patch.object(ui, 'choose_list', return_value=0), \
                        patch.object(ui, 'choose_copy_destination', return_value=(0, 0)), \
                        patch.object(ui, prepare_name, return_value=(None, 'test stop')) as prepare:
                    if generation == 1:
                        ui.gen1_gift_workflow(None)
                    else:
                        ui.gen2_gift_workflow(None)
                    prepare.assert_called_once()
                presets = module.PRESETS if generation == 1 else ['mew', 'odd-egg-pichu']
                for preset in presets:
                    if preset not in module.PRESETS:
                        continue
                    assert module.gift_from_rom(raw, preset, dvs=[1, 2, 3, 4]) == module.gift_from_rom(zipped, preset, dvs=[1, 2, 3, 4])
                    count += 1
                if name == 'Crystal':
                    errors = []
                    for rom in (raw, zipped):
                        try:
                            crystal.validate(b'', rom)
                        except ValueError as error:
                            errors.append(str(error))
                    assert errors == ['Use an ordinary Crystal in-game save, not a save state.'] * 2
                # Modifying the content must still fail the exact retail whitelist.
                damaged = Path(folder) / ('modified-' + name + '.zip')
                with zipfile.ZipFile(damaged, 'w') as archive:
                    archive.writestr(raw.name, raw.read_bytes()[:-1] + bytes([raw.read_bytes()[-1] ^ 1]))
                try:
                    module.gift_from_rom(damaged, 'mew')
                except ValueError:
                    pass
                else:
                    raise AssertionError('Modified ROM accepted')
                assert hashlib.sha256(raw.read_bytes()).hexdigest() == before
        ambiguous = Path(folder) / 'two.zip'
        with zipfile.ZipFile(ambiguous, 'w') as archive:
            archive.writestr('one.gb', b'X' * 0x150)
            archive.writestr('two.gb', b'X' * 0x150)
        try:
            ui.rom_cache_digest(1, str(ambiguous))
        except ValueError as error:
            assert 'exactly-one' in str(error)
        else:
            raise AssertionError('Ambiguous ZIP accepted')
    print('PASS:', count, 'raw/ZIP gift comparisons, six ROM digests and modified-ROM refusals, invalid ZIPs skipped during matching, Crystal ROM qualification, ambiguous ZIP refusal; source ROMs unchanged.')


if __name__ == '__main__':
    main()

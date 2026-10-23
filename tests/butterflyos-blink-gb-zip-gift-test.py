#!/usr/bin/env python3
"""Compare raw and ZIP gift/event inputs using a private ROM fixture directory."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import zipfile

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
    print('PASS:', count, 'raw/ZIP gift comparisons, six ROM digests and modified-ROM refusals, Crystal ROM qualification, ambiguous ZIP refusal; source ROMs unchanged.')


if __name__ == '__main__':
    main()

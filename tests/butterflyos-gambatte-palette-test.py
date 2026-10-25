#!/usr/bin/env python3
"""Run the launcher's actual palette functions against isolated settings."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

root = Path(__file__).resolve().parents[1]
source = (root / 'projects/ROCKNIX/packages/rocknix/sources/scripts/setsettings.sh').read_text()
functions = source[source.index('function gambatte_setting()'):source.index('function setup_controllers()')]
rom = 'Pokemon - Blue Version (USA, Europe) (SGB Enhanced).zip'


class PaletteTest(unittest.TestCase):
    def generate(self, settings, fallback='', initial='custom_option = "keep"\n'):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            config = path / 'system.cfg'
            config.write_text(settings)
            option = path / 'config/Gambatte/Gambatte.opt'
            option.parent.mkdir(parents=True)
            option.write_text(initial)
            env = dict(os.environ, SYSTEM_CONFIG=str(config), RETROARCH_PATH=folder,
                       PLATFORM='gb', ROM=rom, CORE='gambatte', FALLBACK=fallback)
            script = 'log() { :; }; game_setting() { if [ "$1" = renderer.colorization ]; then printf "%s" "$FALLBACK"; fi; };\n'
            subprocess.run(['bash', '-c', script + functions + '\nset_gambatte'], env=env, check=True)
            return option.read_text()

    def test_legacy_game_key_and_unrelated_option_preserved(self):
        result = self.generate('gb["'+rom+'"]-renderer.colorization=GBC - Blue\n')
        self.assertIn('gambatte_gb_colorization = "internal"', result)
        self.assertIn('gambatte_gb_internal_palette = "GBC - Blue"', result)
        self.assertIn('custom_option = "keep"', result)
        self.assertNotIn('palette_twb64', result)

    def test_canonical_game_key_precedes_legacy_and_system(self):
        result = self.generate('gb.renderer.colorization=GBC - Green\n'
            'gb["'+rom+'"]-renderer.colorization=GBC - Red\n'
            'gb["'+rom+'"].renderer.colorization=GBC - Blue\n')
        self.assertIn('gambatte_gb_internal_palette = "GBC - Blue"', result)

    def test_legacy_game_overrides_canonical_system(self):
        result = self.generate('gb.renderer.colorization=GBC - Red\n'
            'gb["'+rom+'"]-renderer.colorization=GBC - Blue\n')
        self.assertIn('gambatte_gb_internal_palette = "GBC - Blue"', result)

    def test_auto_and_none(self):
        for choice, mode in [('auto', 'auto'), ('none', 'disabled')]:
            result = self.generate('gb-renderer.colorization='+choice+'\n')
            self.assertIn('gambatte_gb_colorization = "'+mode+'"', result)

    def test_no_selection_preserves_manual_options(self):
        original = 'gambatte_gb_colorization = "GBC"\ncustom_option = "keep"\n'
        self.assertEqual(original, self.generate('', initial=original))

    def test_global_fallback_and_repeated_palette_keys(self):
        result = self.generate('', fallback='GBC - Blue', initial=
            'gambatte_gb_colorization = "disabled"\ngambatte_gb_colorization = "GBC"\n')
        self.assertEqual(1, result.count('gambatte_gb_colorization ='))
        self.assertIn('gambatte_gb_internal_palette = "GBC - Blue"', result)


if __name__ == '__main__':
    unittest.main()

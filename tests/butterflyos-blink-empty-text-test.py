#!/usr/bin/env python3
"""Blank wrapped lines must not send zero-width text to SDL_ttf."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-save-trade-sdl.py'
spec = importlib.util.spec_from_file_location('blink_ui', SOURCE)
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


class BlankTextRegression(unittest.TestCase):
    def setUp(self):
        self.front = ui.SDLFrontEnd.__new__(ui.SDLFrontEnd)
        self.front.sdl = Mock()
        self.front.renderer = object()
        self.front.refresh_text_scale = lambda: None
        self.rendered = []

        def texture(value, size, color, bold=False):
            if not value:
                raise RuntimeError('Text has zero width')
            self.rendered.append(value)
            return object(), len(value) * 8, size
        self.front.text_texture = texture

    def test_empty_optional_list_fields(self):
        self.front.draw_list('ROM SELECTION', '', [('ROM', ''), ('', 'Original.zip')], 0, '')
        self.assertIn('Original.zip', self.rendered)
        self.front.sdl.SDL_RenderPresent.assert_called_once()

    def test_notice_blank_lines_and_footer(self):
        self.front.draw_message('ROM NEEDED', 'First paragraph.\n\nSecond paragraph.', '')
        self.assertIn('First paragraph.', self.rendered)
        self.assertIn('Second paragraph.', self.rendered)
        self.front.sdl.SDL_RenderPresent.assert_called_once()

    def test_gen1_party_preview_without_optional_identity(self):
        record = dict(where='Party', slot=0, name='TEST', generation=1,
                      level=None, nature='', held=0, moves=[1])
        self.front.draw_sprite_browser('Save', 'Party is read-only', [record], 0, None)
        self.assertIn('TEST', self.rendered)
        self.front.sdl.SDL_RenderPresent.assert_called_once()

    def test_gift_save_label_keeps_trainer_and_full_filename(self):
        filename = 'Pokemon - Blue Version (USA, Europe) (SGB Enhanced).srm'
        save = ('/storage/roms/gb/' + filename, 'KeatenB', 'Red/Blue', [])
        with patch.object(ui, 'generation_saves', return_value=[save]), \
                patch.object(ui, 'choose_list', return_value=0) as menu:
            self.assertEqual(ui.choose_save(None, 1, 'GIFT DESTINATION SAVE'), save)
        label = menu.call_args.args[3][0][1]
        self.assertTrue(label.startswith('KeatenB | OS Card | '))
        self.assertIn(filename, label)
        self.assertTrue(label.endswith('PC 0'))


if __name__ == '__main__':
    unittest.main()

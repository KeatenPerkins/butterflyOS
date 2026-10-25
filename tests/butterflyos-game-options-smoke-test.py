#!/usr/bin/env python3
"""Check actual launcher functions with temporary configs, without device access."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / 'projects/ROCKNIX/packages/rocknix/sources/scripts/setsettings.sh').read_text()
PROFILE = (ROOT / 'projects/ROCKNIX/packages/rocknix/profile.d/001-functions').read_text()
ROM = 'Pokemon - Blue Version (USA, Europe) (SGB Enhanced).zip'


def function(text, name):
    start = text.index('function ' + name + '()')
    end = text.find('\nfunction ', start + 1)
    return text[start:end if end != -1 else len(text)]


FUNCTIONS = function(PROFILE, 'get_setting') + '\n'
for name in ('game_setting', 'clear_setting', 'flush_settings', 'add_setting',
             'match', 'set_filtering', 'set_integerscale', 'set_aspectratio',
             'set_shader', 'set_filter', 'set_rewind', 'set_autosave',
             'set_savestates', 'set_runahead', 'set_audiolatency', 'set_fps'):
    FUNCTIONS += function(SCRIPT, name) + '\n'
for name in ('CORE_RATIOS', 'NO_REWIND', 'NO_RUNAHEAD', 'IS_32BIT'):
    match = re.search(r'declare -a ' + name + r'=\(.*?\)', SCRIPT, re.S)
    if match:
        FUNCTIONS += match.group() + '\n'


def generate(settings, name, platform='gb'):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)
        (path / 'system.cfg').write_text(settings)
        (path / 'retroarch.cfg').write_text('unrelated_preference = "keep"\n')
        (path / 'states').mkdir()
        env = dict(os.environ, J_CONF=str(path / 'system.cfg'),
                   ROM=ROM, PLATFORM=platform, CORE='gambatte', AUTOSAVE='', SNAPSHOT='',
                   TMP_CONFIG=str(path / 'append.cfg'), RETROARCH_CONFIG=str(path / 'retroarch.cfg'),
                   SNAPSHOTS=str(path / 'states'), LOGGING='off')
        run = subprocess.run(['bash', '-c', 'log() { :; };\n' + FUNCTIONS + '\n' + name + '\nflush_settings'],
                             env=env, text=True, capture_output=True, check=True)
        if run.stderr:
            raise AssertionError(run.stderr)
        result = dict(re.findall(r'^([^=\n]+) = "(.*)"$', (path / 'append.cfg').read_text(), re.M))
        assert 'unrelated_preference = "keep"' in (path / 'retroarch.cfg').read_text()
        return result


class GameOptionsSmoke(unittest.TestCase):
    def test_common_options_per_system_and_per_game(self):
        cases = [
            ('smooth','1','set_filtering','video_smooth','1'),
            ('smooth','0','set_filtering','video_smooth','0'),
            ('integerscale','1','set_integerscale','video_scale_integer','1'),
            ('integerscale','0','set_integerscale','video_scale_integer','0'),
            ('ratio','4/3','set_aspectratio','aspect_ratio_index','0'),
            ('ratio','none','set_aspectratio','aspect_ratio_index','22'),
            ('shaderset','none','set_shader','video_shader_enable','false'),
            ('shaderset','test-shader','set_shader','video_shader','test-shader'),
            ('videofilter','none','set_filter','video_filter',''),
            ('rewind','1','set_rewind','rewind_enable','true'),
            ('rewind','0','set_rewind','rewind_enable','false'),
            ('autosave','1','set_autosave','savestate_auto_save','true'),
            ('autosave','0','set_autosave','savestate_auto_load','false'),
            ('incrementalsavestates','0','set_savestates','savestate_auto_index','false'),
            ('incrementalsavestates','1','set_savestates','savestate_auto_index','true'),
            ('maxincrementalsaves','8','set_savestates','savestate_max_keep','8'),
            ('runahead','1','set_runahead','run_ahead_frames','1'),
            ('runahead','0','set_runahead','run_ahead_enabled','false'),
            ('audiolatency','64','set_audiolatency','audio_latency','64'),
            ('showFPS','1','set_fps','fps_show','1'),
        ]
        for key, value, name, output, expected in cases:
            for prefix in ('gb', 'gb["'+ROM+'"]'):
                with self.subTest(key=key, value=value, scope=prefix):
                    settings = prefix+'.'+key+'='+value+'\n'
                    self.assertEqual(expected, generate(settings,name)[output])

    def test_game_overrides_system(self):
        result = generate('gb.smooth=0\ngb["'+ROM+'"].smooth=1\n', 'set_filtering')
        self.assertEqual('1',result['video_smooth'])

    def test_global_fallback(self):
        self.assertEqual('64',generate('global.audiolatency=64\n','set_audiolatency')['audio_latency'])


if __name__ == '__main__':
    unittest.main()

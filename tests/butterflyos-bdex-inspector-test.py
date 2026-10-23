#!/usr/bin/env python3
"""Known stat vectors, generation rules and inspector navigation regressions."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

SOURCES = Path(__file__).resolve().parents[1] / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'
def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCES / name)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m
stats = load('butterflyos-bdex-inspector.py')
app = load('butterflyos-bdex-sdl.py')


class StatTests(unittest.TestCase):
    def test_gen3_integer_rounding_and_nature(self):
        record = dict(generation=3, dex=1, level=50, personality=3,
                      ivs=[31]*6, evs=[252]*6)
        info = {'base_stats': {'1': [50]*6}}
        before = copy.deepcopy(record)
        self.assertEqual(stats.calculated(record, info), [157,112,102,102,91,102])
        self.assertEqual(record, before)
        record['evs'] = [255]*6
        self.assertEqual(stats.calculated(record, info), [157,112,102,102,91,102])
        record['dex'] = 292
        self.assertEqual(stats.calculated(record, {'base_stats': {'292': [50]*6}})[0], 1)

    def test_gen1_hp_dv_and_stat_experience(self):
        record = dict(generation=1, dex=1, level=50, dvs=[15]*4, stat_exp=[65535]*5)
        self.assertEqual(stats.inherited(record), [15]*5)
        self.assertEqual(stats.calculated(record, {'base_stats': {'1': [50]*5}}), [156,101,101,101,101])
        record['dvs'] = [1,0,1,0]
        self.assertEqual(stats.inherited(record)[0], 10)
        self.assertEqual([stats.effort_bonus(x) for x in [0,1,9,10,16,65535]], [0,0,0,1,1,63])

    def test_gen2_shared_special_but_distinct_base_stats(self):
        record = dict(generation=2, dex=1, level=50, dvs=[10]*4, stat_exp=[64]*5)
        values = stats.calculated(record, {'base_stats': {'1': [50,50,50,50,60,80]}})
        self.assertEqual(values[-2:], [76,96])
        self.assertEqual(stats.inherited(record)[-2:], [10,10])
        self.assertEqual(stats.training(record)[-2:], [64,64])

    def test_level_from_experience_and_old_cache_fallback(self):
        record = dict(generation=1, dex=2, level=0, experience=10465)
        self.assertEqual(stats.level_of(record, {'growth_rates': {'2': 3}}), 24)
        self.assertIsNone(stats.calculated(record, {}))
        self.assertIsNone(stats.inherited({'generation': 3, 'ivs': [99]*6}))
        self.assertEqual(stats.chart({'generation': 1}, {}, 1)[3], 15)
        self.assertEqual(len(stats.chart({'generation': 1}, {}, 0)[1]), 5)
        self.assertEqual(len(stats.chart({'generation': 2}, {}, 0)[1]), 6)

    def test_inspector_keeps_details_and_is_read_only(self):
        record = dict(name='TEST', dex=1, species=1, cache='/missing', game='red', level=5,
                      ot='PLAYER', ot_id=1, experience=125, moves=[1,0,0,0], pp=[35,0,0,0],
                      pp_ups=[0]*4, stat_exp=[0]*5, dvs=[1]*4, source_path='/private/save.srm',
                      kind='box', box=0, slot=0, generation=1, hp=20, status=0)
        row = {'metadata': record, 'imported': 0}
        store = Mock(); store.entry.return_value = row; store.history.return_value = []
        ui = Mock(); ui.link = load('butterflyos-save-trade-sdl.py')
        obj = app.Bdex.__new__(app.Bdex)
        obj.store, obj.ui, obj.front, obj.blink = store, ui, ui.frontend, ui.link
        obj.error_types = (OSError, ValueError)
        obj.sprite = Mock(return_value=None)
        obj.front.next_key.side_effect = [ui.link.KEY_RIGHT, ui.link.KEY_DOWN,
                                          ui.link.KEY_RIGHT, ui.link.KEY_DOWN, ui.link.KEY_ESCAPE]
        snapshot = copy.deepcopy(record)
        with patch.object(app.engine, 'cache_info', return_value={}), \
                patch.object(app.inspector_ui, 'draw', return_value=50) as draw:
            obj.inspector(7)
        self.assertEqual([c.args[5] for c in draw.call_args_list], [0,1,1,2,2])
        self.assertIn('Source save: /private/save.srm', draw.call_args.args[7])
        self.assertEqual(record, snapshot)
        store.reconnect_cache.assert_not_called()
        obj.sprite.assert_called_once_with('/missing', 1, False)


if __name__ == '__main__':
    unittest.main()

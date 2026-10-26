#!/usr/bin/env python3
"""Version-specific acquisition rules, missing-species guidance and read-only safety."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import zipfile
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCES / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guide = load('butterflyos-bdex-acquisition')
app = load('butterflyos-bdex-sdl')


class AcquisitionTests(unittest.TestCase):
    def test_every_species_in_every_game_renders_without_cache_or_writes(self):
        before = hashlib.sha256((SOURCES / 'butterflyos-bdex-acquisition.json').read_bytes()).hexdigest()
        for game in guide.TITLES:
            for dex in range(1, guide.LIMITS[guide.GENERATION[game]] + 1):
                with self.subTest(game=game, dex=dex):
                    text = guide.describe(game, dex)
                    self.assertIn('#%03d' % dex, text)
                    self.assertIn('does not create', text)
        self.assertEqual(before, hashlib.sha256((SOURCES / 'butterflyos-bdex-acquisition.json').read_bytes()).hexdigest())

    def test_all_encounter_methods_and_evolution_methods_supported(self):
        for game, data in guide.reference().items():
            limit = guide.LIMITS[guide.GENERATION[game]]
            self.assertGreater(len(data['encounters']), 100)
            self.assertEqual(len(data['evolutions']), {1: 72, 2: 122, 3: 184}[guide.GENERATION[game]])
            for dex, rows in data['encounters'].items():
                self.assertTrue(1 <= int(dex) <= limit)
                for place, method, low, high, condition in rows:
                    self.assertIn(method, guide.METHODS)
                    self.assertTrue(place)
                    self.assertTrue(1 <= low <= high <= 100)

    def test_gen1_trade_evolution_includes_actionable_pre_evolution_sources(self):
        text = guide.describe('red', 65, {63: 'ABRA', 64: 'KADABRA'})
        self.assertIn('#064 KADABRA: trade in-game', text)
        self.assertIn('copies do not trigger evolution', text)
        self.assertIn('#063 ABRA: level up to Lv 16', text)
        self.assertIn('Route', text)
        self.assertIn('FIND THE PRE-EVOLUTION', text)
        self.assertNotIn('BREEDING', text)

    def test_fishing_fossils_npc_trades_and_legendaries(self):
        self.assertIn('Rod', guide.describe('red', 129))
        self.assertIn('Helix Fossil', guide.describe('red', 138))
        self.assertIn('NPC trade', guide.describe('red', 122))
        self.assertIn('Seafoam', guide.describe('blue', 144))
        self.assertIn('historical', guide.describe('red', 151).lower())
        self.assertIn('Other versions', guide.describe('red', 37))
        self.assertIn('Blue', guide.describe('red', 37))
        self.assertIn('Recorded direct sources in other versions: Blue', guide.describe('red', 38))

    def test_yellow_starter_pikachu_exception(self):
        self.assertIn('starter in Yellow refuses', guide.describe('yellow', 26))
        self.assertNotIn('starter in Yellow refuses', guide.describe('red', 26))

    def test_gen2_held_item_and_stat_branches(self):
        for dex, item in ((208, 'Metal Coat'), (199, "King's Rock"), (230, 'Dragon Scale'), (233, 'Up Grade')):
            text = guide.describe('crystal', dex)
            self.assertIn('trade in-game while holding ' + item, text)
        for dex, relation in ((106, '>'), (107, '<'), (237, '=')):
            self.assertIn('Attack %s Defense' % relation, guide.describe('gold', dex))
        self.assertIn('friendship at least 220 at 04:00-17:59', guide.describe('silver', 196))
        self.assertIn('18:00-03:59', guide.describe('gold', 197))

    def test_gen3_clock_beauty_personality_and_shedinja(self):
        self.assertIn('12:00-23:59', guide.describe('emerald', 196))
        self.assertIn('00:00-11:59', guide.describe('ruby', 197))
        for game in ('firered', 'leafgreen'):
            self.assertIn('time-of-day evolution is unavailable', guide.describe(game, 196))
            self.assertIn('Beauty cannot be raised', guide.describe(game, 350))
            self.assertIn('National Pokedex', guide.describe(game, 169))
        self.assertIn('Beauty to at least 170', guide.describe('emerald', 350))
        self.assertIn('does not use a Prism Scale', guide.describe('sapphire', 350))
        self.assertIn('personality', guide.describe('emerald', 266))
        for game in ('ruby', 'sapphire', 'emerald', 'firered', 'leafgreen'):
            text = guide.describe(game, 292)
            self.assertIn('empty party slot', text)
            self.assertNotIn('regular Poke Ball in the bag', text)
            self.assertIn('does not require a spare Poke Ball', text)

    def test_eggs_and_events_are_not_claimed_as_normal_wild_access(self):
        self.assertIn('Sea Incense', guide.describe('ruby', 298))
        self.assertIn('Lax Incense', guide.describe('emerald', 360))
        self.assertIn('Baby Pokemon cannot breed', guide.describe('crystal', 172))
        self.assertIn('not normally enabled', guide.describe('crystal', 251))
        self.assertNotIn('Playing on the Virtual Console', guide.describe('crystal', 251))
        for game in ('firered', 'leafgreen', 'emerald'):
            self.assertIn('AuroraTicket', guide.describe(game, 386))
            self.assertIn('MysticTicket', guide.describe(game, 249))
        self.assertIn('Japanese Emerald', guide.describe('emerald', 151))
        self.assertIn('choose blue', guide.describe('emerald', 381))
        self.assertIn('choose red', guide.describe('emerald', 380))
        self.assertNotIn('Beat the Elite 4 for the second time', guide.describe('firered', 243))

    def test_rom_qualification_uses_content_not_filename(self):
        data = b'qualified-private-fixture'
        reader = Mock(return_value=data)
        allowed = {hashlib.sha256(data).hexdigest(): 'ruby'}
        self.assertEqual(('ruby', data), guide.qualify('not-pokemon.zip', reader, allowed))
        reader.return_value = b'changed'
        with self.assertRaisesRegex(ValueError, 'qualified English'):
            guide.qualify('Emerald.gba', reader, allowed)
        reader.side_effect = zipfile.BadZipFile('invalid archive')
        with self.assertRaisesRegex(ValueError, 'Cannot read'):
            guide.qualify('Emerald.zip', reader, allowed)
        for generation, title in ((1, 'POKEMON RED'), (2, 'PM_CRYSTAL')):
            profile = Mock(SUPPORTED_ROMS={'digest': title})
            self.assertEqual(list(guide.supported_games(generation, profile)), ['digest'])
        profile = Mock(ROM_PROFILES={str(i): ('family', i) for i in range(1, 6)})
        self.assertEqual(guide.supported_games(3, profile), {'1': 'sapphire', '2': 'ruby', '3': 'emerald', '4': 'firered', '5': 'leafgreen'})

    def test_bad_game_and_generation_are_rejected(self):
        for game, dex in (('red', 152), ('gold', 252), ('emerald', 387), ('emerald', 0), ('hack', 25)):
            with self.assertRaises(ValueError):
                guide.describe(game, dex)

    def test_gen1_rom_rows_are_distinguished_from_reference_data(self):
        index = {'species': {'129': [{'min': 9, 'max': 10, 'area': 'Private ROM area', 'method': 'Surfing'}]}}
        text = guide.describe('blue', 129, rom_index=index)
        self.assertIn('Private ROM area | Surfing | Lv 9-10', text)
        self.assertIn('REFERENCE DATA', text)
        self.assertIn('Rod', text)


if __name__ == '__main__':
    unittest.main()

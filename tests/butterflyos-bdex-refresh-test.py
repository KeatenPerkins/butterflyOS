#!/usr/bin/env python3
"""Controller refresh action clears stale sprites and handles cancellation."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

source=Path(__file__).resolve().parents[1]/'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-bdex-sdl.py'
spec=importlib.util.spec_from_file_location('refresh_ui',source)
ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui)

class RefreshTests(unittest.TestCase):
    def app(self, cache):
        app=object.__new__(ui.Bdex)
        app.ui=Mock()
        app.store=Mock()
        app.store.reconnect_cache.return_value=(6,4)
        app.prepare_cache=Mock(return_value=cache)
        app.sprites={'stale-image':None}
        return app

    def test_refresh_repairs_references_and_clears_negative_cache(self):
        app=self.app('/verified/cache')
        app.refresh_sprites()
        app.prepare_cache.assert_called_once_with(force=True)
        app.store.reconnect_cache.assert_called_once_with('/verified/cache')
        self.assertEqual({},app.sprites)
        self.assertIn('6 stored copies',app.ui.message.call_args.args[1])

    def test_cancel_keeps_collection_and_artwork_unchanged(self):
        app=self.app(None)
        app.refresh_sprites()
        app.store.reconnect_cache.assert_not_called()
        self.assertEqual({'stale-image':None},app.sprites)

if __name__=='__main__':unittest.main()

#!/usr/bin/env python3
"""Discovery keeps searching, cancels promptly, and returns available hosts early."""
import importlib.util
import json
from pathlib import Path
import socket
import unittest
from unittest import mock
SOURCE=Path(__file__).resolve().parents[1]/'projects/ROCKNIX/packages/misc/butterflyos-flip-onboarding/sources/butterflyos-bslap.py'
spec=importlib.util.spec_from_file_location('bslap_discovery',SOURCE)
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
class Clock:
    now=0.0
    def monotonic(self):return self.now
class FakeSocket:
    def __init__(self,clock,packets=()):self.clock=clock;self.packets=list(packets);self.broadcasts=0;self.closed=False
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def setsockopt(self,*args):pass
    def settimeout(self,value):self.timeout=value
    def bind(self,*args):pass
    def sendto(self,*args):self.broadcasts+=1
    def recvfrom(self,*args):
        if self.packets and self.clock.now>=self.packets[0][0]:
            when,ip=self.packets.pop(0)
            data=dict(app='Bslap',version=4,backend=app.BACKEND,port=app.PORT,lobby_port=app.LOBBY_PORT,
                      name='Test host',rom_sha='a'*64,game_code='G2CR')
            return json.dumps(data).encode(),(ip,app.DISCOVERY_PORT)
        self.clock.now+=self.timeout
        raise socket.timeout()
class DiscoveryTests(unittest.TestCase):
    def test_default_waits_a_full_minute_and_rebroadcasts(self):
        clock=Clock();sock=FakeSocket(clock);ui=mock.Mock();ui.action.return_value=None
        with mock.patch.object(app.time,'monotonic',side_effect=clock.monotonic),mock.patch.object(app.socket,'socket',return_value=sock):
            self.assertEqual(app.discover(ui=ui),[])
        self.assertGreaterEqual(clock.now,60)
        self.assertLess(clock.now,60.2)
        self.assertGreater(sock.broadcasts,80)
        self.assertTrue(sock.closed)
        self.assertTrue(any('60 seconds remaining' in call.args[1] for call in ui.frontend.draw_message.call_args_list))
        self.assertTrue(all(call.args[2]=='B Cancel' for call in ui.frontend.draw_message.call_args_list))
    def test_b_cancels_without_waiting_or_showing_no_host(self):
        clock=Clock();sock=FakeSocket(clock);ui=mock.Mock()
        ui.action.side_effect=lambda:'back' if clock.now>=1 else None
        with mock.patch.object(app.time,'monotonic',side_effect=clock.monotonic),mock.patch.object(app.socket,'socket',return_value=sock):
            self.assertIsNone(app.discover(ui=ui))
        self.assertLess(clock.now,1.2)
        self.assertTrue(sock.closed)
    def test_found_hosts_show_promptly_with_short_collection_window(self):
        clock=Clock();sock=FakeSocket(clock,[(2,'192.168.1.17'),(2.2,'192.168.1.20')])
        with mock.patch.object(app.time,'monotonic',side_effect=clock.monotonic),mock.patch.object(app.socket,'socket',return_value=sock):
            rooms=app.discover()
        self.assertEqual([r['ip'] for r in rooms],['192.168.1.17','192.168.1.20'])
        self.assertLess(clock.now,3)
if __name__=='__main__':unittest.main()

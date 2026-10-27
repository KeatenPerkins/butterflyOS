#!/usr/bin/env python3
"""Headless native-core load/frames/SRAM/RTC/API smoke test. Never writes saves."""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--core',required=True,type=Path)
parser.add_argument('--rom',required=True,type=Path)
parser.add_argument('--save',type=Path)
args=parser.parse_args()
lib=c.CDLL(str(args.core))
class Variable(c.Structure):_fields_=[('key',c.c_char_p),('value',c.c_char_p)]
class Info(c.Structure):_fields_=[('path',c.c_char_p),('data',c.c_void_p),('size',c.c_size_t),('meta',c.c_char_p)]
ENV=c.CFUNCTYPE(c.c_bool,c.c_uint,c.c_void_p)
VIDEO=c.CFUNCTYPE(None,c.c_void_p,c.c_uint,c.c_uint,c.c_size_t)
AUDIO=c.CFUNCTYPE(None,c.c_int16,c.c_int16)
BATCH=c.CFUNCTYPE(c.c_size_t,c.c_void_p,c.c_size_t)
POLL=c.CFUNCTYPE(None)
INPUT=c.CFUNCTYPE(c.c_int16,c.c_uint,c.c_uint,c.c_uint,c.c_uint)
options={b'gambatte_gb_colorization':b'internal',b'gambatte_gb_internal_palette':b'Special 3',b'gambatte_gb_palette_switching':b'disabled'}
packet_address=None
frames=0
@ENV
def environment(command,data):
    global packet_address
    cmd=command & 0xFFFF
    if cmd==3:
        c.cast(data,c.POINTER(c.c_bool))[0]=True;return True
    if cmd==78: # RETRO_ENVIRONMENT_SET_NETPACKET_INTERFACE (experimental)
        packet_address=data
        return True
    if cmd==15:
        var=c.cast(data,c.POINTER(Variable)).contents
        if var.key in options:var.value=options[var.key];return True
        return False
    if cmd==16:
        values=c.cast(data,c.POINTER(Variable));i=0
        while values[i].key:
            value=values[i].value or b''
            if b'; ' in value:options.setdefault(values[i].key,value.split(b'; ',1)[1].split(b'|')[0])
            i+=1
        return True
    if cmd==17:
        c.cast(data,c.POINTER(c.c_bool))[0]=False;return True
    if cmd in (10,18,35,36):return True
    return False
@VIDEO
def video(data,w,h,pitch):
    global frames
    if data and w and h:frames+=1
@AUDIO
def audio(left,right):pass
@BATCH
def batch(data,size):return size
@POLL
def poll():pass
@INPUT
def input_state(port,device,index,button):return 0
for name,callback in [('environment',environment),('video_refresh',video),('audio_sample',audio),('audio_sample_batch',batch),('input_poll',poll),('input_state',input_state)]:
    fn=getattr(lib,'retro_set_'+name);fn.argtypes=[type(callback)];fn(callback)
lib.retro_init()
# Assert the interface, not merely a version string, is registered.
if not packet_address:raise AssertionError('Netpacket interface not registered')
lib.retro_get_memory_size.argtypes=[c.c_uint];lib.retro_get_memory_size.restype=c.c_size_t
lib.retro_get_memory_data.argtypes=[c.c_uint];lib.retro_get_memory_data.restype=c.c_void_p
lib.retro_load_game.argtypes=[c.POINTER(Info)];lib.retro_load_game.restype=c.c_bool
rom=args.rom.read_bytes();buffer=c.create_string_buffer(rom)
info=Info(str(args.rom).encode(),c.cast(buffer,c.c_void_p),len(rom),None)
assert lib.retro_load_game(c.byref(info))
size=lib.retro_get_memory_size(0)
assert size==32768,size
save_before=None
if args.save:
    save_before=hashlib.sha256(args.save.read_bytes()).hexdigest()
    c.memmove(lib.retro_get_memory_data(0),args.save.read_bytes()[:size],size)
for _ in range(120):lib.retro_run()
assert frames>=100,frames
rtc_size=lib.retro_get_memory_size(1)
lib.retro_unload_game();lib.retro_deinit()
if args.save:assert hashlib.sha256(args.save.read_bytes()).hexdigest()==save_before
print(json.dumps(dict(rom=args.rom.name,frames=frames,sram_bytes=size,rtc_bytes=rtc_size,netpacket=True,save_unchanged=True)))

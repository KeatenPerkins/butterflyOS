#!/usr/bin/env python3
"""Exercise the compiled palette updater; --core checks real libretro registration."""
import ctypes as c
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'build.ROCKNIX-RK3566.aarch64/build/sameboy-lr-2d29ece3b8e7ec44347c9daad0fabb84912ed44f/Core/gb.c'


def check_core(path):
    class Value(c.Structure):
        _fields_ = [('value', c.c_char_p), ('label', c.c_char_p)]
    class Definition(c.Structure):
        _fields_ = [(name, c.c_char_p) for name in ('key', 'desc', 'desc_categorized', 'info', 'info_categorized', 'category_key')]
        _fields_ += [('values', Value * 128), ('default_value', c.c_char_p)]
    class Options(c.Structure):
        _fields_ = [('categories', c.c_void_p), ('definitions', c.POINTER(Definition))]
    class International(c.Structure):
        _fields_ = [('us', c.POINTER(Options)), ('local', c.POINTER(Options))]
    registered = {}
    @c.CFUNCTYPE(c.c_bool, c.c_uint, c.c_void_p)
    def environment(command, data):
        if command == 52:
            c.cast(data, c.POINTER(c.c_uint))[0] = 2
            return True
        if command == 39:
            c.cast(data, c.POINTER(c.c_uint))[0] = 0
            return True
        if command in (67, 68):
            options = (c.cast(data, c.POINTER(International)).contents.us.contents if command == 68
                       else c.cast(data, c.POINTER(Options)).contents)
            index = 0
            while options.definitions[index].key:
                item = options.definitions[index]
                registered[item.key.decode()] = (item.default_value.decode(), [v.value.decode() for v in item.values if v.value])
                index += 1
            return True
        return False
    core = c.CDLL(str(path))
    core.retro_set_environment.argtypes = [type(environment)]
    core.retro_set_environment(environment)
    for key in ('sameboy_mono_palette', 'sameboy_mono_palette_1', 'sameboy_mono_palette_2'):
        assert registered[key] == ('greyscale', ['greyscale', 'lime', 'olive', 'teal', 'special3']), (key, registered.get(key))
    print('PASS: built core exposes Special 3 for both players; ordinary defaults remain greyscale.')


class PaletteTests(unittest.TestCase):
    @unittest.skipUnless(SOURCE.is_file(), 'Requires the unpacked, patched SameBoy build source')
    def test_real_palette_updater_keeps_three_palettes_separate_and_leaves_cgb_untouched(self):
        source = SOURCE.read_text()
        start = source.index('const GB_palette_t GB_PALETTE_SPECIAL3 =')
        end = source.index('const GB_palette_t *GB_get_palette', start)
        actual = source[start:end]
        program = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
typedef struct { struct { uint8_t r,g,b; } colors[5]; } GB_palette_t;
typedef struct GB_gameboy_s GB_gameboy_t;
struct GB_gameboy_s {
    const GB_palette_t *dmg_palette;
    uint32_t (*rgb_encode_callback)(GB_gameboy_t *,uint8_t,uint8_t,uint8_t);
    uint32_t background_palettes_rgb[32], object_palettes_rgb[32];
    bool cgb;
};
static bool GB_is_cgb(GB_gameboy_t *gb) { return gb->cgb; }
const GB_palette_t GB_PALETTE_GREY = {.colors={{0,0,0},{85,85,85},{170,170,170},{255,255,255},{255,255,255}}};
static uint32_t encode(GB_gameboy_t *gb,uint8_t r,uint8_t g,uint8_t b) { (void)gb;return (uint32_t)r<<16 | (uint32_t)g<<8 | b; }
''' + actual + r'''
int main(void) {
    GB_gameboy_t gb={.rgb_encode_callback=encode};
    const uint32_t bg[4]={0xF8F8F8,0xA59E8C,0x49726C,0};
    const uint32_t sprites[8]={0xF8F8F8,0xE49685,0x6E241E,0,0xF8F8F8,0xD7543C,0x7D3023,0};
    GB_set_palette(&gb,&GB_PALETTE_SPECIAL3);
    assert(memcmp(bg,gb.background_palettes_rgb,sizeof(bg))==0);
    assert(memcmp(sprites,gb.object_palettes_rgb,sizeof(sprites))==0);
    assert(gb.background_palettes_rgb[4]==0xF8F8F8);
    GB_set_palette(&gb,&GB_PALETTE_GREY);
    for (int i=0;i<4;i++) {
        assert(gb.object_palettes_rgb[i]==gb.background_palettes_rgb[i]);
        assert(gb.object_palettes_rgb[i+4]==gb.background_palettes_rgb[i]);
    }
    gb.cgb=true;
    uint32_t saved_bg[32],saved_objects[32];
    memcpy(saved_bg,gb.background_palettes_rgb,sizeof(saved_bg));
    memcpy(saved_objects,gb.object_palettes_rgb,sizeof(saved_objects));
    GB_set_palette(&gb,&GB_PALETTE_SPECIAL3);
    assert(memcmp(saved_bg,gb.background_palettes_rgb,sizeof(saved_bg))==0);
    assert(memcmp(saved_objects,gb.object_palettes_rgb,sizeof(saved_objects))==0);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            source_path, binary = Path(directory) / 'palette.c', Path(directory) / 'palette'
            source_path.write_text(program)
            subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(source_path), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--core':
        check_core(sys.argv[2])
    else:
        unittest.main()

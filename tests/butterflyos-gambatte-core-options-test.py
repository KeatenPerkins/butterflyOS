#!/usr/bin/env python3
"""Check actual core option registration. Run on target with the built .so path."""
import ctypes as c
import sys


class Value(c.Structure):
    _fields_ = [('value', c.c_char_p), ('label', c.c_char_p)]


class Definition(c.Structure):
    _fields_ = [(name, c.c_char_p) for name in
                ('key', 'desc', 'desc_categorized', 'info', 'info_categorized', 'category_key')]
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
        options = (c.cast(data, c.POINTER(International)).contents.us.contents
                   if command == 68 else c.cast(data, c.POINTER(Options)).contents)
        index = 0
        while options.definitions[index].key:
            item = options.definitions[index]
            values = []
            for value in item.values:
                if not value.value:
                    break
                values.append(value.value.decode())
            registered[item.key.decode()] = (item.default_value.decode(), values)
            index += 1
        return True
    return False


core = c.CDLL(sys.argv[1])
core.retro_set_environment.argtypes = [type(environment)]
core.retro_set_environment(environment)
assert registered['gambatte_gb_palette_switching'] == ('disabled', ['disabled', 'enabled']), registered
assert 'gambatte_gb_colorization' in registered
assert 'gambatte_gb_internal_palette' in registered
print('PASS: built core registers disabled-by-default L/R cycling and retains colorization/palette options.')

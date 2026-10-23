#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only stat calculations and lightweight SDL inspector drawing.

Array order is HP/Attack/Defense/Speed/Special (Gen 1), or
HP/Attack/Defense/Speed/Sp.Attack/Sp.Defense (Gen 2/3).
Base stats are supplied by the user's qualified ROM cache, never bundled here.
"""
import math

LABELS = ('HP', 'Attack', 'Defense', 'Speed', 'Sp. Atk', 'Sp. Def')


def vector(value, count, maximum):
    if not isinstance(value, (list, tuple)) or len(value) != count:
        return None
    if any(type(v) is not int or not 0 <= v <= maximum for v in value):
        return None
    return list(value)


def inherited(record):
    generation = record.get('generation', 1)
    if generation == 3:
        return vector(record.get('ivs'), 6, 31)
    dvs = vector(record.get('dvs'), 4, 15)
    if dvs is None:
        return None
    attack, defense, speed, special = dvs
    hp = ((attack & 1) << 3) | ((defense & 1) << 2) | ((speed & 1) << 1) | (special & 1)
    return [hp, attack, defense, speed, special] + ([special] if generation == 2 else [])


def training(record):
    generation = record.get('generation', 1)
    if generation == 3:
        return vector(record.get('evs'), 6, 255)
    values = vector(record.get('stat_exp'), 5, 65535)
    return values + ([values[-1]] if generation == 2 else []) if values is not None else None


def threshold(rate, level):
    if rate == 0:
        return level ** 3
    if rate == 3:
        return max(0, 6 * level ** 3 // 5 - 15 * level ** 2 + 100 * level - 140)
    if rate == 4:
        return 4 * level ** 3 // 5
    if rate == 5:
        return 5 * level ** 3 // 4
    return None


def level_of(record, info):
    dex = str(record.get('dex', ''))
    # Gen I's boxed-level byte is not reliably the current level. Derive it
    # from experience and the ROM's growth rate, as the game does on withdrawal.
    rate = info.get('growth_rates', {}).get(dex)
    exp = record.get('experience')
    table = info.get('experience_tables', {}).get(str(rate))
    if type(exp) is int and exp >= 0:
        if isinstance(table, list) and len(table) == 101:
            return max((n for n in range(1, 101) if exp >= table[n]), default=1)
        if record.get('generation', 1) < 3 and threshold(rate, 1) is not None:
            return max((n for n in range(1, 101) if exp >= threshold(rate, n)), default=1)
    level = record.get('level')
    return level if type(level) is int and 1 <= level <= 100 else None


def effort_bonus(value):
    # GB games search for ceil(sqrt(stat_exp)), capped at 255, then divide by 4.
    root = math.isqrt(value)
    if root * root < value:
        root += 1
    return min(255, root) // 4


def calculated(record, info):
    generation = record.get('generation', 1)
    count = 5 if generation == 1 else 6
    base = vector(info.get('base_stats', {}).get(str(record.get('dex'))), count, 255)
    iv, effort, level = inherited(record), training(record), level_of(record, info)
    if base is None or iv is None or effort is None or level is None:
        return None
    result = []
    for index, (b, v, e) in enumerate(zip(base, iv, effort)):
        term = 2 * b + v + e // 4 if generation == 3 else 2 * (b + v) + effort_bonus(e)
        value = term * level // 100 + (level + 10 if index == 0 else 5)
        if generation == 3:
            if index == 0 and record.get('dex') == 292:  # Native Shedinja exception.
                value = 1
            elif index:
                personality = record.get('personality')
                if type(personality) is not int:
                    return None
                nature = personality % 25
                up, down = nature // 5 + 1, nature % 5 + 1
                if up != down:
                    value = value * (11 if index == up else 9 if index == down else 10) // 10
        else:
            value = min(999, value)
        result.append(value)
    return result


def chart(record, info, mode):
    generation = record.get('generation', 1)
    labels = LABELS[:4] + ('Special',) if generation == 1 else LABELS
    if mode == 1:
        maximum = 31 if generation == 3 else 15
        return ('IVs' if generation == 3 else 'DVs', labels, inherited(record), maximum,
                'Scale 0–%d%s' % (maximum, '; HP derived' if generation < 3 else ''))
    if mode == 2:
        maximum = 255 if generation == 3 else 65535
        return ('EVs (training)' if generation == 3 else 'Stat Exp (training)', labels, training(record), maximum,
                'EV total %d / 510; 252 effective/stat' % sum(record.get('evs', [])) if generation == 3
                else 'Training counters; scale 0–65535')
    level = level_of(record, info)
    # One shared ceiling at a given level, based on the 255-byte base-stat
    # limit; do not rescale each Pokemon to make its strongest stat look full.
    ceiling = ((604 if generation == 3 else 603) * level // 100 + level + 10) if level else 1
    return ('Calculated stats', labels, calculated(record, info), ceiling,
            'Scale 0–%d at Lv. %s' % (ceiling, level) if level else 'Level unavailable')


def polygon(front, points, color, filled=False):
    if filled:
        # Tiny convex polygons: bounded scanline fill, no image library or GPU shader.
        for y in range(math.ceil(min(p[1] for p in points)), math.floor(max(p[1] for p in points)) + 1):
            intersections = []
            for a, b in zip(points, points[1:] + points[:1]):
                if min(a[1], b[1]) <= y < max(a[1], b[1]):
                    intersections.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
            if len(intersections) >= 2:
                front.line(round(min(intersections)), y, round(max(intersections)), y, color)
    for a, b in zip(points, points[1:] + points[:1]):
        front.line(round(a[0]), round(a[1]), round(b[0]), round(b[1]), color)


def radar(front, record, info, mode, cx, cy, radius):
    title, labels, values, maximum, note = chart(record, info, mode)
    front.draw_text(title, cx, cy - radius - 67, 17, (36, 226, 224), center=True)
    count = len(labels)
    order = list(range(5)) if count == 5 else [0, 1, 2, 3, 5, 4]
    axes = [(math.sin(2 * math.pi * i / count), -math.cos(2 * math.pi * i / count)) for i in range(count)]
    for fraction in (.25, .5, .75, 1):
        polygon(front, [(cx + x * radius * fraction, cy + y * radius * fraction) for x, y in axes], (36, 65, 98))
    for x, y in axes:
        front.line(cx, cy, round(cx + x * radius), round(cy + y * radius), (48, 83, 119))
    if values is not None:
        points = [(cx + x * radius * min(1, max(0, values[index] / maximum)),
                   cy + y * radius * min(1, max(0, values[index] / maximum))) for (x, y), index in zip(axes, order)]
        polygon(front, points, (43, 112, 131), filled=True)
        polygon(front, points, (68, 235, 210))
    for (x, y), index in zip(axes, order):
        lx, ly = round(cx + x * (radius + 30)), round(cy + y * (radius + 30))
        front.draw_text(labels[index], lx, ly - 12, 12, (186, 207, 228), center=True)
        front.draw_text(str(values[index]) if values is not None else '—', lx, ly + 4, 14, (255, 255, 255), center=True)
    if values is None:
        front.draw_text('ROM stat data needed' if mode == 0 else 'Data unavailable', cx, cy - 7, 12, (255, 188, 96), center=True)
    front.draw_text(note, cx, 401, 10, (153, 187, 220), center=True)
    return values


def sprite(front, image, cx, cy, size=106):
    front.fill(cx - size // 2, cy - size // 2, size, size, (216, 220, 226))
    if not image:
        front.draw_text('No sprite', cx, cy - 6, 12, (32, 48, 70), center=True)
        return
    width, height, pixels = image
    scale = max(1, min(2, (size - 8) // max(width, height)))
    left, top = cx - width * scale // 2, cy - height * scale // 2
    for y in range(height):
        for x in range(width):
            r, g, b, alpha = pixels[(y * width + x) * 4:(y * width + x) * 4 + 4]
            if alpha:
                front.fill(left + x * scale, top + y * scale, scale, scale, (r, g, b))


def draw(front, record, info, image, ident, page, mode, details, offset=0):
    front.refresh_text_scale()
    front.sdl.SDL_SetRenderDrawColor(front.renderer, 6, 9, 22, 255)
    front.sdl.SDL_RenderClear(front.renderer)
    front.outline(10, 10, 620, 460, (38, 129, 190), 3)
    front.draw_text(record['name'], 30, 23, 24, (36, 226, 224), bold=True)
    front.draw_text('#%03d  GEN %d  COPY #%d' % (record['dex'], record.get('generation', 1), ident), 348, 31, 13, (173, 197, 220))
    for i, title in enumerate(('Summary', 'Stats', 'Details')):
        x = 27 + i * 197
        front.fill(x, 66, 191, 32, (24, 83, 153) if i == page else (14, 30, 67))
        front.draw_text(title, x + 95, 73, 15, (255, 255, 255), center=True)
    maximum = 0
    if page == 2:
        lines = []
        for text in details:
            lines.extend(front.wrap_text(text, 15, 556))
        capacity = 13
        maximum = max(0, len(lines) - capacity)
        offset = min(maximum, max(0, offset))
        front.outline(24, 108, 592, 306, (35, 88, 160), 2)
        for i, text in enumerate(lines[offset:offset + capacity]):
            front.draw_text(text, 37, 118 + i * 22, 15, (222, 231, 242))
    else:
        front.outline(24, 108, 282, 306, (35, 88, 160), 2)
        front.outline(316, 108, 300, 306, (35, 88, 160), 2)
        radar(front, record, info, mode, 466, 267, 74)
        if page == 0:
            level = level_of(record, info)
            species = info.get('names', {}).get(str(record['dex']), '')
            source = (species + ' / ' if species and species != record['name'] else 'From ') + record['game'].title()
            front.draw_text(source, 36, 118, 13, (220, 231, 242))
            front.draw_text('Lv. %s   EXP %d' % (level or '?', record['experience']), 36, 141, 13, (173, 197, 220))
            sprite(front, image, 92, 215)
            for i, text in enumerate(front.wrap_text('OT: ' + record['ot'], 12, 130)[:2]):
                front.draw_text(text, 157, 172 + i * 17, 12, (220, 231, 242))
            if record.get('generation', 1) > 1:
                item = record.get('held_item', 0)
                held = info.get('items', {}).get(str(item), 'Item #%d' % item) if item else 'None'
                for i, text in enumerate(front.wrap_text('Held: ' + held, 12, 130)[:3]):
                    front.draw_text(text, 157, 209 + i * 16, 12, (220, 231, 242))
                flags = ('Shiny ' if record.get('shiny') else '') + ('Egg' if record.get('egg') else record.get('gender', ''))
                front.draw_text(flags, 36, 276, 12, (255, 215, 110))
            front.draw_text('MOVES', 36, 297, 13, (36, 226, 224))
            for i, move in enumerate(record['moves']):
                label = info.get('moves', {}).get(str(move), 'Move #%d' % move) if move else '—'
                front.draw_text('%s  %s' % (label, ('PP %d' % record['pp'][i]) if move else ''), 36, 321 + i * 20, 12, (222, 231, 242))
        else:
            title, labels, values, max_value, note = chart(record, info, mode)
            front.draw_text(title, 37, 121, 18, (36, 226, 224))
            for i, label in enumerate(labels):
                front.draw_text(label, 38, 163 + i * 29, 14, (186, 207, 228))
                front.draw_text(str(values[i]) if values is not None else '—', 235, 163 + i * 29, 14, (255, 255, 255), center=True)
            text = ('Training counters, not battle stats.' if mode == 2 else
                    'Special DV/training is shared.' if record.get('generation') == 2 else
                    'Gen 1 uses one Special stat.' if record.get('generation', 1) == 1 else
                    'Stats include level and nature.')
            for i, line in enumerate(front.wrap_text(text, 11, 250)):
                front.draw_text(line, 38, 356 + i * 16, 11, (153, 187, 220))
    front.draw_text('L/R or LEFT/RIGHT Pages   UP/DOWN ' + ('Scroll' if page == 2 else 'Graph mode'), 320, 430, 12, (153, 187, 220), center=True)
    footer = ('A / B Back' if page == 2 else
              'A Refresh ROM data   B Back' if not info.get('base_stats') else 'A Next graph mode   B Back')
    front.draw_text(footer, 320, 448, 12, (153, 187, 220), center=True)
    front.sdl.SDL_RenderPresent(front.renderer)
    return maximum

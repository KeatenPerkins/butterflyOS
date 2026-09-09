-- SPDX-License-Identifier: GPL-2.0-or-later
-- ButterflyOS compact now-playing overlay for MPV.

local mp = require "mp"
local assdraw = require "mp.assdraw"

local overlay = mp.create_osd_overlay("ass-events")

local function ass_escape(value)
    return (value or ""):gsub("\\", "\\e"):gsub("{", "\\{"):gsub("}", "\\}"):gsub("\n", " ")
end

local function clock(seconds)
    seconds = math.max(0, math.floor(tonumber(seconds) or 0))
    return string.format("%d:%02d", math.floor(seconds / 60), seconds % 60)
end

local function rectangle(ass, x1, y1, x2, y2, color, alpha)
    ass:new_event()
    ass:append(string.format("{\\bord0\\1c&H%s&\\1a&H%s&}", color, alpha))
    ass:draw_start()
    ass:rect_cw(x1, y1, x2, y2)
    ass:draw_stop()
end

local function render()
    local width, height = mp.get_osd_size()
    if width < 1 or height < 1 then return end

    local title = ass_escape(mp.get_property("media-title", "Unknown track"))
    local artist = ass_escape(mp.get_property("metadata/by-key/Artist", ""))
    local album = ass_escape(mp.get_property("metadata/by-key/Album", ""))
    local position = mp.get_property_number("time-pos", 0)
    local duration = mp.get_property_number("duration", 0)
    local paused = mp.get_property_bool("pause", false)
    local ratio = duration > 0 and math.min(1, position / duration) or 0

    local left, right = width * 0.075, width * 0.925
    local top, bottom = height * 0.655, height * 0.94
    local bar_left, bar_right = width * 0.12, width * 0.88
    local bar_top, bar_bottom = height * 0.845, height * 0.865
    local ass = assdraw.ass_new()

    rectangle(ass, left, top, right, bottom, "160D08", "18")
    rectangle(ass, left, top, left + width * 0.008, bottom, "FFD910", "00")
    rectangle(ass, bar_left, bar_top, bar_right, bar_bottom, "493020", "20")
    rectangle(ass, bar_left, bar_top, bar_left + (bar_right - bar_left) * ratio, bar_bottom, "FF9D15", "00")

    ass:new_event()
    ass:append(string.format("{\\an7\\pos(%.0f,%.0f)\\fnLiberation Sans\\fs%.0f\\b1\\c&HFFFFFF&\\bord1\\3c&H120A08&}%s",
        width * 0.12, height * 0.69, height * 0.055, title))

    local details = artist
    if album ~= "" then details = details ~= "" and (details .. "  /  " .. album) or album end
    if details ~= "" then
        ass:new_event()
        ass:append(string.format("{\\an7\\pos(%.0f,%.0f)\\fnLiberation Sans\\fs%.0f\\c&HD6E7F4&}%s",
            width * 0.12, height * 0.765, height * 0.034, details))
    end

    ass:new_event()
    ass:append(string.format("{\\an4\\pos(%.0f,%.0f)\\fnLiberation Sans\\fs%.0f\\b1\\c&HFF9D15&}%s",
        width * 0.12, height * 0.905, height * 0.032, paused and "PAUSED" or "PLAYING"))
    ass:new_event()
    ass:append(string.format("{\\an6\\pos(%.0f,%.0f)\\fnLiberation Sans\\fs%.0f\\c&HFFFFFF&}%s  /  %s",
        width * 0.88, height * 0.905, height * 0.032, clock(position), clock(duration)))

    overlay.res_x = width
    overlay.res_y = height
    overlay.data = ass.text
    overlay:update()
end

mp.observe_property("time-pos", "number", render)
mp.observe_property("pause", "bool", render)
mp.observe_property("media-title", "string", render)
mp.observe_property("metadata", "native", render)
mp.register_event("file-loaded", render)

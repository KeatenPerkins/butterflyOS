#!/usr/bin/env python3
"""Local, no-device preview for the Butterfly Link terminal UI.

This deliberately previews layout and colors only.  It never reads or writes
ROMs/saves and does not call the device-side save-trade binary.
Controls: Up/Down, A or Enter to select, B/Esc to go back, Q to quit.
"""

from __future__ import annotations

import curses
import textwrap


CYAN = 1
BLUE = 2
SELECTED = 3
WHITE = 4
MUTED = 5


MAIN_ITEMS = [
    ("local", "Local transfer"),
    ("remote", "Another ButterflyOS device"),
    ("inspect", "Inspect a save  -  read-only"),
    ("prepare", "Resume prepared transfer"),
    ("commit", "Commit prepared transfer"),
    ("discard", "Discard prepared transfer"),
    ("about", "How Butterfly Link works"),
    ("close", "Back to Tools"),
]

PAGES = {
    "local": (
        "LOCAL TRANSFER",
        "Choose a generation.  A Select   B Back",
        [("gen1", "Generation 1  -  Red / Blue / Yellow"),
         ("gen2", "Generation 2  -  Gold / Silver / Crystal"),
         ("gen3", "Generation 3  -  Ruby / Sapphire / Emerald / FRLG")],
    ),
    "gen3": (
        "GENERATION 3",
        "Choose how to move a Pokemon.  A Select   B Back",
        [("swap", "Trade / Swap  -  exchange two Pokemon"),
         ("copy", "Copy  -  leave the source unchanged")],
    ),
    "copy": (
        "LOCAL COPY  -  GENERATION 3",
        "Choose the source save and Pokemon first.  A Select   B Back",
        [("ruby", "OS Card  |  Ruby  |  ZZZ  |  PC: 3"),
         ("emerald", "Game Card  |  Emerald  |  KEATEN  |  PC: 5"),
         ("back", "Back")],
    ),
    "inspect": (
        "INSPECT A SAVE  -  READ ONLY",
        "Choose a save.  Trainer, game, card, and boxed count are shown.",
        [("ruby", "OS Card  |  Ruby  |  ZZZ  |  PC: 3"),
         ("emerald", "Game Card  |  Emerald  |  KEATEN  |  PC: 5"),
         ("back", "Back")],
    ),
    "prepare": (
        "RESUME PREPARED TRANSFER",
        "Protected working copies are ready.  A Select   B Back",
        [("commit", "Commit prepared transfer"),
         ("discard", "Discard prepared transfer"),
         ("back", "Back")],
    ),
    "about": (
        "HOW BUTTERFLY LINK WORKS",
        "A Select   B Back",
        [("back", "Back")],
    ),
}


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(SELECTED, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(MUTED, curses.COLOR_CYAN, curses.COLOR_BLACK)


def put(stdscr, y: int, x: int, text: str, attr: int = 0, max_width: int | None = None) -> None:
    if y < 0 or y >= stdscr.getmaxyx()[0] or x >= stdscr.getmaxyx()[1]:
        return
    if max_width is not None:
        text = text[:max_width]
    try:
        stdscr.addstr(y, max(0, x), text, attr)
    except curses.error:
        pass


def draw_frame(stdscr, title: str, prompt: str, items: list[tuple[str, str]], selected: int) -> None:
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    stdscr.bkgd(" ", curses.color_pair(WHITE))

    left, top = 1, 1
    right, bottom = max(left + 10, width - 2), max(top + 10, height - 2)
    stdscr.attron(curses.color_pair(BLUE))
    stdscr.border()
    stdscr.attroff(curses.color_pair(BLUE))

    title_x = max(2, (width - len(title)) // 2)
    put(stdscr, top, title_x, title, curses.color_pair(CYAN) | curses.A_BOLD)
    put(stdscr, top + 2, left + 2, prompt, curses.color_pair(MUTED), width - 6)

    menu_top = top + 4
    menu_bottom = bottom - 3
    menu_left, menu_right = left + 2, right - 2
    stdscr.attron(curses.color_pair(BLUE))
    for x in range(menu_left, menu_right + 1):
        put(stdscr, menu_top - 1, x, "-")
        put(stdscr, menu_bottom + 1, x, "-")
    put(stdscr, menu_top - 1, menu_left, "+")
    put(stdscr, menu_top - 1, menu_right, "+")
    put(stdscr, menu_bottom + 1, menu_left, "+")
    put(stdscr, menu_bottom + 1, menu_right, "+")
    stdscr.attroff(curses.color_pair(BLUE))

    visible = max(1, menu_bottom - menu_top + 1)
    start = min(max(0, selected - visible + 1), max(0, len(items) - visible))
    for row, (key, label) in enumerate(items[start : start + visible]):
        index = start + row
        y = menu_top + row
        active = index == selected
        attr = curses.color_pair(SELECTED) | curses.A_BOLD if active else curses.color_pair(WHITE)
        put(stdscr, y, menu_left + 1, " " * max(1, menu_right - menu_left - 1), attr)
        put(stdscr, y, menu_left + 2, f"{key:<9}", attr, max_width=10)
        put(stdscr, y, menu_left + 12, label, attr, max_width=max(1, menu_right - menu_left - 14))

    footer = "UP/DOWN Navigate    A / ENTER Select    B / ESC Back    Q Quit"
    put(stdscr, bottom - 1, max(2, (width - len(footer)) // 2), footer, curses.color_pair(MUTED), width - 4)
    stdscr.refresh()


def page(stdscr, page_name: str) -> str:
    title, prompt, items = PAGES[page_name]
    selected = 0
    while True:
        draw_frame(stdscr, title, prompt, items, selected)
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            selected = (selected - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(items)
        elif key in (27, ord("b"), ord("B")):
            return "back"
        elif key in (ord("q"), ord("Q")):
            return "quit"
        elif key in (curses.KEY_ENTER, 10, 13, ord("a"), ord("A")):
            choice = items[selected][0]
            if choice == "back":
                return "back"
            if page_name == "main" and choice == "close":
                return "back"
            if choice in ("gen1", "gen2"):
                show_message(stdscr, "This preview keeps the current Gen III transfer engine boundary.")
            elif choice == "gen3":
                result = page(stdscr, "gen3")
                if result == "quit":
                    return result
            elif choice in PAGES:
                result = page(stdscr, choice)
                if result == "quit":
                    return result
            else:
                show_message(stdscr, "Preview only: no save files were changed.")


def show_message(stdscr, text: str) -> None:
    height, width = stdscr.getmaxyx()
    lines = []
    for paragraph in text.splitlines() or [""]:
        lines.extend(textwrap.wrap(paragraph, max(10, width - 12)) or [""])
    title = "BUTTERFLY LINK"
    draw_frame(stdscr, title, "A / ENTER Continue    B / ESC Back", [("OK", " ")], 0)
    start = max(4, (height - len(lines)) // 2)
    for offset, line in enumerate(lines[: max(1, height - 8)]):
        put(stdscr, start + offset, max(3, (width - len(line)) // 2), line, curses.color_pair(WHITE), width - 6)
    stdscr.refresh()
    while stdscr.getch() not in (curses.KEY_ENTER, 10, 13, 27, ord("a"), ord("A"), ord("b"), ord("B")):
        pass


def run(stdscr) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()
    page(stdscr, "local") if False else None
    while True:
        result = page(stdscr, "main") if "main" in PAGES else None
        if result in ("quit", "back"):
            return


if __name__ == "__main__":
    # Add the main page after constants are defined so it stays easy to edit.
    PAGES["main"] = ("BUTTERFLY LINK", "Choose an action.  A Select   B Back", MAIN_ITEMS)
    curses.wrapper(run)

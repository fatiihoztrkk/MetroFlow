"""Terminal output mode for metro display."""
import re
import shutil
import time

from . import app, config
from .db import get_connection


def _format_time(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _clear():
    print("\x1b[2J\x1b[H", end="")


def _terminal_width() -> int:
    if config.TERMINAL_WIDTH and config.TERMINAL_WIDTH > 0:
        return max(config.TERMINAL_WIDTH, 60)
    cols = shutil.get_terminal_size((100, 24)).columns
    return max(min(cols, 120), 60)


def _trim(text: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    return text[: max_len - 3] + "..."


def _frame_row(text: str, width: int) -> str:
    inner = width - 4
    content = _trim(text, inner)
    chars = _frame_chars()
    return f"{chars['v']} {content:<{inner}} {chars['v']}"


def _frame_center(text: str, width: int) -> str:
    inner = width - 2
    content = _trim(text, inner)
    chars = _frame_chars()
    return f"{chars['v']}{content:^{inner}}{chars['v']}"


def _frame_chars():
    if config.TERMINAL_USE_UNICODE:
        return {
            "h": "─",
            "v": "│",
            "tl": "┌",
            "tr": "┐",
            "bl": "└",
            "br": "┘",
            "ml": "├",
            "mr": "┤",
        }
    return {
        "h": "=",
        "v": "|",
        "tl": "+",
        "tr": "+",
        "bl": "+",
        "br": "+",
        "ml": "|",
        "mr": "|",
    }


def _box_top(width: int) -> str:
    chars = _frame_chars()
    return f"{chars['tl']}{chars['h'] * (width - 2)}{chars['tr']}"


def _box_bottom(width: int) -> str:
    chars = _frame_chars()
    return f"{chars['bl']}{chars['h'] * (width - 2)}{chars['br']}"


def _box_separator(width: int) -> str:
    chars = _frame_chars()
    return f"{chars['ml']}{chars['h'] * (width - 2)}{chars['mr']}"


def _section_header(text: str, width: int) -> str:
    chars = _frame_chars()
    inner = width - 2
    title = f" {text} "
    fill_char = chars["h"] if config.TERMINAL_USE_UNICODE else "-"
    content = _trim(title, inner)
    if len(content) < inner:
        total = inner - len(content)
        left = total // 2
        right = total - left
        content = f"{fill_char * left}{content}{fill_char * right}"
    return f"{chars['v']}{content}{chars['v']}"


def _format_departure_chip(dep: str) -> str:
    if not dep:
        return "[ -- ]"

    if dep.lower().startswith("yarın"):
        parts = dep.split()
        time_part = parts[-1] if parts else "--:--"
        return f"[ YARIN {time_part} ]"

    match = re.match(r"^\s*(\d+)\s+dk\s+(\d{2}:\d{2})\s*$", dep, flags=re.IGNORECASE)
    if not match:
        return f"[ {dep} ]"

    minutes = int(match.group(1))
    hhmm = match.group(2)
    if minutes == 0:
        return f"[ HEMEN {hhmm} ]"
    return f"[ {minutes:>2} dk {hhmm} ]"


def _format_departures_row(departures) -> str:
    if not departures:
        return "[ -- ]"
    chips = [_format_departure_chip(dep) for dep in departures]
    return " ".join(chips)


def _print_model(model) -> None:
    width = _terminal_width()
    section_separator = _box_separator(width)

    _clear()
    print(_box_top(width))
    print(_frame_center(model.title, width))
    print(section_separator)
    print(_frame_row(f"Updated: {_format_time(model.updated_at)} | Refresh: {config.REFRESH_SECONDS}s", width))
    if model.note:
        print(_frame_row(model.note, width))
    print(section_separator)

    for idx, line in enumerate(model.lines):
        print(_section_header(line.name, width))
        for direction in line.directions:
            departures = _format_departures_row(direction.departures)
            label = f"{direction.label:<{config.TERMINAL_LABEL_WIDTH}}"
            print(_frame_row(f"{label} {departures}", width))
        if config.TERMINAL_SECTION_PADDING and idx < len(model.lines) - 1:
            print(_frame_row("", width))
        if idx < len(model.lines) - 1:
            print(section_separator)

    if model.footer_lines:
        print(section_separator)
        print(_section_header("RAMAZAN", width))
        for footer_line in model.footer_lines:
            print(_frame_row(footer_line, width))
    print(_box_bottom(width))


def main() -> None:
    app._ensure_db()
    while True:
        with get_connection() as conn:
            model = app._build_model(conn)
        _print_model(model)
        time.sleep(config.REFRESH_SECONDS)


if __name__ == "__main__":
    main()

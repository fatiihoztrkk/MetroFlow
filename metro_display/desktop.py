"""Desktop dashboard UI (1024x600) with station-sign look."""
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import tkinter as tk
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "tkinter bulunamadi. macOS (Homebrew Python) icin once su komutu calistir:\n"
        "  brew install python-tk@3.11\n"
        "Sonra proje icinde .venv ile calistir:\n"
        "  source .venv/bin/activate\n"
        "  python -m metro_display.desktop"
    ) from exc

from . import app, config
from .db import get_connection
from .render.draw import LineBlock, ScreenModel

BG_TOP = "#1d2533"
BG_BOTTOM = "#0b1220"
SHELL_OUTER = "#090d15"
SHELL_INNER = "#121a28"
PANEL_FILL = "#182235"
PANEL_BORDER = "#43516c"
PANEL_DIVIDER = "#2c3850"

TEXT_MAIN = "#f7fbff"
TEXT_MUTED = "#aab6cb"
TEXT_SOFT = "#7f8aa2"
CYAN = "#3fe2ff"
MAGENTA = "#ff5de2"
GREEN = "#66ffac"

RAM_BG = "#122013"
RAM_BORDER = "#2f6c46"
RAM_TITLE = "#def9e5"
RAM_TEXT = "#f0fff3"
RAM_ACCENT = "#ffd35a"


def _safe_text(value: str) -> str:
    return value or ""


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    raw = value.lstrip("#")
    if len(raw) != 6:
        return (0, 0, 0)
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _blend_color(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex(
        (
            int(ar + (br - ar) * t),
            int(ag + (bg - ag) * t),
            int(ab + (bb - ab) * t),
        )
    )


def _parse_departure(dep: str) -> Dict[str, object]:
    dep = (dep or "").strip()
    out: Dict[str, object] = {
        "minutes": None,
        "time": "",
        "next_day": False,
    }
    if not dep or dep == "--":
        return out

    if dep.lower().startswith("yarın"):
        match = re.search(r"(\d{2}:\d{2})", dep)
        out["minutes"] = 24 * 60
        out["time"] = match.group(1) if match else ""
        out["next_day"] = True
        return out

    match = re.match(r"^\s*(\d+)\s+dk\s+(\d{2}:\d{2})\s*$", dep, re.I)
    if match:
        out["minutes"] = int(match.group(1))
        out["time"] = match.group(2)
        return out

    match = re.search(r"(\d{2}:\d{2})", dep)
    if match:
        out["time"] = match.group(1)
    return out


def _departure_label(dep: str) -> str:
    info = _parse_departure(dep)
    minutes = info["minutes"]
    time_str = str(info["time"] or "")
    next_day = bool(info["next_day"])

    if next_day:
        if time_str:
            return time_str
        return "--"
    if minutes is None:
        return "--"

    threshold = getattr(config, "DESKTOP_SHOW_TIME_AFTER_MINUTES", 30)
    if int(minutes) > int(threshold) and time_str:
        return time_str
    return str(int(minutes))


def _line_theme(line_name: str) -> Tuple[str, str]:
    norm = line_name.lower()
    if "marmaray" in norm:
        return (CYAN, CYAN)
    if norm == "m4" or "m4" in norm:
        return (MAGENTA, MAGENTA)
    return ("#7edfff", "#f5cf58")


def _line_title(line_name: str) -> str:
    norm = line_name.lower()
    if "marmaray" in norm:
        return "MARMARAY 🚉"
    if norm == "m4" or "m4" in norm:
        return "M4 METRO LINE 🚇"
    return f"{line_name.upper()} 🚇"


def _line_rows(line: LineBlock) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for direction in line.directions:
        raw_deps = direction.departures if direction.departures else ["--"]
        dep_infos = [_parse_departure(dep) for dep in raw_deps[:2]]
        cells = [_departure_label(dep) for dep in raw_deps[:2]]
        next_day_flags = [bool(info.get("next_day")) for info in dep_infos]
        while len(cells) < 2:
            cells.append("--")
            next_day_flags.append(False)

        first = _parse_departure(raw_deps[0]) if raw_deps else _parse_departure("--")
        rows.append(
            {
                "dest": _safe_text(direction.label),
                "cells": cells,
                "next_day_flags": next_day_flags,
                "first_minutes": first["minutes"],
                "first_next_day": first["next_day"],
            }
        )
    return rows


def _minute_color(label: str, minute_base: str, is_next_day: bool = False) -> str:
    if is_next_day:
        return CYAN
    if label == "--":
        return TEXT_SOFT
    if re.fullmatch(r"\d{2}:\d{2}", label):
        return TEXT_MUTED
    try:
        minute = int(label)
    except ValueError:
        return TEXT_MAIN
    if minute == 0:
        return GREEN
    if minute <= 2:
        return GREEN
    return minute_base


def _row_indicator_color(row: Dict[str, object], accent: str) -> str:
    if bool(row.get("first_next_day")):
        return CYAN
    minutes = row.get("first_minutes")
    if minutes is None:
        return TEXT_SOFT
    try:
        minute = int(minutes)
    except Exception:  # noqa: BLE001
        return TEXT_SOFT
    if minute <= 2:
        return GREEN
    if minute <= 10:
        return accent
    if minute <= int(getattr(config, "DESKTOP_SHOW_TIME_AFTER_MINUTES", 30)):
        return _blend_color(accent, TEXT_MAIN, 0.35)
    return TEXT_SOFT


def _parse_ramadan(footer_lines: List[str]) -> Dict[str, str]:
    out = {
        "title": "Ramazan - Istanbul",
        "imsak_time": "--:--",
        "imsak_left": "--",
        "iftar_time": "--:--",
        "iftar_left": "--",
    }
    if footer_lines:
        out["title"] = footer_lines[0]
    if len(footer_lines) >= 2:
        match = re.search(
            r"Imsak\s+(\d{2}:\d{2})\s+\(([^)]+)\)\s+\|\s+Iftar\s+(\d{2}:\d{2})\s+\(([^)]+)\)",
            footer_lines[1],
            re.I,
        )
        if match:
            out["imsak_time"] = match.group(1)
            out["imsak_left"] = match.group(2)
            out["iftar_time"] = match.group(3)
            out["iftar_left"] = match.group(4)
    return out


class DesktopBoard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AyrilikPano")
        self.root.configure(bg=config.DESKTOP_BG_COLOR)
        self.root.geometry(f"{config.DESKTOP_WIDTH}x{config.DESKTOP_HEIGHT}")
        self.root.minsize(960, 540)
        self.root.bind("<Escape>", lambda _e: self.root.destroy())
        self.root.bind("q", lambda _e: self.root.destroy())
        self.root.bind("<F11>", self._toggle_fullscreen)

        if config.DESKTOP_FULLSCREEN:
            try:
                self.root.attributes("-fullscreen", True)
            except tk.TclError:
                pass

        self.canvas = tk.Canvas(self.root, bg=config.DESKTOP_BG_COLOR, highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

        self.model = ScreenModel(
            title=config.STATION_NAME.upper(),
            updated_at=datetime.now(),
            lines=[],
            note="Yukleniyor...",
            footer_lines=[],
        )

    def _toggle_fullscreen(self, _event=None):
        current = bool(self.root.attributes("-fullscreen"))
        self.root.attributes("-fullscreen", not current)

    def _font(self, size: int, weight: str = "normal"):
        return (config.DESKTOP_FONT_FAMILY, size, weight)

    def _on_resize(self, _event):
        self._draw()

    def _draw_background(self, width: int, height: int):
        for y in range(height):
            color = _blend_color(BG_TOP, BG_BOTTOM, y / float(max(1, height - 1)))
            self.canvas.create_line(0, y, width, y, fill=color)

    def _draw_shell(self, width: int, height: int) -> Tuple[int, int, int, int]:
        margin = 26
        self.canvas.create_rectangle(
            margin,
            margin,
            width - margin,
            height - margin,
            fill=SHELL_OUTER,
            outline="#2b313d",
            width=2,
        )

        inset = margin + 12
        self.canvas.create_rectangle(
            inset,
            inset,
            width - inset,
            height - inset,
            fill=SHELL_INNER,
            outline="#556078",
            width=1,
        )

        self.canvas.create_polygon(
            width - inset - 240,
            inset + 20,
            width - inset - 40,
            inset + 20,
            width - inset - 90,
            height - inset - 20,
            width - inset - 300,
            height - inset - 20,
            fill="#253045",
            outline="",
            smooth=True,
        )
        self.canvas.create_polygon(
            inset + 50,
            inset + 10,
            inset + 320,
            inset + 10,
            inset + 190,
            height - inset - 10,
            inset - 20,
            height - inset - 10,
            fill="#2a3244",
            outline="",
            smooth=True,
        )
        self.canvas.create_line(inset + 8, inset + 8, width - inset - 8, inset + 8, fill="#7f8ea8", width=1)
        return (inset + 12, inset + 10, width - inset - 12, height - inset - 10)

    def _draw_header(self, x0: int, y0: int, x1: int) -> int:
        self.canvas.create_text(
            x0 + 8,
            y0 + 26,
            anchor="w",
            text=self.model.title,
            fill=TEXT_SOFT,
            font=self._font(15, "bold"),
        )
        clock = self.model.updated_at.strftime("%H:%M")
        self.canvas.create_text(
            x1 - 6,
            y0 + 30,
            anchor="e",
            text=clock,
            fill="#0f1118",
            font=self._font(42, "bold"),
        )
        self.canvas.create_text(
            x1 - 8,
            y0 + 28,
            anchor="e",
            text=clock,
            fill=TEXT_MAIN,
            font=self._font(42, "bold"),
        )
        return y0 + 58

    def _draw_line_panel(self, x0: int, y0: int, x1: int, h: int, line: LineBlock):
        accent, minute_base = _line_theme(line.name)
        rows = _line_rows(line)
        panel_w = x1 - x0
        y1 = y0 + h

        self.canvas.create_rectangle(x0 + 3, y0 + 4, x1 + 3, y1 + 4, fill="#121722", outline="", width=0)
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=PANEL_FILL, outline=PANEL_BORDER, width=1)
        left_w = int(panel_w * 0.62)
        left_x1 = x0 + left_w

        self.canvas.create_text(
            x0 + 18,
            y0 + 30,
            anchor="w",
            text=_line_title(line.name),
            fill=TEXT_MAIN,
            font=self._font(33 if "m4" not in line.name.lower() else 30, "bold"),
        )

        self.canvas.create_text(
            x0 + 20,
            y0 + 62,
            anchor="w",
            text="DESTINATION",
            fill=TEXT_MUTED,
            font=self._font(16, "bold"),
        )
        self.canvas.create_line(x0 + 16, y0 + 74, left_x1 - 16, y0 + 74, fill=PANEL_DIVIDER, width=1)
        self.canvas.create_line(left_x1, y0 + 14, left_x1, y1 - 14, fill=PANEL_DIVIDER, width=1)

        right_w = panel_w - left_w
        right_x0 = left_x1
        self.canvas.create_text(
            right_x0 + right_w / 2,
            y0 + 62,
            anchor="center",
            text="MINUTES AWAY",
            fill=minute_base,
            font=self._font(16, "bold"),
        )
        self.canvas.create_line(right_x0 + 16, y0 + 74, x1 - 16, y0 + 74, fill=PANEL_DIVIDER, width=1)

        row_top = y0 + 98
        row_bottom = y1 - 18
        count = max(1, len(rows))
        row_step = (row_bottom - row_top) / float(count)

        col1 = int(right_x0 + right_w * 0.35)
        col2 = int(right_x0 + right_w * 0.75)

        for idx, row in enumerate(rows):
            y_mid = int(row_top + idx * row_step + row_step * 0.5)
            dest = str(row["dest"])
            dest_color = accent if idx == 0 else TEXT_MAIN

            indicator = _row_indicator_color(row, accent)
            self.canvas.create_oval(x0 + 18, y_mid - 8, x0 + 34, y_mid + 8, outline=indicator, fill="", width=1)
            self.canvas.create_oval(x0 + 22, y_mid - 4, x0 + 30, y_mid + 4, outline="", fill=indicator)

            self.canvas.create_text(
                x0 + 40,
                y_mid,
                anchor="w",
                text=dest,
                fill=dest_color,
                font=self._font(34, "normal"),
            )

            mins: List[str] = row["cells"]  # type: ignore[assignment]
            next_day_flags: List[bool] = row.get("next_day_flags", [False, False])  # type: ignore[assignment]
            m1 = mins[0] if len(mins) > 0 else "--"
            m2 = mins[1] if len(mins) > 1 else "--"
            f1 = bool(next_day_flags[0]) if len(next_day_flags) > 0 else False
            f2 = bool(next_day_flags[1]) if len(next_day_flags) > 1 else False

            self.canvas.create_text(
                col1,
                y_mid,
                anchor="center",
                text=m1,
                fill=_minute_color(m1, minute_base, f1),
                font=self._font(40, "bold"),
            )
            self.canvas.create_text(
                col2,
                y_mid,
                anchor="center",
                text=m2,
                fill=_minute_color(m2, minute_base, f2),
                font=self._font(40, "bold"),
            )

    def _draw_crescent(self, cx: int, cy: int, radius: int):
        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=RAM_ACCENT, outline="")
        self.canvas.create_oval(
            cx - radius + 8,
            cy - radius - 1,
            cx + radius + 8,
            cy + radius - 1,
            fill=RAM_BG,
            outline="",
        )

    def _draw_ramadan_bar(self, x0: int, y0: int, x1: int, h: int):
        ram = _parse_ramadan(self.model.footer_lines)
        y1 = y0 + h
        bar_w = x1 - x0
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=RAM_BG, outline=RAM_BORDER, width=1)
        self._draw_crescent(x0 + 24, y0 + h // 2, 11)

        self.canvas.create_text(
            x0 + 44,
            y0 + h // 2,
            anchor="w",
            text=f"🕌 {ram['title']}",
            fill=RAM_TEXT,
            font=self._font(20, "normal"),
        )

        info_x = x0 + int(bar_w * 0.53)
        self.canvas.create_text(
            info_x,
            y0 + 18,
            anchor="w",
            text="SAHUR / IMSAK",
            fill=RAM_TITLE,
            font=self._font(15, "bold"),
        )
        self.canvas.create_text(
            info_x,
            y0 + h - 22,
            anchor="w",
            text=f"{ram['imsak_time']}    Kalan: {ram['imsak_left']}",
            fill=RAM_TEXT,
            font=self._font(18, "bold"),
        )

        iftar_x = x0 + int(bar_w * 0.77)
        self.canvas.create_text(
            iftar_x,
            y0 + 18,
            anchor="w",
            text="IFTAR",
            fill=RAM_ACCENT,
            font=self._font(15, "bold"),
        )
        self.canvas.create_text(
            iftar_x,
            y0 + h - 22,
            anchor="w",
            text=f"{ram['iftar_time']}    Kalan: {ram['iftar_left']}",
            fill=RAM_ACCENT,
            font=self._font(18, "bold"),
        )

    def _draw(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 100 or height < 100:
            return

        self.canvas.delete("all")
        self._draw_background(width, height)
        x0, y0, x1, y1 = self._draw_shell(width, height)

        header_bottom = self._draw_header(x0, y0, x1)
        inner_h = y1 - header_bottom
        show_ramadan = config.SHOW_RAMADAN_PANEL and bool(self.model.footer_lines)
        footer_h = 72 if show_ramadan else 0
        cards_gap = 12 if show_ramadan else 0
        cards_h = inner_h - footer_h - cards_gap - 8
        card_h = int(cards_h / 2)
        panel_w = x1 - x0

        lines = self.model.lines[:2]
        if len(lines) < 2:
            lines = lines + [LineBlock(name="LINE", directions=[])] * (2 - len(lines))

        self._draw_line_panel(x0, header_bottom, x0 + panel_w, card_h, lines[0])
        second_y = header_bottom + card_h + cards_gap
        self._draw_line_panel(x0, second_y, x0 + panel_w, card_h, lines[1])

        if show_ramadan:
            ram_y = y1 - footer_h
            self._draw_ramadan_bar(x0, ram_y, x1, footer_h)

        if self.model.note:
            self.canvas.create_text(
                x1 - 6,
                y1 - 4,
                anchor="se",
                text=self.model.note,
                fill=TEXT_SOFT,
                font=self._font(11, "normal"),
            )

    def _refresh_model(self):
        try:
            with get_connection() as conn:
                self.model = app._build_model(conn)
        except Exception as err:  # noqa: BLE001
            self.model = ScreenModel(
                title=config.STATION_NAME.upper(),
                updated_at=datetime.now(),
                lines=[],
                note=f"Hata: {err}",
                footer_lines=[],
            )
        self._draw()
        self.root.after(config.REFRESH_SECONDS * 1000, self._refresh_model)

    def run(self):
        app._ensure_db()
        self._refresh_model()
        self.root.mainloop()


def main() -> None:
    DesktopBoard().run()


if __name__ == "__main__":
    main()

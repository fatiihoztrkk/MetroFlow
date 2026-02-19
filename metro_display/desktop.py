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

BG_TOP = "#353941"
BG_BOTTOM = "#141820"
SHELL_OUTER = "#0c0f14"
SHELL_INNER = "#1b2230"
PANEL_FILL = "#1e2431"
PANEL_BORDER = "#3b4354"
PANEL_DIVIDER = "#414a5e"

TEXT_MAIN = "#f3f5fa"
TEXT_MUTED = "#9da7bb"
TEXT_SOFT = "#7d889c"
CYAN = "#72efff"
GREEN = "#8dffbd"

RAM_BG = "#15211a"
RAM_BORDER = "#3d5847"
RAM_TITLE = "#ddf6e4"
RAM_TEXT = "#f0fff4"
RAM_ACCENT = "#ffd66a"


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


def _departure_min(dep: str) -> Optional[int]:
    dep = (dep or "").strip()
    if not dep:
        return None
    if dep.lower().startswith("yarın"):
        return 24 * 60
    match = re.match(r"^\s*(\d+)\s+dk", dep, re.I)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _departure_label(dep: str) -> str:
    minutes = _departure_min(dep)
    if minutes is None:
        return "--"
    if minutes >= 24 * 60:
        return "YRN"
    return str(minutes)


def _line_theme(line_name: str) -> Tuple[str, str]:
    norm = line_name.lower()
    if "marmaray" in norm:
        return ("#ff6a79", "#f5cf58")
    if norm == "m4":
        return ("#ff78d8", "#f279ff")
    return ("#7edfff", "#f5cf58")


def _line_rows(line: LineBlock) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for direction in line.directions:
        raw_deps = direction.departures if direction.departures else ["--"]
        mins = [_departure_label(dep) for dep in raw_deps[:2]]
        while len(mins) < 2:
            mins.append("--")
        rows.append({"dest": _safe_text(direction.label), "mins": mins})
    return rows


def _minute_color(label: str, minute_base: str) -> str:
    if label == "--":
        return TEXT_SOFT
    if label == "YRN":
        return CYAN
    try:
        minute = int(label)
    except ValueError:
        return TEXT_MAIN
    if minute == 0:
        return GREEN
    if minute <= 2:
        return GREEN
    return minute_base


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
        clock = self.model.updated_at.strftime("%H:%M:%S")
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

        self.canvas.create_rectangle(x0, y0, x1, y1, fill=PANEL_FILL, outline=PANEL_BORDER, width=1)
        left_w = int(panel_w * 0.60)
        left_x1 = x0 + left_w

        self.canvas.create_text(
            x0 + 18,
            y0 + 28,
            anchor="w",
            text=line.name.upper(),
            fill=TEXT_MAIN,
            font=self._font(46 if "M4" not in line.name else 42, "bold"),
        )

        self.canvas.create_line(x0 + 16, y0 + 50, left_x1 - 16, y0 + 50, fill=PANEL_DIVIDER, width=1)
        self.canvas.create_line(left_x1, y0 + 14, left_x1, y1 - 14, fill=PANEL_DIVIDER, width=1)

        right_w = panel_w - left_w
        right_x0 = left_x1
        self.canvas.create_text(
            right_x0 + right_w / 2,
            y0 + 28,
            anchor="center",
            text="MINUTES AWAY",
            fill=minute_base,
            font=self._font(36, "bold"),
        )
        self.canvas.create_line(right_x0 + 16, y0 + 50, x1 - 16, y0 + 50, fill=PANEL_DIVIDER, width=1)

        row_top = y0 + 76
        row_bottom = y1 - 18
        count = max(1, len(rows))
        row_step = (row_bottom - row_top) / float(count)

        col1 = int(right_x0 + right_w * 0.34)
        col2 = int(right_x0 + right_w * 0.72)

        for idx, row in enumerate(rows):
            y_mid = int(row_top + idx * row_step + row_step * 0.5)
            dest = str(row["dest"])
            dest_color = accent if idx == 0 else TEXT_MAIN
            self.canvas.create_text(
                x0 + 22,
                y_mid,
                anchor="w",
                text=dest,
                fill=dest_color,
                font=self._font(42, "normal"),
            )

            mins: List[str] = row["mins"]  # type: ignore[assignment]
            m1 = mins[0] if len(mins) > 0 else "--"
            m2 = mins[1] if len(mins) > 1 else "--"

            self.canvas.create_text(
                col1,
                y_mid,
                anchor="center",
                text=m1,
                fill=_minute_color(m1, minute_base),
                font=self._font(48, "bold"),
            )
            self.canvas.create_text(
                col2,
                y_mid,
                anchor="center",
                text=m2,
                fill=_minute_color(m2, minute_base),
                font=self._font(48, "bold"),
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
            text=ram["title"],
            fill=RAM_TEXT,
            font=self._font(24, "normal"),
        )

        info_x = x0 + int(bar_w * 0.53)
        self.canvas.create_text(
            info_x,
            y0 + 18,
            anchor="w",
            text="SAHUR / IMSAK",
            fill=RAM_TITLE,
            font=self._font(18, "bold"),
        )
        self.canvas.create_text(
            info_x,
            y0 + h - 22,
            anchor="w",
            text=f"{ram['imsak_time']}    Kalan: {ram['imsak_left']}",
            fill=RAM_TEXT,
            font=self._font(22, "bold"),
        )

        iftar_x = x0 + int(bar_w * 0.77)
        self.canvas.create_text(
            iftar_x,
            y0 + 18,
            anchor="w",
            text="IFTAR",
            fill=RAM_ACCENT,
            font=self._font(18, "bold"),
        )
        self.canvas.create_text(
            iftar_x,
            y0 + h - 22,
            anchor="w",
            text=f"{ram['iftar_time']}    Kalan: {ram['iftar_left']}",
            fill=RAM_ACCENT,
            font=self._font(22, "bold"),
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

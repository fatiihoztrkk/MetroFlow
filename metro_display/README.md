# metro_display

Canli metro panosu motoru (M4 + Marmaray + Ramazan paneli).

## Modlar
- `python -m metro_display.desktop`
  - 1024x600 profesyonel dashboard UI
  - Ana panellerde destination + dakika kolonlari
- `python -m metro_display.terminal`
  - terminal odakli gorunum
- `python -m metro_display.app`
  - PNG/E-Ink render (`metro_display/data/last.png`)

## Gereksinimler
- Python `3.11+`
- `pip install -r metro_display/requirements.txt`
- GUI icin `tkinter`:
  - macOS: `brew install python-tk@3.11`
  - Linux: `sudo apt install python3-tk`

## Baslangic
```bash
source .venv/bin/activate
python -m metro_display.desktop
```

## Veri Akisi
- M4: Metro Istanbul timetable endpoint
- Marmaray: TCDD timetable endpoint
- Ramazan: Aladhan timings endpoint
- `LIVE_FALLBACK_TO_GTFS=True` ise canli hata durumunda GTFS fallback devrede kalir

## Ana Ayarlar (`config.py`)
- Genel: `STATION_NAME`, `TIMEZONE`, `REFRESH_SECONDS`
- Canli/Fallback: `USE_LIVE_SOURCES`, `LIVE_FALLBACK_TO_GTFS`, `SHOW_STATUS_NOTE`
- Ramazan: `SHOW_RAMADAN_PANEL`, `RAMADAN_TARGET_DATE`
- Desktop: `DESKTOP_WIDTH`, `DESKTOP_HEIGHT`, `DESKTOP_FULLSCREEN`, `DESKTOP_FONT_FAMILY`
- Terminal: `TERMINAL_WIDTH`, `TERMINAL_USE_UNICODE`

## Notlar
- Bu paket `urllib` kullandigi icin `requests` gerekmez.
- `tkinter` pip paketi degildir; sistemden kurulmalidir.

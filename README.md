# AyrilikPano

Ayrilik Cesmesi icin canli metro panosu:
- Marmaray + M4 kalan dakika
- 1024x600 profesyonel desktop dashboard
- Ramazan alt bar (imsak/iftar + kalan sure)
- Canli kaynak hata verirse GTFS fallback

## Ozellikler
- Canli veri:
  - M4: Metro Istanbul sefer endpoint
  - Marmaray: TCDD sefer endpoint
- Ekran modlari:
  - `terminal`: sade tablo gorunumu
  - `desktop`: profesyonel dashboard (onerilen)
  - `app`: PNG/E-Ink render
- Ramazan paneli:
  - Tarih, imsak, iftar, kalan sure
  - API hatasinda kontrollu fallback

## Gereksinimler
- Python `3.11+` (onerilen)
- `pip`
- Masaustu GUI icin `tkinter`

macOS (Homebrew Python) icin `tkinter`:
```bash
brew install python@3.11 python-tk@3.11
```

Linux/Raspberry Pi icin `tkinter`:
```bash
sudo apt update
sudo apt install -y python3-tk
```

## Kurulum
```bash
cd m4_marmaray_timeline
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r metro_display/requirements.txt
```

Not:
- `tkinter` pip ile kurulmaz; sistemden kurulur.
- Ayrinti ve komutlar `metro_display/requirements.txt` icine eklendi.

## Calistirma

Desktop dashboard (onerilen):
```bash
source .venv/bin/activate
python -m metro_display.desktop
```

Terminal:
```bash
source .venv/bin/activate
python -m metro_display.terminal
```

PNG/E-Ink render:
```bash
source .venv/bin/activate
python -m metro_display.app
```

PNG cikti yolu:
```text
metro_display/data/last.png
```

## Kisa Kontroller
- `F11`: fullscreen ac/kapat (desktop mod)
- `Esc` veya `q`: cikis

## Veri Kaynaklari
- M4:
  - `https://www.metro.istanbul/SeferDurumlari/SeferDetaylari`
  - `https://www.metro.istanbul/SeferDurumlari/AJAXSeferGetir`
- Marmaray:
  - `https://www.tcddtasimacilik.gov.tr/marmaray/tr/gunluk_tren_saatleri`
  - `https://api.tcddtasimacilik.gov.tr/api/SubPages/GetTransportationTrainsGroupwithHours?marmaray=true`
- Ramazan:
  - `https://api.aladhan.com/v1/timingsByCity`

## Konfigurasyon
Tum ayarlar: `metro_display/config.py`

Temel:
- `STATION_NAME`
- `TIMEZONE`
- `REFRESH_SECONDS`
- `DEPARTURES_PER_DIRECTION`
- `LOOKAHEAD_MINUTES`

Canli/Fallback:
- `USE_LIVE_SOURCES`
- `LIVE_FALLBACK_TO_GTFS`
- `SHOW_STATUS_NOTE`
- `ALLOW_CALENDAR_FALLBACK`
- `CALENDAR_FALLBACK_DAYS`

Ramazan:
- `SHOW_RAMADAN_PANEL`
- `RAMADAN_TARGET_DATE`
- `RAMADAN_CITY` / `RAMADAN_COUNTRY` / `RAMADAN_METHOD`

Desktop UI (1024x600):
- `DESKTOP_WIDTH` / `DESKTOP_HEIGHT`
- `DESKTOP_FULLSCREEN`
- `DESKTOP_FONT_FAMILY`
- `DESKTOP_SHOW_TIME_AFTER_MINUTES` (`30` ise 31+ dk satirlarinda dakika yerine `HH:MM` gosterir)

Terminal UI:
- `TERMINAL_WIDTH`
- `TERMINAL_LABEL_WIDTH`
- `TERMINAL_USE_UNICODE`
- `TERMINAL_SECTION_PADDING`

## SSS / Sorun Giderme

`ModuleNotFoundError: No module named '_tkinter'`
- `python-tk` kur:
  - macOS: `brew install python-tk@3.11`
  - Linux: `sudo apt install python3-tk`
- Sonra `.venv` ile calistir:
```bash
source .venv/bin/activate
python -m metro_display.desktop
```

`PIL` hatasi:
```bash
source .venv/bin/activate
pip install -r metro_display/requirements.txt
```

GTFS cache sifirlama:
```bash
rm -f metro_display/data/gtfs.zip
source .venv/bin/activate
python -m metro_display.terminal
```

## Proje Yapisi
- `metro_display/app.py`: model uretimi ve ana dongu
- `metro_display/live_sources.py`: canli M4/Marmaray toplayici
- `metro_display/ramadan.py`: imsak/iftar panel verisi
- `metro_display/desktop.py`: 1024x600 dashboard UI
- `metro_display/terminal.py`: terminal UI
- `metro_display/render/`: PNG/E-Ink cizim
- `metro_display/gtfs/`: GTFS indirme/import

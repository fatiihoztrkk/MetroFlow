# AyrilikPano

## 🚀 Proje Hakkında
Ayrılık Çeşmesi gibi kritik aktarma noktalarında kullanılmak üzere geliştirilmiş gerçek zamanlı bir ulaşım panosudur.  
Python tabanlıdır ve M4 / Marmaray canlı kaynaklarını kullanır; canlı veri alınamazsa GTFS fallback ile çalışmayı sürdürür.

## Özellikler
- M4 ve Marmaray için yaklaşan sefer süreleri
- 1024x600 kiosk odaklı desktop ekran (`metro_display.desktop`)
- Terminal görünümü (`metro_display.terminal`)
- PNG/E-Ink render modu (`metro_display.app`)
- Ramazan alt barı (imsak / iftar + kalan süre)

## 🛠️ Özelleştirme (M3 veya Başka Duraklar İçin)

### 1) Durak Seçimi (`station_id` / `stop_id`)
Ana ayarlar `metro_display/config.py` dosyasındadır.

- Genel durak adı: `STATION_NAME`
- Hat bazlı sabit duraklar: `LINES[*].stop_ids`
- Hat filtreleri: `LINES[*].route_keywords`, `LINES[*].directions[*].headsign_keywords`

Örnek (M3 gibi başka bir hat eklemek için):

```python
LINES = [
    {
        "name": "M3",
        "route_keywords": ["M3"],
        "stop_ids": ["BURAYA_STOP_ID"],
        "directions": [
            {"label": "Kirazli", "headsign_keywords": ["Kirazli"]},
            {"label": "Basin Ekspres", "headsign_keywords": ["Basin"]},
        ],
    },
]
```

Yerel GTFS veritabanından `stop_id` bulma örneği:

```bash
sqlite3 metro_display/data/gtfs.sqlite3 "SELECT stop_id, stop_name FROM stops WHERE lower(stop_name) LIKE '%kirazli%';"
```

### 2) API Kaynağı
Proje şu kaynakları kullanır:

- M4 canlı: `https://www.metro.istanbul/SeferDurumlari/SeferDetaylari` ve `https://www.metro.istanbul/SeferDurumlari/AJAXSeferGetir`
- Marmaray canlı: `https://www.tcddtasimacilik.gov.tr/marmaray/tr/gunluk_tren_saatleri` ve `https://api.tcddtasimacilik.gov.tr/api/SubPages/GetTransportationTrainsGroupwithHours?marmaray=true`
- GTFS fallback: `CKAN_BASE_URL` + `CKAN_DATASET_ID` (varsayılan: B40/İBB GTFS)
- Ramazan: `https://api.aladhan.com/v1/timingsByCity`

Farklı hatlara uyarlarken önce ilgili canlı endpoint var mı kontrol et; yoksa GTFS ile çalıştır.

## GTFS Teknik Notu
GTFS (General Transit Feed Specification), toplu taşıma verilerinin (duraklar, güzergahlar, saatler) ortak bir formatta paylaşılmasını sağlayan küresel bir standarttır ve Google tarafından başlatılmıştır.  
Bu projede GTFS verisini canlı kaynaklarla birlikte kullanarak statik tarife + anlık veri yaklaşımı kurulmuştur. Bu yapı, büyük ulaşım veri setlerini gerçek zamanlı işleme tarafında güçlü bir temel sağlar.

### Diğer Hatlara Uyarlama
Bu proje GTFS standartlarını kullandığı için, `config.py` içindeki durak (`Station/Stop ID`) ve hat bilgilerini değiştirerek projeyi herhangi bir İstanbul metrosuna veya Marmaray durağına kısa sürede uyarlayabilirsiniz.

## 📦 Kurulum ve Çalıştırma

### Gereksinimler
- Python `3.11+`
- `tkinter` (pip paketi değildir)

Linux / Raspberry Pi:

```bash
sudo apt update
sudo apt install -y python3-full python3-venv python3-tk
```

### Sanal Ortam

```bash
cd m4_marmaray_timeline
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r metro_display/requirements.txt
```

### Çalıştırma

Desktop (önerilen):

```bash
python -m metro_display.desktop
```

Terminal:

```bash
python -m metro_display.terminal
```

PNG/E-Ink:

```bash
python -m metro_display.app
```

## Raspberry Pi Kiosk Modu

### Manuel kiosk açılış

```bash
cd /home/yusuf/Desktop/m4_marmaray_timeline
source .venv/bin/activate
export DISPLAY=:0
export XAUTHORITY=/home/yusuf/.Xauthority
PYTHONPATH="$PWD" python -m metro_display.desktop
```

Desktop modu kiosk davranışı içerir:
- Tam ekran + başlıksız pencere
- Fare gizleme
- `Esc`: fullscreen çıkış
- `q`: uygulamayı kapatma

### Autostart (systemd)
Repo içinde örnek service: `metro_display/systemd/metro-display.service`

1. Servisi sisteme kopyala:

```bash
sudo cp metro_display/systemd/metro-display.service /etc/systemd/system/metro-display.service
```

2. Servis dosyasında `User`, `WorkingDirectory`, `ExecStart` yollarını kendi ortama göre güncelle.

Örnek kiosk servis:

```ini
[Unit]
Description=Metro Display Desktop
After=graphical.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=yusuf
WorkingDirectory=/home/yusuf/Desktop/m4_marmaray_timeline
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/yusuf/.Xauthority
Environment=PYTHONPATH=/home/yusuf/Desktop/m4_marmaray_timeline
ExecStart=/home/yusuf/Desktop/m4_marmaray_timeline/.venv/bin/python -m metro_display.desktop
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
```

3. Etkinleştir:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now metro-display.service
sudo systemctl status metro-display.service
```

Log takibi:

```bash
journalctl -u metro-display.service -f
```

## Konfigürasyon Özeti
Tüm ayarlar: `metro_display/config.py`

- Genel: `STATION_NAME`, `TIMEZONE`, `REFRESH_SECONDS`
- Canlı/Fallback: `USE_LIVE_SOURCES`, `LIVE_FALLBACK_TO_GTFS`, `SHOW_STATUS_NOTE`
- Hatlar: `LINES`, `stop_ids`, `route_keywords`, `headsign_keywords`
- Desktop: `DESKTOP_WIDTH`, `DESKTOP_HEIGHT`, `DESKTOP_FULLSCREEN`
- Ramazan: `SHOW_RAMADAN_PANEL`, `RAMADAN_TARGET_DATE`

## Sorun Giderme

`No module named metro_display.desktop`:

```bash
cd /home/yusuf/Desktop/m4_marmaray_timeline
PYTHONPATH="$PWD" .venv/bin/python -c "import metro_display.desktop; print('ok')"
```

`_tkinter` hatası:

```bash
sudo apt install -y python3-tk
```

## Proje Yapısı
- `metro_display/app.py`: model üretimi ve ana döngü
- `metro_display/live_sources.py`: canlı kaynak toplayıcı
- `metro_display/ramadan.py`: imsak/iftar verisi
- `metro_display/desktop.py`: 1024x600 dashboard/kiosk UI
- `metro_display/terminal.py`: terminal UI
- `metro_display/gtfs/`: GTFS indirme/import
- `metro_display/render/`: PNG/E-Ink render

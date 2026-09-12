# Stream TV

Stylish dark Windows desktop IPTV client that browses free country playlists from [publiciptv.com](https://publiciptv.com/countries) and plays streams via VLC.

Türkçe arayüz · Modern koyu tema · Favoriler · Yerel önbellek

---

## English

### Features
- Country list with search (scraped from `https://publiciptv.com/countries`)
- Per-country M3U pages (`/countries/{iso2}/m3u`) — parses `#EXTINF` from HTML `<pre>`
- Channel list with logos, name, category; search + category filter
- Favorites persisted as JSON
- Playback via **python-vlc** when VLC is installed; otherwise Turkish guidance + open/copy URL
- Remembers last country and window geometry
- Local playlist/logo cache with polite HTTP User-Agent

### Requirements
- Windows 10/11 (primary), Python **3.11+**
- [VLC Media Player](https://www.videolan.org/vlc/) (recommended for in-app playback)
- Dependencies in `requirements.txt`

### Install & Run

```bat
run.bat
```

Or manually:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app
```

Also works: `python main.py`

### Project layout

```
stream-tv/
├── app/
│   ├── main.py              # entry logic
│   ├── models.py
│   ├── fetcher/             # HTTP client, countries, M3U parser
│   ├── player/              # VLC + fallbacks
│   ├── settings/            # JSON settings & favorites
│   └── ui/                  # CustomTkinter dark UI
├── cache/                   # playlists & logos (gitignored)
├── data/                    # settings.json, favorites.json
├── main.py
├── run.bat
└── requirements.txt
```

### Notes
- Streams come from public third-party sources; availability varies by region and ISP.
- Some countries may have no M3U — the app shows a clear empty state.
- Without VLC, use **Tarayıcıda Aç** / **URL Kopyala**.

---

## Türkçe

### Özellikler
- Ülke listesi ve arama (`publiciptv.com/countries`)
- Ülke M3U sayfalarından kanal ayrıştırma (`/countries/{iso2}/m3u`)
- Logo, ad, kategori; arama ve kategori filtresi
- Favoriler (JSON)
- VLC ile oynatma; yoksa Türkçe uyarı + tarayıcı / panoya kopyala
- Son ülke ve pencere boyutu hatırlanır
- Yerel önbellek, nazik User-Agent

### Kurulum

1. [Python 3.11+](https://www.python.org/downloads/) kurun (PATH’e ekleyin).
2. İsteğe bağlı: [VLC](https://www.videolan.org/vlc/) kurun.
3. `run.bat` dosyasını çalıştırın.

Manuel:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app
```

### Sorun giderme
| Sorun | Çözüm |
|--------|--------|
| `VLC bulunamadı` | VLC kurup uygulamayı yeniden başlatın |
| Ülke/kanal yüklenmiyor | İnterneti kontrol edin; ↻ ile yenileyin |
| Logo görünmüyor | Önbellek `cache/logos` — ağ engeli olabilir |

### Lisans / kaynak
Kanal listeleri [Public IPTV](https://publiciptv.com) üzerinden alınır. Bu uygulama bağımsız bir masaüstü istemcisidir.

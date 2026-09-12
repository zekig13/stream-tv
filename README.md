# Stream TV

Stylish dark Windows desktop IPTV client that browses free country playlists from [publiciptv.com](https://publiciptv.com/countries) and plays streams via VLC.

**Sürüm:** 1.1.1 · Türkçe arayüz · Modern koyu tema · Favoriler · Yerel önbellek

---

## Hazır Windows EXE (v1.1.1)

İndir: [releases/StreamTV.exe](https://github.com/zekig13/stream-tv/releases/download/v1.1.1/StreamTV.exe)  
(alternatif: [repo içi kopya](https://github.com/zekig13/stream-tv/raw/main/releases/StreamTV.exe))

### SmartScreen uyarısı
İmzasız olduğu için Windows “tanınmayan uygulama” diyebilir:

1. **Ek bilgi**
2. **Yine de çalıştır**

Bu beklenen bir durum; kişisel kullanımda güvenlidir (kaynak bu repoda).

### VLC
Uygulama içi / sistem VLC oynatma için [VLC Media Player](https://www.videolan.org/vlc/) kurun.

---

## English

### Features
- Country list with search (`https://publiciptv.com/countries`)
- Per-country M3U pages (`/countries/{iso2}/m3u`) — parses `#EXTINF` from HTML `<pre>`
- Channel list with logos, name, category; search + category filter
- Favorites persisted as JSON
- Playback via **python-vlc** when available; otherwise system `vlc.exe`, browser, or copy URL
- Remembers last country and window geometry
- Local playlist/logo cache (writable next to the EXE when packaged)

### Requirements
- Windows 10/11 (primary), Python **3.11+** (source run)
- [VLC Media Player](https://www.videolan.org/vlc/) (recommended)
- Dependencies in `requirements.txt`

### Install & Run (source)

```bat
run.bat
```

Or:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app
```

### Build EXE

```bat
build.bat
```

Output: `dist\StreamTV.exe`

---

## Türkçe

### Özellikler
- Ülke listesi ve arama
- M3U sayfalarından kanal ayrıştırma
- Logo, ad, kategori; arama / filtre / favoriler
- VLC (python-vlc veya sistem VLC), tarayıcı, URL kopyala
- Son ülke ve pencere boyutu hatırlanır

### Kaynaktan çalıştırma
1. [Python 3.11+](https://www.python.org/downloads/) kurun  
2. İsteğe bağlı: [VLC](https://www.videolan.org/vlc/)  
3. `run.bat`

### Sorun giderme
| Sorun | Çözüm |
|--------|--------|
| SmartScreen | Ek bilgi → Yine de çalıştır |
| VLC bulunamadı | VLC kurup uygulamayı yeniden başlatın |
| Ülke/kanal yok | İnternet / ↻ yenile |
| Ayarlar kayboluyor | EXE yanında `data\` klasörüne yazma izni verin |

### Lisans / kaynak
Kanal listeleri [Public IPTV](https://publiciptv.com) üzerinden alınır. Bu uygulama bağımsız bir masaüstü istemcisidir.

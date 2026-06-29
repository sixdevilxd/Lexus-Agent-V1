# 🤖 Lexus-Agent-V1 — AI Agent Telegram via Conduit (Termux-Ready)

AI Agent Bot Telegram bertenaga **Conduit (conduit.ozdoev.net)** dengan **riset internet otonom** dan output bergaya _coding-vibes_ ala **Claude / Fable 5 / Mythos**. Ringan, tanpa kompilasi Rust, siap jalan di **Termux** maupun VPS.

> ⚙️ Memanggil API Conduit langsung via `requests` (bukan SDK `openai`) → bebas dari error build `jiter`/`pydantic-core` di Termux.

---

## ⚡ Fitur Utama
1. **🧠 Chat AI multi-turn** — ingat konteks percakapan.
2. **🔄 Multi-model** — ganti model dari chat (`/model <id polos>`).
3. **🖼️ Vision** — kirim foto + pertanyaan.
4. **🔍 Web Search otonom** — AI mencari sendiri di internet saat perlu (DuckDuckGo).
5. **📱 Riset Sosmed** — X/Twitter, Facebook, Instagram, Reddit, TikTok, YouTube, LinkedIn.
6. **👽 Riset Reddit** — diskusi & sentimen komunitas.
7. **🌐 Baca halaman** — ekstrak & ringkas isi URL.
8. **📊 Analisa Teknikal TradingView** — `/ta SYMBOL`.
9. **💰 Harga Real-Time** — Binance, `/price SYMBOL`.
10. **🌊 Streaming** & **✨ output rapi** bergaya coding-vibes.

> 💡 Riset internet memakai **function-calling**: cukup tanya biasa, AI otomatis memutuskan kapan harus mencari, lalu meringkas + menyertakan sumber.

---

## 📲 Instalasi di Termux
```bash
pkg update && pkg upgrade -y
pkg install python git -y

git clone https://github.com/sixdevilxd/Lexus-Agent-V1.git
cd Lexus-Agent-V1

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env        # isi TELEGRAM_BOT_TOKEN & CONDUIT_API_KEY
python bot.py
```

---

## 🔑 Konfigurasi `.env`
| Variabel | Keterangan |
|----------|-----------|
| `TELEGRAM_BOT_TOKEN` | Token dari @BotFather |
| `CONDUIT_API_KEY` | API key Conduit (`sk-cdt-...`) |
| `CONDUIT_BASE_URL` | **WAJIB** `https://conduit.ozdoev.net/api/v1` |
| `DEFAULT_MODEL` | **id POLOS** tanpa prefix, mis. `claude-sonnet-4-6` |
| `MAX_HISTORY` | Jumlah memori percakapan |
| `STREAM_ENABLED` | `true`/`false` (berlaku saat tools off) |

> ⚠️ **Model harus id polos.** Conduit menolak `anthropic/claude-opus-4-8` (error `Unknown model`). Pakai `claude-opus-4-8`. Bot otomatis menghapus prefix bila ada.

---

## 🛠️ Perintah Bot
| Perintah | Fungsi |
|----------|--------|
| `/start` `/help` | Panduan & fitur |
| `/model [id]` | Lihat / ganti model |
| `/search <kata>` | Cari di internet |
| `/reddit <kata>` | Riset Reddit |
| `/social <platform> <kata>` | Riset sosmed (x/fb/ig/reddit/tiktok/youtube/linkedin) |
| `/web <url>` | Baca & ringkas halaman |
| `/ta SYMBOL [TF]` | Analisa teknikal TradingView |
| `/price SYMBOL` | Harga real-time Binance |
| `/tools` | Nyalakan/matikan riset otonom (default ON) |
| `/stream` | Streaming (saat tools off) |
| `/clear` | Hapus memori percakapan |

**Contoh:** `/social x bitcoin etf` · `/ta BTCUSDT 4h` · `/price SOLUSDT`

---

## 📁 Struktur Proyek
```
Lexus-Agent-V1/
├── bot.py             # Handler, agentic tool-calling, perintah
├── conduit_client.py  # Client Conduit (chat, stream, tools) + normalisasi model
├── research.py        # Web search, fetch URL, Reddit, sosmed
├── market.py          # TradingView TA + harga Binance
├── utils.py           # Render pesan aman (Markdown fallback + split)
├── config.py          # Konfigurasi & validasi
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚠️ Troubleshooting
- **`Unknown model: anthropic/...`** → pakai id polos (`claude-opus-4-8`). Bot kini auto-strip prefix.
- **`No scheme supplied` / URL aneh** → `CONDUIT_BASE_URL=https://conduit.ozdoev.net/api/v1`.
- **`can't parse entities`** → sudah ditangani (auto fallback ke teks biasa).
- **`Failed to build jiter`** → repo ini tidak pakai `openai` SDK; `git pull` & `pip install -r requirements.txt`.
- **401 Unauthorized** → cek API key & kredit di dashboard Conduit.

## 👥 Mode Grup
Matikan **Group Privacy** di @BotFather (`/mybots` → Bot Settings → Group Privacy → Turn off) agar bot membaca pesan grup. Panggil via `@mention` atau balas pesannya.

# 🤖 Lexus-Agent-V1 — AI Agent Telegram

**Visi/Misi:** AI Agent yang fokus pada **otomatisasi**, **web search cerdas**, dan **coding vibes**. Ringan, siap jalan di **Termux** maupun VPS.

---

## ⚡ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🧠 **Chat AI multi-turn** | Ingat konteks percakapan |
| 🔄 **Multi-model** | Ganti model dari chat (`/model <id>`) |
| 🖼️ **Vision** | Kirim foto + pertanyaan |
| 🔍 **Web Search otonom** | AI cari info sendiri saat perlu (DuckDuckGo) |
| 📱 **Riset Sosmed** | X/Twitter, Facebook, Instagram, Reddit, TikTok, YouTube, LinkedIn |
| 👽 **Riset Reddit** | Diskusi & sentimen komunitas |
| 🌐 **Baca halaman** | Ekstrak & ringkas isi URL |
| 📊 **Analisa Teknikal TradingView** | `/ta SYMBOL` |
| 💰 **Harga Real-Time** | Binance, `/price SYMBOL` |
| 🌊 **Streaming output** | Respons real-time bergaya coding vibes |

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
nano .env        # isi TELEGRAM_BOT_TOKEN & API_KEY
python bot.py
```

---

## 🔑 Konfigurasi `.env`

| Variabel | Keterangan |
|----------|-----------|
| `TELEGRAM_BOT_TOKEN` | Token dari @BotFather |
| `API_KEY` | API key dari penyedia layanan |
| `API_BASE_URL` | Endpoint API |
| `DEFAULT_MODEL` | Nama model default (mis. `claude-sonnet-4-6`) |
| `MAX_HISTORY` | Jumlah memori percakapan |
| `STREAM_ENABLED` | `true`/`false` (streaming saat tools off) |

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
├── api_client.py      # Client API (chat, stream, tools) + normalisasi model
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

- **Error model tidak dikenal** → pakai nama model tanpa prefix (mis. `claude-sonnet-4-6`).
- **Error URL/endpoint** → pastikan `API_BASE_URL` diisi dengan benar.
- **`can't parse entities`** → sudah ditangani (auto fallback ke teks biasa).
- **401 Unauthorized** → cek API key & kredit akun.

## 👥 Mode Grup

Matikan **Group Privacy** bot di @BotFather agar bot bisa baca semua pesan grup.

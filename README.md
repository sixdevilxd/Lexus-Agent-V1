# Lexus-Agent-V1 — AI Agent Telegram

**Visi/Misi:** Otomatisasi, web search, coding vibes. Jalan di Termux & VPS.

---

## Fitur

| Fitur | Fungsi |
|-------|--------|
| Chat multi-turn | Ingat konteks percakapan |
| Multi-model | Ganti model via chat (`/model <id>`) |
| Vision | Input gambar + tanya, AI baca & jawab |
| Web search | Cari info otomatis (DuckDuckGo) |
| Riset sosmed | X, Facebook, Instagram, Reddit, TikTok, YouTube, LinkedIn |
| Riset Reddit | Cari diskusi & trending topic |
| Baca URL | Ambil & ringkas isi halaman |
| Analisa teknikal | `/ta SYMBOL` via TradingView |
| Harga crypto | `/price SYMBOL` via Binance |
| Streaming output | Respons real-time |

> **Vision:** Kirim foto/gambar apa aja — screenshot error, diagram, dokumen scan, code screenshot, meme. AI bakal baca teks, jelasin isi, atau jawab pertanyaan seputar gambar itu. Tinggal kirim foto + ketik pertanyaan, beres.
>
> Riset internet pakai function-calling: tinggal tanya, AI mutusin sendiri kapan perlu cari info, lalu ngasih jawaban + sumber.

---

## Instalasi (Termux)

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

## Konfigurasi `.env`

| Variabel | Fungsi |
|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Token dari @BotFather |
| `API_KEY` | API key penyedia layanan |
| `API_BASE_URL` | Endpoint API |
| `DEFAULT_MODEL` | Model default (mis. `claude-sonnet-4-6`) |
| `MAX_HISTORY` | Jumlah memori percakapan |
| `STREAM_ENABLED` | `true`/`false` (streaming pas tools off) |

---

## Perintah Bot

| Perintah | Fungsi |
|----------|--------|
| `/start` `/help` | Bantuan & daftar fitur |
| `/model [id]` | Lihat / ganti model |
| `/search <kata>` | Cari di internet |
| `/reddit <kata>` | Cari di Reddit |
| `/social <platform> <kata>` | Cari di sosmed (x/fb/ig/reddit/tiktok/youtube/linkedin) |
| `/web <url>` | Baca & ringkas URL |
| `/ta SYMBOL [TF]` | Analisa teknikal TradingView |
| `/price SYMBOL` | Harga real-time Binance |
| `/tools` | Aktif/nonaktif riset otomatis (default: ON) |
| `/stream` | Streaming output (pas tools off) |
| `/clear` | Hapus memori chat |

**Contoh:** `/social x bitcoin etf` · `/ta BTCUSDT 4h` · `/price SOLUSDT`

---

## Struktur File

```
Lexus-Agent-V1/
├── bot.py             # Handler, agentic tool-calling, perintah
├── api_client.py      # Client API (chat, stream, tools)
├── research.py        # Web search, fetch URL, Reddit, sosmed
├── market.py          # TradingView TA + harga Binance
├── utils.py           # Render pesan (Markdown fallback + split)
├── config.py          # Konfigurasi & validasi env
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Troubleshooting

- **Model error** → pakai nama model tanpa prefix (mis. `claude-sonnet-4-6`).
- **URL/endpoint error** → pastiin `API_BASE_URL` bener.
- **`can't parse entities`** → udah di-handle (auto fallback ke teks).
- **401 Unauthorized** → cek API key & saldo akun.

## Mode Grup

Matikan **Group Privacy** bot di @BotFather biar bot bisa baca semua pesan grup.

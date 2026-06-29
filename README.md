# 🤖 Lexus-Agent-V1 — AI Agent Telegram via Conduit (Termux-Ready)

AI Agent Bot Telegram bertenaga **Conduit (conduit.ozdoev.net)** dengan output bergaya _coding-vibes_ ala **Claude / Fable 5 / Mythos**. Ringan, tanpa kompilasi Rust, dan siap dijalankan di **Termux** maupun VPS.

> ⚙️ Bot ini memanggil API Conduit langsung via `requests` (bukan SDK `openai`), sehingga **terhindar dari error build `jiter` / `pydantic-core`** di Termux.

---

## ⚡ Fitur Utama
1. **🧠 Memori Percakapan** — mengingat konteks obrolan multi-turn.
2. **🔄 Multi-model Switcher** — ganti model AI langsung dari chat (`/model <nama>`).
3. **🖼️ Vision** — kirim **foto** lalu ajukan pertanyaan tentang gambar tersebut.
4. **🌊 Streaming Respons** — jawaban tampil real-time, bisa di-toggle via `/stream`.
5. **👥 Mode Grup** — bekerja di grup; panggil bot dengan `@mention` atau balas pesannya.
6. **✨ Output Rapi** — persona "Lexus" memformat jawaban dengan judul, poin, dan blok kode bertanda bahasa.
7. **📊 Analisa Teknikal TradingView** — sinyal BUY/SELL/NEUTRAL via `/ta SYMBOL`.
8. **💰 Harga Real-Time** — harga & statistik 24 jam dari Binance via `/price SYMBOL`.

---

## 📲 Panduan Instalasi di Termux

### 1. Update & Instal Dependensi Sistem
```bash
pkg update && pkg upgrade -y
pkg install python git -y
```

### 2. Kloning Repositori
```bash
git clone https://github.com/sixdevilxd/Lexus-Agent-V1.git
cd Lexus-Agent-V1
```

### 3. Virtual Environment (Direkomendasikan)
```bash
python -m venv venv
source venv/bin/activate
```

### 4. Instal Package Python
```bash
pip install -r requirements.txt
```

### 5. Konfigurasi `.env`
```bash
cp .env.example .env
nano .env
```
Isi kredensial:
- `TELEGRAM_BOT_TOKEN` — dari [@BotFather](https://t.me/BotFather).
- `CONDUIT_API_KEY` — API Key Conduit Anda.

Simpan di nano: `CTRL+O` → `ENTER`, keluar `CTRL+X`.

### 6. Jalankan Bot
```bash
python bot.py
```

---

## ⚠️ Troubleshooting

**Error `No scheme supplied` atau URL `.../api/v/v1/...`?**
Pastikan `CONDUIT_BASE_URL` di `.env` Anda **persis**:
```
CONDUIT_BASE_URL=https://conduit.ozdoev.net/api/v1
```
Wajib diawali `https://` dan diakhiri `/api/v1` (bukan `/api/v`).

---

## ⚠️ Troubleshooting Termux

**Error `Failed to build 'jiter'` / `pydantic-core` saat `pip install`?**
Itu terjadi jika memakai SDK `openai` (butuh kompilasi Rust). Repo ini **sudah tidak memakainya** — pastikan `requirements.txt` Anda mutakhir (`git pull`). Jika tetap perlu Rust untuk paket lain:
```bash
pkg install rust binutils -y
```

---

## 🛠️ Perintah Bot
| Perintah | Fungsi |
|----------|--------|
| `/start` / `/help` | Panduan & daftar fitur |
| `/model [nama]` | Lihat / ganti model AI |
| `/stream` | Nyalakan / matikan streaming |
| `/clear` | Hapus memori percakapan |
| `/ta SYMBOL [TF]` | Analisa teknikal TradingView |
| `/price SYMBOL` | Harga real-time (Binance) |

**Contoh ganti model:** `/model openai/gpt-5-mini`

**Contoh trading:**
```
/ta BTCUSDT 4h
/ta AAPL 1d NASDAQ america
/price SOLUSDT
```

---

## 📁 Struktur Proyek
```
Lexus-Agent-V1/
├── bot.py             # Logika utama bot (handler, vision, streaming, grup)
├── conduit_client.py  # Client Conduit ringan (requests, tanpa Rust)
├── market.py          # TradingView TA + harga Binance real-time
├── utils.py           # Helper render pesan (Markdown fallback + split)
├── config.py          # Konfigurasi & validasi kredensial
├── requirements.txt   # Dependensi Python (ringan, Termux-friendly)
├── .env.example       # Template kredensial
├── .gitignore         # Proteksi .env
└── README.md          # Dokumentasi ini
```

---

## 👥 Catatan Mode Grup
Agar bot membaca pesan grup (bukan hanya perintah), matikan **Group Privacy** di [@BotFather](https://t.me/BotFather):
`/mybots` → pilih bot → *Bot Settings* → *Group Privacy* → **Turn off**.

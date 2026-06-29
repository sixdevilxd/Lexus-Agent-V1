# 🤖 Lexus-Agent-V1 — AI Agent Telegram via Conduit (Termux-Ready)

Repository ini berisi kode untuk menjalankan AI Agent Bot Telegram yang ditenagai oleh **Conduit (conduit.ozdoev.net)**. Bot ini dirancang sangat ringan, handal, dan dapat dijalankan dengan mudah menggunakan **Termux** di ponsel Android maupun server/VPS.

---

## ⚡ Fitur Utama
1. **Multi-model Switcher**: Ganti model AI (Claude Sonnet, GPT-5, o4, dll.) secara langsung dari Telegram dengan perintah `/model <nama_model>`.
2. **Context Memory**: Mengingat riwayat percakapan Anda sehingga obrolan mengalir secara kontekstual.
3. **Termux Optimized**: Desain program sangat efisien, bebas dari library berat, dan mudah diinstal di HP Android.
4. **Keamanan Kunci**: Menggunakan berkas `.env` untuk menyimpan token agar API Key Anda tetap aman dari publikasi publik.

---

## 📲 Panduan Instalasi & Menjalankan di Termux

Buka aplikasi Termux di Android Anda, lalu ikuti langkah-langkah berikut:

### 1. Update Termux & Instal Dependensi Sistem
Pastikan Termux Anda mutakhir dan memiliki Python serta Git:
```bash
pkg update && pkg upgrade -y
pkg install python git -y
```

### 2. Kloning Repositori Ini
```bash
git clone https://github.com/sixdevilxd/Lexus-Agent-V1.git
cd Lexus-Agent-V1
```
*(Catatan: Ganti `sixdevilxd` dengan username GitHub Anda)*

### 3. Buat & Aktifkan Virtual Environment (Sangat Direkomendasikan)
Guna menghindari konflik package global:
```bash
python -m venv venv
source venv/bin/activate
```

### 4. Instal Package Python yang Dibutuhkan
```bash
pip install -r requirements.txt
```

### 5. Konfigurasi Variabel Lingkungan (.env)
Salin berkas contoh konfigurasi ke berkas `.env` aktif:
```bash
cp .env.example .env
```
Gunakan text editor bawaan Termux seperti `nano` untuk mengedit kredensial Anda:
```bash
nano .env
```
Masukkan token Anda pada baris berikut:
- `TELEGRAM_BOT_TOKEN`: Dapatkan dari [@BotFather](https://t.me/BotFather) di Telegram.
- `CONDUIT_API_KEY`: API Key Conduit Anda yang bersumber dari `conduit.ozdoev.net`.

*Simpan berkas di nano dengan menekan `CTRL + O`, lalu `ENTER`. Keluar dengan `CTRL + X`.*

### 6. Jalankan Bot Anda!
```bash
python bot.py
```

---

## 🛠️ Perintah Bot Telegram
* `/start` / `/help` : Memulai bot dan menampilkan panduan.
* `/model` : Melihat model aktif atau beralih model (contoh: `/model openai/gpt-5-mini`).
* `/clear` : Menghapus memori riwayat obrolan agar percakapan dimulai ulang dari awal.

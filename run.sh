#!/data/data/com.termux/files/usr/bin/bash
# run.sh - Menjalankan Lexus-Agent-V1 24/7 di Termux
# Fitur: Wake-lock (cegah CPU tidur) + Auto-restart (jika bot crash)

# Cegah Android mematikan proses saat layar mati
termux-wake-lock

# Pindah ke direktori skrip ini berada
cd "$(dirname "$0")"

# Aktifkan virtual environment jika ada
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "=========================================="
echo " Lexus-Agent-V1 berjalan dalam mode 24/7  "
echo "=========================================="

# Loop tak terbatas: jika bot mati/crash, otomatis dinyalakan lagi
while true; do
    echo "[$(date)] Menyalakan bot..."
    python bot.py
    echo "[$(date)] Bot berhenti. Menyalakan ulang dalam 5 detik..."
    sleep 5
done

"""Rate limiter sederhana berbasis sliding-window per pengguna.
Mencegah spam yang bisa menguras kredit Conduit API."""
import time

# Maksimal 20 pesan per 60 detik per pengguna (bisa disesuaikan)
LIMIT = 20
WINDOW = 60

_calls = {}


def allowed(chat_id):
    """Return True bila pengguna masih boleh kirim pesan, False bila kena limit."""
    now = time.time()
    arr = [t for t in _calls.get(chat_id, []) if now - t < WINDOW]
    if len(arr) >= LIMIT:
        _calls[chat_id] = arr
        return False
    arr.append(now)
    _calls[chat_id] = arr
    return True

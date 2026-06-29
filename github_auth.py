import requests
import time
import threading
from config import GITHUB_CLIENT_ID

def initiate_device_flow():
    """
    Langkah 1: Meminta kode otentikasi perangkat ke GitHub.
    Scope 'repo' memberi akses baca/tulis ke repositori publik & privat milik user.
    """
    url = "https://github.com/login/device/code"
    payload = {
        "client_id": GITHUB_CLIENT_ID,
        "scope": "repo write:discussion gist"
    }
    headers = {"Accept": "application/json"}

    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def poll_for_token(device_code, interval, callback_success, callback_failed, chat_id):
    """
    Langkah 2: Melakukan polling ke GitHub sampai user memasukkan kode di web.
    Dijalankan di thread terpisah agar bot Telegram tidak macet.
    """
    url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": GITHUB_CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
    }
    headers = {"Accept": "application/json"}

    while True:
        time.sleep(interval)
        try:
            response = requests.post(url, data=payload, headers=headers)
            res_data = response.json()

            if "access_token" in res_data:
                callback_success(chat_id, res_data["access_token"])
                break

            error = res_data.get("error")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval += 5
            elif error in ["expired_token", "access_denied"]:
                callback_failed(chat_id, error)
                break
            else:
                callback_failed(chat_id, f"Unknown error: {error}")
                break
        except Exception as e:
            callback_failed(chat_id, str(e))
            break


def start_auth_session(chat_id, send_message_func, save_token_func):
    """
    Memulai sesi otentikasi untuk pengguna tertentu.
    """
    try:
        flow_data = initiate_device_flow()
        user_code = flow_data["user_code"]
        verification_uri = flow_data["verification_uri"]
        device_code = flow_data["device_code"]
        interval = flow_data.get("interval", 5)

        msg_text = (
            f"🔑 *Hubungkan ke GitHub Anda*\n\n"
            f"1. Buka halaman ini: {verification_uri}\n"
            f"2. Masukkan kode unik ini:\n"
            f"   👉 ` {user_code} ` 👈 *(Ketuk untuk salin)*\n\n"
            f"⏳ _Bot sedang menunggu persetujuan Anda..._"
        )
        send_message_func(chat_id, msg_text)

        def on_success(cid, token):
            save_token_func(cid, token)
            send_message_func(cid, "✅ *Koneksi Berhasil!* Akun GitHub Anda sekarang terhubung dengan Lexus Agent.")

        def on_failed(cid, error_msg):
            send_message_func(cid, f"❌ *Koneksi Gagal / Batal.*\nDetail: `{error_msg}`")

        t = threading.Thread(
            target=poll_for_token, 
            args=(device_code, interval, on_success, on_failed, chat_id)
        )
        t.daemon = True
        t.start()

    except Exception as e:
        send_message_func(chat_id, f"❌ Gagal memulai sesi login GitHub: {str(e)}")

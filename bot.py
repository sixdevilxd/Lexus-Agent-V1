import time
import base64
import json
import logging
import telebot
from config import TELEGRAM_BOT_TOKEN, DEFAULT_MODEL, MAX_HISTORY, STREAM_ENABLED, GITHUB_CLIENT_ID
import github_auth
import github_db
import github_client
import conduit_client
import market
import research
from utils import send_long_message, edit_safe, split_text, safe_send, safe_reply

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
BOT_USERNAME = bot.get_me().username

github_db.init_db()  # Inisialisasi database token GitHub

chat_history = {}
chat_models = {}

SYSTEM_PROMPT = (
    "Namamu adalah *Lexus*, AI Agent Telegram eksklusif dengan estetika coding-vibes "
    "terinspirasi gaya Claude, Fable 5, dan Mythos.\n\n"
    "ATURAN IDENTITAS (WAJIB):\n"
    "- Kamu BUKAN 'Claude Code', BUKAN CLI, BUKAN asisten resmi Anthropic/OpenAI. Kamu Lexus.\n"
    "- SELALU balas dalam Bahasa Indonesia, kecuali user jelas memakai bahasa lain.\n\n"
    "RISET INTERNET:\n"
    "- Kamu punya alat: web_search, fetch_url, reddit_search, social_search.\n"
    "- Gunakan alat saat butuh info terkini/faktual (berita, harga, tren, profil, dll).\n"
    "- Setelah meriset, RINGKAS temuan dengan jelas dan SEBUTKAN sumber (judul + link).\n\n"
    "ATURAN FORMAT (Telegram Markdown):\n"
    "- Buka dengan judul tebal + emoji yang sesuai topik.\n"
    "- Pakai poin/langkah bernomor bila membantu.\n"
    "- SELALU bungkus kode dalam blok kode bertanda bahasa (```python, ```bash).\n"
    "- Pakai `inline code` untuk perintah, file, variabel, nilai.\n"
    "- Ringkas, elegan, dan bergaya. Akhiri dengan saran langkah berikutnya bila relevan."
)

EXAMPLE_MODELS = (
    "\u2022 `claude-opus-4-8`\n"
    "\u2022 `claude-sonnet-4-6`\n"
    "\u2022 `gpt-5`\n"
    "\u2022 `gpt-5-mini`\n"
    "\u2022 `gemini-3-pro`"
)

# ---------------- Tool definitions (OpenAI function-calling schema) ----------------
TOOLS = [
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Cari informasi terkini di internet (berita, fakta, harga, tren, dsb).",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Kata kunci pencarian"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "fetch_url",
        "description": "Ambil dan baca isi teks dari sebuah URL/halaman web.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "reddit_search",
        "description": "Cari diskusi/postingan di Reddit beserta skor & komentar.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "social_search",
        "description": "Riset media sosial (X/Twitter, Facebook, Instagram, Reddit, TikTok, YouTube, LinkedIn).",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
            "platform": {"type": "string",
                         "enum": ["x", "twitter", "facebook", "instagram", "reddit", "tiktok", "youtube", "linkedin"]}},
            "required": ["query", "platform"]}}},
    {"type": "function", "function": {
        "name": "github_read_file",
        "description": "Membaca isi file teks dari repositori GitHub pengguna (user harus login dulu).",
        "parameters": {"type": "object", "properties": {
            "repo_owner": {"type": "string", "description": "Username pemilik repositori"},
            "repo_name": {"type": "string", "description": "Nama repositori"},
            "file_path": {"type": "string", "description": "Path file lengkap (contoh: 'src/main.py')"},
            "branch": {"type": "string", "description": "Branch file (default: 'main')", "default": "main"}},
            "required": ["repo_owner", "repo_name", "file_path"]}}},
    {"type": "function", "function": {
        "name": "github_push_file",
        "description": "Membuat commit baru atau mengupdate file teks di repositori GitHub pengguna (user harus login dulu).",
        "parameters": {"type": "object", "properties": {
            "repo_owner": {"type": "string", "description": "Username pemilik repositori"},
            "repo_name": {"type": "string", "description": "Nama repositori"},
            "file_path": {"type": "string", "description": "Path file lengkap (contoh: 'src/main.py')"},
            "file_content": {"type": "string", "description": "Isi kode atau teks baru dalam file"},
            "commit_message": {"type": "string", "description": "Pesan commit"},
            "branch": {"type": "string", "description": "Branch tujuan (default: 'main')", "default": "main"}},
            "required": ["repo_owner", "repo_name", "file_path", "file_content", "commit_message"]}}},
]


def dispatch(fn, args):
    if fn == "web_search":
        return research.web_search(args.get("query", ""))
    if fn == "fetch_url":
        return research.fetch_url(args.get("url", ""))
    if fn == "reddit_search":
        return research.reddit_search(args.get("query", ""))
    if fn == "social_search":
        return research.social_search(args.get("query", ""), args.get("platform", "x"))
    return {"error": f"unknown tool {fn}"}


def should_respond(message):
    if message.chat.type == "private":
        return True
    text = message.text or message.caption or ""
    if BOT_USERNAME and ("@" + BOT_USERNAME) in text:
        return True
    if message.reply_to_message and message.reply_to_message.from_user \
            and message.reply_to_message.from_user.username == BOT_USERNAME:
        return True
    return False


def clean_mention(text):
    if not text:
        return text
    return text.replace("@" + BOT_USERNAME, "").strip() if BOT_USERNAME else text


# ---------------- Commands ----------------
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    txt = (
        "\u2728 *Lexus-Agent-V1* \u2014 AI Agent siap melayani\n\n"
        "Ditenagai *Conduit* + riset internet otonom, output bergaya coding-vibes.\n\n"
        "\u26a1 *Kemampuan:*\n"
        "\U0001f9e0 Chat AI multi-turn  \u00b7  \U0001f5bc\ufe0f Vision (kirim foto)\n"
        "\U0001f50d Web search  \u00b7  \U0001f4f1 Riset sosmed (X/FB/IG/Reddit)\n"
        "\U0001f4ca Analisa teknikal  \u00b7  \U0001f4b0 Harga real-time\n\n"
        "\U0001f916 *Perintah:*\n"
        "\u2022 `/model` \u2014 lihat / ganti model\n"
        "\u2022 `/search <kata>` \u2014 cari di internet\n"
        "\u2022 `/reddit <kata>` \u2014 riset Reddit\n"
        "\u2022 `/social <platform> <kata>` \u2014 riset sosmed\n"
        "\u2022 `/web <url>` \u2014 baca isi halaman\n"
        "\u2022 `/ta SYMBOL` \u2014 analisa teknikal\n"
        "\u2022 `/price SYMBOL` \u2014 harga real-time\n"
        "\u2022 `/tools` \u2014 nyalakan/matikan riset otonom\n"
        "\u2022 `/stream` \u2014 streaming (saat tools off)\n"
        "\u2022 `/clear` \u2014 hapus riwayat\n\n"
        "_Cukup tanya biasa \u2014 aku otomatis mencari di internet bila perlu._"
    )
    safe_send(bot, message.chat.id, txt)


@bot.message_handler(commands=["model"])
def manage_model(message):
    chat_id = message.chat.id
    current = chat_models.get(chat_id, DEFAULT_MODEL)
    args = (message.text or "").split()
    if len(args) > 1:
        m = conduit_client.normalize_model(args[1])
        chat_models[chat_id] = m
        safe_reply(bot, message, f"\u2705 *Model diganti ke:* `{m}`")
    else:
        safe_reply(bot, message,
                   f"\U0001f916 *Model aktif:* `{current}`\n\nGanti dengan `/model <nama>`\n\n"
                   f"\U0001f4a1 *Gunakan id POLOS (tanpa `anthropic/` atau `openai/`):*\n{EXAMPLE_MODELS}")


@bot.message_handler(commands=["tools"])
def toggle_tools(message):
    chat_id = message.chat.id
    cur = chat_history.get("_tools_" + str(chat_id), True)
    chat_history["_tools_" + str(chat_id)] = not cur
    state = "AKTIF \U0001f50d" if not cur else "NONAKTIF"
    safe_reply(bot, message, f"\u2699\ufe0f *Riset internet otonom:* {state}")


@bot.message_handler(commands=["stream"])
def toggle_stream(message):
    chat_id = message.chat.id
    cur = chat_history.get("_stream_" + str(chat_id), STREAM_ENABLED)
    chat_history["_stream_" + str(chat_id)] = not cur
    state = "AKTIF \U0001f30a" if not cur else "NONAKTIF"
    safe_reply(bot, message, f"\u2699\ufe0f *Streaming:* {state} _(berlaku saat tools off)_")


@bot.message_handler(commands=["clear"])
def clear_history(message):
    chat_history[message.chat.id] = []
    safe_reply(bot, message, "\U0001f9f9 *Riwayat percakapan dibersihkan!*")


@bot.message_handler(commands=["search"])
def cmd_search(message):
    q = (message.text or "").split(maxsplit=1)
    if len(q) < 2:
        safe_reply(bot, message, "\U0001f50d Format: `/search <kata kunci>`")
        return
    _research_and_reply(message, f"Cari di internet dan ringkas: {q[1]}")


@bot.message_handler(commands=["reddit"])
def cmd_reddit(message):
    q = (message.text or "").split(maxsplit=1)
    if len(q) < 2:
        safe_reply(bot, message, "\U0001f47d Format: `/reddit <kata kunci>`")
        return
    _research_and_reply(message, f"Riset Reddit tentang: {q[1]}. Gunakan reddit_search lalu ringkas.")


@bot.message_handler(commands=["social"])
def cmd_social(message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        safe_reply(bot, message, "\U0001f4f1 Format: `/social <platform> <kata>`\nContoh: `/social x bitcoin etf`")
        return
    _research_and_reply(message, f"Riset sosmed platform '{parts[1]}' tentang: {parts[2]}. Gunakan social_search lalu ringkas.")


@bot.message_handler(commands=["web"])
def cmd_web(message):
    q = (message.text or "").split(maxsplit=1)
    if len(q) < 2:
        safe_reply(bot, message, "\U0001f310 Format: `/web <url>`")
        return
    _research_and_reply(message, f"Baca halaman ini dengan fetch_url lalu ringkas isinya: {q[1]}")


@bot.message_handler(commands=["ta"])
def cmd_ta(message):
    args = (message.text or "").split()
    if len(args) < 2:
        safe_reply(bot, message,
                   "\U0001f4ca *Analisa Teknikal TradingView*\n\n"
                   "Format: `/ta SYMBOL [TF] [EXCHANGE] [SCREENER]`\n\n"
                   "*Contoh:*\n\u2022 `/ta BTCUSDT`\n\u2022 `/ta ETHUSDT 4h`\n\u2022 `/ta AAPL 1d NASDAQ america`\n\n"
                   "TF: `1m 5m 15m 30m 1h 2h 4h 1d 1w 1M`")
        return
    symbol = args[1]
    interval = args[2] if len(args) > 2 else "1h"
    exchange = args[3] if len(args) > 3 else "BINANCE"
    screener = args[4] if len(args) > 4 else "crypto"
    bot.send_chat_action(message.chat.id, "typing")
    try:
        safe_reply(bot, message, market.get_ta(symbol, interval, exchange, screener))
    except Exception as e:
        logging.error(f"TA error: {e}")
        safe_reply(bot, message, f"\u274c Gagal ambil analisa untuk `{symbol}`:\n`{e}`")


@bot.message_handler(commands=["price"])
def cmd_price(message):
    args = (message.text or "").split()
    if len(args) < 2:
        safe_reply(bot, message, "\U0001f4b0 *Harga Real-Time (Binance)*\n\nFormat: `/price SYMBOL`\n\n*Contoh:* `/price BTCUSDT`")
        return
    bot.send_chat_action(message.chat.id, "typing")
    try:
        safe_reply(bot, message, market.get_price(args[1]))
    except Exception as e:
        logging.error(f"Price error: {e}")
        safe_reply(bot, message, f"\u274c Gagal ambil harga `{args[1]}`:\n`{e}`")


# ---------------- Core chat ----------------
def get_history(chat_id):
    return chat_history.setdefault(chat_id, [])


def remember(chat_id, user_content, reply):
    history = get_history(chat_id)
    if isinstance(user_content, list):
        text_part = " ".join(p.get("text", "") for p in user_content if p.get("type") == "text")
        user_store = text_part + " [gambar dilampirkan]"
    else:
        user_store = user_content
    history.append({"role": "user", "content": user_store})
    history.append({"role": "assistant", "content": reply})
    if len(history) > MAX_HISTORY * 2:
        chat_history[chat_id] = history[-(MAX_HISTORY * 2):]


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    if not should_respond(message):
        return
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, "typing")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        caption = clean_mention(message.caption) or "Jelaskan gambar ini secara detail."
        user_content = [
            {"type": "text", "text": caption},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ]
        # vision -> plain chat (no tools)
        model = chat_models.get(chat_id, DEFAULT_MODEL)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(chat_id) + [
            {"role": "user", "content": user_content}]
        reply = conduit_client.chat(model, messages)
        send_long_message(bot, chat_id, reply, reply_to=message.message_id)
        remember(chat_id, user_content, reply)
    except Exception as e:
        logging.error(f"Photo error: {e}")
        safe_reply(bot, message, f"\u274c Gagal memproses gambar:\n`{e}`")


@bot.message_handler(commands=["login_github"])
def handle_login_github(message):
    chat_id = message.chat.id
    if not GITHUB_CLIENT_ID:
        safe_reply(bot, message, "⚠️ *Fitur login GitHub belum dikonfigurasi.*\n\nSilakan daftarkan OAuth App Anda di GitHub dan atur `GITHUB_CLIENT_ID` di file `.env` terlebih dahulu.")
        return

    existing_token = github_db.get_token(chat_id)
    if existing_token:
        bot.reply_to(message, "ℹ️ Akun Anda *sudah terhubung* ke GitHub. Gunakan `/logout_github` jika ingin memutuskan koneksi.")
        return

    def send_msg(cid, text):
        bot.send_message(cid, text, parse_mode="Markdown")

    github_auth.start_auth_session(chat_id, send_msg, github_db.save_token)


@bot.message_handler(commands=["logout_github"])
def handle_logout_github(message):
    chat_id = message.chat.id
    github_db.delete_token(chat_id)
    bot.reply_to(message, "🗑️ Koneksi GitHub Anda berhasil diputuskan.")


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not should_respond(message):
        return
    user_text = clean_mention(message.text)
    if not user_text:
        return
    process_and_reply(message, user_text)


def process_and_reply(message, user_text):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, "typing")
    model = chat_models.get(chat_id, DEFAULT_MODEL)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(chat_id) + [
        {"role": "user", "content": user_text}]

    tools_on = chat_history.get("_tools_" + str(chat_id), True)
    streaming = chat_history.get("_stream_" + str(chat_id), STREAM_ENABLED)
    try:
        if tools_on:
            reply = agentic_reply(message, model, messages)
        elif streaming:
            reply = stream_reply(message, model, messages)
        else:
            reply = conduit_client.chat(model, messages)
            send_long_message(bot, chat_id, reply, reply_to=message.message_id)
        remember(chat_id, user_text, reply)
    except Exception as e:
        logging.error(f"API error: {e}")
        safe_reply(bot, message, f"\u274c *Gagal memproses permintaan:*\n\n`{e}`")


def _research_and_reply(message, instruction):
    """Force a research-style turn (used by /search, /reddit, /social, /web)."""
    chat_id = message.chat.id
    model = chat_models.get(chat_id, DEFAULT_MODEL)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(chat_id) + [
        {"role": "user", "content": instruction}]
    try:
        reply = agentic_reply(message, model, messages)
        remember(chat_id, instruction, reply)
    except Exception as e:
        logging.error(f"Research error: {e}")
        safe_reply(bot, message, f"\u274c *Gagal riset:*\n\n`{e}`")


def agentic_reply(message, model, messages):
    chat_id = message.chat.id
    sent = bot.send_message(chat_id, "\U0001f4ad _thinking..._", parse_mode="Markdown",
                            reply_to_message_id=message.message_id)

    labels = {"web_search": "\U0001f50d mencari di internet",
              "fetch_url": "\U0001f4c4 membaca halaman",
              "reddit_search": "\U0001f47d riset Reddit",
              "social_search": "\U0001f4f1 riset sosmed"}

    def dispatch_with_progress(fn, args):
        if fn in ["github_read_file", "github_push_file"]:
            token = github_db.get_token(chat_id)
            if not token:
                return {
                    "status": "error",
                    "message": "Maaf, Anda belum menghubungkan akun GitHub ke bot Lexus ini. Silakan gunakan perintah /login_github terlebih dahulu di aplikasi Telegram Anda."
                }
            repo = f"{args.get('repo_owner')}/{args.get('repo_name')}"
            path = args.get('file_path', '')
            if fn == "github_read_file":
                edit_safe(bot, chat_id, sent.message_id, f"📖 Membaca file GitHub: {repo}/{path} ...", markdown=False)
                return github_client.read_file(token, args.get('repo_owner'), args.get('repo_name'), path, args.get('branch', 'main'))
            else:
                edit_safe(bot, chat_id, sent.message_id, f"🚀 Push commit ke GitHub: {repo}/{path} ...", markdown=False)
                return github_client.commit_and_push_file(token, args.get('repo_owner'), args.get('repo_name'), path, args.get('file_content', ''), args.get('commit_message', 'update via Lexus Agent'), args.get('branch', 'main'))

        q = args.get("query") or args.get("url") or args.get("platform") or ""
        edit_safe(bot, chat_id, sent.message_id, f"{labels.get(fn, 'memproses')}: {q} ...", markdown=False)
        bot.send_chat_action(chat_id, "typing")
        return dispatch(fn, args)

    reply = conduit_client.chat_with_tools(model, messages, TOOLS, dispatch_with_progress)
    reply = reply or "_(tidak ada jawaban)_"
    parts = split_text(reply)
    edit_safe(bot, chat_id, sent.message_id, parts[0])
    for extra in parts[1:]:
        safe_send(bot, chat_id, extra)
    return reply


def stream_reply(message, model, messages):
    chat_id = message.chat.id
    sent = bot.send_message(chat_id, "\U0001f4ad _thinking..._", parse_mode="Markdown",
                            reply_to_message_id=message.message_id)
    buffer = ""
    last_edit = time.time()
    for delta in conduit_client.chat_stream(model, messages):
        buffer += delta
        if time.time() - last_edit > 1.3 and buffer.strip():
            edit_safe(bot, chat_id, sent.message_id, buffer + " \u258c", markdown=False)
            last_edit = time.time()
    parts = split_text(buffer)
    edit_safe(bot, chat_id, sent.message_id, parts[0])
    for extra in parts[1:]:
        safe_send(bot, chat_id, extra)
    return buffer


if __name__ == "__main__":
    logging.info(f"Lexus-Agent-V1 starting as @{BOT_USERNAME} ...")
    bot.infinity_polling(skip_pending=True)

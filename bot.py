import os
import time
import base64
import logging
import telebot
from openai import OpenAI
from config import (
    TELEGRAM_BOT_TOKEN, CONDUIT_API_KEY, CONDUIT_BASE_URL,
    DEFAULT_MODEL, MAX_HISTORY, STREAM_ENABLED
)
from utils import send_long_message, edit_safe, split_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = OpenAI(api_key=CONDUIT_API_KEY, base_url=CONDUIT_BASE_URL)
BOT_USERNAME = bot.get_me().username

# Per-chat state
chat_history = {}
chat_models = {}

# ── "Mythos" coding-vibes persona ──────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Lexus, an elite AI agent with refined coding-vibes aesthetics inspired by "
    "Claude, Fable 5, and the Mythos style. Always respond with crisp, well-structured output.\n\n"
    "FORMATTING RULES (Telegram Markdown):\n"
    "- Open with a short bold title line using an emoji that fits the topic.\n"
    "- Use clear sections, bullet points, and numbered steps when helpful.\n"
    "- ALWAYS wrap any code in fenced code blocks with the correct language tag (```python, ```bash, ```js).\n"
    "- Use `inline code` for commands, filenames, variables, and values.\n"
    "- Keep prose tight and elegant; no rambling. End with a subtle next-step hint when relevant.\n"
    "- Answer in the user\'s language (default Bahasa Indonesia if unclear).\n"
    "Be accurate, helpful, and stylish."
)

EXAMPLE_MODELS = (
    "• `anthropic/claude-sonnet-4-6`\n"
    "• `anthropic/claude-opus-4-8`\n"
    "• `openai/gpt-5`\n"
    "• `openai/gpt-5-mini`\n"
    "• `openai/o4`"
)


def should_respond(message):
    """In private chat always; in groups only when mentioned or replied to."""
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


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    txt = (
        "✨ *Lexus\\-Agent\\-V1* — AI Agent siap melayani\n\n"
        "Ditenagai *Conduit* dengan output bergaya _coding\\-vibes_ ala Claude / Fable 5 / Mythos\\.\n\n"
        "⚡ *Fitur:*\n"
        "1\\. 🧠 Memori percakapan multi\\-turn\n"
        "2\\. 🔄 Ganti model langsung dari chat\n"
        "3\\. 🖼️ Vision — kirim *foto* lalu tanya apa saja\n"
        "4\\. 🌊 Streaming respons real\\-time\n"
        "5\\. 👥 Mode grup \\(panggil dengan @mention\\)\n\n"
        "🤖 *Perintah:*\n"
        "• `/model` — lihat / ganti model\n"
        "• `/stream` — nyalakan/matikan streaming\n"
        "• `/clear` — hapus riwayat\n"
    )
    bot.send_message(message.chat.id, txt, parse_mode="MarkdownV2")


@bot.message_handler(commands=["model"])
def manage_model(message):
    chat_id = message.chat.id
    current = chat_models.get(chat_id, DEFAULT_MODEL)
    args = (message.text or "").split()
    if len(args) > 1:
        chat_models[chat_id] = args[1]
        bot.reply_to(message, f"✅ *Model diganti ke:* `{args[1]}`", parse_mode="Markdown")
    else:
        bot.reply_to(
            message,
            f"🤖 *Model aktif:* `{current}`\n\nGanti dengan `/model <nama>`\n\n"
            f"💡 *Contoh model Conduit:*\n{EXAMPLE_MODELS}",
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["stream"])
def toggle_stream(message):
    chat_id = message.chat.id
    cur = chat_history.get("_stream_" + str(chat_id), STREAM_ENABLED)
    chat_history["_stream_" + str(chat_id)] = not cur
    state = "AKTIF 🌊" if not cur else "NONAKTIF"
    bot.reply_to(message, f"⚙️ *Streaming sekarang:* {state}", parse_mode="Markdown")


@bot.message_handler(commands=["clear"])
def clear_history(message):
    chat_history[message.chat.id] = []
    bot.reply_to(message, "🧹 *Riwayat percakapan dibersihkan\\!*", parse_mode="MarkdownV2")


def get_history(chat_id):
    return chat_history.setdefault(chat_id, [])


def run_completion(chat_id, user_content):
    """Build payload, call Conduit, return (full_text, generator_or_none)."""
    model = chat_models.get(chat_id, DEFAULT_MODEL)
    history = get_history(chat_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": user_content}
    ]
    streaming = chat_history.get("_stream_" + str(chat_id), STREAM_ENABLED)
    return model, messages, streaming


def remember(chat_id, user_content, reply):
    history = get_history(chat_id)
    # store only text form of user content for memory
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
        process_and_reply(message, user_content)
    except Exception as e:
        logging.error(f"Photo error: {e}")
        bot.reply_to(message, f"❌ Gagal memproses gambar:\n`{e}`", parse_mode="Markdown")


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not should_respond(message):
        return
    user_text = clean_mention(message.text)
    if not user_text:
        return
    process_and_reply(message, user_text)


def process_and_reply(message, user_content):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, "typing")
    model, messages, streaming = run_completion(chat_id, user_content)
    try:
        logging.info(f"Conduit call | chat={chat_id} | model={model} | stream={streaming}")
        if streaming:
            reply = stream_reply(message, model, messages)
        else:
            resp = client.chat.completions.create(model=model, messages=messages, stream=False)
            reply = resp.choices[0].message.content
            send_long_message(bot, chat_id, reply, reply_to=message.message_id)
        remember(chat_id, user_content, reply)
    except Exception as e:
        logging.error(f"API error: {e}")
        bot.reply_to(message, f"❌ *Gagal memproses permintaan:*\n\n`{e}`", parse_mode="Markdown")


def stream_reply(message, model, messages):
    chat_id = message.chat.id
    sent = bot.send_message(chat_id, "🌊 _menyusun jawaban..._", parse_mode="Markdown",
                            reply_to_message_id=message.message_id)
    buffer = ""
    last_edit = time.time()
    stream = client.chat.completions.create(model=model, messages=messages, stream=True)
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        buffer += delta
        if time.time() - last_edit > 1.3 and buffer.strip():
            edit_safe(bot, chat_id, sent.message_id, buffer + " ▌")
            last_edit = time.time()
    # final render (handle >4096 by splitting)
    parts = split_text(buffer)
    edit_safe(bot, chat_id, sent.message_id, parts[0])
    for extra in parts[1:]:
        bot.send_message(chat_id, extra, parse_mode="Markdown")
    return buffer


if __name__ == "__main__":
    logging.info(f"Lexus-Agent-V1 starting as @{BOT_USERNAME} ...")
    bot.infinity_polling(skip_pending=True)

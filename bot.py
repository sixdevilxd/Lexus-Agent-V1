import os
import time
import base64
import logging
import telebot
from config import (
    TELEGRAM_BOT_TOKEN, DEFAULT_MODEL, MAX_HISTORY, STREAM_ENABLED
)
import conduit_client
import market
from utils import send_long_message, edit_safe, split_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
BOT_USERNAME = bot.get_me().username

# Per-chat state
chat_history = {}
chat_models = {}

# \u2500\u2500 "Mythos" coding-vibes persona \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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
    "\u2022 `anthropic/claude-sonnet-4-6`\n"
    "\u2022 `anthropic/claude-opus-4-8`\n"
    "\u2022 `openai/gpt-5`\n"
    "\u2022 `openai/gpt-5-mini`\n"
    "\u2022 `openai/o4`"
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
        "\u2728 *Lexus\\-Agent\\-V1* \u2014 AI Agent siap melayani\n\n"
        "Ditenagai *Conduit* dengan output bergaya _coding\\-vibes_ ala Claude / Fable 5 / Mythos\\.\n\n"
        "\u26a1 *Fitur:*\n"
        "1\\. \U0001f9e0 Memori percakapan multi\\-turn\n"
        "2\\. \U0001f504 Ganti model langsung dari chat\n"
        "3\\. \U0001f5bc\ufe0f Vision \u2014 kirim *foto* lalu tanya apa saja\n"
        "4\\. \U0001f30a Streaming respons real\\-time\n"
        "5\\. \U0001f465 Mode grup \\(panggil dengan @mention\\)\n\n"
        "\U0001f916 *Perintah:*\n"
        "\u2022 `/model` \u2014 lihat / ganti model\n"
        "\u2022 `/stream` \u2014 nyalakan/matikan streaming\n"
        "\u2022 `/clear` \u2014 hapus riwayat\n"
        "\u2022 `/ta SYMBOL` \u2014 analisa teknikal TradingView\n"
        "\u2022 `/price SYMBOL` \u2014 harga real\\-time Binance\n"
    )
    bot.send_message(message.chat.id, txt, parse_mode="MarkdownV2")


@bot.message_handler(commands=["model"])
def manage_model(message):
    chat_id = message.chat.id
    current = chat_models.get(chat_id, DEFAULT_MODEL)
    args = (message.text or "").split()
    if len(args) > 1:
        chat_models[chat_id] = args[1]
        bot.reply_to(message, f"\u2705 *Model diganti ke:* `{args[1]}`", parse_mode="Markdown")
    else:
        bot.reply_to(
            message,
            f"\U0001f916 *Model aktif:* `{current}`\n\nGanti dengan `/model <nama>`\n\n"
            f"\U0001f4a1 *Contoh model Conduit:*\n{EXAMPLE_MODELS}",
            parse_mode="Markdown",
        )


@bot.message_handler(commands=["stream"])
def toggle_stream(message):
    chat_id = message.chat.id
    cur = chat_history.get("_stream_" + str(chat_id), STREAM_ENABLED)
    chat_history["_stream_" + str(chat_id)] = not cur
    state = "AKTIF \U0001f30a" if not cur else "NONAKTIF"
    bot.reply_to(message, f"\u2699\ufe0f *Streaming sekarang:* {state}", parse_mode="Markdown")


@bot.message_handler(commands=["clear"])
def clear_history(message):
    chat_history[message.chat.id] = []
    bot.reply_to(message, "\U0001f9f9 *Riwayat percakapan dibersihkan\\!*", parse_mode="MarkdownV2")


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


@bot.message_handler(commands=["ta"])
def cmd_ta(message):
    chat_id = message.chat.id
    args = (message.text or "").split()
    if len(args) < 2:
        bot.reply_to(
            message,
            "\U0001f4ca *Analisa Teknikal TradingView*\n\n"
            "Format: `/ta SYMBOL [TF] [EXCHANGE] [SCREENER]`\n\n"
            "*Contoh:*\n"
            "\u2022 `/ta BTCUSDT` \u2014 crypto, TF 1h (default)\n"
            "\u2022 `/ta ETHUSDT 4h`\n"
            "\u2022 `/ta AAPL 1d NASDAQ america` \u2014 saham\n\n"
            "TF: `1m 5m 15m 30m 1h 2h 4h 1d 1w 1M`",
            parse_mode="Markdown",
        )
        return
    symbol = args[1]
    interval = args[2] if len(args) > 2 else "1h"
    exchange = args[3] if len(args) > 3 else "BINANCE"
    screener = args[4] if len(args) > 4 else "crypto"
    bot.send_chat_action(chat_id, "typing")
    try:
        bot.reply_to(message, market.get_ta(symbol, interval, exchange, screener),
                     parse_mode="Markdown")
    except Exception as e:
        logging.error(f"TA error: {e}")
        bot.reply_to(message, f"\u274c Gagal ambil analisa untuk `{symbol}`:\n`{e}`",
                     parse_mode="Markdown")


@bot.message_handler(commands=["price"])
def cmd_price(message):
    chat_id = message.chat.id
    args = (message.text or "").split()
    if len(args) < 2:
        bot.reply_to(
            message,
            "\U0001f4b0 *Harga Real-Time (Binance)*\n\n"
            "Format: `/price SYMBOL`\n\n"
            "*Contoh:* `/price BTCUSDT`, `/price SOLUSDT`",
            parse_mode="Markdown",
        )
        return
    symbol = args[1]
    bot.send_chat_action(chat_id, "typing")
    try:
        bot.reply_to(message, market.get_price(symbol), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Price error: {e}")
        bot.reply_to(message, f"\u274c Gagal ambil harga `{symbol}`:\n`{e}`",
                     parse_mode="Markdown")


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
        bot.reply_to(message, f"\u274c Gagal memproses gambar:\n`{e}`", parse_mode="Markdown")


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
    model = chat_models.get(chat_id, DEFAULT_MODEL)
    history = get_history(chat_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": user_content}
    ]
    streaming = chat_history.get("_stream_" + str(chat_id), STREAM_ENABLED)
    try:
        logging.info(f"Conduit call | chat={chat_id} | model={model} | stream={streaming}")
        if streaming:
            reply = stream_reply(message, model, messages)
        else:
            reply = conduit_client.chat(model, messages)
            send_long_message(bot, chat_id, reply, reply_to=message.message_id)
        remember(chat_id, user_content, reply)
    except Exception as e:
        logging.error(f"API error: {e}")
        bot.reply_to(message, f"\u274c *Gagal memproses permintaan:*\n\n`{e}`", parse_mode="Markdown")


def stream_reply(message, model, messages):
    chat_id = message.chat.id
    sent = bot.send_message(chat_id, "\U0001f30a _menyusun jawaban..._", parse_mode="Markdown",
                            reply_to_message_id=message.message_id)
    buffer = ""
    last_edit = time.time()
    for delta in conduit_client.chat_stream(model, messages):
        buffer += delta
        if time.time() - last_edit > 1.3 and buffer.strip():
            edit_safe(bot, chat_id, sent.message_id, buffer + " \u258c")
            last_edit = time.time()
    parts = split_text(buffer)
    edit_safe(bot, chat_id, sent.message_id, parts[0])
    for extra in parts[1:]:
        bot.send_message(chat_id, extra, parse_mode="Markdown")
    return buffer


if __name__ == "__main__":
    logging.info(f"Lexus-Agent-V1 starting as @{BOT_USERNAME} ...")
    bot.infinity_polling(skip_pending=True)

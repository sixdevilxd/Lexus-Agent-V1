import os
import logging
import telebot
from openai import OpenAI
from config import TELEGRAM_BOT_TOKEN, CONDUIT_API_KEY, CONDUIT_BASE_URL, DEFAULT_MODEL, MAX_HISTORY

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize bot and openai client
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = OpenAI(api_key=CONDUIT_API_KEY, base_url=CONDUIT_BASE_URL)

# Conversations memory
chat_history = {}
chat_models = {}

# System Instruction
SYSTEM_PROMPT = "Anda adalah AI Agent Telegram yang asisten cerdas dan responsif. Berikan jawaban yang membantu, akurat, dan format pesan yang rapi menggunakan Markdown."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **Halo! Saya adalah AI Agent Telegram Anda.**\n\n"
        "Saya ditenagai oleh API Conduit, yang memungkinkan saya beralih di antara berbagai model AI canggih secara dinamis!\n\n"
        "⚡ **Fitur Utama:**\n"
        "1. Percakapan multi-turn (ingat riwayat chat)\n"
        "2. Kemudahan ganti model AI langsung dari obrolan\n\n"
        "🤖 **Perintah yang tersedia:**\n"
        "• `/start` atau `/help` - Menampilkan bantuan ini\n"
        "• `/model` - Melihat model aktif atau mengubah model\n"
        "• `/clear` - Menghapus riwayat percakapan Anda\n\n"
        "Kirim pesan apa saja untuk memulai obrolan!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['model'])
def manage_model(message):
    chat_id = message.chat.id
    current_model = chat_models.get(chat_id, DEFAULT_MODEL)

    args = message.text.split()
    if len(args) > 1:
        new_model = args[1]
        chat_models[chat_id] = new_model
        bot.reply_to(message, f"✅ **Model berhasil diubah!**\n\nModel aktif sekarang: `{new_model}`", parse_mode='Markdown')
        logging.info(f"Chat {chat_id} changed model to {new_model}")
    else:
        info_text = (
            f"🤖 **Model Aktif Saat Ini:** `{current_model}`\n\n"
            "Anda dapat mengubah model dengan mengetik: `/model <nama_model>`\n\n"
            "💡 **Contoh model yang terhubung di Conduit Anda:**\n"
            "• `anthropic/claude-sonnet-4-6`\n"
            "• `openai/gpt-5-mini`\n"
            "• `openai/gpt-5`\n"
            "• `openai/o4`\n"
            "• `anthropic/claude-opus-4-8`\n\n"
            "**Contoh:** `/model openai/gpt-5-mini`"
        )
        bot.reply_to(message, info_text, parse_mode='Markdown')

@bot.message_handler(commands=['clear'])
def clear_history(message):
    chat_id = message.chat.id
    if chat_id in chat_history:
        chat_history[chat_id] = []
        bot.reply_to(message, "🧹 **Riwayat percakapan untuk chat ini telah dihapus!**", parse_mode='Markdown')
        logging.info(f"Cleared history for chat {chat_id}")
    else:
        bot.reply_to(message, "Riwayat percakapan Anda sudah bersih.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_text = message.text

    # Send typing feedback
    bot.send_chat_action(chat_id, 'typing')

    if chat_id not in chat_history:
        chat_history[chat_id] = []

    active_model = chat_models.get(chat_id, DEFAULT_MODEL)

    # Prepare payload with history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in chat_history[chat_id]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_text})

    try:
        logging.info(f"Sending request to Conduit API using model {active_model} for chat {chat_id}")

        response = client.chat.completions.create(
            model=active_model,
            messages=messages,
            stream=False
        )

        reply_content = response.choices[0].message.content

        # Save to history
        chat_history[chat_id].append({"role": "user", "content": user_text})
        chat_history[chat_id].append({"role": "assistant", "content": reply_content})

        # Prune memory if exceeds limits
        if len(chat_history[chat_id]) > MAX_HISTORY * 2:
            chat_history[chat_id] = chat_history[chat_id][-(MAX_HISTORY * 2):]

        bot.reply_to(message, reply_content, parse_mode='Markdown')

    except Exception as e:
        error_msg = f"❌ **Gagal memproses permintaan:**\n\n`{str(e)}`"
        bot.reply_to(message, error_msg, parse_mode='Markdown')
        logging.error(f"Error calling Conduit API: {str(e)}")

if __name__ == '__main__':
    logging.info("Bot is starting...")
    bot.infinity_polling()

"""Helpers for safe Telegram message rendering (Markdown fallback + splitting)."""
import logging

TG_LIMIT = 4096


def split_text(text, limit=TG_LIMIT):
    """Split long text into Telegram-safe chunks, preferring newline boundaries."""
    if not text:
        return [""]
    parts = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:]
    parts.append(text)
    return parts


def send_long_message(bot, chat_id, text, reply_to=None):
    """Send a (possibly long) message; fall back to plain text if Markdown fails."""
    for i, part in enumerate(split_text(text)):
        rt = reply_to if i == 0 else None
        try:
            bot.send_message(chat_id, part, parse_mode="Markdown", reply_to_message_id=rt)
        except Exception:
            bot.send_message(chat_id, part, reply_to_message_id=rt)


def edit_safe(bot, chat_id, message_id, text):
    """Edit a message; try Markdown, fall back to plain, ignore 'not modified' noise."""
    snippet = text[:TG_LIMIT]
    try:
        bot.edit_message_text(snippet, chat_id, message_id, parse_mode="Markdown")
    except Exception as e:
        if "not modified" in str(e).lower():
            return
        try:
            bot.edit_message_text(snippet, chat_id, message_id)
        except Exception as e2:
            logging.debug(f"edit_safe failed: {e2}")

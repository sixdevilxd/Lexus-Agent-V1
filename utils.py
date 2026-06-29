"""Helpers for safe Telegram message rendering (Markdown fallback + splitting).

Telegram\'s legacy Markdown parser rejects unbalanced entities (a stray `_`, `*`
or backtick) with HTTP 400 "can\'t parse entities". Since the AI output is not
guaranteed to be valid Markdown, every dynamic-content send/edit here tries
Markdown first and automatically falls back to plain text on failure."""
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


def safe_send(bot, chat_id, text, reply_to=None):
    """Send one chunk: try Markdown, fall back to plain text on parse errors."""
    try:
        return bot.send_message(chat_id, text, parse_mode="Markdown",
                                reply_to_message_id=reply_to)
    except Exception as e:
        logging.debug(f"safe_send markdown failed, plain fallback: {e}")
        return bot.send_message(chat_id, text, reply_to_message_id=reply_to)


def safe_reply(bot, message, text):
    """Reply to a message with Markdown, falling back to plain text."""
    return safe_send(bot, message.chat.id, text, reply_to=message.message_id)


def send_long_message(bot, chat_id, text, reply_to=None):
    """Send a (possibly long) message in safe chunks."""
    for i, part in enumerate(split_text(text)):
        safe_send(bot, chat_id, part, reply_to=reply_to if i == 0 else None)


def edit_safe(bot, chat_id, message_id, text, markdown=True):
    """Edit a message; try Markdown (optional), fall back to plain text.
    Ignores Telegram\'s harmless \'message is not modified\' error."""
    snippet = text[:TG_LIMIT]
    if markdown:
        try:
            return bot.edit_message_text(snippet, chat_id, message_id, parse_mode="Markdown")
        except Exception as e:
            if "not modified" in str(e).lower():
                return
    try:
        return bot.edit_message_text(snippet, chat_id, message_id)
    except Exception as e:
        if "not modified" not in str(e).lower():
            logging.debug(f"edit_safe failed: {e}")

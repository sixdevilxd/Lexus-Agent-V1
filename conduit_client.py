"""Lightweight Conduit (OpenAI-compatible) client using requests only.
Avoids the heavy `openai` SDK so it installs cleanly on Termux (no Rust build)."""
import json
import requests
from config import CONDUIT_API_KEY, CONDUIT_BASE_URL


def _endpoint():
    base = CONDUIT_BASE_URL.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return base + "/chat/completions"


def _headers():
    return {
        "Authorization": f"Bearer {CONDUIT_API_KEY}",
        "Content-Type": "application/json",
    }


def chat(model, messages, timeout=120):
    """Non-streaming completion. Returns assistant text."""
    payload = {"model": model, "messages": messages, "stream": False}
    r = requests.post(_endpoint(), headers=_headers(), json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def chat_stream(model, messages, timeout=300):
    """Streaming completion. Yields text deltas as they arrive (SSE)."""
    payload = {"model": model, "messages": messages, "stream": True}
    with requests.post(_endpoint(), headers=_headers(), json=payload,
                       stream=True, timeout=timeout) as r:
        r.raise_for_status()
        for raw in r.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data:"):
                continue
            chunk = raw[len("data:"):].strip()
            if chunk == "[DONE]":
                break
            try:
                obj = json.loads(chunk)
                delta = obj["choices"][0]["delta"].get("content")
                if delta:
                    yield delta
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

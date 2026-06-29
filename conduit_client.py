"""Lightweight Conduit (OpenAI-compatible) client using requests only.
Avoids the heavy `openai` SDK so it installs cleanly on Termux (no Rust build).

Conduit OpenAI-compatible endpoint:
    POST https://conduit.ozdoev.net/api/v1/chat/completions
"""
import json
import requests
from config import CONDUIT_API_KEY, CONDUIT_BASE_URL


def _endpoint():
    """Build a robust chat-completions URL from CONDUIT_BASE_URL.
    - Adds https:// if scheme is missing.
    - Appends /chat/completions only if not already present (no path doubling)."""
    base = (CONDUIT_BASE_URL or "").strip().rstrip("/")
    if not base:
        base = "https://conduit.ozdoev.net/api/v1"
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def _headers():
    return {
        "Authorization": f"Bearer {CONDUIT_API_KEY}",
        "Content-Type": "application/json",
    }


def _raise_for_status(r):
    """Raise a clear error that includes the server response body."""
    if r.status_code >= 400:
        try:
            body = r.json()
            detail = body.get("error", {})
            if isinstance(detail, dict):
                detail = detail.get("message") or json.dumps(body)[:400]
        except Exception:
            detail = r.text[:400]
        raise RuntimeError(f"{r.status_code} {r.reason} \u2014 {detail}")


def chat(model, messages, timeout=120):
    """Non-streaming completion. Returns assistant text."""
    payload = {"model": model, "messages": messages, "stream": False}
    r = requests.post(_endpoint(), headers=_headers(), json=payload, timeout=timeout)
    _raise_for_status(r)
    data = r.json()
    return data["choices"][0]["message"]["content"]


def chat_stream(model, messages, timeout=300):
    """Streaming completion. Yields text deltas as they arrive (SSE)."""
    payload = {"model": model, "messages": messages, "stream": True}
    with requests.post(_endpoint(), headers=_headers(), json=payload,
                       stream=True, timeout=timeout) as r:
        _raise_for_status(r)
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

"""Lightweight Conduit (OpenAI-compatible) client using requests only.
Avoids the heavy `openai` SDK so it installs cleanly on Termux (no Rust build).

Conduit OpenAI-compatible endpoint:
    POST https://conduit.ozdoev.net/api/v1/chat/completions
NOTE: Conduit expects BARE model ids (e.g. `claude-opus-4-8`, `gpt-5-mini`),
NOT provider-prefixed ones like `anthropic/claude-opus-4-8`.
"""
import json
import requests
from config import CONDUIT_API_KEY, CONDUIT_BASE_URL


def _endpoint():
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


def normalize_model(model):
    """Strip provider prefix: 'anthropic/claude-opus-4-8' -> 'claude-opus-4-8'."""
    if not model:
        return model
    return model.strip().lstrip("/").split("/")[-1]


def _raise_for_status(r):
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
    payload = {"model": normalize_model(model), "messages": messages, "stream": False}
    r = requests.post(_endpoint(), headers=_headers(), json=payload, timeout=timeout)
    _raise_for_status(r)
    return r.json()["choices"][0]["message"]["content"]


def chat_stream(model, messages, timeout=300):
    """Streaming completion. Yields text deltas as they arrive (SSE)."""
    payload = {"model": normalize_model(model), "messages": messages, "stream": True}
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


def chat_with_tools(model, messages, tools, dispatch, max_rounds=5, timeout=120):
    """Agentic loop: let the model call tools until it produces a final answer.
    `dispatch(name, args)` runs a tool and returns a JSON-serializable result.
    Returns the final assistant text."""
    msgs = list(messages)
    last_text = ""
    for _ in range(max_rounds):
        payload = {
            "model": normalize_model(model),
            "messages": msgs,
            "tools": tools,
            "tool_choice": "auto",
            "stream": False,
        }
        r = requests.post(_endpoint(), headers=_headers(), json=payload, timeout=timeout)
        _raise_for_status(r)
        m = r.json()["choices"][0]["message"]
        last_text = m.get("content") or last_text
        tool_calls = m.get("tool_calls")

        # clean assistant message for the next request
        amsg = {"role": "assistant", "content": m.get("content")}
        if tool_calls:
            amsg["tool_calls"] = tool_calls
        msgs.append(amsg)

        if not tool_calls:
            return m.get("content") or ""

        for tc in tool_calls:
            fn = tc.get("function", {}).get("name", "")
            try:
                args = json.loads(tc.get("function", {}).get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                result = dispatch(fn, args)
            except Exception as e:
                result = {"error": str(e)}
            msgs.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": json.dumps(result, ensure_ascii=False)[:4000],
            })

    return last_text or "Maaf, riset belum selesai dalam batas langkah yang ditentukan."

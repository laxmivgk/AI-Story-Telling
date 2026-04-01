from __future__ import annotations

import json
import math
import os
import random
import re
import time
from collections.abc import Callable

from groq import Groq
from groq import APIConnectionError
from groq import APIError
from groq import APIStatusError
from groq import APITimeoutError
from groq import RateLimitError

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    return Groq(api_key=key)


def _model() -> str:
    return os.getenv("GROQ_MODEL", DEFAULT_MODEL)


def _friendly_api_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "429" in str(exc) or "rate" in msg or "too many requests" in msg:
        return "Rate limit reached. Please wait a short moment and try again."
    if "401" in str(exc) or "invalid api key" in msg or "unauthorized" in msg:
        return "API key was rejected. Check GROQ_API_KEY in your .env file."
    if "503" in str(exc) or "overload" in msg or "unavailable" in msg:
        return "The model is temporarily unavailable. Try again in a moment."
    return f"Something went wrong with the AI request: {exc}"


def _retry_wait_seconds(exc: Exception, attempt: int) -> float:
    if isinstance(exc, APIStatusError) and exc.response is not None:
        h = exc.response.headers.get("retry-after")
        if h:
            try:
                return max(1.0, float(h))
            except ValueError:
                pass
    return min(60.0, (2**attempt) + random.uniform(0.25, 1.5))


def _is_retriable(exc: Exception) -> bool:
    if isinstance(exc, (RateLimitError, APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, APIStatusError):
        code = getattr(exc, "status_code", 0) or 0
        return code in (408, 429, 500, 502, 503, 504)
    return False


def _sleep_with_countdown(total: float, on_tick: Callable[[int], None] | None) -> None:
    deadline = time.time() + max(0.0, total)
    while True:
        left = deadline - time.time()
        if left <= 0:
            break
        display = max(1, int(math.ceil(left)))
        if on_tick:
            on_tick(display)
        time.sleep(min(1.0, left))


def chat_completion(
    system: str,
    user: str,
    temperature: float,
    max_tokens: int = 2048,
    max_retries: int = 6,
    on_retry_countdown: Callable[[int], None] | None = None,
) -> str:
    client = _client()
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=_model(),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=float(temperature),
                max_tokens=max_tokens,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                raise RuntimeError("The model returned an empty response.")
            return text
        except APIError as e:
            if attempt < max_retries - 1 and _is_retriable(e):
                wait = _retry_wait_seconds(e, attempt)
                _sleep_with_countdown(wait, on_retry_countdown)
                continue
            raise RuntimeError(_friendly_api_error(e)) from e
        except Exception as e:
            raise RuntimeError(_friendly_api_error(e)) from e


def parse_choices_json(raw: str) -> list[str]:
    """Extract JSON object from model output; tolerate optional markdown fences."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\"choices\"[\s\S]*\}", text)
        if not m:
            raise ValueError("Could not parse choices JSON.")
        data = json.loads(m.group(0))
    choices = data.get("choices")
    if not isinstance(choices, list) or len(choices) != 3:
        raise ValueError("Expected exactly 3 choices in JSON.")
    out = [str(c).strip() for c in choices]
    if any(not x for x in out):
        raise ValueError("Empty choice text.")
    return out


def parse_characters_json(raw: str) -> list[dict[str, str]]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\"characters\"[\s\S]*\}", text)
        if not m:
            raise ValueError("Could not parse characters JSON.")
        data = json.loads(m.group(0))
    chars = data.get("characters")
    if not isinstance(chars, list):
        raise ValueError("Invalid characters list.")
    out: list[dict[str, str]] = []
    for item in chars:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        desc = str(item.get("description", "")).strip()
        if name:
            out.append({"name": name, "description": desc})
    return out

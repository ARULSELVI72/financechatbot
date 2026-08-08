"""
LLM client layer.

This wraps the Groq API (OpenAI-compatible chat completions, running
open models like Llama 3.3 at very high speed). It's isolated from the
backend/frontend so you can swap in a different provider by only editing
this file.

Docs: https://console.groq.com/docs/quickstart
"""

import os

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = 1024

_api_key = os.environ.get("GROQ_API_KEY")
_client = None

if _api_key:
    from groq import Groq
    _client = Groq(api_key=_api_key)


def get_response(user_message: str, history=None, system_prompt: str = "") -> str:
    """
    Get a chat completion from Groq.

    history: list of {"user": "...", "assistant": "..."} turns, oldest first.
    """
    if _client is None:
        # Demo mode so the app still runs end-to-end without an API key.
        return (
            "[Demo mode - no GROQ_API_KEY set]\n"
            "Set the GROQ_API_KEY environment variable to get real answers. "
            f"You said: \"{user_message}\""
        )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for turn in history or []:
        if turn.get("user"):
            messages.append({"role": "user", "content": turn["user"]})
        if turn.get("assistant"):
            messages.append({"role": "assistant", "content": turn["assistant"]})
    messages.append({"role": "user", "content": user_message})

    completion = _client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
    )

    return completion.choices[0].message.content

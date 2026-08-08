"""
Lightweight safety layer.

This is intentionally simple (keyword/pattern based) rather than a full
moderation model, since the goal is to demonstrate the concept of a safety
gate in the pipeline: check the incoming message before it reaches the LLM,
and refuse or redirect if it trips a rule.

For a production system you'd typically add a real moderation API or model
here in addition to (not instead of) these pattern checks.
"""

import re

# Patterns that look like attempts to override the system prompt / jailbreak.
PROMPT_INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior) instructions",
    r"disregard (all|any|previous|prior) instructions",
    r"you are now",
    r"act as (an?|the) (unfiltered|unrestricted|jailbroken)",
    r"reveal (your|the) system prompt",
    r"what (are|is) your system prompt",
]

# Topics this finance assistant should decline to give specific guidance on,
# per the "not a licensed advisor" boundary in the system prompt.
OUT_OF_SCOPE_PATTERNS = [
    r"which (stock|crypto|coin)s? should i buy",
    r"guarantee(d)? returns?",
    r"insider (tip|information)",
]

REFUSAL_PROMPT_INJECTION = (
    "I can't follow instructions that try to override how I'm configured to "
    "behave. I'm happy to keep helping with your finance question though —"
    " what would you like to know?"
)

REFUSAL_OUT_OF_SCOPE = (
    "I'm not able to recommend specific stocks, coins, or guarantee any "
    "investment returns — no one can honestly guarantee returns, and "
    "specific picks need a licensed financial advisor who knows your full "
    "situation. I can explain the general concepts involved instead, if "
    "that would help."
)


def check_message(message: str):
    """
    Returns (is_allowed: bool, refusal_message: str | None).
    """
    lowered = message.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return False, REFUSAL_PROMPT_INJECTION

    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, lowered):
            return False, REFUSAL_OUT_OF_SCOPE

    return True, None

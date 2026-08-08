"""
A small external tool the chatbot can call: a compound interest calculator.

LLMs are unreliable at precise arithmetic. Rather than trust the model to
compute compound growth itself, we detect the intent with a simple rule and
do the math in real Python, then hand the LLM the computed result to explain
in a message rather than to calculate.

This is a deliberately simple, rule-based "tool call" rather than a full
function-calling setup, to keep the moving parts easy to follow — the same
pattern (detect -> compute -> hand result to the LLM) extends naturally to
real function calling with tool schemas.
"""

import re

COMPOUND_INTEREST_TRIGGER = re.compile(r"compound interest", re.IGNORECASE)

# e.g. "$1000 at 5% for 10 years" / "1,000 dollars at 5.5 percent for 3 years"
CALC_PATTERN = re.compile(
    r"([\d,]+\.?\d*)\D+?(\d+\.?\d*)\s*%?.*?(\d+)\s*year",
    re.IGNORECASE,
)


def try_compound_interest_tool(message: str):
    """
    Returns a formatted calculation string if the message looks like a
    compound-interest question with extractable numbers, else None.
    """
    if not COMPOUND_INTEREST_TRIGGER.search(message):
        return None

    match = CALC_PATTERN.search(message)
    if not match:
        return None

    try:
        principal = float(match.group(1).replace(",", ""))
        rate = float(match.group(2)) / 100
        years = int(match.group(3))
    except ValueError:
        return None

    amount = principal * ((1 + rate) ** years)
    interest_earned = amount - principal

    return (
        f"[Tool: compound_interest_calculator]\n"
        f"Principal: {principal:,.2f}\n"
        f"Annual rate: {rate * 100:.2f}%\n"
        f"Years: {years}\n"
        f"Formula: A = P × (1 + r)^t\n"
        f"Final amount: {amount:,.2f}\n"
        f"Interest earned: {interest_earned:,.2f}"
    )

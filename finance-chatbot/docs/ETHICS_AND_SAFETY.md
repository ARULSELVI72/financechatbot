# Ethical Considerations and Safety Filters

## Domain-specific risk: financial harm

Unlike a generic chatbot, a finance assistant's mistakes have a direct path
to real financial harm — bad advice can cost someone money they can't
recover. The design responds to this in a few ways:

- **No personalized recommendations.** The system prompt explicitly forbids
  telling a user which specific stock, crypto asset, or product to buy, and
  forbids promising or implying guaranteed returns. `backend/safety.py`
  backs this up with a pattern-based check that catches common phrasings of
  "which stock should I buy" and "guaranteed returns" and returns a fixed
  refusal pointing the user to a licensed advisor, rather than relying on
  the LLM to self-police every time.
- **No fabricated data.** The system prompt instructs the model not to
  invent specific market prices, rates, or figures it doesn't actually have
  access to, since a confidently wrong number is worse than an honest "I
  don't have live data for that."
- **Grounding in a reviewed knowledge base.** Where possible, answers are
  grounded in the curated documents in `data/finance_docs/` via RAG, rather
  than purely from the model's parametric memory, which reduces (but does
  not eliminate) the chance of subtly wrong general-finance explanations.
- **Consistent disclaimers for high-stakes topics.** For anything touching
  large investments, tax filing specifics, or legal/estate matters, the
  model is instructed to point the user to a licensed professional rather
  than attempt a complete answer itself.

## Prompt injection / jailbreak resistance

`backend/safety.py` checks incoming messages against patterns associated
with attempts to override the system prompt (e.g. "ignore previous
instructions", "reveal your system prompt", "act as an unrestricted..."). A
match short-circuits the request before it reaches the LLM at all, and
returns a fixed, non-negotiable refusal message. This is a first line of
defense, not a complete solution — a sufficiently creative rephrasing could
still get through a keyword-based filter, which is a known limitation (see
below).

## Data and privacy

- The app does not persist user conversations server-side; history lives in
  the frontend's session state only (see `docs/ARCHITECTURE.md`, Memory
  management).
- The knowledge base in `data/finance_docs/` contains only general,
  non-personal finance educational content written for this project — no
  user data is ingested into the vector store.
- If this project were extended to ingest a user's real financial documents
  (e.g. bank statements) for retrieval, that would introduce meaningfully
  higher privacy stakes — encryption at rest, access controls, and a clear
  data-retention policy would become necessary before shipping.

## Tone and accessibility

Money is an emotionally loaded topic for many people (debt shame, anxiety
about retirement, etc.). The system prompt asks for a warm,
non-judgmental tone deliberately, since a curt or moralizing tone on
financial topics can discourage someone from engaging with their finances
at all.

## Known limitations

- The safety filter is regex/keyword based, not a trained moderation model.
  It will miss creative rephrasings and can false-positive on legitimate
  questions that happen to match a pattern. A production deployment should
  add a real moderation model/API as a second layer, not replace this one.
- The LLM can still occasionally produce a plausible-sounding but incorrect
  general explanation (hallucination) even with RAG grounding, since
  retrieval reduces but doesn't eliminate this risk. The evaluation harness
  (`docs/EVALUATION.md`) exists to catch regressions in answer quality, but
  it is not exhaustive.
- The tool-call detection for compound interest is regex-based and will
  miss numbers phrased in unusual ways (e.g. spelled-out numbers). It fails
  closed — if it can't confidently extract the numbers, it returns nothing
  and the LLM answers without a computed tool result rather than guessing.

# Evaluation

## Approach

`eval/evaluate.py` runs a fixed set of questions (`eval/eval_dataset.json`)
through the live backend API and scores each response on three metrics
chosen to approximate the assignment's accuracy / coherence / engagement
criteria without requiring a large labeled dataset or human annotators:

| Metric              | What it measures                                                                 | How it's computed |
|----------------------|-----------------------------------------------------------------------------------|--------------------|
| Keyword coverage     | Proxy for **accuracy** — does the answer actually contain the key facts expected? | % of hand-picked expected keywords found in the response text |
| Retrieval hit rate    | Whether RAG is grounding answers correctly                                        | Whether the expected source document appears in the response's `sources` list |
| LLM-judged coherence  | Proxy for **coherence / engagement**                                              | The LLM itself rates each answer 1–5 for clarity and helpfulness ("LLM-as-judge") |

The eval set also includes a couple of adversarial-ish cases (e.g. "which
specific stock should I buy") to check that the safety/scope boundaries in
`docs/ETHICS_AND_SAFETY.md` actually hold in practice, not just in the
system prompt text.

## Running it

```bash
# terminal 1
python backend/app.py

# terminal 2
python eval/evaluate.py
```

Output looks like:

```
[1] What is the 50/30/20 rule for budgeting?
    keyword_coverage : 1.00
    retrieval_hit    : True  (sources: ['budgeting_basics.txt'])
    coherence (1-5)  : 5

...

==================================================
SUMMARY
==================================================
Avg keyword coverage : 92.50%
Retrieval hit rate   : 100.00%
Avg coherence (1-5)  : 4.75
```

## Why these metrics (and their limitations)

- **Keyword coverage** is cheap and fast to compute, and correlates
  reasonably well with "did the answer cover the right facts" for
  short-answer finance questions, but it's a blunt instrument — a paraphrase
  that avoids the exact keyword would be scored as missing it, and a bad
  answer that happens to name-drop the keywords could score well. Treat it
  as a signal, not ground truth.
- **Retrieval hit rate** directly tests the RAG pipeline in isolation from
  generation quality, which is useful for debugging whether a bad answer
  came from bad retrieval vs. bad generation.
- **LLM-as-judge coherence** is a widely used technique for evaluating
  open-ended text at scale without human raters, but it inherits the
  judge model's own biases and is not a substitute for periodic human
  review, especially for a domain with real financial-harm risk (see
  `docs/ETHICS_AND_SAFETY.md`). It's skipped automatically if `GROQ_API_KEY`
  isn't set, since it requires an LLM call.

## Extending the eval set

Add more entries to `eval/eval_dataset.json` in the same shape:

```json
{
  "question": "...",
  "expected_keywords": ["...", "..."],
  "expected_source": "some_doc.txt"  // or null if no specific doc should match
}
```

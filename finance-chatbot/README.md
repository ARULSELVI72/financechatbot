# FinanceBot — RAG-Powered Personal Finance Chatbot

A capstone-style Generative AI chatbot for the **personal finance** use case,
with a full UI, a retrieval-augmented generation (RAG) pipeline, memory,
a tool integration, safety filtering, and an evaluation harness.

| Layer      | Tech                                                |
|------------|------------------------------------------------------|
| Frontend   | Python + Gradio (`ChatInterface`)                     |
| Backend    | Flask REST API                                        |
| LLM        | Groq API (Llama 3.3, swappable — see `llm/`)          |
| RAG        | ChromaDB (local, persistent, no external API needed)  |
| Deployment | Gradio `launch()` + Docker/Compose                    |

See **`docs/ARCHITECTURE.md`** for the full request-flow diagram,
**`docs/ETHICS_AND_SAFETY.md`** for the safety design, and
**`docs/EVALUATION.md`** for how answer quality is measured.

## Project layout

```
data/finance_docs/   knowledge base documents used for retrieval
rag/                 ingestion (rag/ingest.py) + retrieval (rag/retriever.py)
llm/                 LLM client + system prompt (swap providers here)
backend/             Flask REST API, safety filter, tool integration
frontend/            Gradio chat UI
eval/                evaluation dataset + harness
docs/                architecture, ethics & safety, evaluation write-ups
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

cp .env.example .env            # then edit .env with your key
export GROQ_API_KEY=your-groq-api-key-here   # Windows PowerShell: $env:GROQ_API_KEY="..."
```

Get a free Groq API key at https://console.groq.com/keys.

## Build the vector index (run once, and after editing the knowledge base)

```bash
python rag/ingest.py
```

This chunks every `.txt` file in `data/finance_docs/` and stores embeddings
in a local, persistent Chroma database at `rag/chroma_db/`.

## Run locally (two terminals)

```bash
# Terminal 1 — backend
python backend/app.py
# -> running on http://localhost:5000

# Terminal 2 — frontend
python frontend/gradio_app.py
# -> running on http://localhost:7860
```

Open http://localhost:7860 and start chatting. Try:
- "How do I start building an emergency fund?" (RAG-grounded)
- "What is compound interest on $2000 at 6% for 5 years?" (tool call)
- "Which specific stock should I buy?" (safety refusal)

Each reply's footer shows which knowledge-base sources were used and
whether the calculator tool fired, so the pipeline is visible live.

## Evaluate

```bash
python eval/evaluate.py
```

Scores every question in `eval/eval_dataset.json` on keyword coverage,
retrieval hit rate, and LLM-judged coherence. Details in
`docs/EVALUATION.md`.

## Run with Docker Compose

```bash
export GROQ_API_KEY=your-groq-api-key-here
docker compose up --build
```

- Frontend: http://localhost:7860
- Backend health check: http://localhost:5000/api/health

Note: run `python rag/ingest.py` locally before building the image (or add
an ingestion step to the backend Dockerfile) so the vector index exists
inside the container.

## Deploying the Gradio frontend standalone (e.g. Hugging Face Spaces)

1. Deploy `backend/` (with `rag/chroma_db/` already built) somewhere
   reachable (Render, Railway, a VM, etc.) and note its public URL.
2. In your Space, set the environment variable `BACKEND_URL` to
   `https://your-backend-domain/api/chat`.
3. Push `frontend/gradio_app.py` + `frontend/requirements.txt` as the
   Space's app — Spaces auto-detects `gradio_app.py` and runs
   `demo.launch()`.

## Swapping the LLM

Everything LLM-specific lives in `llm/llm_client.py`. To use a different
provider (OpenAI, Anthropic, a local HuggingFace model) instead of Groq,
replace the body of `get_response()` — the backend, RAG, and frontend don't
need to change.

## Extending to other use cases

The knowledge base (`data/finance_docs/`), system prompt
(`llm/system_prompts.py`), and tool (`backend/tools.py`) are the
domain-specific pieces. To repurpose this same
frontend/backend/RAG/deployment skeleton for **HRMS**, **Education**, or
**Healthcare**, swap those three pieces for the new domain and re-run
`rag/ingest.py`.

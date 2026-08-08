# Architecture

## Overview

FinanceBot is a retrieval-augmented generation (RAG) chatbot scoped to
personal finance topics. It follows a standard four-layer design:

```
┌──────────────────┐     HTTP POST      ┌───────────────────────────────┐
│  Gradio Frontend  │ ──/api/chat──────▶ │        Flask Backend          │
│    (port 7860)    │ ◀──JSON reply───── │         (port 5000)           │
└──────────────────┘                    │                                │
                                         │  1. safety.check_message()    │
                                         │  2. tools.try_compound_...()  │
                                         │  3. rag.retriever.retrieve()  │
                                         │  4. llm.llm_client.get_...()  │
                                         └───────────────┬────────────────┘
                                                          │
                                          ┌───────────────┼────────────────┐
                                          ▼               ▼                ▼
                                   ┌────────────┐  ┌─────────────┐  ┌───────────┐
                                   │ Chroma      │  │ Groq API    │  │ In-process │
                                   │ vector DB   │  │ (Llama 3.3) │  │ tool logic │
                                   │ (local)     │  │             │  │            │
                                   └────────────┘  └─────────────┘  └───────────┘
```

## Request flow (`POST /api/chat`)

1. **Safety gate** (`backend/safety.py`) — the raw message is checked
   against prompt-injection and out-of-scope patterns before anything else
   runs. A tripped rule short-circuits the request with a refusal message.
2. **Tool call** (`backend/tools.py`) — a rule-based check looks for a
   compound-interest question with extractable numbers. If found, the exact
   calculation is computed in Python (not left to the LLM, which is
   unreliable at precise arithmetic).
3. **Retrieval** (`rag/retriever.py`) — the message is embedded and used to
   query a local, persistent Chroma vector store built from the documents in
   `data/finance_docs/`. The top-3 most relevant chunks are returned along
   with their source filenames.
4. **Generation** (`llm/llm_client.py`) — the original question, retrieved
   context (if any), and tool result (if any) are combined into a single
   user turn (`llm/system_prompts.py:build_user_turn`) and sent to the LLM
   (Groq, running Llama 3.3) along with the finance system prompt and prior
   conversation history.
5. The API returns `{ reply, sources, tool_used }`. The frontend appends a
   small footer showing which sources were used and whether the calculator
   tool fired, so the RAG pipeline is visible during a live demo.

## RAG pipeline details

- **Ingestion** (`rag/ingest.py`): reads every `.txt` file in
  `data/finance_docs/`, splits it into ~180-word chunks with 30-word
  overlap, and stores each chunk in Chroma with its source filename as
  metadata. Run this once (`python rag/ingest.py`) before starting the
  backend, and again after editing the knowledge base.
- **Embeddings**: Chroma's built-in default embedding function is used
  (ONNX-based MiniLM), which requires no external API key and no GPU/torch
  install — chosen deliberately to keep the local setup lightweight.
- **Vector store**: `chromadb.PersistentClient`, persisted to
  `rag/chroma_db/` on disk, so the index survives restarts.
- **Retrieval**: cosine-similarity nearest-neighbor search, top-k=3 by
  default (configurable in `rag/retriever.py`).

## Memory management

Conversation memory is **client-held, server-stateless**: the Gradio
frontend keeps the full chat history in its own UI state and sends it with
every request; the backend has no session store. This keeps the backend
simple and horizontally scalable (no sticky sessions needed) at the cost of
resending history on every call — an acceptable trade-off at this scale.
For a production system with very long conversations, you'd add
summarization or a windowed history to bound token usage.

## Why Groq

Groq was chosen as the LLM provider for fast inference on open models
(Llama 3.3) with a simple, OpenAI-style chat completions API. The LLM layer
is isolated in `llm/llm_client.py` specifically so it can be swapped for
another provider (OpenAI, Anthropic, a local model) without touching the
backend, RAG, or frontend layers.

## Deployment

- **Local dev**: run `backend/app.py` and `frontend/gradio_app.py` as two
  separate processes.
- **Docker**: `docker-compose.yml` builds and runs both services together,
  with the frontend configured to reach the backend over the Docker network.
- **Gradio-only deploy** (e.g. Hugging Face Spaces): deploy the backend
  separately and point the frontend's `BACKEND_URL` environment variable at
  its public URL.

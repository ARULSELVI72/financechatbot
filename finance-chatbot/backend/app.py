"""
Flask REST API backend for the Finance Chatbot (RAG-enabled).

Endpoints:
    GET  /api/health   -> liveness check
    POST /api/chat      -> { "message": str, "history": [{"user": str, "assistant": str}, ...] }
                            returns { "reply": str, "sources": [str, ...] }

Pipeline for /api/chat:
    1. Safety check on the incoming message (backend/safety.py).
    2. Try a rule-based tool call, e.g. compound interest (backend/tools.py).
    3. Retrieve relevant chunks from the local vector DB (rag/retriever.py).
    4. Build a system+user prompt combining retrieved context and/or tool
       output, then call the LLM (llm/llm_client.py).
"""

import os
import sys

# Allow importing sibling packages (llm/, rag/) when run as a script.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify
from flask_cors import CORS

from llm.llm_client import get_response
from llm.system_prompts import FINANCE_SYSTEM_PROMPT, build_user_turn
from rag.retriever import retrieve, format_context
from backend.safety import check_message
from backend.tools import try_compound_interest_tool

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "'message' is required"}), 400

    # 1. Safety gate
    allowed, refusal = check_message(message)
    if not allowed:
        return jsonify({"reply": refusal, "sources": [], "tool_used": False})

    try:
        # 2. Tool call (rule-based)
        tool_result = try_compound_interest_tool(message)

        # 3. Retrieval
        chunks = retrieve(message, top_k=3)
        context_text = format_context(chunks)
        sources = sorted({c["source"] for c in chunks})

        # 4. Build augmented user turn and call the LLM
        augmented_message = build_user_turn(
            user_message=message,
            retrieved_context=context_text,
            tool_result=tool_result or "",
        )
        reply = get_response(
            augmented_message,
            history=history,
            system_prompt=FINANCE_SYSTEM_PROMPT,
        )

        return jsonify({
            "reply": reply,
            "sources": sources,
            "tool_used": tool_result is not None,
        })
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

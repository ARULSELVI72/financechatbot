"""
Gradio frontend for the Finance Chatbot.

This is a plain Python UI (no HTML/JS to write) that calls the Flask REST API
backend over HTTP. Run the backend first, then run this file.
"""

import os
import requests
import gradio as gr

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000/api/chat")


def chat_fn(message, history):
    """
    message: str, the latest user message
    history: list of [user, assistant] pairs (Gradio's ChatInterface format)
    """
    api_history = [
        {"user": u, "assistant": a}
        for u, a in history
        if u is not None and a is not None
    ]

    try:
        response = requests.post(
            BACKEND_URL,
            json={"message": message, "history": api_history},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return f"⚠️ Backend error: {data['error']}"

        reply = data.get("reply", "Sorry, I couldn't generate a response.")
        sources = data.get("sources") or []
        tool_used = data.get("tool_used", False)

        footer_bits = []
        if tool_used:
            footer_bits.append("🧮 used the compound interest calculator")
        if sources:
            footer_bits.append(f"📚 sources: {', '.join(sources)}")
        if footer_bits:
            reply += "\n\n---\n_" + " · ".join(footer_bits) + "_"

        return reply
    except requests.exceptions.RequestException as exc:
        return f"⚠️ Could not reach the backend at {BACKEND_URL}: {exc}"


demo = gr.ChatInterface(
    fn=chat_fn,
    title="💰 FinanceBot — RAG-Powered Personal Finance Assistant",
    description=(
        "Ask about budgeting, saving, investing basics, debt, credit scores, retirement "
        "accounts, and more. Answers are grounded in a local finance knowledge base via "
        "retrieval-augmented generation (RAG). Educational information only — not a "
        "substitute for professional financial advice."
    ),
    examples=[
        "How do I start building an emergency fund?",
        "What's the difference between a Roth IRA and a traditional IRA?",
        "What is compound interest on $2000 at 6% for 5 years?",
        "Snowball or avalanche — which debt payoff method is better?",
        "How do I build a simple monthly budget?",
    ],
    theme=gr.themes.Soft(),
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

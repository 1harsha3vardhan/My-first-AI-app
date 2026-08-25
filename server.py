"""
Web version of my AI chat app, built with Flask.

Now supports:
- Multiple saved chat sessions (sidebar)
- Conversation memory (the AI sees earlier messages in the same session)
- Chats persisted to a local JSON file so they survive server restarts
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "No GEMINI_API_KEY found. Did you create a .env file with "
        "GEMINI_API_KEY=your-key-here ?"
    )

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

# ---------------------------------------------------------------------
# Simple JSON-file storage for chat sessions.
# Good enough for a personal project; not meant for many concurrent users.
# ---------------------------------------------------------------------
DATA_FILE = Path(__file__).parent / "data" / "chats.json"
DATA_FILE.parent.mkdir(exist_ok=True)


def load_chats():
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chats(chats):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2)


def make_title(first_message: str) -> str:
    """Turn the first user message into a short session title."""
    title = first_message.strip().replace("\n", " ")
    return title[:40] + ("…" if len(title) > 40 else "")


# ---------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------------------
# Session list: get all sessions, or create a new one
# ---------------------------------------------------------------------
@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    chats = load_chats()
    summary = [
        {
            "id": sid,
            "title": chat["title"],
            "updated_at": chat["updated_at"],
        }
        for sid, chat in chats.items()
    ]
    summary.sort(key=lambda s: s["updated_at"], reverse=True)
    return jsonify(summary)


@app.route("/api/sessions", methods=["POST"])
def create_session():
    chats = load_chats()
    session_id = str(uuid.uuid4())
    chats[session_id] = {
        "title": "New chat",
        "messages": [],
        "updated_at": datetime.utcnow().isoformat(),
    }
    save_chats(chats)
    return jsonify({"id": session_id})


# ---------------------------------------------------------------------
# Single session: get its messages, or delete it
# ---------------------------------------------------------------------
@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    chats = load_chats()
    chat = chats.get(session_id)
    if not chat:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(chat)


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    chats = load_chats()
    if session_id in chats:
        del chats[session_id]
        save_chats(chats)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------
# Chat: send a message within a session, get the AI's reply
# ---------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    session_id = data.get("session_id")
    user_message = data.get("message", "").strip()

    if not session_id or not user_message:
        return jsonify({"error": "Missing session_id or message"}), 400

    chats = load_chats()
    chat_session = chats.get(session_id)
    if not chat_session:
        return jsonify({"error": "Session not found"}), 404

    # Build the conversation history in the format the Gemini API expects
    contents = []
    for msg in chat_session["messages"]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["text"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
        )
        reply_text = response.text
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Save both the user message and the AI reply
    chat_session["messages"].append({"role": "user", "text": user_message})
    chat_session["messages"].append({"role": "ai", "text": reply_text})
    chat_session["updated_at"] = datetime.utcnow().isoformat()

    if chat_session["title"] == "New chat":
        chat_session["title"] = make_title(user_message)

    chats[session_id] = chat_session
    save_chats(chats)

    return jsonify({"reply": reply_text, "title": chat_session["title"]})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

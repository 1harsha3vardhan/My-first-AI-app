"""
Web version of my AI chat app, built with Flask.

Reuses the same Gemini setup as app.py, just serves it over a browser
instead of the terminal.
"""

import os
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


@app.route("/")
def home():
    """Serve the chat page."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Receive a message from the browser, ask Gemini, send back the reply."""
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_message,
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

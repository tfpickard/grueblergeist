#!/usr/bin/env python
"""
Flask API for Grüblergeist React Frontend.
"""
import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from rich import print

from .chat_assistant import ChatAssistant

app = Flask(__name__)
CORS(app)  # Allow frontend requests

assistant = ChatAssistant()

STYLE_PROFILE_FILE = "data/user_style_profile.json"
ROLLING_CHAT_LOG = "data/rolling_chat_log.json"


def load_json(file_path):
    """Load JSON data safely."""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat interactions."""
    data = request.get_json()
    user_message = data.get("message", "")
    assistant_reply = assistant.reply(user_message)
    print("\n\n")
    print(jsonify({"reply": assistant_reply}))
    print(assistant_reply)
    print("\n\n")
    return jsonify({"reply": assistant_reply})


@app.route("/api/persona", methods=["GET"])
def get_persona():
    """Return AI persona details."""
    persona = load_json(STYLE_PROFILE_FILE)
    return jsonify(persona)


@app.route("/api/chat-log", methods=["GET"])
def get_chat_log():
    """Return the last 10 messages from chat history."""
    chat_log = load_json(ROLLING_CHAT_LOG).get("messages", [])
    return jsonify(chat_log[-10:])  # Only return last 10


def run_web():
    """Start the Flask Web UI."""
    app.run(debug=True, port=5001)


def run_api():
    """Start Flask API."""
    app.run(debug=True, port=5001)

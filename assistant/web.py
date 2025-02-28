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
    data = request.get_json()
    user_message = data.get("message", "")
    strict_enforcement = data.get("strictEnforcement", False)  # boolean

    # Now call ChatAssistant with that param
    assistant_reply = assistant.reply(user_message, strict_enforcement)

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


@app.route("/api/threshold-history", methods=["GET"])
def get_threshold_history():
    """Returns historical threshold vs. snarkiness data."""
    return jsonify(
        {"threshold": assistant.threshold_history, "snark": assistant.snark_history}
    )


@app.route("/api/topic-score", methods=["GET"])
def get_last_topic_score():
    """Returns the latest topic match percentage."""
    if assistant.recent_topic_scores:
        return jsonify(
            {"topic_score": assistant.recent_topic_scores[-1] * 100}
        )  # Convert to %
    return jsonify({"topic_score": 50})  # Default neutral


# @app.route("/api/threshold-history", methods=["GET"])
# def get_threshold_history():
#     """Returns historical threshold vs. snarkiness data."""
#     return jsonify(
#         {"threshold": assistant.threshold_history, "snark": assistant.snark_history}
#     )
#


def run_web():
    """Start the Flask Web UI."""
    app.run(debug=True, port=5001)


def run_api():
    """Start Flask API."""
    app.run(debug=True, port=5001)

#!/usr/bin/env python
"""
Flask-based Web Interface for Grüblergeist, combining Chat UI and Debugging Dashboard.
"""

import json
import os

from flask import Flask, jsonify, render_template, request
from rich.console import Console

from .chat_assistant import ChatAssistant

console = Console()
app = Flask(__name__, template_folder="../templates")
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
        console.print(f"[red]Error reading {file_path}.[/]")
        return {}


@app.route("/")
def index():
    """Render the combined Chat + Debugging UI."""
    style_profile = load_json(STYLE_PROFILE_FILE)
    chat_log = load_json(ROLLING_CHAT_LOG).get("messages", [])

    return render_template(
        "combined_ui.html",
        style_profile=style_profile,
        chat_log=chat_log[-10:],  # Show last 10 messages
    )


@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat interactions."""
    data = request.get_json()
    user_message = data.get("message", "")
    assistant_reply = assistant.reply(user_message)

    return jsonify({"reply": assistant_reply})


def run_web():
    """Start the Flask Web UI."""
    console.print("[cyan]Starting Web Interface...[/]")
    app.run(debug=True, port=5000)

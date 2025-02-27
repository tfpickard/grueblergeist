#!/usr/bin/env python
"""
Debugging Dashboard for tracking AI persona evolution.
"""

import json
import os
from flask import Flask, render_template
from rich.console import Console

console = Console()
app = Flask(__name__, template_folder="../templates")

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
def dashboard():
    """Render the debugging dashboard."""
    style_profile = load_json(STYLE_PROFILE_FILE)
    chat_log = load_json(ROLLING_CHAT_LOG).get("messages", [])

    return render_template(
        "dashboard.html",
        style_profile=style_profile,
        chat_log=chat_log[-10:],  # Show the last 10 messages
    )


def run_dashboard():
    """Start the Flask debugging dashboard."""
    console.print("[cyan]Starting Debugging Dashboard...[/]")
    app.run(debug=True, port=5001)

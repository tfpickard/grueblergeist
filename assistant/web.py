# assistant/web.py
"""
Flask-based web interface for Grüblergeist.
"""

import logging
from typing import Any

from flask import Flask, jsonify, render_template, request

from .chat_assistant import ChatAssistant
from .config import get_config_value

logger = logging.getLogger(__name__)
app = Flask(__name__)
assistant = ChatAssistant()


@app.route("/")
def index() -> str:
    """
    Serve the main chat interface.

    :return: Rendered HTML page with chat UI.
    """
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat_api() -> Any:
    """
    Handle AJAX requests for user messages.

    :return: JSON response containing assistant's reply.
    """
    data = request.get_json()
    user_message: str = data.get("message", "")
    assistant_reply = assistant.reply(user_message)
    logger.info(f"User: {user_message}\nGrüblergeist: {assistant_reply}")
    return jsonify({"reply": assistant_reply})


def run_web() -> None:
    """
    Launch the Flask web server in debug mode.
    """
    host = get_config_value("flask_host", "127.0.0.1")
    port = get_config_value("flask_port", 5000)
    logger.info(f"Starting Flask web server on {host}:{port}")
    app.run(host=host, port=port, debug=True)

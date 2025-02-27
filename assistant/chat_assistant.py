#!/usr/bin/env python
"""
ChatAssistant class for Grüblergeist.
Handles conversation memory, user-specific adaptations, and AI interactions.
"""

import json
import logging
from typing import Optional

from .config import get_config_value
from .db import get_conversation_history, get_user_profile, save_interaction
from .llm_client import LLMClient

# Set up logging
logger = logging.getLogger(__name__)

# File paths for user data tracking
STYLE_PROFILE_FILE = "data/user_style_profile.json"
ROLLING_CHAT_LOG = "data/rolling_chat_log.json"


class ChatAssistant:
    """
    ChatAssistant orchestrates the retrieval of conversation context,
    loads user-specific response patterns, and interacts with the LLM.
    """

    def __init__(self, user_id: Optional[int] = None) -> None:
        """
        :param user_id: If not provided, defaults to the 'assistant_user_id' from config.json.
        """
        self.user_id: int = (
            user_id if user_id else get_config_value("assistant_user_id", 1234)
        )
        self.llm = LLMClient()
        self.user_style = self.load_user_style()

    def load_user_style(self) -> dict:
        """
        Load user-specific style traits from a precomputed JSON file.
        """
        try:
            with open(STYLE_PROFILE_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning("User style profile not found. Using default AI tone.")
            return {}

    def append_to_chat_log(self, user_message: str, assistant_reply: str) -> None:
        """
        Append messages to a rolling chat log for debugging and AI refinement.
        Keeps only the last 100 messages to prevent memory bloat.
        """
        try:
            with open(ROLLING_CHAT_LOG, "r", encoding="utf-8") as file:
                chat_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            chat_data = {"messages": []}

        chat_data["messages"].append(
            {"user": user_message, "assistant": assistant_reply}
        )

        # Keep only the last 100 messages
        chat_data["messages"] = chat_data["messages"][-100:]

        with open(ROLLING_CHAT_LOG, "w", encoding="utf-8") as file:
            json.dump(chat_data, file, indent=4)

    def reply(self, user_message: str) -> str:
        """
        Generates a reply from the assistant given the user's message.

        :param user_message: The user's latest query or statement.
        :return: The assistant's response as a string.
        """
        history = get_conversation_history(self.user_id, limit=10)  # last 10 messages
        user_profile = get_user_profile(self.user_id)

        system_note = f"You are Grüblergeist, a helpful assistant. Respond using the user's style."

        # Adjust AI persona based on extracted user style
        if self.user_style:
            response_style = self.user_style.get("response_style", "Neutral")
            common_phrases = ", ".join(self.user_style.get("common_phrases", []))
            system_note += f" The user prefers {response_style} responses. Use phrases like: {common_phrases}."

        # Insert system note if we have one
        history = [("system", system_note)] + history

        # Generate reply using the LLM
        assistant_reply: str = self.llm.generate_reply(history, user_message)

        # Save interaction
        save_interaction(
            self.user_id, user_message, assistant_reply, tone_detected=None
        )
        self.append_to_chat_log(user_message, assistant_reply)

        return assistant_reply

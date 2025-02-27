# assistant/chat_assistant.py
"""
ChatAssistant class for Grüblergeist.
Now includes user-specific style adaptation.
"""

import json
import logging
from typing import Optional

from .config import get_config_value
from .db import get_conversation_history, get_user_profile, save_interaction
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


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
        style_file = "/mnt/data/user_style_profile.json"
        try:
            with open(style_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning("User style profile not found. Using default AI tone.")
            return {}

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
        return assistant_reply

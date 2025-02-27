# assistant/llm_client.py
"""
LLM client for Grüblergeist.
Supports OpenAI or local LLM (Ollama).
"""

import logging
import os
from typing import List, Tuple

import openai
import requests

from .config import get_config_value

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Abstraction for generating replies via either OpenAI or a local LLM (Ollama).
    """

    def __init__(self) -> None:
        """
        Initialize the LLMClient by reading config to see if we use OpenAI or local LLM.
        """
        self.use_openai: bool = get_config_value("use_openai", True)
        self.openai_model: str = get_config_value("openai_model", "gpt-3.5-turbo")
        self.local_model: str = get_config_value("local_model", "llama2")

        # We'll rely on the environment variable for OpenAI key.
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.use_openai:
            if not openai_api_key:
                logger.warning(
                    "OPENAI_API_KEY environment variable not found! "
                    "OpenAI requests will fail unless you set this."
                )
            else:
                openai.api_key = openai_api_key
        else:
            logger.info(f"Using local LLM with Ollama: {self.local_model}")

    def generate_reply(
        self, conversation_history: List[Tuple[str, str]], user_input: str
    ) -> str:
        """
        Generate an assistant reply given the conversation history and user input.

        :param conversation_history: A list of (role, message) representing context.
        :param user_input: The user's latest message.
        :return: The assistant's reply as a string.
        """
        if self.use_openai:
            if not openai.api_key:
                return "[OpenAI key not set; cannot generate response.]"

            messages = [
                {"role": role, "content": msg} for role, msg in conversation_history
            ]
            messages.append({"role": "user", "content": user_input})

            try:
                # New OpenAI API Call for v1.0.0+
                client = openai.OpenAI()
                response = client.chat.completions.create(
                    model=self.openai_model, messages=messages
                )
                reply_text: str = response.choices[0].message.content
                return reply_text
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return f"[Error from OpenAI API: {e}]"
        else:
            # Local LLM via Ollama
            url = "http://localhost:11434/api/chat"
            messages_payload = [
                {"role": role, "content": msg} for role, msg in conversation_history
            ]
            messages_payload.append({"role": "user", "content": user_input})

            payload = {
                "model": self.local_model,
                "messages": messages_payload,
                "stream": False,
            }
            try:
                res = requests.post(url, json=payload, timeout=60)
                data = res.json()
                if "message" in data and data["message"]:
                    reply_text = data["message"].get("content", "")
                else:
                    reply_text = data.get("response", "") or data.get("content", "")
                return reply_text
            except Exception as e:
                logger.error(f"Local LLM error: {e}")
                return f"[Error from local LLM: {e}]"

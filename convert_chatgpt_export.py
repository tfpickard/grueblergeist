#!/usr/bin/env python
"""
Convert OpenAI's ChatGPT export (conversations.json) into a clean text format
for analysis by analyze_chat.py.
"""

import json
import re


def load_chatgpt_export(file_path: str):
    """Load exported ChatGPT conversation JSON."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_user_messages(conversations):
    """Extract only the user's messages from the exported ChatGPT JSON."""
    user_messages = []
    for convo in conversations["conversations"]:
        for turn in convo["mapping"].values():
            if isinstance(turn, dict) and "message" in turn:
                message = turn["message"]
                if message and message.get("author", {}).get("role") == "user":
                    user_messages.append(
                        message["content"]["parts"][0]
                    )  # Extract user's message
    return user_messages


def save_to_markdown(messages, output_file: str):
    """Save extracted messages to a Markdown file."""
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("# User Chat History\n\n")
        for msg in messages:
            file.write(f"**You:** {msg}\n\n")


# Run conversion
chatgpt_export_path = (
    "/mnt/data/conversations.json"  # Change this to your actual file location
)
output_markdown_path = "/mnt/data/user_chat_history.md"

conversations = load_chatgpt_export(chatgpt_export_path)
user_messages = extract_user_messages(conversations)
save_to_markdown(user_messages, output_markdown_path)

print(f"User chat history saved to {output_markdown_path}")

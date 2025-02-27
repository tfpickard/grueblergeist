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

    for convo in conversations:  # Iterate over list, not dict
        if "mapping" not in convo:
            continue  # Skip malformed conversations

        for turn in convo["mapping"].values():
            if isinstance(turn, dict) and "message" in turn:
                message = turn["message"]

                # Debugging: Print one sample message structure
                if not user_messages:
                    print(
                        "DEBUG: Sample message structure:",
                        json.dumps(message, indent=2),
                    )

                # Check if 'content' exists and is properly structured
                if message and message.get("author", {}).get("role") == "user":
                    content = message.get("content", {})

                    # Handle different content structures
                    if isinstance(content, str):  # Direct string
                        user_messages.append(content)
                    elif isinstance(content, dict) and "parts" in content:
                        user_messages.append(content["parts"][0])
                    else:
                        print("WARNING: Unrecognized content format", content)

    return user_messages


def save_to_markdown(messages, output_file: str):
    """Save extracted messages to a Markdown file."""
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("# User Chat History\n\n")
        for msg in messages:
            file.write(f"**You:** {msg}\n\n")


# Run conversion
chatgpt_export_path = (
    "data/conversations.json"  # Change this to your actual file location
)
output_markdown_path = "data/user_chat_history.md"

conversations = load_chatgpt_export(chatgpt_export_path)
user_messages = extract_user_messages(conversations)
save_to_markdown(user_messages, output_markdown_path)

print(f"User chat history saved to {output_markdown_path}")

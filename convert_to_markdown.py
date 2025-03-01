#!/usr/bin/env python3
"""
Convert conversations.json to user_chat_history.md format.
"""

import json

def load_conversations(file_path: str):
    """Load conversations from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def extract_user_messages(conversations):
    """Extract user messages from conversations."""
    user_messages = []
    for convo in conversations:
        if "mapping" not in convo:
            continue
        for turn in convo["mapping"].values():
            if isinstance(turn, dict) and "message" in turn:
                message = turn["message"]
                if message and message.get("author", {}).get("role") == "user":
                    content = message.get("content", {})
                    if isinstance(content, str):
                        user_messages.append(content)
                    elif isinstance(content, dict) and "parts" in content:
                        user_messages.append(content["parts"][0])
    return user_messages

def save_to_markdown(messages, output_file: str):
    """Save messages to a Markdown file."""
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("# User Chat History\n\n")
        for msg in messages:
            file.write(f"**You:** {msg}\n\n")

def main():
    conversations_path = "data/conversations.json"
    output_markdown_path = "data/user_chat_history.md"

    conversations = load_conversations(conversations_path)
    user_messages = extract_user_messages(conversations)
    save_to_markdown(user_messages, output_markdown_path)

    print(f"User chat history saved to {output_markdown_path}")

if __name__ == "__main__":
    main()

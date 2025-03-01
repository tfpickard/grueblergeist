#!/usr/bin/env python3
"""
Extract user data from conversations.json, grouped by chat for context.
Includes useful metadata for each conversation.
"""

import json

def load_conversations(file_path: str):
    """Load conversations from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def extract_user_data(conversations):
    """Extract user data grouped by chat with metadata."""
    user_data = []
    for convo in conversations:
        if "mapping" not in convo:
            continue
        chat_id = convo.get("id", "unknown")
        created_at = convo.get("created_at", "unknown")
        messages = []
        for turn in convo["mapping"].values():
            if isinstance(turn, dict) and "message" in turn:
                message = turn["message"]
                if message and message.get("author", {}).get("role") == "user":
                    content = message.get("content", {})
                    if isinstance(content, str):
                        messages.append(content)
                    elif isinstance(content, dict) and "parts" in content:
                        messages.append(content["parts"][0])
        user_data.append({
            "chat_id": chat_id,
            "created_at": created_at,
            "messages": messages
        })
    return user_data

def save_to_markdown(user_data, output_file: str):
    """Save user data to a Markdown file."""
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("# User Chat Data\n\n")
        for chat in user_data:
            file.write(f"## Chat ID: {chat['chat_id']}\n")
            file.write(f"**Created At:** {chat['created_at']}\n\n")
            for msg in chat["messages"]:
                file.write(f"**You:** {msg}\n\n")

def main():
    conversations_path = "data/conversations.json"
    output_markdown_path = "data/user_chat_data.md"

    conversations = load_conversations(conversations_path)
    user_data = extract_user_data(conversations)
    save_to_markdown(user_data, output_markdown_path)

    print(f"User chat data saved to {output_markdown_path}")

if __name__ == "__main__":
    main()

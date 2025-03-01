#!/usr/bin/env python3
"""
Generate a detailed user profile from OpenAI conversation data.
Processes the data in chunks to avoid API usage limits.
"""

import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import os
from typing import List

# Set up OpenAI API client

# File paths
CONVERSATIONS_PATH = "data/conversations.json"
STYLE_PROFILE_PATH = "data/user_style_profile.json"
CHUNK_SIZE = 6000  # Approx. characters per chunk

def load_conversations(file_path: str) -> List[dict]:
    """Load conversations from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def chunk_conversations(conversations: List[dict], chunk_size: int) -> List[str]:
    """Chunk conversations into manageable pieces."""
    text = json.dumps(conversations)
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def analyze_chunk(chunk: str) -> dict:
    """Analyze a chunk of conversation data using OpenAI."""
    prompt = f"""
    Analyze the following conversation data and provide a JSON summary with keys:
    "tone", "style", "common_phrases", "preferred_topics".

    Conversation Data:
    {chunk}
    """
    response = client.completions.create(engine="gpt-4",
    prompt=prompt,
    max_tokens=500,
    temperature=0.3)
    return json.loads(response.choices[0].text.strip())

def consolidate_profiles(profiles: List[dict]) -> dict:
    """Consolidate multiple profiles into a single profile."""
    # This is a simple example; you might want to implement a more sophisticated consolidation logic
    consolidated = {
        "tone": [],
        "style": [],
        "common_phrases": [],
        "preferred_topics": []
    }
    for profile in profiles:
        for key in consolidated.keys():
            consolidated[key].extend(profile.get(key, []))
    # Remove duplicates
    for key in consolidated.keys():
        consolidated[key] = list(set(consolidated[key]))
    return consolidated

def save_profile(profile: dict, file_path: str) -> None:
    """Save the consolidated profile to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

def main():
    conversations = load_conversations(CONVERSATIONS_PATH)
    chunks = chunk_conversations(conversations, CHUNK_SIZE)
    profiles = [analyze_chunk(chunk) for chunk in chunks]
    consolidated_profile = consolidate_profiles(profiles)
    save_profile(consolidated_profile, STYLE_PROFILE_PATH)
    print(f"User style profile saved to {STYLE_PROFILE_PATH}")

if __name__ == "__main__":
    main()

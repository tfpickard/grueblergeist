#!/usr/bin/env python
"""
Analyze chat history to extract user-specific traits and response patterns.
"""

import re
import json
from collections import Counter
from typing import Dict, List


def load_chat_log(file_path: str) -> List[str]:
    """Load chat history from a Markdown file."""
    with open(file_path, "r", encoding="utf-8") as file:
        chat_text = file.read()

    # Extract only user responses (assuming format: 'User: Response')
    user_responses = re.findall(r"^You:\s(.+)$", chat_text, re.MULTILINE)
    return user_responses


def analyze_text_patterns(responses: List[str]) -> Dict[str, any]:
    """Analyze text patterns from user responses."""
    word_counts = Counter()
    sentence_lengths = []

    for response in responses:
        words = response.split()
        sentence_lengths.append(len(words))
        word_counts.update(words)

    avg_sentence_length = (
        sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    )
    most_common_words = word_counts.most_common(20)  # Top 20 words

    # Identify style traits
    style_traits = {
        "avg_sentence_length": avg_sentence_length,
        "most_common_words": [word for word, _ in most_common_words],
        "common_phrases": [
            word for word, count in most_common_words if count > 3
        ],  # Words used often
        "response_style": "Concise" if avg_sentence_length < 10 else "Detailed",
    }

    return style_traits


def save_style_profile(style_profile: Dict[str, any], output_file: str) -> None:
    """Save the analyzed style profile to a JSON file."""
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(style_profile, file, indent=4)


# Run analysis
chat_log_path = "/mnt/data/Grueblergeist_Full_Chat_Export.md"
output_style_profile = "/mnt/data/user_style_profile.json"

user_responses = load_chat_log(chat_log_path)
style_profile = analyze_text_patterns(user_responses)
save_style_profile(style_profile, output_style_profile)

print(f"User style profile saved to {output_style_profile}")

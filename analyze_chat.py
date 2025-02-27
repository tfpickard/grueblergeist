#!/usr/bin/env python
"""
Analyze chat history to extract user-specific traits and response patterns.
Uses Rich for verbose output.
"""

import json
import logging
import re
from collections import Counter
from typing import Dict, List

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import track
from rich.table import Table

# Set up Rich console for styled output
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger("analyze_chat")


def load_chat_log(file_path: str) -> List[str]:
    """Load chat history from a Markdown file and extract user messages."""
    console.print(f"[cyan]Loading chat history from:[/] {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            chat_text = file.readlines()  # Read line by line
    except FileNotFoundError:
        console.print("[bold red]Error:[/] File not found!", style="red")
        return []

    # Extract user responses (matching "**You:** Some text")
    user_responses = []
    for line in chat_text:
        match = re.match(r"^\*\*You:\*\*\s*(.+)", line.strip())  # Improved regex
        if match:
            user_responses.append(match.group(1))

    console.print(f"[green]Loaded {len(user_responses)} messages from chat history.[/]")
    if len(user_responses) < 5:
        console.print(
            "[yellow]Warning: Very few messages detected. Check your input file![/]"
        )

    return user_responses


def analyze_text_patterns(responses: List[str]) -> Dict[str, any]:
    """Analyze text patterns from user responses with progress tracking."""
    if not responses:
        console.print(
            "[bold yellow]Warning:[/] No user messages found.", style="yellow"
        )
        return {}

    word_counts = Counter()
    sentence_lengths = []

    console.print("[blue]Analyzing chat history...[/]")
    for response in track(responses, description="Processing messages..."):
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

    console.print(f"[bold green]User style profile saved to:[/] {output_file}")


def display_results(style_profile: Dict[str, any]) -> None:
    """Display results in a formatted table."""
    if not style_profile:
        console.print("[red]No style data available.[/]")
        return

    table = Table(title="User Style Profile", show_lines=True)
    table.add_column("Trait", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row(
        "Avg Sentence Length", str(round(style_profile["avg_sentence_length"], 2))
    )
    table.add_row("Response Style", style_profile["response_style"])
    table.add_row(
        "Most Common Words", ", ".join(style_profile["most_common_words"][:10])
    )
    table.add_row("Common Phrases", ", ".join(style_profile["common_phrases"]))

    console.print(table)


# Run analysis
chat_log_path = "data/user_chat_history.md"
output_style_profile = "data/user_style_profile.json"

user_responses = load_chat_log(chat_log_path)
style_profile = analyze_text_patterns(user_responses)
save_style_profile(style_profile, output_style_profile)
display_results(style_profile)

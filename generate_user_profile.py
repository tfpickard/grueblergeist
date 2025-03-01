#!/usr/bin/env python3
"""
Generate a detailed user profile from OpenAI conversation data.
Processes the data in chunks to avoid API usage limits.
"""

import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import os
import logging
from typing import List
from rich.console import Console
from rich.table import Table

logging.basicConfig(filename="profile_build.log", level=logging.INFO, format="%(asctime)s %(message)s")

console = Console()

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
    response = client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=500,
    temperature=0.3)
    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        console.print("[bold red]JSON decoding failed![/bold red]")
        console.print(f"[yellow]Raw response:[/yellow] {content}")
        raise e

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
    console.print("[bold cyan]Loading conversations...[/bold cyan]")
    conversations = load_conversations(CONVERSATIONS_PATH)
    console.print(f"[green]Loaded {len(conversations)} conversations.[/green]")

    console.print("[bold cyan]Chunking conversations...[/bold cyan]")
    chunks = chunk_conversations(conversations, CHUNK_SIZE)
    console.print(f"[green]Created {len(chunks)} chunks.[/green]")

    profiles = []
    logging.info("Starting profile analysis.")
    for idx, chunk in enumerate(chunks, start=1):
        console.print(f"[bold cyan]Analyzing chunk {idx}/{len(chunks)}...[/bold cyan]")
        profile = analyze_chunk(chunk)
        profiles.append(profile)
        logging.info(f"Chunk {idx} analyzed: {json.dumps(profile)}")
        console.print(f"[green]Chunk {idx} analyzed successfully.[/green]")

    console.print("[bold cyan]Consolidating profiles...[/bold cyan]")
    logging.info("Starting profile consolidation.")
    consolidated_profile = consolidate_profiles(profiles)
    logging.info(f"Consolidated profile: {json.dumps(consolidated_profile)}")

    table = Table(title="Consolidated User Profile")
    table.add_column("Attribute", style="magenta", no_wrap=True)
    table.add_column("Values", style="yellow")

    for key, values in consolidated_profile.items():
        table.add_row(key, ", ".join(values))

    console.print(table)

    save_profile(consolidated_profile, STYLE_PROFILE_PATH)
    console.print(f"[bold green]User style profile saved to {STYLE_PROFILE_PATH}[/bold green]")

if __name__ == "__main__":
    main()

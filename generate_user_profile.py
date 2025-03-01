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
import logging
import os
import re
from typing import List

from rich.console import Console
from rich.table import Table

logging.basicConfig(
    filename="profile_build.log", level=logging.INFO, format="%(asctime)s %(message)s"
)

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
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def analyze_chunk(chunk: str, max_retries: int = 3) -> dict:
    """Analyze a chunk of conversation data using OpenAI with retries."""
    prompt = f"""
    Analyze the following conversation data and provide a JSON summary with keys:
    "tone", "style", "common_phrases", "preferred_topics".

    Conversation Data:
    {chunk}
    """
    for attempt in range(1, max_retries + 1):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            console.print(
                f"[bold red]JSON decoding failed on attempt {attempt}/{max_retries}![/bold red]"
            )
            console.print(f"[yellow]Raw response:[/yellow]\n{content}")
            logging.warning(f"Badly formatted JSON response:\n{content}")
            logging.warning(
                f"JSON decoding failed on attempt {attempt}/{max_retries}. Raw response: {content}"
            )
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                extracted_json = json_match.group(0)
                try:
                    return json.loads(extracted_json)
                except json.JSONDecodeError:
                    logging.warning(
                        f"Extracted JSON also failed to decode: {extracted_json}"
                    )
    raise ValueError("Failed to decode JSON after multiple retries.")


def consolidate_profiles(profiles: List[dict]) -> dict:
    """Consolidate multiple profiles into a single profile."""
    # This is a simple example; you might want to implement a more sophisticated consolidation logic
    consolidated = {
        "tone": [],
        "style": [],
        "common_phrases": [],
        "preferred_topics": [],
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
    console.print(
        f"[bold green]User style profile saved to {STYLE_PROFILE_PATH}[/bold green]"
    )

    console.print("[bold cyan]Generating detailed persona analysis...[/bold cyan]")
    persona_prompt = f"""
    Given the following user style profile, generate an extremely detailed persona description.
    Include personality traits, likely interests, communication style, and any other relevant details.

    User Style Profile:
    {json.dumps(consolidated_profile, indent=2)}
    """

    persona_response = client.chat.completions.create(
        model="gpt-4.5-preview",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in user profiling and persona creation.",
            },
            {"role": "user", "content": persona_prompt},
        ],
        max_tokens=1000,
        temperature=0.5,
    )

    detailed_persona = persona_response.choices[0].message.content.strip()

    persona_path = "data/detailed_persona.txt"
    with open(persona_path, "w", encoding="utf-8") as persona_file:
        persona_file.write(detailed_persona)

    console.print(
        f"[bold green]Detailed persona analysis saved to {persona_path}[/bold green]"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Process interrupted by user (Ctrl+C). Exiting gracefully...[/bold red]")

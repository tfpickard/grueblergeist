#!/usr/bin/env python3
"""
Generate a detailed user profile from OpenAI conversation data.
Processes the data in chunks to avoid API usage limits.
"""

import json
import logging
import os
import random
import re
import signal
from datetime import datetime, timedelta
from typing import Any, List, Tuple

from openai import OpenAI
from rich import print
from rich.console import Console, Group
from rich.table import Table

logging.basicConfig(
    filename="profile_build.log", level=logging.INFO, format="%(asctime)s %(message)s"
)

console = Console()

# File paths
CONVERSATIONS_PATH = "data/conversations.json"
STYLE_PROFILE_PATH = "data/user_style_profile.json"
CHUNK_SIZE = 6000  # Approx. characters per chunk

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_conversations(file_path: str) -> List[dict]:
    """Load conversations from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def chunk_conversations(conversations: List[dict], chunk_size: int) -> List[str]:
    """Chunk conversations into manageable pieces."""
    text = json.dumps(conversations)
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def analyze_chunk(chunk: str, max_retries: int = 3) -> Tuple[dict, Any]:
    """Analyze a chunk of conversation data using OpenAI with retries."""
    prompt = f"""
    Analyze the following conversation data and provide a JSON summary with keys:
    "tone", "style", "common_phrases", "preferred_topics", "average_sentence_length", "vocabulary_richness".

    Conversation Data:
    {chunk}
    """
    for attempt in range(1, max_retries + 1):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        try:
            return json.loads(content), response
        except json.JSONDecodeError:
            console.print(
                f"[bold red]JSON decoding failed on attempt {attempt}/{max_retries}![/bold red]"
            )
            # console.print(f"[yellow]Raw response:[/yellow]\n{content}")
            logging.warning(f"Badly formatted JSON response:\n{content}")
            logging.warning(
                f"JSON decoding failed on attempt {attempt}/{max_retries}. Raw response: {content}"
            )
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                extracted_json = json_match.group(1)
                try:
                    return json.loads(extracted_json), response
                except json.JSONDecodeError:
                    logging.warning(
                        f"Extracted JSON also failed to decode: {extracted_json}"
                    )
    raise ValueError("Failed to decode JSON after multiple retries.")


def consolidate_profiles(profiles: List[dict], chunks: List[str]) -> dict:
    """Consolidate multiple profiles into a single profile."""
    # This is a simple example; you might want to implement a more sophisticated consolidation logic
    consolidated = {
        "tone": [],
        "style": [],
        "common_phrases": [],
        "preferred_topics": [],
        "average_sentence_length": 0,
        "vocabulary_richness": 0,
    }
    for profile in profiles:
        for key in consolidated.keys():
            v = profile.get(key)
            if key in ["average_sentence_length", "vocabulary_richness"]:
                consolidated[key] += v if isinstance(v, (int, float)) else 0
            else:
                if isinstance(v, str):
                    v = re.split(r",|and", v)
                    v = [x.strip() for x in v if x.strip()]
                elif isinstance(v, list):
                    v = [x for x in v if isinstance(x, str)]
                elif not isinstance(v, list):
                    v = [f"{v}"]
                consolidated[key].extend(v)
    # Remove duplicates for list-type keys
    for key in ["tone", "style", "common_phrases", "preferred_topics"]:
        consolidated[key] = list(set(consolidated[key]))

    # Calculate average sentence length and vocabulary richness
    total_sentences = sum(len(re.split(r"[.!?]", chunk)) for chunk in chunks)
    total_words = sum(len(chunk.split()) for chunk in chunks)
    consolidated["average_sentence_length"] = (
        total_words / total_sentences if total_sentences > 0 else 0
    )
    unique_words = set(word for chunk in chunks for word in chunk.split())
    consolidated["vocabulary_richness"] = (
        len(unique_words) / total_words if total_words > 0 else 0
    )

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
    total_time = 0
    total_cost = 0.0
    cost_per_token = 0.000002  # Example cost per token for gpt-3.5-turbo
    actual_times = []  # Track actual times for each chunk
    chunk_sizes = []  # Track sizes of each chunk
    interrupted = False
    rolling_window_size = 10
    total_words = 0  # Track total words processed

    def signal_handler(sig, frame):
        nonlocal interrupted
        if interrupted:
            console.print(
                "\n[bold red]Process interrupted again. Exiting immediately...[/bold red]"
            )
            exit(1)
        console.print(
            "\n[bold yellow]Process interrupted. Finalizing current chunk and generating profile...[/bold yellow]"
        )
        interrupted = True

    signal.signal(signal.SIGINT, signal_handler)
    logging.info("Starting profile analysis.")
    total_bytes = 0
    for idx, chunk in enumerate(chunks, start=0):
        total_bytes += len(chunk)
    random.shuffle(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        console.print(
            f"[bold cyan]Analyzing {len(chunk)}-byte chunk {idx}/{len(chunks)}...[/bold cyan]"
        )
        if interrupted:
            break

        start_time = datetime.now()
        profile, response = analyze_chunk(chunk)
        end_time = datetime.now()
        tokens_used = response.usage.total_tokens
        total_cost += tokens_used * cost_per_token
        chunk_size = len(chunk)
        word_count = len(chunk.split())
        total_words += word_count
        chunk_sizes.append(chunk_size)
        elapsed_time = (end_time - start_time).total_seconds()
        total_time += elapsed_time

        # Calculate rolling average of time per API call
        if len(actual_times) > rolling_window_size:
            rolling_avg_time = (
                sum(actual_times[-rolling_window_size:]) / rolling_window_size
            )
        else:
            if len(actual_times) > 0:
                rolling_avg_time = sum(actual_times) / len(actual_times)
            else:
                rolling_avg_time = 999

        # Estimate completion
        actual_times.append(elapsed_time)
        avg_time_per_char = total_time / sum(chunk_sizes) if sum(chunk_sizes) > 0 else 0
        avg_time_per_word = total_time / total_words if total_words > 0 else 0
        percent_complete = (idx + 1) / len(chunks) * 100
        # remaining_chars = sum(chunk_sizes[(idx - 1):])
        remaining_chars = total_bytes - sum(chunk_sizes)
        # print(f"Chunk {idx} size: {chunk_sizes[idx-1]}")
        print(f"Remaining chars: {remaining_chars}")
        estimated_time_remaining = (
            avg_time_per_char * remaining_chars if remaining_chars > 0 else 999
        )

        table = Table(title=f"Chunk {idx}/{len(chunks)} Analysis")

        table.add_column("Metric", style="magenta")
        table.add_column("Value", style="cyan")

        table.add_row("Elapsed Time (s)", f"{elapsed_time:.2f}")
        table.add_row("Percent Complete", f"{percent_complete:.2f}%")
        estimated_time_remaining_hms = str(
            timedelta(seconds=int(estimated_time_remaining))
        )
        table.add_row("Average Time per Word (s)", f"{avg_time_per_word:.4f}")
        table.add_row(
            "Estimated Time Remaining (hh:mm:ss)", estimated_time_remaining_hms
        )
        total_elapsed_time_hms = str(timedelta(seconds=int(total_time)))
        table.add_row("Total Elapsed Time (hh:mm:ss)", total_elapsed_time_hms)
        table.add_row("Rolling Avg Time per Call (s)", f"{rolling_avg_time:.2f}")
        table.add_row("Total Cost ($)", f"{total_cost:.6f}")

        console.print(Group(table))
        profiles.append(profile)
        logging.info(f"Chunk {idx} analyzed: {json.dumps(profile)}")
        console.print(f"[green]Chunk {idx} analyzed successfully.[/green]")

    console.print(
        f"[bold green]Total cost of API calls: ${total_cost:.6f}[/bold green]"
    )

    if interrupted:
        console.print(
            "[bold yellow]Interrupted: Generating profile from current progress...[/bold yellow]"
        )
    logging.info("Starting profile consolidation.")
    consolidated_profile = consolidate_profiles(profiles, chunks)
    logging.info(f"Consolidated profile: {json.dumps(consolidated_profile)}")

    table = Table(title="Consolidated User Profile")
    table.add_column("Attribute", style="magenta", no_wrap=True)
    table.add_column("Values", style="yellow")

    for key, values in consolidated_profile.items():
        table.add_row(key, ", ".join(values))
        # print(f"  >>>  {key} = -->|{values}|")

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
        model="gpt-4o",
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

    persona_path = "data/detailed_persona.md"
    with open(persona_path, "w", encoding="utf-8") as persona_file:
        persona_file.write(detailed_persona)

    console.print(
        f"[bold green]Detailed persona analysis saved to {persona_path}[/bold green]"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(
            "\n[bold red]Process interrupted by user (Ctrl+C). Exiting gracefully...[/bold red]"
        )

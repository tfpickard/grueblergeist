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


def extract_conversations(conversations: List[dict]) -> List[str]:
    """Extract individual conversations for analysis."""
    extracted_conversations = []
    random.shuffle(conversations)
    for convo in conversations:
        if "mapping" not in convo:
            continue
        messages = []
        for turn in convo["mapping"].values():
            if isinstance(turn, dict) and "message" in turn:
                message = turn["message"]
                if message and message.get("author", {}).get("role") == "user":
                    content = message.get("content", {})
                    if isinstance(content, str):
                        messages.append(content)
                    elif isinstance(content, dict) and "parts" in content:
                        part = content["parts"][0]
                        if isinstance(part, str):
                            messages.append(part)
        extracted_conversations.append(" ".join(messages))
    return extracted_conversations


def analyze_chunk(chunk: str, max_retries: int = 3) -> Tuple[dict, Any]:
    """Analyze a chunk of conversation data using OpenAI with retries."""
    prompt = f"""
    Analyze the following conversation data and provide a JSON summary with keys:
    "tone", "style", "common_phrases", "preferred_topics", "average_sentence_length", "vocabulary_richness",
    "sentiment", "response_time_patterns", "engagement_level", "topic_diversity", "question_frequency".

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
            # console.print(f"[bold red]Raw response:[/bold red]\n[red]{content}[/red]")
            if attempt > 1:
                console.print(
                    f"[bold yellow]JSON decoding failed on attempt {attempt}/{max_retries}![/bold yellow]"
                )
                logging.warning(f"Badly formatted JSON response:\n{content}")
                logging.warning(
                    f"JSON decoding failed on attempt {attempt}/{max_retries}. Raw response: {content}"
                )
            # json_match = re.search(r"```json\s*({.*?})\s*```", content, re.DOTALL)
            # if not json_match:
            # json_match = re.search(r"({.*?})", content, re.DOTALL)
            # if not json_match:
            json_match = re.search(r"({.*?})", content, re.DOTALL)

            if json_match:
                extracted_json = json_match.group(1)
                try:
                    return json.loads(extracted_json), response
                except json.JSONDecodeError:
                    logging.warning(
                        f"Extracted JSON also failed to decode: {extracted_json}"
                    )
    console.print("[bold red]Failed to decode JSON after multiple retries. Skipping this conversation.[/bold red]")
    console.print("[bold red]Last raw response:[/bold red]\n", content)
    return {}, None


def consolidate_profiles(profiles: List[dict], chunks: List[str]) -> dict:
    """Consolidate multiple profiles into a single profile."""
    # This is a simple example; you might want to implement a more sophisticated consolidation logic
    consolidated = {
        "tone": [],
        "style": [],
        "common_phrases": [],
        "preferred_topics": [],
        "average_sentence_length": 0.0,
        "vocabulary_richness": 0.0,
        "sentiment": "neutral",
        "response_time_patterns": [],
        "engagement_level": 0.0,
        "topic_diversity": 0.0,
        "question_frequency": 0.0,
    }
    for profile in profiles:
        for key in consolidated.keys():
            v = profile.get(key)
            if key in ["average_sentence_length", "vocabulary_richness"]:
                consolidated[key] += v if isinstance(v, (int, float)) else 0
            elif key in ["sentiment"]:
                # Handle sentiment as a single string value
                consolidated[key] = v if isinstance(v, str) else consolidated[key]
            else:
                if isinstance(v, str):
                    v = re.split(r",|and", v)
                    v = [x.strip() for x in v if x.strip()]
                elif isinstance(v, list):
                    v = [x for x in v if isinstance(x, str)]
                # elif not isinstance(v, list):
                else:
                    v = [f"{v}"]
                # print(v)
                # print(consolidated[key])
                if not isinstance(consolidated[key], list):
                    consolidated[key] = [] # [f"{consolidated[key]}"]
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

    # Calculate sentiment, response time patterns, engagement level, topic diversity, and question frequency
    consolidated["sentiment"] = calculate_sentiment(profiles)
    consolidated["response_time_patterns"] = calculate_response_time_patterns(profiles)
    consolidated["engagement_level"] = calculate_engagement_level(profiles)
    consolidated["topic_diversity"] = calculate_topic_diversity(profiles)
    consolidated["question_frequency"] = calculate_question_frequency(profiles)

    return consolidated


def calculate_sentiment(profiles: List[dict]) -> str:
    """Calculate the overall sentiment from profiles."""
    # Placeholder logic for sentiment calculation
    sentiments = [profile.get("sentiment", "neutral") for profile in profiles]
    return max(set(sentiments), key=sentiments.count)

def calculate_response_time_patterns(profiles: List[dict]) -> List[str]:
    """Calculate response time patterns from profiles."""
    # Placeholder logic for response time patterns
    return ["consistent", "varied"]

def calculate_engagement_level(profiles: List[dict]) -> int:
    """Calculate engagement level from profiles."""
    # Placeholder logic for engagement level
    total_engagement = 0
    for profile in profiles:
        level = profile.get("engagement_level", 0)
        if isinstance(level, str):
            # Convert string levels to numeric values
            level = convert_engagement_level_to_numeric(level)
        total_engagement += level
    return total_engagement / len(profiles)

def convert_engagement_level_to_numeric(level: str) -> int:
    """Convert string engagement levels to numeric values."""
    level_mapping = {
        "low": 1,
        "medium": 2,
        "high": 3
    }
    x = 1
    if "low" in level.lower():
        x = 1
    elif "med" in level.lower() or "mod" in level.lower():
        x = 50
    elif "high" in level.lower():
        x = 100
    
        
    return x #level_mapping.get(level.lower(), 0)

def calculate_topic_diversity(profiles: List[dict]) -> int:
    """Calculate topic diversity from profiles."""
    # Placeholder logic for topic diversity
    topics = [topic for profile in profiles for topic in profile.get("preferred_topics", [])]
    unique_topics = set()
    for topic in topics:
        if isinstance(topic, str):
            unique_topics.add(topic)
        elif isinstance(topic, (int, float)):
            unique_topics.add(str(topic))
    return float(len(unique_topics))

def calculate_question_frequency(profiles: List[dict]) -> int:
    """Calculate question frequency from profiles."""
    # Placeholder logic for question frequency
    total_questions = 0
    for profile in profiles:
        frequency = profile.get("question_frequency", 0)
        if isinstance(frequency, str):
            # Convert string frequencies to numeric values
            # frequency = convert_question_frequency_to_numeric(frequency)
            frequency = convert_engagement_level_to_numeric(frequency)
        total_questions += frequency
    return total_questions / len(profiles)

def convert_question_frequency_to_numeric(frequency: str) -> int:
    """Convert string question frequencies to numeric values."""
    frequency_mapping = {
        "low": 1,
        "medium": 2,
        "high": 3
    }
    return frequency_mapping.get(frequency.lower(), 0)
def save_profile(profile: dict, file_path: str) -> None:
    """Save the consolidated profile to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)


def main():
    console.print("[bold cyan]Loading conversations...[/bold cyan]")
    conversations = load_conversations(CONVERSATIONS_PATH)
    console.print(f"[green]Loaded {len(conversations)} conversations.[/green]")

    console.print("[bold cyan]Extracting individual conversations...[/bold cyan]")
    extracted_conversations = extract_conversations(conversations)
    console.print(
        f"[green]Extracted {len(extracted_conversations)} conversations.[/green]"
    )

    profiles = []
    total_time = 0
    total_cost = 0.0
    cost_per_token = 0.15 / 1e6  # Cost per token in dollars
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
    for idx, conversation in enumerate(extracted_conversations, start=0):
        total_bytes += len(conversation)
    # random.shuffle(chunks)
    for idx, conversation in enumerate(extracted_conversations, start=1):
        console.print(
            f"[bold cyan]Analyzing conversation {idx}/{len(extracted_conversations)}...[/bold cyan]"
        )
        if interrupted:
            break

        start_time = datetime.now()
        profile, response = analyze_chunk(conversation)
        end_time = datetime.now()
        if response is not None:
            tokens_used = response.usage.total_tokens
            total_cost += tokens_used * cost_per_token
        chunk_size = len(conversation)
        word_count = len(conversation.split())
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
        percent_complete = (idx + 1) / len(extracted_conversations) * 100
        # remaining_chars = sum(chunk_sizes[(idx - 1):])
        remaining_chars = total_bytes - sum(chunk_sizes)
        # print(f"Chunk {idx} size: {chunk_sizes[idx-1]}")
        print(f"Remaining chars: {remaining_chars}")
        estimated_time_remaining = (
            avg_time_per_char * remaining_chars if remaining_chars > 0 else 999
        )

        table = Table(
            title=f"Conversation {idx}/{len(extracted_conversations)} Analysis"
        )

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
    consolidated_profile = consolidate_profiles(profiles, extracted_conversations)
    logging.info(f"Consolidated profile: {json.dumps(consolidated_profile)}")

    table = Table(title="Consolidated User Profile")
    table.add_column("Attribute", style="magenta", no_wrap=True)
    table.add_column("Values", style="yellow")

    for key, values in consolidated_profile.items():
        if isinstance(values, list):
            table.add_row(key, ", ".join(values))
        else:
            table.add_row(key, str(values))
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

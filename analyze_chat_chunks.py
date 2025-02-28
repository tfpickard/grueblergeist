#!/usr/bin/env python3
"""
Multi-chunk approach to analyzing a large chat history with GPT-4, with multi-level summary consolidation.

Flow:
1) Read large chat file (data/user_chat_history.md).
2) Break it into ~6000-character chunks to avoid GPT-4's token limit.
3) Summarize each chunk individually with GPT-4.
4) Consolidate partial summaries in multiple passes until we get a final style profile.

Features:
- Rich-based verbose console output
- "stop_early" flag to limit chunk processing to 5 chunks
- Multi-level consolidation to handle hundreds of partial summaries
"""

import json
import math
import os
import time

import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
CHAT_LOG_PATH = "data/user_chat_history.md"  # Large chat text in Markdown
STYLE_PROFILE_PATH = "data/user_style_profile.json"
CHUNK_SIZE = 6000  # Approx. characters per chunk
BATCH_SIZE = 10  # Summaries per pass in multi-level consolidation
STOP_EARLY = False  # If True, only process first 5 chunks to keep it short
SLEEP_ON_RATE_LIMIT = 30  # seconds to sleep if we hit rate limit

console = Console()


# -------------------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------------------
def main():
    # if not openai.api_key:
    #     console.print("[bold red]Error:[/] OPENAI_API_KEY is not set.", style="red")
    #     return

    # 1. Load chat text
    chat_text = load_chat_history(CHAT_LOG_PATH)
    if not chat_text:
        console.print(f"[red]No chat history found at {CHAT_LOG_PATH}[/]")
        return

    # 2. Chunk the chat
    chunks = chunk_text(chat_text, chunk_size=CHUNK_SIZE)
    console.print(
        Panel.fit(
            f"Loaded [yellow]{len(chunks)}[/yellow] chunks from [cyan]{CHAT_LOG_PATH}[/cyan].",
            title="Chat History Loaded",
        )
    )

    # Optionally stop early
    if STOP_EARLY and len(chunks) > 5:
        console.print(
            "[bold magenta]stop_early=True, limiting chunk processing to 5 chunks.[/bold magenta]"
        )
        chunks = chunks[:5]

    if not chunks:
        console.print("[red]No chunks to process.[/red]")
        return

    # 3. Summarize each chunk individually
    chunk_summaries = []
    for i, chunk in enumerate(
        track(chunks, description="Summarizing chunks...", console=console)
    ):
        summary = summarize_chunk(chunk, i + 1, len(chunks))
        chunk_summaries.append(summary)

    # 4. Multi-level consolidation of chunk summaries
    console.print("[blue]Multi-level consolidation of chunk summaries...[/blue]")
    style_profile = multi_level_consolidation(chunk_summaries, batch_size=BATCH_SIZE)

    if not style_profile:
        console.print(
            "[bold red]Error:[/] Could not consolidate style profile. Aborting."
        )
        return

    # 5. Save final style profile
    with open(STYLE_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(style_profile, f, indent=4)

    console.print(
        Panel.fit(
            f"Done! Style profile saved to [green]{STYLE_PROFILE_PATH}[/green].",
            title="Success",
        )
    )


# -------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------
def load_chat_history(path: str) -> str:
    """Reads the user chat history from a Markdown file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def chunk_text(text: str, chunk_size: int = 6000) -> list[str]:
    """
    Breaks text into ~chunk_size characters to keep GPT-4 requests manageable.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks


def summarize_chunk(chunk_text: str, chunk_index: int, total_chunks: int) -> str:
    """
    Sends chunk_text to GPT-4 for a brief summary focusing on style/tone.
    Returns a short chunk summary (string).
    """
    prompt = f"""
Please summarize the following portion of the user's chat. Focus on
unusual words, phrases, tone, or style elements that stand out.

Chunk {chunk_index}/{total_chunks}:
{chunk_text}
"""
    try:
        response = call_openai_chat(prompt)
        summary = response.strip()
        # Print a snippet to console
        console.log(
            f"[bold magenta]Chunk {chunk_index} Summary Snippet:[/] "
            f"{summary[:100]}{'...' if len(summary) > 100 else ''}"
        )
        return summary
    except Exception as e:
        console.print(f"[red]Error summarizing chunk {chunk_index}:[/] {e}")
        return ""


def multi_level_consolidation(chunk_summaries: list[str], batch_size: int) -> dict:
    """
    Consolidates a large list of chunk summaries in multiple passes, preventing token overload.

    1) If only 1 summary, parse it as final JSON or prompt GPT for final JSON.
    2) If <= batch_size, combine them in a single pass -> final JSON
    3) Otherwise, break them into groups of `batch_size`. Summarize each group -> partial_summaries
       Then recursively call multi_level_consolidation() on partial_summaries
    """
    # Base case: if we have only 1 summary
    if len(chunk_summaries) == 1:
        # Try parsing as JSON first
        try:
            # If the single summary is already valid JSON, return it
            return json.loads(chunk_summaries[0])
        except:
            # Otherwise pass it to GPT for final JSON
            return pass_through_gpt_for_json(chunk_summaries[0])

    # If we have <= batch_size, do a single pass
    if len(chunk_summaries) <= batch_size:
        combined_text = ""
        for i, summary in enumerate(chunk_summaries):
            combined_text += f"Summary {i+1}:\n{summary}\n\n"
        return pass_through_gpt_for_json(combined_text)

    # If more than batch_size, break into smaller groups
    group_count = math.ceil(len(chunk_summaries) / batch_size)
    partial_summaries = []
    index = 0
    for group_index in range(group_count):
        batch = chunk_summaries[index : index + batch_size]
        index += batch_size

        # Combine this group's partial summaries
        combined_text = ""
        for i, summary in enumerate(batch):
            combined_text += f"Summary {i+1}:\n{summary}\n\n"

        console.print(
            f"[blue]Consolidating group {group_index+1}/{group_count} of size {len(batch)}[/blue]"
        )
        partial_summary_json = pass_through_gpt_for_json(combined_text)
        # We'll convert partial_summary_json back to a string (for next pass)
        partial_summaries.append(json.dumps(partial_summary_json))

    # Now partial_summaries is a smaller list
    return multi_level_consolidation(partial_summaries, batch_size)


def pass_through_gpt_for_json(combined_text: str) -> dict:
    """
    Sends combined_text to GPT-4 to produce final style profile in JSON format
    with keys: "tone", "style", "common_phrases", "preferred_topics".

    If GPT returns invalid JSON or rate-limit error, we handle it.
    """
    final_prompt = f"""
We have multiple partial summaries of a user's chat. Combine them into a single
persona/style profile. Return valid JSON with keys: 
"tone", "style", "common_phrases", "preferred_topics".

Partial Summaries:
{combined_text}
"""
    try:
        raw = call_openai_chat(final_prompt)
        # Attempt to parse JSON
        console.log("[bold green]Partial Consolidation Response:[/]", raw[:150], "...")
        return json.loads(raw)
    except Exception as e:
        console.print(f"[red]Error in pass_through_gpt_for_json:[/] {e}")
        return {}


def call_openai_chat(prompt: str) -> str:
    """
    Calls GPT-4 with a user prompt, returning the raw string content.
    Includes minimal error handling, rate-limit retries.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a language model that returns only JSON. No extra commentary or markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        console.print(f"[bold red]Rate limit exceeded:[/] {e}")
        console.print(f"[yellow]Sleeping {SLEEP_ON_RATE_LIMIT} seconds...[/yellow]")
        time.sleep(SLEEP_ON_RATE_LIMIT)
        # retry once
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a language model that returns only JSON. No extra commentary or markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content

    except Exception as e:
        raise e


if __name__ == "__main__":
    main()

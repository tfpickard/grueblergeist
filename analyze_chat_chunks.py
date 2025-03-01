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
import random
import time
import signal
from typing import Optional
from datetime import datetime

import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from rich import print
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
STOP_EARLY = True  # If True, only process first 5 chunks to keep it short
SLEEP_ON_RATE_LIMIT = 30  # seconds to sleep if we hit rate limit
mu = 1.5
sigma = 2
console = Console()


# -------------------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------------------
def main():
    interrupted = False

    def signal_handler(sig, frame):
        nonlocal interrupted
        if interrupted:
            console.print(
                "\n[bold red]Process interrupted again. Exiting immediately...[/bold red]"
            )
            exit(1)
        console.print(
            f"[bold blue]Average actual time per chunk: {avg_actual_time:.2f}s.[/bold blue]"
            "\n[bold yellow]Process interrupted. Finalizing current chunk and generating profile...[/bold yellow]"
        )
        interrupted = True

    signal.signal(signal.SIGINT, signal_handler)
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
    if False and STOP_EARLY and len(chunks) > 5:
        console.print(
            "[bold magenta]stop_early=True, limiting chunk processing to 5 chunks.[/bold magenta]"
        )
        chunks = chunks[:5]

    if not chunks:
        console.print("[red]No chunks to process.[/red]")
        return

    # 3. Summarize each chunk individually
    chunk_summaries = []
    nchunks = 0
    total_time = 0
    total_cost = 0.0
    cost_per_token = 0.000002  # Example cost per token for gpt-3.5-turbo
    actual_times = []  # Track actual times for each chunk
    total_cost = 0.0
    cost_per_token = 0.000002  # Example cost per token for gpt-3.5-turbo
    for i, chunk in enumerate(
        track(chunks, description="Summarizing chunks...", console=console)
    ):
        if interrupted:
            break
        if STOP_EARLY and i >= 40:
            break
        if len(chunk) - i < 10:
            break
        x = 0
        while x <= 0.0:
            x = random.normalvariate(mu, sigma)
        x = int(x)

        if STOP_EARLY and i % (1 + x) != 0:
            # print(f"Skipping chunk {i}...")
            continue
        else:
            nchunks += 1
            # print(f"Chunk {nchunks} of {len(chunks)}")

        start_time = datetime.now()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": chunk},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        total_cost += tokens_used * cost_per_token
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        total_time += elapsed_time

        actual_times.append(elapsed_time)

        # Estimate completion
        avg_actual_time = sum(actual_times) / len(actual_times)
        percent_complete = (i + 1) / len(chunks) * 100
        avg_time_per_chunk = total_time / (i + 1)
        estimated_time_remaining = avg_time_per_chunk * (len(chunks) - (i + 1))

        console.print(
            f"[bold cyan]Chunk {i + 1}/{len(chunks)} processed in {elapsed_time:.2f}s.[/bold cyan]"
        )
        console.print(
            f"[bold green]Estimated {percent_complete:.2f}% complete. "
            f"Estimated time remaining: {estimated_time_remaining:.2f}s.[/bold green]"
        )
        chunk_summaries.append(summary)
    console.print(
        f"[bold green]Total cost of API calls: ${total_cost:.6f}[/bold green]"
    )
    print(f"Summarized {nchunks} chunks of {len(chunks)} ({nchunks/len(chunks)*100}%)")
    if interrupted:
        console.print(
            "[bold yellow]Interrupted: Generating profile from current progress...[/bold yellow]"
        )

    # 4. Multi-level consolidation of chunk summaries
    console.print(
        f"[blue]Multi-level consolidation of {nchunks} chunk summaries...[/blue]"
    )
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
        y = ""
        for i, summary in enumerate(chunk_summaries):
            combined_text += f"Summary {i+1}:\n{summary}\n\n"
            x = pass_through_gpt_for_json(combined_text)
            if len(x) > 4:
                y = combined_text
            else:
                break
        if len(y) == 0:
            y = "{}"
        print(f" y Combined text: {y}")
        return json.loads(y)

    # If more than batch_size, break into smaller groups
    group_count = math.ceil(len(chunk_summaries) / batch_size)
    partial_summaries = []
    index = 0
    for group_index in range(group_count):
        batch = chunk_summaries[index : index + batch_size]
        index += batch_size

        # Combine this group's partial summaries
        combined_text = ""
        y = ""
        for i, summary in enumerate(batch):
            combined_text += f"Summary {i+1}:\n{summary}\n\n"
            x = pass_through_gpt_for_json(combined_text)
            if len(x) > 4:
                y = combined_text
            else:
                break
        combined_text = y
        console.print(
            f"[blue]Consolidating group {group_index+1}/{group_count} of size {len(batch)}[/blue]"
        )
        print(1)
        partial_summary_json = pass_through_gpt_for_json(combined_text)
        # We'll convert partial_summary_json back to a string (for next pass)
        print(2)
        partial_summaries.append(json.dumps(partial_summary_json))

    # Now partial_summaries is a smaller list
    return multi_level_consolidation(partial_summaries, batch_size)


def pass_through_gpt_for_json(combined_text: str, max_retries: int = 2) -> dict:
    """
    Sends combined_text to GPT-4 to produce final style profile in JSON format
    with keys: "tone", "style", "common_phrases", "preferred_topics".

    We do a salvage parse to handle truncated or extra text beyond the JSON.
    If it fails, we optionally retry a few times.
    """
    final_prompt = f"""
We have multiple partial summaries of a user's chat. Combine them into a single
persona/style profile. Return valid JSON with keys: 
"tone", "style", "common_phrases", "preferred_topics".

Partial Summaries (keep your JSON as short as possible, no extra arrays, no multiline strings):
{combined_text}

IMPORTANT:
- Output must be strictly valid JSON, no leading or trailing text outside the outermost braces.
- Do not exceed ~500 tokens if possible.
"""
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        try:
            raw = call_openai_chat(final_prompt)
            console.log(
                f"[bold green]Partial Consolidation Response (attempt {attempt}):[/] {raw}..."
            )

            # salvage parse
            parsed = salvage_json_substring(raw)
            if parsed is not None:
                return parsed
            else:
                console.print(
                    f"[red]Failed to parse JSON on attempt {attempt}, retrying...[/red]"
                )
        except Exception as e:
            console.print(
                f"[red]Error in pass_through_gpt_for_json attempt {attempt}:[/] {e}"
            )

    # if all attempts fail
    console.print(
        "[bold red]All parse attempts failed. Returning empty profile.[/bold red]"
    )
    return {}


def salvage_json_substring(raw_str: str) -> Optional[dict]:
    """
    Attempt to find the first '{' and last '}' in raw_str, parse that substring as JSON.
    If it fails, return None.
    """
    start_idx = raw_str.find("{")
    end_idx = raw_str.rfind("}")
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        console.print("[red]Could not find matching braces in GPT output.[/red]")
        return None

    candidate = raw_str[start_idx : end_idx + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        console.print(f"[red]json.JSONDecodeError in salvage_json_substring:[/] {e}")
        return json.loads("{}")


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

#!/usr/bin/env python3
"""
Sends chat history to OpenAI for a detailed style/persona analysis,
and writes the resulting style profile to user_style_profile.json.

Requires openai>=1.0.0
"""

import json
import os

from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
from rich.console import Console

console = Console()

# Path to chat log (Markdown)
CHAT_LOG_PATH = "data/user_chat_history.md"
# Output JSON with style profile
STYLE_PROFILE_PATH = "data/user_style_profile.json"


def main():
    # 1. Load Chat History
    chat_text = load_chat_history(CHAT_LOG_PATH)
    if not chat_text:
        console.print("[red]No chat history found.[/]")
        return

    # 2. Ask OpenAI for Style Analysis
    style_profile = analyze_text_via_openai(chat_text)
    if not style_profile:
        console.print("[red]No style profile returned from OpenAI.[/]")
        return

    # 3. Save to user_style_profile.json
    save_style_profile(style_profile, STYLE_PROFILE_PATH)
    console.print(f"[green]User style profile saved to:[/] {STYLE_PROFILE_PATH}")


def load_chat_history(file_path: str) -> str:
    """Reads the entire user chat history from Markdown and returns it as a string."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        console.print(f"[red]File not found:[/] {file_path}")
        return ""


def analyze_text_via_openai(chat_history: str) -> dict:
    """
    Sends the chat history to OpenAI GPT-4 for a detailed style/persona analysis.
    Returns a dict with keys like tone, style, common_phrases, preferred_topics, etc.

    Requires openai>=1.0.0
    """

    # Make sure your OPENAI_API_KEY is set in environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[red]OPENAI_API_KEY not set![/]")
        return {}

    # We'll ask GPT-4 to parse the entire chat, extracting the user's style
    # The new usage is ChatCompletion.create() for openai>=1.0.0
    prompt = f"""
You are an expert at persona analysis. Analyze the following chat history
and produce a concise JSON summary describing the user's:

1. Overall tone as a list of descriptive words (e.g. ['casual', 'witty', 'technical'])
2. Writing style as a list of descriptive words (e.g. ['concise', 'verbose', 'direct', 'roundabout'])
3. Common phrases or idiomatic expressions they frequently use
4. Preferred topics of conversation or areas of expertise

Provide only valid JSON in your answer with keys: 
"tone", "style", "common_phrases", "preferred_topics"

Chat History:
{chat_history}
"""

    console.print("[cyan]Sending chat history to OpenAI for style analysis...[/]")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a language model that returns only JSON. "
                        "No extra commentary or markdown. "
                        "Be concise and direct in your analysis."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        # The new usage returns a "ChatCompletion" object
        raw_content = response.choices[0].message.content
        console.print("[green]Raw AI Analysis Received:[/]\n", raw_content)

        try:
            # Attempt to parse the raw content as JSON
            style_profile = json.loads(raw_content)
            # Ensure tone and style are lists of strings
            if isinstance(style_profile['tone'], str):
                style_profile['tone'] = [style_profile['tone']]
            if isinstance(style_profile['style'], str):
                style_profile['style'] = [style_profile['style']]
            console.print("[green]Parsed JSON:[/]\n", json.dumps(style_profile, indent=2))
            return style_profile
        except json.JSONDecodeError:
            console.print("[red]Failed to parse JSON response. Raw content:[/]\n", raw_content)
            return {}

    except Exception as e:
        console.print(f"[red]Error calling OpenAI API:[/] {e}")
        return {}


def save_style_profile(profile: dict, file_path: str) -> None:
    """Save the style profile as JSON."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4)


if __name__ == "__main__":
    main()

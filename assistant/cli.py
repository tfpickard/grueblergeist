# assistant/cli.py
"""
Command-line interface for Grüblergeist using Rich.
"""

import logging
from typing import NoReturn

from rich.console import Console
from rich.prompt import Prompt

from .chat_assistant import ChatAssistant

logger = logging.getLogger(__name__)


def run_cli() -> NoReturn:
    """
    Run the command-line interface loop using Rich for formatting.
    Exits on user input of 'quit' or 'exit'.
    """
    console = Console()
    assistant = ChatAssistant()

    console.print(
        "[bold cyan]Welcome to Grüblergeist (CLI Mode)! Type 'quit' or 'exit' to quit.[/bold cyan]"
    )
    logger.info("CLI started. Waiting for user input...")

    while True:
        user_input = Prompt.ask("[bold green]You[/bold green]")
        if user_input.lower() in {"quit", "exit"}:
            console.print("Goodbye!")
            logger.info("User exited CLI.")
            break

        assistant_reply = assistant.reply(user_input)
        console.print(f"[bold magenta]Grüblergeist:[/bold magenta] {assistant_reply}")

    # As a typical CLI loop, it doesn't return; but once broken out, the function ends.
    # If we want to type-annotate that it never returns (strictly), we might do -> None instead of NoReturn.

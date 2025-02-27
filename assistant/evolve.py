# assistant/evolve.py
"""
Self-modification module for Grüblergeist.
Contains functions for taking the current code, requesting improvements from an LLM,
and writing to a new file.
"""

import logging
import os
from typing import Optional

import openai

from .config import get_config_value

logger = logging.getLogger(__name__)


def evolve_code(
    source_file_path: str, output_file_path: str, instructions: Optional[str] = None
) -> None:
    """
    Reads the code from source_file_path, sends it to OpenAI with 'instructions',
    writes the modified code to output_file_path.

    :param source_file_path: Path to the source code file we want to evolve.
    :param output_file_path: Path where the improved code should be written.
    :param instructions: Additional instructions for the code refactoring/evolution.
    """
    evolve_model = get_config_value("evolve_model", "gpt-4")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found; cannot evolve code via OpenAI.")
        return

    openai.api_key = openai_api_key

    if not os.path.exists(source_file_path):
        logger.error(f"Source file not found: {source_file_path}")
        return

    with open(source_file_path, "r", encoding="utf-8") as f:
        code_text = f.read()

    if instructions is None:
        instructions = (
            "Refactor the above code to improve performance and readability. "
            "Keep the functionality the same and preserve all features. "
            "Add comments where necessary. Do not include any extraneous text."
        )

    prompt = f"```python\n{code_text}\n```\n\n{instructions}"

    try:
        response = openai.ChatCompletion.create(
            model=evolve_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        improved_code: str = response["choices"][0]["message"]["content"]
        with open(output_file_path, "w", encoding="utf-8") as out:
            out.write(improved_code)
        logger.info(f"New code written to {output_file_path}")
    except Exception as e:
        logger.error(f"Error evolving code: {e}")


def evolve_self(source_file_path: str, output_file_path: str) -> None:
    """
    Self-evolution function specifically instructing the LLM to preserve the evolve_self logic.

    :param source_file_path: Path to the source code file we want to evolve.
    :param output_file_path: Path where the improved code should be written.
    """
    evolve_model = get_config_value("evolve_model", "gpt-4")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found; cannot self-evolve via OpenAI.")
        return

    openai.api_key = openai_api_key

    if not os.path.exists(source_file_path):
        logger.error(f"Source file not found: {source_file_path}")
        return

    with open(source_file_path, "r", encoding="utf-8") as f:
        code_text = f.read()

    instructions = (
        "Refactor the above code to improve performance and readability. "
        "Retain and possibly improve the evolve_self function. "
        "Ensure that the new program can again perform a similar API call "
        "so that each generation can build on itself. "
        "Return only the revised code in your answer, with proper formatting."
    )

    prompt = f"```python\n{code_text}\n```\n\n{instructions}"

    try:
        response = openai.ChatCompletion.create(
            model=evolve_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        improved_code: str = response["choices"][0]["message"]["content"]
        with open(output_file_path, "w", encoding="utf-8") as out:
            out.write(improved_code)
        logger.info(f"New self-evolved code written to {output_file_path}")
    except Exception as e:
        logger.error(f"Error evolving code: {e}")

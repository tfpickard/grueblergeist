import json
import logging
import math
import random
from typing import Optional

from .config import get_config_value
from .db import get_conversation_history, save_interaction
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class ChatAssistant:
    def __init__(self, user_id: Optional[int] = None):
        self.user_id = (
            user_id if user_id else get_config_value("assistant_user_id", 1234)
        )
        self.llm = LLMClient()

        # Initialize the dynamic threshold randomly between 0.3 and 0.7, for example
        self.dynamic_threshold = random.uniform(0.3, 0.7)
        logger.debug(
            f"[init] Starting dynamic_threshold = {self.dynamic_threshold:.2f}"
        )

    def load_user_style(self) -> dict:
        """
        Load the user style profile from data/user_style_profile.json
        containing keys like 'tone', 'style', 'common_phrases', 'preferred_topics'.
        """
        try:
            with open("data/user_style_profile.json", "r", encoding="utf-8") as f:
                style_data = json.load(f)
                logger.debug(f"[load_user_style] Loaded style profile: {style_data}")
                return style_data
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(
                "[load_user_style] No valid user_style_profile.json found. Using defaults."
            )
            return {}

    def reply(self, user_message: str, strict_enforcement: bool = False) -> str:
        """
        Generate an AI reply.

        If strict_enforcement is True, we do a second LLM call to score how "in-ballpark"
        the user's message is, relative to the user's preferred_topics. Then compare with
        our dynamic_threshold (which changes over time). If score < threshold, we do a snarky shutdown.
        """
        style_data = self.load_user_style()
        tone = style_data.get("tone", "Neutral")
        style = style_data.get("style", "Straightforward")
        common_phrases = style_data.get("common_phrases", [])
        preferred_topics = style_data.get("preferred_topics", [])

        logger.debug(f"[reply] User said: {user_message!r}")
        logger.debug(
            f"[reply] strict_enforcement={strict_enforcement}, preferred_topics={preferred_topics}"
        )
        logger.debug(
            f"[reply] current dynamic_threshold = {self.dynamic_threshold:.2f}"
        )

        if strict_enforcement:
            # 1) Get a relevance score [0..1]
            score = self.score_topic_via_llm(user_message, preferred_topics)
            logger.debug(f"[reply] LLM-based topic score = {score:.2f}")

            # 2) Compare with dynamic_threshold
            if score < self.dynamic_threshold:
                # Off-topic => produce snarky response
                logger.info(
                    "[reply] Shutting down off-topic conversation (strict enforcement)."
                )
                off_topic_reply = self.generate_snarky_off_topic_reply(
                    user_message, preferred_topics
                )
                logger.debug(f"[reply] Snarky response = {off_topic_reply!r}")
                save_interaction(
                    self.user_id, user_message, off_topic_reply, tone_detected=None
                )
                logger.debug("[reply] Off-topic interaction saved to DB.")

                # 3) Update dynamic_threshold with a normal distribution shift
                self.update_threshold(score)
                return off_topic_reply
            else:
                logger.debug("[reply] On-topic enough, continuing conversation.")
                # Also update threshold if we want to push it up
                self.update_threshold(score)

        # Build the system prompt to adopt user’s style
        system_note = (
            "You are Grüblergeist, an AI assistant that mimics the user's style "
            "and steers conversation toward the user's interests. "
            f"Tone: {tone}. Style: {style}. "
            f"Use phrases like: {', '.join(common_phrases)}. "
            "If the user tries to talk about something not in the user's domain, gently steer them "
            "back to the user’s preferred topics, or shut it down if strict_enforcement is on."
        )

        logger.debug(f"[reply] system_note:\n{system_note}")

        history = [("system", system_note)]
        recent_history = get_conversation_history(self.user_id, limit=5)
        logger.debug(f"[reply] Adding last 5 messages to history: {recent_history}")
        history += recent_history

        assistant_reply = self.llm.generate_reply(history, user_message)
        logger.debug(f"[reply] AI reply = {assistant_reply!r}")

        save_interaction(
            self.user_id, user_message, assistant_reply, tone_detected=None
        )
        logger.debug("[reply] Interaction saved to DB.")
        return assistant_reply

    def score_topic_via_llm(
        self, candidate_topic: str, preferred_topics: list[str]
    ) -> float:
        """
        Calls GPT-based LLM to produce a single float [0..1] representing how "in the ballpark"
        the candidate_topic is with respect to the array of preferred_topics.

        Returns 0.0 if not relevant, 1.0 if definitely relevant, or something in between.
        We parse the LLM's response. If it fails, we default to 0.0 or 1.0.
        """

        # If no preferred topics, default to always 1.0
        if not preferred_topics:
            logger.debug(
                "[score_topic_via_llm] No preferred topics => returning 1.0 by default."
            )
            return 1.0

        # Build a prompt
        topics_str = ", ".join(preferred_topics)
        prompt = f"""
You are an AI that only returns a single float between 0 and 1.
Here is the user's list of preferred topics:
{topics_str}

The user has proposed a candidate topic:
{candidate_topic}

Rate how "reasonably within the ballpark" or "a natural extension" it is, relative to the user's preferred topics.
Return a single float between 0.0 and 1.0. No extra text, no JSON.
        """

        logger.debug(f"[score_topic_via_llm] prompt:\n{prompt}")

        # We'll do a minimal LLM call
        response = self.llm.generate_reply([], prompt)
        logger.debug(f"[score_topic_via_llm] raw response = {response!r}")

        # Try parse it as float
        try:
            # If user types "0.75" or "0.2" or "1"
            cleaned = response.strip()
            # remove possible punctuation, then convert
            cleaned = cleaned.rstrip("., ")
            score = float(cleaned)
            if score < 0.0:
                score = 0.0
            elif score > 1.0:
                score = 1.0
            return score
        except ValueError:
            logger.warning(
                "[score_topic_via_llm] Could not parse as float, defaulting to 0.0"
            )
            return 0.0

    def generate_snarky_off_topic_reply(
        self, user_msg: str, preferred_topics: list[str]
    ) -> str:
        """
        Calls the LLM to produce a short, unique, snarky response referencing the off-topic subject,
        then transitions to a random or first domain from preferred_topics.
        """
        if preferred_topics:
            redirect_topic = random.choice(preferred_topics)
        else:
            redirect_topic = "something about your usual interests"

        # We'll craft a minimal prompt
        prompt = f"""
You are an AI that returns ONLY a short, snarky one-liner telling the user that
their topic ("{user_msg}") is off-topic right now, and we want to
redirect them to talk about "{redirect_topic}" instead.
Be witty, be snarky, but no more than 40 words. No extra commentary.
"""

        logger.debug(f"[generate_snarky_off_topic_reply] prompt:\n{prompt}")

        short_response = self.llm.generate_reply([], prompt).strip()
        logger.debug(
            f"[generate_snarky_off_topic_reply] raw short_response = {short_response!r}"
        )

        # fallback if it's too long or not a single line
        words_count = len(short_response.split())
        if words_count > 40 or "\n" in short_response:
            short_response = f"Meh, '{user_msg}' doesn't spark joy. Let's pivot to {redirect_topic}, pronto."
        return short_response

    def update_threshold(self, last_score: float):
        """
        Adjust dynamic_threshold with a normal distribution shift.
        If the user_message was extremely off-topic (score is very low),
        threshold might shift down a bit. If it's quite high, threshold goes up.
        Also add a 10% random bias.
        """
        # Example logic: shift around mean = 0.0 stdev=0.1
        delta = random.gauss(0, 0.1)
        # Weighted by how the last_score compares to threshold
        direction = last_score - self.dynamic_threshold
        # e.g. if direction is negative, threshold tends to shift down
        shift = 0.05 * direction + 0.1 * delta  # 10% random bias plus partial

        new_threshold = self.dynamic_threshold + shift

        # clamp between 0.05 and 0.95
        new_threshold = max(0.05, min(0.95, new_threshold))

        logger.debug(
            f"[update_threshold] old={self.dynamic_threshold:.2f}, last_score={last_score:.2f}, "
            f"delta={delta:.2f}, shift={shift:.2f} => new={new_threshold:.2f}"
        )

        self.dynamic_threshold = new_threshold


def is_on_topic(user_msg: str, preferred_topics: list[str]) -> bool:
    """
    This function is no longer used in strict_enforcement mode,
    but if strict_enforcement=False, you might still use a simpler check.
    Or you can just always rely on LLM scoring. This is here if needed.
    """
    return True

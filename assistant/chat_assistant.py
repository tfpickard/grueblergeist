import json
import logging
import math
import random

from openai import OpenAI

client = OpenAI()
from openai import OpenAI

client = OpenAI()

from .config import get_config_value
from .db import get_conversation_history, save_interaction
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class ChatAssistant:
    def __init__(self, user_id=None):
        self.user_id = (
            user_id if user_id else get_config_value("assistant_user_id", 1234)
        )
        self.llm = LLMClient()
        self.dynamic_threshold = 0.3  # Starts neutral
        self.threshold_momentum = 0.15  # Momentum effect for patience
        self.off_topic_streak = 0
        self.threshold_history = []  # ✅ Store historical patience values
        self.snark_history = []  # ✅ Store historical snark levels
        self.recent_topic_scores = []  # ✅ Stores past topic relevance scores
        self.max_topic_memory = 5  #

    def load_user_style(self) -> dict:
        """Loads the user style profile from user_style_profile.json."""
        try:
            with open("data/user_style_profile.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def update_threshold(self, last_score: float):
        """
        - If the user is repeatedly off-topic, patience erodes even faster.
        - If the user is consistently on-topic, patience recovers more smoothly.
        """
        momentum_factor = 0.05
        recovery_rate = 0.32
        decay_rate = 0.27
        noise_intensity = 0.03

        # Compute recent topic trend (average of last N scores)
        recent_avg = (
            sum(self.recent_topic_scores) / len(self.recent_topic_scores)
            if self.recent_topic_scores
            else 0.5
        )

        if last_score < self.dynamic_threshold:
            self.off_topic_streak += 1  # Track repeated off-topic messages
        else:
            self.off_topic_streak = max(
                0, self.off_topic_streak - 1
            )  # Reduce streak on recovery

        # If user has been off-topic multiple times, decay patience faster
        adaptive_decay = decay_rate * (1 + 0.2 * self.off_topic_streak)

        # Adjust shift based on recent topic trend
        if last_score > self.dynamic_threshold:
            shift = recovery_rate * (1 - self.dynamic_threshold) * (recent_avg + 0.5)
        else:
            shift = -adaptive_decay * self.dynamic_threshold * (1 - recent_avg)

        noise = random.gauss(0, noise_intensity)

        self.dynamic_threshold += momentum_factor * shift + noise
        self.dynamic_threshold = max(0.05, min(0.95, self.dynamic_threshold))

        self.threshold_history.append(self.dynamic_threshold)
        self.snark_history.append(self.get_snarkiness())

    def get_snarkiness(self) -> float:
        """Returns snark level inversely proportional to patience (exponential scale)."""
        return math.exp(-3 * self.dynamic_threshold)  # More snark as patience drops

    def generate_shutdown_response(self, redirect_topic: str) -> str:
        """
        Uses the LLM to generate a custom shutdown response.
        The irritation level is controlled by the patience threshold.
        """
        snarkiness = self.get_snarkiness()

        shutdown_prompt = (
            f"You are an AI assistant that is getting increasingly irritated by an off-topic conversation. "
            f"Your patience level is {self.dynamic_threshold:.2f} (0 = no patience, 1 = full patience). "
            f"Generate a brief shutdown response reflecting this irritation, and redirect to a more interesting topic: {redirect_topic}. "
            "Your tone should be dismissive and annoyed if patience is low, but polite if patience is high."
        )

        logger.info(
            f"Generating LLM shutdown response (Patience: {self.dynamic_threshold:.2f}, Snark: {snarkiness:.2f})"
        )

        response = self.llm.generate_reply([("system", shutdown_prompt)], "")
        return response.strip()

    def reply(self, user_message: str, strict_enforcement: bool = False) -> str:
        """
        Generates an AI reply.
        If strict_enforcement is True, the AI forcefully redirects or shuts down off-topic convos.
        """
        style_data = self.load_user_style()
        tone = style_data.get("tone", "Neutral")
        style = style_data.get("style", "Straightforward")
        common_phrases = style_data.get("common_phrases", [])
        preferred_topics = style_data.get("preferred_topics", [])

        # Compute topic relevance
        topic_score = self.compute_topic_score(user_message, preferred_topics)
        self.update_threshold(topic_score)
        snarkiness = self.get_snarkiness()
        logger.info(
            f"Topic Score: {topic_score:.2f}, Snarkiness: {snarkiness:.2f}, Threshold: {self.dynamic_threshold:.2f}, strict_enforcement: {strict_enforcement}"
        )
        if strict_enforcement and topic_score < self.dynamic_threshold:
            redirect_topic = (
                random.choice(preferred_topics)
                if preferred_topics
                else "something actually interesting"
            )
            shutdown_response = self.generate_shutdown_response(redirect_topic)
            save_interaction(
                self.user_id, user_message, shutdown_response, tone_detected=None
            )
            return shutdown_response

        # System prompt for AI
        system_prompt = (
            f"You are Grüblergeist, an AI assistant that mimics the user's style and steers "
            f"conversation toward the user's interests. "
            f"Tone: {tone}. Style: {style}. "
            f"Use phrases like: {', '.join(common_phrases)}. "
            f"Snark Level: {snarkiness:.2f}."
        )

        history = [("system", system_prompt)]
        history += get_conversation_history(self.user_id, limit=5)
        assistant_reply = self.llm.generate_reply(history, user_message)

        save_interaction(
            self.user_id, user_message, assistant_reply, tone_detected=None
        )
        return assistant_reply

    def compute_topic_score(self, user_msg: str, preferred_topics: list[str]) -> float:
        """
        Uses GPT-4 to compare user_msg against a list of preferred topics.
        Stores past topic scores to bias future responses.
        """
        if not preferred_topics:
            return 0.5  # Default neutral score

        prompt = (
            f"Score the relevance of the following message to each of the given topics on a scale from 0 to 1, "
            f"where 1 is a perfect match and 0 is completely unrelated.\n\n"
            f"User Message: {user_msg}\n\n"
            f"Topics:\n" + "\n".join([f"- {topic}" for topic in preferred_topics])
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            gpt_response = response.choices[0].message.content
            topic_scores = parse_topic_scores(gpt_response, preferred_topics)

            # ✅ Store latest score, limiting history to 5
            if len(topic_scores) > 0:
                avg_score = sum(topic_scores.values()) / len(topic_scores)
            else:
                avg_score = 0.0
            self.recent_topic_scores.append(avg_score)
            if len(self.recent_topic_scores) > self.max_topic_memory:
                self.recent_topic_scores.pop(0)

            return avg_score

        except Exception as e:
            print(f"Error fetching topic scores: {e}")
            return 0.5  # Default neutral score


def parse_topic_scores(gpt_response: str, topics: list[str]) -> dict:
    """
    Parses the GPT-4 response into a dictionary of {topic: score}.
    Expects the response to contain scores formatted like: 'Topic Name: 0.85'
    """
    scores = {}
    logger.info(f"Parsing topic scores from GPT-4 response:\n{gpt_response}")
    for line in gpt_response.split("\n"):
        logger.info(f"Line: {line}")
        for topic in topics:
            if line.lower().find(topic.lower()) != -1:
                logger.info(f"Matched topic: {topic}")
                try:
                    score = float(line.split(":")[-1].strip())
                    scores[topic] = score
                except ValueError:
                    logger.error(f"Failed to parse score for topic {topic}: {line}")
                    scores[topic] = 0.5  # Default if parsing fails
    return scores


def compute_topic_score_embedding(user_msg: str, preferred_topics: list[str]) -> float:
    """
    Uses OpenAI embeddings to compare topic relevance.
    """
    if not preferred_topics:
        return 0.5  # Default neutral score

    # Get embeddings for the message
    # print(client.embeddings.create(input=user_msg, model="text-embedding-ada-002").data[0].embedding)

    user_embedding = (
        client.embeddings.create(input=user_msg, model="text-embedding-ada-002")
        .data[0]
        .embedding
    )

    # Compute cosine similarity for each preferred topic
    topic_scores = []
    i = 0
    p = preferred_topics
    random.shuffle(p)
    for topic in p:
        print(f"topic: {topic}")
        topic_embedding = (
            client.embeddings.create(input=topic, model="text-embedding-ada-002")
            .data[0]
            .embedding
        )
        score = cosine_similarity(user_embedding, topic_embedding)
        topic_scores.append(score)
        if i > 10:
            break
        i += 1

    s = sum(topic_scores) / len(topic_scores)
    print(len(preferred_topics))
    print(f"return s = {s}")
    return s


def cosine_similarity(vec1, vec2):
    """Computes cosine similarity between two embedding vectors."""
    return sum(a * b for a, b in zip(vec1, vec2)) / (
        math.sqrt(sum(a**2 for a in vec1)) * math.sqrt(sum(b**2 for b in vec2))
    )


# len(preferred_topics) if preferred_topics else 0.5

import re
from typing import Dict, List, Set, Tuple

from models.schemas import MentionedUser, UserInput
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MentionDetector:
    """Detects user mentions in transcript text"""

    def __init__(self, users: List[UserInput]):
        """Initialize with user data"""
        user_dicts = [u.model_dump() for u in users]
        self.user_dictionary = self.build_user_dictionary(user_dicts)
        self.user_lookup = {u.user_id: u for u in users}
        logger.info(f"User dictionary loaded: {len(self.user_dictionary)} entries")

    @staticmethod
    def build_user_dictionary(users: List[Dict]) -> Dict[str, int]:
        """Build normalized user dictionary"""
        if not users:
            return {}

        dictionary = {}

        for user in users:
            user_id = user.get("user_id")
            if not user_id:
                continue

            # First name
            if user.get("first_name"):
                normalized = MentionDetector._normalize(user["first_name"])
                dictionary[normalized] = user_id

            # Last name
            if user.get("last_name"):
                normalized = MentionDetector._normalize(user["last_name"])
                dictionary[normalized] = user_id

            # Full name
            if user.get("first_name") and user.get("last_name"):
                full_name = f"{user['first_name']} {user['last_name']}"
                normalized = MentionDetector._normalize(full_name)
                dictionary[normalized] = user_id

            # Username variants
            if user.get("username"):
                username = user["username"].lstrip("@")

                # "nedu_codes" -> "nedu codes"
                username_spaced = re.sub(r"[_\.]", " ", username)
                dictionary[MentionDetector._normalize(username_spaced)] = user_id

                # "nedu_codes" -> "neducodes"
                username_joined = re.sub(r"[_\.]", "", username)
                dictionary[MentionDetector._normalize(username_joined)] = user_id

                # "millennium.py" -> "millennium"
                if "." in username:
                    base = username.split(".")[0]
                    dictionary[MentionDetector._normalize(base)] = user_id

        return dictionary

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for matching"""
        text = text.lower().strip()
        text = re.sub(r"[_\.@]", " ", text)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return " ".join(text.split())

    def detect_mentions(
        self, transcript: str, video_id: str
    ) -> Tuple[Set[int], List[MentionedUser]]:
        """Detect user mentions in transcript"""
        if not transcript:
            return set(), []

        normalized_text = self._normalize(transcript)
        words = normalized_text.split()
        n = len(words)

        matched_positions = set()
        final_matches = {}

        # Match longest first (trigram -> bigram -> unigram)
        for length in [3, 2, 1]:
            for i in range(n - length + 1):
                if any(pos in matched_positions for pos in range(i, i + length)):
                    continue

                phrase = " ".join(words[i : i + length])

                if phrase in self.user_dictionary:
                    user_id = self.user_dictionary[phrase]

                    if user_id not in final_matches:
                        final_matches[user_id] = (phrase, i)
                        matched_positions.update(range(i, i + length))

        # Build result
        mentioned_users = []
        for user_id, (matched_term, _) in final_matches.items():
            user = self.user_lookup.get(user_id)
            if user:
                mentioned_users.append(
                    MentionedUser(
                        user_id=user.user_id,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        username=user.username,
                        matched_term=matched_term,
                        display_name=f"{user.first_name or ''} {user.last_name or ''}".strip()
                        or f"@{user.username}",
                    )
                )

        logger.info(
            f"Mentions detected: video_id={video_id}, count={len(final_matches)}"
        )

        return set(final_matches.keys()), mentioned_users

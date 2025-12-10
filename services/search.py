from typing import Dict, List

from models.schemas import SearchResultItem, TranscriptItem
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptSearch:
    """Transcript search with fuzzy matching"""

    @staticmethod
    def search_transcripts(
        query: str, transcripts: List[TranscriptItem]
    ) -> List[SearchResultItem]:
        """
        Search through transcripts.

        Args:
            query: Search query
            transcripts: List of transcript items

        Returns:
            List of matching results with snippets
        """
        if not query or not transcripts:
            return []

        query_lower = query.lower().strip()
        results = []

        for item in transcripts:
            transcript = item.transcript
            if not transcript:
                continue

            transcript_lower = transcript.lower()

            # Exact match count
            exact_count = transcript_lower.count(query_lower)

            # Fuzzy matches
            fuzzy_matches = TranscriptSearch._fuzzy_match(query_lower, transcript_lower)

            total_matches = exact_count + len(fuzzy_matches)

            if total_matches > 0:
                snippet = TranscriptSearch._extract_snippet(
                    transcript, query_lower, exact_count > 0
                )
                relevance = TranscriptSearch._calculate_relevance(
                    query_lower, transcript_lower, exact_count, len(fuzzy_matches)
                )

                results.append(
                    SearchResultItem(
                        video_id=item.video_id,
                        snippet=snippet,
                        match_count=total_matches,
                        relevance_score=relevance,
                    )
                )

        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return results

    @staticmethod
    def _fuzzy_match(query: str, transcript: str, threshold: int = 2) -> List[str]:
        """Find fuzzy matches (typo tolerance)"""
        words = transcript.split()
        matches = []

        for word in words:
            clean_word = "".join(c for c in word if c.isalnum())

            if len(clean_word) < 3:
                continue

            distance = TranscriptSearch._levenshtein_distance(query, clean_word)

            if 0 < distance <= threshold and len(query) > 3:
                matches.append(clean_word)

        return matches

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance"""
        if len(s1) < len(s2):
            return TranscriptSearch._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def _extract_snippet(transcript: str, query: str, exact_match: bool) -> str:
        """Extract snippet with context"""
        if exact_match:
            transcript_lower = transcript.lower()
            pos = transcript_lower.find(query)

            if pos != -1:
                start = max(0, pos - 30)
                end = min(len(transcript), pos + len(query) + 30)
                snippet = transcript[start:end]

                if start > 0:
                    snippet = "..." + snippet
                if end < len(transcript):
                    snippet = snippet + "..."

                return snippet

        return transcript[:100] + ("..." if len(transcript) > 100 else "")

    @staticmethod
    def _calculate_relevance(
        query: str, transcript: str, exact_count: int, fuzzy_count: int
    ) -> float:
        """Calculate relevance score (0.0 to 1.0)"""
        weighted_matches = (exact_count * 1.0) + (fuzzy_count * 0.5)
        transcript_words = len(transcript.split())

        if transcript_words == 0:
            return 0.0

        density_score = weighted_matches / max(1, transcript_words / 100)
        return min(1.0, density_score)

"""OpenAI LLM client for generating personalized destination content."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Async OpenAI client for generating personalized travel content.

    Features:
    - Retry logic with exponential backoff
    - Batch generation for multiple destinations
    - Graceful fallback on errors
    """

    BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_MAX_TOKENS = 300
    DEFAULT_TEMPERATURE = 0.7

    def __init__(
        self,
        api_key: str,
        http_client: "httpx.AsyncClient",
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            http_client: Shared httpx async client
            model: Model to use (default: gpt-4o-mini)
            max_tokens: Max tokens for response (default: 300)
        """
        self._api_key = api_key
        self._client = http_client
        self._model = model
        self._max_tokens = max_tokens
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def generate_destination_content(
        self,
        country_name: str,
        user_interests: list[str],
        travel_style: str,
        occasion: Optional[str],
        budget_level: str,
        key_factors: list[str],
        top_activities: list[dict],
        max_retries: int = 3,
    ) -> tuple[str, str]:
        """
        Generate personalized headline and description for a destination.

        Args:
            country_name: Name of the destination country
            user_interests: List of user interests
            travel_style: Travel style (solo, couple, family, etc.)
            occasion: Special occasion if any
            budget_level: Budget tier
            key_factors: Key matching factors for this destination
            top_activities: Top activities in the destination
            max_retries: Number of retry attempts

        Returns:
            Tuple of (headline, description)

        Raises:
            Exception: If all retries fail
        """
        # Build context-aware prompt
        interests_str = (
            ", ".join(user_interests) if user_interests else "decouverte generale"
        )
        activities_str = ", ".join([a.get("name", "") for a in top_activities[:3]])
        factors_str = ", ".join(key_factors) if key_factors else "destination adaptee"

        occasion_context = ""
        if occasion:
            occasion_context = f"- Occasion: {occasion}\n"

        prompt = f"""Tu es un expert en voyage. Genere du contenu pour {country_name} pour un voyageur {travel_style}.

Profil utilisateur:
- Interets: {interests_str}
- Budget: {budget_level}
{occasion_context}- Points forts de ce pays pour lui: {factors_str}
- Activites populaires: {activities_str}

Genere:
1. Un titre accrocheur (max 50 caracteres) qui explique pourquoi CE pays pour CE profil
2. Une description personnalisee (max 150 caracteres) avec des details specifiques

Format strict:
HEADLINE: [titre]
DESCRIPTION: [description]

Sois specifique et evite les phrases generiques comme "Decouvrez" ou "Explorez"."""

        # Retry with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                response = await self._client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers,
                    json={
                        "model": self._model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Tu es un copywriter voyage expert, creatif et precis. Reponds uniquement avec le format demande.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": self._max_tokens,
                        "temperature": self.DEFAULT_TEMPERATURE,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]

                # Parse response
                headline, description = self._parse_response(content)

                if headline and description:
                    return headline, description

                raise ValueError("Failed to parse LLM response")

            except Exception as e:
                last_error = e
                logger.warning(
                    f"OpenAI API attempt {attempt + 1}/{max_retries} failed for {country_name}: {e}"
                )
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    await asyncio.sleep(2**attempt)

        logger.error(f"All OpenAI API attempts failed for {country_name}: {last_error}")
        raise last_error or Exception("Unknown error")

    def _parse_response(self, content: str) -> tuple[str, str]:
        """
        Parse LLM response to extract headline and description.

        Args:
            content: Raw LLM response text

        Returns:
            Tuple of (headline, description)
        """
        headline = ""
        description = ""

        # Try to extract HEADLINE: and DESCRIPTION:
        for line in content.strip().split("\n"):
            line = line.strip()
            if line.upper().startswith("HEADLINE:"):
                headline = line[9:].strip()[:50]  # Max 50 chars
            elif line.upper().startswith("DESCRIPTION:"):
                description = line[12:].strip()[:150]  # Max 150 chars

        # Fallback: try regex patterns
        if not headline:
            match = re.search(r"HEADLINE:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            if match:
                headline = match.group(1).strip()[:50]

        if not description:
            match = re.search(r"DESCRIPTION:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            if match:
                description = match.group(1).strip()[:150]

        return headline, description

    async def generate_batch(
        self,
        destinations: list[dict],
        user_preferences: dict,
        max_concurrent: int = 3,
    ) -> list[tuple[str, str, str]]:
        """
        Generate content for multiple destinations concurrently.

        Args:
            destinations: List of destination dicts with:
                - country_code: ISO 2-letter code
                - country_name: Full country name
                - top_activities: List of top activities
                - key_factors: List of matching factors
            user_preferences: Dict with:
                - interests: List of interests
                - travel_style: Travel style string
                - occasion: Optional occasion
                - budget_level: Budget tier

        Returns:
            List of (country_code, headline, description) tuples
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_one(dest: dict) -> tuple[str, str, str]:
            async with semaphore:
                country_code = dest.get("country_code", "")
                country_name = dest.get("country_name", "Unknown")

                try:
                    headline, description = await self.generate_destination_content(
                        country_name=country_name,
                        user_interests=user_preferences.get("interests", []),
                        travel_style=user_preferences.get("travel_style", "couple"),
                        occasion=user_preferences.get("occasion"),
                        budget_level=user_preferences.get("budget_level", "comfort"),
                        key_factors=dest.get("key_factors", []),
                        top_activities=dest.get("top_activities", []),
                    )
                    return (country_code, headline, description)

                except Exception as e:
                    logger.warning(f"Failed to generate content for {country_code}: {e}")
                    # Fallback content
                    return (
                        country_code,
                        f"{country_name}, le choix ideal",
                        f"Parfait pour votre voyage {user_preferences.get('travel_style', 'couple')}.",
                    )

        results = await asyncio.gather(*[generate_one(d) for d in destinations])
        return list(results)

    @staticmethod
    def get_fallback_content(
        country_name: str, travel_style: str
    ) -> tuple[str, str]:
        """
        Generate fallback content when LLM is unavailable.

        Args:
            country_name: Name of the destination
            travel_style: Travel style

        Returns:
            Tuple of (headline, description)
        """
        return (
            f"{country_name}, le choix ideal",
            f"Destination parfaite pour votre voyage {travel_style}.",
        )

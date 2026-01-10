"""Business logic service for destination suggestions with multi-dimensional scoring."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.models.destination_suggestions import (
    BudgetEstimate,
    BudgetLevel,
    DestinationSuggestion,
    DestinationSuggestionsResponse,
    ProfileCompleteness,
    StyleAxes,
    TopActivity,
    UserPreferencesPayload,
)

if TYPE_CHECKING:
    from app.repositories.country_profiles_repository import CountryProfilesRepository
    from app.services.llm.openai_client import OpenAIClient
    from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class DestinationSuggestionService:
    """
    Service for generating personalized destination suggestions.

    Uses a multi-dimensional scoring algorithm:
    - 25% Style Matching: Distance between user style and country profile
    - 30% Interest Alignment: Match user interests with country affinities
    - 15% Must-Haves: Validation of mandatory requirements
    - 10% Budget Alignment: Cost of living vs budget level
    - 10% Seasonal Relevance: Bonus for visiting in the right season
    - 5% Trending Score: Current popularity
    - 5% Travel Context: Travel style and occasion bonuses
    """

    # Scoring weight distribution (total = 100)
    WEIGHTS = {
        "style": 25,
        "interests": 30,
        "must_haves": 15,
        "budget": 10,
        "seasonal": 10,
        "trending": 5,
        "context": 5,
    }

    # Minimum score threshold for recommendation
    MIN_SCORE_THRESHOLD = 40

    def __init__(
        self,
        profiles_repo: "CountryProfilesRepository",
        llm_client: Optional["OpenAIClient"],
        redis_cache: "RedisCache",
        cache_ttl: int = 3600,
    ):
        """
        Initialize the destination suggestion service.

        Args:
            profiles_repo: Repository for country profiles
            llm_client: OpenAI client for content generation (optional)
            redis_cache: Redis cache for response caching
            cache_ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.profiles = profiles_repo
        self.llm = llm_client
        self.cache = redis_cache
        self.cache_ttl = cache_ttl

    async def get_suggestions(
        self,
        preferences: UserPreferencesPayload,
        limit: int = 3,
        force_refresh: bool = False,
        fast_mode: bool = False,
    ) -> DestinationSuggestionsResponse:
        """
        Generate personalized destination suggestions.

        Flow:
        1. Check Redis cache (unless force_refresh)
        2. Load all country profiles from MongoDB
        3. Score each country against user preferences
        4. Select top N countries above threshold
        5. Generate LLM content for selected countries
        6. Build and cache response

        Args:
            preferences: User preferences payload
            limit: Number of suggestions to return (default: 3)
            force_refresh: Bypass cache if True

        Returns:
            DestinationSuggestionsResponse with scored suggestions
        """
        # Determine current month for seasonal scoring
        current_month = preferences.travelMonth or datetime.now().month

        # Build cache key including month for seasonal relevance
        cache_key = self._build_cache_key(preferences, current_month)

        # Check cache
        if not force_refresh:
            cached = self.cache.get("dest_suggest", {"key": cache_key})
            if cached:
                logger.info("Cache HIT for destination suggestions")
                return DestinationSuggestionsResponse(**cached)

        logger.info(
            f"Generating destination suggestions for {preferences.travelStyle.value} traveler"
        )

        # Load all country profiles
        profiles = await self.profiles.get_all_profiles()
        logger.info(f"Loaded {len(profiles)} country profiles")

        # Score each country
        scored_countries = []
        for profile in profiles:
            score, key_factors = self._calculate_score(profile, preferences, current_month)

            # Skip countries below threshold
            if score < self.MIN_SCORE_THRESHOLD:
                continue

            scored_countries.append(
                {
                    "profile": profile,
                    "score": score,
                    "key_factors": key_factors,
                }
            )

        # Sort by score descending and select top N
        scored_countries.sort(key=lambda x: x["score"], reverse=True)
        top_countries = scored_countries[:limit]

        logger.info(
            f"Top {len(top_countries)} countries: {[c['profile'].get('country_code', '??') for c in top_countries]}"
        )

        # Generate LLM content for top destinations (skip if fast_mode)
        suggestions = []
        llm_map = {}

        if not fast_mode and self.llm and top_countries:
            # Prepare data for batch LLM generation
            llm_input = [
                {
                    "country_code": c["profile"].get("country_code", ""),
                    "country_name": c["profile"].get("country_name", "Unknown"),
                    "top_activities": c["profile"].get("top_activities", []),
                    "key_factors": c["key_factors"],
                }
                for c in top_countries
            ]

            user_prefs_dict = {
                "interests": preferences.interests,
                "travel_style": preferences.travelStyle.value,
                "occasion": preferences.occasion.value if preferences.occasion else None,
                "budget_level": preferences.budgetLevel.value,
            }

            try:
                llm_results = await self.llm.generate_batch(llm_input, user_prefs_dict)
                llm_map = {r[0]: (r[1], r[2]) for r in llm_results}
            except Exception as e:
                logger.error(f"LLM batch generation failed: {e}")
                llm_map = {}
        elif fast_mode:
            logger.debug("Fast mode enabled - using pre-computed headlines")

        # Build suggestion objects
        for country_data in top_countries:
            profile = country_data["profile"]
            country_code = profile.get("country_code", "")

            # Get LLM content or use fallback (pre-computed headlines if available)
            if country_code in llm_map:
                headline, description = llm_map[country_code]
            else:
                # Try to use pre-computed fallback headlines from profile
                fallback_headlines = profile.get("fallback_headlines", {})
                travel_style = preferences.travelStyle.value

                if travel_style in fallback_headlines:
                    headline = fallback_headlines[travel_style]
                else:
                    headline = f"{profile.get('country_name', 'Unknown')}, le choix ideal"

                description = profile.get(
                    "fallback_description",
                    f"Parfait pour votre voyage {travel_style}."
                )

            # Get budget for user's level (converted to per-day)
            budget_data = profile.get("budget", {})
            budget_level = preferences.budgetLevel.value
            
            # Convert 7-day budget to daily budget
            min_7d = budget_data.get(f"{budget_level}_min_7d", 500)
            max_7d = budget_data.get(f"{budget_level}_max_7d", 1500)

            budget_estimate = BudgetEstimate(
                min=round(min_7d / 7),
                max=round(max_7d / 7),
                duration="per_day",
            )

            # Map top activities
            top_activities = [
                TopActivity(
                    name=a.get("name", "Activity"),
                    emoji=a.get("emoji", "star"),
                    category=a.get("category", "activity"),
                )
                for a in profile.get("top_activities", [])[:5]
            ]

            suggestion = DestinationSuggestion(
                countryCode=country_code,
                countryName=profile.get("country_name", "Unknown"),
                flagEmoji=profile.get("flag_emoji", ""),
                headline=headline,
                description=description,
                matchScore=country_data["score"],
                keyFactors=country_data["key_factors"],
                estimatedBudgetPerPerson=budget_estimate,
                topActivities=top_activities,
                bestSeasons=profile.get("best_seasons", []),
                flightDurationFromOrigin=None,
                flightPriceEstimate=None,
            )

            suggestions.append(suggestion)

        # Build profile completeness
        profile_completeness = self._calculate_profile_completeness(preferences)

        # Build response
        response = DestinationSuggestionsResponse(
            success=True,
            suggestions=suggestions,
            generatedAt=datetime.utcnow().isoformat() + "Z",
            basedOnProfile=profile_completeness,
        )

        # Cache response
        try:
            self.cache.set(
                "dest_suggest",
                {"key": cache_key},
                response.model_dump(),
                ttl_seconds=self.cache_ttl,
            )
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")

        return response

    def _calculate_score(
        self,
        profile: dict,
        prefs: UserPreferencesPayload,
        current_month: int,
    ) -> tuple[int, list[str]]:
        """
        Calculate match score using multi-dimensional algorithm.

        Args:
            profile: Country profile document
            prefs: User preferences
            current_month: Current/target travel month (1-12)

        Returns:
            Tuple of (score 0-100, list of key factors)
        """
        scores: dict[str, float] = {}
        factors: list[str] = []

        # === 1. STYLE MATCHING (25%) ===
        style = profile.get("style_scores", {})
        axes = prefs.styleAxes

        distances = [
            abs(style.get("chill_vs_intense", 50) - axes.chillVsIntense),
            abs(style.get("city_vs_nature", 50) - axes.cityVsNature),
            abs(style.get("eco_vs_luxury", 50) - axes.ecoVsLuxury),
            abs(style.get("tourist_vs_local", 50) - axes.touristVsLocal),
        ]
        avg_dist = sum(distances) / len(distances)
        scores["style"] = max(0, 100 - avg_dist)

        if avg_dist < 15:
            factors.append("Style de voyage parfaitement adapte")
        elif avg_dist < 25:
            factors.append("Ambiance correspondant a vos attentes")

        # === 2. INTEREST ALIGNMENT (30%) ===
        interest_scores = profile.get("interest_scores", {})
        user_interests = [i.lower() for i in prefs.interests]

        if user_interests:
            matched_scores = []
            for interest in user_interests:
                score = interest_scores.get(interest, 50)
                matched_scores.append(score)
                if score >= 85:
                    factors.append(f"Excellent pour {interest}")
                elif score >= 75:
                    factors.append(f"Tres bon pour {interest}")

            scores["interests"] = sum(matched_scores) / len(matched_scores)
        else:
            scores["interests"] = 70  # Neutral score if no interests specified

        # === 3. MUST-HAVES VALIDATION (15%) ===
        must_haves = profile.get("must_haves", {})
        mh = prefs.mustHaves
        penalty = 0

        if mh.accessibilityRequired:
            acc = must_haves.get("accessibility_score", 50)
            if acc < 60:
                penalty += 40
            elif acc >= 80:
                factors.append("Bonne accessibilite PMR")

        if mh.petFriendly:
            pet = must_haves.get("pet_friendly_score", 50)
            if pet < 50:
                penalty += 35
            elif pet >= 70:
                factors.append("Pet-friendly")

        if mh.familyFriendly:
            fam = must_haves.get("family_friendly_score", 50)
            if fam < 60:
                penalty += 30
            elif fam >= 80:
                factors.append("Ideal pour les familles")

        if mh.highSpeedWifi:
            wifi = must_haves.get("wifi_quality_score", 50)
            if wifi < 70:
                penalty += 25
            elif wifi >= 85:
                factors.append("Excellente connectivite")

        scores["must_haves"] = max(0, 100 - penalty)

        # === 4. BUDGET ALIGNMENT (10%) ===
        budget_data = profile.get("budget", {})
        col = budget_data.get("cost_of_living_index", 100)

        if prefs.budgetLevel in [BudgetLevel.BUDGET, BudgetLevel.COMFORT]:
            scores["budget"] = max(0, min(100, 150 - col))
            if col < 50:
                factors.append("Excellent rapport qualite-prix")
            elif col < 70:
                factors.append("Destination abordable")
        else:
            scores["budget"] = min(100, 30 + (col * 0.7))
            if col > 100:
                factors.append("Options luxe disponibles")

        # === 5. SEASONAL RELEVANCE (10%) ===
        best_months = profile.get("best_months", [])
        avoid_months = profile.get("avoid_months", [])

        if current_month in best_months:
            scores["seasonal"] = 100
            factors.append("Saison ideale pour visiter")
        elif current_month in avoid_months:
            scores["seasonal"] = 30
        else:
            scores["seasonal"] = 70

        # === 6. TRENDING SCORE (5%) ===
        trending = profile.get("trending_score", 50)
        scores["trending"] = trending
        if trending >= 80:
            factors.append("Destination tendance")

        # === 7. TRAVEL CONTEXT (5%) ===
        travel_bonuses = profile.get("travel_style_bonuses", {})
        style_bonus = travel_bonuses.get(prefs.travelStyle.value, 0)

        occasion_bonus = 0
        if prefs.occasion:
            occasion_bonuses = profile.get("occasion_bonuses", {})
            occasion_bonus = occasion_bonuses.get(prefs.occasion.value, 0)
            if occasion_bonus >= 15:
                factors.append(f"Parfait pour {prefs.occasion.value}")

        scores["context"] = min(100, max(0, 50 + style_bonus + occasion_bonus))

        # === CALCULATE FINAL WEIGHTED SCORE ===
        final = sum(scores[k] * (self.WEIGHTS[k] / 100) for k in self.WEIGHTS)

        # Limit to 5 key factors, prioritizing most specific
        factors = factors[:5]

        return int(round(final)), factors

    def _calculate_profile_completeness(
        self, preferences: UserPreferencesPayload
    ) -> ProfileCompleteness:
        """
        Calculate how complete the user's profile is.

        Args:
            preferences: User preferences payload

        Returns:
            ProfileCompleteness with score and key factors
        """
        score = 20  # Base score for providing any data
        factors: list[str] = []

        if preferences.userLocation.city or preferences.userLocation.country:
            score += 15
            factors.append("Localisation fournie")

        if preferences.interests:
            score += 20
            factors.append(f"{len(preferences.interests)} centres d'interet")

        # Check if style axes differ from defaults
        default_axes = StyleAxes()
        if preferences.styleAxes != default_axes:
            score += 20
            factors.append("Preferences de style definies")

        if preferences.occasion:
            score += 10
            factors.append(f"Occasion: {preferences.occasion.value}")

        if any(
            [
                preferences.mustHaves.accessibilityRequired,
                preferences.mustHaves.petFriendly,
                preferences.mustHaves.familyFriendly,
                preferences.mustHaves.highSpeedWifi,
            ]
        ):
            score += 10
            factors.append("Exigences specifiees")

        if preferences.dietaryRestrictions:
            score += 5
            factors.append("Restrictions alimentaires")

        return ProfileCompleteness(
            completionScore=min(100, score),
            keyFactors=factors[:4],
        )

    def _build_cache_key(
        self, preferences: UserPreferencesPayload, current_month: int
    ) -> str:
        """
        Build unique cache key from preferences.

        Args:
            preferences: User preferences
            current_month: Current/target travel month

        Returns:
            MD5 hash of normalized preferences
        """
        key_data = {
            "style": preferences.styleAxes.model_dump(),
            "interests": sorted(preferences.interests),
            "must_haves": preferences.mustHaves.model_dump(),
            "travel_style": preferences.travelStyle.value,
            "occasion": preferences.occasion.value if preferences.occasion else None,
            "budget": preferences.budgetLevel.value,
            "month": current_month,
        }

        serialized = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

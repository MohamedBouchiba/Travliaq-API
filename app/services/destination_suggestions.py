"""Business logic service for destination suggestions with multi-dimensional scoring."""

from __future__ import annotations

import hashlib
import json
import logging
import random
from collections import defaultdict
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
from app.services.flight_price_cache import (
    COUNTRY_MAIN_AIRPORTS,
    AIRPORT_COORDINATES,
)

import math
import re

if TYPE_CHECKING:
    from app.repositories.country_profiles_repository import CountryProfilesRepository
    from app.services.flight_price_cache import FlightPriceCacheService
    from app.services.llm.openai_client import OpenAIClient
    from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class DestinationSuggestionService:
    """
    Service for generating personalized destination suggestions.

    Uses an 11-dimensional scoring algorithm with two-phase pricing:
    - 17% Style Matching: Position-weighted distance between user style and country profile
    - 17% Interest Alignment: Match user interests with country affinities
    - 10% Must-Haves: Validation of mandatory requirements
    - 8% Budget Alignment: Cost of living vs budget level
    - 12% Climate: Temperature + sunshine matched to user interests and travel month
    - 10% Distance: Haversine proximity from departure (budget-sensitive)
    - 3% Trending Score: Current popularity
    - 5% Travel Context: Travel style and occasion bonuses
    - 10% Trip Feasibility: Flight duration vs trip duration ratio
    - 8% Flight Price: Real flight price scoring (Phase 2, via get_map_prices)
    """

    # Scoring weight distribution (total = 100)
    WEIGHTS = {
        "style": 17,
        "interests": 17,
        "must_haves": 10,
        "budget": 8,
        "climate": 12,
        "distance": 10,
        "trending": 3,
        "context": 5,
        "trip_feasibility": 10,
        "flight_price": 8,
    }

    # Position weights for style axes when user has defined an order
    POSITION_WEIGHTS = [0.40, 0.30, 0.20, 0.10]

    # Default axes order (equal weighting) when no order is provided
    DEFAULT_AXES_ORDER = ["chillVsIntense", "cityVsNature", "ecoVsLuxury", "touristVsLocal"]

    # Mapping: camelCase axis name → (snake_case profile key, camelCase pref key)
    AXIS_KEY_MAP = {
        "chillVsIntense": ("chill_vs_intense", "chillVsIntense"),
        "cityVsNature": ("city_vs_nature", "cityVsNature"),
        "ecoVsLuxury": ("eco_vs_luxury", "ecoVsLuxury"),
        "touristVsLocal": ("tourist_vs_local", "touristVsLocal"),
    }

    # Minimum score threshold for recommendation
    MIN_SCORE_THRESHOLD = 40

    # Diversity settings
    EXTRA_POOL_SIZE = 5  # Take N + 5 candidates for random selection
    MAX_PER_REGION = 2  # Max countries from same region in pool
    VARIATION_INTERVAL_HOURS = 1  # Change recommendations every hour

    def __init__(
        self,
        profiles_repo: "CountryProfilesRepository",
        llm_client: Optional["OpenAIClient"],
        redis_cache: "RedisCache",
        cache_ttl: int = 3600,
        flight_price_cache: Optional["FlightPriceCacheService"] = None,
    ):
        """
        Initialize the destination suggestion service.

        Args:
            profiles_repo: Repository for country profiles
            llm_client: OpenAI client for content generation (optional)
            redis_cache: Redis cache for response caching
            cache_ttl: Cache TTL in seconds (default: 1 hour)
            flight_price_cache: Service for flight price lookups (optional)
        """
        self.profiles = profiles_repo
        self.llm = llm_client
        self.cache = redis_cache
        self.cache_ttl = cache_ttl
        self.flight_price_cache = flight_price_cache

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

        # Phase 1: Score all countries (flight_price = neutral 70)
        scored_countries = []
        for profile in profiles:
            score, key_factors, distance_km = self._calculate_score(
                profile, preferences, current_month
            )
            if score < self.MIN_SCORE_THRESHOLD:
                continue
            scored_countries.append({
                "profile": profile,
                "score": score,
                "key_factors": key_factors,
                "distance_km": distance_km,
            })

        scored_countries.sort(key=lambda x: x["score"], reverse=True)

        # Phase 2: Re-score top candidates with real flight prices
        source_airport_iata: Optional[str] = None
        TOP_CANDIDATES = 20
        top_candidates = scored_countries[:TOP_CANDIDATES]

        if self.flight_price_cache and preferences.userLocation.city and top_candidates:
            country_codes = [c["profile"].get("country_code", "") for c in top_candidates]
            profiles_dict = {
                c["profile"].get("country_code", ""): c["profile"]
                for c in top_candidates
            }
            try:
                phase2_prices, source_airport_iata = (
                    await self.flight_price_cache.get_flight_prices_batch_with_fallbacks(
                        origin_city=preferences.userLocation.city,
                        destination_country_codes=country_codes,
                        destination_profiles=profiles_dict,
                        currency="EUR",
                    )
                )
                if phase2_prices:
                    all_prices = [p[0] for p in phase2_prices.values()]
                    dynamic_weights = self._get_dynamic_weights(preferences)
                    fp_weight = dynamic_weights.get("flight_price", 8)

                    for country in top_candidates:
                        cc = country["profile"].get("country_code", "")
                        price_data = phase2_prices.get(cc)
                        if price_data:
                            real_fp_score = self._calculate_flight_price_score(
                                price_data[0], preferences.budgetLevel, all_prices
                            )
                            country["score"] += int(round((real_fp_score - 70) * fp_weight / 100))
                            country["score"] = max(0, min(100, country["score"]))
                            country["flight_price"] = price_data[0]
                            country["flight_price_source"] = price_data[1]

                    top_candidates.sort(key=lambda x: x["score"], reverse=True)
                    scored_countries = top_candidates + scored_countries[TOP_CANDIDATES:]
                    logger.info(
                        f"Phase 2: Re-scored {len(top_candidates)} candidates "
                        f"with real flight prices from {source_airport_iata}"
                    )
            except Exception as e:
                logger.warning(f"Phase 2 flight price scoring failed: {e}")

        # Apply diversity selection
        pool_size = limit + self.EXTRA_POOL_SIZE
        top_countries = self._select_diverse_random(
            scored_countries, preferences, limit, pool_size
        )

        logger.info(
            f"Top {len(top_countries)} countries (diverse selection): "
            f"{[c['profile'].get('country_code', '??') for c in top_countries]}"
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

            # Get budget for user's level (converted to per-day with 40% reduction)
            budget_data = profile.get("budget", {})
            budget_level = preferences.budgetLevel.value
            
            # Convert 7-day budget to daily budget with realistic adjustment
            min_7d = budget_data.get(f"{budget_level}_min_7d", 500)
            max_7d = budget_data.get(f"{budget_level}_max_7d", 1500)
            BUDGET_ADJUSTMENT = 0.6  # 40% reduction for realistic estimates

            budget_estimate = BudgetEstimate(
                min=round((min_7d / 7) * BUDGET_ADJUSTMENT),
                max=round((max_7d / 7) * BUDGET_ADJUSTMENT),
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

            # Flight price from Phase 2 scoring
            flight_price = country_data.get("flight_price")
            flight_price_source = country_data.get("flight_price_source")

            # Flight duration from distance
            dist_km = country_data.get("distance_km")
            flight_duration_str = None
            flight_duration_min = None
            if dist_km:
                flight_duration_min = self._estimate_flight_minutes(dist_km)
                hours, mins = divmod(flight_duration_min, 60)
                flight_duration_str = f"{hours}h{mins:02d}" if mins else f"{hours}h"

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
                flightDurationFromOrigin=flight_duration_str,
                flightDurationMinutes=flight_duration_min,
                flightPriceEstimate=flight_price,
                flightPriceSource=flight_price_source,
                imageUrl=profile.get("photo_url"),
                imageCredit=profile.get("photo_credit"),
            )

            suggestions.append(suggestion)

        # Build profile completeness
        profile_completeness = self._calculate_profile_completeness(preferences)

        # Build response
        # Note: source_airport_iata is set earlier from flight_price_cache.get_flight_prices_batch_with_fallbacks()
        response = DestinationSuggestionsResponse(
            success=True,
            suggestions=suggestions,
            generatedAt=datetime.utcnow().isoformat() + "Z",
            basedOnProfile=profile_completeness,
            sourceAirportIata=source_airport_iata,
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
        flight_price_score: Optional[float] = None,
    ) -> tuple[int, list[str], Optional[float]]:
        """
        Calculate match score using 11-dimensional algorithm.

        Args:
            profile: Country profile document
            prefs: User preferences
            current_month: Current/target travel month (1-12)
            flight_price_score: Real flight price score (Phase 2). None = 70 neutral.

        Returns:
            Tuple of (score 0-100, list of key factors, distance_km or None)
        """
        scores: dict[str, float] = {}
        factors: list[str] = []

        # === 1. STYLE MATCHING (20%) — weighted by position ===
        style = profile.get("style_scores", {})
        axes = prefs.styleAxes

        axes_order = (
            [a.value for a in prefs.styleAxesOrder]
            if prefs.styleAxesOrder
            else None
        )
        if axes_order:
            pos_weights = self.POSITION_WEIGHTS  # [0.40, 0.30, 0.20, 0.10]
        else:
            axes_order = self.DEFAULT_AXES_ORDER
            pos_weights = [0.25, 0.25, 0.25, 0.25]

        weighted_distance = 0.0
        for i, axis_key in enumerate(axes_order):
            snake_key, camel_key = self.AXIS_KEY_MAP[axis_key]
            distance = abs(style.get(snake_key, 50) - getattr(axes, camel_key))
            weighted_distance += distance * pos_weights[i]

        scores["style"] = max(0.0, 100.0 - weighted_distance)

        if weighted_distance < 15:
            factors.append("Style de voyage parfaitement adapte")
        elif weighted_distance < 25:
            factors.append("Ambiance correspondant a vos attentes")

        # === 2. INTEREST ALIGNMENT (20%) ===
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

        # === 3. MUST-HAVES VALIDATION (12%) ===
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

        # === 5. CLIMATE (15%) — temperature + sunshine vs user preferences ===
        monthly_climate = profile.get("monthly_climate", [])
        best_months = profile.get("best_months", [])
        avoid_months = profile.get("avoid_months", [])

        month_data = next(
            (m for m in monthly_climate if m["month"] == current_month), None
        )

        if month_data:
            avg_temp = month_data["avg_temp_c"]
            sunshine = month_data["sunshine_hours"]

            # Determine ideal temp range based on user interests
            user_interest_set = set(i.lower() for i in prefs.interests)
            if user_interest_set & {"beach", "wellness"}:
                ideal_min, ideal_max = 24, 35  # wants warm
            elif user_interest_set & {"adventure", "sports"}:
                ideal_min, ideal_max = 12, 28  # tolerates wide range
            elif user_interest_set & {"culture", "history", "art", "food", "shopping"}:
                ideal_min, ideal_max = 15, 30  # comfortable
            else:
                ideal_min, ideal_max = 18, 28  # pleasant default

            # Temperature score: 100 if in ideal range, decreasing outside
            if ideal_min <= avg_temp <= ideal_max:
                temp_score = 100.0
            else:
                deviation = min(abs(avg_temp - ideal_min), abs(avg_temp - ideal_max))
                temp_score = max(0.0, 100.0 - deviation * 5)  # -5 pts per °C

            # Sunshine bonus: 0-8h mapped to 0-100
            sunshine_score = min(100.0, sunshine * 12.5)  # 8h+ = 100

            # Combine: 60% temp, 40% sunshine
            climate_score = temp_score * 0.6 + sunshine_score * 0.4

            # Seasonal overlay: bonus/malus from best/avoid months
            if current_month in best_months:
                climate_score = min(100.0, climate_score + 10)
            elif current_month in avoid_months:
                climate_score = max(0.0, climate_score - 25)

            scores["climate"] = climate_score

            if climate_score >= 85:
                factors.append("Climat ideal pour cette periode")
            elif climate_score >= 70:
                factors.append("Bon climat a cette saison")
        else:
            # Fallback: use existing seasonal data
            if current_month in best_months:
                scores["climate"] = 85
                factors.append("Saison ideale pour visiter")
            elif current_month in avoid_months:
                scores["climate"] = 30
            else:
                scores["climate"] = 65

        # === 6. DISTANCE (10%) — proximity from departure ===
        country_code = profile.get("country_code", "")
        dest_iata = COUNTRY_MAIN_AIRPORTS.get(country_code)
        dep_coords = self._get_departure_coords(prefs)
        dest_coords = AIRPORT_COORDINATES.get(dest_iata) if dest_iata else None
        distance_km: Optional[float] = None

        if dep_coords and dest_coords:
            distance_km = self._haversine(dep_coords, dest_coords)

            if prefs.budgetLevel in [BudgetLevel.BUDGET, BudgetLevel.COMFORT]:
                # Budget: proximity matters a lot
                if distance_km < 2000:
                    scores["distance"] = 100
                    factors.append("Destination proche et economique")
                elif distance_km < 4000:
                    scores["distance"] = 70
                elif distance_km < 7000:
                    scores["distance"] = 45
                else:
                    scores["distance"] = 25
            else:
                # Premium/Luxury: distance matters less
                if distance_km < 3000:
                    scores["distance"] = 100
                elif distance_km < 6000:
                    scores["distance"] = 80
                elif distance_km < 10000:
                    scores["distance"] = 60
                else:
                    scores["distance"] = 45
        else:
            scores["distance"] = 60  # Neutral when no coordinates available

        # === 7. TRENDING SCORE (3%) ===
        trending = profile.get("trending_score", 50)
        scores["trending"] = trending
        if trending >= 80:
            factors.append("Destination tendance")

        # === 8. TRAVEL CONTEXT (5%) ===
        travel_bonuses = profile.get("travel_style_bonuses", {})
        style_bonus = travel_bonuses.get(prefs.travelStyle.value, 0)

        occasion_bonus = 0
        if prefs.occasion:
            occasion_bonuses = profile.get("occasion_bonuses", {})
            occasion_bonus = occasion_bonuses.get(prefs.occasion.value, 0)
            if occasion_bonus >= 15:
                factors.append(f"Parfait pour {prefs.occasion.value}")

        scores["context"] = min(100, max(0, 50 + style_bonus + occasion_bonus))

        # === 9. TRIP FEASIBILITY (10%) — flight duration vs trip duration ===
        trip_days = self._parse_trip_days(prefs.tripDuration)
        if trip_days and distance_km:
            flight_hours = self._estimate_flight_minutes(distance_km) / 60
            max_hours = self._max_flight_hours(trip_days)
            ratio = flight_hours / max_hours

            if ratio <= 0.5:
                scores["trip_feasibility"] = 100
            elif ratio <= 0.75:
                scores["trip_feasibility"] = 85
            elif ratio <= 1.0:
                scores["trip_feasibility"] = 60
            elif ratio <= 1.3:
                scores["trip_feasibility"] = 30
            else:
                scores["trip_feasibility"] = max(0, 15 - (ratio - 1.3) * 20)

            if scores["trip_feasibility"] >= 85:
                factors.append("Vol court, ideal pour la duree du sejour")
            elif scores["trip_feasibility"] <= 30:
                factors.append("Vol trop long pour un court sejour")
        else:
            scores["trip_feasibility"] = 70  # Neutral when no trip duration

        # === 10. FLIGHT PRICE (8%) — real price injected in Phase 2 ===
        scores["flight_price"] = flight_price_score if flight_price_score is not None else 70

        # === CALCULATE FINAL WEIGHTED SCORE ===
        dynamic_weights = self._get_dynamic_weights(prefs)
        final = sum(scores[k] * (dynamic_weights[k] / 100) for k in dynamic_weights)

        # Limit to 5 key factors, prioritizing most specific
        factors = factors[:5]

        return int(round(final)), factors, distance_km

    @staticmethod
    def _haversine(c1: tuple[float, float], c2: tuple[float, float]) -> float:
        """Great-circle distance in km between two (lat, lon) points."""
        lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
        lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _get_departure_coords(
        prefs: UserPreferencesPayload,
    ) -> tuple[float, float] | None:
        """Get departure coordinates from user location or nearest airport."""
        loc = prefs.userLocation
        if loc.lat is not None and loc.lng is not None:
            return (loc.lat, loc.lng)
        # Fallback: resolve city/country to a known airport
        if loc.city:
            city_lower = loc.city.lower()
            # Common city → airport mapping for quick resolution
            city_airport_map = {
                "paris": "CDG", "london": "LHR", "londres": "LHR",
                "new york": "JFK", "tokyo": "NRT", "dubai": "DXB",
                "madrid": "MAD", "rome": "FCO", "roma": "FCO",
                "berlin": "FRA", "amsterdam": "AMS", "lisbon": "LIS",
                "lisbonne": "LIS", "bangkok": "BKK", "istanbul": "IST",
                "barcelone": "MAD", "barcelona": "MAD", "marseille": "CDG",
                "lyon": "CDG", "montreal": "YYZ", "montréal": "YYZ",
                "casablanca": "CMN", "marrakech": "CMN", "tunis": "TUN",
                "le caire": "CAI", "cairo": "CAI", "athènes": "ATH",
                "athens": "ATH", "bruxelles": "BRU", "brussels": "BRU",
            }
            iata = city_airport_map.get(city_lower)
            if iata and iata in AIRPORT_COORDINATES:
                return AIRPORT_COORDINATES[iata]
        return None

    @staticmethod
    def _parse_trip_days(trip_duration: Optional[str]) -> Optional[int]:
        """Parse freeform FR/EN trip duration string into number of days."""
        if not trip_duration:
            return None
        text = trip_duration.lower().strip()

        # Direct keywords
        if text in ("weekend", "un weekend", "we"):
            return 2
        if text in ("long weekend", "un long weekend"):
            return 3

        # Pattern: number + unit (jour/semaine/mois / day/week/month)
        m = re.match(r"(\d+)\s*(jour|jours|day|days|j)\b", text)
        if m:
            return int(m.group(1))

        m = re.match(r"(\d+)\s*(semaine|semaines|week|weeks)\b", text)
        if m:
            return int(m.group(1)) * 7

        m = re.match(r"(\d+)\s*(mois|month|months)\b", text)
        if m:
            return int(m.group(1)) * 30

        # "une semaine", "un mois"
        if re.match(r"(une?\s+)?(semaine|week)\b", text):
            return 7
        if re.match(r"(une?\s+)?(mois|month)\b", text):
            return 30

        return None

    @staticmethod
    def _estimate_flight_minutes(distance_km: float) -> int:
        """Estimate one-way flight duration in minutes from distance.

        Uses 800 km/h cruise speed + 45 min overhead (takeoff/landing).
        """
        return max(60, int(distance_km / 800 * 60 + 45))

    @staticmethod
    def _max_flight_hours(trip_days: int) -> float:
        """Maximum acceptable one-way flight hours for a given trip duration.

        Rule: don't spend more than ~25% of the trip in total transit.
        """
        if trip_days <= 2:
            return 2.5
        if trip_days <= 3:
            return 3.5
        if trip_days <= 5:
            return 5.0
        if trip_days <= 7:
            return 7.0
        if trip_days <= 10:
            return 10.0
        if trip_days <= 14:
            return 12.0
        return 999  # No limit for 30+ day trips

    @staticmethod
    def _calculate_flight_price_score(
        price: int,
        budget_level: BudgetLevel,
        all_prices: list[int],
    ) -> float:
        """Score a flight price relative to other candidates (percentile).

        Budget/Comfort: aggressive curve penalizing expensive flights.
        Premium/Luxury: gentle curve, price matters less.
        """
        if not all_prices or len(all_prices) < 2:
            return 70.0

        min_p = min(all_prices)
        max_p = max(all_prices)
        if max_p == min_p:
            return 80.0

        normalized = (price - min_p) / (max_p - min_p)

        if budget_level in (BudgetLevel.BUDGET, BudgetLevel.COMFORT):
            return max(0, 100 - normalized ** 0.7 * 100)
        else:
            return max(0, 100 - normalized ** 1.3 * 60)

    def _get_dynamic_weights(self, prefs: UserPreferencesPayload) -> dict[str, int]:
        """Adjust dimension weights based on user's top priority axis."""
        weights = dict(self.WEIGHTS)

        if not prefs.styleAxesOrder:
            return weights

        top_axis = prefs.styleAxesOrder[0].value
        eco = prefs.styleAxes.ecoVsLuxury
        nature = prefs.styleAxes.cityVsNature

        # ecoVsLuxury #1 + extreme value → boost price-related dimensions
        if top_axis == "ecoVsLuxury" and (eco < 30 or eco > 70):
            weights["flight_price"] += 3  # 8 → 11
            weights["budget"] += 4        # 8 → 12
            weights["distance"] += 2      # 10 → 12
            weights["trending"] -= 3      # 3 → 0
            weights["context"] -= 3       # 5 → 2
            weights["style"] -= 3         # 17 → 14

        # cityVsNature #1 + extreme value → boost climate
        elif top_axis == "cityVsNature" and (nature < 30 or nature > 70):
            weights["climate"] += 5     # 12 → 17
            weights["trending"] -= 3    # 3 → 0
            weights["context"] -= 2     # 5 → 3

        return weights

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

        if preferences.styleAxesOrder:
            score += 10
            factors.append("Priorites de style definies")

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

        Includes time bucket to allow cache to expire and vary recommendations
        over time while still being efficient within the same hour.

        Args:
            preferences: User preferences
            current_month: Current/target travel month

        Returns:
            MD5 hash of normalized preferences
        """
        # Time bucket ensures cache expires hourly for varied recommendations
        time_bucket = datetime.now().hour // self.VARIATION_INTERVAL_HOURS

        key_data = {
            "style": preferences.styleAxes.model_dump(),
            "axes_order": (
                [a.value for a in preferences.styleAxesOrder]
                if preferences.styleAxesOrder
                else None
            ),
            "interests": sorted(preferences.interests),
            "must_haves": preferences.mustHaves.model_dump(),
            "travel_style": preferences.travelStyle.value,
            "occasion": preferences.occasion.value if preferences.occasion else None,
            "budget": preferences.budgetLevel.value,
            "month": current_month,
            "time_bucket": time_bucket,
            "city": preferences.userLocation.city,  # Include city for airport-specific results
            "trip_duration": preferences.tripDuration,
        }

        serialized = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

    def _select_diverse_random(
        self,
        scored_countries: list[dict],
        preferences: UserPreferencesPayload,
        limit: int = 3,
        pool_size: int = 6,
    ) -> list[dict]:
        """
        Select destinations with diversity and deterministic randomization.

        Takes the top-scoring countries, ensures regional diversity,
        then selects a random subset using a deterministic seed based
        on user preferences (same preferences = same results for caching).

        Args:
            scored_countries: Countries sorted by score (descending)
            preferences: User preferences (used for deterministic seed)
            limit: Number of destinations to return
            pool_size: Size of diverse pool to select from

        Returns:
            List of selected country data dicts
        """
        if len(scored_countries) <= limit:
            return scored_countries

        # Build diverse pool with regional balance
        # Take more candidates to ensure we have enough after region filtering
        diverse_pool = self._ensure_region_diversity(
            scored_countries[: pool_size * 3], pool_size
        )

        if len(diverse_pool) <= limit:
            return diverse_pool

        # Generate deterministic seed from preferences + time bucket
        # This allows cache to work within the hour but vary recommendations over time
        time_bucket = datetime.now().hour // self.VARIATION_INTERVAL_HOURS
        seed_data = (
            f"{preferences.travelStyle.value}_"
            f"{sorted(preferences.interests)}_"
            f"{preferences.budgetLevel.value}_"
            f"{time_bucket}"
        )
        seed = int(hashlib.md5(seed_data.encode()).hexdigest()[:8], 16)

        # Use seeded random for reproducible selection within time bucket
        rng = random.Random(seed)
        selected = rng.sample(diverse_pool, min(limit, len(diverse_pool)))

        # Sort selected by score for consistent display order
        selected.sort(key=lambda x: x["score"], reverse=True)

        logger.debug(
            f"Diverse selection: pool={len(diverse_pool)}, "
            f"selected={[c['profile'].get('country_code') for c in selected]}, "
            f"time_bucket={time_bucket}"
        )

        return selected

    def _ensure_region_diversity(
        self, candidates: list[dict], target_count: int
    ) -> list[dict]:
        """
        Ensure regional diversity in the candidate pool.

        Limits the number of countries from each region to avoid
        recommendations like "Thailand, Vietnam, Indonesia" all from
        Southeast Asia.

        Args:
            candidates: Sorted list of country candidates
            target_count: Target size of diverse pool

        Returns:
            List of countries with regional diversity
        """
        region_counts: dict[str, int] = defaultdict(int)
        diverse_pool: list[dict] = []

        for candidate in candidates:
            region = candidate["profile"].get("region", "Unknown")

            # Allow max N countries per region
            if region_counts[region] < self.MAX_PER_REGION:
                diverse_pool.append(candidate)
                region_counts[region] += 1

            if len(diverse_pool) >= target_count:
                break

        return diverse_pool

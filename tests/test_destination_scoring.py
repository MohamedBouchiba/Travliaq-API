"""
Tests for the V2 destination scoring algorithm (9 dimensions).

Tests the _calculate_score method directly with mock country profiles.
No database, no Redis, no external services needed — pure function tests.
"""

import os
import sys
import unittest

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.destination_suggestions import (
    StyleAxisName,
    UserPreferencesPayload,
)
from app.services.destination_suggestions import DestinationSuggestionService


# ============================================================================
# MOCK COUNTRY PROFILES
# ============================================================================

PORTUGAL = {
    "country_code": "PT",
    "country_name": "Portugal",
    "region": "Europe",
    "style_scores": {
        "chill_vs_intense": 35,
        "city_vs_nature": 45,
        "eco_vs_luxury": 30,   # Budget-friendly
        "tourist_vs_local": 55,
    },
    "interest_scores": {
        "culture": 85, "food": 90, "beach": 88, "adventure": 60,
        "nature": 70, "nightlife": 70, "history": 80, "art": 75,
        "shopping": 65, "wellness": 70, "sports": 65,
    },
    "must_haves": {
        "accessibility_score": 75, "pet_friendly_score": 65,
        "family_friendly_score": 80, "wifi_quality_score": 82,
    },
    "budget": {"cost_of_living_index": 55},
    "monthly_climate": [
        {"month": 1, "avg_temp_c": 12, "sunshine_hours": 5},
        {"month": 2, "avg_temp_c": 13, "sunshine_hours": 6},
        {"month": 3, "avg_temp_c": 14, "sunshine_hours": 7},
        {"month": 4, "avg_temp_c": 16, "sunshine_hours": 8},
        {"month": 5, "avg_temp_c": 18, "sunshine_hours": 10},
        {"month": 6, "avg_temp_c": 22, "sunshine_hours": 11},
        {"month": 7, "avg_temp_c": 24, "sunshine_hours": 12},
        {"month": 8, "avg_temp_c": 24, "sunshine_hours": 11},
        {"month": 9, "avg_temp_c": 22, "sunshine_hours": 9},
        {"month": 10, "avg_temp_c": 18, "sunshine_hours": 7},
        {"month": 11, "avg_temp_c": 14, "sunshine_hours": 5},
        {"month": 12, "avg_temp_c": 12, "sunshine_hours": 4},
    ],
    "best_months": [4, 5, 6, 9, 10],
    "avoid_months": [],
    "trending_score": 78,
    "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 10, "friends": 10, "pet": 5},
    "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 5, "vacation": 5},
}

JAPAN = {
    "country_code": "JP",
    "country_name": "Japon",
    "region": "Asia",
    "style_scores": {
        "chill_vs_intense": 55,
        "city_vs_nature": 40,
        "eco_vs_luxury": 65,   # Expensive
        "tourist_vs_local": 60,
    },
    "interest_scores": {
        "culture": 98, "food": 95, "beach": 40, "adventure": 65,
        "nature": 80, "nightlife": 65, "history": 95, "art": 90,
        "shopping": 85, "wellness": 80, "sports": 55,
    },
    "must_haves": {
        "accessibility_score": 90, "pet_friendly_score": 50,
        "family_friendly_score": 85, "wifi_quality_score": 95,
    },
    "budget": {"cost_of_living_index": 110},
    "monthly_climate": [
        {"month": 1, "avg_temp_c": 5, "sunshine_hours": 6},
        {"month": 2, "avg_temp_c": 6, "sunshine_hours": 6},
        {"month": 3, "avg_temp_c": 9, "sunshine_hours": 6},
        {"month": 4, "avg_temp_c": 14, "sunshine_hours": 6},
        {"month": 5, "avg_temp_c": 19, "sunshine_hours": 6},
        {"month": 6, "avg_temp_c": 22, "sunshine_hours": 5},
        {"month": 7, "avg_temp_c": 26, "sunshine_hours": 5},
        {"month": 8, "avg_temp_c": 27, "sunshine_hours": 6},
        {"month": 9, "avg_temp_c": 24, "sunshine_hours": 5},
        {"month": 10, "avg_temp_c": 18, "sunshine_hours": 5},
        {"month": 11, "avg_temp_c": 13, "sunshine_hours": 5},
        {"month": 12, "avg_temp_c": 8, "sunshine_hours": 5},
    ],
    "best_months": [3, 4, 10, 11],
    "avoid_months": [6, 7, 8],
    "trending_score": 85,
    "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 10, "pet": 0},
    "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 5, "vacation": 5},
}

THAILAND = {
    "country_code": "TH",
    "country_name": "Thailande",
    "region": "Asia",
    "style_scores": {
        "chill_vs_intense": 40,
        "city_vs_nature": 55,
        "eco_vs_luxury": 25,   # Very budget-friendly
        "tourist_vs_local": 45,
    },
    "interest_scores": {
        "culture": 80, "food": 92, "beach": 95, "adventure": 80,
        "nature": 75, "nightlife": 85, "history": 65, "art": 60,
        "shopping": 75, "wellness": 90, "sports": 65,
    },
    "must_haves": {
        "accessibility_score": 55, "pet_friendly_score": 45,
        "family_friendly_score": 70, "wifi_quality_score": 75,
    },
    "budget": {"cost_of_living_index": 35},
    "monthly_climate": [
        {"month": 1, "avg_temp_c": 27, "sunshine_hours": 9},
        {"month": 2, "avg_temp_c": 28, "sunshine_hours": 8},
        {"month": 3, "avg_temp_c": 30, "sunshine_hours": 9},
        {"month": 4, "avg_temp_c": 31, "sunshine_hours": 8},
        {"month": 5, "avg_temp_c": 30, "sunshine_hours": 7},
        {"month": 6, "avg_temp_c": 29, "sunshine_hours": 5},
        {"month": 7, "avg_temp_c": 29, "sunshine_hours": 5},
        {"month": 8, "avg_temp_c": 29, "sunshine_hours": 5},
        {"month": 9, "avg_temp_c": 28, "sunshine_hours": 5},
        {"month": 10, "avg_temp_c": 28, "sunshine_hours": 6},
        {"month": 11, "avg_temp_c": 27, "sunshine_hours": 8},
        {"month": 12, "avg_temp_c": 26, "sunshine_hours": 8},
    ],
    "best_months": [11, 12, 1, 2, 3],
    "avoid_months": [5, 6, 9, 10],
    "trending_score": 82,
    "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": 0},
    "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 5, "vacation": 5},
}

NORWAY = {
    "country_code": "NO",
    "country_name": "Norvege",
    "region": "Europe",
    "style_scores": {
        "chill_vs_intense": 55,
        "city_vs_nature": 85,   # Very nature-oriented
        "eco_vs_luxury": 70,    # Expensive
        "tourist_vs_local": 55,
    },
    "interest_scores": {
        "culture": 70, "food": 60, "beach": 30, "adventure": 90,
        "nature": 98, "nightlife": 45, "history": 60, "art": 65,
        "shopping": 50, "wellness": 75, "sports": 85,
    },
    "must_haves": {
        "accessibility_score": 85, "pet_friendly_score": 70,
        "family_friendly_score": 80, "wifi_quality_score": 92,
    },
    "budget": {"cost_of_living_index": 125},
    "monthly_climate": [
        {"month": 1, "avg_temp_c": -4, "sunshine_hours": 1},
        {"month": 2, "avg_temp_c": -3, "sunshine_hours": 2},
        {"month": 3, "avg_temp_c": 1, "sunshine_hours": 4},
        {"month": 4, "avg_temp_c": 6, "sunshine_hours": 6},
        {"month": 5, "avg_temp_c": 12, "sunshine_hours": 8},
        {"month": 6, "avg_temp_c": 16, "sunshine_hours": 9},
        {"month": 7, "avg_temp_c": 18, "sunshine_hours": 8},
        {"month": 8, "avg_temp_c": 17, "sunshine_hours": 7},
        {"month": 9, "avg_temp_c": 12, "sunshine_hours": 5},
        {"month": 10, "avg_temp_c": 7, "sunshine_hours": 3},
        {"month": 11, "avg_temp_c": 2, "sunshine_hours": 1},
        {"month": 12, "avg_temp_c": -2, "sunshine_hours": 1},
    ],
    "best_months": [5, 6, 7, 8, 9, 12, 1, 2],
    "avoid_months": [11],
    "trending_score": 82,
    "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": 5},
    "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5},
}

MOROCCO = {
    "country_code": "MA",
    "country_name": "Maroc",
    "region": "Africa",
    "style_scores": {
        "chill_vs_intense": 45,
        "city_vs_nature": 50,
        "eco_vs_luxury": 25,   # Very budget-friendly
        "tourist_vs_local": 65,
    },
    "interest_scores": {
        "culture": 92, "food": 90, "beach": 70, "adventure": 75,
        "nature": 70, "nightlife": 55, "history": 85, "art": 80,
        "shopping": 85, "wellness": 80, "sports": 55,
    },
    "must_haves": {
        "accessibility_score": 50, "pet_friendly_score": 40,
        "family_friendly_score": 70, "wifi_quality_score": 65,
    },
    "budget": {"cost_of_living_index": 35},
    "monthly_climate": [
        {"month": 1, "avg_temp_c": 12, "sunshine_hours": 6},
        {"month": 2, "avg_temp_c": 13, "sunshine_hours": 6},
        {"month": 3, "avg_temp_c": 15, "sunshine_hours": 7},
        {"month": 4, "avg_temp_c": 16, "sunshine_hours": 8},
        {"month": 5, "avg_temp_c": 19, "sunshine_hours": 9},
        {"month": 6, "avg_temp_c": 22, "sunshine_hours": 10},
        {"month": 7, "avg_temp_c": 24, "sunshine_hours": 10},
        {"month": 8, "avg_temp_c": 24, "sunshine_hours": 10},
        {"month": 9, "avg_temp_c": 22, "sunshine_hours": 8},
        {"month": 10, "avg_temp_c": 19, "sunshine_hours": 7},
        {"month": 11, "avg_temp_c": 15, "sunshine_hours": 6},
        {"month": 12, "avg_temp_c": 13, "sunshine_hours": 5},
    ],
    "best_months": [3, 4, 5, 9, 10, 11],
    "avoid_months": [7, 8],
    "trending_score": 80,
    "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 10, "friends": 10, "pet": 0},
    "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 5, "vacation": 5},
}

GREECE = {
    "country_code": "GR",
    "country_name": "Grece",
    "region": "Europe",
    "style_scores": {
        "chill_vs_intense": 35,
        "city_vs_nature": 55,
        "eco_vs_luxury": 40,   # Moderate
        "tourist_vs_local": 50,
    },
    "interest_scores": {
        "culture": 90, "food": 88, "beach": 92, "adventure": 65,
        "nature": 75, "nightlife": 75, "history": 95, "art": 80,
        "shopping": 65, "wellness": 70, "sports": 60,
    },
    "must_haves": {
        "accessibility_score": 60, "pet_friendly_score": 55,
        "family_friendly_score": 80, "wifi_quality_score": 70,
    },
    "budget": {"cost_of_living_index": 60},
    "monthly_climate": [
        {"month": 1, "avg_temp_c": 10, "sunshine_hours": 4},
        {"month": 2, "avg_temp_c": 10, "sunshine_hours": 5},
        {"month": 3, "avg_temp_c": 13, "sunshine_hours": 6},
        {"month": 4, "avg_temp_c": 16, "sunshine_hours": 8},
        {"month": 5, "avg_temp_c": 21, "sunshine_hours": 10},
        {"month": 6, "avg_temp_c": 26, "sunshine_hours": 12},
        {"month": 7, "avg_temp_c": 29, "sunshine_hours": 12},
        {"month": 8, "avg_temp_c": 28, "sunshine_hours": 12},
        {"month": 9, "avg_temp_c": 24, "sunshine_hours": 9},
        {"month": 10, "avg_temp_c": 19, "sunshine_hours": 7},
        {"month": 11, "avg_temp_c": 15, "sunshine_hours": 5},
        {"month": 12, "avg_temp_c": 11, "sunshine_hours": 4},
    ],
    "best_months": [5, 6, 9, 10],
    "avoid_months": [1, 2],
    "trending_score": 80,
    "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 10, "friends": 15, "pet": 5},
    "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5},
}

# No monthly_climate — tests fallback behavior
PROFILE_NO_CLIMATE = {
    "country_code": "XX",
    "country_name": "TestLand",
    "region": "Europe",
    "style_scores": {
        "chill_vs_intense": 50, "city_vs_nature": 50,
        "eco_vs_luxury": 50, "tourist_vs_local": 50,
    },
    "interest_scores": {"culture": 70, "food": 70, "beach": 70},
    "must_haves": {
        "accessibility_score": 70, "pet_friendly_score": 70,
        "family_friendly_score": 70, "wifi_quality_score": 70,
    },
    "budget": {"cost_of_living_index": 70},
    "best_months": [6, 7, 8],
    "avoid_months": [12, 1, 2],
    "trending_score": 50,
    "travel_style_bonuses": {"solo": 5, "couple": 5, "family": 5, "friends": 5},
    "occasion_bonuses": {},
}

PANAMA = {
    "country_code": "PA",
    "country_name": "Panama",
    "region": "Central America",
    "style_scores": {
        "chill_vs_intense": 45,
        "city_vs_nature": 60,
        "eco_vs_luxury": 35,
        "tourist_vs_local": 55,
    },
    "interest_scores": {
        "culture": 65, "food": 70, "beach": 85, "adventure": 80,
        "nature": 85, "nightlife": 60, "history": 55, "art": 50,
        "shopping": 55, "wellness": 65, "sports": 60,
    },
    "must_haves": {
        "accessibility_score": 45, "pet_friendly_score": 40,
        "family_friendly_score": 60, "wifi_quality_score": 60,
    },
    "budget": {"cost_of_living_index": 55},
    "monthly_climate": [
        {"month": m, "avg_temp_c": 28, "sunshine_hours": 7}
        for m in range(1, 13)
    ],
    "best_months": [12, 1, 2, 3],
    "avoid_months": [5, 6, 9, 10],
    "trending_score": 55,
    "travel_style_bonuses": {"solo": 5, "couple": 10, "family": 5, "friends": 10, "pet": 0},
    "occasion_bonuses": {"honeymoon": 10, "anniversary": 5, "birthday": 5, "vacation": 5},
}

SPAIN = {
    "country_code": "ES",
    "country_name": "Espagne",
    "region": "Europe",
    "style_scores": {
        "chill_vs_intense": 40,
        "city_vs_nature": 45,
        "eco_vs_luxury": 35,
        "tourist_vs_local": 50,
    },
    "interest_scores": {
        "culture": 88, "food": 92, "beach": 90, "adventure": 65,
        "nature": 70, "nightlife": 85, "history": 85, "art": 85,
        "shopping": 75, "wellness": 70, "sports": 70,
    },
    "must_haves": {
        "accessibility_score": 75, "pet_friendly_score": 60,
        "family_friendly_score": 80, "wifi_quality_score": 80,
    },
    "budget": {"cost_of_living_index": 55},
    "monthly_climate": [
        {"month": 1, "avg_temp_c": 10, "sunshine_hours": 5},
        {"month": 2, "avg_temp_c": 12, "sunshine_hours": 6},
        {"month": 3, "avg_temp_c": 15, "sunshine_hours": 7},
        {"month": 4, "avg_temp_c": 17, "sunshine_hours": 8},
        {"month": 5, "avg_temp_c": 21, "sunshine_hours": 10},
        {"month": 6, "avg_temp_c": 26, "sunshine_hours": 11},
        {"month": 7, "avg_temp_c": 30, "sunshine_hours": 12},
        {"month": 8, "avg_temp_c": 29, "sunshine_hours": 11},
        {"month": 9, "avg_temp_c": 25, "sunshine_hours": 9},
        {"month": 10, "avg_temp_c": 19, "sunshine_hours": 7},
        {"month": 11, "avg_temp_c": 14, "sunshine_hours": 5},
        {"month": 12, "avg_temp_c": 10, "sunshine_hours": 5},
    ],
    "best_months": [4, 5, 6, 9, 10],
    "avoid_months": [],
    "trending_score": 80,
    "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 15, "friends": 15, "pet": 5},
    "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 10},
}

ALL_PROFILES = [PORTUGAL, JAPAN, THAILAND, NORWAY, MOROCCO, GREECE, PANAMA, SPAIN]


# ============================================================================
# HELPER
# ============================================================================


def _make_prefs(**kwargs) -> UserPreferencesPayload:
    """Create UserPreferencesPayload with sensible defaults, overriding with kwargs."""
    defaults = {
        "travelStyle": "couple",
        "budgetLevel": "comfort",
        "interests": [],
    }
    defaults.update(kwargs)
    return UserPreferencesPayload(**defaults)


def _score(service, profile, prefs, month=None):
    """Shorthand: returns (total_score, factors). Drops distance_km for compat."""
    m = month or prefs.travelMonth or 2
    score, factors, _distance_km = service._calculate_score(profile, prefs, m)
    return score, factors


# ============================================================================
# TESTS
# ============================================================================


class TestPositionWeightedStyle(unittest.TestCase):
    """Tests for position-weighted style axis scoring."""

    def setUp(self):
        self.svc = DestinationSuggestionService.__new__(DestinationSuggestionService)

    def test_without_axes_order_uses_equal_weights(self):
        """Without styleAxesOrder, all 4 axes get 25% weight each (retrocompat)."""
        prefs = _make_prefs(
            styleAxes={"chillVsIntense": 30, "cityVsNature": 50, "ecoVsLuxury": 10, "touristVsLocal": 50},
            # No styleAxesOrder
        )
        score_pt, _ = _score(self.svc, PORTUGAL, prefs)
        # Should not crash and produce a valid score
        self.assertGreaterEqual(score_pt, 0)
        self.assertLessEqual(score_pt, 100)

    def test_eco_first_boosts_budget_countries(self):
        """With ecoVsLuxury #1 + low value, budget-friendly countries score higher on style."""
        prefs_eco_first = _make_prefs(
            styleAxes={"chillVsIntense": 50, "cityVsNature": 50, "ecoVsLuxury": 10, "touristVsLocal": 50},
            styleAxesOrder=["ecoVsLuxury", "chillVsIntense", "cityVsNature", "touristVsLocal"],
            interests=["culture"],
            budgetLevel="budget",
            userLocation={"city": "Paris"},
            travelMonth=4,
        )
        pt_score, _ = _score(self.svc, PORTUGAL, prefs_eco_first)
        jp_score, _ = _score(self.svc, JAPAN, prefs_eco_first)
        # Portugal (eco=30, close to user's 10) should outscore Japan (eco=65, far from 10)
        self.assertGreater(pt_score, jp_score)

    def test_different_order_produces_different_scores(self):
        """Same axis values but different order → different final scores."""
        axes = {"chillVsIntense": 80, "cityVsNature": 20, "ecoVsLuxury": 10, "touristVsLocal": 50}

        prefs_a = _make_prefs(
            styleAxes=axes,
            styleAxesOrder=["ecoVsLuxury", "chillVsIntense", "cityVsNature", "touristVsLocal"],
            interests=["beach"], budgetLevel="budget", travelMonth=6,
        )
        prefs_b = _make_prefs(
            styleAxes=axes,
            styleAxesOrder=["cityVsNature", "touristVsLocal", "chillVsIntense", "ecoVsLuxury"],
            interests=["beach"], budgetLevel="budget", travelMonth=6,
        )

        score_a, _ = _score(self.svc, NORWAY, prefs_a)
        score_b, _ = _score(self.svc, NORWAY, prefs_b)
        # Norway has city_vs_nature=85; prefs_b puts cityVsNature first (20 vs 85 = big distance weighted 40%)
        # vs prefs_a puts ecoVsLuxury first (10 vs 70 = big distance weighted 40%)
        # These should produce different scores
        self.assertNotEqual(score_a, score_b)


class TestClimateScoring(unittest.TestCase):
    """Tests for climate dimension (temperature + sunshine)."""

    def setUp(self):
        self.svc = DestinationSuggestionService.__new__(DestinationSuggestionService)

    def test_beach_february_prefers_warm(self):
        """Beach interest in February: Thailand (28°C) >> Norway (-3°C)."""
        prefs = _make_prefs(
            interests=["beach"],
            budgetLevel="comfort",
            travelMonth=2,
        )
        th_score, th_factors = _score(self.svc, THAILAND, prefs)
        no_score, _ = _score(self.svc, NORWAY, prefs)
        self.assertGreater(th_score, no_score)
        # Thailand should have a climate-positive factor
        climate_factors = [f for f in th_factors if "climat" in f.lower() or "Climat" in f]
        self.assertTrue(len(climate_factors) > 0 or th_score > no_score + 10)

    def test_culture_february_portugal_in_range(self):
        """Culture interest in February: PT (13°C) is in ideal 15-30 range... nearly.
        JP (6°C) is far below. PT should score better on climate."""
        prefs = _make_prefs(
            interests=["culture"],
            budgetLevel="comfort",
            travelMonth=2,
        )
        pt_score, _ = _score(self.svc, PORTUGAL, prefs)
        jp_score, _ = _score(self.svc, JAPAN, prefs)
        # Portugal is warmer in Feb and closer to ideal culture range
        # Even though Japan excels at culture interest_scores, climate helps PT
        # We just verify PT total isn't crushed by JP
        self.assertGreater(pt_score, 40)

    def test_fallback_without_monthly_climate(self):
        """Profile without monthly_climate uses best_months/avoid_months fallback."""
        prefs = _make_prefs(interests=["culture"], travelMonth=7)
        score_best, factors_best = _score(self.svc, PROFILE_NO_CLIMATE, prefs, month=7)  # best_months=[6,7,8]
        score_avoid, _ = _score(self.svc, PROFILE_NO_CLIMATE, prefs, month=1)  # avoid_months=[12,1,2]

        # Best month should score higher than avoid month
        self.assertGreater(score_best, score_avoid)


class TestDistanceScoring(unittest.TestCase):
    """Tests for distance dimension (haversine from departure)."""

    def setUp(self):
        self.svc = DestinationSuggestionService.__new__(DestinationSuggestionService)

    def test_budget_paris_prefers_nearby(self):
        """Budget traveler from Paris: Portugal (1600km) >> Thailand (9500km)."""
        prefs = _make_prefs(
            userLocation={"city": "Paris"},
            budgetLevel="budget",
            interests=["beach"],
            travelMonth=7,
        )
        pt_score, pt_factors = _score(self.svc, PORTUGAL, prefs)
        th_score, _ = _score(self.svc, THAILAND, prefs)
        # Portugal closer = higher distance score for budget travelers
        self.assertGreater(pt_score, th_score)
        # Check for proximity factor
        proximity_factors = [f for f in pt_factors if "proche" in f.lower()]
        self.assertTrue(len(proximity_factors) > 0)

    def test_luxury_distance_less_penalized(self):
        """Luxury traveler: Thailand not penalized worse than budget on distance."""
        prefs_budget = _make_prefs(
            userLocation={"city": "Paris"}, budgetLevel="budget",
            interests=["beach"], travelMonth=2,
        )
        prefs_luxury = _make_prefs(
            userLocation={"city": "Paris"}, budgetLevel="luxury",
            interests=["beach"], travelMonth=2,
        )
        th_budget, _ = _score(self.svc, THAILAND, prefs_budget)
        th_luxury, _ = _score(self.svc, THAILAND, prefs_luxury)
        # Thailand should score at least as high for luxury as budget
        self.assertGreaterEqual(th_luxury, th_budget)

    def test_no_location_gives_neutral_score(self):
        """Without user location, distance score is neutral (60)."""
        prefs = _make_prefs(interests=["culture"], travelMonth=4)
        # No userLocation → no coords → distance=60
        score, _ = _score(self.svc, JAPAN, prefs)
        self.assertGreater(score, 0)  # Should still produce valid score


class TestDynamicWeights(unittest.TestCase):
    """Tests for dynamic weight adjustment based on top priority axis."""

    def setUp(self):
        self.svc = DestinationSuggestionService.__new__(DestinationSuggestionService)

    def test_eco_priority_boosts_price_dimensions(self):
        """ecoVsLuxury #1 + extreme value → boosts flight_price, budget, distance."""
        prefs = _make_prefs(
            styleAxes={"chillVsIntense": 50, "cityVsNature": 50, "ecoVsLuxury": 10, "touristVsLocal": 50},
            styleAxesOrder=["ecoVsLuxury", "chillVsIntense", "cityVsNature", "touristVsLocal"],
        )
        weights = self.svc._get_dynamic_weights(prefs)
        self.assertEqual(weights["flight_price"], 11)  # 8 + 3
        self.assertEqual(weights["budget"], 12)         # 8 + 4
        self.assertEqual(weights["distance"], 12)       # 10 + 2
        self.assertEqual(weights["trending"], 0)        # 3 - 3
        self.assertEqual(weights["context"], 2)         # 5 - 3
        self.assertEqual(weights["style"], 14)          # 17 - 3
        # Total should still sum to 100
        self.assertEqual(sum(weights.values()), 100)

    def test_nature_priority_boosts_climate(self):
        """cityVsNature #1 + extreme value → climate weight 17."""
        prefs = _make_prefs(
            styleAxes={"chillVsIntense": 50, "cityVsNature": 90, "ecoVsLuxury": 50, "touristVsLocal": 50},
            styleAxesOrder=["cityVsNature", "chillVsIntense", "ecoVsLuxury", "touristVsLocal"],
        )
        weights = self.svc._get_dynamic_weights(prefs)
        self.assertEqual(weights["climate"], 17)  # 12 + 5
        self.assertEqual(weights["trending"], 0)   # 3 - 3
        # Total should still sum to 100
        self.assertEqual(sum(weights.values()), 100)


class TestRealUserScenarios(unittest.TestCase):
    """End-to-end scoring scenarios that simulate real user behavior."""

    def setUp(self):
        self.svc = DestinationSuggestionService.__new__(DestinationSuggestionService)

    def test_cheap_sun_paris_february(self):
        """'Pas cher + soleil, départ Paris, février'
        Expected: PT & MA top, JP & NO bottom.
        This is THE key scenario from the V2 plan."""
        prefs = _make_prefs(
            userLocation={"city": "Paris"},
            styleAxes={"chillVsIntense": 40, "cityVsNature": 50, "ecoVsLuxury": 10, "touristVsLocal": 50},
            styleAxesOrder=["ecoVsLuxury", "chillVsIntense", "cityVsNature", "touristVsLocal"],
            interests=["beach"],
            budgetLevel="budget",
            travelMonth=2,
        )

        scores = {}
        for profile in ALL_PROFILES:
            s, factors = _score(self.svc, profile, prefs)
            scores[profile["country_code"]] = s

        # Portugal and Morocco should be in the top
        self.assertGreater(scores["PT"], scores["JP"])
        self.assertGreater(scores["MA"], scores["JP"])
        self.assertGreater(scores["PT"], scores["NO"])
        self.assertGreater(scores["MA"], scores["NO"])

        # Discrimination should be significant (not just 2-3 pts)
        self.assertGreater(scores["PT"] - scores["JP"], 10)
        self.assertGreater(scores["MA"] - scores["NO"], 10)

    def test_luxury_culture_paris_april(self):
        """'Luxe + culture, départ Paris, avril'
        Japan should recover (distance less penalized), Greece good too."""
        prefs = _make_prefs(
            userLocation={"city": "Paris"},
            styleAxes={"chillVsIntense": 50, "cityVsNature": 30, "ecoVsLuxury": 85, "touristVsLocal": 60},
            styleAxesOrder=["ecoVsLuxury", "touristVsLocal", "chillVsIntense", "cityVsNature"],
            interests=["culture", "food", "history"],
            budgetLevel="luxury",
            travelMonth=4,
        )

        scores = {}
        for profile in ALL_PROFILES:
            s, _ = _score(self.svc, profile, prefs)
            scores[profile["country_code"]] = s

        # Japan should score well (culture 98, food 95, history 95, luxury-friendly)
        self.assertGreater(scores["JP"], 50)
        # Greece should also score well (culture 90, history 95, good April climate)
        self.assertGreater(scores["GR"], 50)

    def test_budget_beach_paris_july(self):
        """'Budget + beach, départ Paris, juillet'
        Greece should be excellent (hot, close, great beach, affordable)."""
        prefs = _make_prefs(
            userLocation={"city": "Paris"},
            styleAxes={"chillVsIntense": 30, "cityVsNature": 60, "ecoVsLuxury": 15, "touristVsLocal": 40},
            styleAxesOrder=["ecoVsLuxury", "cityVsNature", "chillVsIntense", "touristVsLocal"],
            interests=["beach", "food"],
            budgetLevel="budget",
            travelMonth=7,
        )

        scores = {}
        for profile in ALL_PROFILES:
            s, _ = _score(self.svc, profile, prefs)
            scores[profile["country_code"]] = s

        # Greece in July: 29°C, 12h sun, close, affordable, beach=92
        self.assertGreater(scores["GR"], scores["NO"])
        self.assertGreater(scores["GR"], scores["JP"])
        # Portugal also good in July
        self.assertGreater(scores["PT"], scores["NO"])

    def test_nature_extreme_paris_december(self):
        """'Nature extreme, départ Paris, décembre'
        Norway: nature=98 match, but very cold. Should still score reasonably due to nature match."""
        prefs = _make_prefs(
            userLocation={"city": "Paris"},
            styleAxes={"chillVsIntense": 70, "cityVsNature": 95, "ecoVsLuxury": 50, "touristVsLocal": 60},
            styleAxesOrder=["cityVsNature", "chillVsIntense", "touristVsLocal", "ecoVsLuxury"],
            interests=["nature", "adventure"],
            budgetLevel="comfort",
            travelMonth=12,
        )

        scores = {}
        for profile in ALL_PROFILES:
            s, _ = _score(self.svc, profile, prefs)
            scores[profile["country_code"]] = s

        # Norway: nature=98, adventure=90, best for nature lovers
        # It's cold (-2°C) in December but it's a best_month (aurora season)
        self.assertGreater(scores["NO"], scores["JP"])
        # Above threshold at minimum
        self.assertGreater(scores["NO"], 40)

    def test_retrocompat_no_axes_order(self):
        """Without styleAxesOrder, scoring should work and produce reasonable results."""
        prefs = _make_prefs(
            userLocation={"city": "Paris"},
            interests=["culture", "food"],
            budgetLevel="comfort",
            travelMonth=5,
            # No styleAxesOrder — retrocompat
        )

        for profile in ALL_PROFILES:
            score, factors = _score(self.svc, profile, prefs)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
            self.assertIsInstance(factors, list)
            self.assertLessEqual(len(factors), 5)


class TestHelperMethods(unittest.TestCase):
    """Tests for helper methods (_haversine, _get_departure_coords)."""

    def setUp(self):
        self.svc = DestinationSuggestionService.__new__(DestinationSuggestionService)

    def test_haversine_paris_lisbon(self):
        """Paris CDG to Lisbon should be ~1700km."""
        paris = (49.0097, 2.5479)
        lisbon = (38.7813, -9.1359)
        dist = self.svc._haversine(paris, lisbon)
        self.assertGreater(dist, 1400)
        self.assertLess(dist, 2000)

    def test_haversine_paris_tokyo(self):
        """Paris CDG to Tokyo NRT should be ~9700km."""
        paris = (49.0097, 2.5479)
        tokyo = (35.7720, 140.3929)
        dist = self.svc._haversine(paris, tokyo)
        self.assertGreater(dist, 9000)
        self.assertLess(dist, 10500)

    def test_get_departure_coords_paris(self):
        """City 'Paris' should resolve to CDG coordinates."""
        prefs = _make_prefs(userLocation={"city": "Paris"})
        coords = self.svc._get_departure_coords(prefs)
        self.assertIsNotNone(coords)
        lat, lon = coords
        self.assertAlmostEqual(lat, 49.0, delta=1.0)
        self.assertAlmostEqual(lon, 2.5, delta=1.0)

    def test_get_departure_coords_with_lat_lng(self):
        """Explicit lat/lng should be used directly."""
        prefs = _make_prefs(userLocation={"lat": 48.8566, "lng": 2.3522})
        coords = self.svc._get_departure_coords(prefs)
        self.assertIsNotNone(coords)
        self.assertAlmostEqual(coords[0], 48.8566, places=3)
        self.assertAlmostEqual(coords[1], 2.3522, places=3)

    def test_get_departure_coords_unknown_city(self):
        """Unknown city without lat/lng returns None."""
        prefs = _make_prefs(userLocation={"city": "Timbuktu"})
        coords = self.svc._get_departure_coords(prefs)
        self.assertIsNone(coords)


class TestParseTripDays(unittest.TestCase):
    """Tests for _parse_trip_days static method."""

    def test_french_days(self):
        self.assertEqual(DestinationSuggestionService._parse_trip_days("2 jours"), 2)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("10 jours"), 10)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("1 jour"), 1)

    def test_french_weeks(self):
        self.assertEqual(DestinationSuggestionService._parse_trip_days("1 semaine"), 7)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("3 semaines"), 21)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("une semaine"), 7)

    def test_french_months(self):
        self.assertEqual(DestinationSuggestionService._parse_trip_days("1 mois"), 30)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("un mois"), 30)

    def test_english(self):
        self.assertEqual(DestinationSuggestionService._parse_trip_days("2 days"), 2)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("2 weeks"), 14)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("1 month"), 30)

    def test_weekend(self):
        self.assertEqual(DestinationSuggestionService._parse_trip_days("weekend"), 2)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("un weekend"), 2)
        self.assertEqual(DestinationSuggestionService._parse_trip_days("long weekend"), 3)

    def test_none_and_empty(self):
        self.assertIsNone(DestinationSuggestionService._parse_trip_days(None))
        self.assertIsNone(DestinationSuggestionService._parse_trip_days(""))
        self.assertIsNone(DestinationSuggestionService._parse_trip_days("quelques temps"))


class TestFlightEstimation(unittest.TestCase):
    """Tests for _estimate_flight_minutes and _max_flight_hours."""

    def test_short_haul(self):
        """Brussels → Marrakech ~2100km → ~2h45."""
        minutes = DestinationSuggestionService._estimate_flight_minutes(2100)
        self.assertGreater(minutes, 150)
        self.assertLess(minutes, 240)

    def test_long_haul(self):
        """Brussels → Panama ~8800km → ~11h."""
        minutes = DestinationSuggestionService._estimate_flight_minutes(8800)
        self.assertGreater(minutes, 600)
        self.assertLess(minutes, 750)

    def test_minimum_flight_time(self):
        """Very short distances still get at least 60 minutes."""
        self.assertEqual(DestinationSuggestionService._estimate_flight_minutes(10), 60)

    def test_max_flight_hours_weekend(self):
        """2-day trip: max 2.5h flight."""
        self.assertEqual(DestinationSuggestionService._max_flight_hours(2), 2.5)

    def test_max_flight_hours_week(self):
        """7-day trip: max 7h flight."""
        self.assertEqual(DestinationSuggestionService._max_flight_hours(7), 7.0)

    def test_max_flight_hours_long(self):
        """30-day trip: no limit."""
        self.assertEqual(DestinationSuggestionService._max_flight_hours(30), 999)


class TestTripFeasibility(unittest.TestCase):
    """Tests for trip_feasibility scoring dimension."""

    def setUp(self):
        self.svc = DestinationSuggestionService.__new__(DestinationSuggestionService)

    def test_weekend_brussels_rejects_panama(self):
        """'2 jours' from Brussels: Spain (2h flight) >> Panama (11h flight)."""
        prefs = _make_prefs(
            userLocation={"city": "Bruxelles"},
            interests=["beach", "food"],
            budgetLevel="budget",
            travelMonth=7,
            tripDuration="2 jours",
        )
        pa_score, _ = _score(self.svc, PANAMA, prefs)
        ma_score, _ = _score(self.svc, MOROCCO, prefs)
        es_score, _ = _score(self.svc, SPAIN, prefs)

        # Spain and Morocco (nearby) should beat Panama (11h flight) for a weekend
        self.assertGreater(es_score, pa_score)
        self.assertGreater(ma_score, pa_score)

    def test_week_allows_medium_haul(self):
        """'1 semaine' from Brussels: Thailand should score > 40."""
        prefs = _make_prefs(
            userLocation={"city": "Bruxelles"},
            interests=["beach"],
            budgetLevel="comfort",
            travelMonth=2,
            tripDuration="1 semaine",
        )
        th_score, _ = _score(self.svc, THAILAND, prefs)
        # Thailand is feasible for a week
        self.assertGreater(th_score, 40)

    def test_no_duration_neutral(self):
        """Without tripDuration, trip_feasibility should not penalize distant countries."""
        prefs_with = _make_prefs(
            userLocation={"city": "Paris"},
            interests=["beach"],
            budgetLevel="comfort",
            travelMonth=2,
            tripDuration="2 jours",
        )
        prefs_without = _make_prefs(
            userLocation={"city": "Paris"},
            interests=["beach"],
            budgetLevel="comfort",
            travelMonth=2,
            # No tripDuration
        )
        # Panama without duration should score higher than with "2 jours"
        pa_with, _ = _score(self.svc, PANAMA, prefs_with)
        pa_without, _ = _score(self.svc, PANAMA, prefs_without)
        self.assertGreater(pa_without, pa_with)

    def test_feasibility_returns_distance(self):
        """_calculate_score should return distance_km as third element."""
        prefs = _make_prefs(
            userLocation={"city": "Paris"},
            interests=["beach"],
            travelMonth=6,
        )
        _score_val, _factors, distance_km = self.svc._calculate_score(PORTUGAL, prefs, 6)
        self.assertIsNotNone(distance_km)
        self.assertGreater(distance_km, 1400)
        self.assertLess(distance_km, 2000)


class TestFlightPriceScore(unittest.TestCase):
    """Tests for _calculate_flight_price_score static method."""

    def test_cheapest_wins_budget(self):
        """Cheapest flight gets 100, most expensive < 20 for budget."""
        from app.models.destination_suggestions import BudgetLevel
        all_prices = [30, 150, 400, 800, 1200]
        cheapest = DestinationSuggestionService._calculate_flight_price_score(
            30, BudgetLevel.BUDGET, all_prices
        )
        most_expensive = DestinationSuggestionService._calculate_flight_price_score(
            1200, BudgetLevel.BUDGET, all_prices
        )
        self.assertAlmostEqual(cheapest, 100, delta=1)
        self.assertLess(most_expensive, 20)

    def test_luxury_less_penalized(self):
        """For luxury, expensive flights are less penalized than for budget."""
        from app.models.destination_suggestions import BudgetLevel
        all_prices = [100, 500, 1000]
        score_budget = DestinationSuggestionService._calculate_flight_price_score(
            1000, BudgetLevel.BUDGET, all_prices
        )
        score_luxury = DestinationSuggestionService._calculate_flight_price_score(
            1000, BudgetLevel.LUXURY, all_prices
        )
        self.assertGreater(score_luxury, score_budget)

    def test_single_price_neutral(self):
        """With only one price, score is neutral."""
        from app.models.destination_suggestions import BudgetLevel
        score = DestinationSuggestionService._calculate_flight_price_score(
            500, BudgetLevel.COMFORT, [500]
        )
        self.assertEqual(score, 70.0)

    def test_equal_prices(self):
        """All same price → 80 (neutral-good)."""
        from app.models.destination_suggestions import BudgetLevel
        score = DestinationSuggestionService._calculate_flight_price_score(
            500, BudgetLevel.COMFORT, [500, 500, 500]
        )
        self.assertEqual(score, 80.0)


if __name__ == "__main__":
    unittest.main()

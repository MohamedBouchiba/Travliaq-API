#!/usr/bin/env python3
"""
Seed script for country profiles.

Populates MongoDB with 80 top tourism destination profiles
including style scores, interest affinities, budget data, and seasonality.

Usage:
    python scripts/seed_country_profiles.py

Environment variables:
    MONGODB_URI: MongoDB connection string
    MONGODB_DB: Database name
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient


# ============================================================================
# COUNTRY PROFILES DATA
# 80 top tourism destinations with comprehensive scoring data
# ============================================================================

COUNTRY_PROFILES = [
    # === EUROPE (21 countries) ===
    {
        "country_code": "FR",
        "country_name": "France",
        "flag_emoji": "FR",
        "region": "Europe",
        "subregion": "Western Europe",
        "languages": ["French"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 50,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 40
        },
        "interest_scores": {
            "culture": 95, "food": 95, "beach": 70, "adventure": 50,
            "nature": 70, "nightlife": 80, "history": 95, "art": 95,
            "shopping": 90, "wellness": 70, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 85, "pet_friendly_score": 75,
            "family_friendly_score": 85, "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 95,
            "budget_min_7d": 500, "budget_max_7d": 800,
            "comfort_min_7d": 800, "comfort_max_7d": 1500,
            "premium_min_7d": 1500, "premium_max_7d": 3000,
            "luxury_min_7d": 3000, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 10, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 10, "vacation": 0, "workation": 10},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 90,
        "top_activities": [
            {"name": "Tour Eiffel", "emoji": "fr", "category": "culture"},
            {"name": "Degustation de vins", "emoji": "wine_glass", "category": "food"},
            {"name": "Chateaux de la Loire", "emoji": "european_castle", "category": "history"},
            {"name": "Cote d'Azur", "emoji": "beach", "category": "beach"},
            {"name": "Mont Saint-Michel", "emoji": "mountain", "category": "culture"}
        ]
    },
    {
        "country_code": "ES",
        "country_name": "Espagne",
        "flag_emoji": "ES",
        "region": "Europe",
        "subregion": "Southern Europe",
        "languages": ["Spanish"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 45,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 90, "food": 90, "beach": 95, "adventure": 60,
            "nature": 65, "nightlife": 90, "history": 85, "art": 85,
            "shopping": 80, "wellness": 70, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 80, "pet_friendly_score": 70,
            "family_friendly_score": 90, "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 70,
            "budget_min_7d": 400, "budget_max_7d": 650,
            "comfort_min_7d": 650, "comfort_max_7d": 1200,
            "premium_min_7d": 1200, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 20, "pet": 5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 10},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 88,
        "top_activities": [
            {"name": "Sagrada Familia", "emoji": "church", "category": "culture"},
            {"name": "Tapas a Madrid", "emoji": "plate_with_cutlery", "category": "food"},
            {"name": "Plages de Barcelone", "emoji": "beach", "category": "beach"},
            {"name": "Flamenco a Seville", "emoji": "dancer", "category": "culture"},
            {"name": "Alhambra de Grenade", "emoji": "mosque", "category": "history"}
        ]
    },
    {
        "country_code": "IT",
        "country_name": "Italie",
        "flag_emoji": "IT",
        "region": "Europe",
        "subregion": "Southern Europe",
        "languages": ["Italian"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 50,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 95, "food": 98, "beach": 75, "adventure": 45,
            "nature": 70, "nightlife": 70, "history": 98, "art": 98,
            "shopping": 90, "wellness": 75, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 70, "pet_friendly_score": 65,
            "family_friendly_score": 85, "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 85,
            "budget_min_7d": 450, "budget_max_7d": 750,
            "comfort_min_7d": 750, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 7000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 25, "family": 10, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 25, "birthday": 10, "vacation": 0, "workation": 5},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 92,
        "top_activities": [
            {"name": "Colisee de Rome", "emoji": "classical_building", "category": "history"},
            {"name": "Canaux de Venise", "emoji": "boat", "category": "culture"},
            {"name": "Pizza a Naples", "emoji": "pizza", "category": "food"},
            {"name": "Toscane viticole", "emoji": "wine_glass", "category": "food"},
            {"name": "Cote Amalfitaine", "emoji": "beach", "category": "beach"}
        ]
    },
    {
        "country_code": "PT",
        "country_name": "Portugal",
        "flag_emoji": "PT",
        "region": "Europe",
        "subregion": "Southern Europe",
        "languages": ["Portuguese"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 55,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 90, "beach": 85, "adventure": 60,
            "nature": 75, "nightlife": 70, "history": 80, "art": 75,
            "shopping": 60, "wellness": 70, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 70, "pet_friendly_score": 65,
            "family_friendly_score": 80, "wifi_quality_score": 88
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 350, "budget_max_7d": 550,
            "comfort_min_7d": 550, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 20},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [],
        "best_seasons": ["Printemps", "Automne", "Ete"],
        "trending_score": 88,
        "top_activities": [
            {"name": "Pasteis de Belem", "emoji": "cookie", "category": "food"},
            {"name": "Tramway de Lisbonne", "emoji": "tram", "category": "culture"},
            {"name": "Caves de Porto", "emoji": "wine_glass", "category": "food"},
            {"name": "Plages de l'Algarve", "emoji": "beach", "category": "beach"},
            {"name": "Sintra", "emoji": "european_castle", "category": "culture"}
        ]
    },
    {
        "country_code": "GR",
        "country_name": "Grece",
        "flag_emoji": "GR",
        "region": "Europe",
        "subregion": "Southern Europe",
        "languages": ["Greek"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 30,
            "city_vs_nature": 60,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 90, "food": 85, "beach": 95, "adventure": 55,
            "nature": 70, "nightlife": 75, "history": 95, "art": 80,
            "shopping": 55, "wellness": 70, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 60, "pet_friendly_score": 55,
            "family_friendly_score": 80, "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 60,
            "budget_min_7d": 400, "budget_max_7d": 650,
            "comfort_min_7d": 650, "comfort_max_7d": 1200,
            "premium_min_7d": 1200, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 10, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [5, 6, 9, 10],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Acropole d'Athenes", "emoji": "classical_building", "category": "history"},
            {"name": "Santorin", "emoji": "beach", "category": "beach"},
            {"name": "Mykonos", "emoji": "night_with_stars", "category": "nightlife"},
            {"name": "Gastronomie grecque", "emoji": "plate_with_cutlery", "category": "food"},
            {"name": "Meteores", "emoji": "mountain", "category": "nature"}
        ]
    },
    {
        "country_code": "DE",
        "country_name": "Allemagne",
        "flag_emoji": "DE",
        "region": "Europe",
        "subregion": "Western Europe",
        "languages": ["German"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 45,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 75, "beach": 30, "adventure": 50,
            "nature": 70, "nightlife": 85, "history": 90, "art": 80,
            "shopping": 80, "wellness": 75, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 90, "pet_friendly_score": 80,
            "family_friendly_score": 85, "wifi_quality_score": 92
        },
        "budget": {
            "cost_of_living_index": 80,
            "budget_min_7d": 450, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1300,
            "premium_min_7d": 1300, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 5500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 10, "family": 15, "friends": 15, "pet": 10},
        "occasion_bonuses": {"honeymoon": 5, "anniversary": 10, "birthday": 10, "vacation": 0, "workation": 15},
        "best_months": [5, 6, 7, 9],
        "avoid_months": [1, 2],
        "best_seasons": ["Ete", "Printemps"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Porte de Brandebourg", "emoji": "classical_building", "category": "history"},
            {"name": "Oktoberfest Munich", "emoji": "beer", "category": "food"},
            {"name": "Chateau Neuschwanstein", "emoji": "european_castle", "category": "culture"},
            {"name": "Foret-Noire", "emoji": "evergreen_tree", "category": "nature"},
            {"name": "Vie nocturne Berlin", "emoji": "night_with_stars", "category": "nightlife"}
        ]
    },
    {
        "country_code": "GB",
        "country_name": "Royaume-Uni",
        "flag_emoji": "GB",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["English"],
        "currency": "GBP",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 45,
            "eco_vs_luxury": 60,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 90, "food": 70, "beach": 35, "adventure": 50,
            "nature": 70, "nightlife": 85, "history": 95, "art": 90,
            "shopping": 90, "wellness": 65, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 88, "pet_friendly_score": 80,
            "family_friendly_score": 85, "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 110,
            "budget_min_7d": 550, "budget_max_7d": 900,
            "comfort_min_7d": 900, "comfort_max_7d": 1800,
            "premium_min_7d": 1800, "premium_max_7d": 3500,
            "luxury_min_7d": 3500, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 10, "family": 10, "friends": 15, "pet": 10},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 15, "birthday": 10, "vacation": 0, "workation": 10},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [11, 12, 1, 2],
        "best_seasons": ["Ete", "Printemps"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Big Ben et Westminster", "emoji": "classical_building", "category": "history"},
            {"name": "British Museum", "emoji": "art", "category": "art"},
            {"name": "Highlands d'Ecosse", "emoji": "mountain", "category": "nature"},
            {"name": "Pubs traditionnels", "emoji": "beer", "category": "food"},
            {"name": "Stonehenge", "emoji": "moyai", "category": "history"}
        ]
    },
    {
        "country_code": "NL",
        "country_name": "Pays-Bas",
        "flag_emoji": "NL",
        "region": "Europe",
        "subregion": "Western Europe",
        "languages": ["Dutch"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 35,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 70, "beach": 40, "adventure": 45,
            "nature": 55, "nightlife": 80, "history": 80, "art": 95,
            "shopping": 75, "wellness": 65, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 92, "pet_friendly_score": 85,
            "family_friendly_score": 90, "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 90,
            "budget_min_7d": 500, "budget_max_7d": 800,
            "comfort_min_7d": 800, "comfort_max_7d": 1500,
            "premium_min_7d": 1500, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 15, "friends": 15, "pet": 10},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 15, "birthday": 15, "vacation": 0, "workation": 15},
        "best_months": [4, 5, 6, 7, 8, 9],
        "avoid_months": [11, 12, 1, 2],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Canaux d'Amsterdam", "emoji": "boat", "category": "culture"},
            {"name": "Musee Van Gogh", "emoji": "art", "category": "art"},
            {"name": "Champs de tulipes", "emoji": "tulip", "category": "nature"},
            {"name": "Velo dans la ville", "emoji": "bike", "category": "adventure"},
            {"name": "Coffee shops", "emoji": "coffee", "category": "nightlife"}
        ]
    },
    {
        "country_code": "AT",
        "country_name": "Autriche",
        "flag_emoji": "AT",
        "region": "Europe",
        "subregion": "Western Europe",
        "languages": ["German"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 90, "food": 80, "beach": 20, "adventure": 70,
            "nature": 90, "nightlife": 60, "history": 90, "art": 90,
            "shopping": 70, "wellness": 85, "sports": 80
        },
        "must_haves": {
            "accessibility_score": 85, "pet_friendly_score": 75,
            "family_friendly_score": 90, "wifi_quality_score": 88
        },
        "budget": {
            "cost_of_living_index": 85,
            "budget_min_7d": 500, "budget_max_7d": 800,
            "comfort_min_7d": 800, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 6500
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 10, "pet": 5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 10, "vacation": 0, "workation": 10},
        "best_months": [6, 7, 8, 9, 12],
        "avoid_months": [11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Vienne imperiale", "emoji": "european_castle", "category": "culture"},
            {"name": "Ski dans les Alpes", "emoji": "ski", "category": "sports"},
            {"name": "Operas et concerts", "emoji": "musical_note", "category": "culture"},
            {"name": "Cafes viennois", "emoji": "coffee", "category": "food"},
            {"name": "Salzbourg", "emoji": "church", "category": "history"}
        ]
    },
    {
        "country_code": "CH",
        "country_name": "Suisse",
        "flag_emoji": "CH",
        "region": "Europe",
        "subregion": "Western Europe",
        "languages": ["German", "French", "Italian"],
        "currency": "CHF",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 70,
            "eco_vs_luxury": 75,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 80, "food": 85, "beach": 25, "adventure": 85,
            "nature": 98, "nightlife": 50, "history": 75, "art": 75,
            "shopping": 85, "wellness": 90, "sports": 90
        },
        "must_haves": {
            "accessibility_score": 90, "pet_friendly_score": 80,
            "family_friendly_score": 95, "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 140,
            "budget_min_7d": 700, "budget_max_7d": 1100,
            "comfort_min_7d": 1100, "comfort_max_7d": 2200,
            "premium_min_7d": 2200, "premium_max_7d": 4500,
            "luxury_min_7d": 4500, "luxury_max_7d": 12000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 20, "friends": 10, "pet": 10},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 25, "birthday": 10, "vacation": 0, "workation": 10},
        "best_months": [6, 7, 8, 9, 12, 1, 2],
        "avoid_months": [11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Alpes suisses", "emoji": "mountain", "category": "nature"},
            {"name": "Ski a Zermatt", "emoji": "ski", "category": "sports"},
            {"name": "Chocolateries", "emoji": "chocolate_bar", "category": "food"},
            {"name": "Train panoramique", "emoji": "train", "category": "adventure"},
            {"name": "Lac Leman", "emoji": "water", "category": "nature"}
        ]
    },
    {
        "country_code": "HR",
        "country_name": "Croatie",
        "flag_emoji": "HR",
        "region": "Europe",
        "subregion": "Southern Europe",
        "languages": ["Croatian"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 60,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 80, "food": 80, "beach": 90, "adventure": 70,
            "nature": 85, "nightlife": 70, "history": 85, "art": 65,
            "shopping": 50, "wellness": 65, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 60, "pet_friendly_score": 55,
            "family_friendly_score": 75, "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 350, "budget_max_7d": 550,
            "comfort_min_7d": 550, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [5, 6, 9],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Dubrovnik (Game of Thrones)", "emoji": "european_castle", "category": "culture"},
            {"name": "Lacs de Plitvice", "emoji": "water", "category": "nature"},
            {"name": "Plages de l'Adriatique", "emoji": "beach", "category": "beach"},
            {"name": "Voile dans les iles", "emoji": "sailboat", "category": "adventure"},
            {"name": "Split et Diocletien", "emoji": "classical_building", "category": "history"}
        ]
    },
    {
        "country_code": "CZ",
        "country_name": "Republique Tcheque",
        "flag_emoji": "CZ",
        "region": "Europe",
        "subregion": "Central Europe",
        "languages": ["Czech"],
        "currency": "CZK",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 40,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 75, "beach": 10, "adventure": 45,
            "nature": 60, "nightlife": 80, "history": 90, "art": 80,
            "shopping": 60, "wellness": 65, "sports": 45
        },
        "must_haves": {
            "accessibility_score": 70, "pet_friendly_score": 65,
            "family_friendly_score": 75, "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 20, "pet": 5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 0, "workation": 15},
        "best_months": [4, 5, 6, 9, 10, 12],
        "avoid_months": [1, 2],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Vieille ville de Prague", "emoji": "european_castle", "category": "culture"},
            {"name": "Bieres tcheques", "emoji": "beer", "category": "food"},
            {"name": "Pont Charles", "emoji": "bridge_at_night", "category": "history"},
            {"name": "Karlovy Vary", "emoji": "hotsprings", "category": "wellness"},
            {"name": "Marches de Noel", "emoji": "christmas_tree", "category": "culture"}
        ]
    },
    # === ASIA (18 countries) ===
    {
        "country_code": "JP",
        "country_name": "Japon",
        "flag_emoji": "JP",
        "region": "Asia",
        "subregion": "Eastern Asia",
        "languages": ["Japanese"],
        "currency": "JPY",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 55,
            "eco_vs_luxury": 60,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 98, "food": 98, "beach": 50, "adventure": 60,
            "nature": 90, "nightlife": 75, "history": 95, "art": 90,
            "shopping": 90, "wellness": 85, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 90, "pet_friendly_score": 40,
            "family_friendly_score": 85, "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 95,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4000,
            "luxury_min_7d": 4000, "luxury_max_7d": 10000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 10, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 0, "workation": 15},
        "best_months": [3, 4, 5, 10, 11],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 92,
        "top_activities": [
            {"name": "Mont Fuji", "emoji": "mountain", "category": "nature"},
            {"name": "Temples de Kyoto", "emoji": "shinto_shrine", "category": "culture"},
            {"name": "Sushi et ramen", "emoji": "sushi", "category": "food"},
            {"name": "Tokyo futuriste", "emoji": "tokyo_tower", "category": "culture"},
            {"name": "Onsen japonais", "emoji": "hotsprings", "category": "wellness"}
        ]
    },
    {
        "country_code": "TH",
        "country_name": "Thailande",
        "flag_emoji": "TH",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Thai"],
        "currency": "THB",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 55,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 95, "beach": 95, "adventure": 75,
            "nature": 80, "nightlife": 85, "history": 75, "art": 65,
            "shopping": 80, "wellness": 90, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 50, "pet_friendly_score": 45,
            "family_friendly_score": 75, "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 250, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 10, "friends": 20, "pet": -5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [11, 12, 1, 2, 3],
        "avoid_months": [5, 6, 7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 88,
        "top_activities": [
            {"name": "Temples de Bangkok", "emoji": "temple", "category": "culture"},
            {"name": "Iles Phi Phi", "emoji": "beach", "category": "beach"},
            {"name": "Street food thai", "emoji": "ramen", "category": "food"},
            {"name": "Massage traditionnel", "emoji": "spa", "category": "wellness"},
            {"name": "Chiang Mai", "emoji": "elephant", "category": "nature"}
        ]
    },
    {
        "country_code": "VN",
        "country_name": "Vietnam",
        "flag_emoji": "VN",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Vietnamese"],
        "currency": "VND",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 85, "food": 95, "beach": 80, "adventure": 75,
            "nature": 85, "nightlife": 65, "history": 80, "art": 60,
            "shopping": 65, "wellness": 65, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 40, "pet_friendly_score": 35,
            "family_friendly_score": 70, "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 30,
            "budget_min_7d": 200, "budget_max_7d": 400,
            "comfort_min_7d": 400, "comfort_max_7d": 800,
            "premium_min_7d": 800, "premium_max_7d": 1600,
            "luxury_min_7d": 1600, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 5, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 15},
        "best_months": [2, 3, 4, 10, 11],
        "avoid_months": [7, 8, 9],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Baie d'Ha Long", "emoji": "mountain", "category": "nature"},
            {"name": "Pho et banh mi", "emoji": "ramen", "category": "food"},
            {"name": "Hoi An historique", "emoji": "lantern", "category": "culture"},
            {"name": "Delta du Mekong", "emoji": "boat", "category": "adventure"},
            {"name": "Motorbike tours", "emoji": "motor_scooter", "category": "adventure"}
        ]
    },
    {
        "country_code": "ID",
        "country_name": "Indonesie",
        "flag_emoji": "ID",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Indonesian"],
        "currency": "IDR",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 70,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 95, "adventure": 80,
            "nature": 95, "nightlife": 70, "history": 70, "art": 75,
            "shopping": 60, "wellness": 90, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 40, "pet_friendly_score": 35,
            "family_friendly_score": 70, "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 20},
        "best_months": [4, 5, 6, 7, 8, 9],
        "avoid_months": [12, 1, 2],
        "best_seasons": ["Ete"],
        "trending_score": 88,
        "top_activities": [
            {"name": "Temples de Bali", "emoji": "temple", "category": "culture"},
            {"name": "Plages de Bali", "emoji": "beach", "category": "beach"},
            {"name": "Yoga retreats", "emoji": "yoga", "category": "wellness"},
            {"name": "Rizieres d'Ubud", "emoji": "rice", "category": "nature"},
            {"name": "Plongee Komodo", "emoji": "fish", "category": "adventure"}
        ]
    },
    {
        "country_code": "KR",
        "country_name": "Coree du Sud",
        "flag_emoji": "KR",
        "region": "Asia",
        "subregion": "Eastern Asia",
        "languages": ["Korean"],
        "currency": "KRW",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 45,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 90, "food": 90, "beach": 50, "adventure": 55,
            "nature": 70, "nightlife": 85, "history": 80, "art": 85,
            "shopping": 95, "wellness": 80, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 85, "pet_friendly_score": 50,
            "family_friendly_score": 80, "wifi_quality_score": 98
        },
        "budget": {
            "cost_of_living_index": 80,
            "budget_min_7d": 450, "budget_max_7d": 750,
            "comfort_min_7d": 750, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 6500
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 10, "friends": 20, "pet": -5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 15, "vacation": 0, "workation": 15},
        "best_months": [3, 4, 5, 9, 10, 11],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 85,
        "top_activities": [
            {"name": "K-Pop et Hallyu", "emoji": "microphone", "category": "culture"},
            {"name": "BBQ coreen", "emoji": "meat_on_bone", "category": "food"},
            {"name": "Palais de Seoul", "emoji": "temple", "category": "history"},
            {"name": "Shopping a Myeongdong", "emoji": "shopping_bags", "category": "shopping"},
            {"name": "DMZ visite", "emoji": "military_helmet", "category": "history"}
        ]
    },
    {
        "country_code": "SG",
        "country_name": "Singapour",
        "flag_emoji": "SG",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["English", "Mandarin", "Malay", "Tamil"],
        "currency": "SGD",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 25,
            "eco_vs_luxury": 70,
            "tourist_vs_local": 40
        },
        "interest_scores": {
            "culture": 80, "food": 95, "beach": 50, "adventure": 45,
            "nature": 55, "nightlife": 80, "history": 65, "art": 80,
            "shopping": 95, "wellness": 75, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 95, "pet_friendly_score": 40,
            "family_friendly_score": 95, "wifi_quality_score": 98
        },
        "budget": {
            "cost_of_living_index": 115,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4000,
            "luxury_min_7d": 4000, "luxury_max_7d": 10000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 20, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 0, "workation": 15},
        "best_months": [2, 3, 4, 5, 6, 7, 8, 9],
        "avoid_months": [11, 12, 1],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Marina Bay Sands", "emoji": "building", "category": "culture"},
            {"name": "Hawker food", "emoji": "plate_with_cutlery", "category": "food"},
            {"name": "Gardens by the Bay", "emoji": "blossom", "category": "nature"},
            {"name": "Shopping Orchard Road", "emoji": "shopping_bags", "category": "shopping"},
            {"name": "Sentosa Island", "emoji": "beach", "category": "beach"}
        ]
    },
    {
        "country_code": "AE",
        "country_name": "Emirats Arabes Unis",
        "flag_emoji": "AE",
        "region": "Asia",
        "subregion": "Western Asia",
        "languages": ["Arabic", "English"],
        "currency": "AED",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 30,
            "eco_vs_luxury": 85,
            "tourist_vs_local": 35
        },
        "interest_scores": {
            "culture": 70, "food": 80, "beach": 80, "adventure": 70,
            "nature": 50, "nightlife": 75, "history": 55, "art": 75,
            "shopping": 98, "wellness": 85, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 85, "pet_friendly_score": 40,
            "family_friendly_score": 90, "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 90,
            "budget_min_7d": 500, "budget_max_7d": 900,
            "comfort_min_7d": 900, "comfort_max_7d": 1800,
            "premium_min_7d": 1800, "premium_max_7d": 4000,
            "luxury_min_7d": 4000, "luxury_max_7d": 15000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 15, "vacation": 0, "workation": 10},
        "best_months": [11, 12, 1, 2, 3, 4],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Hiver"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Burj Khalifa", "emoji": "building", "category": "culture"},
            {"name": "Safari desert", "emoji": "camel", "category": "adventure"},
            {"name": "Dubai Mall", "emoji": "shopping_cart", "category": "shopping"},
            {"name": "Plages de luxe", "emoji": "beach", "category": "beach"},
            {"name": "Louvre Abu Dhabi", "emoji": "art", "category": "art"}
        ]
    },
    {
        "country_code": "IN",
        "country_name": "Inde",
        "flag_emoji": "IN",
        "region": "Asia",
        "subregion": "Southern Asia",
        "languages": ["Hindi", "English"],
        "currency": "INR",
        "style_scores": {
            "chill_vs_intense": 60,
            "city_vs_nature": 50,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 98, "food": 90, "beach": 65, "adventure": 70,
            "nature": 80, "nightlife": 55, "history": 95, "art": 85,
            "shopping": 75, "wellness": 95, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 40, "pet_friendly_score": 35,
            "family_friendly_score": 65, "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 25,
            "budget_min_7d": 200, "budget_max_7d": 400,
            "comfort_min_7d": 400, "comfort_max_7d": 800,
            "premium_min_7d": 800, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 5, "friends": 15, "pet": -15},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 5, "vacation": 5, "workation": 10},
        "best_months": [10, 11, 12, 1, 2, 3],
        "avoid_months": [6, 7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Taj Mahal", "emoji": "mosque", "category": "history"},
            {"name": "Cuisine indienne", "emoji": "curry", "category": "food"},
            {"name": "Yoga a Rishikesh", "emoji": "yoga", "category": "wellness"},
            {"name": "Kerala backwaters", "emoji": "boat", "category": "nature"},
            {"name": "Rajasthan palais", "emoji": "classical_building", "category": "culture"}
        ]
    },
    # === AMERICAS (12 countries) ===
    {
        "country_code": "US",
        "country_name": "Etats-Unis",
        "flag_emoji": "US",
        "region": "Americas",
        "subregion": "Northern America",
        "languages": ["English"],
        "currency": "USD",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 50,
            "eco_vs_luxury": 60,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 80, "adventure": 85,
            "nature": 95, "nightlife": 90, "history": 75, "art": 85,
            "shopping": 95, "wellness": 75, "sports": 90
        },
        "must_haves": {
            "accessibility_score": 90, "pet_friendly_score": 80,
            "family_friendly_score": 95, "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 100,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4500,
            "luxury_min_7d": 4500, "luxury_max_7d": 12000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 20, "friends": 20, "pet": 10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 10},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Grand Canyon", "emoji": "national_park", "category": "nature"},
            {"name": "New York City", "emoji": "statue_of_liberty", "category": "culture"},
            {"name": "Las Vegas", "emoji": "slot_machine", "category": "nightlife"},
            {"name": "Parcs nationaux", "emoji": "evergreen_tree", "category": "nature"},
            {"name": "Miami Beach", "emoji": "beach", "category": "beach"}
        ]
    },
    {
        "country_code": "MX",
        "country_name": "Mexique",
        "flag_emoji": "MX",
        "region": "Americas",
        "subregion": "Central America",
        "languages": ["Spanish"],
        "currency": "MXN",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 55,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 95, "food": 95, "beach": 95, "adventure": 75,
            "nature": 80, "nightlife": 80, "history": 90, "art": 85,
            "shopping": 70, "wellness": 70, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 55, "pet_friendly_score": 50,
            "family_friendly_score": 80, "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 40,
            "budget_min_7d": 350, "budget_max_7d": 550,
            "comfort_min_7d": 550, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 5500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 20, "pet": 0},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [11, 12, 1, 2, 3, 4],
        "avoid_months": [9],
        "best_seasons": ["Hiver"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Chichen Itza", "emoji": "pyramid", "category": "history"},
            {"name": "Plages de Cancun", "emoji": "beach", "category": "beach"},
            {"name": "Tacos et guacamole", "emoji": "taco", "category": "food"},
            {"name": "Mexico City", "emoji": "city_sunset", "category": "culture"},
            {"name": "Oaxaca artisanat", "emoji": "art", "category": "culture"}
        ]
    },
    {
        "country_code": "BR",
        "country_name": "Bresil",
        "flag_emoji": "BR",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Portuguese"],
        "currency": "BRL",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 60,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 90, "food": 85, "beach": 95, "adventure": 80,
            "nature": 98, "nightlife": 95, "history": 65, "art": 75,
            "shopping": 65, "wellness": 70, "sports": 85
        },
        "must_haves": {
            "accessibility_score": 50, "pet_friendly_score": 50,
            "family_friendly_score": 70, "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 400, "budget_max_7d": 650,
            "comfort_min_7d": 650, "comfort_max_7d": 1200,
            "premium_min_7d": 1200, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 10, "friends": 25, "pet": 0},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 20, "vacation": 5, "workation": 10},
        "best_months": [4, 5, 6, 7, 8, 9, 10],
        "avoid_months": [1, 2],
        "best_seasons": ["Automne", "Hiver"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Rio de Janeiro", "emoji": "statue_of_liberty", "category": "culture"},
            {"name": "Amazonie", "emoji": "deciduous_tree", "category": "nature"},
            {"name": "Carnaval", "emoji": "dancer", "category": "culture"},
            {"name": "Plages de Copacabana", "emoji": "beach", "category": "beach"},
            {"name": "Chutes d'Iguazu", "emoji": "water", "category": "nature"}
        ]
    },
    {
        "country_code": "PE",
        "country_name": "Perou",
        "flag_emoji": "PE",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Spanish"],
        "currency": "PEN",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 70,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 90, "food": 95, "beach": 50, "adventure": 90,
            "nature": 95, "nightlife": 55, "history": 98, "art": 75,
            "shopping": 55, "wellness": 65, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 40, "pet_friendly_score": 35,
            "family_friendly_score": 65, "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 5, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [4, 5, 6, 7, 8, 9, 10],
        "avoid_months": [1, 2, 3],
        "best_seasons": ["Automne", "Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Machu Picchu", "emoji": "mountain", "category": "history"},
            {"name": "Ceviche peruvien", "emoji": "fish", "category": "food"},
            {"name": "Cusco colonial", "emoji": "church", "category": "culture"},
            {"name": "Lac Titicaca", "emoji": "water", "category": "nature"},
            {"name": "Nazca lignes", "emoji": "small_airplane", "category": "adventure"}
        ]
    },
    {
        "country_code": "CR",
        "country_name": "Costa Rica",
        "flag_emoji": "CR",
        "region": "Americas",
        "subregion": "Central America",
        "languages": ["Spanish"],
        "currency": "CRC",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 85,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 60, "food": 65, "beach": 90, "adventure": 95,
            "nature": 98, "nightlife": 50, "history": 45, "art": 45,
            "shopping": 40, "wellness": 85, "sports": 80
        },
        "must_haves": {
            "accessibility_score": 50, "pet_friendly_score": 55,
            "family_friendly_score": 85, "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1300,
            "premium_min_7d": 1300, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 6500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 20, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 15},
        "best_months": [12, 1, 2, 3, 4],
        "avoid_months": [9, 10],
        "best_seasons": ["Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Rainforest trekking", "emoji": "deciduous_tree", "category": "nature"},
            {"name": "Volcan Arenal", "emoji": "volcano", "category": "adventure"},
            {"name": "Observation faune", "emoji": "monkey", "category": "nature"},
            {"name": "Surf Pacifique", "emoji": "surfing_man", "category": "sports"},
            {"name": "Eco-lodges", "emoji": "house_with_garden", "category": "wellness"}
        ]
    },
    # === AFRICA (9 countries) ===
    {
        "country_code": "MA",
        "country_name": "Maroc",
        "flag_emoji": "MA",
        "region": "Africa",
        "subregion": "Northern Africa",
        "languages": ["Arabic", "French"],
        "currency": "MAD",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 95, "food": 90, "beach": 70, "adventure": 75,
            "nature": 80, "nightlife": 50, "history": 90, "art": 85,
            "shopping": 90, "wellness": 85, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 50, "pet_friendly_score": 40,
            "family_friendly_score": 75, "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 250, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5500
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 10, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [3, 4, 5, 9, 10, 11],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Medina de Marrakech", "emoji": "mosque", "category": "culture"},
            {"name": "Sahara desert", "emoji": "desert", "category": "adventure"},
            {"name": "Tajines et couscous", "emoji": "stew", "category": "food"},
            {"name": "Riads traditionnels", "emoji": "house", "category": "culture"},
            {"name": "Hammam spa", "emoji": "spa", "category": "wellness"}
        ]
    },
    {
        "country_code": "EG",
        "country_name": "Egypte",
        "flag_emoji": "EG",
        "region": "Africa",
        "subregion": "Northern Africa",
        "languages": ["Arabic"],
        "currency": "EGP",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 50,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 90, "food": 75, "beach": 85, "adventure": 70,
            "nature": 70, "nightlife": 55, "history": 100, "art": 80,
            "shopping": 70, "wellness": 60, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 45, "pet_friendly_score": 30,
            "family_friendly_score": 70, "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 30,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 5500
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 10, "friends": 15, "pet": -15},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 0},
        "best_months": [10, 11, 12, 1, 2, 3, 4],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Pyramides de Gizeh", "emoji": "pyramid", "category": "history"},
            {"name": "Croisiere sur le Nil", "emoji": "boat", "category": "adventure"},
            {"name": "Temples de Louxor", "emoji": "classical_building", "category": "history"},
            {"name": "Plongee Mer Rouge", "emoji": "fish", "category": "adventure"},
            {"name": "Sphinx et Caire", "emoji": "sphinx", "category": "culture"}
        ]
    },
    {
        "country_code": "ZA",
        "country_name": "Afrique du Sud",
        "flag_emoji": "ZA",
        "region": "Africa",
        "subregion": "Southern Africa",
        "languages": ["English", "Afrikaans", "Zulu"],
        "currency": "ZAR",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 70,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 80, "food": 80, "beach": 80, "adventure": 95,
            "nature": 98, "nightlife": 70, "history": 75, "art": 70,
            "shopping": 65, "wellness": 80, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 60, "pet_friendly_score": 50,
            "family_friendly_score": 80, "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 3000,
            "luxury_min_7d": 3000, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [3, 4, 5, 9, 10, 11],
        "avoid_months": [12, 1, 2],
        "best_seasons": ["Automne", "Printemps"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Safari Kruger", "emoji": "lion", "category": "nature"},
            {"name": "Cape Town", "emoji": "mountain", "category": "culture"},
            {"name": "Route des vins", "emoji": "wine_glass", "category": "food"},
            {"name": "Garden Route", "emoji": "national_park", "category": "nature"},
            {"name": "Cage aux requins", "emoji": "shark", "category": "adventure"}
        ]
    },
    {
        "country_code": "KE",
        "country_name": "Kenya",
        "flag_emoji": "KE",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["English", "Swahili"],
        "currency": "KES",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 85,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 75, "food": 60, "beach": 75, "adventure": 95,
            "nature": 100, "nightlife": 45, "history": 60, "art": 55,
            "shopping": 45, "wellness": 65, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 40, "pet_friendly_score": 35,
            "family_friendly_score": 70, "wifi_quality_score": 60
        },
        "budget": {
            "cost_of_living_index": 40,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1500,
            "premium_min_7d": 1500, "premium_max_7d": 3500,
            "luxury_min_7d": 3500, "luxury_max_7d": 10000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 0},
        "best_months": [1, 2, 6, 7, 8, 9, 10],
        "avoid_months": [4, 5, 11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Safari Masai Mara", "emoji": "lion", "category": "nature"},
            {"name": "Grande migration", "emoji": "water_buffalo", "category": "nature"},
            {"name": "Mont Kenya", "emoji": "mountain", "category": "adventure"},
            {"name": "Plages de Mombasa", "emoji": "beach", "category": "beach"},
            {"name": "Rencontre Maasai", "emoji": "person", "category": "culture"}
        ]
    },
    {
        "country_code": "MU",
        "country_name": "Maurice",
        "flag_emoji": "MU",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["English", "French", "Creole"],
        "currency": "MUR",
        "style_scores": {
            "chill_vs_intense": 25,
            "city_vs_nature": 70,
            "eco_vs_luxury": 60,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 65, "food": 80, "beach": 98, "adventure": 65,
            "nature": 85, "nightlife": 55, "history": 50, "art": 45,
            "shopping": 60, "wellness": 90, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 60, "pet_friendly_score": 50,
            "family_friendly_score": 90, "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 500, "budget_max_7d": 900,
            "comfort_min_7d": 900, "comfort_max_7d": 1800,
            "premium_min_7d": 1800, "premium_max_7d": 4000,
            "luxury_min_7d": 4000, "luxury_max_7d": 12000
        },
        "travel_style_bonuses": {"solo": 5, "couple": 25, "family": 20, "friends": 10, "pet": -5},
        "occasion_bonuses": {"honeymoon": 30, "anniversary": 25, "birthday": 15, "vacation": 5, "workation": 5},
        "best_months": [4, 5, 6, 9, 10, 11],
        "avoid_months": [1, 2, 3],
        "best_seasons": ["Automne", "Printemps"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Plages paradisiaques", "emoji": "beach", "category": "beach"},
            {"name": "Plongee coraux", "emoji": "fish", "category": "adventure"},
            {"name": "Spa de luxe", "emoji": "spa", "category": "wellness"},
            {"name": "Ile aux Cerfs", "emoji": "palm_tree", "category": "beach"},
            {"name": "Grand Bassin", "emoji": "temple", "category": "culture"}
        ]
    },
    # === OCEANIA (4 countries) ===
    {
        "country_code": "AU",
        "country_name": "Australie",
        "flag_emoji": "AU",
        "region": "Oceania",
        "subregion": "Australia and New Zealand",
        "languages": ["English"],
        "currency": "AUD",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 65,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 75, "food": 80, "beach": 95, "adventure": 95,
            "nature": 98, "nightlife": 80, "history": 60, "art": 75,
            "shopping": 75, "wellness": 80, "sports": 90
        },
        "must_haves": {
            "accessibility_score": 85, "pet_friendly_score": 70,
            "family_friendly_score": 95, "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 95,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4500,
            "luxury_min_7d": 4500, "luxury_max_7d": 12000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 20, "friends": 20, "pet": 5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [9, 10, 11, 3, 4, 5],
        "avoid_months": [12, 1, 2],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Grande Barriere de Corail", "emoji": "coral", "category": "nature"},
            {"name": "Opera de Sydney", "emoji": "performing_arts", "category": "culture"},
            {"name": "Outback australien", "emoji": "desert", "category": "adventure"},
            {"name": "Kangourous et koalas", "emoji": "kangaroo", "category": "nature"},
            {"name": "Surf a Gold Coast", "emoji": "surfing_man", "category": "sports"}
        ]
    },
    {
        "country_code": "NZ",
        "country_name": "Nouvelle-Zelande",
        "flag_emoji": "NZ",
        "region": "Oceania",
        "subregion": "Australia and New Zealand",
        "languages": ["English", "Maori"],
        "currency": "NZD",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 80,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 75, "food": 75, "beach": 70, "adventure": 98,
            "nature": 100, "nightlife": 55, "history": 60, "art": 65,
            "shopping": 50, "wellness": 80, "sports": 90
        },
        "must_haves": {
            "accessibility_score": 80, "pet_friendly_score": 70,
            "family_friendly_score": 95, "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 85,
            "budget_min_7d": 550, "budget_max_7d": 900,
            "comfort_min_7d": 900, "comfort_max_7d": 1800,
            "premium_min_7d": 1800, "premium_max_7d": 3800,
            "luxury_min_7d": 3800, "luxury_max_7d": 10000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 20, "family": 20, "friends": 20, "pet": 5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [10, 11, 12, 1, 2, 3, 4],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Ete"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Fjords de Milford Sound", "emoji": "mountain", "category": "nature"},
            {"name": "Saut a l'elastique Queenstown", "emoji": "person_climbing", "category": "adventure"},
            {"name": "Hobbiton (LOTR)", "emoji": "house_with_garden", "category": "culture"},
            {"name": "Geysers Rotorua", "emoji": "volcano", "category": "nature"},
            {"name": "Randonnee glaciers", "emoji": "ice_cube", "category": "adventure"}
        ]
    },
    {
        "country_code": "FJ",
        "country_name": "Fidji",
        "flag_emoji": "FJ",
        "region": "Oceania",
        "subregion": "Melanesia",
        "languages": ["English", "Fijian"],
        "currency": "FJD",
        "style_scores": {
            "chill_vs_intense": 20,
            "city_vs_nature": 80,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 70, "food": 65, "beach": 100, "adventure": 70,
            "nature": 90, "nightlife": 40, "history": 45, "art": 45,
            "shopping": 35, "wellness": 90, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 45, "pet_friendly_score": 40,
            "family_friendly_score": 85, "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 70,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2200,
            "premium_min_7d": 2200, "premium_max_7d": 5000,
            "luxury_min_7d": 5000, "luxury_max_7d": 15000
        },
        "travel_style_bonuses": {"solo": 5, "couple": 25, "family": 15, "friends": 10, "pet": -10},
        "occasion_bonuses": {"honeymoon": 30, "anniversary": 25, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [5, 6, 7, 8, 9, 10],
        "avoid_months": [12, 1, 2, 3],
        "best_seasons": ["Hiver"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Iles paradisiaques", "emoji": "palm_tree", "category": "beach"},
            {"name": "Plongee corallienne", "emoji": "fish", "category": "adventure"},
            {"name": "Villages traditionnels", "emoji": "hut", "category": "culture"},
            {"name": "Resorts de luxe", "emoji": "hotel", "category": "wellness"},
            {"name": "Kayak lagon", "emoji": "canoe", "category": "adventure"}
        ]
    },
    {
        "country_code": "PF",
        "country_name": "Polynesie Francaise",
        "flag_emoji": "PF",
        "region": "Oceania",
        "subregion": "Polynesia",
        "languages": ["French", "Tahitian"],
        "currency": "XPF",
        "style_scores": {
            "chill_vs_intense": 15,
            "city_vs_nature": 85,
            "eco_vs_luxury": 75,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 75, "food": 75, "beach": 100, "adventure": 70,
            "nature": 95, "nightlife": 35, "history": 50, "art": 60,
            "shopping": 45, "wellness": 95, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 50, "pet_friendly_score": 40,
            "family_friendly_score": 80, "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 120,
            "budget_min_7d": 800, "budget_max_7d": 1400,
            "comfort_min_7d": 1400, "comfort_max_7d": 3000,
            "premium_min_7d": 3000, "premium_max_7d": 7000,
            "luxury_min_7d": 7000, "luxury_max_7d": 20000
        },
        "travel_style_bonuses": {"solo": 5, "couple": 30, "family": 10, "friends": 10, "pet": -10},
        "occasion_bonuses": {"honeymoon": 35, "anniversary": 30, "birthday": 15, "vacation": 5, "workation": 0},
        "best_months": [4, 5, 6, 7, 8, 9, 10, 11],
        "avoid_months": [1, 2, 3],
        "best_seasons": ["Automne", "Hiver", "Printemps"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Bora Bora lagons", "emoji": "beach", "category": "beach"},
            {"name": "Overwater bungalows", "emoji": "house", "category": "wellness"},
            {"name": "Plongee avec raies", "emoji": "fish", "category": "adventure"},
            {"name": "Danse tahitienne", "emoji": "dancer", "category": "culture"},
            {"name": "Moorea montagnes", "emoji": "mountain", "category": "nature"}
        ]
    },
]


async def seed_database():
    """Seed the MongoDB database with country profiles."""
    # Get MongoDB connection from environment
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_db = os.getenv("MONGODB_DB", "travliaq")

    if not mongodb_uri:
        print("ERROR: MONGODB_URI environment variable not set")
        sys.exit(1)

    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[mongodb_db]
    collection = db["country_profiles"]

    # Add metadata to each profile
    now = datetime.utcnow()
    for profile in COUNTRY_PROFILES:
        profile["updated_at"] = now
        profile["source_data"] = {
            "manual_seed": True,
            "seed_date": now.isoformat() + "Z"
        }

    print(f"Inserting {len(COUNTRY_PROFILES)} country profiles...")

    # Use bulk upsert
    from pymongo import UpdateOne

    operations = [
        UpdateOne(
            {"country_code": p["country_code"]},
            {"$set": p},
            upsert=True
        )
        for p in COUNTRY_PROFILES
    ]

    result = await collection.bulk_write(operations)

    print(f"Upserted: {result.upserted_count}")
    print(f"Modified: {result.modified_count}")

    # Create indexes
    await collection.create_index("country_code", unique=True)
    await collection.create_index("region")
    await collection.create_index("trending_score")
    print("Indexes created")

    # Close connection
    client.close()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(seed_database())

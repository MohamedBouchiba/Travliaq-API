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
            {"name": "Tour Eiffel", "emoji": "🗼", "category": "landmark"},
            {"name": "Degustation de vins", "emoji": "🍷", "category": "food"},
            {"name": "Chateaux de la Loire", "emoji": "🏰", "category": "history"},
            {"name": "Cote d'Azur", "emoji": "🏖️", "category": "beach"},
            {"name": "Mont Saint-Michel", "emoji": "🏔️", "category": "landmark"}
        ],
        "fallback_headlines": {
            "solo": "France, l'art de vivre en solo",
            "couple": "Paris romantique et terroirs francais",
            "family": "La France en famille, histoire et saveurs",
            "friends": "France entre amis, vins et culture",
            "pet": "France avec votre compagnon"
        },
        "fallback_description": "Gastronomie, patrimoine et art de vivre a la francaise."
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
        ],
        "fallback_headlines": {
            "solo": "Espagne, soleil et tapas en solo",
            "couple": "Romantisme espagnol, flamenco et plages",
            "family": "Espagne en famille, plages et fiestas",
            "friends": "Espagne entre amis, tapas et nightlife",
            "pet": "Espagne avec votre compagnon"
        },
        "fallback_description": "Tapas, flamenco, plages paradisiaques et art de vivre mediterraneen."
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
        ],
        "fallback_headlines": {
            "solo": "Italie, dolce vita en solo",
            "couple": "Romance italienne, Venise et Toscane",
            "family": "Italie en famille, histoire et pizza",
            "friends": "Italie entre amis, vins et dolce vita",
            "pet": "Italie avec votre compagnon"
        },
        "fallback_description": "Art, gastronomie et romantisme a l'italienne."
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
        ],
        "fallback_headlines": {
            "solo": "Portugal, saudade et liberte en solo",
            "couple": "Portugal romantique, Porto et Lisbonne",
            "family": "Portugal en famille, plages et pasteis",
            "friends": "Portugal entre amis, surf et nightlife",
            "pet": "Portugal avec votre compagnon"
        },
        "fallback_description": "Pasteis de nata, fado et plages dorees de l'Atlantique."
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
        ],
        "fallback_headlines": {
            "solo": "Grece, odyssee en solo",
            "couple": "Iles grecques romantiques, Santorin",
            "family": "Grece en famille, mythes et plages",
            "friends": "Grece entre amis, Mykonos et histoire",
            "pet": "Grece avec votre compagnon"
        },
        "fallback_description": "Iles paradisiaques, histoire antique et meze au soleil."
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
        ],
        "fallback_headlines": {
            "solo": "Allemagne, culture et techno en solo",
            "couple": "Allemagne romantique, chateaux et bieres",
            "family": "Allemagne en famille, contes et nature",
            "friends": "Allemagne entre amis, Berlin et Munich",
            "pet": "Allemagne avec votre compagnon"
        },
        "fallback_description": "Chateaux feeriques, biergartens et scene culturelle vibrante."
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
        ],
        "fallback_headlines": {
            "solo": "Royaume-Uni, Londres et pubs en solo",
            "couple": "UK romantique, Londres et Ecosse",
            "family": "Royaume-Uni en famille, Harry Potter",
            "friends": "UK entre amis, pubs et football",
            "pet": "UK avec votre compagnon"
        },
        "fallback_description": "Pubs historiques, musees gratuits et Highlands sauvages."
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
        ],
        "fallback_headlines": {
            "solo": "Pays-Bas, velo et liberte en solo",
            "couple": "Amsterdam romantique, canaux et art",
            "family": "Pays-Bas en famille, tulipes et moulins",
            "friends": "Pays-Bas entre amis, nightlife libre",
            "pet": "Pays-Bas avec votre compagnon"
        },
        "fallback_description": "Canaux pittoresques, maitres flamands et ambiance libre."
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
        ],
        "fallback_headlines": {
            "solo": "Autriche, musique et ski en solo",
            "couple": "Vienne romantique, valses et cafes",
            "family": "Autriche en famille, Sound of Music",
            "friends": "Autriche entre amis, ski et apres-ski",
            "pet": "Autriche avec votre compagnon"
        },
        "fallback_description": "Palais imperiaux, concerts classiques et Alpes majestueuses."
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
        ],
        "fallback_headlines": {
            "solo": "Suisse, montagnes et liberte en solo",
            "couple": "Suisse romantique, lacs et neige",
            "family": "Suisse en famille, nature et chocolat",
            "friends": "Suisse entre amis, ski et fondue",
            "pet": "Suisse avec votre compagnon"
        },
        "fallback_description": "Sommets alpins, trains panoramiques et chocolat artisanal."
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
        ],
        "fallback_headlines": {
            "solo": "Croatie, Adriatique en solo",
            "couple": "Croatie romantique, Dubrovnik et iles",
            "family": "Croatie en famille, plages et nature",
            "friends": "Croatie entre amis, voile et fiestas",
            "pet": "Croatie avec votre compagnon"
        },
        "fallback_description": "Cote adriatique spectaculaire, villes medievales et parcs naturels."
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
        ],
        "fallback_headlines": {
            "solo": "Prague, bieres et histoire en solo",
            "couple": "Prague romantique, ponts et chateaux",
            "family": "Republique Tcheque en famille",
            "friends": "Prague entre amis, bieres et nightlife",
            "pet": "Prague avec votre compagnon"
        },
        "fallback_description": "Prague magique, bieres artisanales et architecture gothique."
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
        ],
        "fallback_headlines": {
            "solo": "Japon, zen et modernite en solo",
            "couple": "Japon romantique, cerisiers et ryokans",
            "family": "Japon en famille, traditions et tech",
            "friends": "Japon entre amis, Tokyo et Kyoto",
            "pet": "Japon avec votre compagnon"
        },
        "fallback_description": "Traditions millenaires, gastronomie raffinee et technologie futuriste."
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
        ],
        "fallback_headlines": {
            "solo": "Thailande, plages et temples en solo",
            "couple": "Thailande romantique, iles paradisiaques",
            "family": "Thailande en famille, plages et elephants",
            "friends": "Thailande entre amis, full moon party",
            "pet": "Thailande avec votre compagnon"
        },
        "fallback_description": "Plages de reve, temples dores et street food legendaire."
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
        ],
        "fallback_headlines": {
            "solo": "Vietnam, aventure solo authentique",
            "couple": "Vietnam romantique, Ha Long et Hoi An",
            "family": "Vietnam en famille, culture et nature",
            "friends": "Vietnam entre amis, road trip moto",
            "pet": "Vietnam avec votre compagnon"
        },
        "fallback_description": "Baie d'Ha Long, street food incroyable et authenticite preservee."
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
        ],
        "fallback_headlines": {
            "solo": "Indonesie, Bali et zen en solo",
            "couple": "Bali romantique, temples et rizieres",
            "family": "Indonesie en famille, plages et nature",
            "friends": "Bali entre amis, surf et fetes",
            "pet": "Indonesie avec votre compagnon"
        },
        "fallback_description": "Temples mystiques, plages de sable fin et wellness a Ubud."
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
        ],
        "fallback_headlines": {
            "solo": "Coree du Sud, K-culture en solo",
            "couple": "Seoul romantique, tradition et modernite",
            "family": "Coree en famille, technologie et palais",
            "friends": "Seoul entre amis, K-pop et nightlife",
            "pet": "Coree avec votre compagnon"
        },
        "fallback_description": "K-pop, barbecue coreen et palais royaux a Seoul."
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
        ],
        "fallback_headlines": {
            "solo": "Singapour, futurisme en solo",
            "couple": "Singapour romantique, gardens et skyline",
            "family": "Singapour en famille, attractions uniques",
            "friends": "Singapour entre amis, food et rooftops",
            "pet": "Singapour avec votre compagnon"
        },
        "fallback_description": "Cite-etat futuriste, hawker food legendaire et jardins spectaculaires."
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
        ],
        "fallback_headlines": {
            "solo": "Dubai, luxe et desert en solo",
            "couple": "Dubai romantique, skyline et plages",
            "family": "Dubai en famille, parcs et attractions",
            "friends": "Dubai entre amis, shopping et brunch",
            "pet": "Emirats avec votre compagnon"
        },
        "fallback_description": "Luxe absolu, gratte-ciels vertigineux et experiences desert."
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
        ],
        "fallback_headlines": {
            "solo": "Inde, eveil spirituel en solo",
            "couple": "Inde romantique, Taj Mahal et palais",
            "family": "Inde en famille, couleurs et traditions",
            "friends": "Inde entre amis, aventure et curry",
            "pet": "Inde avec votre compagnon"
        },
        "fallback_description": "Spiritualite, palais somptueux et cuisine aux mille saveurs."
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
        ],
        "fallback_headlines": {
            "solo": "USA, road trip solo mythique",
            "couple": "USA romantique, NYC et Californie",
            "family": "USA en famille, parcs et Disney",
            "friends": "USA entre amis, Vegas et roadtrip",
            "pet": "USA avec votre compagnon"
        },
        "fallback_description": "Road trips epiques, parcs nationaux grandioses et villes iconiques."
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
        ],
        "fallback_headlines": {
            "solo": "Mexique, tacos et pyramides en solo",
            "couple": "Mexique romantique, plages et ruines",
            "family": "Mexique en famille, Cancun et culture",
            "friends": "Mexique entre amis, fiestas et plages",
            "pet": "Mexique avec votre compagnon"
        },
        "fallback_description": "Pyramides mayas, plages caribbeennes et gastronomie explosive."
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
        ],
        "fallback_headlines": {
            "solo": "Bresil, samba et aventure en solo",
            "couple": "Bresil romantique, Rio et plages",
            "family": "Bresil en famille, nature et culture",
            "friends": "Bresil entre amis, carnaval et fetes",
            "pet": "Bresil avec votre compagnon"
        },
        "fallback_description": "Carnaval de Rio, plages mythiques et nature amazonienne."
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
        ],
        "fallback_headlines": {
            "solo": "Perou, Incas et aventure en solo",
            "couple": "Perou romantique, Machu Picchu",
            "family": "Perou en famille, histoire vivante",
            "friends": "Perou entre amis, trek et ceviche",
            "pet": "Perou avec votre compagnon"
        },
        "fallback_description": "Machu Picchu legendaire, ceviche frais et tresors incas."
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
        ],
        "fallback_headlines": {
            "solo": "Costa Rica, pura vida en solo",
            "couple": "Costa Rica romantique, jungle et plages",
            "family": "Costa Rica en famille, nature vivante",
            "friends": "Costa Rica entre amis, surf et volcans",
            "pet": "Costa Rica avec votre compagnon"
        },
        "fallback_description": "Biodiversite exceptionnelle, volcans et plages des deux oceans."
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
        ],
        "fallback_headlines": {
            "solo": "Maroc, medinas et desert en solo",
            "couple": "Maroc romantique, riads et couchers soleil",
            "family": "Maroc en famille, souks et aventure",
            "friends": "Maroc entre amis, desert et tajines",
            "pet": "Maroc avec votre compagnon"
        },
        "fallback_description": "Medinas envoûtantes, dunes sahariennes et hospitalite marocaine."
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
        ],
        "fallback_headlines": {
            "solo": "Egypte, pharaons et Nil en solo",
            "couple": "Egypte romantique, croisiere sur le Nil",
            "family": "Egypte en famille, pyramides et mysteres",
            "friends": "Egypte entre amis, histoire et plongee",
            "pet": "Egypte avec votre compagnon"
        },
        "fallback_description": "Pyramides millenaires, croisiere sur le Nil et tresors pharaoniques."
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
        ],
        "fallback_headlines": {
            "solo": "Afrique du Sud, safari solo epique",
            "couple": "Afrique du Sud romantique, vins et safari",
            "family": "Afrique du Sud en famille, Big Five",
            "friends": "Afrique du Sud entre amis, aventure",
            "pet": "Afrique du Sud avec votre compagnon"
        },
        "fallback_description": "Safaris Big Five, vignobles et Table Mountain."
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
        ],
        "fallback_headlines": {
            "solo": "Kenya, safari solo inoubliable",
            "couple": "Kenya romantique, safari et plages",
            "family": "Kenya en famille, Big Five et savane",
            "friends": "Kenya entre amis, aventure sauvage",
            "pet": "Kenya avec votre compagnon"
        },
        "fallback_description": "Grande migration, Big Five et rencontres Maasai authentiques."
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
        ],
        "fallback_headlines": {
            "solo": "Maurice, paradis relaxant en solo",
            "couple": "Maurice romantique, lune de miel parfaite",
            "family": "Maurice en famille, plages et lagons",
            "friends": "Maurice entre amis, plongee et farniente",
            "pet": "Maurice avec votre compagnon"
        },
        "fallback_description": "Lagons turquoise, spas de luxe et cuisine creole."
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
        ],
        "fallback_headlines": {
            "solo": "Australie, road trip solo legendaire",
            "couple": "Australie romantique, recifs et outback",
            "family": "Australie en famille, nature unique",
            "friends": "Australie entre amis, surf et aventure",
            "pet": "Australie avec votre compagnon"
        },
        "fallback_description": "Grande Barriere de Corail, outback rouge et faune unique."
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
        ],
        "fallback_headlines": {
            "solo": "Nouvelle-Zelande, aventure solo extreme",
            "couple": "NZ romantique, fjords et paysages epiques",
            "family": "Nouvelle-Zelande en famille, Hobbiton",
            "friends": "NZ entre amis, adrealine et nature",
            "pet": "Nouvelle-Zelande avec votre compagnon"
        },
        "fallback_description": "Paysages du Seigneur des Anneaux, sports extremes et fjords."
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
        ],
        "fallback_headlines": {
            "solo": "Fidji, iles de reve en solo",
            "couple": "Fidji romantique, lune de miel idyllique",
            "family": "Fidji en famille, plages et culture",
            "friends": "Fidji entre amis, plongee et detente",
            "pet": "Fidji avec votre compagnon"
        },
        "fallback_description": "Archipel paradisiaque, plongee corallienne et hospitalite fidjienne."
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
        ],
        "fallback_headlines": {
            "solo": "Polynesie, paradis du voyageur solo",
            "couple": "Bora Bora, lune de miel de reve",
            "family": "Tahiti en famille, magie du Pacifique",
            "friends": "Aventure entre amis en Polynesie",
            "pet": "Polynesie avec votre compagnon"
        },
        "fallback_description": "Lagons turquoise, bungalows sur pilotis et culture polynesienne authentique."
    },

    # === NEW COUNTRIES (16 additions to reach 50) ===

    # Europe additions
    {
        "country_code": "TR",
        "country_name": "Turquie",
        "flag_emoji": "TR",
        "region": "Europe",
        "subregion": "Western Asia",
        "languages": ["Turkish"],
        "currency": "TRY",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 50,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 95, "food": 90, "beach": 85, "adventure": 70,
            "nature": 80, "nightlife": 75, "history": 95, "art": 80,
            "shopping": 90, "wellness": 85, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 60, "pet_friendly_score": 50,
            "family_friendly_score": 80, "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 250, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 15, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 88,
        "top_activities": [
            {"name": "Cappadoce en montgolfiere", "emoji": "balloon", "category": "adventure"},
            {"name": "Sainte-Sophie Istanbul", "emoji": "mosque", "category": "history"},
            {"name": "Bains turcs", "emoji": "hot_springs", "category": "wellness"},
            {"name": "Ephese ruines", "emoji": "classical_building", "category": "history"},
            {"name": "Plages d'Antalya", "emoji": "beach", "category": "beach"}
        ],
        "fallback_headlines": {
            "solo": "Turquie, carrefour des civilisations",
            "couple": "Istanbul romantique et plages turquoises",
            "family": "Turquie en famille, histoire et plages",
            "friends": "Cappadoce et Istanbul entre amis",
            "pet": "Turquie avec votre compagnon"
        },
        "fallback_description": "Merveilles historiques, cuisine delicieuse et plages mediterraneennes."
    },
    {
        "country_code": "PL",
        "country_name": "Pologne",
        "flag_emoji": "PL",
        "region": "Europe",
        "subregion": "Eastern Europe",
        "languages": ["Polish"],
        "currency": "PLN",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 55,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 40, "adventure": 55,
            "nature": 70, "nightlife": 80, "history": 95, "art": 80,
            "shopping": 70, "wellness": 60, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 70, "pet_friendly_score": 60,
            "family_friendly_score": 75, "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 10, "family": 10, "friends": 20, "pet": 5},
        "occasion_bonuses": {"honeymoon": 5, "anniversary": 10, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [1, 2, 12],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Vieille ville de Cracovie", "emoji": "european_castle", "category": "history"},
            {"name": "Mines de sel Wieliczka", "emoji": "gem", "category": "culture"},
            {"name": "Auschwitz memorial", "emoji": "candle", "category": "history"},
            {"name": "Tatras randonnee", "emoji": "mountain", "category": "nature"},
            {"name": "Varsovie nightlife", "emoji": "night_with_stars", "category": "nightlife"}
        ],
        "fallback_headlines": {
            "solo": "Pologne, tresor cache de l'Europe",
            "couple": "Cracovie romantique et histoire",
            "family": "Pologne en famille, decouverte culturelle",
            "friends": "Varsovie et Cracovie entre amis",
            "pet": "Pologne avec votre compagnon"
        },
        "fallback_description": "Histoire fascinante, villes charmantes et excellent rapport qualite-prix."
    },
    {
        "country_code": "HU",
        "country_name": "Hongrie",
        "flag_emoji": "HU",
        "region": "Europe",
        "subregion": "Eastern Europe",
        "languages": ["Hungarian"],
        "currency": "HUF",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 60,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 85, "beach": 30, "adventure": 45,
            "nature": 60, "nightlife": 85, "history": 90, "art": 80,
            "shopping": 70, "wellness": 95, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 70, "pet_friendly_score": 55,
            "family_friendly_score": 75, "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 50,
            "budget_min_7d": 300, "budget_max_7d": 550,
            "comfort_min_7d": 550, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 20, "pet": 5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 10},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [1, 2],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Bains thermaux Budapest", "emoji": "hot_springs", "category": "wellness"},
            {"name": "Parlement de Budapest", "emoji": "classical_building", "category": "culture"},
            {"name": "Ruin bars", "emoji": "tropical_drink", "category": "nightlife"},
            {"name": "Croisiere sur le Danube", "emoji": "ship", "category": "culture"},
            {"name": "Cuisine hongroise", "emoji": "plate_with_cutlery", "category": "food"}
        ],
        "fallback_headlines": {
            "solo": "Budapest, perle du Danube",
            "couple": "Budapest romantique et bains thermaux",
            "family": "Hongrie en famille, culture accessible",
            "friends": "Budapest festive entre amis",
            "pet": "Hongrie avec votre compagnon"
        },
        "fallback_description": "Bains thermaux, architecture sublime et vie nocturne animee."
    },
    {
        "country_code": "BE",
        "country_name": "Belgique",
        "flag_emoji": "BE",
        "region": "Europe",
        "subregion": "Western Europe",
        "languages": ["French", "Dutch", "German"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 65,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 90, "food": 95, "beach": 40, "adventure": 35,
            "nature": 55, "nightlife": 75, "history": 90, "art": 95,
            "shopping": 80, "wellness": 60, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 85, "pet_friendly_score": 70,
            "family_friendly_score": 85, "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 90,
            "budget_min_7d": 450, "budget_max_7d": 750,
            "comfort_min_7d": 750, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": 10},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [4, 5, 6, 9],
        "avoid_months": [1, 2, 11, 12],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Chocolateries belges", "emoji": "chocolate_bar", "category": "food"},
            {"name": "Grand-Place Bruxelles", "emoji": "european_castle", "category": "culture"},
            {"name": "Canaux de Bruges", "emoji": "boat", "category": "culture"},
            {"name": "Bieres belges", "emoji": "beer", "category": "food"},
            {"name": "Musees d'art", "emoji": "art", "category": "art"}
        ],
        "fallback_headlines": {
            "solo": "Belgique, art de vivre et chocolat",
            "couple": "Bruges romantique et gastronomie",
            "family": "Belgique en famille, accessible et gourmande",
            "friends": "Biere et culture belge entre amis",
            "pet": "Belgique avec votre compagnon"
        },
        "fallback_description": "Chocolat, bieres, architecture et art dans un pays compact."
    },
    {
        "country_code": "IE",
        "country_name": "Irlande",
        "flag_emoji": "IE",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["English", "Irish"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 55,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 90, "food": 75, "beach": 50, "adventure": 65,
            "nature": 90, "nightlife": 85, "history": 90, "art": 75,
            "shopping": 65, "wellness": 55, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 80, "pet_friendly_score": 75,
            "family_friendly_score": 85, "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 100,
            "budget_min_7d": 500, "budget_max_7d": 850,
            "comfort_min_7d": 850, "comfort_max_7d": 1600,
            "premium_min_7d": 1600, "premium_max_7d": 3200,
            "luxury_min_7d": 3200, "luxury_max_7d": 7000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 20, "pet": 10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [11, 12, 1, 2],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Falaises de Moher", "emoji": "mountain", "category": "nature"},
            {"name": "Pubs de Dublin", "emoji": "beer", "category": "nightlife"},
            {"name": "Ring of Kerry", "emoji": "car", "category": "nature"},
            {"name": "Chateau de Blarney", "emoji": "european_castle", "category": "history"},
            {"name": "Musique traditionnelle", "emoji": "musical_note", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Irlande, terre de legendes",
            "couple": "Irlande romantique et paysages verts",
            "family": "Irlande en famille, nature et histoire",
            "friends": "Pubs et aventures irlandaises entre amis",
            "pet": "Irlande avec votre compagnon"
        },
        "fallback_description": "Paysages verdoyants, pubs chaleureux et culture celtique authentique."
    },
    {
        "country_code": "SE",
        "country_name": "Suede",
        "flag_emoji": "SE",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["Swedish"],
        "currency": "SEK",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 50,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 45, "adventure": 70,
            "nature": 90, "nightlife": 75, "history": 80, "art": 85,
            "shopping": 80, "wellness": 85, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 90, "pet_friendly_score": 80,
            "family_friendly_score": 90, "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 110,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4000,
            "luxury_min_7d": 4000, "luxury_max_7d": 9000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 20, "friends": 15, "pet": 15},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 20},
        "best_months": [5, 6, 7, 8],
        "avoid_months": [11, 12, 1, 2],
        "best_seasons": ["Ete"],
        "trending_score": 70,
        "top_activities": [
            {"name": "Stockholm archipel", "emoji": "island", "category": "nature"},
            {"name": "Aurores boreales", "emoji": "sparkles", "category": "nature"},
            {"name": "Design scandinave", "emoji": "art", "category": "shopping"},
            {"name": "Fika tradition cafe", "emoji": "coffee", "category": "culture"},
            {"name": "Musee ABBA", "emoji": "musical_note", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Suede, design et nature nordique",
            "couple": "Stockholm romantique et iles",
            "family": "Suede en famille, qualite de vie",
            "friends": "Aventure scandinave entre amis",
            "pet": "Suede avec votre compagnon"
        },
        "fallback_description": "Design elegant, nature preservee et qualite de vie exceptionnelle."
    },

    # Asia additions
    {
        "country_code": "MY",
        "country_name": "Malaisie",
        "flag_emoji": "MY",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Malay", "English"],
        "currency": "MYR",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 85, "food": 95, "beach": 85, "adventure": 75,
            "nature": 90, "nightlife": 70, "history": 75, "art": 70,
            "shopping": 85, "wellness": 75, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 65, "pet_friendly_score": 45,
            "family_friendly_score": 80, "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 40,
            "budget_min_7d": 250, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 15},
        "best_months": [3, 4, 5, 9, 10],
        "avoid_months": [11, 12, 1],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Torres Petronas", "emoji": "cityscape", "category": "culture"},
            {"name": "Street food Penang", "emoji": "plate_with_cutlery", "category": "food"},
            {"name": "Plages Langkawi", "emoji": "beach", "category": "beach"},
            {"name": "Jungle Borneo", "emoji": "deciduous_tree", "category": "nature"},
            {"name": "Grottes Batu", "emoji": "mountain", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Malaisie, diversite culturelle",
            "couple": "Langkawi romantique et Kuala Lumpur",
            "family": "Malaisie en famille, aventure accessible",
            "friends": "Aventure malaisienne entre amis",
            "pet": "Malaisie avec votre compagnon"
        },
        "fallback_description": "Melange unique de cultures, street food legendaire et nature tropicale."
    },
    {
        "country_code": "PH",
        "country_name": "Philippines",
        "flag_emoji": "PH",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Filipino", "English"],
        "currency": "PHP",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 65,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 75, "food": 80, "beach": 98, "adventure": 85,
            "nature": 90, "nightlife": 70, "history": 65, "art": 60,
            "shopping": 70, "wellness": 70, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 45, "pet_friendly_score": 40,
            "family_friendly_score": 75, "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 200, "budget_max_7d": 400,
            "comfort_min_7d": 400, "comfort_max_7d": 800,
            "premium_min_7d": 800, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 20, "pet": -10},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 15, "vacation": 5, "workation": 10},
        "best_months": [1, 2, 3, 4, 5],
        "avoid_months": [7, 8, 9, 10],
        "best_seasons": ["Hiver", "Printemps"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Palawan El Nido", "emoji": "beach", "category": "beach"},
            {"name": "Collines chocolat Bohol", "emoji": "mountain", "category": "nature"},
            {"name": "Plongee Cebu", "emoji": "fish", "category": "adventure"},
            {"name": "Rizicultures Banaue", "emoji": "rice", "category": "nature"},
            {"name": "Island hopping", "emoji": "boat", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Philippines, 7000 iles paradisiaques",
            "couple": "Palawan romantique et plages secretes",
            "family": "Philippines en famille, iles accessibles",
            "friends": "Island hopping entre amis",
            "pet": "Philippines avec votre compagnon"
        },
        "fallback_description": "Plages de reve, island hopping et hospitalite legendaire."
    },
    {
        "country_code": "LK",
        "country_name": "Sri Lanka",
        "flag_emoji": "LK",
        "region": "Asia",
        "subregion": "Southern Asia",
        "languages": ["Sinhala", "Tamil", "English"],
        "currency": "LKR",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 60,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 90, "food": 85, "beach": 85, "adventure": 80,
            "nature": 95, "nightlife": 45, "history": 90, "art": 70,
            "shopping": 65, "wellness": 90, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 45, "pet_friendly_score": 40,
            "family_friendly_score": 75, "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 30,
            "budget_min_7d": 200, "budget_max_7d": 400,
            "comfort_min_7d": 400, "comfort_max_7d": 800,
            "premium_min_7d": 800, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [1, 2, 3, 4],
        "avoid_months": [5, 6, 10, 11],
        "best_seasons": ["Hiver"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Train des montagnes", "emoji": "train", "category": "nature"},
            {"name": "Temples de Sigiriya", "emoji": "shinto_shrine", "category": "history"},
            {"name": "Safari Yala", "emoji": "elephant", "category": "nature"},
            {"name": "Plages du sud", "emoji": "beach", "category": "beach"},
            {"name": "Ayurveda", "emoji": "lotus", "category": "wellness"}
        ],
        "fallback_headlines": {
            "solo": "Sri Lanka, ile aux tresors",
            "couple": "Sri Lanka romantique, nature et temples",
            "family": "Sri Lanka en famille, aventure douce",
            "friends": "Safari et plages entre amis",
            "pet": "Sri Lanka avec votre compagnon"
        },
        "fallback_description": "Temples anciens, plages dorees, safaris et ayurveda authentique."
    },
    {
        "country_code": "KH",
        "country_name": "Cambodge",
        "flag_emoji": "KH",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Khmer"],
        "currency": "KHR",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 95, "food": 80, "beach": 70, "adventure": 70,
            "nature": 75, "nightlife": 65, "history": 98, "art": 75,
            "shopping": 60, "wellness": 65, "sports": 45
        },
        "must_haves": {
            "accessibility_score": 40, "pet_friendly_score": 35,
            "family_friendly_score": 65, "wifi_quality_score": 60
        },
        "budget": {
            "cost_of_living_index": 28,
            "budget_min_7d": 180, "budget_max_7d": 350,
            "comfort_min_7d": 350, "comfort_max_7d": 700,
            "premium_min_7d": 700, "premium_max_7d": 1500,
            "luxury_min_7d": 1500, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 5, "friends": 15, "pet": -15},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [11, 12, 1, 2, 3],
        "avoid_months": [5, 6, 7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Angkor Wat", "emoji": "shinto_shrine", "category": "history"},
            {"name": "Temples de Siem Reap", "emoji": "classical_building", "category": "culture"},
            {"name": "Phnom Penh", "emoji": "cityscape", "category": "culture"},
            {"name": "Plages de Sihanoukville", "emoji": "beach", "category": "beach"},
            {"name": "Cuisine khmere", "emoji": "plate_with_cutlery", "category": "food"}
        ],
        "fallback_headlines": {
            "solo": "Cambodge, temples millenaires",
            "couple": "Angkor romantique et mystique",
            "family": "Cambodge en famille, histoire vivante",
            "friends": "Temples et aventures entre amis",
            "pet": "Cambodge avec votre compagnon"
        },
        "fallback_description": "Temples d'Angkor, histoire khmere et authenticite preservee."
    },
    {
        "country_code": "NP",
        "country_name": "Nepal",
        "flag_emoji": "NP",
        "region": "Asia",
        "subregion": "Southern Asia",
        "languages": ["Nepali"],
        "currency": "NPR",
        "style_scores": {
            "chill_vs_intense": 65,
            "city_vs_nature": 80,
            "eco_vs_luxury": 30,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 90, "food": 75, "beach": 0, "adventure": 98,
            "nature": 100, "nightlife": 40, "history": 85, "art": 70,
            "shopping": 55, "wellness": 80, "sports": 85
        },
        "must_haves": {
            "accessibility_score": 25, "pet_friendly_score": 30,
            "family_friendly_score": 50, "wifi_quality_score": 50
        },
        "budget": {
            "cost_of_living_index": 25,
            "budget_min_7d": 150, "budget_max_7d": 300,
            "comfort_min_7d": 300, "comfort_max_7d": 600,
            "premium_min_7d": 600, "premium_max_7d": 1500,
            "luxury_min_7d": 1500, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 25, "couple": 15, "family": 0, "friends": 20, "pet": -20},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 15, "vacation": 5, "workation": 5},
        "best_months": [3, 4, 5, 10, 11],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Trek Everest Base Camp", "emoji": "mountain", "category": "adventure"},
            {"name": "Temples Katmandou", "emoji": "shinto_shrine", "category": "culture"},
            {"name": "Annapurna Circuit", "emoji": "hiking", "category": "adventure"},
            {"name": "Safari Chitwan", "emoji": "elephant", "category": "nature"},
            {"name": "Yoga et meditation", "emoji": "lotus", "category": "wellness"}
        ],
        "fallback_headlines": {
            "solo": "Nepal, toit du monde",
            "couple": "Himalaya romantique et spirituel",
            "family": "Nepal en famille, aventure moderee",
            "friends": "Trek et aventures entre amis",
            "pet": "Nepal avec votre compagnon"
        },
        "fallback_description": "Himalayas majestueuses, spiritualite et aventure au sommet du monde."
    },

    # Americas additions
    {
        "country_code": "CA",
        "country_name": "Canada",
        "flag_emoji": "CA",
        "region": "Americas",
        "subregion": "Northern America",
        "languages": ["English", "French"],
        "currency": "CAD",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 45, "adventure": 90,
            "nature": 98, "nightlife": 75, "history": 70, "art": 80,
            "shopping": 80, "wellness": 80, "sports": 85
        },
        "must_haves": {
            "accessibility_score": 90, "pet_friendly_score": 85,
            "family_friendly_score": 95, "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 95,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4000,
            "luxury_min_7d": 4000, "luxury_max_7d": 10000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 25, "friends": 20, "pet": 15},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 10, "workation": 15},
        "best_months": [6, 7, 8, 9],
        "avoid_months": [12, 1, 2],
        "best_seasons": ["Ete", "Automne"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Rocheuses canadiennes", "emoji": "mountain", "category": "nature"},
            {"name": "Chutes Niagara", "emoji": "droplet", "category": "nature"},
            {"name": "Vancouver outdoor", "emoji": "evergreen_tree", "category": "adventure"},
            {"name": "Quebec historique", "emoji": "european_castle", "category": "history"},
            {"name": "Aurores boreales Yukon", "emoji": "sparkles", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Canada, grands espaces sauvages",
            "couple": "Canada romantique, nature grandiose",
            "family": "Canada en famille, aventure securisee",
            "friends": "Road trip canadien entre amis",
            "pet": "Canada avec votre compagnon"
        },
        "fallback_description": "Nature spectaculaire, villes cosmopolites et hospitalite legendaire."
    },
    {
        "country_code": "AR",
        "country_name": "Argentine",
        "flag_emoji": "AR",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Spanish"],
        "currency": "ARS",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 55,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 90, "food": 90, "beach": 55, "adventure": 85,
            "nature": 95, "nightlife": 90, "history": 80, "art": 85,
            "shopping": 75, "wellness": 70, "sports": 85
        },
        "must_haves": {
            "accessibility_score": 55, "pet_friendly_score": 60,
            "family_friendly_score": 75, "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 350, "budget_max_7d": 600,
            "comfort_min_7d": 600, "comfort_max_7d": 1200,
            "premium_min_7d": 1200, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 25, "family": 10, "friends": 20, "pet": 5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 15, "vacation": 5, "workation": 10},
        "best_months": [10, 11, 12, 3, 4],
        "avoid_months": [6, 7],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Tango Buenos Aires", "emoji": "dancer", "category": "culture"},
            {"name": "Glacier Perito Moreno", "emoji": "ice_cube", "category": "nature"},
            {"name": "Vignobles Mendoza", "emoji": "wine_glass", "category": "food"},
            {"name": "Chutes Iguazu", "emoji": "droplet", "category": "nature"},
            {"name": "Patagonie", "emoji": "mountain", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Argentine, passion et grands espaces",
            "couple": "Buenos Aires romantique et Patagonie",
            "family": "Argentine en famille, diversite naturelle",
            "friends": "Tango et vin entre amis",
            "pet": "Argentine avec votre compagnon"
        },
        "fallback_description": "Tango passionnel, vins exceptionnels et paysages patagoniens epoustouflants."
    },
    {
        "country_code": "CL",
        "country_name": "Chili",
        "flag_emoji": "CL",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Spanish"],
        "currency": "CLP",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 70,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 80, "food": 85, "beach": 55, "adventure": 95,
            "nature": 98, "nightlife": 70, "history": 75, "art": 75,
            "shopping": 65, "wellness": 70, "sports": 80
        },
        "must_haves": {
            "accessibility_score": 60, "pet_friendly_score": 55,
            "family_friendly_score": 75, "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 60,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 3000,
            "luxury_min_7d": 3000, "luxury_max_7d": 7000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 10, "friends": 20, "pet": 0},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [10, 11, 12, 1, 2, 3],
        "avoid_months": [6, 7],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Torres del Paine", "emoji": "mountain", "category": "nature"},
            {"name": "Ile de Paques", "emoji": "moyai", "category": "history"},
            {"name": "Atacama desert", "emoji": "desert", "category": "nature"},
            {"name": "Vallee viticole", "emoji": "wine_glass", "category": "food"},
            {"name": "Santiago moderne", "emoji": "cityscape", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Chili, terre des extremes",
            "couple": "Chili romantique, desert aux glaciers",
            "family": "Chili en famille, aventure nature",
            "friends": "Patagonie chilienne entre amis",
            "pet": "Chili avec votre compagnon"
        },
        "fallback_description": "Du desert d'Atacama aux glaciers de Patagonie, nature a l'etat brut."
    },

    # Africa additions
    {
        "country_code": "TZ",
        "country_name": "Tanzanie",
        "flag_emoji": "TZ",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["Swahili", "English"],
        "currency": "TZS",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 85,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 75, "food": 65, "beach": 90, "adventure": 95,
            "nature": 100, "nightlife": 40, "history": 60, "art": 55,
            "shopping": 50, "wellness": 65, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 35, "pet_friendly_score": 25,
            "family_friendly_score": 60, "wifi_quality_score": 50
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 600, "budget_max_7d": 1200,
            "comfort_min_7d": 1200, "comfort_max_7d": 2500,
            "premium_min_7d": 2500, "premium_max_7d": 5000,
            "luxury_min_7d": 5000, "luxury_max_7d": 15000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 25, "family": 15, "friends": 15, "pet": -20},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 25, "birthday": 15, "vacation": 5, "workation": 0},
        "best_months": [6, 7, 8, 9, 10, 1, 2],
        "avoid_months": [3, 4, 5, 11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Safari Serengeti", "emoji": "lion", "category": "nature"},
            {"name": "Cratere Ngorongoro", "emoji": "volcano", "category": "nature"},
            {"name": "Zanzibar plages", "emoji": "beach", "category": "beach"},
            {"name": "Kilimandjaro trek", "emoji": "mountain", "category": "adventure"},
            {"name": "Migration gnous", "emoji": "water_buffalo", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Tanzanie, safari au coeur de l'Afrique",
            "couple": "Serengeti romantique et Zanzibar",
            "family": "Tanzanie en famille, safari adapte",
            "friends": "Aventure safari entre amis",
            "pet": "Tanzanie avec votre compagnon"
        },
        "fallback_description": "Safari mythique au Serengeti, Kilimandjaro et plages de Zanzibar."
    },
    {
        "country_code": "TN",
        "country_name": "Tunisie",
        "flag_emoji": "TN",
        "region": "Africa",
        "subregion": "Northern Africa",
        "languages": ["Arabic", "French"],
        "currency": "TND",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 50,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 85, "beach": 85, "adventure": 65,
            "nature": 65, "nightlife": 60, "history": 95, "art": 75,
            "shopping": 80, "wellness": 85, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 50, "pet_friendly_score": 40,
            "family_friendly_score": 80, "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 250, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 20, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 10, "workation": 5},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 68,
        "top_activities": [
            {"name": "Medina Tunis", "emoji": "mosque", "category": "culture"},
            {"name": "Ruines Carthage", "emoji": "classical_building", "category": "history"},
            {"name": "Plages Djerba", "emoji": "beach", "category": "beach"},
            {"name": "Sahara excursion", "emoji": "camel", "category": "adventure"},
            {"name": "Thalasso", "emoji": "hot_springs", "category": "wellness"}
        ],
        "fallback_headlines": {
            "solo": "Tunisie, mediterranee authentique",
            "couple": "Tunisie romantique, plages et histoire",
            "family": "Tunisie en famille, soleil accessible",
            "friends": "Aventure tunisienne entre amis",
            "pet": "Tunisie avec votre compagnon"
        },
        "fallback_description": "Heritage romain, plages mediterraneennes et hospitalite tunisienne."
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

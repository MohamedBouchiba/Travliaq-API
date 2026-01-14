#!/usr/bin/env python3
"""
Seed script for 50 NEW country profiles in MongoDB.
Following the exact same structure as seed_country_profiles.py
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGODB_URI = "mongodb+srv://teamtravliaq_db_user:DUfRgh8TkEDJHSlT@travliaq-countrybasis.wljfuyy.mongodb.net/?retryWrites=true&w=majority&appName=Travliaq-CountryBasis"
MONGODB_DB = "travliaq_knowledge_base"
COLLECTION_NAME = "country_profiles"

# ============================================================================
# 50 NEW COUNTRY PROFILES
# ============================================================================

NEW_COUNTRY_PROFILES = [
    # ========================================================================
    # EUROPE (12 countries)
    # ========================================================================
    {
        "country_code": "NO",
        "country_name": "Norvege",
        "flag_emoji": "🇳🇴",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["Norwegian"],
        "currency": "NOK",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 85,
            "eco_vs_luxury": 70,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 70, "food": 60, "beach": 30, "adventure": 90,
            "nature": 98, "nightlife": 45, "history": 60, "art": 65,
            "shopping": 50, "wellness": 75, "sports": 85
        },
        "must_haves": {
            "accessibility_score": 85,
            "pet_friendly_score": 70,
            "family_friendly_score": 80,
            "wifi_quality_score": 92
        },
        "budget": {
            "cost_of_living_index": 125,
            "budget_min_7d": 700, "budget_max_7d": 1100,
            "comfort_min_7d": 1100, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4000,
            "luxury_min_7d": 4000, "luxury_max_7d": 10000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [5, 6, 7, 8, 9, 12, 1, 2],
        "avoid_months": [11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Fjords de Norvege", "emoji": "🏔️", "category": "nature"},
            {"name": "Aurores boreales", "emoji": "🌌", "category": "nature"},
            {"name": "Tromso", "emoji": "🦌", "category": "adventure"},
            {"name": "Bergen", "emoji": "🏘️", "category": "culture"},
            {"name": "Randonnee Preikestolen", "emoji": "🥾", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Norvege, aventure arctique en solo",
            "couple": "Fjords et aurores boreales a deux",
            "family": "Norvege en famille, nature et trolls",
            "friends": "Norvege entre amis, randos et fjords",
            "pet": "Norvege avec votre compagnon"
        },
        "fallback_description": "Fjords spectaculaires, aurores boreales et nature arctique."
    },
    {
        "country_code": "DK",
        "country_name": "Danemark",
        "flag_emoji": "🇩🇰",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["Danish"],
        "currency": "DKK",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 45,
            "eco_vs_luxury": 65,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 45, "adventure": 50,
            "nature": 60, "nightlife": 70, "history": 75, "art": 85,
            "shopping": 75, "wellness": 70, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 90,
            "pet_friendly_score": 75,
            "family_friendly_score": 90,
            "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 115,
            "budget_min_7d": 650, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 1800,
            "premium_min_7d": 1800, "premium_max_7d": 3500,
            "luxury_min_7d": 3500, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 20, "friends": 15, "pet": 10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 20},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [1, 2],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Copenhague", "emoji": "🏰", "category": "culture"},
            {"name": "Tivoli Gardens", "emoji": "🎢", "category": "family"},
            {"name": "Nyhavn", "emoji": "🏘️", "category": "culture"},
            {"name": "Design danois", "emoji": "🪑", "category": "art"},
            {"name": "Gastronomie Noma", "emoji": "🍽️", "category": "food"}
        ],
        "fallback_headlines": {
            "solo": "Copenhague, hygge en solo",
            "couple": "Danemark romantique et design",
            "family": "Danemark en famille, Legoland et Vikings",
            "friends": "Copenhague entre amis, velo et bars",
            "pet": "Danemark avec votre compagnon"
        },
        "fallback_description": "Design scandinave, hygge et gastronomie de classe mondiale."
    },
    {
        "country_code": "FI",
        "country_name": "Finlande",
        "flag_emoji": "🇫🇮",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["Finnish", "Swedish"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 80,
            "eco_vs_luxury": 65,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 70, "food": 60, "beach": 25, "adventure": 85,
            "nature": 95, "nightlife": 55, "history": 60, "art": 70,
            "shopping": 55, "wellness": 90, "sports": 80
        },
        "must_haves": {
            "accessibility_score": 88,
            "pet_friendly_score": 70,
            "family_friendly_score": 85,
            "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 110,
            "budget_min_7d": 600, "budget_max_7d": 950,
            "comfort_min_7d": 950, "comfort_max_7d": 1700,
            "premium_min_7d": 1700, "premium_max_7d": 3200,
            "luxury_min_7d": 3200, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 15},
        "best_months": [6, 7, 8, 12, 1, 2, 3],
        "avoid_months": [11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Laponie finlandaise", "emoji": "🦌", "category": "nature"},
            {"name": "Sauna traditionnel", "emoji": "🧖", "category": "wellness"},
            {"name": "Helsinki", "emoji": "🏛️", "category": "culture"},
            {"name": "Aurores boreales", "emoji": "🌌", "category": "nature"},
            {"name": "Lacs et forets", "emoji": "🌲", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Finlande, solitude et nature pure",
            "couple": "Laponie romantique sous les aurores",
            "family": "Finlande en famille, Pere Noel et rennes",
            "friends": "Finlande entre amis, sauna et lacs",
            "pet": "Finlande avec votre compagnon"
        },
        "fallback_description": "Laponie magique, saunas authentiques et nature intacte."
    },
    {
        "country_code": "IS",
        "country_name": "Islande",
        "flag_emoji": "🇮🇸",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["Icelandic"],
        "currency": "ISK",
        "style_scores": {
            "chill_vs_intense": 65,
            "city_vs_nature": 95,
            "eco_vs_luxury": 75,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 65, "food": 55, "beach": 20, "adventure": 95,
            "nature": 100, "nightlife": 50, "history": 60, "art": 60,
            "shopping": 40, "wellness": 85, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 75,
            "pet_friendly_score": 50,
            "family_friendly_score": 70,
            "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 130,
            "budget_min_7d": 800, "budget_max_7d": 1200,
            "comfort_min_7d": 1200, "comfort_max_7d": 2200,
            "premium_min_7d": 2200, "premium_max_7d": 4500,
            "luxury_min_7d": 4500, "luxury_max_7d": 12000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [12, 1, 2],
        "best_seasons": ["Ete"],
        "trending_score": 88,
        "top_activities": [
            {"name": "Cercle d'Or", "emoji": "🌋", "category": "nature"},
            {"name": "Blue Lagoon", "emoji": "♨️", "category": "wellness"},
            {"name": "Glaciers et cascades", "emoji": "🧊", "category": "nature"},
            {"name": "Observation baleines", "emoji": "🐋", "category": "adventure"},
            {"name": "Aurores boreales", "emoji": "🌌", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Islande, aventure volcanique en solo",
            "couple": "Islande romantique, feu et glace",
            "family": "Islande en famille, geysers et cascades",
            "friends": "Islande entre amis, road trip epique",
            "pet": "Islande sauvage"
        },
        "fallback_description": "Volcans, glaciers, geysers et paysages lunaires uniques."
    },
    {
        "country_code": "RO",
        "country_name": "Roumanie",
        "flag_emoji": "🇷🇴",
        "region": "Europe",
        "subregion": "Eastern Europe",
        "languages": ["Romanian"],
        "currency": "RON",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 65,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 80, "food": 70, "beach": 40, "adventure": 70,
            "nature": 85, "nightlife": 65, "history": 90, "art": 65,
            "shopping": 50, "wellness": 60, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 60,
            "pet_friendly_score": 55,
            "family_friendly_score": 70,
            "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 250, "budget_max_7d": 400,
            "comfort_min_7d": 400, "comfort_max_7d": 750,
            "premium_min_7d": 750, "premium_max_7d": 1400,
            "luxury_min_7d": 1400, "luxury_max_7d": 3500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 15},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [1, 2],
        "best_seasons": ["Printemps", "Ete", "Automne"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Transylvanie", "emoji": "🏰", "category": "history"},
            {"name": "Chateau de Bran", "emoji": "🧛", "category": "history"},
            {"name": "Carpates", "emoji": "⛰️", "category": "nature"},
            {"name": "Bucarest", "emoji": "🏛️", "category": "culture"},
            {"name": "Villages saxons", "emoji": "🏘️", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Roumanie, mystere et aventure en solo",
            "couple": "Transylvanie romantique et chateaux",
            "family": "Roumanie en famille, legendes et nature",
            "friends": "Roumanie entre amis, Carpates et fetes",
            "pet": "Roumanie avec votre compagnon"
        },
        "fallback_description": "Transylvanie mysterieuse, Carpates sauvages et chateaux legendaires."
    },
    {
        "country_code": "SK",
        "country_name": "Slovaquie",
        "flag_emoji": "🇸🇰",
        "region": "Europe",
        "subregion": "Central Europe",
        "languages": ["Slovak"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 70,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 70, "food": 65, "beach": 20, "adventure": 75,
            "nature": 85, "nightlife": 55, "history": 80, "art": 60,
            "shopping": 45, "wellness": 65, "sports": 80
        },
        "must_haves": {
            "accessibility_score": 65,
            "pet_friendly_score": 60,
            "family_friendly_score": 75,
            "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 50,
            "budget_min_7d": 280, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 800,
            "premium_min_7d": 800, "premium_max_7d": 1500,
            "luxury_min_7d": 1500, "luxury_max_7d": 3500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [5, 6, 7, 8, 9, 12, 1, 2],
        "avoid_months": [11],
        "best_seasons": ["Printemps", "Ete", "Hiver"],
        "trending_score": 68,
        "top_activities": [
            {"name": "Hautes Tatras", "emoji": "🏔️", "category": "nature"},
            {"name": "Bratislava", "emoji": "🏰", "category": "culture"},
            {"name": "Chateaux medievaux", "emoji": "🏰", "category": "history"},
            {"name": "Ski dans les Tatras", "emoji": "⛷️", "category": "sports"},
            {"name": "Grottes de glace", "emoji": "🧊", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Slovaquie, montagnes et chateaux en solo",
            "couple": "Tatras romantiques et nature sauvage",
            "family": "Slovaquie en famille, aventure accessible",
            "friends": "Slovaquie entre amis, rando et ski",
            "pet": "Slovaquie avec votre compagnon"
        },
        "fallback_description": "Hautes Tatras majestueuses, chateaux et nature preservee."
    },
    {
        "country_code": "SI",
        "country_name": "Slovenie",
        "flag_emoji": "🇸🇮",
        "region": "Europe",
        "subregion": "Central Europe",
        "languages": ["Slovenian"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 75,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 75, "food": 75, "beach": 45, "adventure": 80,
            "nature": 90, "nightlife": 55, "history": 70, "art": 65,
            "shopping": 50, "wellness": 80, "sports": 80
        },
        "must_haves": {
            "accessibility_score": 75,
            "pet_friendly_score": 70,
            "family_friendly_score": 85,
            "wifi_quality_score": 88
        },
        "budget": {
            "cost_of_living_index": 65,
            "budget_min_7d": 350, "budget_max_7d": 550,
            "comfort_min_7d": 550, "comfort_max_7d": 1000,
            "premium_min_7d": 1000, "premium_max_7d": 1900,
            "luxury_min_7d": 1900, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 15, "friends": 15, "pet": 10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [1, 2],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Lac de Bled", "emoji": "🏞️", "category": "nature"},
            {"name": "Ljubljana", "emoji": "🏛️", "category": "culture"},
            {"name": "Grottes de Postojna", "emoji": "🦇", "category": "nature"},
            {"name": "Alpes juliennes", "emoji": "🏔️", "category": "adventure"},
            {"name": "Cote adriatique", "emoji": "🌊", "category": "beach"}
        ],
        "fallback_headlines": {
            "solo": "Slovenie, perle verte en solo",
            "couple": "Lac de Bled romantique et Alpes",
            "family": "Slovenie en famille, nature et grottes",
            "friends": "Slovenie entre amis, outdoor et vins",
            "pet": "Slovenie avec votre compagnon"
        },
        "fallback_description": "Lac de Bled feerique, Alpes juliennes et nature preservee."
    },
    {
        "country_code": "BA",
        "country_name": "Bosnie-Herzegovine",
        "flag_emoji": "🇧🇦",
        "region": "Europe",
        "subregion": "Southeast Europe",
        "languages": ["Bosnian", "Croatian", "Serbian"],
        "currency": "BAM",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 30,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 85, "food": 75, "beach": 30, "adventure": 65,
            "nature": 75, "nightlife": 60, "history": 90, "art": 60,
            "shopping": 45, "wellness": 50, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 50,
            "pet_friendly_score": 50,
            "family_friendly_score": 65,
            "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 38,
            "budget_min_7d": 200, "budget_max_7d": 350,
            "comfort_min_7d": 350, "comfort_max_7d": 650,
            "premium_min_7d": 650, "premium_max_7d": 1200,
            "luxury_min_7d": 1200, "luxury_max_7d": 3000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [12, 1, 2],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 70,
        "top_activities": [
            {"name": "Mostar et son pont", "emoji": "🌉", "category": "history"},
            {"name": "Sarajevo", "emoji": "🕌", "category": "culture"},
            {"name": "Cascades de Kravice", "emoji": "💧", "category": "nature"},
            {"name": "Cuisine bosniaque", "emoji": "🥘", "category": "food"},
            {"name": "Histoire ottomane", "emoji": "🏛️", "category": "history"}
        ],
        "fallback_headlines": {
            "solo": "Bosnie, histoire et authenticite en solo",
            "couple": "Mostar romantique et multiculturel",
            "family": "Bosnie en famille, decouverte culturelle",
            "friends": "Bosnie entre amis, histoire et cafes",
            "pet": "Bosnie avec votre compagnon"
        },
        "fallback_description": "Mostar iconique, melange culturel unique et histoire poignante."
    },
    {
        "country_code": "CY",
        "country_name": "Chypre",
        "flag_emoji": "🇨🇾",
        "region": "Europe",
        "subregion": "Southern Europe",
        "languages": ["Greek", "Turkish"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 55,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 75, "food": 80, "beach": 90, "adventure": 55,
            "nature": 65, "nightlife": 70, "history": 85, "art": 55,
            "shopping": 60, "wellness": 70, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 70,
            "pet_friendly_score": 55,
            "family_friendly_score": 85,
            "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 75,
            "budget_min_7d": 400, "budget_max_7d": 650,
            "comfort_min_7d": 650, "comfort_max_7d": 1200,
            "premium_min_7d": 1200, "premium_max_7d": 2300,
            "luxury_min_7d": 2300, "luxury_max_7d": 5500
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 20, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 10, "workation": 10},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 74,
        "top_activities": [
            {"name": "Plages de Paphos", "emoji": "🏖️", "category": "beach"},
            {"name": "Site archeologique Kourion", "emoji": "🏛️", "category": "history"},
            {"name": "Monts Troodos", "emoji": "⛰️", "category": "nature"},
            {"name": "Cuisine chypriote", "emoji": "🍽️", "category": "food"},
            {"name": "Bain d'Aphrodite", "emoji": "🧜‍♀️", "category": "history"}
        ],
        "fallback_headlines": {
            "solo": "Chypre, soleil et histoire en solo",
            "couple": "Chypre romantique, ile d'Aphrodite",
            "family": "Chypre en famille, plages et ruines",
            "friends": "Chypre entre amis, fete et plage",
            "pet": "Chypre avec votre compagnon"
        },
        "fallback_description": "Ile d'Aphrodite, plages dorees et vestiges antiques."
    },
    {
        "country_code": "MT",
        "country_name": "Malte",
        "flag_emoji": "🇲🇹",
        "region": "Europe",
        "subregion": "Southern Europe",
        "languages": ["Maltese", "English"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 45,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 85, "food": 75, "beach": 80, "adventure": 60,
            "nature": 55, "nightlife": 75, "history": 95, "art": 70,
            "shopping": 55, "wellness": 60, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 70,
            "pet_friendly_score": 50,
            "family_friendly_score": 80,
            "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 70,
            "budget_min_7d": 380, "budget_max_7d": 600,
            "comfort_min_7d": 600, "comfort_max_7d": 1100,
            "premium_min_7d": 1100, "premium_max_7d": 2100,
            "luxury_min_7d": 2100, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 15, "friends": 20, "pet": 0},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 10, "workation": 15},
        "best_months": [4, 5, 6, 9, 10],
        "avoid_months": [7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 76,
        "top_activities": [
            {"name": "La Valette", "emoji": "🏰", "category": "history"},
            {"name": "Temples megalithiques", "emoji": "🗿", "category": "history"},
            {"name": "Plongee sous-marine", "emoji": "🤿", "category": "adventure"},
            {"name": "Gozo", "emoji": "🏝️", "category": "nature"},
            {"name": "Blue Lagoon Comino", "emoji": "🌊", "category": "beach"}
        ],
        "fallback_headlines": {
            "solo": "Malte, histoire millenaire en solo",
            "couple": "Malte romantique, chevaliers et lagons",
            "family": "Malte en famille, histoire et plages",
            "friends": "Malte entre amis, plongee et fetes",
            "pet": "Malte avec votre compagnon"
        },
        "fallback_description": "Temples prehistoriques, chevaliers de Malte et eaux cristallines."
    },
    {
        "country_code": "LU",
        "country_name": "Luxembourg",
        "flag_emoji": "🇱🇺",
        "region": "Europe",
        "subregion": "Western Europe",
        "languages": ["Luxembourgish", "French", "German"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 40,
            "eco_vs_luxury": 80,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 80, "food": 85, "beach": 10, "adventure": 40,
            "nature": 55, "nightlife": 55, "history": 80, "art": 75,
            "shopping": 70, "wellness": 70, "sports": 45
        },
        "must_haves": {
            "accessibility_score": 90,
            "pet_friendly_score": 65,
            "family_friendly_score": 80,
            "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 105,
            "budget_min_7d": 550, "budget_max_7d": 850,
            "comfort_min_7d": 850, "comfort_max_7d": 1500,
            "premium_min_7d": 1500, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 7000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 15, "friends": 10, "pet": 5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 15},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [1, 2],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 65,
        "top_activities": [
            {"name": "Vieille ville Luxembourg", "emoji": "🏰", "category": "history"},
            {"name": "Casemates du Bock", "emoji": "🏛️", "category": "history"},
            {"name": "Moselle luxembourgeoise", "emoji": "🍷", "category": "food"},
            {"name": "Chateau de Vianden", "emoji": "🏰", "category": "history"},
            {"name": "Gastronomie etoilee", "emoji": "⭐", "category": "food"}
        ],
        "fallback_headlines": {
            "solo": "Luxembourg, elegance compacte en solo",
            "couple": "Luxembourg romantique et raffine",
            "family": "Luxembourg en famille, chateaux et nature",
            "friends": "Luxembourg entre amis, vins et culture",
            "pet": "Luxembourg avec votre compagnon"
        },
        "fallback_description": "Grand-Duche elegant, chateaux medievaux et gastronomie raffinee."
    },
    {
        "country_code": "LV",
        "country_name": "Lettonie",
        "flag_emoji": "🇱🇻",
        "region": "Europe",
        "subregion": "Northern Europe",
        "languages": ["Latvian"],
        "currency": "EUR",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 55,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 75, "food": 65, "beach": 40, "adventure": 55,
            "nature": 70, "nightlife": 65, "history": 80, "art": 80,
            "shopping": 55, "wellness": 65, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 75,
            "pet_friendly_score": 60,
            "family_friendly_score": 70,
            "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 300, "budget_max_7d": 480,
            "comfort_min_7d": 480, "comfort_max_7d": 850,
            "premium_min_7d": 850, "premium_max_7d": 1600,
            "luxury_min_7d": 1600, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [5, 6, 7, 8, 9],
        "avoid_months": [1, 2],
        "best_seasons": ["Printemps", "Ete"],
        "trending_score": 68,
        "top_activities": [
            {"name": "Riga Art Nouveau", "emoji": "🏛️", "category": "art"},
            {"name": "Vieille ville Riga", "emoji": "🏘️", "category": "history"},
            {"name": "Jurmala", "emoji": "🏖️", "category": "beach"},
            {"name": "Parc national Gauja", "emoji": "🌲", "category": "nature"},
            {"name": "Marche central Riga", "emoji": "🛒", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Lettonie, Art Nouveau et charme balte en solo",
            "couple": "Riga romantique et elegante",
            "family": "Lettonie en famille, plages et forets",
            "friends": "Riga entre amis, bars et culture",
            "pet": "Lettonie avec votre compagnon"
        },
        "fallback_description": "Riga Art Nouveau, charme balte et forets mysterieuses."
    },
    # ========================================================================
    # ASIA (12 countries) - Part 1
    # ========================================================================
    {
        "country_code": "CN",
        "country_name": "Chine",
        "flag_emoji": "🇨🇳",
        "region": "Asia",
        "subregion": "Eastern Asia",
        "languages": ["Mandarin Chinese"],
        "currency": "CNY",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 50,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 95, "food": 95, "beach": 45, "adventure": 70,
            "nature": 85, "nightlife": 65, "history": 98, "art": 85,
            "shopping": 80, "wellness": 75, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 65,
            "pet_friendly_score": 40,
            "family_friendly_score": 70,
            "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 350, "budget_max_7d": 600,
            "comfort_min_7d": 600, "comfort_max_7d": 1100,
            "premium_min_7d": 1100, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [4, 5, 9, 10],
        "avoid_months": [7, 8, 1, 2],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Grande Muraille", "emoji": "🏯", "category": "history"},
            {"name": "Cite Interdite", "emoji": "🏛️", "category": "history"},
            {"name": "Armee de terre cuite", "emoji": "🗿", "category": "history"},
            {"name": "Shanghai moderne", "emoji": "🌆", "category": "culture"},
            {"name": "Guilin et Li River", "emoji": "🏞️", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Chine, immersion millenaire en solo",
            "couple": "Chine romantique, empire et modernite",
            "family": "Chine en famille, merveilles du monde",
            "friends": "Chine entre amis, decouverte epique",
            "pet": "Chine avec votre compagnon"
        },
        "fallback_description": "Grande Muraille, Cite Interdite et 5000 ans d'histoire."
    },
    {
        "country_code": "HK",
        "country_name": "Hong Kong",
        "flag_emoji": "🇭🇰",
        "region": "Asia",
        "subregion": "Eastern Asia",
        "languages": ["Cantonese", "English"],
        "currency": "HKD",
        "style_scores": {
            "chill_vs_intense": 65,
            "city_vs_nature": 25,
            "eco_vs_luxury": 70,
            "tourist_vs_local": 40
        },
        "interest_scores": {
            "culture": 85, "food": 95, "beach": 45, "adventure": 50,
            "nature": 55, "nightlife": 85, "history": 70, "art": 75,
            "shopping": 95, "wellness": 70, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 90,
            "pet_friendly_score": 45,
            "family_friendly_score": 80,
            "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 95,
            "budget_min_7d": 500, "budget_max_7d": 850,
            "comfort_min_7d": 850, "comfort_max_7d": 1500,
            "premium_min_7d": 1500, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 20, "pet": -5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 15, "birthday": 20, "vacation": 5, "workation": 15},
        "best_months": [10, 11, 12, 3, 4],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Automne", "Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Victoria Peak", "emoji": "🏙️", "category": "culture"},
            {"name": "Street food", "emoji": "🍜", "category": "food"},
            {"name": "Shopping Kowloon", "emoji": "🛍️", "category": "shopping"},
            {"name": "Big Buddha Lantau", "emoji": "🗿", "category": "culture"},
            {"name": "Star Ferry", "emoji": "⛴️", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Hong Kong, metropole vibrante en solo",
            "couple": "Hong Kong romantique, skyline et dim sum",
            "family": "Hong Kong en famille, Disneyland et plus",
            "friends": "Hong Kong entre amis, shopping et rooftops",
            "pet": "Hong Kong avec votre compagnon"
        },
        "fallback_description": "Skyline iconique, street food legendaire et shopping sans fin."
    },
    {
        "country_code": "TW",
        "country_name": "Taiwan",
        "flag_emoji": "🇹🇼",
        "region": "Asia",
        "subregion": "Eastern Asia",
        "languages": ["Mandarin Chinese"],
        "currency": "TWD",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 55,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 85, "food": 95, "beach": 55, "adventure": 70,
            "nature": 80, "nightlife": 75, "history": 75, "art": 75,
            "shopping": 80, "wellness": 70, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 85,
            "pet_friendly_score": 55,
            "family_friendly_score": 85,
            "wifi_quality_score": 92
        },
        "budget": {
            "cost_of_living_index": 60,
            "budget_min_7d": 350, "budget_max_7d": 600,
            "comfort_min_7d": 600, "comfort_max_7d": 1100,
            "premium_min_7d": 1100, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 15, "friends": 20, "pet": 0},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 15, "vacation": 5, "workation": 20},
        "best_months": [3, 4, 5, 10, 11],
        "avoid_months": [6, 7, 8, 9],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Night markets", "emoji": "🌃", "category": "food"},
            {"name": "Taipei 101", "emoji": "🏙️", "category": "culture"},
            {"name": "Gorges de Taroko", "emoji": "🏞️", "category": "nature"},
            {"name": "Jiufen", "emoji": "🏮", "category": "culture"},
            {"name": "Sun Moon Lake", "emoji": "🌅", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Taiwan, paradis foodie en solo",
            "couple": "Taiwan romantique, temples et montagnes",
            "family": "Taiwan en famille, night markets et nature",
            "friends": "Taiwan entre amis, street food et fete",
            "pet": "Taiwan avec votre compagnon"
        },
        "fallback_description": "Night markets legendaires, montagnes et culture chinoise moderne."
    },
    {
        "country_code": "LA",
        "country_name": "Laos",
        "flag_emoji": "🇱🇦",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Lao"],
        "currency": "LAK",
        "style_scores": {
            "chill_vs_intense": 30,
            "city_vs_nature": 70,
            "eco_vs_luxury": 30,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 85, "food": 70, "beach": 20, "adventure": 70,
            "nature": 85, "nightlife": 40, "history": 80, "art": 60,
            "shopping": 45, "wellness": 65, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 45,
            "pet_friendly_score": 40,
            "family_friendly_score": 60,
            "wifi_quality_score": 60
        },
        "budget": {
            "cost_of_living_index": 32,
            "budget_min_7d": 180, "budget_max_7d": 320,
            "comfort_min_7d": 320, "comfort_max_7d": 600,
            "premium_min_7d": 600, "premium_max_7d": 1200,
            "luxury_min_7d": 1200, "luxury_max_7d": 3000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 10, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [11, 12, 1, 2, 3],
        "avoid_months": [5, 6, 7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Luang Prabang", "emoji": "🛕", "category": "culture"},
            {"name": "Cascades Kuang Si", "emoji": "💧", "category": "nature"},
            {"name": "Mekong River", "emoji": "🚣", "category": "adventure"},
            {"name": "Offrandes aux moines", "emoji": "🙏", "category": "culture"},
            {"name": "Vang Vieng", "emoji": "🏞️", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Laos, serenite et spiritualite en solo",
            "couple": "Laos romantique, Mekong et temples",
            "family": "Laos en famille, aventure douce",
            "friends": "Laos entre amis, kayak et temples",
            "pet": "Laos avec votre compagnon"
        },
        "fallback_description": "Luang Prabang sacre, Mekong paisible et spiritualite bouddhiste."
    },
    {
        "country_code": "MM",
        "country_name": "Myanmar",
        "flag_emoji": "🇲🇲",
        "region": "Asia",
        "subregion": "South-Eastern Asia",
        "languages": ["Burmese"],
        "currency": "MMK",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 65,
            "eco_vs_luxury": 30,
            "tourist_vs_local": 75
        },
        "interest_scores": {
            "culture": 95, "food": 70, "beach": 50, "adventure": 65,
            "nature": 75, "nightlife": 30, "history": 90, "art": 70,
            "shopping": 50, "wellness": 60, "sports": 40
        },
        "must_haves": {
            "accessibility_score": 35,
            "pet_friendly_score": 30,
            "family_friendly_score": 55,
            "wifi_quality_score": 50
        },
        "budget": {
            "cost_of_living_index": 30,
            "budget_min_7d": 170, "budget_max_7d": 300,
            "comfort_min_7d": 300, "comfort_max_7d": 550,
            "premium_min_7d": 550, "premium_max_7d": 1100,
            "luxury_min_7d": 1100, "luxury_max_7d": 2800
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 5, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 5, "vacation": 5, "workation": 0},
        "best_months": [11, 12, 1, 2],
        "avoid_months": [5, 6, 7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 65,
        "top_activities": [
            {"name": "Temples de Bagan", "emoji": "🛕", "category": "history"},
            {"name": "Lac Inle", "emoji": "🚣", "category": "nature"},
            {"name": "Pagode Shwedagon", "emoji": "✨", "category": "culture"},
            {"name": "Mandalay", "emoji": "🏛️", "category": "culture"},
            {"name": "Rocher d'Or", "emoji": "🪨", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Myanmar, temples milleniares en solo",
            "couple": "Bagan romantique au lever du soleil",
            "family": "Myanmar en famille, decouverte culturelle",
            "friends": "Myanmar entre amis, aventure spirituelle",
            "pet": "Myanmar spirituel"
        },
        "fallback_description": "Temples de Bagan, pagodes dorees et culture birmane authentique."
    },
    {
        "country_code": "UZ",
        "country_name": "Ouzbekistan",
        "flag_emoji": "🇺🇿",
        "region": "Asia",
        "subregion": "Central Asia",
        "languages": ["Uzbek"],
        "currency": "UZS",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 45,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 95, "food": 75, "beach": 10, "adventure": 60,
            "nature": 60, "nightlife": 35, "history": 98, "art": 90,
            "shopping": 65, "wellness": 50, "sports": 35
        },
        "must_haves": {
            "accessibility_score": 50,
            "pet_friendly_score": 35,
            "family_friendly_score": 65,
            "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 200, "budget_max_7d": 350,
            "comfort_min_7d": 350, "comfort_max_7d": 650,
            "premium_min_7d": 650, "premium_max_7d": 1300,
            "luxury_min_7d": 1300, "luxury_max_7d": 3500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [4, 5, 9, 10],
        "avoid_months": [6, 7, 8, 12, 1, 2],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Samarcande", "emoji": "🕌", "category": "history"},
            {"name": "Boukhara", "emoji": "🏛️", "category": "history"},
            {"name": "Khiva", "emoji": "🏰", "category": "history"},
            {"name": "Route de la Soie", "emoji": "🐫", "category": "adventure"},
            {"name": "Artisanat ouzbek", "emoji": "🎨", "category": "art"}
        ],
        "fallback_headlines": {
            "solo": "Ouzbekistan, Route de la Soie en solo",
            "couple": "Samarcande romantique et legendaire",
            "family": "Ouzbekistan en famille, histoire vivante",
            "friends": "Ouzbekistan entre amis, epopee culturelle",
            "pet": "Ouzbekistan historique"
        },
        "fallback_description": "Samarcande mythique, Route de la Soie et mosaiques eblouissantes."
    },
    {
        "country_code": "KZ",
        "country_name": "Kazakhstan",
        "flag_emoji": "🇰🇿",
        "region": "Asia",
        "subregion": "Central Asia",
        "languages": ["Kazakh", "Russian"],
        "currency": "KZT",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 70,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 70, "food": 60, "beach": 15, "adventure": 75,
            "nature": 85, "nightlife": 55, "history": 70, "art": 60,
            "shopping": 55, "wellness": 50, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 55,
            "pet_friendly_score": 40,
            "family_friendly_score": 60,
            "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 280, "budget_max_7d": 480,
            "comfort_min_7d": 480, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 10, "family": 10, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [5, 6, 9],
        "avoid_months": [12, 1, 2, 7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 68,
        "top_activities": [
            {"name": "Almaty", "emoji": "🏙️", "category": "culture"},
            {"name": "Charyn Canyon", "emoji": "🏜️", "category": "nature"},
            {"name": "Lac Big Almaty", "emoji": "🏞️", "category": "nature"},
            {"name": "Steppes kazakh", "emoji": "🌾", "category": "nature"},
            {"name": "Nur-Sultan moderne", "emoji": "🏗️", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Kazakhstan, steppes infinies en solo",
            "couple": "Kazakhstan romantique et sauvage",
            "family": "Kazakhstan en famille, nature et culture",
            "friends": "Kazakhstan entre amis, aventure unique",
            "pet": "Kazakhstan avec votre compagnon"
        },
        "fallback_description": "Steppes infinies, canyons spectaculaires et modernite futuriste."
    },
    {
        "country_code": "SA",
        "country_name": "Arabie Saoudite",
        "flag_emoji": "🇸🇦",
        "region": "Asia",
        "subregion": "Western Asia",
        "languages": ["Arabic"],
        "currency": "SAR",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 55,
            "eco_vs_luxury": 75,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 90, "food": 75, "beach": 60, "adventure": 70,
            "nature": 75, "nightlife": 30, "history": 95, "art": 70,
            "shopping": 85, "wellness": 65, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 65,
            "pet_friendly_score": 25,
            "family_friendly_score": 70,
            "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 70,
            "budget_min_7d": 450, "budget_max_7d": 750,
            "comfort_min_7d": 750, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 15, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [11, 12, 1, 2, 3],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Al-Ula et Hegra", "emoji": "🏛️", "category": "history"},
            {"name": "Riyad moderne", "emoji": "🏙️", "category": "culture"},
            {"name": "Mer Rouge plongee", "emoji": "🤿", "category": "adventure"},
            {"name": "Desert du Rub al-Khali", "emoji": "🏜️", "category": "nature"},
            {"name": "Jeddah historique", "emoji": "🕌", "category": "history"}
        ],
        "fallback_headlines": {
            "solo": "Arabie Saoudite, tresor cache en solo",
            "couple": "Arabie Saoudite romantique et mysterieuse",
            "family": "Arabie Saoudite en famille, decouverte",
            "friends": "Arabie Saoudite entre amis, aventure",
            "pet": "Arabie Saoudite majestueuse"
        },
        "fallback_description": "Al-Ula mysterieuse, desert majestueux et patrimoine millenaire."
    },
    {
        "country_code": "JO",
        "country_name": "Jordanie",
        "flag_emoji": "🇯🇴",
        "region": "Asia",
        "subregion": "Western Asia",
        "languages": ["Arabic"],
        "currency": "JOD",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 70,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 90, "food": 80, "beach": 55, "adventure": 85,
            "nature": 85, "nightlife": 40, "history": 98, "art": 65,
            "shopping": 60, "wellness": 80, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 60,
            "pet_friendly_score": 35,
            "family_friendly_score": 75,
            "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 350, "budget_max_7d": 600,
            "comfort_min_7d": 600, "comfort_max_7d": 1100,
            "premium_min_7d": 1100, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 5500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [3, 4, 5, 10, 11],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Petra", "emoji": "🏛️", "category": "history"},
            {"name": "Wadi Rum", "emoji": "🏜️", "category": "adventure"},
            {"name": "Mer Morte", "emoji": "🌊", "category": "wellness"},
            {"name": "Amman", "emoji": "🕌", "category": "culture"},
            {"name": "Aqaba plongee", "emoji": "🤿", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Jordanie, Petra et desert en solo",
            "couple": "Jordanie romantique, merveilles antiques",
            "family": "Jordanie en famille, Indiana Jones style",
            "friends": "Jordanie entre amis, aventure epique",
            "pet": "Jordanie majestueuse"
        },
        "fallback_description": "Petra rose, Wadi Rum lunaire et Mer Morte therapeutique."
    },
    {
        "country_code": "OM",
        "country_name": "Oman",
        "flag_emoji": "🇴🇲",
        "region": "Asia",
        "subregion": "Western Asia",
        "languages": ["Arabic"],
        "currency": "OMR",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 70,
            "eco_vs_luxury": 65,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 85, "food": 70, "beach": 80, "adventure": 85,
            "nature": 90, "nightlife": 25, "history": 80, "art": 60,
            "shopping": 60, "wellness": 75, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 65,
            "pet_friendly_score": 30,
            "family_friendly_score": 80,
            "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 65,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1300,
            "premium_min_7d": 1300, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 6500
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [10, 11, 12, 1, 2, 3],
        "avoid_months": [5, 6, 7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Fjords de Musandam", "emoji": "🏞️", "category": "nature"},
            {"name": "Desert Wahiba Sands", "emoji": "🏜️", "category": "adventure"},
            {"name": "Muscat", "emoji": "🕌", "category": "culture"},
            {"name": "Wadis et oasis", "emoji": "🌴", "category": "nature"},
            {"name": "Plongee a Oman", "emoji": "🤿", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Oman, authenticite et nature en solo",
            "couple": "Oman romantique, fjords et desert",
            "family": "Oman en famille, aventure securisee",
            "friends": "Oman entre amis, road trip epique",
            "pet": "Oman authentique"
        },
        "fallback_description": "Fjords arabes, desert dore et authenticite preservee."
    },
    {
        "country_code": "QA",
        "country_name": "Qatar",
        "flag_emoji": "🇶🇦",
        "region": "Asia",
        "subregion": "Western Asia",
        "languages": ["Arabic"],
        "currency": "QAR",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 30,
            "eco_vs_luxury": 85,
            "tourist_vs_local": 40
        },
        "interest_scores": {
            "culture": 80, "food": 80, "beach": 70, "adventure": 55,
            "nature": 45, "nightlife": 50, "history": 65, "art": 85,
            "shopping": 90, "wellness": 80, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 85,
            "pet_friendly_score": 30,
            "family_friendly_score": 85,
            "wifi_quality_score": 95
        },
        "budget": {
            "cost_of_living_index": 85,
            "budget_min_7d": 500, "budget_max_7d": 850,
            "comfort_min_7d": 850, "comfort_max_7d": 1600,
            "premium_min_7d": 1600, "premium_max_7d": 3200,
            "luxury_min_7d": 3200, "luxury_max_7d": 10000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 20, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [11, 12, 1, 2, 3],
        "avoid_months": [5, 6, 7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Doha moderne", "emoji": "🏙️", "category": "culture"},
            {"name": "Musee d'Art Islamique", "emoji": "🏛️", "category": "art"},
            {"name": "Souq Waqif", "emoji": "🛒", "category": "shopping"},
            {"name": "Desert safari", "emoji": "🏜️", "category": "adventure"},
            {"name": "The Pearl Qatar", "emoji": "💎", "category": "shopping"}
        ],
        "fallback_headlines": {
            "solo": "Qatar, luxe et culture en solo",
            "couple": "Qatar romantique et sophistique",
            "family": "Qatar en famille, musees et plages",
            "friends": "Qatar entre amis, shopping et brunch",
            "pet": "Qatar moderne"
        },
        "fallback_description": "Architecture futuriste, musees world-class et luxe absolu."
    },
    {
        "country_code": "BH",
        "country_name": "Bahrein",
        "flag_emoji": "🇧🇭",
        "region": "Asia",
        "subregion": "Western Asia",
        "languages": ["Arabic"],
        "currency": "BHD",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 30,
            "eco_vs_luxury": 65,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 75, "food": 75, "beach": 65, "adventure": 45,
            "nature": 35, "nightlife": 60, "history": 80, "art": 65,
            "shopping": 80, "wellness": 70, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 80,
            "pet_friendly_score": 35,
            "family_friendly_score": 75,
            "wifi_quality_score": 90
        },
        "budget": {
            "cost_of_living_index": 70,
            "budget_min_7d": 400, "budget_max_7d": 650,
            "comfort_min_7d": 650, "comfort_max_7d": 1200,
            "premium_min_7d": 1200, "premium_max_7d": 2400,
            "luxury_min_7d": 2400, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [11, 12, 1, 2, 3],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Hiver"],
        "trending_score": 68,
        "top_activities": [
            {"name": "Manama", "emoji": "🏙️", "category": "culture"},
            {"name": "Fort de Bahrein", "emoji": "🏰", "category": "history"},
            {"name": "Musee national", "emoji": "🏛️", "category": "history"},
            {"name": "F1 Grand Prix", "emoji": "🏎️", "category": "sports"},
            {"name": "Souks traditionnels", "emoji": "🛒", "category": "shopping"}
        ],
        "fallback_headlines": {
            "solo": "Bahrein, perle du Golfe en solo",
            "couple": "Bahrein romantique et historique",
            "family": "Bahrein en famille, culture et plages",
            "friends": "Bahrein entre amis, F1 et brunch",
            "pet": "Bahrein compact"
        },
        "fallback_description": "Ile historique, melange de tradition et modernite du Golfe."
    },
    # ========================================================================
    # AMERICAS (11 countries)
    # ========================================================================
    {
        "country_code": "CO",
        "country_name": "Colombie",
        "flag_emoji": "🇨🇴",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Spanish"],
        "currency": "COP",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 55,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 75, "adventure": 75,
            "nature": 85, "nightlife": 80, "history": 80, "art": 75,
            "shopping": 65, "wellness": 60, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 55,
            "pet_friendly_score": 50,
            "family_friendly_score": 70,
            "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 40,
            "budget_min_7d": 250, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 850,
            "premium_min_7d": 850, "premium_max_7d": 1600,
            "luxury_min_7d": 1600, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 20, "pet": 0},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 15, "vacation": 5, "workation": 15},
        "best_months": [12, 1, 2, 3, 7, 8],
        "avoid_months": [4, 5, 10, 11],
        "best_seasons": ["Hiver", "Ete"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Cartagena historique", "emoji": "🏛️", "category": "history"},
            {"name": "Region du cafe", "emoji": "☕", "category": "food"},
            {"name": "Medellin", "emoji": "🌆", "category": "culture"},
            {"name": "Plages des Caraibes", "emoji": "🏖️", "category": "beach"},
            {"name": "Ciudad Perdida", "emoji": "🏛️", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Colombie, cafe et aventure en solo",
            "couple": "Cartagena romantique et Caraibes",
            "family": "Colombie en famille, couleurs et nature",
            "friends": "Colombie entre amis, salsa et fiesta",
            "pet": "Colombie avec votre compagnon"
        },
        "fallback_description": "Cafe, Caraibes, histoire coloniale et biodiversite exceptionnelle."
    },
    {
        "country_code": "EC",
        "country_name": "Equateur",
        "flag_emoji": "🇪🇨",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Spanish"],
        "currency": "USD",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 80,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 80, "food": 70, "beach": 60, "adventure": 90,
            "nature": 98, "nightlife": 50, "history": 75, "art": 65,
            "shopping": 50, "wellness": 60, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 50,
            "pet_friendly_score": 45,
            "family_friendly_score": 75,
            "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 42,
            "budget_min_7d": 280, "budget_max_7d": 480,
            "comfort_min_7d": 480, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [6, 7, 8, 9, 12, 1],
        "avoid_months": [2, 3, 4, 5],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Iles Galapagos", "emoji": "🐢", "category": "nature"},
            {"name": "Quito colonial", "emoji": "🏛️", "category": "history"},
            {"name": "Amazonie equatorienne", "emoji": "🌳", "category": "nature"},
            {"name": "Avenue des volcans", "emoji": "🌋", "category": "adventure"},
            {"name": "Marches indigenes", "emoji": "🎨", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Equateur, Galapagos et Amazonie en solo",
            "couple": "Equateur romantique, nature unique",
            "family": "Equateur en famille, animaux et volcans",
            "friends": "Equateur entre amis, aventure totale",
            "pet": "Equateur nature"
        },
        "fallback_description": "Galapagos uniques, Amazonie et volcans des Andes."
    },
    {
        "country_code": "BO",
        "country_name": "Bolivie",
        "flag_emoji": "🇧🇴",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Spanish"],
        "currency": "BOB",
        "style_scores": {
            "chill_vs_intense": 60,
            "city_vs_nature": 80,
            "eco_vs_luxury": 25,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 85, "food": 60, "beach": 15, "adventure": 95,
            "nature": 95, "nightlife": 45, "history": 80, "art": 65,
            "shopping": 50, "wellness": 45, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 35,
            "pet_friendly_score": 35,
            "family_friendly_score": 55,
            "wifi_quality_score": 55
        },
        "budget": {
            "cost_of_living_index": 32,
            "budget_min_7d": 180, "budget_max_7d": 320,
            "comfort_min_7d": 320, "comfort_max_7d": 600,
            "premium_min_7d": 600, "premium_max_7d": 1200,
            "luxury_min_7d": 1200, "luxury_max_7d": 3000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 5, "friends": 20, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 0},
        "best_months": [5, 6, 7, 8, 9, 10],
        "avoid_months": [12, 1, 2, 3],
        "best_seasons": ["Hiver"],
        "trending_score": 80,
        "top_activities": [
            {"name": "Salar d'Uyuni", "emoji": "🪞", "category": "nature"},
            {"name": "La Paz", "emoji": "🏔️", "category": "culture"},
            {"name": "Lac Titicaca", "emoji": "🌊", "category": "nature"},
            {"name": "Route de la Mort", "emoji": "🚴", "category": "adventure"},
            {"name": "Sucre colonial", "emoji": "🏛️", "category": "history"}
        ],
        "fallback_headlines": {
            "solo": "Bolivie, Uyuni et altitude en solo",
            "couple": "Bolivie romantique, miroir du ciel",
            "family": "Bolivie en famille, aventure altitude",
            "friends": "Bolivie entre amis, road trip extreme",
            "pet": "Bolivie sauvage"
        },
        "fallback_description": "Salar d'Uyuni magique, Lac Titicaca et aventure andine."
    },
    {
        "country_code": "UY",
        "country_name": "Uruguay",
        "flag_emoji": "🇺🇾",
        "region": "Americas",
        "subregion": "South America",
        "languages": ["Spanish"],
        "currency": "UYU",
        "style_scores": {
            "chill_vs_intense": 30,
            "city_vs_nature": 50,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 60
        },
        "interest_scores": {
            "culture": 75, "food": 85, "beach": 80, "adventure": 45,
            "nature": 65, "nightlife": 70, "history": 70, "art": 70,
            "shopping": 55, "wellness": 70, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 75,
            "pet_friendly_score": 70,
            "family_friendly_score": 85,
            "wifi_quality_score": 85
        },
        "budget": {
            "cost_of_living_index": 60,
            "budget_min_7d": 350, "budget_max_7d": 580,
            "comfort_min_7d": 580, "comfort_max_7d": 1050,
            "premium_min_7d": 1050, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 20, "friends": 15, "pet": 15},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 10, "workation": 15},
        "best_months": [12, 1, 2, 3],
        "avoid_months": [6, 7, 8],
        "best_seasons": ["Ete"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Montevideo", "emoji": "🏙️", "category": "culture"},
            {"name": "Punta del Este", "emoji": "🏖️", "category": "beach"},
            {"name": "Colonia del Sacramento", "emoji": "🏛️", "category": "history"},
            {"name": "Vignobles uruguayens", "emoji": "🍷", "category": "food"},
            {"name": "Estancias", "emoji": "🐴", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Uruguay, tranquillite et vins en solo",
            "couple": "Uruguay romantique, plages et vignobles",
            "family": "Uruguay en famille, securite et plages",
            "friends": "Uruguay entre amis, Punta del Este",
            "pet": "Uruguay pet-friendly"
        },
        "fallback_description": "Plages paisibles, vins tannat et douceur de vivre sud-americaine."
    },
    {
        "country_code": "GT",
        "country_name": "Guatemala",
        "flag_emoji": "🇬🇹",
        "region": "Americas",
        "subregion": "Central America",
        "languages": ["Spanish"],
        "currency": "GTQ",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 70,
            "eco_vs_luxury": 30,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 95, "food": 70, "beach": 50, "adventure": 80,
            "nature": 85, "nightlife": 50, "history": 95, "art": 80,
            "shopping": 65, "wellness": 55, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 45,
            "pet_friendly_score": 40,
            "family_friendly_score": 65,
            "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 200, "budget_max_7d": 380,
            "comfort_min_7d": 380, "comfort_max_7d": 700,
            "premium_min_7d": 700, "premium_max_7d": 1400,
            "luxury_min_7d": 1400, "luxury_max_7d": 3500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [11, 12, 1, 2, 3, 4],
        "avoid_months": [6, 7, 8, 9, 10],
        "best_seasons": ["Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Tikal Maya", "emoji": "🏛️", "category": "history"},
            {"name": "Antigua Guatemala", "emoji": "⛪", "category": "culture"},
            {"name": "Lac Atitlan", "emoji": "🌋", "category": "nature"},
            {"name": "Marches indigenes", "emoji": "🎨", "category": "culture"},
            {"name": "Volcans actifs", "emoji": "🌋", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Guatemala, Maya et volcans en solo",
            "couple": "Guatemala romantique, couleurs et mystere",
            "family": "Guatemala en famille, histoire vivante",
            "friends": "Guatemala entre amis, aventure Maya",
            "pet": "Guatemala colore"
        },
        "fallback_description": "Ruines Maya de Tikal, volcans et culture indigene vibrante."
    },
    {
        "country_code": "CU",
        "country_name": "Cuba",
        "flag_emoji": "🇨🇺",
        "region": "Americas",
        "subregion": "Caribbean",
        "languages": ["Spanish"],
        "currency": "CUP",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 45,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 95, "food": 70, "beach": 80, "adventure": 55,
            "nature": 65, "nightlife": 85, "history": 90, "art": 85,
            "shopping": 45, "wellness": 55, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 50,
            "pet_friendly_score": 35,
            "family_friendly_score": 70,
            "wifi_quality_score": 35
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 1700,
            "luxury_min_7d": 1700, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 10, "friends": 20, "pet": -10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 15, "vacation": 5, "workation": 0},
        "best_months": [11, 12, 1, 2, 3, 4],
        "avoid_months": [8, 9, 10],
        "best_seasons": ["Hiver"],
        "trending_score": 80,
        "top_activities": [
            {"name": "La Havane vintage", "emoji": "🚗", "category": "culture"},
            {"name": "Musique et salsa", "emoji": "💃", "category": "nightlife"},
            {"name": "Trinidad colonial", "emoji": "🏛️", "category": "history"},
            {"name": "Plages de Varadero", "emoji": "🏖️", "category": "beach"},
            {"name": "Vallee de Vinales", "emoji": "🌳", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Cuba, voyage dans le temps en solo",
            "couple": "Cuba romantique, salsa et mojitos",
            "family": "Cuba en famille, histoire et plages",
            "friends": "Cuba entre amis, musique et fete",
            "pet": "Cuba authentique"
        },
        "fallback_description": "Voitures vintage, salsa, cigares et charme retro unique."
    },
    {
        "country_code": "PA",
        "country_name": "Panama",
        "flag_emoji": "🇵🇦",
        "region": "Americas",
        "subregion": "Central America",
        "languages": ["Spanish"],
        "currency": "PAB",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 60,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 70, "food": 70, "beach": 85, "adventure": 75,
            "nature": 85, "nightlife": 70, "history": 70, "art": 55,
            "shopping": 75, "wellness": 65, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 70,
            "pet_friendly_score": 50,
            "family_friendly_score": 80,
            "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 350, "budget_max_7d": 580,
            "comfort_min_7d": 580, "comfort_max_7d": 1050,
            "premium_min_7d": 1050, "premium_max_7d": 2100,
            "luxury_min_7d": 2100, "luxury_max_7d": 5500
        },
        "travel_style_bonuses": {"solo": 10, "couple": 15, "family": 20, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 10, "workation": 15},
        "best_months": [12, 1, 2, 3, 4],
        "avoid_months": [9, 10, 11],
        "best_seasons": ["Hiver"],
        "trending_score": 76,
        "top_activities": [
            {"name": "Canal de Panama", "emoji": "🚢", "category": "history"},
            {"name": "San Blas Islands", "emoji": "🏝️", "category": "beach"},
            {"name": "Panama City", "emoji": "🏙️", "category": "culture"},
            {"name": "Bocas del Toro", "emoji": "🏖️", "category": "beach"},
            {"name": "Foret tropicale", "emoji": "🌳", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Panama, canal et iles en solo",
            "couple": "Panama romantique, San Blas paradisiaque",
            "family": "Panama en famille, canal et plages",
            "friends": "Panama entre amis, iles et fete",
            "pet": "Panama tropical"
        },
        "fallback_description": "Canal iconique, iles San Blas et biodiversite exceptionnelle."
    },
    {
        "country_code": "DO",
        "country_name": "Republique Dominicaine",
        "flag_emoji": "🇩🇴",
        "region": "Americas",
        "subregion": "Caribbean",
        "languages": ["Spanish"],
        "currency": "DOP",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 55,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 40
        },
        "interest_scores": {
            "culture": 70, "food": 70, "beach": 95, "adventure": 60,
            "nature": 70, "nightlife": 80, "history": 65, "art": 55,
            "shopping": 60, "wellness": 80, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 75,
            "pet_friendly_score": 50,
            "family_friendly_score": 90,
            "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 950,
            "premium_min_7d": 950, "premium_max_7d": 1900,
            "luxury_min_7d": 1900, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 25, "friends": 20, "pet": 0},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 15, "vacation": 15, "workation": 5},
        "best_months": [12, 1, 2, 3, 4],
        "avoid_months": [8, 9, 10],
        "best_seasons": ["Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Punta Cana", "emoji": "🏖️", "category": "beach"},
            {"name": "Santo Domingo", "emoji": "🏛️", "category": "history"},
            {"name": "Samana baleines", "emoji": "🐋", "category": "nature"},
            {"name": "Resorts all-inclusive", "emoji": "🏨", "category": "wellness"},
            {"name": "Golf", "emoji": "⛳", "category": "sports"}
        ],
        "fallback_headlines": {
            "solo": "Dominicaine, plages et merengue en solo",
            "couple": "Dominicaine romantique, paradis tropical",
            "family": "Dominicaine en famille, all-inclusive ideal",
            "friends": "Dominicaine entre amis, plage et fete",
            "pet": "Dominicaine tropicale"
        },
        "fallback_description": "Plages de reve, resorts all-inclusive et merengue."
    },
    {
        "country_code": "JM",
        "country_name": "Jamaique",
        "flag_emoji": "🇯🇲",
        "region": "Americas",
        "subregion": "Caribbean",
        "languages": ["English"],
        "currency": "JMD",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 55,
            "eco_vs_luxury": 50,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 85, "food": 80, "beach": 90, "adventure": 65,
            "nature": 75, "nightlife": 85, "history": 65, "art": 75,
            "shopping": 55, "wellness": 75, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 65,
            "pet_friendly_score": 45,
            "family_friendly_score": 75,
            "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 350, "budget_max_7d": 600,
            "comfort_min_7d": 600, "comfort_max_7d": 1100,
            "premium_min_7d": 1100, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 20, "pet": 0},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 15, "vacation": 10, "workation": 5},
        "best_months": [12, 1, 2, 3, 4],
        "avoid_months": [8, 9, 10],
        "best_seasons": ["Hiver"],
        "trending_score": 76,
        "top_activities": [
            {"name": "Plages de Negril", "emoji": "🏖️", "category": "beach"},
            {"name": "Reggae et Bob Marley", "emoji": "🎵", "category": "culture"},
            {"name": "Blue Mountains", "emoji": "⛰️", "category": "nature"},
            {"name": "Cuisine jerk", "emoji": "🍗", "category": "food"},
            {"name": "Dunn's River Falls", "emoji": "💧", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Jamaique, reggae et plages en solo",
            "couple": "Jamaique romantique, irie vibes",
            "family": "Jamaique en famille, nature et culture",
            "friends": "Jamaique entre amis, One Love",
            "pet": "Jamaique decontractee"
        },
        "fallback_description": "Reggae, plages paradisiaques et vibes irie authentiques."
    },
    {
        "country_code": "HN",
        "country_name": "Honduras",
        "flag_emoji": "🇭🇳",
        "region": "Americas",
        "subregion": "Central America",
        "languages": ["Spanish"],
        "currency": "HNL",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 75,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 70, "food": 60, "beach": 80, "adventure": 85,
            "nature": 85, "nightlife": 45, "history": 80, "art": 50,
            "shopping": 40, "wellness": 50, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 45,
            "pet_friendly_score": 40,
            "family_friendly_score": 60,
            "wifi_quality_score": 60
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 200, "budget_max_7d": 380,
            "comfort_min_7d": 380, "comfort_max_7d": 700,
            "premium_min_7d": 700, "premium_max_7d": 1400,
            "luxury_min_7d": 1400, "luxury_max_7d": 3500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [1, 2, 3, 4],
        "avoid_months": [9, 10, 11],
        "best_seasons": ["Hiver"],
        "trending_score": 68,
        "top_activities": [
            {"name": "Roatan plongee", "emoji": "🤿", "category": "adventure"},
            {"name": "Ruines de Copan", "emoji": "🏛️", "category": "history"},
            {"name": "Bay Islands", "emoji": "🏝️", "category": "beach"},
            {"name": "Recif corallien", "emoji": "🐠", "category": "nature"},
            {"name": "Jungle et faune", "emoji": "🦜", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Honduras, plongee et Maya en solo",
            "couple": "Honduras romantique, Roatan et recifs",
            "family": "Honduras en famille, nature et histoire",
            "friends": "Honduras entre amis, plongee et aventure",
            "pet": "Honduras sauvage"
        },
        "fallback_description": "Roatan paradisiaque, ruines Maya de Copan et recif corallien."
    },
    {
        "country_code": "NI",
        "country_name": "Nicaragua",
        "flag_emoji": "🇳🇮",
        "region": "Americas",
        "subregion": "Central America",
        "languages": ["Spanish"],
        "currency": "NIO",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 70,
            "eco_vs_luxury": 30,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 75, "food": 60, "beach": 70, "adventure": 80,
            "nature": 85, "nightlife": 50, "history": 75, "art": 60,
            "shopping": 45, "wellness": 55, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 45,
            "pet_friendly_score": 40,
            "family_friendly_score": 60,
            "wifi_quality_score": 60
        },
        "budget": {
            "cost_of_living_index": 32,
            "budget_min_7d": 180, "budget_max_7d": 320,
            "comfort_min_7d": 320, "comfort_max_7d": 600,
            "premium_min_7d": 600, "premium_max_7d": 1200,
            "luxury_min_7d": 1200, "luxury_max_7d": 3000
        },
        "travel_style_bonuses": {"solo": 20, "couple": 15, "family": 10, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [12, 1, 2, 3, 4],
        "avoid_months": [9, 10, 11],
        "best_seasons": ["Hiver"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Granada coloniale", "emoji": "🏛️", "category": "history"},
            {"name": "Volcan Masaya", "emoji": "🌋", "category": "adventure"},
            {"name": "Lac Nicaragua", "emoji": "🌊", "category": "nature"},
            {"name": "Ile d'Ometepe", "emoji": "🏝️", "category": "nature"},
            {"name": "Surf San Juan", "emoji": "🏄", "category": "sports"}
        ],
        "fallback_headlines": {
            "solo": "Nicaragua, volcans et lacs en solo",
            "couple": "Nicaragua romantique, nature sauvage",
            "family": "Nicaragua en famille, aventure budget",
            "friends": "Nicaragua entre amis, surf et volcans",
            "pet": "Nicaragua authentique"
        },
        "fallback_description": "Volcans actifs, lacs immenses et charme colonial budget."
    },
    # ========================================================================
    # AFRICA (11 countries)
    # ========================================================================
    {
        "country_code": "GH",
        "country_name": "Ghana",
        "flag_emoji": "🇬🇭",
        "region": "Africa",
        "subregion": "Western Africa",
        "languages": ["English"],
        "currency": "GHS",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 50,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 90, "food": 75, "beach": 60, "adventure": 60,
            "nature": 70, "nightlife": 70, "history": 90, "art": 75,
            "shopping": 65, "wellness": 50, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 50,
            "pet_friendly_score": 40,
            "family_friendly_score": 70,
            "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 42,
            "budget_min_7d": 280, "budget_max_7d": 480,
            "comfort_min_7d": 480, "comfort_max_7d": 900,
            "premium_min_7d": 900, "premium_max_7d": 1800,
            "luxury_min_7d": 1800, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 10, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [11, 12, 1, 2, 3],
        "avoid_months": [5, 6, 7],
        "best_seasons": ["Hiver"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Accra vibrante", "emoji": "🏙️", "category": "culture"},
            {"name": "Chateaux d'esclaves", "emoji": "🏰", "category": "history"},
            {"name": "Cape Coast", "emoji": "🏛️", "category": "history"},
            {"name": "Parc national Kakum", "emoji": "🌳", "category": "nature"},
            {"name": "Marches artisanaux", "emoji": "🎨", "category": "shopping"}
        ],
        "fallback_headlines": {
            "solo": "Ghana, histoire et accueil en solo",
            "couple": "Ghana romantique, culture et plages",
            "family": "Ghana en famille, heritage africain",
            "friends": "Ghana entre amis, Accra vibrante",
            "pet": "Ghana chaleureux"
        },
        "fallback_description": "Hospitalite legendaire, histoire de l'esclavage et culture vibrante."
    },
    {
        "country_code": "SN",
        "country_name": "Senegal",
        "flag_emoji": "🇸🇳",
        "region": "Africa",
        "subregion": "Western Africa",
        "languages": ["French"],
        "currency": "XOF",
        "style_scores": {
            "chill_vs_intense": 40,
            "city_vs_nature": 50,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 90, "food": 80, "beach": 75, "adventure": 60,
            "nature": 70, "nightlife": 75, "history": 80, "art": 85,
            "shopping": 70, "wellness": 55, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 55,
            "pet_friendly_score": 45,
            "family_friendly_score": 75,
            "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 45,
            "budget_min_7d": 300, "budget_max_7d": 500,
            "comfort_min_7d": 500, "comfort_max_7d": 950,
            "premium_min_7d": 950, "premium_max_7d": 1900,
            "luxury_min_7d": 1900, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 15, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [11, 12, 1, 2, 3, 4],
        "avoid_months": [7, 8, 9],
        "best_seasons": ["Hiver"],
        "trending_score": 74,
        "top_activities": [
            {"name": "Dakar", "emoji": "🏙️", "category": "culture"},
            {"name": "Ile de Goree", "emoji": "🏛️", "category": "history"},
            {"name": "Lac Rose", "emoji": "🌸", "category": "nature"},
            {"name": "Musique senegalaise", "emoji": "🎵", "category": "culture"},
            {"name": "Saint-Louis colonial", "emoji": "🏛️", "category": "history"}
        ],
        "fallback_headlines": {
            "solo": "Senegal, teranga et musique en solo",
            "couple": "Senegal romantique, Goree et plages",
            "family": "Senegal en famille, accueil africain",
            "friends": "Senegal entre amis, Dakar vibrante",
            "pet": "Senegal accueillant"
        },
        "fallback_description": "Teranga legendaire, Ile de Goree et musique senegalaise."
    },
    {
        "country_code": "RW",
        "country_name": "Rwanda",
        "flag_emoji": "🇷🇼",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["Kinyarwanda", "French", "English"],
        "currency": "RWF",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 75,
            "eco_vs_luxury": 60,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 80, "food": 60, "beach": 20, "adventure": 85,
            "nature": 95, "nightlife": 45, "history": 85, "art": 60,
            "shopping": 45, "wellness": 60, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 60,
            "pet_friendly_score": 35,
            "family_friendly_score": 70,
            "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 50,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 3000,
            "luxury_min_7d": 3000, "luxury_max_7d": 8000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 10},
        "best_months": [6, 7, 8, 9, 12, 1, 2],
        "avoid_months": [3, 4, 5, 10, 11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Gorilles des montagnes", "emoji": "🦍", "category": "nature"},
            {"name": "Parc des Volcans", "emoji": "🌋", "category": "adventure"},
            {"name": "Kigali moderne", "emoji": "🏙️", "category": "culture"},
            {"name": "Lac Kivu", "emoji": "🌊", "category": "nature"},
            {"name": "Memorial du genocide", "emoji": "🕯️", "category": "history"}
        ],
        "fallback_headlines": {
            "solo": "Rwanda, gorilles et renaissance en solo",
            "couple": "Rwanda romantique, gorilles mythiques",
            "family": "Rwanda en famille, nature et histoire",
            "friends": "Rwanda entre amis, aventure unique",
            "pet": "Rwanda vert"
        },
        "fallback_description": "Gorilles des montagnes, collines verdoyantes et renaissance inspirante."
    },
    {
        "country_code": "UG",
        "country_name": "Ouganda",
        "flag_emoji": "🇺🇬",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["English", "Swahili"],
        "currency": "UGX",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 80,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 65
        },
        "interest_scores": {
            "culture": 75, "food": 55, "beach": 30, "adventure": 90,
            "nature": 95, "nightlife": 50, "history": 65, "art": 55,
            "shopping": 45, "wellness": 50, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 45,
            "pet_friendly_score": 35,
            "family_friendly_score": 65,
            "wifi_quality_score": 60
        },
        "budget": {
            "cost_of_living_index": 40,
            "budget_min_7d": 350, "budget_max_7d": 600,
            "comfort_min_7d": 600, "comfort_max_7d": 1200,
            "premium_min_7d": 1200, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 7000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 15, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [6, 7, 8, 9, 12, 1, 2],
        "avoid_months": [3, 4, 5, 10, 11],
        "best_seasons": ["Ete", "Hiver"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Gorilles de Bwindi", "emoji": "🦍", "category": "nature"},
            {"name": "Source du Nil", "emoji": "🌊", "category": "adventure"},
            {"name": "Safari Queen Elizabeth", "emoji": "🦁", "category": "nature"},
            {"name": "Chimpanzes Kibale", "emoji": "🐒", "category": "nature"},
            {"name": "Rafting Nil blanc", "emoji": "🚣", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Ouganda, perle de l'Afrique en solo",
            "couple": "Ouganda romantique, gorilles et Nil",
            "family": "Ouganda en famille, safari et primates",
            "friends": "Ouganda entre amis, aventure sauvage",
            "pet": "Ouganda sauvage"
        },
        "fallback_description": "Perle de l'Afrique, gorilles, source du Nil et safari."
    },
    {
        "country_code": "ET",
        "country_name": "Ethiopie",
        "flag_emoji": "🇪🇹",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["Amharic"],
        "currency": "ETB",
        "style_scores": {
            "chill_vs_intense": 55,
            "city_vs_nature": 65,
            "eco_vs_luxury": 30,
            "tourist_vs_local": 75
        },
        "interest_scores": {
            "culture": 98, "food": 85, "beach": 10, "adventure": 75,
            "nature": 85, "nightlife": 45, "history": 98, "art": 80,
            "shopping": 55, "wellness": 50, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 40,
            "pet_friendly_score": 30,
            "family_friendly_score": 55,
            "wifi_quality_score": 50
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 220, "budget_max_7d": 400,
            "comfort_min_7d": 400, "comfort_max_7d": 750,
            "premium_min_7d": 750, "premium_max_7d": 1500,
            "luxury_min_7d": 1500, "luxury_max_7d": 4000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 10, "family": 5, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 10, "anniversary": 10, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [10, 11, 12, 1, 2, 3],
        "avoid_months": [6, 7, 8, 9],
        "best_seasons": ["Automne", "Hiver"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Eglises de Lalibela", "emoji": "⛪", "category": "history"},
            {"name": "Montagnes du Simien", "emoji": "🏔️", "category": "nature"},
            {"name": "Addis-Abeba", "emoji": "🏙️", "category": "culture"},
            {"name": "Cafe ethiopien", "emoji": "☕", "category": "food"},
            {"name": "Vallee de l'Omo", "emoji": "👥", "category": "culture"}
        ],
        "fallback_headlines": {
            "solo": "Ethiopie, berceau de l'humanite en solo",
            "couple": "Ethiopie romantique, Lalibela mystique",
            "family": "Ethiopie en famille, histoire unique",
            "friends": "Ethiopie entre amis, aventure culturelle",
            "pet": "Ethiopie ancestrale"
        },
        "fallback_description": "Lalibela mystique, cafe originel et histoire millenaire unique."
    },
    {
        "country_code": "NA",
        "country_name": "Namibie",
        "flag_emoji": "🇳🇦",
        "region": "Africa",
        "subregion": "Southern Africa",
        "languages": ["English"],
        "currency": "NAD",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 90,
            "eco_vs_luxury": 55,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 65, "food": 55, "beach": 40, "adventure": 90,
            "nature": 98, "nightlife": 30, "history": 55, "art": 55,
            "shopping": 40, "wellness": 55, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 55,
            "pet_friendly_score": 45,
            "family_friendly_score": 75,
            "wifi_quality_score": 65
        },
        "budget": {
            "cost_of_living_index": 50,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1400,
            "premium_min_7d": 1400, "premium_max_7d": 2800,
            "luxury_min_7d": 2800, "luxury_max_7d": 7000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 15, "friends": 15, "pet": 0},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 5, "workation": 5},
        "best_months": [5, 6, 7, 8, 9, 10],
        "avoid_months": [12, 1, 2, 3],
        "best_seasons": ["Hiver"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Dunes de Sossusvlei", "emoji": "🏜️", "category": "nature"},
            {"name": "Etosha safari", "emoji": "🦁", "category": "nature"},
            {"name": "Skeleton Coast", "emoji": "💀", "category": "adventure"},
            {"name": "Swakopmund", "emoji": "🏖️", "category": "adventure"},
            {"name": "Ciel etoile", "emoji": "🌌", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Namibie, desert et etoiles en solo",
            "couple": "Namibie romantique, dunes et safari",
            "family": "Namibie en famille, aventure securisee",
            "friends": "Namibie entre amis, road trip epique",
            "pet": "Namibie sauvage"
        },
        "fallback_description": "Dunes rouges de Sossusvlei, safari Etosha et ciels etoiles."
    },
    {
        "country_code": "BW",
        "country_name": "Botswana",
        "flag_emoji": "🇧🇼",
        "region": "Africa",
        "subregion": "Southern Africa",
        "languages": ["English", "Setswana"],
        "currency": "BWP",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 95,
            "eco_vs_luxury": 75,
            "tourist_vs_local": 45
        },
        "interest_scores": {
            "culture": 60, "food": 50, "beach": 15, "adventure": 85,
            "nature": 100, "nightlife": 25, "history": 50, "art": 45,
            "shopping": 35, "wellness": 70, "sports": 50
        },
        "must_haves": {
            "accessibility_score": 50,
            "pet_friendly_score": 30,
            "family_friendly_score": 70,
            "wifi_quality_score": 55
        },
        "budget": {
            "cost_of_living_index": 70,
            "budget_min_7d": 600, "budget_max_7d": 1000,
            "comfort_min_7d": 1000, "comfort_max_7d": 2000,
            "premium_min_7d": 2000, "premium_max_7d": 4500,
            "luxury_min_7d": 4500, "luxury_max_7d": 12000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 25, "family": 15, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 25, "birthday": 10, "vacation": 5, "workation": 0},
        "best_months": [5, 6, 7, 8, 9, 10],
        "avoid_months": [12, 1, 2, 3],
        "best_seasons": ["Hiver"],
        "trending_score": 82,
        "top_activities": [
            {"name": "Delta de l'Okavango", "emoji": "🌊", "category": "nature"},
            {"name": "Safari Chobe", "emoji": "🐘", "category": "nature"},
            {"name": "Makgadikgadi Pans", "emoji": "🌅", "category": "nature"},
            {"name": "Mokoro", "emoji": "🛶", "category": "adventure"},
            {"name": "Safari de luxe", "emoji": "🏕️", "category": "wellness"}
        ],
        "fallback_headlines": {
            "solo": "Botswana, safari ultime en solo",
            "couple": "Botswana romantique, Okavango magique",
            "family": "Botswana en famille, safari exclusif",
            "friends": "Botswana entre amis, aventure luxe",
            "pet": "Botswana sauvage"
        },
        "fallback_description": "Delta de l'Okavango, safari de luxe et nature africaine pristine."
    },
    {
        "country_code": "MZ",
        "country_name": "Mozambique",
        "flag_emoji": "🇲🇿",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["Portuguese"],
        "currency": "MZN",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 70,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 70, "food": 75, "beach": 95, "adventure": 75,
            "nature": 80, "nightlife": 50, "history": 65, "art": 55,
            "shopping": 40, "wellness": 70, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 40,
            "pet_friendly_score": 35,
            "family_friendly_score": 60,
            "wifi_quality_score": 50
        },
        "budget": {
            "cost_of_living_index": 40,
            "budget_min_7d": 300, "budget_max_7d": 550,
            "comfort_min_7d": 550, "comfort_max_7d": 1100,
            "premium_min_7d": 1100, "premium_max_7d": 2200,
            "luxury_min_7d": 2200, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 10, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 10, "workation": 5},
        "best_months": [4, 5, 6, 7, 8, 9, 10, 11],
        "avoid_months": [1, 2, 3],
        "best_seasons": ["Automne", "Hiver", "Printemps"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Archipel de Bazaruto", "emoji": "🏝️", "category": "beach"},
            {"name": "Plongee Tofo", "emoji": "🤿", "category": "adventure"},
            {"name": "Raies manta", "emoji": "🐟", "category": "nature"},
            {"name": "Maputo", "emoji": "🏙️", "category": "culture"},
            {"name": "Cuisine afro-portugaise", "emoji": "🍽️", "category": "food"}
        ],
        "fallback_headlines": {
            "solo": "Mozambique, plages secretes en solo",
            "couple": "Mozambique romantique, paradis cache",
            "family": "Mozambique en famille, plages et plongee",
            "friends": "Mozambique entre amis, plongee et fete",
            "pet": "Mozambique tropical"
        },
        "fallback_description": "Plages vierges, plongee world-class et fusion afro-portugaise."
    },
    {
        "country_code": "MG",
        "country_name": "Madagascar",
        "flag_emoji": "🇲🇬",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["Malagasy", "French"],
        "currency": "MGA",
        "style_scores": {
            "chill_vs_intense": 50,
            "city_vs_nature": 85,
            "eco_vs_luxury": 35,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 80, "food": 65, "beach": 80, "adventure": 85,
            "nature": 100, "nightlife": 40, "history": 65, "art": 60,
            "shopping": 50, "wellness": 55, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 35,
            "pet_friendly_score": 30,
            "family_friendly_score": 60,
            "wifi_quality_score": 45
        },
        "budget": {
            "cost_of_living_index": 35,
            "budget_min_7d": 250, "budget_max_7d": 450,
            "comfort_min_7d": 450, "comfort_max_7d": 850,
            "premium_min_7d": 850, "premium_max_7d": 1700,
            "luxury_min_7d": 1700, "luxury_max_7d": 4500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 0},
        "best_months": [4, 5, 9, 10, 11],
        "avoid_months": [1, 2, 3, 6, 7, 8],
        "best_seasons": ["Automne", "Printemps"],
        "trending_score": 78,
        "top_activities": [
            {"name": "Lemuriens", "emoji": "🐒", "category": "nature"},
            {"name": "Allee des Baobabs", "emoji": "🌳", "category": "nature"},
            {"name": "Nosy Be", "emoji": "🏝️", "category": "beach"},
            {"name": "Tsingy de Bemaraha", "emoji": "🏔️", "category": "adventure"},
            {"name": "Faune unique", "emoji": "🦎", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Madagascar, ile unique en solo",
            "couple": "Madagascar romantique, lemuriens et plages",
            "family": "Madagascar en famille, faune extraordinaire",
            "friends": "Madagascar entre amis, aventure unique",
            "pet": "Madagascar extraordinaire"
        },
        "fallback_description": "Ile unique, lemuriens, baobabs et biodiversite exceptionnelle."
    },
    {
        "country_code": "CV",
        "country_name": "Cap-Vert",
        "flag_emoji": "🇨🇻",
        "region": "Africa",
        "subregion": "Western Africa",
        "languages": ["Portuguese"],
        "currency": "CVE",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 60,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 55
        },
        "interest_scores": {
            "culture": 80, "food": 70, "beach": 90, "adventure": 70,
            "nature": 75, "nightlife": 70, "history": 60, "art": 75,
            "shopping": 45, "wellness": 65, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 60,
            "pet_friendly_score": 45,
            "family_friendly_score": 80,
            "wifi_quality_score": 70
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 350, "budget_max_7d": 580,
            "comfort_min_7d": 580, "comfort_max_7d": 1050,
            "premium_min_7d": 1050, "premium_max_7d": 2000,
            "luxury_min_7d": 2000, "luxury_max_7d": 5000
        },
        "travel_style_bonuses": {"solo": 15, "couple": 20, "family": 15, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 10, "workation": 10},
        "best_months": [11, 12, 1, 2, 3, 4, 5, 6],
        "avoid_months": [8, 9],
        "best_seasons": ["Hiver", "Printemps"],
        "trending_score": 74,
        "top_activities": [
            {"name": "Plages de Sal", "emoji": "🏖️", "category": "beach"},
            {"name": "Musique Morna", "emoji": "🎵", "category": "culture"},
            {"name": "Randonnee Santo Antao", "emoji": "🥾", "category": "adventure"},
            {"name": "Mindelo", "emoji": "🏙️", "category": "culture"},
            {"name": "Kitesurf Boa Vista", "emoji": "🪁", "category": "sports"}
        ],
        "fallback_headlines": {
            "solo": "Cap-Vert, iles et musique en solo",
            "couple": "Cap-Vert romantique, plages et morna",
            "family": "Cap-Vert en famille, soleil garanti",
            "friends": "Cap-Vert entre amis, kitesurf et fete",
            "pet": "Cap-Vert ensoleille"
        },
        "fallback_description": "Iles atlantiques, musique morna et plages de sable fin."
    },
    {
        "country_code": "SC",
        "country_name": "Seychelles",
        "flag_emoji": "🇸🇨",
        "region": "Africa",
        "subregion": "Eastern Africa",
        "languages": ["Seychellois Creole", "English", "French"],
        "currency": "SCR",
        "style_scores": {
            "chill_vs_intense": 25,
            "city_vs_nature": 70,
            "eco_vs_luxury": 85,
            "tourist_vs_local": 35
        },
        "interest_scores": {
            "culture": 55, "food": 75, "beach": 100, "adventure": 60,
            "nature": 90, "nightlife": 45, "history": 45, "art": 45,
            "shopping": 50, "wellness": 90, "sports": 65
        },
        "must_haves": {
            "accessibility_score": 70,
            "pet_friendly_score": 40,
            "family_friendly_score": 85,
            "wifi_quality_score": 80
        },
        "budget": {
            "cost_of_living_index": 95,
            "budget_min_7d": 700, "budget_max_7d": 1200,
            "comfort_min_7d": 1200, "comfort_max_7d": 2500,
            "premium_min_7d": 2500, "premium_max_7d": 5000,
            "luxury_min_7d": 5000, "luxury_max_7d": 15000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 25, "family": 15, "friends": 10, "pet": -5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 25, "birthday": 15, "vacation": 10, "workation": 5},
        "best_months": [4, 5, 10, 11],
        "avoid_months": [1, 2, 7, 8],
        "best_seasons": ["Printemps", "Automne"],
        "trending_score": 85,
        "top_activities": [
            {"name": "Plages d'Anse Source d'Argent", "emoji": "🏖️", "category": "beach"},
            {"name": "Snorkeling", "emoji": "🤿", "category": "adventure"},
            {"name": "Vallee de Mai", "emoji": "🌴", "category": "nature"},
            {"name": "Island hopping", "emoji": "🏝️", "category": "beach"},
            {"name": "Spa de luxe", "emoji": "🧖", "category": "wellness"}
        ],
        "fallback_headlines": {
            "solo": "Seychelles, paradis luxueux en solo",
            "couple": "Seychelles romantiques, lune de miel parfaite",
            "family": "Seychelles en famille, paradis tropical",
            "friends": "Seychelles entre amis, luxe et plages",
            "pet": "Seychelles paradisiaques"
        },
        "fallback_description": "Plages paradisiaques, eaux cristallines et luxe tropical ultime."
    },
    # ========================================================================
    # OCEANIA (4 countries)
    # ========================================================================
    {
        "country_code": "WS",
        "country_name": "Samoa",
        "flag_emoji": "🇼🇸",
        "region": "Oceania",
        "subregion": "Polynesia",
        "languages": ["Samoan", "English"],
        "currency": "WST",
        "style_scores": {
            "chill_vs_intense": 25,
            "city_vs_nature": 75,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 85, "food": 65, "beach": 90, "adventure": 65,
            "nature": 85, "nightlife": 35, "history": 55, "art": 60,
            "shopping": 35, "wellness": 70, "sports": 55
        },
        "must_haves": {
            "accessibility_score": 45,
            "pet_friendly_score": 40,
            "family_friendly_score": 75,
            "wifi_quality_score": 55
        },
        "budget": {
            "cost_of_living_index": 60,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1300,
            "premium_min_7d": 1300, "premium_max_7d": 2500,
            "luxury_min_7d": 2500, "luxury_max_7d": 6000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": -5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 10, "workation": 5},
        "best_months": [5, 6, 7, 8, 9, 10],
        "avoid_months": [12, 1, 2, 3],
        "best_seasons": ["Hiver"],
        "trending_score": 68,
        "top_activities": [
            {"name": "To Sua Ocean Trench", "emoji": "🏊", "category": "nature"},
            {"name": "Culture samoane", "emoji": "🎭", "category": "culture"},
            {"name": "Plages vierges", "emoji": "🏖️", "category": "beach"},
            {"name": "Villages traditionnels", "emoji": "🏘️", "category": "culture"},
            {"name": "Cascades tropicales", "emoji": "💧", "category": "nature"}
        ],
        "fallback_headlines": {
            "solo": "Samoa, polynesie authentique en solo",
            "couple": "Samoa romantique, paradis cache",
            "family": "Samoa en famille, culture et lagons",
            "friends": "Samoa entre amis, aventure tropicale",
            "pet": "Samoa traditionnel"
        },
        "fallback_description": "Polynesie authentique, culture fa'a Samoa et lagons turquoise."
    },
    {
        "country_code": "VU",
        "country_name": "Vanuatu",
        "flag_emoji": "🇻🇺",
        "region": "Oceania",
        "subregion": "Melanesia",
        "languages": ["Bislama", "English", "French"],
        "currency": "VUV",
        "style_scores": {
            "chill_vs_intense": 45,
            "city_vs_nature": 85,
            "eco_vs_luxury": 40,
            "tourist_vs_local": 70
        },
        "interest_scores": {
            "culture": 85, "food": 60, "beach": 85, "adventure": 90,
            "nature": 95, "nightlife": 35, "history": 55, "art": 60,
            "shopping": 35, "wellness": 55, "sports": 70
        },
        "must_haves": {
            "accessibility_score": 40,
            "pet_friendly_score": 35,
            "family_friendly_score": 65,
            "wifi_quality_score": 50
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1300,
            "premium_min_7d": 1300, "premium_max_7d": 2600,
            "luxury_min_7d": 2600, "luxury_max_7d": 6500
        },
        "travel_style_bonuses": {"solo": 15, "couple": 15, "family": 10, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 20, "anniversary": 15, "birthday": 10, "vacation": 5, "workation": 0},
        "best_months": [4, 5, 6, 7, 8, 9, 10],
        "avoid_months": [1, 2, 3],
        "best_seasons": ["Automne", "Hiver"],
        "trending_score": 72,
        "top_activities": [
            {"name": "Volcan Yasur", "emoji": "🌋", "category": "adventure"},
            {"name": "Plongee sous-marine", "emoji": "🤿", "category": "adventure"},
            {"name": "Blue Holes", "emoji": "🌊", "category": "nature"},
            {"name": "Culture melanesienne", "emoji": "🎭", "category": "culture"},
            {"name": "Saut du Naghol", "emoji": "🦘", "category": "adventure"}
        ],
        "fallback_headlines": {
            "solo": "Vanuatu, volcans et aventure en solo",
            "couple": "Vanuatu romantique, nature sauvage",
            "family": "Vanuatu en famille, decouverte unique",
            "friends": "Vanuatu entre amis, adrénaline garantie",
            "pet": "Vanuatu sauvage"
        },
        "fallback_description": "Volcans actifs, culture tribale et plongee exceptionnelle."
    },
    {
        "country_code": "NC",
        "country_name": "Nouvelle-Caledonie",
        "flag_emoji": "🇳🇨",
        "region": "Oceania",
        "subregion": "Melanesia",
        "languages": ["French"],
        "currency": "XPF",
        "style_scores": {
            "chill_vs_intense": 35,
            "city_vs_nature": 70,
            "eco_vs_luxury": 60,
            "tourist_vs_local": 50
        },
        "interest_scores": {
            "culture": 75, "food": 80, "beach": 95, "adventure": 75,
            "nature": 90, "nightlife": 50, "history": 55, "art": 60,
            "shopping": 55, "wellness": 70, "sports": 75
        },
        "must_haves": {
            "accessibility_score": 65,
            "pet_friendly_score": 50,
            "family_friendly_score": 85,
            "wifi_quality_score": 75
        },
        "budget": {
            "cost_of_living_index": 85,
            "budget_min_7d": 550, "budget_max_7d": 950,
            "comfort_min_7d": 950, "comfort_max_7d": 1800,
            "premium_min_7d": 1800, "premium_max_7d": 3500,
            "luxury_min_7d": 3500, "luxury_max_7d": 9000
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 20, "friends": 15, "pet": 5},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 10, "workation": 10},
        "best_months": [9, 10, 11, 12],
        "avoid_months": [1, 2, 3, 7, 8],
        "best_seasons": ["Printemps"],
        "trending_score": 75,
        "top_activities": [
            {"name": "Lagon UNESCO", "emoji": "🌊", "category": "nature"},
            {"name": "Ile des Pins", "emoji": "🏝️", "category": "beach"},
            {"name": "Plongee recif", "emoji": "🤿", "category": "adventure"},
            {"name": "Noumea", "emoji": "🏙️", "category": "culture"},
            {"name": "Cuisine francaise-melanesienne", "emoji": "🍽️", "category": "food"}
        ],
        "fallback_headlines": {
            "solo": "Nouvelle-Caledonie, lagon UNESCO en solo",
            "couple": "Nouvelle-Caledonie romantique, paradis francais",
            "family": "Nouvelle-Caledonie en famille, plages et lagon",
            "friends": "Nouvelle-Caledonie entre amis, plongee et fete",
            "pet": "Nouvelle-Caledonie tropicale"
        },
        "fallback_description": "Plus grand lagon du monde, Ile des Pins et douceur francaise."
    },
    {
        "country_code": "TO",
        "country_name": "Tonga",
        "flag_emoji": "🇹🇴",
        "region": "Oceania",
        "subregion": "Polynesia",
        "languages": ["Tongan", "English"],
        "currency": "TOP",
        "style_scores": {
            "chill_vs_intense": 30,
            "city_vs_nature": 80,
            "eco_vs_luxury": 45,
            "tourist_vs_local": 75
        },
        "interest_scores": {
            "culture": 80, "food": 60, "beach": 85, "adventure": 80,
            "nature": 90, "nightlife": 30, "history": 55, "art": 55,
            "shopping": 30, "wellness": 65, "sports": 60
        },
        "must_haves": {
            "accessibility_score": 40,
            "pet_friendly_score": 35,
            "family_friendly_score": 70,
            "wifi_quality_score": 50
        },
        "budget": {
            "cost_of_living_index": 55,
            "budget_min_7d": 400, "budget_max_7d": 700,
            "comfort_min_7d": 700, "comfort_max_7d": 1300,
            "premium_min_7d": 1300, "premium_max_7d": 2600,
            "luxury_min_7d": 2600, "luxury_max_7d": 6500
        },
        "travel_style_bonuses": {"solo": 10, "couple": 20, "family": 15, "friends": 15, "pet": -10},
        "occasion_bonuses": {"honeymoon": 25, "anniversary": 20, "birthday": 10, "vacation": 10, "workation": 0},
        "best_months": [6, 7, 8, 9, 10, 11],
        "avoid_months": [1, 2, 3, 4],
        "best_seasons": ["Hiver", "Printemps"],
        "trending_score": 70,
        "top_activities": [
            {"name": "Nager avec les baleines", "emoji": "🐋", "category": "nature"},
            {"name": "Iles Ha'apai", "emoji": "🏝️", "category": "beach"},
            {"name": "Culture royale tongienne", "emoji": "👑", "category": "culture"},
            {"name": "Kayak et snorkeling", "emoji": "🤿", "category": "adventure"},
            {"name": "Plages desertes", "emoji": "🏖️", "category": "beach"}
        ],
        "fallback_headlines": {
            "solo": "Tonga, royaume polynesien en solo",
            "couple": "Tonga romantique, baleines et lagons",
            "family": "Tonga en famille, aventure authentique",
            "friends": "Tonga entre amis, nature et exploration",
            "pet": "Tonga authentique"
        },
        "fallback_description": "Royaume polynesien, nager avec les baleines et iles intactes."
    },
]

# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Seed the 50 new country profiles to MongoDB."""
    print("=" * 60)
    print("SEED COUNTRY PROFILES V2 - 50 New Countries")
    print("=" * 60)

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db[COLLECTION_NAME]

    print(f"\nConnecting to MongoDB: {MONGODB_DB}")
    print(f"Collection: {COLLECTION_NAME}")

    # Count existing profiles
    existing_count = await collection.count_documents({})
    print(f"Existing profiles: {existing_count}")
    print(f"New profiles to add: {len(NEW_COUNTRY_PROFILES)}")

    # Add timestamp to each profile
    for profile in NEW_COUNTRY_PROFILES:
        profile["created_at"] = datetime.utcnow()
        profile["updated_at"] = datetime.utcnow()

    # Insert or update profiles
    inserted = 0
    updated = 0

    for profile in NEW_COUNTRY_PROFILES:
        code = profile["country_code"]

        # Check if already exists
        existing = await collection.find_one({"country_code": code})

        if existing:
            # Update existing
            result = await collection.update_one(
                {"country_code": code},
                {"$set": profile}
            )
            if result.modified_count > 0:
                updated += 1
                print(f"  Updated: {profile['country_name']} ({code})")
        else:
            # Insert new
            await collection.insert_one(profile)
            inserted += 1
            print(f"  Inserted: {profile['country_name']} ({code})")

    # Final count
    final_count = await collection.count_documents({})

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")
    print(f"Total profiles now: {final_count}")
    print("=" * 60)

    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(main())

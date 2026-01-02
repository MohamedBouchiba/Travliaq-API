"""Constants and mappings for Viator API."""

# Supported currencies
SUPPORTED_CURRENCIES = [
    "AUD", "BRL", "CAD", "CHF", "DKK", "EUR", "GBP",
    "HKD", "INR", "JPY", "NOK", "NZD", "SEK", "SGD",
    "TWD", "USD", "ZAR"
]

# Supported languages
SUPPORTED_LANGUAGES = [
    "en", "fr", "es", "de", "it", "pt", "nl", "sv",
    "da", "no", "fi", "pl", "ru", "ja", "zh", "ko"
]

# Activity flags
ACTIVITY_FLAGS = [
    "NEW_ON_VIATOR",
    "FREE_CANCELLATION",
    "SKIP_THE_LINE",
    "PRIVATE_TOUR",
    "SPECIAL_OFFER",
    "LIKELY_TO_SELL_OUT"
]

# Sort options mapping
SORT_MAPPING = {
    "default": "DEFAULT",
    "rating": "TRAVELER_RATING",
    "price": "PRICE",
    "duration": "ITINERARY_DURATION",
    "date_added": "DATE_ADDED"
}

# Simplified category to Viator tags mapping
# Note: In production, this should be stored in MongoDB and fetched dynamically
CATEGORY_TAG_MAPPING = {
    "food": {
        "name": "Food & Dining",
        "name_translations": {
            "fr": "Gastronomie",
            "es": "Gastronomía",
            "de": "Essen & Trinken"
        },
        "viator_tags": [21972, 21973, 21974],
        "icon": "🍴"
    },
    "museum": {
        "name": "Museums",
        "name_translations": {
            "fr": "Musées",
            "es": "Museos",
            "de": "Museen"
        },
        "viator_tags": [21975],
        "icon": "🏛️"
    },
    "art": {
        "name": "Art & Culture",
        "name_translations": {
            "fr": "Art & Culture",
            "es": "Arte y Cultura",
            "de": "Kunst & Kultur"
        },
        "viator_tags": [21976, 21977],
        "icon": "🎨"
    },
    "adventure": {
        "name": "Adventure & Outdoor",
        "name_translations": {
            "fr": "Aventure & Plein air",
            "es": "Aventura y Aire libre",
            "de": "Abenteuer & Outdoor"
        },
        "viator_tags": [21980, 21981],
        "icon": "⛰️"
    },
    "nature": {
        "name": "Nature & Wildlife",
        "name_translations": {
            "fr": "Nature & Faune",
            "es": "Naturaleza y Vida Silvestre",
            "de": "Natur & Tierwelt"
        },
        "viator_tags": [21985],
        "icon": "🌿"
    },
    "tours": {
        "name": "City Tours",
        "name_translations": {
            "fr": "Visites de la ville",
            "es": "Tours por la ciudad",
            "de": "Stadtführungen"
        },
        "viator_tags": [21990],
        "icon": "🚌"
    },
    "water": {
        "name": "Water Activities",
        "name_translations": {
            "fr": "Activités nautiques",
            "es": "Actividades acuáticas",
            "de": "Wasseraktivitäten"
        },
        "viator_tags": [21995],
        "icon": "🌊"
    },
    "nightlife": {
        "name": "Nightlife",
        "name_translations": {
            "fr": "Vie nocturne",
            "es": "Vida nocturna",
            "de": "Nachtleben"
        },
        "viator_tags": [22000],
        "icon": "🌃"
    },
    "shopping": {
        "name": "Shopping",
        "name_translations": {
            "fr": "Shopping",
            "es": "Compras",
            "de": "Einkaufen"
        },
        "viator_tags": [22005],
        "icon": "🛍️"
    }
}

# Error codes
ERROR_CODES = {
    "DESTINATION_NOT_FOUND": "Unable to find destination",
    "INVALID_DATE_RANGE": "Invalid date range provided",
    "INVALID_LOCATION": "Invalid location input",
    "VIATOR_API_ERROR": "Error communicating with Viator API",
    "CACHE_ERROR": "Cache service error",
    "DATABASE_ERROR": "Database error"
}

# Cache TTLs (seconds)
CACHE_TTL = {
    "activities_search": 604800,  # 7 days
    "activity_details": 604800,   # 7 days
    "availability": 3600,         # 1 hour
    "destinations": 2592000,      # 30 days
    "categories": 2592000         # 30 days
}

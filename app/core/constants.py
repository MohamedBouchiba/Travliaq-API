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

# ============================================================================
# CATEGORY_TAG_MAPPING REMOVED - Now 100% Dynamic from Viator API
# ============================================================================
# Categories and tags are now fetched from Viator /products/tags endpoint
# and stored in MongoDB via TaxonomySyncService.
#
# The old hardcoded mapping violated the "rien de hardcoder" requirement.
# Tags are now resolved dynamically at runtime from the tags collection.
#
# See:
# - app.services.taxonomy_sync.TaxonomySyncService (sync Viator tags to MongoDB)
# - app.repositories.tags_repository.TagsRepository (query tags from MongoDB)
# - app.services.activities_service.ActivitiesService._map_categories_to_tags (dynamic mapping)
# ============================================================================

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

# Viator API Integration - Quick Start Guide

## Overview

This guide will help you quickly start using the Viator activities search endpoint in the Travliaq-API.

## Prerequisites

1. **Environment Variables**: Ensure your `.env` file has the following Viator-related variables:

```bash
# Viator API
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c
VIATOR_ENV=dev  # Use "prod" for production
VIATOR_BASE_URL=https://api.viator.com

# MongoDB Collections
MONGODB_COLLECTION_ACTIVITIES=activities
MONGODB_COLLECTION_DESTINATIONS=destinations

# Cache TTL (in seconds)
CACHE_TTL_ACTIVITIES_SEARCH=604800  # 7 days
```

2. **Dependencies**: Install required packages:
```bash
pip install -r requirements.txt
```

3. **MongoDB**: Ensure MongoDB is running and accessible. The application will automatically create indexes on startup.

## Starting the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once started, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoint: Search Activities

**POST** `/api/v1/activities/search`

### Request Examples

#### 1. Search by City Name

```json
{
  "location": {
    "city": "Paris",
    "country_code": "FR"
  },
  "dates": {
    "start_date": "2025-06-01",
    "end_date": "2025-06-07"
  },
  "filters": {
    "categories": ["museum", "food"],
    "min_rating": 4.0,
    "price_range": {
      "min": 0,
      "max": 100
    }
  },
  "pagination": {
    "page": 1,
    "page_size": 20
  },
  "currency": "EUR",
  "language": "en"
}
```

#### 2. Search by Destination ID

```json
{
  "location": {
    "destination_id": "684"
  },
  "dates": {
    "start_date": "2025-06-01"
  },
  "currency": "EUR",
  "language": "fr"
}
```

#### 3. Search by Geo Coordinates

```json
{
  "location": {
    "geo": {
      "latitude": 48.8566,
      "longitude": 2.3522
    }
  },
  "dates": {
    "start_date": "2025-06-01",
    "end_date": "2025-06-07"
  },
  "filters": {
    "categories": ["adventure", "water"],
    "min_duration_minutes": 60,
    "max_duration_minutes": 240,
    "flags": ["likely_to_sell_out", "free_cancellation"]
  },
  "sorting": {
    "sort_by": "rating",
    "order": "desc"
  },
  "currency": "USD",
  "language": "en"
}
```

### Response Structure

```json
{
  "success": true,
  "location": {
    "type": "city",
    "city": "Paris",
    "country_code": "FR",
    "destination_id": "684",
    "matched_name": "Paris",
    "match_score": 100.0
  },
  "results": {
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8,
    "activities": [
      {
        "id": "12345",
        "title": "Louvre Museum Skip-the-Line Tour",
        "description": "Explore the world's largest art museum...",
        "images": [
          {
            "url": "https://example.com/image.jpg",
            "is_cover": true,
            "variants": {
              "small": "https://example.com/image-small.jpg",
              "medium": "https://example.com/image-medium.jpg",
              "large": "https://example.com/image-large.jpg"
            }
          }
        ],
        "pricing": {
          "from_price": 59.99,
          "currency": "EUR",
          "is_discounted": false,
          "original_price": null,
          "discount_percentage": null
        },
        "rating": {
          "average": 4.8,
          "count": 2543,
          "distribution": {
            "5": 1800,
            "4": 600,
            "3": 100,
            "2": 30,
            "1": 13
          }
        },
        "duration": {
          "type": "fixed",
          "minutes": 180,
          "label": "3 hours"
        },
        "categories": ["museum", "art"],
        "flags": ["skip_the_line", "free_cancellation"],
        "booking_url": "https://www.viator.com/tours/..."
      }
    ]
  },
  "cache_info": {
    "cached": false,
    "cache_key": "activities:684:2025-06-01:...",
    "ttl_seconds": 604800
  },
  "metadata": {
    "request_id": "req_abc123",
    "timestamp": "2025-01-02T10:30:00Z",
    "processing_time_ms": 245
  }
}
```

## Available Filters

### Categories
- `food` - Food & Dining
- `museum` - Museums & Art
- `adventure` - Adventure Activities
- `water` - Water Activities
- `culture` - Cultural Experiences
- `nature` - Nature & Wildlife
- `entertainment` - Entertainment & Shows
- `tours` - Guided Tours
- `sports` - Sports & Recreation
- `shopping` - Shopping Tours
- `nightlife` - Nightlife

### Flags (Activity Features)
- `skip_the_line` - Skip-the-line access
- `free_cancellation` - Free cancellation available
- `likely_to_sell_out` - Popular activities
- `instant_confirmation` - Instant booking confirmation
- `mobile_ticket` - Mobile tickets accepted
- `audio_guide` - Audio guide included
- `pickup_included` - Hotel pickup included
- `accessible` - Wheelchair accessible

### Sorting Options
- `default` - Default Viator ranking
- `rating` - By traveler rating
- `price` - By price (low to high or high to low)

## Cache Strategy

- **Cache TTL**: 7 days (604800 seconds)
- **Cache Key Format**: `activities:{destination_id}:{start_date}:{filters_hash}`
- **Cache Storage**: Redis (Upstash)
- **Cache Hit**: Response includes `cache_info.cached: true`
- **Cache Miss**: Fresh data from Viator API, then cached

## MongoDB Persistence

All activities are automatically persisted in MongoDB with:
- **Collection**: `activities`
- **Unique Key**: `product_code`
- **Metadata Tracking**:
  - `first_seen` - When first encountered
  - `last_updated` - Last refresh timestamp
  - `fetch_count` - Number of times returned in searches

## Troubleshooting

### 1. "Location not found" Error

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "LOCATION_NOT_FOUND",
    "message": "Could not resolve location"
  }
}
```

**Solution**:
- Check city name spelling
- Provide `country_code` for better matching
- Use `destination_id` directly if known
- Try geo coordinates instead

### 2. Rate Limit Errors

The client includes automatic retry with exponential backoff. If you encounter persistent rate limits:
- Wait for the `Retry-After` period
- Reduce request frequency
- Consider switching to production API key (higher limits)

### 3. No Results Returned

If `results.total: 0`:
- Try broader date range
- Remove or relax filters (min_rating, price_range, etc.)
- Check if destination has activities in Viator's catalog
- Try different categories

## Testing with curl

```bash
curl -X POST "http://localhost:8000/api/v1/activities/search" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"city": "Paris", "country_code": "FR"},
    "dates": {"start_date": "2025-06-01"},
    "currency": "EUR",
    "language": "en"
  }'
```

## Next Steps

1. **Populate Destinations**: Use the admin endpoints to populate the destinations collection with Viator's destination data
2. **Test Different Cities**: Try various cities to build up the location cache
3. **Monitor Cache Hit Rate**: Check `cache_info.cached` in responses to monitor cache effectiveness
4. **Customize Categories**: Modify `app/core/constants.py` to add more category mappings
5. **Add More Endpoints**: Implement availability checks, booking, and other Viator endpoints

## Support

For issues or questions:
- Check the comprehensive documentation in `VIATOR_IMPLEMENTATION_GUIDE.md`
- Review API models in `VIATOR_MODELS_REFERENCE.md`
- Consult the implementation checklist in `VIATOR_IMPLEMENTATION_CHECKLIST.md`

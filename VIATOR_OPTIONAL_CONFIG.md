# Viator Integration - Optional Configuration

## Overview

The Viator API integration has been implemented as an **optional feature**. The application will start successfully whether or not Viator API keys are configured.

## Configuration Status

### Without Viator API Keys
- ✅ Application starts normally
- ✅ All existing endpoints work as before
- ❌ `/api/v1/activities/*` endpoints return 503 Service Unavailable
- ❌ Error message: "Viator integration is not configured"

### With Viator API Keys
- ✅ Application starts normally
- ✅ All existing endpoints work as before
- ✅ `/api/v1/activities/*` endpoints are fully functional
- ✅ Activities search with caching and persistence

## Enabling Viator Integration

To enable the Viator activities feature, add the following environment variables to your `.env` file:

```bash
# Viator API Keys (at least one is required)
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c

# Environment selector (determines which key to use)
VIATOR_ENV=dev  # Use "prod" for production

# Viator API base URL (default is fine)
VIATOR_BASE_URL=https://api.viator.com

# Optional: Cache TTL settings (defaults shown)
CACHE_TTL_ACTIVITIES_SEARCH=604800  # 7 days
CACHE_TTL_ACTIVITY_DETAILS=604800   # 7 days
CACHE_TTL_AVAILABILITY=3600         # 1 hour
```

### Minimum Required Configuration

Only the API keys are required. The simplest configuration is:

```bash
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c
```

All other settings have sensible defaults.

## How It Works

### Startup Behavior

1. **Check Configuration**: On startup, the application checks `settings.viator_enabled`
   - Returns `True` if either `VIATOR_API_KEY_DEV` or `VIATOR_API_KEY_PROD` is set
   - Returns `False` if both are empty or missing

2. **Conditional Initialization**:
   - **If enabled**: Initialize Viator client, repositories, location resolver, and activities service
   - **If disabled**: Set all Viator-related services to `None`

3. **API Route Protection**: The `/api/v1/activities/*` endpoints check if the service is available
   - **If available**: Process requests normally
   - **If unavailable**: Return HTTP 503 with clear error message

### Code Implementation

**In [app/core/config.py:35-51](app/core/config.py#L35-L51)**:
```python
# Viator API (optional)
viator_api_key_dev: str = Field("", alias="VIATOR_API_KEY_DEV")
viator_api_key_prod: str = Field("", alias="VIATOR_API_KEY_PROD")
viator_env: str = Field("dev", alias="VIATOR_ENV")

@property
def viator_enabled(self) -> bool:
    """Check if Viator integration is enabled."""
    return bool(self.viator_api_key)
```

**In [app/main.py:113-152](app/main.py#L113-L152)**:
```python
# Initialize Viator API services (only if API keys are configured)
if settings.viator_enabled:
    # Initialize all Viator services...
else:
    # Set to None if not configured
    app.state.viator_client = None
    app.state.activities_service = None
    # ... etc
```

**In [app/api/v1/activities.py:18-33](app/api/v1/activities.py#L18-L33)**:
```python
def get_activities_service(request: Request):
    """Dependency to get activities service from app state."""
    service = request.app.state.activities_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Viator integration is not configured..."
                }
            }
        )
    return service
```

## Testing the Configuration

### 1. Check if Viator is Enabled

**Endpoint**: `GET /api/v1/activities/health`

**Response when disabled**:
```json
{
  "detail": {
    "success": false,
    "error": {
      "code": "SERVICE_UNAVAILABLE",
      "message": "Viator integration is not configured. Please set VIATOR_API_KEY_DEV or VIATOR_API_KEY_PROD in environment variables."
    }
  }
}
```
**Status**: `503 Service Unavailable`

**Response when enabled**:
```json
{
  "status": "healthy",
  "service": "activities",
  "viator_api": "connected"
}
```
**Status**: `200 OK`

### 2. Test Activities Search

**Endpoint**: `POST /api/v1/activities/search`

**Request**:
```json
{
  "location": {"city": "Paris", "country_code": "FR"},
  "dates": {"start_date": "2026-06-01"},
  "currency": "EUR"
}
```

**Response when disabled**: Same 503 error as above

**Response when enabled**: Full activity search results with caching

## Deployment Strategy

### Option 1: Gradual Rollout (Recommended)
1. Deploy code without adding Viator API keys to production
2. Application continues working normally
3. Add API keys when ready to enable Viator features
4. Restart application to activate Viator integration

### Option 2: Full Deployment
1. Add Viator API keys to environment before deploying
2. Deploy updated code
3. Viator features are immediately available

## Environment-Specific Configuration

### Development
```bash
VIATOR_ENV=dev
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
# VIATOR_API_KEY_PROD can be omitted
```

### Production
```bash
VIATOR_ENV=prod
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c
# VIATOR_API_KEY_DEV can be omitted
```

### Both Environments (Recommended)
```bash
VIATOR_ENV=prod  # or dev
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c
```

## Troubleshooting

### Application won't start
- **Before this fix**: Missing `VIATOR_API_KEY_DEV` or `VIATOR_API_KEY_PROD` caused validation error
- **After this fix**: Application starts successfully without these variables

### Activities endpoint returns 503
- **Cause**: Viator API keys not configured
- **Solution**: Add `VIATOR_API_KEY_DEV` or `VIATOR_API_KEY_PROD` to `.env`
- **Verify**: Check health endpoint first: `GET /api/v1/activities/health`

### Which API key is being used?
- Determined by `VIATOR_ENV` setting
- `VIATOR_ENV=dev` → uses `VIATOR_API_KEY_DEV`
- `VIATOR_ENV=prod` → uses `VIATOR_API_KEY_PROD`
- Default is `dev` if not specified

## Related Documentation

- [VIATOR_QUICKSTART.md](VIATOR_QUICKSTART.md) - How to use the activities API
- [VIATOR_IMPLEMENTATION_GUIDE.md](VIATOR_IMPLEMENTATION_GUIDE.md) - Complete implementation details
- [.env.example](.env.example) - Example environment configuration

"""Flight search routes."""

from fastapi import APIRouter, Depends, Request, HTTPException, Body

from app.models.flights import (
    FlightSearchRequest,
    FlightSearchResponse,
    CalendarPricesRequest,
    CalendarPricesResponse
)
from app.services.flights import FlightsService

router = APIRouter(tags=["flights"])


def get_flights_service(request: Request) -> FlightsService:
    """Dependency to get the flights service from app state."""
    service = request.app.state.flights_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Flights service unavailable - Google Flights API not configured"
        )
    return service


@router.post("/flight-search", response_model=FlightSearchResponse)
async def search_flights(
    search_request: FlightSearchRequest = Body(...),
    service: FlightsService = Depends(get_flights_service)
) -> FlightSearchResponse:
    """
    Search for flights based on departure, arrival, dates, and travelers.

    ## Features
    - **One-way & round-trip**: Supports both trip types
    - **Flexible travelers**: Adults, children, infants (with/without seat)
    - **Travel class**: Economy, Premium Economy, Business, First
    - **Real-time prices**: Live pricing from Google Flights
    - **Multiple airlines**: Compare flights across carriers

    ## Parameters
    - **departure_id** (required): IATA code of departure airport (e.g., "LAX")
    - **arrival_id** (required): IATA code of arrival airport (e.g., "JFK")
    - **outbound_date** (required): Departure date (YYYY-MM-DD)
    - **return_date** (optional): Return date for round-trip (YYYY-MM-DD)
    - **adults** (optional): Number of adults 12+ years (default: 1, max: 9)
    - **children** (optional): Number of children 2-11 years (default: 0, max: 8)
    - **infant_in_seat** (optional): Infants requiring seat (default: 0, max: 4)
    - **infant_on_lap** (optional): Infants without seat (default: 0, max: 4)
    - **travel_class** (optional): ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST (default: ECONOMY)
    - **show_hidden** (optional): Include hidden flights (default: false)
    - **currency** (optional): Currency code (default: "USD")
    - **language_code** (optional): Language code (default: "en-US")
    - **country_code** (optional): Country code (default: "US")

    ## Example Request
    ```json
    {
      "departure_id": "LAX",
      "arrival_id": "JFK",
      "outbound_date": "2026-01-12",
      "return_date": "2026-01-19",
      "adults": 2,
      "children": 1,
      "travel_class": "ECONOMY",
      "currency": "USD"
    }
    ```

    ## Example Response
    ```json
    {
      "itineraries": [
        {
          "departure_time": "12-01-2026 07:50 AM",
          "arrival_time": "12-01-2026 04:10 PM",
          "duration": {
            "raw": 380,
            "text": "6 hr 20 min"
          },
          "price": 450.00,
          "stops": 0,
          "airline": "Delta Air Lines",
          "booking_token": "xyz123..."
        },
        {
          "departure_time": "12-01-2026 10:30 AM",
          "arrival_time": "12-01-2026 07:00 PM",
          "duration": {
            "raw": 390,
            "text": "6 hr 30 min"
          },
          "price": 485.00,
          "stops": 1,
          "airline": "United Airlines",
          "booking_token": "abc456..."
        }
      ],
      "next_token": "token_for_more_results"
    }
    ```

    ## Response Fields
    - **itineraries**: List of available flights
      - **departure_time**: Formatted departure time
      - **arrival_time**: Formatted arrival time
      - **duration**: Flight duration (raw minutes + formatted text)
      - **price**: Price in requested currency
      - **stops**: Number of stops (0 = non-stop)
      - **airline**: Primary airline name
      - **booking_token**: Token to get booking details
    - **next_token**: Token to fetch more results (use with /next-flights endpoint)

    ## Error Cases
    - **400 Bad Request**: Invalid parameters
    - **503 Service Unavailable**: Google Flights API not configured
    - **500 Internal Server Error**: API request failed or unexpected error
    """
    try:
        result = service.search_flights(search_request)

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to search flights. The Google Flights API may be unavailable."
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching flights: {str(e)}"
        )


@router.post("/calendar-prices", response_model=CalendarPricesResponse)
async def get_calendar_prices(
    calendar_request: CalendarPricesRequest = Body(...),
    service: FlightsService = Depends(get_flights_service)
) -> CalendarPricesResponse:
    """
    Get flight prices by day for a given month (calendar view).

    ## Features
    - **Price calendar**: See prices for each day in a date range
    - **One-way & round-trip**: Supports both trip types
    - **Flexible dates**: Compare prices across different departure dates
    - **Budget planning**: Find the cheapest days to fly

    ## Parameters
    - **departure_id** (required): IATA code of departure airport (e.g., "LAX")
    - **arrival_id** (required): IATA code of arrival airport (e.g., "JFK")
    - **outbound_date** (required): Initial departure date (YYYY-MM-DD)
    - **start_date** (optional): Start of calendar range (default: today)
    - **end_date** (optional): End of calendar range (default: next month)
    - **adults** (optional): Number of adults 12+ years (default: 1, max: 9)
    - **children** (optional): Number of children 2-11 years (default: 0, max: 8)
    - **infant_in_seat** (optional): Infants requiring seat (default: 0, max: 4)
    - **infant_on_lap** (optional): Infants without seat (default: 0, max: 4)
    - **trip_type** (optional): ONE_WAY or ROUND (default: ONE_WAY)
    - **trip_days** (optional): Days between outbound/return for round trips (default: 7, max: 30)
    - **travel_class** (optional): ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST (default: ECONOMY)
    - **currency** (optional): Currency code (default: "USD")
    - **country_code** (optional): Country code (default: "US")

    ## Example Request
    ```json
    {
      "departure_id": "LAX",
      "arrival_id": "JFK",
      "outbound_date": "2026-04-01",
      "start_date": "2026-04-01",
      "end_date": "2026-04-30",
      "adults": 1,
      "trip_type": "ROUND",
      "trip_days": 7,
      "currency": "USD"
    }
    ```

    ## Example Response
    ```json
    {
      "prices": [
        {
          "departure": "2026-04-01",
          "price": 450.00,
          "return_date": "2026-04-08"
        },
        {
          "departure": "2026-04-02",
          "price": 385.00,
          "return_date": "2026-04-09"
        },
        {
          "departure": "2026-04-03",
          "price": 520.00,
          "return_date": "2026-04-10"
        }
      ],
      "currency": "USD",
      "trip_type": "ROUND"
    }
    ```

    ## Response Fields
    - **prices**: List of daily prices
      - **departure**: Departure date
      - **price**: Price in requested currency
      - **return_date**: Return date (for round trips only)
    - **currency**: Currency code used
    - **trip_type**: Trip type (ONE_WAY or ROUND)

    ## Use Cases
    - **Price comparison**: Find the cheapest day to fly
    - **Calendar integration**: Display prices in a calendar UI
    - **Flexible travel**: Show users price variations across dates
    - **Budget alerts**: Notify when prices drop below threshold

    ## Error Cases
    - **400 Bad Request**: Invalid parameters
    - **503 Service Unavailable**: Google Flights API not configured
    - **500 Internal Server Error**: API request failed or unexpected error
    """
    try:
        result = service.get_calendar_prices(calendar_request)

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to get calendar prices. The Google Flights API may be unavailable."
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting calendar prices: {str(e)}"
        )

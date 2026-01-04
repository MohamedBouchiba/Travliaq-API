"""Flight search and calendar pricing models."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum


class TravelClass(str, Enum):
    """Travel class options."""
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class TripType(str, Enum):
    """Trip type options."""
    ONE_WAY = "ONE_WAY"
    ROUND = "ROUND"


# ========== Flight Search Models ==========

class FlightSearchRequest(BaseModel):
    """Request model for flight search."""
    departure_id: str = Field(..., description="IATA code of departure airport (e.g., 'LAX')")
    arrival_id: str = Field(..., description="IATA code of arrival airport (e.g., 'JFK')")
    outbound_date: date = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: Optional[date] = Field(None, description="Return date for round-trip (YYYY-MM-DD)")

    adults: int = Field(1, ge=1, le=9, description="Number of adults (12+ years)")
    children: int = Field(0, ge=0, le=8, description="Number of children (2-11 years)")
    infant_in_seat: int = Field(0, ge=0, le=4, description="Number of infants requiring a seat")
    infant_on_lap: int = Field(0, ge=0, le=4, description="Number of infants without a seat")

    travel_class: TravelClass = Field(TravelClass.ECONOMY, description="Preferred travel class")
    show_hidden: bool = Field(False, description="Include hidden or restricted flights")

    currency: str = Field("USD", description="Currency code (e.g., 'USD', 'EUR')")
    language_code: str = Field("en-US", description="Language code")
    country_code: str = Field("US", description="Country code")


class FlightDuration(BaseModel):
    """Flight duration details."""
    raw: int = Field(..., description="Duration in minutes")
    text: str = Field(..., description="Human-readable duration (e.g., '2 hr 20 min')")


class Airport(BaseModel):
    """Airport details for departure or arrival."""
    airport_name: str = Field(..., description="Full airport name")
    airport_code: str = Field(..., description="IATA airport code")
    time: str = Field(..., description="Departure or arrival time")


class FlightSegment(BaseModel):
    """Individual flight segment details."""
    departure_airport: Airport = Field(..., description="Departure airport details")
    arrival_airport: Airport = Field(..., description="Arrival airport details")
    duration: FlightDuration = Field(..., description="Flight duration")
    airline: str = Field(..., description="Airline name")
    airline_logo: str = Field(..., description="URL to airline logo")
    flight_number: str = Field(..., description="Flight number")
    aircraft: Optional[str] = Field(None, description="Aircraft type")
    seat: Optional[str] = Field(None, description="Seat type description")
    legroom: Optional[str] = Field(None, description="Legroom information")
    extensions: Optional[list[str]] = Field(None, description="Flight features/amenities")
    travel_class: Optional[str] = Field(None, description="Travel class")
    overnight: Optional[bool] = Field(None, description="Whether flight is overnight")


class Layover(BaseModel):
    """Layover information between flight segments."""
    duration: int = Field(..., description="Layover duration in minutes")
    airport_name: str = Field(..., description="Layover airport name")
    airport_code: str = Field(..., description="Layover airport IATA code")
    duration_label: Optional[str] = Field(None, description="Human-readable duration")
    city: Optional[str] = Field(None, description="Layover city")
    overnight: Optional[bool] = Field(None, description="Whether layover is overnight")


class Baggage(BaseModel):
    """Baggage allowance information."""
    carry_on: Optional[int] = Field(None, description="Number of carry-on bags included")
    checked: Optional[int] = Field(None, description="Number of checked bags included")


class CarbonEmissions(BaseModel):
    """Carbon emissions data for the flight."""
    CO2e: int = Field(..., description="CO2e emissions for this flight in grams")
    typical_for_this_route: int = Field(..., description="Typical CO2e emissions for this route in grams")
    difference_percent: int = Field(..., description="Percentage difference from typical")
    higher: Optional[int] = Field(None, description="Difference in grams from typical")


class FlightItinerary(BaseModel):
    """Complete flight itinerary with all details."""
    flights: Optional[list[FlightSegment]] = Field(None, description="List of flight segments")
    layovers: Optional[list[Layover]] = Field(None, description="Layover information")
    total_duration: Optional[int] = Field(None, description="Total trip duration in minutes")

    # Pricing and booking
    price: float = Field(..., description="Price in specified currency")
    booking_token: Optional[str] = Field(None, description="Token for booking details")

    # Additional details
    carbon_emissions: Optional[CarbonEmissions] = Field(None, description="Carbon emissions data")
    bags: Optional[Baggage] = Field(None, description="Baggage allowance")
    airline_logo: Optional[str] = Field(None, description="URL to primary airline logo")
    delay: Optional[int] = Field(None, description="Delay in minutes")
    self_transfer: Optional[bool] = Field(None, description="Whether transfer is self-organized")

    # Legacy fields for backward compatibility
    departure_time: Optional[str] = Field(None, description="Overall departure time")
    arrival_time: Optional[str] = Field(None, description="Overall arrival time")
    stops: Optional[int] = Field(None, description="Number of stops (0 = non-stop)")
    airline: Optional[str] = Field(None, description="Primary airline")


class FlightSearchResponse(BaseModel):
    """Response model for flight search."""
    itineraries: list[FlightItinerary] = Field(..., description="List of available flights")
    next_token: Optional[str] = Field(None, description="Token to fetch more results")


# ========== Calendar Pricing Models ==========

class CalendarPricesRequest(BaseModel):
    """Request model for calendar prices."""
    departure_id: str = Field(..., description="IATA code of departure airport (e.g., 'LAX')")
    arrival_id: str = Field(..., description="IATA code of arrival airport (e.g., 'JFK')")
    outbound_date: date = Field(..., description="Initial departure date (YYYY-MM-DD)")

    start_date: Optional[date] = Field(None, description="Start of calendar range (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End of calendar range (YYYY-MM-DD)")

    adults: int = Field(1, ge=1, le=9, description="Number of adults (12+ years)")
    children: int = Field(0, ge=0, le=8, description="Number of children (2-11 years)")
    infant_in_seat: int = Field(0, ge=0, le=4, description="Number of infants requiring a seat")
    infant_on_lap: int = Field(0, ge=0, le=4, description="Number of infants without a seat")

    trip_type: TripType = Field(TripType.ONE_WAY, description="Trip type")
    trip_days: int = Field(7, ge=1, le=30, description="Days between outbound and return for round trips")

    travel_class: TravelClass = Field(TravelClass.ECONOMY, description="Preferred travel class")
    currency: str = Field("USD", description="Currency code (e.g., 'USD', 'EUR')")
    country_code: str = Field("US", description="Country code")


class DailyPrice(BaseModel):
    """Price for a specific date."""
    departure: date = Field(..., description="Departure date")
    price: float = Field(..., description="Price in specified currency")
    return_date: Optional[date] = Field(None, description="Return date (for round trips)")


class CalendarPricesResponse(BaseModel):
    """Response model for calendar prices."""
    prices: list[DailyPrice] = Field(..., description="List of prices by date")
    currency: str = Field(..., description="Currency code")
    trip_type: str = Field(..., description="Trip type (ONE_WAY or ROUND)")


# ========== Map Prices Models ==========

class DestinationPrice(BaseModel):
    """Price and date for a destination."""
    price: float = Field(..., description="Cheapest price found")
    date: date = Field(..., description="Date of the cheapest flight")


class MapPricesRequest(BaseModel):
    """Request model for map prices endpoint."""
    origin: str = Field(
        ...,
        description="IATA code of origin airport (e.g., 'CDG')",
        min_length=3,
        max_length=3
    )
    destinations: list[str] = Field(
        ...,
        description="List of destination IATA codes (max 50)",
        min_length=1,
        max_length=50
    )
    adults: int = Field(1, ge=1, le=9, description="Number of adults")
    currency: str = Field("EUR", description="Currency code")

    @field_validator('origin')
    @classmethod
    def validate_origin(cls, v):
        return v.upper()

    @field_validator('destinations')
    @classmethod
    def validate_destinations(cls, v):
        return [code.upper() for code in v]


class MapPricesResponse(BaseModel):
    """Response model for map prices endpoint."""
    success: bool = True
    prices: dict[str, Optional[DestinationPrice]] = Field(
        ...,
        description="IATA code -> {price, date} (null if unavailable)"
    )
    currency: str
    origin: str
    cached_destinations: int = 0
    fetched_destinations: int = 0

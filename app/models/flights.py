"""Flight search and calendar pricing models."""

from pydantic import BaseModel, Field
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


class FlightLeg(BaseModel):
    """Individual flight leg details."""
    departure_airport: str = Field(..., description="Departure airport IATA code")
    arrival_airport: str = Field(..., description="Arrival airport IATA code")
    departure_time: str = Field(..., description="Departure time")
    arrival_time: str = Field(..., description="Arrival time")
    airline: Optional[str] = Field(None, description="Airline name")
    flight_number: Optional[str] = Field(None, description="Flight number")
    duration: FlightDuration


class FlightItinerary(BaseModel):
    """Flight itinerary with all details."""
    departure_time: str = Field(..., description="Overall departure time")
    arrival_time: str = Field(..., description="Overall arrival time")
    duration: FlightDuration
    price: float = Field(..., description="Price in specified currency")
    stops: int = Field(..., description="Number of stops (0 = non-stop)")
    legs: Optional[list[FlightLeg]] = Field(None, description="Individual flight legs")
    airline: Optional[str] = Field(None, description="Primary airline")
    booking_token: Optional[str] = Field(None, description="Token for booking details")


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

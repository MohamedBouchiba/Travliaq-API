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


class Airport(BaseModel):
    """Airport details for departure or arrival."""
    airport_name: str = Field(..., description="Full airport name")
    airport_code: str = Field(..., description="IATA airport code")
    time: str = Field(..., description="Departure or arrival time")


class FlightSegment(BaseModel):
    """Individual flight segment details."""
    departure_airport: Airport = Field(..., description="Departure airport details")
    arrival_airport: Airport = Field(..., description="Arrival airport details")
    duration: int = Field(..., description="Flight duration in minutes")
    airline: str = Field(..., description="Airline name")
    airline_logo: str = Field(..., description="URL to airline logo")
    travel_class: str = Field(..., description="Travel class")
    flight_number: str = Field(..., description="Flight number")
    legroom: Optional[str] = Field(None, description="Legroom information")
    extensions: Optional[list[str]] = Field(None, description="Flight features/amenities")
    overnight: Optional[bool] = Field(None, description="Whether flight is overnight")
    airplane: Optional[str] = Field(None, description="Aircraft type")


class Layover(BaseModel):
    """Layover information between flight segments."""
    duration: int = Field(..., description="Layover duration in minutes")
    name: str = Field(..., description="Layover airport name")
    id: str = Field(..., description="Layover airport IATA code")
    overnight: Optional[bool] = Field(None, description="Whether layover is overnight")


class Baggage(BaseModel):
    """Baggage allowance information."""
    carry_on: bool = Field(..., description="Carry-on bag included")
    checked: Optional[int] = Field(None, description="Number of checked bags included")


class CarbonEmissions(BaseModel):
    """Carbon emissions data for the flight."""
    this_flight: int = Field(..., description="CO2e emissions for this flight in grams")
    typical_for_this_route: int = Field(..., description="Typical CO2e emissions for this route in grams")
    difference_percent: int = Field(..., description="Percentage difference from typical")


class FlightItinerary(BaseModel):
    """Complete flight itinerary with all details."""
    flights: list[FlightSegment] = Field(..., description="List of flight segments")
    layovers: Optional[list[Layover]] = Field(None, description="Layover information")
    total_duration: int = Field(..., description="Total trip duration in minutes")

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

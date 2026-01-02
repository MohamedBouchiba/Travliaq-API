"""Mapper to transform Viator API responses to simplified format."""

from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ViatorMapper:
    """Transform Viator API responses to simplified format for frontend."""

    @staticmethod
    def map_product_summary(product: dict) -> dict:
        """
        Transform Viator ProductSummary to simplified Activity format.

        Args:
            product: ProductSummary from Viator API

        Returns:
            Simplified activity dict
        """
        # Extract images
        images = []
        if product.get("images"):
            for img in product["images"]:
                variants = {}
                if img.get("variants"):
                    for variant in img["variants"]:
                        height = variant.get("height", 0)
                        if height <= 200:
                            variants["small"] = variant["url"]
                        elif height <= 600:
                            variants["medium"] = variant["url"]
                        else:
                            variants["large"] = variant["url"]

                images.append({
                    "url": img["variants"][0]["url"] if img.get("variants") else "",
                    "is_cover": img.get("isCover", False),
                    "variants": variants
                })

        # Extract pricing
        pricing_info = product.get("pricing", {})
        pricing_summary = pricing_info.get("summary", {})

        pricing = {
            "from_price": pricing_summary.get("fromPrice", 0),
            "currency": pricing_info.get("currency", "EUR"),
            "original_price": pricing_summary.get("fromPriceBeforeDiscount"),
            "is_discounted": pricing_summary.get("fromPriceBeforeDiscount") is not None
        }

        # Extract rating
        reviews = product.get("reviews", {})
        rating = {
            "average": reviews.get("combinedAverageRating", 0),
            "count": reviews.get("totalReviews", 0)
        }

        # Extract duration
        duration_obj = product.get("duration", {})
        duration_minutes = duration_obj.get("fixedDurationInMinutes", 0)

        duration = {
            "minutes": duration_minutes,
            "formatted": ViatorMapper._format_duration(duration_minutes)
        }

        # Extract destination
        destinations = product.get("destinations", [])
        primary_dest = destinations[0] if destinations else {}

        location = {
            "destination": primary_dest.get("name", "Unknown"),
            "country": primary_dest.get("country", "Unknown")
        }

        # Extract categories (tags → simple category names)
        tags = product.get("tags", [])
        categories = ViatorMapper._map_tags_to_categories(tags)

        # Build simplified activity
        return {
            "id": product.get("productCode"),
            "title": product.get("title", ""),
            "description": product.get("description", ""),
            "images": images,
            "pricing": pricing,
            "rating": rating,
            "duration": duration,
            "categories": categories,
            "flags": product.get("flags", []),
            "booking_url": product.get("productUrl", ""),
            "confirmation_type": product.get("confirmationType", "UNKNOWN"),
            "location": location,
            "availability": "available"  # Default - would need /availability/check for real status
        }

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """Format duration in minutes to human-readable string."""
        if minutes == 0:
            return "Flexible"

        hours = minutes // 60
        mins = minutes % 60

        if hours > 0 and mins > 0:
            return f"{hours}h {mins}min"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{mins}min"

    @staticmethod
    def _map_tags_to_categories(tags: list[int]) -> list[str]:
        """
        Convert Viator tag IDs to string representations.

        NOTE: This is a temporary simple implementation. Tag IDs are converted to strings.
        For production, this should be enhanced to:
        - Look up tag names from MongoDB tags collection
        - Map to user-friendly category names
        - Support multilingual tag names

        Args:
            tags: List of Viator tag IDs

        Returns:
            List of tag IDs as strings (or ["general"] if no tags)
        """
        # For now, convert tag IDs to strings to preserve information
        # Frontend can look up tag names from /tags endpoint if needed
        if not tags:
            return ["general"]

        # Return first 5 tags as strings to avoid too many categories
        return [f"tag_{tag_id}" for tag_id in tags[:5]]

    @staticmethod
    def extract_location_refs(product: dict) -> list[str]:
        """
        Extract location reference codes from product details.
        
        Look for:
        - logistics.start.location.ref
        - logistics.end.location.ref
        - itinerary.pointsOfInterest[].location.ref
        
        Args:
            product: Product details from Viator API
            
        Returns:
            List of location reference codes
        """
        refs = set()
        
        # Check logistics start/end
        logistics = product.get("logistics", {})
        
        # Start points
        for start_point in logistics.get("start", []):
            ref = ViatorMapper._get_location_ref(start_point)
            if ref:
                refs.add(ref)
                
        # End points
        for end_point in logistics.get("end", []):
            ref = ViatorMapper._get_location_ref(end_point)
            if ref:
                refs.add(ref)
                
        # Check itinerary points of interest
        itinerary = product.get("itinerary", {})
        for day in itinerary.get("days", []):
            for item in day.get("items", []):
                point_of_interest = item.get("pointOfInterest", {})
                ref = ViatorMapper._get_location_ref(point_of_interest)
                if ref:
                    refs.add(ref)
                    
        return list(refs)

    @staticmethod
    def _get_location_ref(obj: dict) -> Optional[str]:
        """Helper to safely extract location ref from nested object."""
        return obj.get("location", {}).get("ref")

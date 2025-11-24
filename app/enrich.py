from __future__ import annotations
from typing import Any, Dict, List
from jsonschema import Draft7Validator
from .normalize import normalize_row_to_schema_props

def compute_applicability(n: Dict[str, Any]) -> Dict[str, str]:
    status: Dict[str, str] = {}

    def set_status(key: str, value: Any, na: bool = False):
        if na:
            status[key] = "not_applicable"
        else:
            status[key] = "answered" if (value is not None and value != [] and value != {}) else "unknown"

    for key in [
        "id","user_id","email","travel_group","number_of_travelers","has_destination",
        "destination","departure_location","climate_preference","travel_affinities",
        "travel_ambiance","dates_type","departure_date","return_date","flexibility",
        "has_approximate_departure_date","approximate_departure_date","duration",
        "exact_nights","budget","budget_type","budget_amount","budget_currency",
        "styles","rhythm","flight_preference","luggage","mobility","accommodation_type",
        "comfort","neighborhood","amenities","constraints","additional_info",
        "created_at","updated_at"
    ]:
        status[key] = "unknown"

    tg = n.get("travel_group")
    if tg in ("En famille","Groupe (3-5)"):
        set_status("number_of_travelers", n.get("number_of_travelers"))
    else:
        set_status("number_of_travelers", n.get("number_of_travelers"), na=True)

    hd = n.get("has_destination")
    if hd in ("Oui","Yes"):
        set_status("destination", n.get("destination"))
        set_status("departure_location", n.get("departure_location"))
        set_status("climate_preference", n.get("climate_preference"), na=True)
    elif hd in ("Non","No"):
        set_status("destination", n.get("destination"), na=True)
        set_status("departure_location", n.get("departure_location"), na=True)
        set_status("climate_preference", n.get("climate_preference"))
    else:
        set_status("destination", n.get("destination"))
        set_status("departure_location", n.get("departure_location"))
        set_status("climate_preference", n.get("climate_preference"))

    dt = n.get("dates_type")
    if dt == "Dates fixes":
        set_status("departure_date", n.get("departure_date"))
        set_status("return_date", n.get("return_date"))
        set_status("duration", n.get("duration"), na=True)
        set_status("flexibility", n.get("flexibility"), na=True)
        set_status("has_approximate_departure_date", n.get("has_approximate_departure_date"), na=True)
        set_status("approximate_departure_date", n.get("approximate_departure_date"), na=True)
        set_status("exact_nights", n.get("exact_nights"), na=True)
    elif dt == "Dates flexibles":
        set_status("duration", n.get("duration"))
        set_status("flexibility", n.get("flexibility"))
        set_status("has_approximate_departure_date", n.get("has_approximate_departure_date"))
        set_status("approximate_departure_date", n.get("approximate_departure_date"))
        set_status("departure_date", n.get("departure_date"), na=True)
        set_status("return_date", n.get("return_date"), na=True)
        if n.get("duration") == "+14 nuits":
            set_status("exact_nights", n.get("exact_nights"))
        else:
            set_status("exact_nights", n.get("exact_nights"), na=True)
    else:
        set_status("duration", n.get("duration"))
        set_status("flexibility", n.get("flexibility"))
        set_status("has_approximate_departure_date", n.get("has_approximate_departure_date"))
        set_status("approximate_departure_date", n.get("approximate_departure_date"))
        set_status("departure_date", n.get("departure_date"))
        set_status("return_date", n.get("return_date"))
        set_status("exact_nights", n.get("exact_nights"))

    if n.get("budget_type") == "Montant précis":
        set_status("budget_amount", n.get("budget_amount"))
        set_status("budget_currency", n.get("budget_currency"))
    else:
        set_status("budget_amount", n.get("budget_amount"), na=True)
        set_status("budget_currency", n.get("budget_currency"), na=True)

    for k in ["id","user_id","email","travel_group","has_destination","travel_affinities",
              "travel_ambiance","styles","rhythm","flight_preference","luggage","mobility",
              "accommodation_type","comfort","neighborhood","amenities","constraints",
              "additional_info","created_at","updated_at"]:
        set_status(k, n.get(k))

    return status

def build_enriched(row: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_row_to_schema_props(row)
    status = compute_applicability(normalized)

    validator = Draft7Validator(schema)
    errors: List[str] = [f"{e.json_path or '<root>'}: {e.message}" for e in validator.iter_errors(normalized)]
    valid = len(errors) == 0

    enriched = {
        "schema": {"$id": schema.get("$id"), "$schema": schema.get("$schema")},
        "meta": {
            "response_id": normalized.get("id"),
            "user_id": normalized.get("user_id"),
            "email": normalized.get("email"),
            "created_at": normalized.get("created_at"),
            "updated_at": normalized.get("updated_at"),
            "source": "db/supabase"
        },
        "answers": {k: {"value": normalized.get(k), "status": status.get(k)} for k in normalized.keys()},
        "normalized": normalized,
        "validation": {"valid": valid, "errors": errors}
    }
    return enriched

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from .mappings import (
    TRAVEL_GROUP_MAP, DATES_TYPE_MAP, FLEXIBILITY_MAP, DURATION_MAP, BUDGET_BAND_MAP,
    BUDGET_TYPE_MAP, BUDGET_CURRENCY_MAP, FLIGHT_PREF_MAP, COMFORT_MAP,
    NEIGHBORHOOD_MAP, ACCOM_TYPE_MAP, AMENITIES_MAP, CLIMATE_MAP, TRAVEL_AMBIANCE_MAP,
    RHYTHM_MAP, MOBILITY_CANONICAL, TRANSPORT_MODES, LUGGAGE_MAP
)

def _none_if_empty(v: Any) -> Optional[Any]:
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v

def _ensure_list(v: Any) -> Optional[List[Any]]:
    if v is None:
        return None
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                return json.loads(s)
            except Exception:
                pass
        return [s]
    return [v]

def _map_list(values: Optional[List[str]], mapping: Dict[str, str]) -> Optional[List[str]]:
    if values is None:
        return None
    out = []
    for x in values:
        if x is None:
            continue
        key = str(x).strip()
        out.append(mapping.get(key, key))
    seen = set()
    dedup = []
    for x in out:
        if x not in seen:
            seen.add(x)
            dedup.append(x)
    return dedup

def normalize_row_to_schema_props(row: Dict[str, Any]) -> Dict[str, Any]:
    n: Dict[str, Any] = {}

    n["id"] = str(row.get("id")) if row.get("id") is not None else None
    n["user_id"] = str(row.get("user_id")) if row.get("user_id") is not None else None
    n["email"] = _none_if_empty(row.get("email"))

    tg = row.get("travel_group")
    if tg is not None:
        tg = TRAVEL_GROUP_MAP.get(tg, tg)
    n["travel_group"] = tg
    n["number_of_travelers"] = row.get("number_of_travelers")

    hd = row.get("has_destination")
    if hd in ("Oui","Yes","Non","No"):
        n["has_destination"] = hd
    else:
        n["has_destination"] = _none_if_empty(hd)

    n["destination"] = _none_if_empty(row.get("destination"))
    n["departure_location"] = _none_if_empty(row.get("departure_location"))

    cp_list = _ensure_list(row.get("climate_preference"))
    cp_list = _map_list(cp_list, CLIMATE_MAP)
    n["climate_preference"] = cp_list

    ta_list = _ensure_list(row.get("travel_affinities"))
    n["travel_affinities"] = ta_list

    amb = row.get("travel_ambiance")
    if amb is not None:
        amb = TRAVEL_AMBIANCE_MAP.get(amb, amb)
    n["travel_ambiance"] = amb

    dt = row.get("dates_type")
    if dt is not None:
        dt = DATES_TYPE_MAP.get(dt, dt)
    n["dates_type"] = dt

    n["departure_date"] = str(row.get("departure_date")) if row.get("departure_date") else None
    n["return_date"] = str(row.get("return_date")) if row.get("return_date") else None

    flex = row.get("flexibility")
    if flex is not None:
        flex = FLEXIBILITY_MAP.get(flex, flex)
    n["flexibility"] = flex

    n["has_approximate_departure_date"] = row.get("has_approximate_departure_date")
    n["approximate_departure_date"] = str(row.get("approximate_departure_date")) if row.get("approximate_departure_date") else None

    dur = row.get("duration")
    if dur is not None:
        dur = DURATION_MAP.get(dur, dur)
    n["duration"] = dur
    n["exact_nights"] = row.get("exact_nights")

    b = row.get("budget")
    if b is not None:
        b = BUDGET_BAND_MAP.get(b, b)
    n["budget"] = b

    bt = row.get("budget_type")
    if bt is not None:
        bt = BUDGET_TYPE_MAP.get(bt, bt)
    n["budget_type"] = bt

    n["budget_amount"] = float(row["budget_amount"]) if row.get("budget_amount") is not None else None

    bc = row.get("budget_currency")
    if bc is not None:
        bc = BUDGET_CURRENCY_MAP.get(bc, bc)
    n["budget_currency"] = bc

    st_list = _ensure_list(row.get("styles"))
    n["styles"] = st_list

    rh = row.get("rhythm")
    if rh is not None:
        rh = RHYTHM_MAP.get(rh, rh)
    n["rhythm"] = rh

    fp = row.get("flight_preference")
    if fp is not None:
        fp = FLIGHT_PREF_MAP.get(fp, fp)
    n["flight_preference"] = fp

    lug = row.get("luggage")
    if isinstance(lug, dict):
        new_lug = {str(k): LUGGAGE_MAP.get(v, v) for k, v in lug.items()}
        n["luggage"] = new_lug
    else:
        if isinstance(lug, str) and lug.strip().startswith("{"):
            try:
                d = json.loads(lug.replace("'", '"'))
                new_lug = {str(k): LUGGAGE_MAP.get(v, v) for k, v in d.items()}
                n["luggage"] = new_lug
            except Exception:
                n["luggage"] = None
        else:
            n["luggage"] = None

    mob_list = _ensure_list(row.get("mobility"))
    if mob_list:
        if all((str(x) in TRANSPORT_MODES) for x in mob_list):
            n["mobility"] = ["Aucun problème de mobilité"]
        else:
            filtered = [x for x in mob_list if str(x) in MOBILITY_CANONICAL]
            n["mobility"] = filtered or ["Aucun problème de mobilité"]
    else:
        n["mobility"] = None

    ac_list = _ensure_list(row.get("accommodation_type"))
    ac_list = _map_list(ac_list, ACCOM_TYPE_MAP)
    n["accommodation_type"] = ac_list

    cf = row.get("comfort")
    if cf is not None:
        cf = COMFORT_MAP.get(cf, cf)
    n["comfort"] = cf

    nb = row.get("neighborhood")
    if nb is not None:
        nb = NEIGHBORHOOD_MAP.get(nb, nb)
    n["neighborhood"] = nb

    am_list = _ensure_list(row.get("amenities"))
    am_list = _map_list(am_list, AMENITIES_MAP)
    n["amenities"] = am_list

    cs_list = _ensure_list(row.get("constraints"))
    n["constraints"] = cs_list

    n["additional_info"] = _none_if_empty(row.get("additional_info"))
    n["created_at"] = row.get("created_at").isoformat() if row.get("created_at") else None
    n["updated_at"] = row.get("updated_at").isoformat() if row.get("updated_at") else None

    return n

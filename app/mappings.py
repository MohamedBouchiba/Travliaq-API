from __future__ import annotations
from typing import Dict

TRAVEL_GROUP_MAP: Dict[str, str] = {
    "Solo": "Solo",
    "Duo": "En duo",
    "En duo": "En duo",
    "Groupe 3-5": "Groupe (3-5)",
    "Groupe (3-5)": "Groupe (3-5)",
    "Famille": "En famille",
    "En famille": "En famille",
    "Famille (enfants <12)": "En famille",
}

DATES_TYPE_MAP = {
    "Je suis flexible": "Dates flexibles",
    "I'm flexible": "Dates flexibles",
    "Dates flexibles": "Dates flexibles",
    "Dates fixes": "Dates fixes",
}

FLEXIBILITY_MAP = {
    "±1 jour": "±1 jour",
    "±3 jours": "±2-3 jours",
    "±2-3 jours": "±2-3 jours",
    "±1 semaine": "±1 semaine",
    "Totalement flexible": "Totalement flexible",
    "±3j": "±2-3 jours",
    "±7j": "±1 semaine",
}

DURATION_MAP = {
    "2 nuits": "2 nuits",
    "3 nuits": "3 nuits",
    "4 nuits": "4 nuits",
    "5 nuits": "5 nuits",
    "6 nuits": "6 nuits",
    "7 nuits": "7 nuits",
    "8-10 nuits": "8 à 10 nuits",
    "8 à 10 nuits": "8 à 10 nuits",
    "11-14 nuits": "11 à 14 nuits",
    "11 à 14 nuits": "11 à 14 nuits",
    ">14 nuits": "+14 nuits",
    "+14 nuits": "+14 nuits",
}

BUDGET_BAND_MAP = {
    "Je ne sais pas": "Je ne sais pas",
    "Montant précis": "Montant précis",
    "Moins de 300€": "Moins de 300€",
    "300-600€": "300-600€",
    "600-900€": "600-900€",
    "900-1200€": "900-1200€",
    "1200-1800€": "1200-1800€",
    "Plus de 1800€": "Plus de 1800€",
    ">1 800€": "Plus de 1800€",
    "1 200-1 800€": "1200-1800€",
}

BUDGET_TYPE_MAP = {
    "Montant précis": "Montant précis",
    "Budget précis": "Montant précis",
}

BUDGET_CURRENCY_MAP = {
    "EUR": "EUR",
    "USD": "USD",
    "GBP": "GBP",
}

FLIGHT_PREF_MAP = {
    "Uniquement vol direct": "Uniquement vol direct",
    "Direct uniquement": "Uniquement vol direct",
    "Max 1 escale": "Max 1 escale",
    "Peu importe": "Peu importe (prix avant tout)",
    "Peu importe (prix avant tout)": "Peu importe (prix avant tout)",
}

COMFORT_MAP = {
    "Note ≥7,5/10": "Note ≥7,5/10",
    "Note ≥8,0/10": "Note ≥8,0/10",
    "Note ≥8,5/10": "Note ≥8,5/10",
    "Peu importe": "Peu importe",
    "Note ≥8.5": "Note ≥8,5/10",
    "Note ≥8.0": "Note ≥8,0/10",
    "Note ≥7.5": "Note ≥7,5/10",
}

NEIGHBORHOOD_MAP = {
    "Calme et reposant": "Calme et reposant",
    "Centre-ville animé": "Centre-ville animé",
    "Proche nature/plage": "Proche nature/plage",
    "Atypique et charmant": "Atypique et charmant",
}

ACCOM_TYPE_MAP = {
    "Hôtel": "Hôtel",
    "Appartement/Airbnb": "Appartement/Airbnb",
    "Maison d'hôtes": "Maison d'hôtes",
    "Auberge de jeunesse": "Auberge de jeunesse",
    "Resort all-inclusive": "Resort all-inclusive",
    "Camping/Glamping": "Camping/Glamping",
    "Camping/glamping": "Camping/Glamping",
    "Resort": "Resort all-inclusive",
}

AMENITIES_MAP = {
    "Wi-Fi fiable": "Wi-Fi fiable",
    "Climatisation": "Climatisation",
    "Cuisine équipée": "Cuisine équipée",
    "Lave-linge": "Lave-linge",
    "Parking": "Parking",
    "Ascenseur": "Ascenseur",
    "Réception 24h/24": "Réception 24h/24",
    "Proche lieu de culte": "Proche lieu de culte",
    "Lit bébé": "Lit bébé",
    "Chambre familiale": "Chambre familiale",
    "Piscine": "Piscine",
    "Salle de sport": "Salle de sport",
    "Spa": "Spa",
    "Jardin/Terrasse": "Jardin/Terrasse",
    "Cuisine": "Cuisine équipée",
    "Proximité lieu de culte": "Proche lieu de culte",
}

CLIMATE_MAP = {
    "Chaud & ensoleillé": "Chaud et ensoleillé",
    "Chaud et ensoleillé": "Chaud et ensoleillé",
    "Doux & tempéré": "Doux et tempéré",
    "Doux et tempéré": "Doux et tempéré",
    "Froid & neigeux": "Froid et neige",
    "Froid et neige": "Froid et neige",
    "Tropical & humide": "Tropical et humide",
    "Tropical et humide": "Tropical et humide",
    "Montagne & altitude": "Montagne et altitude",
    "Montagne et altitude": "Montagne et altitude",
    "Peu importe": "Peu importe",
}

TRAVEL_AMBIANCE_MAP = {
    "Détente totale": "Détente totale",
    "Aventure & découverte": "Aventure & découverte",
    "Culture & patrimoine": "Culture & patrimoine",
    "Fête & vie nocturne": "Fête & vie nocturne",
    "Nature & ressourcement": "Nature & ressourcement",
}

RHYTHM_MAP = {
    "Cool": "Cool (2-3h d'activités/jour)",
    "Équilibré": "Équilibré (4-6h d'activités/jour)",
    "Intense": "Intense (7h+ d'activités/jour)",
    "Cool (2-3h d'activités/jour)": "Cool (2-3h d'activités/jour)",
    "Équilibré (4-6h d'activités/jour)": "Équilibré (4-6h d'activités/jour)",
    "Intense (7h+ d'activités/jour)": "Intense (7h+ d'activités/jour)",
}

MOBILITY_CANONICAL = {
    "Aucun problème de mobilité",
    "Mobilité réduite (fauteuil roulant)",
    "Mobilité limitée (canne, déambulateur)",
    "Besoin d'ascenseurs",
    "Éviter les escaliers",
    "Voyageur avec bébé/enfant en bas âge",
}

TRANSPORT_MODES = {
    "Transports en commun",
    "Location de voiture",
    "Vélo",
    "À pied",
    "Scooter/Moto",
    "Location voiture",
    "Moto/scooter",
    "Transport atypique",
}

LUGGAGE_MAP = {
    "Cabine uniquement": "Cabine uniquement",
    "1 bagage en soute": "1 bagage en soute",
    "2 bagages en soute": "2 bagages en soute",
    "Objet personnel + cabine": "Cabine uniquement",
    "Objet personnel": "Cabine uniquement",
    "Cabine + soute": "1 bagage en soute",
    "Cabin baggage": "Cabine uniquement",
}

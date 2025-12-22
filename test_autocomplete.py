#!/usr/bin/env python3
"""
Script de test pour l'endpoint d'autocomplétion.
Usage: python test_autocomplete.py
"""

import requests
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def test_autocomplete(
    query: str,
    limit: int = 10,
    types: str = "city,airport,country"
) -> Dict[str, Any]:
    """Test l'endpoint d'autocomplétion."""
    url = f"{BASE_URL}/autocomplete"

    params = {
        "q": query,
        "limit": limit,
        "types": types
    }

    print(f"\n{'='*60}")
    print(f"🔍 Recherche: '{query}' (limit: {limit}, types: {types})")
    print(f"{'='*60}")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        print(f"\n✅ Statut: {response.status_code}")
        print(f"📊 Résultats trouvés: {len(data['results'])}")

        if data['results']:
            print(f"\n📍 Résultats:")
            for i, result in enumerate(data['results'], 1):
                icon = {
                    'country': '🌍',
                    'city': '🏙️',
                    'airport': '✈️'
                }.get(result['type'], '📍')

                lat_lon = ""
                if result.get('lat') and result.get('lon'):
                    lat_lon = f" ({result['lat']:.4f}, {result['lon']:.4f})"

                print(f"   {i}. {icon} {result['label']}{lat_lon}")
                print(f"      Type: {result['type']}")
                print(f"      ID: {result['id']}")
                print(f"      Country: {result['country_code']}")
                print(f"      Slug: {result['slug']}")
                print()
        else:
            if len(query.strip()) < 3:
                print("\n⚠️  Query < 3 caractères → résultats vides (comportement normal)")
            else:
                print("\n⚠️  Aucun résultat trouvé")

        return data

    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur")
        print("💡 Assurez-vous que le serveur est lancé: uvicorn app.main:app --reload")
        return {}

    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP: {e}")
        print(f"   Réponse: {response.text}")
        return {}

    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return {}


def test_health():
    """Teste le endpoint de santé."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print("✅ Serveur en ligne et opérationnel")
        return True
    except:
        print("❌ Serveur hors ligne ou inaccessible")
        return False


def main():
    """Exécute une série de tests."""

    print("🚀 Test de l'API d'autocomplétion")
    print("="*60)

    # Vérifier que le serveur est en ligne
    if not test_health():
        print("\n💡 Lancez le serveur avec: uvicorn app.main:app --reload")
        return

    # Tests de recherche
    test_cases = [
        ("par", 10, "city,airport,country"),    # Recherche de "Paris" - tous types
        ("CDG", 5, "airport"),                   # Code aéroport - filtré
        ("Fran", 10, "country"),                 # Recherche de pays - filtré
        ("New", 10, "city,airport"),             # Villes et aéroports uniquement
        ("Lon", 10, "city,airport,country"),     # "London" - tous types
        ("Pa", 5, "city,airport,country"),       # 2 caractères - devrait retourner []
        ("A", 3, "city,airport,country"),        # 1 caractère - devrait retourner []
    ]

    for query, limit, types in test_cases:
        test_autocomplete(query, limit, types)

    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)

    print("\n📚 Pour plus d'infos, consultez:")
    print(f"   - Swagger UI: {BASE_URL}/docs")
    print(f"   - ReDoc: {BASE_URL}/redoc")
    print(f"   - Documentation: AUTOCOMPLETE_API.md")


if __name__ == "__main__":
    main()

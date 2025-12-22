#!/usr/bin/env python3
"""
Script de test pour l'endpoint d'autocomplétion.
Usage: python test_autocomplete.py
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def test_autocomplete(query: str, limit: int = 5) -> Dict[str, Any]:
    """Test l'endpoint d'autocomplétion."""
    url = f"{BASE_URL}/search/autocomplete"

    payload = {
        "query": query,
        "limit": limit
    }

    print(f"\n{'='*60}")
    print(f"🔍 Recherche: '{query}' (limit: {limit})")
    print(f"{'='*60}")

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()

        print(f"\n✅ Statut: {response.status_code}")
        print(f"📊 Résultats trouvés: {data['count']}")

        if data['results']:
            print(f"\n📍 Résultats:")
            for i, result in enumerate(data['results'], 1):
                icon = {
                    'country': '🌍',
                    'city': '🏙️',
                    'airport': '✈️'
                }.get(result['type'], '📍')

                print(f"   {i}. {icon} {result['label']}")
                print(f"      Type: {result['type']}")
                print(f"      Ref: {result['ref']}")
                print(f"      Country: {result['country_code']}")
                print(f"      Slug: {result['slug']}")
                print()
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
        ("Par", 5),          # Recherche de "Paris"
        ("CDG", 3),          # Code aéroport
        ("Fran", 5),         # Recherche de pays
        ("New", 5),          # Recherche de ville
        ("Lon", 5),          # "London"
        ("A", 3),            # Recherche courte (1 caractère)
    ]

    for query, limit in test_cases:
        test_autocomplete(query, limit)

    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)

    print("\n📚 Pour plus d'infos, consultez:")
    print(f"   - Swagger UI: {BASE_URL}/docs")
    print(f"   - ReDoc: {BASE_URL}/redoc")
    print(f"   - Documentation: AUTOCOMPLETE_API.md")


if __name__ == "__main__":
    main()

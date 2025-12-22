# Travliaq API

Microservice FastAPI pour:
1. **POI Details**: Récupérer et enrichir les informations d'un Point of Interest (POI)
2. **Search Autocomplete** ⭐: Autocomplétion de recherche de lieux (pays, villes, aéroports)

## Fonctionnalités

### POI Details
- Endpoint `POST /poi-details` pour retourner un POI normalisé
- Persistance MongoDB avec clé canonique `poi_key` et index sur `poi_key` / `place_id`
- Enrichissement via Google Places (Essentials), OpenTripMap (free), Wikidata
- Règles de complétude et TTL (par défaut 365 jours) pour éviter les appels externes inutiles

### Search Autocomplete ⭐ NEW
- Endpoint `POST /search/autocomplete` pour l'autocomplétion de recherche
- Support pays, villes et aéroports
- Recherche intelligente avec priorité et rang de pertinence
- Vue PostgreSQL/Supabase optimisée
- **Documentation complète**: [AUTOCOMPLETE_API.md](AUTOCOMPLETE_API.md)

## Démarrage local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Variables d'environnement
Ajoutez un fichier `.env` (voir `.env.example`) avec :

### MongoDB (POI Details)
- `MONGODB_URI`
- `MONGODB_DB`
- `MONGODB_COLLECTION_POI` (optionnel, défaut `poi_details`)

### PostgreSQL/Supabase (Search Autocomplete)
- `PG_HOST`
- `PG_DATABASE`
- `PG_USER`
- `PG_PASSWORD`
- `PG_PORT` (optionnel, défaut `5432`)
- `PG_SSLMODE` (optionnel, défaut `require`)

### API Keys
- `GOOGLE_MAPS_API_KEY`
- `GEOAPIFY_API_KEY`

## Utilisation
Requête :
```http
POST /poi-details
Content-Type: application/json
{
  "poi_name": "Senso-ji Temple",
  "city": "Tokyo",
  "detail_types": ["hours", "pricing", "contact", "facts"]
}
```

Réponse (exemple abrégé) :
```json
{
  "name": "Senso-ji Temple",
  "city": "Tokyo",
  "country": "Japan",
  "location": {"lat": 35.7148, "lng": 139.7967},
  "hours": {"weekly": {...}, "raw": {...}},
  "pricing": {"admission_type": "unknown"},
  "contact": {"phone": "+81 ...", "website": "https://..."},
  "facts": {"year_built": 645, "unesco_site": false},
  "sources": {"google_places": {...}},
  "last_updated": "2025-12-01T10:00:00Z",
  "poi_key": "senso-ji-temple__tokyo",
  "place_id": "..."
}
```

## Docker
```
docker build -t poi-details-api .
docker run -p 8000:8000 --env-file .env poi-details-api
```

La santé du conteneur est vérifiée via `GET /health`.

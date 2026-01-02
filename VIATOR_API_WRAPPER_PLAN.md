# Plan Détaillé - Wrapper API Viator pour Travliaq

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Analyse de l'API Viator](#analyse-de-lapi-viator)
3. [Endpoints Travliaq-API (Wrapper)](#endpoints-travliaq-api-wrapper)
4. [Architecture et Structure de Code](#architecture-et-structure-de-code)
5. [Stratégie Cache Redis](#stratégie-cache-redis)
6. [Stratégie MongoDB](#stratégie-mongodb)
7. [Modèles de Données](#modèles-de-données)
8. [Gestion des Erreurs](#gestion-des-erreurs)
9. [Plan d'implémentation](#plan-dimplémentation)

---

## 🎯 Vue d'ensemble

### Objectif
Créer un wrapper simple et efficace autour de l'API Viator qui :
- Masque la complexité de l'API externe
- Fournit des endpoints simples pour le frontend/agents
- Met en cache les résultats (Redis + MongoDB)
- Retourne uniquement les données essentielles

### MVP - Fonctionnalités Minimales

**Endpoint principal** : Recherche d'activités par ville + date

**Entrées** :
- Ville (nom ou destination ID)
- Date (ou plage de dates)
- Position géographique (lat/lon) optionnelle
- Affinités/catégories (optionnel)

**Sorties** :
- Liste d'activités avec :
  - Prix (fromPrice)
  - Disponibilité
  - Images (URL et variants)
  - Rating
  - Durée
  - Catégories/tags
  - Lien de réservation
  - Description

---

## 🔍 Analyse de l'API Viator

### Endpoints Viator Disponibles (Pertinents)

#### 1. **`POST /products/search`** ⭐ Principal
- **Usage** : Rechercher des produits/activités par destination, dates, prix, tags, etc.
- **Inputs** :
  - `filtering.destination` (required) : ID de destination Viator
  - `filtering.startDate` / `endDate` : Plage de dates (YYYY-MM-DD)
  - `filtering.tags[]` : Catégories (food, museums, adventure, etc.)
  - `filtering.lowestPrice` / `highestPrice` : Fourchette de prix
  - `filtering.rating` : Note minimum/maximum
  - `filtering.durationInMinutes` : Durée
  - `filtering.flags[]` : FREE_CANCELLATION, LIKELY_TO_SELL_OUT, etc.
  - `sorting.sort` : DEFAULT, PRICE, TRAVELER_RATING, etc.
  - `pagination.start` / `count` : Pagination (max 50 par page)
  - `currency` (required) : EUR, USD, etc.
- **Output** :
  - `products[]` : Liste de ProductSummary
  - `totalCount` : Nombre total de résultats

#### 2. **`POST /search/freetext`**
- **Usage** : Recherche libre par texte (produits, attractions, destinations)
- **Inputs** :
  - `searchTerm` : Texte libre (ex: "big ben")
  - `productFiltering` : Mêmes filtres que /products/search
  - `searchTypes[]` : PRODUCTS, ATTRACTIONS, DESTINATIONS
  - `pagination`, `currency`
- **Output** : Résultats mixtes (produits + attractions + destinations)

#### 3. **`GET /availability/schedules/{product-code}`**
- **Usage** : Obtenir la disponibilité détaillée d'un produit
- **Output** : Horaires, prix détaillés, options de produit

#### 4. **`POST /availability/check`**
- **Usage** : Vérifier disponibilité réelle avant réservation
- **Inputs** :
  - `productCode`
  - `travelDate`
  - `currency`
  - `paxMix[]` : Nombre de voyageurs (ADULT, CHILD, etc.)

#### 5. **`POST /attractions/search`**
- **Usage** : Rechercher des attractions par destination
- **Inputs** :
  - `destinationId`
- **Output** : Liste d'attractions avec produits mappés

#### 6. **`GET /destinations`**
- **Usage** : Liste de toutes les destinations Viator
- **Output** : Hiérarchie de destinations (pays → villes)

#### 7. **`POST /locations/bulk`**
- **Usage** : Obtenir les détails de localisation par référence
- **Inputs** :
  - `locationReferences[]`

#### 8. **`GET /products/tags`**
- **Usage** : Liste de tous les tags/catégories disponibles
- **Output** : Mapping ID → nom de catégorie

---

## 🎨 Endpoints Travliaq-API (Wrapper)

### Design Proposé : **1 Endpoint Unifié + Endpoints Spécialisés**

### 1. **`POST /api/v1/activities/search`** ⭐ Endpoint Principal (MVP)

**Description** : Recherche d'activités avec support ville OU position géographique

**Request Body** :
```json
{
  "location": {
    "city": "Paris",           // Option 1: Nom de ville
    "country_code": "FR",      // Optionnel mais recommandé
    // OU
    "destination_id": "77",    // Option 2: ID destination Viator direct
    // OU
    "geo": {                   // Option 3: Position géographique
      "lat": 48.8566,
      "lon": 2.3522,
      "radius_km": 50          // Rayon de recherche
    }
  },
  "dates": {
    "start": "2026-03-15",     // Date de début (YYYY-MM-DD)
    "end": "2026-03-20"        // Date de fin (optionnel)
  },
  "filters": {
    "categories": ["food", "museum", "adventure"],  // Tags/affinités
    "price_range": {
      "min": 10,
      "max": 200
    },
    "rating_min": 4.0,
    "duration_minutes": {
      "min": 60,
      "max": 480
    },
    "flags": ["FREE_CANCELLATION", "LIKELY_TO_SELL_OUT"]
  },
  "sorting": {
    "sort_by": "rating",       // rating, price, default
    "order": "desc"            // asc, desc
  },
  "pagination": {
    "page": 1,
    "limit": 20                // Max 50
  },
  "currency": "EUR",
  "language": "fr"             // Pour traductions
}
```

**Response** :
```json
{
  "success": true,
  "location": {
    "matched_city": "Paris",
    "destination_id": "77",
    "coordinates": {"lat": 48.8566, "lon": 2.3522}
  },
  "filters_applied": {
    "categories": ["food", "museum"],
    "price_range": {"min": 10, "max": 200}
  },
  "results": {
    "total": 234,
    "page": 1,
    "limit": 20,
    "activities": [
      {
        "id": "5010SYDNEY",
        "title": "Louvre Museum Skip-the-Line Ticket",
        "description": "Explore the world's largest art museum...",
        "images": [
          {
            "url": "https://cdn.viator.com/...",
            "is_cover": true,
            "variants": {
              "small": "https://...",
              "medium": "https://...",
              "large": "https://..."
            }
          }
        ],
        "pricing": {
          "from_price": 45.00,
          "currency": "EUR",
          "original_price": 60.00,  // Si en promo
          "is_discounted": true
        },
        "rating": {
          "average": 4.7,
          "count": 1523
        },
        "duration": {
          "minutes": 180,
          "formatted": "3 hours"
        },
        "categories": ["museum", "art", "culture"],
        "flags": ["SKIP_THE_LINE", "FREE_CANCELLATION"],
        "booking_url": "https://www.viator.com/tours/...",
        "confirmation_type": "INSTANT",
        "location": {
          "destination": "Paris",
          "country": "France"
        },
        "availability": "available"  // available, limited, sold_out
      }
    ]
  },
  "cache_info": {
    "cached": false,
    "cached_at": null,
    "expires_at": null
  }
}
```

**Logique Interne** :
1. **Résolution de la localisation** :
   - Si `city` fourni → Appel `/destinations` pour trouver destination_id (avec fuzzy matching)
   - Si `geo` fourni → Trouver destination la plus proche (via MongoDB des destinations)
   - Si `destination_id` fourni → Utiliser directement
2. **Mapping des catégories** :
   - Convertir catégories simples ("food", "museum") → tag IDs Viator
   - Maintenir un mapping statique en base
3. **Cache** :
   - Clé Redis : `activities_search:{destination_id}:{start_date}:{filters_hash}`
   - TTL : 7 jours
4. **Appel Viator** :
   - `POST /products/search` avec filtres mappés
5. **Transformation de la réponse** :
   - Simplifier ProductSummary → format clean
   - Extraire uniquement les champs essentiels
6. **Persistance MongoDB** :
   - Upsert des activités par `product_code`
   - Historique des prix et disponibilités

---

### 2. **`GET /api/v1/activities/{activity_id}`**

**Description** : Détails complets d'une activité

**Response** :
```json
{
  "success": true,
  "activity": {
    "id": "5010SYDNEY",
    "title": "...",
    "description": "...",
    "images": [...],
    "pricing": {...},
    "rating": {...},
    "duration": {...},
    "categories": [...],
    "itinerary": {
      "highlights": ["Visit the Louvre", "See Mona Lisa"],
      "included": ["Skip-the-line entry", "Audio guide"],
      "excluded": ["Hotel pickup", "Food"],
      "meeting_point": "Louvre Pyramid entrance"
    },
    "cancellation_policy": {
      "type": "FREE_CANCELLATION",
      "cutoff_hours": 24
    },
    "booking_url": "https://..."
  }
}
```

**Source** : `GET /products/{product-code}` de Viator (données complètes)

---

### 3. **`POST /api/v1/activities/availability`**

**Description** : Vérifier disponibilité réelle pour une date/nombre de personnes

**Request** :
```json
{
  "activity_id": "5010SYDNEY",
  "date": "2026-03-15",
  "travelers": {
    "adults": 2,
    "children": 1,
    "infants": 0
  },
  "currency": "EUR"
}
```

**Response** :
```json
{
  "success": true,
  "available": true,
  "options": [
    {
      "option_id": "TG1",
      "time": "10:00",
      "price": {
        "total": 135.00,
        "per_person": 45.00,
        "breakdown": {
          "adults": 90.00,
          "children": 45.00
        },
        "currency": "EUR"
      },
      "availability": "available",
      "spots_remaining": 12
    }
  ]
}
```

**Source** : `POST /availability/check` de Viator

---

### 4. **`GET /api/v1/destinations`**

**Description** : Liste des destinations disponibles (avec cache long)

**Query Params** :
- `country_code` : Filtrer par pays (optionnel)
- `search` : Recherche par nom
- `type` : city, country, region

**Response** :
```json
{
  "success": true,
  "destinations": [
    {
      "id": "77",
      "name": "Paris",
      "country": "France",
      "country_code": "FR",
      "type": "city",
      "coordinates": {"lat": 48.8566, "lon": 2.3522},
      "activity_count": 1234
    }
  ]
}
```

**Source** : `GET /destinations` de Viator (à ingérer et stocker dans MongoDB)

---

### 5. **`GET /api/v1/categories`**

**Description** : Liste des catégories/tags disponibles

**Response** :
```json
{
  "success": true,
  "categories": [
    {
      "id": "food",
      "name": "Food & Dining",
      "viator_tags": [21972, 21973],
      "icon": "🍴"
    },
    {
      "id": "museum",
      "name": "Museums",
      "viator_tags": [21975],
      "icon": "🏛️"
    }
  ]
}
```

**Source** : `GET /products/tags` + mapping manuel pour simplification

---

### 6. **`GET /api/v1/activities/recommendations/{activity_id}`**

**Description** : Recommandations basées sur une activité

**Response** :
```json
{
  "success": true,
  "recommendations": [
    // Liste d'activités similaires (même format que /search)
  ]
}
```

**Source** : `POST /products/recommendations` de Viator

---

### 7. **`POST /api/v1/activities/search/freetext`**

**Description** : Recherche libre par texte (alternatif à /search)

**Request** :
```json
{
  "query": "eiffel tower tours",
  "destination_id": "77",  // Optionnel
  "filters": {...},
  "pagination": {...}
}
```

**Source** : `POST /search/freetext` de Viator

---

## 🏗️ Architecture et Structure de Code

### Structure de Dossiers (Production-Ready)

```
Travliaq-API/
├── app/
│   ├── api/
│   │   ├── v1/                          # Versioning API
│   │   │   ├── __init__.py
│   │   │   ├── activities.py            # Routes activités
│   │   │   ├── destinations.py          # Routes destinations
│   │   │   └── categories.py            # Routes catégories
│   │   └── __init__.py
│   ├── services/
│   │   ├── viator/                      # Client API Viator
│   │   │   ├── __init__.py
│   │   │   ├── client.py                # Client HTTP principal
│   │   │   ├── products.py              # Méthodes /products/*
│   │   │   ├── search.py                # Méthodes /search/*
│   │   │   ├── availability.py          # Méthodes /availability/*
│   │   │   ├── destinations.py          # Méthodes /destinations
│   │   │   └── models.py                # Modèles Pydantic Viator
│   │   ├── activities_service.py        # Service métier activités
│   │   ├── destinations_service.py      # Service métier destinations
│   │   ├── categories_service.py        # Service métier catégories
│   │   └── location_resolver.py         # Résolution ville → destination_id
│   ├── models/
│   │   ├── activities.py                # Modèles API publique (simplifié)
│   │   ├── destinations.py
│   │   └── categories.py
│   ├── repositories/
│   │   ├── activities_repository.py     # Accès MongoDB activités
│   │   ├── destinations_repository.py   # Accès MongoDB destinations
│   │   └── categories_repository.py     # Accès MongoDB catégories
│   ├── core/
│   │   ├── config.py                    # Config (+ clés API Viator)
│   │   ├── cache.py
│   │   └── constants.py                 # Constantes (mappings tags, etc.)
│   ├── utils/
│   │   ├── viator_mapper.py             # Mapping Viator → format simple
│   │   ├── fuzzy_matcher.py             # Fuzzy matching villes
│   │   └── validators.py                # Validations inputs
│   └── main.py
├── openapi.json                         # Spec Viator (référence)
├── requirements.txt
└── README.md
```

### Composants Clés

#### 1. **ViatorClient** (`app/services/viator/client.py`)

```python
class ViatorClient:
    """Client HTTP pour l'API Viator."""

    def __init__(self, api_key: str, env: str = "prod"):
        self.api_key = api_key
        self.base_url = "https://api.viator.com"
        self.headers = {
            "Accept": "application/json;version=2.0",
            "Accept-Language": "en",
            "exp-api-key": api_key
        }

    async def request(self, method: str, endpoint: str, **kwargs):
        # Gestion requêtes avec retry, rate limiting, etc.
        pass
```

#### 2. **ActivitiesService** (`app/services/activities_service.py`)

```python
class ActivitiesService:
    """Service métier pour les activités."""

    def __init__(
        self,
        viator_client: ViatorClient,
        redis_cache: RedisCache,
        activities_repo: ActivitiesRepository,
        location_resolver: LocationResolver
    ):
        self.viator = viator_client
        self.cache = redis_cache
        self.repo = activities_repo
        self.location_resolver = location_resolver

    async def search_activities(self, request: ActivitySearchRequest) -> ActivitySearchResponse:
        # 1. Résoudre localisation (ville → destination_id)
        # 2. Vérifier cache Redis
        # 3. Si pas en cache → Appel Viator
        # 4. Transformer réponse (mapper)
        # 5. Mettre en cache Redis + MongoDB
        # 6. Retourner résultat simplifié
        pass
```

#### 3. **LocationResolver** (`app/services/location_resolver.py`)

```python
class LocationResolver:
    """Résout ville/geo → destination_id Viator."""

    async def resolve_city(self, city: str, country_code: str = None) -> str:
        # Fuzzy matching sur MongoDB destinations
        # Retourne destination_id
        pass

    async def resolve_geo(self, lat: float, lon: float, radius_km: float) -> str:
        # Trouve destination la plus proche via géospatial query
        pass
```

#### 4. **ViatorMapper** (`app/utils/viator_mapper.py`)

```python
class ViatorMapper:
    """Transforme réponses Viator en format simplifié."""

    @staticmethod
    def map_product_summary(viator_product: dict) -> Activity:
        # Transforme ProductSummary → Activity (modèle simple)
        pass

    @staticmethod
    def map_categories(tags: list[int]) -> list[str]:
        # Tags Viator → catégories simples ("food", "museum")
        pass
```

---

## 🗄️ Stratégie Cache Redis

### Structure des Clés

```
activities_search:{destination_id}:{start_date}:{end_date}:{filters_hash}
activity_details:{product_code}
availability:{product_code}:{date}:{pax_hash}
destinations:all
categories:all
tags_mapping
```

### TTL Recommandés

| Clé | TTL | Raison |
|-----|-----|--------|
| `activities_search:*` | **7 jours** | Activités changent peu |
| `activity_details:*` | **7 jours** | Infos produit stables |
| `availability:*` | **1 heure** | Disponibilité temps réel |
| `destinations:all` | **30 jours** | Destinations très stables |
| `categories:all` | **30 jours** | Tags rarement mis à jour |

### Invalidation

**Manuelle** :
- Endpoint admin : `DELETE /api/v1/admin/cache/{pattern}`
- Exemples :
  - `DELETE /api/v1/admin/cache/activities_search:77:*` → Clear Paris
  - `DELETE /api/v1/admin/cache/activity_details:5010SYDNEY` → Clear produit

**Automatique** :
- Webhook Viator (si disponible) → Invalider cache produit modifié
- Cron job quotidien → Nettoyer clés expirées

### Implémentation

```python
class ActivitiesCache:
    """Cache spécialisé pour activités."""

    def __init__(self, redis: RedisCache):
        self.redis = redis

    def get_search_results(self, params: ActivitySearchParams) -> Optional[list[Activity]]:
        key = self._build_search_key(params)
        return self.redis.get("activities_search", {"key": key})

    def set_search_results(self, params: ActivitySearchParams, results: list[Activity]):
        key = self._build_search_key(params)
        self.redis.set("activities_search", {"key": key}, results, ttl_seconds=604800)  # 7 jours

    def _build_search_key(self, params: ActivitySearchParams) -> str:
        filters_hash = hashlib.md5(
            json.dumps(params.filters, sort_keys=True).encode()
        ).hexdigest()[:8]
        return f"{params.destination_id}:{params.dates.start}:{params.dates.end}:{filters_hash}"
```

---

## 🍃 Stratégie MongoDB

### Collections

#### 1. **`activities`** (Collection Principale)

**Schéma** :
```javascript
{
  "_id": ObjectId("..."),
  "product_code": "5010SYDNEY",  // Index unique
  "title": "Sydney Hop-on Hop-off Tour",
  "description": "...",
  "images": [
    {
      "url": "https://...",
      "is_cover": true,
      "variants": {...}
    }
  ],
  "pricing": {
    "from_price": 45.00,
    "currency": "EUR",
    "last_updated": ISODate("2026-01-02T10:00:00Z")
  },
  "rating": {
    "average": 4.7,
    "count": 1523
  },
  "duration_minutes": 180,
  "categories": ["museum", "art"],
  "viator_tags": [21972, 21973],
  "flags": ["SKIP_THE_LINE"],
  "destination": {
    "id": "77",
    "name": "Paris",
    "country": "France"
  },
  "location": {
    "type": "Point",
    "coordinates": [2.3522, 48.8566]  // [lon, lat] pour géospatial
  },
  "booking_url": "https://...",
  "confirmation_type": "INSTANT",
  "itinerary": {...},
  "cancellation_policy": {...},
  "metadata": {
    "first_seen": ISODate("2026-01-01T00:00:00Z"),
    "last_updated": ISODate("2026-01-02T10:00:00Z"),
    "fetch_count": 42,
    "viator_raw": {...}  // Optionnel : données brutes Viator
  }
}
```

**Index** :
```javascript
db.activities.createIndex({ "product_code": 1 }, { unique: true })
db.activities.createIndex({ "destination.id": 1 })
db.activities.createIndex({ "categories": 1 })
db.activities.createIndex({ "pricing.from_price": 1 })
db.activities.createIndex({ "rating.average": -1 })
db.activities.createIndex({ "location": "2dsphere" })  // Géospatial
db.activities.createIndex({ "metadata.last_updated": 1 })
```

**Upsert Logic** :
```python
async def upsert_activity(self, product_code: str, data: dict):
    result = await self.collection.update_one(
        {"product_code": product_code},
        {
            "$set": {
                **data,
                "metadata.last_updated": datetime.utcnow()
            },
            "$setOnInsert": {
                "metadata.first_seen": datetime.utcnow(),
                "metadata.fetch_count": 0
            },
            "$inc": {
                "metadata.fetch_count": 1
            }
        },
        upsert=True
    )
```

---

#### 2. **`destinations`**

**Schéma** :
```javascript
{
  "_id": ObjectId("..."),
  "destination_id": "77",  // Index unique (ID Viator)
  "name": "Paris",
  "slug": "paris",
  "country": "France",
  "country_code": "FR",
  "type": "city",  // city, country, region
  "location": {
    "type": "Point",
    "coordinates": [2.3522, 48.8566]
  },
  "parent_destination_id": "76",  // ID pays
  "activity_count": 1234,
  "metadata": {
    "last_synced": ISODate("2026-01-02T00:00:00Z")
  }
}
```

**Index** :
```javascript
db.destinations.createIndex({ "destination_id": 1 }, { unique: true })
db.destinations.createIndex({ "slug": 1 })
db.destinations.createIndex({ "country_code": 1 })
db.destinations.createIndex({ "location": "2dsphere" })
db.destinations.createIndex({ "name": "text" })  // Full-text search
```

**Sync** : Ingest initial + refresh hebdomadaire via `GET /destinations`

---

#### 3. **`categories`**

**Schéma** :
```javascript
{
  "_id": ObjectId("..."),
  "id": "food",  // ID simple pour frontend
  "name": "Food & Dining",
  "name_translations": {
    "fr": "Gastronomie",
    "es": "Gastronomía"
  },
  "viator_tags": [21972, 21973],  // Mapping vers tags Viator
  "icon": "🍴",
  "parent_category": null,  // Hiérarchie optionnelle
  "metadata": {
    "last_updated": ISODate("2026-01-01T00:00:00Z")
  }
}
```

**Index** :
```javascript
db.categories.createIndex({ "id": 1 }, { unique: true })
db.categories.createIndex({ "viator_tags": 1 })
```

---

#### 4. **`price_history`** (Optionnel - Analytics)

**Schéma** :
```javascript
{
  "_id": ObjectId("..."),
  "product_code": "5010SYDNEY",
  "date": ISODate("2026-01-02T00:00:00Z"),
  "from_price": 45.00,
  "currency": "EUR",
  "is_discounted": true,
  "original_price": 60.00
}
```

**Index** :
```javascript
db.price_history.createIndex({ "product_code": 1, "date": -1 })
```

**Usage** : Analyse de variations de prix, graphiques temporels

---

### Versioning & Migration

**Stratégie** :
- Ajouter champ `schema_version: 1` dans chaque document
- Migration progressive (pas de downtime)
- Exemple :
  ```javascript
  {
    "product_code": "5010SYDNEY",
    "schema_version": 2,  // Nouvelle version
    // ...
  }
  ```

---

## 📦 Modèles de Données

### Modèles Pydantic (API Publique)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class LocationInput(BaseModel):
    """Input pour localisation (3 options mutuellement exclusives)."""
    city: Optional[str] = None
    country_code: Optional[str] = None
    destination_id: Optional[str] = None
    geo: Optional[GeoInput] = None

class GeoInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=50, ge=1, le=200)

class DateRange(BaseModel):
    start: date
    end: Optional[date] = None

class PriceRange(BaseModel):
    min: Optional[float] = Field(None, ge=0)
    max: Optional[float] = Field(None, ge=0)

class DurationRange(BaseModel):
    min: Optional[int] = Field(None, ge=0)  # minutes
    max: Optional[int] = Field(None, ge=0)

class ActivityFilters(BaseModel):
    categories: Optional[List[str]] = None
    price_range: Optional[PriceRange] = None
    rating_min: Optional[float] = Field(None, ge=0, le=5)
    duration_minutes: Optional[DurationRange] = None
    flags: Optional[List[str]] = None  # FREE_CANCELLATION, etc.

class Sorting(BaseModel):
    sort_by: str = Field(default="default", pattern="^(default|rating|price)$")
    order: str = Field(default="desc", pattern="^(asc|desc)$")

class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)

class ActivitySearchRequest(BaseModel):
    location: LocationInput
    dates: DateRange
    filters: Optional[ActivityFilters] = None
    sorting: Optional[Sorting] = None
    pagination: Optional[Pagination] = None
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")
    language: str = Field(default="en", pattern="^[a-z]{2}$")

class ImageVariants(BaseModel):
    small: str
    medium: str
    large: str

class ActivityImage(BaseModel):
    url: str
    is_cover: bool
    variants: ImageVariants

class ActivityPricing(BaseModel):
    from_price: float
    currency: str
    original_price: Optional[float] = None
    is_discounted: bool = False

class ActivityRating(BaseModel):
    average: float
    count: int

class ActivityDuration(BaseModel):
    minutes: int
    formatted: str  # "3 hours"

class Activity(BaseModel):
    id: str
    title: str
    description: str
    images: List[ActivityImage]
    pricing: ActivityPricing
    rating: ActivityRating
    duration: ActivityDuration
    categories: List[str]
    flags: List[str]
    booking_url: str
    confirmation_type: str
    location: dict
    availability: str  # available, limited, sold_out

class ActivitySearchResponse(BaseModel):
    success: bool = True
    location: dict
    filters_applied: dict
    results: dict  # {total, page, limit, activities}
    cache_info: dict
```

---

## ⚠️ Gestion des Erreurs

### Types d'Erreurs

1. **Erreurs Client (4xx)** :
   - 400 : Paramètres invalides
   - 404 : Activité/destination non trouvée
   - 429 : Rate limit dépassé

2. **Erreurs Serveur (5xx)** :
   - 500 : Erreur interne
   - 502 : Erreur API Viator
   - 503 : Service indisponible (Redis/MongoDB down)

### Format de Réponse d'Erreur

```json
{
  "success": false,
  "error": {
    "code": "DESTINATION_NOT_FOUND",
    "message": "Unable to find destination for city 'Parisx'. Did you mean 'Paris'?",
    "details": {
      "city_query": "Parisx",
      "suggestions": ["Paris", "Parma"]
    }
  }
}
```

### Retry & Fallback

```python
class ViatorClient:
    async def request_with_retry(self, method: str, endpoint: str, retries: int = 3):
        for attempt in range(retries):
            try:
                response = await self.http_client.request(method, endpoint)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit - backoff exponentiel
                    await asyncio.sleep(2 ** attempt)
                    continue
                elif e.response.status_code >= 500:
                    # Erreur serveur Viator - retry
                    await asyncio.sleep(1)
                    continue
                else:
                    raise
            except httpx.RequestError:
                # Erreur réseau - retry
                await asyncio.sleep(1)
                continue

        raise ViatorAPIError("Max retries exceeded")
```

---

## 📝 Plan d'Implémentation

### Phase 1 : Setup & Infrastructure (Jour 1-2)

1. **Configuration**
   - [ ] Ajouter clés API Viator dans `.env`
   - [ ] Créer constantes (mappings catégories, currencies, etc.)
   - [ ] Configurer logging

2. **Client Viator**
   - [ ] Implémenter `ViatorClient` base
   - [ ] Méthodes pour `/products/search`, `/destinations`, `/products/tags`
   - [ ] Gestion retry & rate limiting

3. **MongoDB**
   - [ ] Créer collections (activities, destinations, categories)
   - [ ] Créer index géospatiaux
   - [ ] Implémenter repositories

4. **Tests**
   - [ ] Tester connexion API Viator
   - [ ] Tester upsert MongoDB

---

### Phase 2 : MVP - Endpoint Principal (Jour 3-5)

5. **Service LocationResolver**
   - [ ] Fuzzy matching ville → destination_id
   - [ ] Géospatial query (lat/lon → destination)
   - [ ] Tests avec vraies villes

6. **Service ActivitiesService**
   - [ ] `search_activities()` avec cache Redis
   - [ ] Mapping Viator → format simple
   - [ ] Upsert MongoDB

7. **Endpoint `POST /api/v1/activities/search`**
   - [ ] Route FastAPI
   - [ ] Validations Pydantic
   - [ ] Tests E2E

---

### Phase 3 : Endpoints Complémentaires (Jour 6-8)

8. **Destinations**
   - [ ] Ingest initial `/destinations` → MongoDB
   - [ ] Endpoint `GET /api/v1/destinations`
   - [ ] Cache 30 jours

9. **Catégories**
   - [ ] Ingest `/products/tags` → MongoDB
   - [ ] Créer mapping simple (food, museum, etc.)
   - [ ] Endpoint `GET /api/v1/categories`

10. **Détails Activité**
    - [ ] Endpoint `GET /api/v1/activities/{id}`
    - [ ] Appel `/products/{product-code}`

11. **Disponibilité**
    - [ ] Endpoint `POST /api/v1/activities/availability`
    - [ ] Appel `/availability/check`

---

### Phase 4 : Optimisations & Production (Jour 9-10)

12. **Cache Avancé**
    - [ ] Endpoint admin invalidation cache
    - [ ] Métriques cache hit/miss
    - [ ] Warm-up cache destinations populaires

13. **Monitoring**
    - [ ] Logs structurés (JSON)
    - [ ] Métriques (nombre d'appels Viator, latence, etc.)
    - [ ] Health check endpoint

14. **Documentation**
    - [ ] OpenAPI spec (Swagger)
    - [ ] README usage
    - [ ] Exemples curl/Postman

15. **Tests**
    - [ ] Tests unitaires (80% coverage)
    - [ ] Tests d'intégration
    - [ ] Load testing (100 req/s)

---

## 🎯 Résumé des Choix Techniques

| Aspect | Choix | Raison |
|--------|-------|--------|
| **Design Endpoint** | 1 endpoint unifié `/search` | Simplifie usage frontend, flexibilité |
| **Localisation** | 3 options (ville, destination_id, geo) | Couvre tous les cas d'usage |
| **Cache Redis** | TTL 7 jours pour activités | Données stables, économie API calls |
| **MongoDB** | Upsert avec `last_updated` | Évite doublons, historique simple |
| **Mapping Catégories** | Tags simples + mapping Viator | UX simple pour frontend |
| **Géospatial** | Index 2dsphere MongoDB | Recherche par proximité |
| **Versioning** | `/api/v1/*` | Évolutivité future |
| **Retry** | 3 tentatives avec backoff | Résilience face aux erreurs Viator |
| **Rate Limiting** | Respecter headers Viator | Éviter blocage compte |

---

## 📚 Ressources & Références

- **API Viator** : `openapi.json` (racine projet)
- **Clés API** :
  - DEV : `1029cf59-4682-496d-8c16-9a229a388861`
  - PROD : `a8f758b5-0349-4eb0-99f6-41381526417c`
- **Documentation Viator** : https://docs.viator.com/partner-api/
- **Tags Viator** : https://partnerresources.viator.com/travel-commerce/tags

---

## 🚀 Prochaines Étapes

1. **Review ce plan** avec l'équipe
2. **Valider les choix** (endpoints, cache, MongoDB)
3. **Commencer Phase 1** (setup infrastructure)
4. **Tester MVP** avec vraies requêtes
5. **Itérer** selon feedback

---

**Date** : 2026-01-02
**Version** : 1.0
**Auteur** : Claude (Anthropic)

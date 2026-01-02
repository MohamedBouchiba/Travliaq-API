# Checklist d'Implémentation - Viator API Wrapper

## 📋 Vue d'Ensemble

Cette checklist vous guidera à travers toutes les étapes d'implémentation du wrapper Viator API, de la configuration initiale jusqu'au déploiement en production.

---

## Phase 1️⃣ : Setup & Infrastructure (Jour 1-2)

### Configuration Environnement

- [ ] **Mise à jour `.env`**
  - [ ] Ajouter `VIATOR_API_KEY_DEV`
  - [ ] Ajouter `VIATOR_API_KEY_PROD`
  - [ ] Ajouter `VIATOR_ENV=dev`
  - [ ] Ajouter `VIATOR_BASE_URL=https://api.viator.com`
  - [ ] Vérifier credentials Redis (déjà présents)
  - [ ] Vérifier credentials MongoDB (déjà présents)

- [ ] **Mise à jour `requirements.txt`**
  - [ ] Ajouter `tenacity==8.2.3` pour retry logic
  - [ ] Exécuter `pip install -r requirements.txt`

- [ ] **Mise à jour `app/core/config.py`**
  - [ ] Ajouter champs Viator API (voir `VIATOR_IMPLEMENTATION_EXAMPLES.md`)
  - [ ] Ajouter collections MongoDB (activities, destinations, categories)
  - [ ] Ajouter propriétés cache TTL
  - [ ] Ajouter propriété `viator_api_key` (switch dev/prod)
  - [ ] Tester chargement config : `python -c "from app.core.config import get_settings; print(get_settings().viator_api_key)"`

- [ ] **Créer fichier `app/core/constants.py`**
  - [ ] Copier contenu depuis `VIATOR_MODELS_REFERENCE.md`
  - [ ] Valider imports : `python -c "from app.core.constants import CATEGORY_TAG_MAPPING"`

### Client Viator API

- [ ] **Créer structure de dossiers**
  ```bash
  mkdir -p app/services/viator
  mkdir -p app/repositories
  mkdir -p app/utils
  mkdir -p app/models
  mkdir -p app/api/v1
  ```

- [ ] **Créer `app/services/viator/__init__.py`**
  ```python
  from .client import ViatorClient
  from .products import ViatorProductsService

  __all__ = ["ViatorClient", "ViatorProductsService"]
  ```

- [ ] **Créer `app/services/viator/client.py`**
  - [ ] Copier code depuis `VIATOR_IMPLEMENTATION_EXAMPLES.md`
  - [ ] Implémenter `__init__`, `request`, `get`, `post`
  - [ ] Implémenter retry logic avec `tenacity`
  - [ ] Implémenter gestion rate limiting (429)
  - [ ] Tester connexion : `python -c "import asyncio; from app.services.viator.client import ViatorClient; asyncio.run(ViatorClient('test-key').get('/destinations'))"`

- [ ] **Créer `app/services/viator/products.py`**
  - [ ] Copier code depuis `VIATOR_IMPLEMENTATION_EXAMPLES.md`
  - [ ] Implémenter `search_products()`
  - [ ] Implémenter `get_product_details()`
  - [ ] Tester avec vraie clé API

### MongoDB Setup

- [ ] **Créer `app/repositories/activities_repository.py`**
  - [ ] Copier code depuis `VIATOR_IMPLEMENTATION_EXAMPLES.md`
  - [ ] Implémenter `upsert_activity()`
  - [ ] Implémenter `get_activity()`
  - [ ] Implémenter `search_activities()`
  - [ ] Implémenter `create_indexes()`

- [ ] **Créer `app/repositories/destinations_repository.py`**
  ```python
  class DestinationsRepository:
      def __init__(self, collection):
          self.collection = collection

      async def upsert_destination(self, destination_id: str, data: dict):
          # Similar to activities_repository
          pass

      async def get_destination(self, destination_id: str):
          pass

      async def search_destinations(self, query: str):
          pass

      async def create_indexes(self):
          # Index: destination_id (unique), slug, country_code, location (2dsphere), name (text)
          pass
  ```

- [ ] **Tester repositories**
  ```python
  # Test script
  import asyncio
  from motor.motor_asyncio import AsyncIOMotorClient
  from app.repositories.activities_repository import ActivitiesRepository

  async def test():
      client = AsyncIOMotorClient("mongodb://localhost:27017")
      db = client["poi_db"]
      repo = ActivitiesRepository(db["activities"])
      await repo.create_indexes()
      print("Indexes created successfully!")

  asyncio.run(test())
  ```

---

## Phase 2️⃣ : MVP - Endpoint Principal (Jour 3-5)

### Modèles Pydantic

- [ ] **Créer `app/models/activities.py`**
  - [ ] Copier tous les modèles depuis `VIATOR_MODELS_REFERENCE.md`
  - [ ] Valider imports : `python -c "from app.models.activities import ActivitySearchRequest"`
  - [ ] Tester validation avec données invalides

### Service LocationResolver

- [ ] **Créer `app/services/location_resolver.py`**
  - [ ] Copier code depuis `VIATOR_IMPLEMENTATION_EXAMPLES.md`
  - [ ] Implémenter `resolve_city()` avec fuzzy matching
  - [ ] Implémenter `resolve_geo()` avec geospatial query
  - [ ] Tester avec vraies villes (Paris, New York, Tokyo)

### Mapper Viator

- [ ] **Créer `app/utils/viator_mapper.py`**
  - [ ] Copier code depuis `VIATOR_IMPLEMENTATION_EXAMPLES.md`
  - [ ] Implémenter `map_product_summary()`
  - [ ] Implémenter `_format_duration()`
  - [ ] Implémenter `_map_tags_to_categories()`
  - [ ] Tester mapping avec vraie réponse Viator

### Service ActivitiesService

- [ ] **Créer `app/services/activities_service.py`**
  - [ ] Copier code depuis `VIATOR_IMPLEMENTATION_EXAMPLES.md`
  - [ ] Implémenter `search_activities()`
  - [ ] Implémenter `_resolve_location()`
  - [ ] Implémenter `_call_viator_search()`
  - [ ] Implémenter `_map_categories_to_tags()`
  - [ ] Implémenter `_persist_activities()`
  - [ ] Implémenter `_build_cache_key()`
  - [ ] Tester end-to-end avec vraies données

### Route API Principal

- [ ] **Créer `app/api/v1/__init__.py`**
  ```python
  from fastapi import APIRouter
  from .activities import router as activities_router

  v1_router = APIRouter(prefix="/api/v1")
  v1_router.include_router(activities_router)
  ```

- [ ] **Créer `app/api/v1/activities.py`**
  ```python
  from fastapi import APIRouter, HTTPException, Depends, Request
  from app.models.activities import (
      ActivitySearchRequest,
      ActivitySearchResponse,
      ErrorResponse
  )

  router = APIRouter(prefix="/activities", tags=["Activities"])

  def get_activities_service(request: Request):
      return request.app.state.activities_service

  @router.post("/search", response_model=ActivitySearchResponse)
  async def search_activities(
      request: ActivitySearchRequest,
      service = Depends(get_activities_service)
  ):
      try:
          return await service.search_activities(request)
      except ValueError as e:
          raise HTTPException(status_code=400, detail=str(e))
      except Exception as e:
          raise HTTPException(status_code=500, detail="Internal server error")
  ```

- [ ] **Mettre à jour `app/main.py`**
  - [ ] Importer `v1_router`
  - [ ] Ajouter `app.include_router(v1_router)`
  - [ ] Initialiser services dans `startup_event()` (voir `VIATOR_IMPLEMENTATION_EXAMPLES.md`)
  - [ ] Fermer connexions dans `shutdown_event()`

### Tests Endpoint MVP

- [ ] **Tester avec curl**
  ```bash
  curl -X POST http://localhost:8000/api/v1/activities/search \
    -H "Content-Type: application/json" \
    -d '{
      "location": {"city": "Paris", "country_code": "FR"},
      "dates": {"start": "2026-03-15"},
      "currency": "EUR"
    }'
  ```

- [ ] **Tester avec Postman/Insomnia**
  - [ ] Recherche par ville
  - [ ] Recherche par destination_id
  - [ ] Recherche par geo
  - [ ] Avec filtres (catégories, prix, rating)
  - [ ] Avec tri (rating, price)
  - [ ] Avec pagination

- [ ] **Vérifier cache Redis**
  - [ ] Première requête → cache miss
  - [ ] Deuxième requête identique → cache hit
  - [ ] Vérifier TTL (7 jours)

- [ ] **Vérifier MongoDB**
  - [ ] Activités bien persistées
  - [ ] Upsert fonctionne (pas de doublons)
  - [ ] Index créés correctement

---

## Phase 3️⃣ : Endpoints Complémentaires (Jour 6-8)

### Destinations

- [ ] **Créer script d'ingestion destinations**
  ```python
  # scripts/ingest_destinations.py
  async def ingest_viator_destinations():
      viator = ViatorClient(api_key=settings.viator_api_key)
      destinations = await viator.get("/destinations")
      # Store in MongoDB
      pass
  ```

- [ ] **Exécuter ingestion initiale**
  ```bash
  python scripts/ingest_destinations.py
  ```

- [ ] **Créer `app/api/v1/destinations.py`**
  ```python
  @router.get("", response_model=DestinationsResponse)
  async def list_destinations(
      country_code: Optional[str] = None,
      search: Optional[str] = None,
      type: Optional[str] = None
  ):
      # Query MongoDB destinations
      pass
  ```

- [ ] **Tester endpoint `/api/v1/destinations`**
  - [ ] Sans filtres
  - [ ] Avec filtre country_code
  - [ ] Avec recherche texte

### Catégories

- [ ] **Créer script d'ingestion catégories**
  ```python
  # scripts/ingest_categories.py
  async def ingest_viator_tags():
      viator = ViatorClient(api_key=settings.viator_api_key)
      tags = await viator.get("/products/tags")
      # Map to simplified categories + store in MongoDB
      pass
  ```

- [ ] **Exécuter ingestion**
  ```bash
  python scripts/ingest_categories.py
  ```

- [ ] **Créer `app/api/v1/categories.py`**
  ```python
  @router.get("", response_model=CategoriesResponse)
  async def list_categories():
      # Query MongoDB categories
      pass
  ```

- [ ] **Tester endpoint `/api/v1/categories`**

### Détails Activité

- [ ] **Ajouter méthode dans `ActivitiesService`**
  ```python
  async def get_activity_details(self, activity_id: str) -> ActivityDetails:
      # 1. Check cache
      # 2. Try MongoDB
      # 3. Fallback to Viator API
      pass
  ```

- [ ] **Ajouter route**
  ```python
  @router.get("/{activity_id}", response_model=ActivityDetailsResponse)
  async def get_activity_details(activity_id: str):
      pass
  ```

- [ ] **Tester endpoint `/api/v1/activities/{id}`**

### Disponibilité

- [ ] **Créer `app/services/viator/availability.py`**
  ```python
  class ViatorAvailabilityService:
      async def check_availability(
          self,
          product_code: str,
          travel_date: str,
          pax_mix: list,
          currency: str
      ):
          # POST /availability/check
          pass
  ```

- [ ] **Ajouter route**
  ```python
  @router.post("/availability", response_model=AvailabilityCheckResponse)
  async def check_availability(request: AvailabilityCheckRequest):
      pass
  ```

- [ ] **Tester endpoint `/api/v1/activities/availability`**

---

## Phase 4️⃣ : Optimisations & Production (Jour 9-10)

### Cache Avancé

- [ ] **Créer endpoint admin invalidation cache**
  ```python
  # app/api/v1/admin.py
  @router.delete("/cache/{pattern}")
  async def invalidate_cache(pattern: str):
      # Clear Redis keys matching pattern
      pass
  ```

- [ ] **Implémenter warm-up cache**
  ```python
  # scripts/warm_cache.py
  async def warm_cache():
      # Pre-cache popular destinations (Paris, London, NYC, etc.)
      pass
  ```

- [ ] **Tester invalidation cache**

### Monitoring & Logs

- [ ] **Configurer logging structuré**
  ```python
  # app/core/logging.py
  import logging
  import json

  class JSONFormatter(logging.Formatter):
      def format(self, record):
          log_data = {
              "timestamp": self.formatTime(record),
              "level": record.levelname,
              "message": record.getMessage(),
              "module": record.module
          }
          return json.dumps(log_data)
  ```

- [ ] **Ajouter métriques**
  - [ ] Compteur appels Viator API
  - [ ] Latence moyenne
  - [ ] Cache hit/miss ratio
  - [ ] Erreurs par endpoint

- [ ] **Créer endpoint health check**
  ```python
  @router.get("/health")
  async def health_check():
      return {
          "status": "healthy",
          "services": {
              "mongodb": await check_mongodb(),
              "redis": await check_redis(),
              "viator_api": await check_viator_api()
          }
      }
  ```

### Documentation

- [ ] **Générer OpenAPI spec automatique**
  - [ ] Aller sur `http://localhost:8000/docs`
  - [ ] Vérifier tous les endpoints documentés
  - [ ] Tester exemples dans Swagger UI

- [ ] **Créer README usage**
  ```markdown
  # Travliaq API - Viator Wrapper

  ## Endpoints

  ### POST /api/v1/activities/search
  Search for activities...

  ### GET /api/v1/activities/{id}
  Get activity details...
  ```

- [ ] **Créer exemples Postman**
  - [ ] Exporter collection Postman
  - [ ] Ajouter variables d'environnement
  - [ ] Documenter chaque requête

### Tests

- [ ] **Tests unitaires**
  ```python
  # tests/test_viator_mapper.py
  def test_map_product_summary():
      product = {...}  # Mock Viator response
      activity = ViatorMapper.map_product_summary(product)
      assert activity["id"] == product["productCode"]
  ```

- [ ] **Tests d'intégration**
  ```python
  # tests/test_activities_service.py
  @pytest.mark.asyncio
  async def test_search_activities():
      # Test avec vraie API (ou mock)
      pass
  ```

- [ ] **Coverage > 80%**
  ```bash
  pytest --cov=app --cov-report=html
  ```

- [ ] **Load testing**
  ```bash
  # Avec locust ou k6
  k6 run load_test.js
  # Objectif: 100 req/s sans erreur
  ```

### Déploiement

- [ ] **Vérifier variables d'environnement production**
  - [ ] `VIATOR_ENV=prod`
  - [ ] Clé API production Viator
  - [ ] MongoDB production URI
  - [ ] Redis production credentials

- [ ] **Dockerfile**
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] **Tester build Docker**
  ```bash
  docker build -t travliaq-api .
  docker run -p 8000:8000 travliaq-api
  ```

- [ ] **Déployer sur Railway/Render/Fly.io**
  - [ ] Configurer variables d'env
  - [ ] Déployer
  - [ ] Tester endpoints production

---

## 🔍 Checklist Validation Finale

### Fonctionnalités

- [ ] ✅ Recherche par ville fonctionne
- [ ] ✅ Recherche par destination_id fonctionne
- [ ] ✅ Recherche par geo fonctionne
- [ ] ✅ Filtres (catégories, prix, rating) fonctionnent
- [ ] ✅ Tri (rating, price, default) fonctionne
- [ ] ✅ Pagination fonctionne
- [ ] ✅ Images retournées (avec variants)
- [ ] ✅ Prix correctement formatés
- [ ] ✅ Ratings affichés
- [ ] ✅ Durée formatée
- [ ] ✅ Catégories mappées
- [ ] ✅ Booking URL présente

### Cache & Performance

- [ ] ✅ Cache Redis fonctionne (hit/miss)
- [ ] ✅ TTL correctement appliqué (7 jours)
- [ ] ✅ MongoDB persistance fonctionne
- [ ] ✅ Upsert évite doublons
- [ ] ✅ Index MongoDB créés
- [ ] ✅ Latence < 500ms (cache hit)
- [ ] ✅ Latence < 2s (cache miss)

### Gestion Erreurs

- [ ] ✅ Ville introuvable → 404 avec suggestions
- [ ] ✅ Destination invalide → 400
- [ ] ✅ Dates invalides → 400
- [ ] ✅ Erreur Viator API → 502
- [ ] ✅ Redis down → fallback gracieux
- [ ] ✅ MongoDB down → erreur 503
- [ ] ✅ Rate limit Viator → retry automatique

### Documentation

- [ ] ✅ Swagger UI accessible
- [ ] ✅ Tous endpoints documentés
- [ ] ✅ Exemples de requêtes fournis
- [ ] ✅ README à jour
- [ ] ✅ Code commenté

### Tests

- [ ] ✅ Tests unitaires > 80% coverage
- [ ] ✅ Tests d'intégration passent
- [ ] ✅ Load test 100 req/s sans erreur
- [ ] ✅ Test manuel de tous les endpoints

### Production

- [ ] ✅ Variables d'env production configurées
- [ ] ✅ Clé API production Viator testée
- [ ] ✅ Déployé et accessible
- [ ] ✅ Monitoring activé
- [ ] ✅ Logs structurés
- [ ] ✅ Health check fonctionne

---

## 📊 Métriques de Succès

### Performance

| Métrique | Cible | Statut |
|----------|-------|--------|
| Latence (cache hit) | < 500ms | ⬜ |
| Latence (cache miss) | < 2s | ⬜ |
| Cache hit ratio | > 60% | ⬜ |
| Throughput | > 100 req/s | ⬜ |
| Uptime | > 99.5% | ⬜ |

### Qualité

| Métrique | Cible | Statut |
|----------|-------|--------|
| Test coverage | > 80% | ⬜ |
| Error rate | < 1% | ⬜ |
| Code complexity | < 10 | ⬜ |

### Usage

| Métrique | Cible | Statut |
|----------|-------|--------|
| API calls Viator | Optimisé (cache) | ⬜ |
| MongoDB storage | < 10GB/mois | ⬜ |
| Redis memory | < 500MB | ⬜ |

---

## 🎯 Next Steps Après MVP

### Court Terme (1-2 semaines)

- [ ] Ajouter endpoint `/search/freetext`
- [ ] Ajouter endpoint `/recommendations/{id}`
- [ ] Implémenter webhooks Viator (si disponibles)
- [ ] Ajouter analytics (tracking recherches populaires)

### Moyen Terme (1 mois)

- [ ] Implémenter système de favoris
- [ ] Ajouter historique de recherches utilisateur
- [ ] Créer dashboard admin (métriques, cache, etc.)
- [ ] Optimiser performances (CDN pour images)

### Long Terme (3+ mois)

- [ ] Machine learning pour recommandations personnalisées
- [ ] Support multi-devises dynamique
- [ ] Integration booking (pas juste liens)
- [ ] API GraphQL en parallèle de REST

---

**Bon courage pour l'implémentation ! 🚀**

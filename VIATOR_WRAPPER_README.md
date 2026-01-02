# 🎯 Viator API Wrapper - Documentation Complète

> **Wrapper production-ready pour l'API Viator dans Travliaq-API**

---

## 📚 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Documentation Disponible](#documentation-disponible)
3. [Quick Start](#quick-start)
4. [Architecture](#architecture)
5. [Clés API](#clés-api)
6. [Support](#support)

---

## 🎯 Vue d'ensemble

Ce wrapper simplifie l'utilisation de l'API Viator en fournissant :

✅ **Endpoints simples** - Interface unifiée pour le frontend/agents
✅ **Cache intelligent** - Redis (7 jours) + MongoDB (persistance)
✅ **Résolution automatique** - Ville/geo → destination_id
✅ **Format simplifié** - Seules les données essentielles
✅ **Gestion d'erreurs** - Retry automatique, fallbacks
✅ **Production-ready** - Logs structurés, métriques, health checks

### MVP - Fonctionnalité Principale

**Endpoint** : `POST /api/v1/activities/search`

**Entrées** :
- 🏙️ Ville (nom + country_code)
- 📍 Position géographique (lat/lon + rayon)
- 🆔 Destination ID Viator
- 📅 Dates (start + end)
- 🏷️ Filtres (catégories, prix, rating, durée, flags)

**Sorties** :
- 💰 Prix (from_price, currency, is_discounted)
- ✅ Disponibilité
- 🖼️ Images (URL + variants small/medium/large)
- ⭐ Rating (average, count)
- ⏱️ Durée (minutes, formatted)
- 🏷️ Catégories (food, museum, adventure, etc.)
- 🔗 Booking URL
- 📝 Description

---

## 📖 Documentation Disponible

### 1️⃣ [Plan Détaillé](./VIATOR_API_WRAPPER_PLAN.md) ⭐ **COMMENCER ICI**
**Fichier** : `VIATOR_API_WRAPPER_PLAN.md`

📋 **Contenu** :
- Analyse complète de l'API Viator (endpoints, schémas)
- Tous les endpoints Travliaq-API proposés
- Architecture et structure de code
- Stratégie cache Redis (clés, TTL, invalidation)
- Stratégie MongoDB (schémas, index, upsert)
- Modèles de données
- Gestion des erreurs
- Plan d'implémentation phase par phase

👉 **Quand l'utiliser** : Pour comprendre la vision globale et l'architecture

---

### 2️⃣ [Exemples d'Implémentation](./VIATOR_IMPLEMENTATION_EXAMPLES.md)
**Fichier** : `VIATOR_IMPLEMENTATION_EXAMPLES.md`

💻 **Contenu** :
- Configuration complète (`.env`, `requirements.txt`, `config.py`)
- Code complet du `ViatorClient` (avec retry logic)
- Code complet du `ViatorProductsService`
- Service `LocationResolver` (ville → destination_id)
- Service `ActivitiesService` (logique métier)
- Repository MongoDB (`ActivitiesRepository`)
- Mapper Viator → format simple
- Mise à jour `main.py` pour intégration

👉 **Quand l'utiliser** : Pour copier/coller du code prêt à l'emploi

---

### 3️⃣ [Référence des Modèles](./VIATOR_MODELS_REFERENCE.md)
**Fichier** : `VIATOR_MODELS_REFERENCE.md`

📦 **Contenu** :
- Tous les modèles Pydantic (Request/Response)
- Enums (SortBy, SortOrder, ActivityFlag, etc.)
- Modèles d'entrée (LocationInput, DateRange, Filters, etc.)
- Modèles de sortie (Activity, SearchResults, etc.)
- Modèles d'erreur (ErrorResponse)
- Constantes et mappings (catégories → tags Viator)
- Exemples d'utilisation dans routes FastAPI

👉 **Quand l'utiliser** : Pour référencer la structure des modèles

---

### 4️⃣ [Checklist d'Implémentation](./VIATOR_IMPLEMENTATION_CHECKLIST.md) ⭐ **SUIVRE ÉTAPE PAR ÉTAPE**
**Fichier** : `VIATOR_IMPLEMENTATION_CHECKLIST.md`

✅ **Contenu** :
- Checklist complète phase par phase
- Phase 1 : Setup & Infrastructure
- Phase 2 : MVP - Endpoint Principal
- Phase 3 : Endpoints Complémentaires
- Phase 4 : Optimisations & Production
- Checklist validation finale
- Métriques de succès
- Next steps après MVP

👉 **Quand l'utiliser** : Pendant l'implémentation pour ne rien oublier

---

## 🚀 Quick Start

### Étape 1 : Configuration

```bash
# 1. Ajouter dans .env
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c
VIATOR_ENV=dev
VIATOR_BASE_URL=https://api.viator.com

# 2. Installer dépendances
pip install tenacity==8.2.3

# 3. Créer structure de dossiers
mkdir -p app/services/viator app/repositories app/utils app/api/v1
```

### Étape 2 : Implémentation Minimale

Suivre la [Checklist d'Implémentation](./VIATOR_IMPLEMENTATION_CHECKLIST.md) Phase 1 et 2.

### Étape 3 : Test

```bash
# Lancer le serveur
uvicorn app.main:app --reload

# Tester l'endpoint
curl -X POST http://localhost:8000/api/v1/activities/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"city": "Paris", "country_code": "FR"},
    "dates": {"start": "2026-03-15"},
    "currency": "EUR"
  }'
```

### Étape 4 : Validation

- ✅ Cache Redis fonctionne
- ✅ Données persistées dans MongoDB
- ✅ Images retournées
- ✅ Prix et ratings corrects

---

## 🏗️ Architecture

### Stack Technique

```
┌─────────────────────────────────────────────────────┐
│                  Frontend / Agents                   │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│             Travliaq-API (FastAPI)                   │
│  ┌─────────────────────────────────────────────┐   │
│  │  POST /api/v1/activities/search             │   │
│  │  GET  /api/v1/activities/{id}               │   │
│  │  POST /api/v1/activities/availability       │   │
│  │  GET  /api/v1/destinations                  │   │
│  │  GET  /api/v1/categories                    │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Activities   │  │ Location     │  │ Viator   │  │
│  │ Service      │─▶│ Resolver     │─▶│ Client   │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│         │                                    │       │
│         ▼                                    ▼       │
│  ┌──────────────┐                  ┌──────────────┐ │
│  │ Redis Cache  │                  │ Viator API   │ │
│  │ (7 days TTL) │                  │ (External)   │ │
│  └──────────────┘                  └──────────────┘ │
│         │                                            │
│         ▼                                            │
│  ┌──────────────┐                                    │
│  │  MongoDB     │                                    │
│  │  (Persist)   │                                    │
│  └──────────────┘                                    │
└─────────────────────────────────────────────────────┘
```

### Flux de Données (Recherche d'Activités)

```
1. Request → LocationResolver
   ├─ Ville "Paris" → Fuzzy match → Destination ID "77"
   ├─ Geo (48.85, 2.35) → Geospatial query → Destination ID "77"
   └─ Destination ID "77" → Direct

2. ActivitiesService
   ├─ Build cache key: activities_search:77:2026-03-15:abc123
   ├─ Check Redis cache
   │  ├─ HIT → Return cached data (< 50ms)
   │  └─ MISS → Continue
   │
   ├─ Call Viator API /products/search
   │  └─ Map filters (categories → tag IDs)
   │
   ├─ Transform response (ViatorMapper)
   │  └─ ProductSummary → Activity (simplified)
   │
   ├─ Cache in Redis (TTL: 7 days)
   │
   ├─ Persist in MongoDB (upsert by product_code)
   │
   └─ Return ActivitySearchResponse

3. Response → Frontend
   └─ JSON with activities, location, cache_info
```

---

## 🔑 Clés API

### Environnements

| Environnement | Clé API | Usage |
|---------------|---------|-------|
| **DEV** | `1029cf59-4682-496d-8c16-9a229a388861` | Développement, tests |
| **PROD** | `a8f758b5-0349-4eb0-99f6-41381526417c` | Production |

### Configuration

```python
# Dans .env
VIATOR_ENV=dev  # ou prod

# Dans code (automatique)
api_key = settings.viator_api_key  # Sélectionne automatiquement dev ou prod
```

### Rate Limits Viator

- **Limite** : Variable selon contrat (vérifier headers `RateLimit-*`)
- **Gestion** : Retry automatique avec backoff exponentiel
- **Cache** : Réduit drastiquement les appels API (hit ratio > 60%)

---

## 📊 Endpoints Disponibles

### 1. Recherche d'Activités (MVP)

```http
POST /api/v1/activities/search
Content-Type: application/json

{
  "location": {"city": "Paris", "country_code": "FR"},
  "dates": {"start": "2026-03-15", "end": "2026-03-20"},
  "filters": {
    "categories": ["food", "museum"],
    "price_range": {"min": 10, "max": 200},
    "rating_min": 4.0
  },
  "sorting": {"sort_by": "rating", "order": "desc"},
  "pagination": {"page": 1, "limit": 20},
  "currency": "EUR",
  "language": "fr"
}
```

**Réponse** : [Voir exemple complet](./VIATOR_API_WRAPPER_PLAN.md#1-post-apiv1activitiessearch--endpoint-principal-mvp)

### 2. Détails d'une Activité

```http
GET /api/v1/activities/{activity_id}
```

### 3. Vérification Disponibilité

```http
POST /api/v1/activities/availability

{
  "activity_id": "5010SYDNEY",
  "date": "2026-03-15",
  "travelers": {"adults": 2, "children": 1},
  "currency": "EUR"
}
```

### 4. Liste des Destinations

```http
GET /api/v1/destinations?country_code=FR&search=paris
```

### 5. Liste des Catégories

```http
GET /api/v1/categories
```

---

## 🗄️ Collections MongoDB

### `activities`
- **Documents** : ~10k-100k activités
- **Index** : product_code (unique), destination.id, categories, location (2dsphere)
- **Upsert** : Mise à jour automatique avec `last_updated`

### `destinations`
- **Documents** : ~5k destinations (villes, pays, régions)
- **Index** : destination_id (unique), slug, country_code, location (2dsphere), name (text)
- **Sync** : Refresh hebdomadaire

### `categories`
- **Documents** : ~20-50 catégories simplifiées
- **Index** : id (unique), viator_tags
- **Mapping** : food → [21972, 21973], museum → [21975], etc.

---

## 📈 Métriques Cibles

| Métrique | Cible | Comment mesurer |
|----------|-------|-----------------|
| **Latence (cache hit)** | < 500ms | Logs + monitoring |
| **Latence (cache miss)** | < 2s | Logs + monitoring |
| **Cache hit ratio** | > 60% | Redis stats |
| **Throughput** | > 100 req/s | Load testing (k6) |
| **Error rate** | < 1% | Logs + monitoring |
| **Test coverage** | > 80% | `pytest --cov` |

---

## 🐛 Gestion d'Erreurs

### Codes d'Erreur

| Code | Statut | Description | Action |
|------|--------|-------------|--------|
| `DESTINATION_NOT_FOUND` | 404 | Ville introuvable | Fournir suggestions |
| `INVALID_DATE_RANGE` | 400 | Dates invalides | Corriger dates |
| `INVALID_LOCATION` | 400 | Location manquante | Fournir city/geo/destination_id |
| `VIATOR_API_ERROR` | 502 | Erreur API Viator | Retry automatique |
| `CACHE_ERROR` | 503 | Redis indisponible | Fallback direct Viator |
| `DATABASE_ERROR` | 503 | MongoDB indisponible | Erreur 503 |

### Retry Logic

- **Erreurs réseau** : 3 tentatives avec backoff exponentiel (2s, 4s, 8s)
- **Rate limit (429)** : Respect header `Retry-After`
- **Erreurs 5xx Viator** : 3 tentatives avec pause 1s

---

## 🔧 Maintenance

### Tasks Réguliers

**Quotidien** :
- Nettoyer clés Redis expirées (automatique)
- Vérifier logs d'erreurs

**Hebdomadaire** :
- Refresh destinations MongoDB (`scripts/ingest_destinations.py`)
- Analyser cache hit ratio

**Mensuel** :
- Mettre à jour mapping catégories → tags Viator
- Review métriques performance
- Update documentation si nouveaux endpoints

### Invalidation Cache

```bash
# Invalider cache pour Paris
curl -X DELETE http://localhost:8000/api/v1/admin/cache/activities_search:77:*

# Invalider cache pour une activité
curl -X DELETE http://localhost:8000/api/v1/admin/cache/activity_details:5010SYDNEY
```

---

## 🧪 Tests

### Tests Unitaires

```bash
pytest tests/unit/ --cov=app --cov-report=html
```

### Tests d'Intégration

```bash
pytest tests/integration/ -v
```

### Load Testing

```bash
# Avec k6
k6 run tests/load/search_activities.js

# Objectif: 100 req/s sans erreur
```

---

## 📚 Ressources Externes

### Documentation Viator

- **API Docs** : https://docs.viator.com/partner-api/
- **Tags Guide** : https://partnerresources.viator.com/travel-commerce/tags
- **Affiliate Guide** : https://partnerresources.viator.com/travel-commerce/affiliate/

### Outils

- **Swagger UI** : http://localhost:8000/docs (après démarrage)
- **ReDoc** : http://localhost:8000/redoc
- **Health Check** : http://localhost:8000/api/v1/health

---

## 🤝 Support

### Questions Fréquentes

**Q: Dois-je toujours fournir le country_code avec la ville ?**
R: Non, c'est optionnel mais **fortement recommandé** car ça améliore la précision du fuzzy matching.

**Q: Quelle est la différence entre destination_id et city ?**
R: `destination_id` est l'ID interne Viator (direct), `city` est le nom de ville (nécessite résolution).

**Q: Comment gérer les activités sans images ?**
R: L'API retourne toujours un array `images`, qui peut être vide `[]`.

**Q: Le cache Redis est-il partagé entre dev et prod ?**
R: Non, utiliser des instances Redis séparées pour dev/prod.

**Q: Combien d'appels Viator API par recherche ?**
R: 1 seul appel pour `/products/search`. Le cache réduit drastiquement les appels répétés.

### Contact

- **Repo GitHub** : [Lien vers repo]
- **Issues** : [Lien vers issues]
- **Slack** : #travliaq-api

---

## 🗺️ Roadmap

### ✅ Phase 1 - MVP (Semaine 1-2)
- Endpoint `/search` avec cache Redis + MongoDB
- Résolution ville → destination_id
- Documentation complète

### 🔄 Phase 2 - Endpoints Complémentaires (Semaine 3-4)
- `/destinations`, `/categories`
- Détails activité
- Vérification disponibilité

### 🚀 Phase 3 - Production (Semaine 5-6)
- Monitoring & métriques
- Load testing
- Déploiement production

### 🌟 Phase 4 - Améliorations (Futur)
- Recommandations ML
- Booking integration
- API GraphQL
- Dashboard admin

---

## 📝 Historique des Versions

| Version | Date | Changements |
|---------|------|-------------|
| 1.0 | 2026-01-02 | Documentation initiale complète |

---

**Créé avec ❤️ par Claude (Anthropic) pour Travliaq**

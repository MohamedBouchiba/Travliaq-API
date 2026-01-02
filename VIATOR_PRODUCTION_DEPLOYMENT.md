# Viator Integration - Guide de Déploiement Production

## ✅ Solution Production-Ready (Sans Code Hardcodé)

Cette implémentation est **100% robuste** et utilise l'API Viator officielle pour récupérer toutes les destinations.

## Architecture

### Services Créés

1. **ViatorDestinationsService** ([app/services/viator/destinations.py](app/services/viator/destinations.py))
   - Appelle l'endpoint GET `/destinations` de Viator
   - Récupère TOUTES les destinations officielles de Viator
   - Pas de données hardcodées

2. **DestinationsSyncService** ([app/services/destinations_sync.py](app/services/destinations_sync.py))
   - Synchronise les destinations Viator vers MongoDB
   - Transforme les données au format de notre schéma
   - Gère les types de destinations (city, country, region, etc.)
   - Mapping automatique des country codes

3. **Admin Endpoints** ([app/api/admin_routes.py](app/api/admin_routes.py))
   - `POST /admin/destinations/sync` - Synchroniser les destinations
   - `GET /admin/destinations/stats` - Statistiques sur les destinations

## Étapes de Déploiement

### 1. Configuration Environnement

Ajoute ces variables à ton `.env` de production:

```bash
# Viator API (Requis)
VIATOR_API_KEY_DEV=1029cf59-4682-496d-8c16-9a229a388861
VIATOR_API_KEY_PROD=a8f758b5-0349-4eb0-99f6-41381526417c
VIATOR_ENV=prod  # Important: utiliser "prod" en production

# MongoDB Collections (Déjà configuré)
MONGODB_COLLECTION_ACTIVITIES=activities
MONGODB_COLLECTION_DESTINATIONS=destinations
MONGODB_COLLECTION_CATEGORIES=categories
```

### 2. Déployer le Code

```bash
# Les fichiers suivants doivent être déployés:
git add app/services/viator/destinations.py
git add app/services/destinations_sync.py
git add app/api/admin_routes.py
git add app/main.py
git add app/services/location_resolver.py
git add app/services/activities_service.py

git commit -m "feat: Production-ready Viator integration with API-based destinations sync"
git push
```

### 3. Synchroniser les Destinations (IMPORTANT!)

**Après le déploiement, tu DOIS exécuter cette étape une fois:**

#### Option A: Via API (Recommandé)

```bash
# Synchroniser TOUTES les destinations (villes, pays, régions, etc.)
curl -X POST "https://travliaq-api-production.up.railway.app/admin/destinations/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "cities_only": false
  }'
```

**OU synchroniser uniquement les villes (plus rapide):**

```bash
curl -X POST "https://travliaq-api-production.up.railway.app/admin/destinations/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "cities_only": true
  }'
```

#### Réponse Attendue

```json
{
  "success": true,
  "message": "Successfully synced 1543 destinations from Viator API",
  "stats": {
    "total_fetched": 1543,
    "inserted": 0,
    "updated": 1543,
    "skipped": 0,
    "errors": 0,
    "by_type": {
      "CITY": {
        "inserted": 0,
        "updated": 892
      },
      "COUNTRY": {
        "inserted": 0,
        "updated": 195
      },
      "REGION": {
        "inserted": 0,
        "updated": 456
      }
    },
    "duration_seconds": 45.3
  }
}
```

### 4. Vérifier la Synchronisation

```bash
# Vérifier les statistiques
curl "https://travliaq-api-production.up.railway.app/admin/destinations/stats"
```

**Réponse attendue:**

```json
{
  "total_destinations": 1543,
  "by_type": {
    "cities": 892,
    "countries": 195,
    "regions": 456,
    "other": 0
  },
  "last_sync": "2026-01-02T15:30:00",
  "database_populated": true
}
```

### 5. Tester l'Endpoint Activities

```bash
# Test de recherche d'activités à Paris
curl -X POST "https://travliaq-api-production.up.railway.app/api/v1/activities/search" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "city": "Paris",
      "country_code": "FR"
    },
    "dates": {
      "start": "2026-03-15"
    },
    "filters": {
      "rating_min": 4
    },
    "pagination": {
      "page": 1,
      "limit": 10
    },
    "currency": "EUR",
    "language": "fr"
  }'
```

**Réponse attendue:** HTTP 200 avec liste d'activités

## Maintenance

### Rafraîchir les Destinations (Hebdomadaire)

Les destinations Viator peuvent changer (nouvelles villes, mises à jour). Il est recommandé de re-synchroniser **une fois par semaine**:

```bash
# Peut être automatisé avec un cron job ou scheduled task
curl -X POST "https://travliaq-api-production.up.railway.app/admin/destinations/sync" \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}'
```

### Monitoring

Vérifie régulièrement les stats:

```bash
curl "https://travliaq-api-production.up.railway.app/admin/destinations/stats"
```

Si `database_populated: false`, re-synchronise les destinations.

## Résolution de Problèmes

### Erreur: "No cities found in database"

**Cause**: La collection destinations est vide

**Solution**:
```bash
POST /admin/destinations/sync
```

### Erreur: 503 Service Unavailable

**Cause**: Les clés API Viator ne sont pas configurées

**Solution**: Vérifie que `VIATOR_API_KEY_PROD` et `VIATOR_ENV=prod` sont dans les variables d'environnement

### Sync trop lent / Timeout

**Option 1**: Synchroniser uniquement les villes
```json
{
  "cities_only": true
}
```

**Option 2**: Filtrer par types spécifiques
```json
{
  "filter_types": ["CITY", "COUNTRY"]
}
```

## Avantages de cette Solution

✅ **Aucun code hardcodé** - Toutes les données viennent de l'API Viator
✅ **Toujours à jour** - Synchronisation depuis la source officielle
✅ **Scalable** - Supporte des milliers de destinations
✅ **Flexible** - Possibilité de filtrer par type, langue, etc.
✅ **Robuste** - Gestion d'erreurs complète
✅ **Production-ready** - Prêt pour le déploiement en production

## Différences avec l'Ancienne Approche

| Aspect | ❌ Approche Hardcodée | ✅ Approche Production |
|--------|---------------------|----------------------|
| Source de données | 10 villes hardcodées dans le code | Toutes les destinations depuis API Viator |
| Nombre de destinations | 10 | 1500+ |
| Mise à jour | Nécessite changement de code | Simple appel API |
| Maintenance | Difficile | Automatisable |
| Scalabilité | Limitée | Illimitée |
| Fiabilité | Données peuvent devenir obsolètes | Toujours à jour avec Viator |

## Sécurité

### Protection de l'Endpoint Admin

**Important**: L'endpoint `/admin/destinations/sync` devrait être protégé en production.

Tu peux ajouter une authentification:

```python
# Dans app/api/admin_routes.py
from fastapi import Header, HTTPException

async def verify_admin_token(x_admin_token: str = Header(...)):
    if x_admin_token != os.getenv("ADMIN_API_TOKEN"):
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("/destinations/sync", dependencies=[Depends(verify_admin_token)])
async def sync_destinations(...):
    ...
```

Puis dans `.env`:
```bash
ADMIN_API_TOKEN=votre-token-secret-ici
```

Et utiliser:
```bash
curl -X POST ".../admin/destinations/sync" \
  -H "X-Admin-Token: votre-token-secret-ici" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Checklist de Déploiement

- [ ] Variables d'environnement configurées (`VIATOR_API_KEY_PROD`, `VIATOR_ENV=prod`)
- [ ] Code déployé sur production
- [ ] Application redémarrée
- [ ] Synchronisation des destinations effectuée (`POST /admin/destinations/sync`)
- [ ] Vérification des stats (`GET /admin/destinations/stats`)
- [ ] Test de l'endpoint activities (`POST /api/v1/activities/search`)
- [ ] Planification de la synchronisation hebdomadaire
- [ ] (Optionnel) Protection de l'endpoint admin

## Support

Si tu rencontres des problèmes:

1. Vérifie les logs de l'application
2. Vérifie les stats: `GET /admin/destinations/stats`
3. Re-synchronise si nécessaire: `POST /admin/destinations/sync`
4. Vérifie que les clés API Viator sont valides

## Prochaines Étapes (Optionnel)

1. **Automatiser la synchronisation**
   - Créer un cron job / scheduled task pour sync hebdomadaire

2. **Endpoint de suggestion**
   - Créer `GET /api/v1/destinations/autocomplete?q=par` pour suggérer des villes

3. **Cache des destinations populaires**
   - Mettre en cache Redis les destinations les plus recherchées

4. **Multi-langue**
   - Synchroniser les destinations en plusieurs langues
   - Stocker les traductions dans MongoDB

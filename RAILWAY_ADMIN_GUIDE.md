# Guide d'Administration Railway - Viator API

Ce guide explique comment gérer votre API Viator depuis Railway via des endpoints HTTP.

## 📋 Table des matières

1. [Synchronisation des Tags (REQUIS)](#1-synchronisation-des-tags-requis)
2. [Vérification du statut des tags](#2-vérification-du-statut-des-tags)
3. [Recherche de tags](#3-recherche-de-tags)
4. [Synchronisation des destinations](#4-synchronisation-des-destinations)
5. [Dépannage](#5-dépannage)

---

## 1. Synchronisation des Tags (REQUIS)

**⚠️ IMPORTANT**: Cette étape est **OBLIGATOIRE** avant d'utiliser les filtres de catégories dans la recherche d'activités.

### Endpoint
```
POST https://travliaq-api-production.up.railway.app/admin/tags/sync
```

### Exemple avec curl
```bash
curl -X POST 'https://travliaq-api-production.up.railway.app/admin/tags/sync' \
  -H 'Content-Type: application/json' \
  -d '{"language": "en"}'
```

### Réponse attendue
```json
{
  "success": true,
  "message": "Successfully synced 245 tags from Viator API (15 root tags, 230 child tags)",
  "stats": {
    "total_fetched": 245,
    "updated": 245,
    "errors": 0,
    "root_tags": 15,
    "child_tags": 230,
    "started_at": "2026-01-02T12:00:00",
    "completed_at": "2026-01-02T12:00:30"
  }
}
```

### Durée
- Temps estimé: 10-30 secondes
- Opération asynchrone (l'endpoint attend la fin de la synchronisation)

### Quand exécuter ?
- **Une fois** lors du premier déploiement (OBLIGATOIRE)
- **Hebdomadairement** pour rafraîchir les données (recommandé par Viator)
- Après une mise à jour du schéma des tags

---

## 2. Vérification du Statut des Tags

### Endpoint
```
GET https://travliaq-api-production.up.railway.app/admin/tags/stats
```

### Exemple avec curl
```bash
curl 'https://travliaq-api-production.up.railway.app/admin/tags/stats'
```

### Réponse
```json
{
  "total_tags": 245,
  "root_tags": 15,
  "child_tags": 230,
  "last_sync": "2026-01-02T12:00:30",
  "database_populated": true,
  "sample_root_tags": [
    "Food & Drink",
    "Cultural & Theme Tours",
    "Water Sports",
    "Museums",
    "Air, Helicopter & Balloon Tours",
    "Shows & Performances",
    "Nature & Wildlife",
    "Classes & Workshops",
    "Outdoor Activities",
    "Day Trips & Excursions"
  ],
  "ready_for_use": true
}
```

### Interprétation
- `database_populated: true` ✅ Tags synchronisés
- `database_populated: false` ❌ Besoin de synchroniser (voir section 1)
- `ready_for_use: true` ✅ Les filtres de catégories fonctionneront
- `last_sync` - Date de la dernière synchronisation

---

## 3. Recherche de Tags

Utile pour **déboguer** les filtres de catégories et voir quels tags correspondent à un mot-clé.

### Endpoint
```
GET https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=food&language=en
```

### Exemple avec curl
```bash
curl 'https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=food&language=en'
```

### Réponse
```json
{
  "keyword": "food",
  "language": "en",
  "count": 8,
  "results": [
    {
      "tag_id": 19927,
      "tag_name": "Food & Drink",
      "parent_tag_id": null,
      "all_names": {
        "en": "Food & Drink",
        "fr": "Gastronomie",
        "es": "Gastronomía",
        "de": "Essen & Trinken"
      }
    },
    {
      "tag_id": 19928,
      "tag_name": "Food Tours",
      "parent_tag_id": 19927,
      "all_names": {
        "en": "Food Tours",
        "fr": "Circuits gastronomiques",
        "es": "Tours gastronómicos"
      }
    }
    // ... plus de résultats
  ],
  "tag_ids": [19927, 19928, 19929, ...]
}
```

### Utilisation
Les `tag_ids` retournés sont exactement ceux envoyés à l'API Viator quand vous utilisez `"categories": ["food"]` dans la recherche d'activités.

### Tester d'autres catégories
```bash
# Museum
curl 'https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=museum'

# Art
curl 'https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=art'

# Tours
curl 'https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=tours'

# Water (activités aquatiques)
curl 'https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=water'
```

---

## 4. Synchronisation des Destinations

Les destinations sont déjà synchronisées, mais si besoin de rafraîchir:

### Endpoint
```
POST https://travliaq-api-production.up.railway.app/admin/destinations/sync
```

### Exemple avec curl
```bash
# Synchroniser toutes les destinations
curl -X POST 'https://travliaq-api-production.up.railway.app/admin/destinations/sync' \
  -H 'Content-Type: application/json' \
  -d '{"language": "en"}'

# Synchroniser uniquement les villes (plus rapide)
curl -X POST 'https://travliaq-api-production.up.railway.app/admin/destinations/sync' \
  -H 'Content-Type: application/json' \
  -d '{"language": "en", "cities_only": true}'
```

### Statut des destinations
```bash
curl 'https://travliaq-api-production.up.railway.app/admin/destinations/stats'
```

---

## 5. Dépannage

### Problème: "Tags repository is not initialized"

**Cause**: La variable d'environnement `MONGODB_COLLECTION_TAGS` n'est pas définie.

**Solution**:
1. Aller dans Railway → Projet → Variables
2. Ajouter: `MONGODB_COLLECTION_TAGS=tags`
3. Redéployer

### Problème: "Viator integration is not configured"

**Cause**: Les clés API Viator ne sont pas configurées.

**Solution**:
1. Vérifier les variables d'environnement:
   - `VIATOR_API_KEY_DEV`
   - `VIATOR_API_KEY_PROD`
   - `VIATOR_ENV=dev` ou `prod`
   - `VIATOR_BASE_URL=https://api.viator.com/partner`

### Problème: Recherche d'activités retourne 0 résultats avec catégories

**Diagnostic**:
```bash
# 1. Vérifier que les tags sont synchronisés
curl 'https://travliaq-api-production.up.railway.app/admin/tags/stats'

# 2. Vérifier quels tags matchent votre catégorie
curl 'https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=museum'
```

**Solutions possibles**:
1. Si `database_populated: false` → Synchroniser les tags (section 1)
2. Si aucun tag ne matche → Utiliser un autre mot-clé ou chercher sans catégories
3. Vider le cache Redis si résultats en cache:
   ```bash
   curl -X POST 'https://travliaq-api-production.up.railway.app/admin/cache/clear'
   ```

### Problème: Timeout lors de la synchronisation

**Cause**: Railway peut avoir des timeouts sur les requêtes longues.

**Solutions**:
1. Augmenter le timeout Railway si possible
2. La synchronisation devrait prendre 10-30 secondes maximum
3. Si échec, réessayer - l'opération est idempotente (safe to retry)

---

## 📊 Flux de travail recommandé

### Premier déploiement
```bash
# 1. Synchroniser les tags (REQUIS)
curl -X POST 'https://travliaq-api-production.up.railway.app/admin/tags/sync' \
  -H 'Content-Type: application/json' \
  -d '{"language": "en"}'

# 2. Vérifier le statut
curl 'https://travliaq-api-production.up.railway.app/admin/tags/stats'

# 3. Tester une recherche avec catégories
curl -X POST 'https://travliaq-api-production.up.railway.app/api/v1/activities/search' \
  -H 'Content-Type: application/json' \
  -d '{
    "location": {"city": "Rome", "country_code": "IT"},
    "dates": {"start": "2026-05-10"},
    "filters": {"categories": ["museum"]},
    "currency": "EUR"
  }'
```

### Maintenance hebdomadaire
```bash
# Rafraîchir les tags (recommandé par Viator)
curl -X POST 'https://travliaq-api-production.up.railway.app/admin/tags/sync' \
  -H 'Content-Type: application/json' \
  -d '{"language": "en"}'

# Optionnel: Rafraîchir les destinations
curl -X POST 'https://travliaq-api-production.up.railway.app/admin/destinations/sync' \
  -H 'Content-Type: application/json' \
  -d '{"language": "en"}'
```

---

## 🎯 Endpoints disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/admin/tags/sync` | Synchroniser tags depuis Viator (REQUIS) |
| GET | `/admin/tags/stats` | Statistiques des tags |
| GET | `/admin/tags/search?keyword=X` | Rechercher tags par mot-clé |
| GET | `/admin/tags/root` | Lister tous les tags racine |
| POST | `/admin/destinations/sync` | Synchroniser destinations |
| GET | `/admin/destinations/stats` | Statistiques destinations |
| POST | `/admin/cache/clear` | Vider le cache Redis |

---

## ✅ Checklist de déploiement

- [ ] Variables d'environnement configurées dans Railway
  - [ ] `MONGODB_COLLECTION_TAGS=tags`
  - [ ] `VIATOR_API_KEY_DEV` ou `VIATOR_API_KEY_PROD`
  - [ ] `VIATOR_ENV=dev` ou `prod`
- [ ] Code déployé sur Railway
- [ ] **Tags synchronisés** via `/admin/tags/sync` ⚠️ CRITIQUE
- [ ] Vérifié avec `/admin/tags/stats` que `ready_for_use: true`
- [ ] Testé une recherche d'activités avec catégories
- [ ] Planifié un refresh hebdomadaire des tags

---

**Créé le**: 2026-01-02
**Dernière mise à jour**: 2026-01-02
**Version API**: v1

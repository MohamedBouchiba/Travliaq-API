# Système de Cache - Documentation

Le système de cache en mémoire réduit la charge sur la base de données PostgreSQL en stockant temporairement les résultats des requêtes fréquentes.

## Architecture

### Composants

**[app/core/cache.py](app/core/cache.py)**
- `SimpleCache`: Classe de cache en mémoire avec TTL (Time To Live)
- `@cache_result`: Décorateur pour cacher automatiquement les résultats de fonctions
- Nettoyage automatique des entrées expirées

### Durées de Cache (TTL)

| Endpoint | Service | TTL | Raison |
|----------|---------|-----|--------|
| `/autocomplete` | AutocompleteService | 10 min | Données stables, requêtes fréquentes |
| `/top-cities/{code}` | CitiesService | 30 min | Populations changent rarement |
| `/nearest-airports` | AirportsService | 15 min | Données géographiques stables |

## Fonctionnement

### Mécanisme de Cache

```python
@cache_result(ttl_seconds=600)  # Cache pour 10 minutes
def search(self, q: str, limit: int = 10):
    # La fonction est exécutée seulement si:
    # 1. Aucun résultat en cache pour ces paramètres
    # 2. Le cache a expiré (> 10 minutes)
    return results
```

### Clé de Cache

Chaque résultat est stocké avec une clé unique basée sur:
- Nom de la fonction
- Tous les arguments (args + kwargs)
- Hash MD5 pour garantir l'unicité

**Exemple:**
```python
# Appel 1
search(q="Paris", limit=10)
# Clé: "search:abc123def456..."

# Appel 2 (même requête) - utilise le cache
search(q="Paris", limit=10)
# Clé: "search:abc123def456..." (même clé = cache hit)

# Appel 3 (différent) - nouvelle requête DB
search(q="Paris", limit=5)
# Clé: "search:xyz789ghi012..." (différente = cache miss)
```

## Nettoyage du Cache

### Automatique

Une tâche de fond s'exécute **toutes les heures** pour supprimer les entrées expirées:

```python
async def cleanup_cache_task():
    while True:
        await asyncio.sleep(3600)  # 1 heure
        cleanup_expired_cache()
```

Démarrée automatiquement au lancement de l'application dans `main.py`.

### Manuel

#### Via API

**Nettoyer tout le cache:**
```bash
POST /admin/cache/clear
```

**Supprimer uniquement les entrées expirées:**
```bash
POST /admin/cache/cleanup
```

#### Via Code

```python
from app.core.cache import clear_cache, cleanup_expired_cache

# Vider complètement le cache
clear_cache()

# Nettoyer seulement les entrées expirées
cleanup_expired_cache()
```

## Avantages

### Performance

- **Première requête**: Temps normal (~50-200ms selon l'endpoint)
- **Requêtes suivantes**: ~5-10ms (99% plus rapide)
- **Réduction de charge DB**: Jusqu'à 90% pour les requêtes répétées

### Exemple de Gains

```
Scénario: 1000 recherches autocomplete "Paris" en 10 minutes

Sans cache:
- 1000 requêtes PostgreSQL
- Temps total: ~50,000ms (50 secondes)
- Charge DB: Élevée

Avec cache (10 min):
- 1 requête PostgreSQL + 999 cache hits
- Temps total: ~50ms + 999×5ms = ~5,045ms (5 secondes)
- Charge DB: Minimale
- Gain: 90% de temps économisé
```

## Monitoring

### Vérifier l'État du Cache

```bash
# Health check
GET /admin/health
```

### Logs

Les services loguent les opérations:
```
INFO: Autocomplete search for 'Paris' returned 10 results
```

## Limitations

### Mémoire

- Cache stocké en RAM
- Croissance proportionnelle au nombre de requêtes uniques
- Nettoyage automatique limite la croissance

### Invalidation

- **Pas de synchronisation multi-instance**: Chaque instance a son propre cache
- **Pas d'invalidation automatique**: Les données changent dans la DB mais restent en cache jusqu'à expiration
- **Solution**: Ajuster les TTL selon la fréquence de mise à jour des données

## Cas d'Usage

### Recommandé ✅

- Recherches répétées (autocomplete pendant la saisie)
- Données géographiques stables (villes, aéroports)
- Requêtes lentes mais résultats stables

### Non Recommandé ❌

- Données changeant fréquemment (< 1 minute)
- Données personnalisées par utilisateur
- Opérations d'écriture (POST, PUT, DELETE)

## Configuration

### Modifier les TTL

Éditer les décorateurs dans les services:

```python
# app/services/autocomplete.py
@cache_result(ttl_seconds=600)  # Changer à 300 pour 5 minutes
def search(self, ...):
    ...
```

### Désactiver le Cache

Commenter ou retirer les décorateurs `@cache_result`:

```python
# @cache_result(ttl_seconds=600)  # Désactivé
def search(self, ...):
    ...
```

## Troubleshooting

### Le Cache ne se vide pas

**Symptôme**: Données obsolètes même après expiration du TTL

**Solutions**:
1. Vérifier que la tâche de nettoyage fonctionne
2. Forcer le nettoyage: `POST /admin/cache/cleanup`
3. Vider complètement: `POST /admin/cache/clear`

### Utilisation mémoire élevée

**Symptôme**: RAM importante utilisée

**Solutions**:
1. Réduire les TTL
2. Nettoyer le cache: `POST /admin/cache/clear`
3. Redémarrer l'application

### Cache miss fréquents

**Symptôme**: Performance faible malgré le cache

**Causes possibles**:
- Paramètres variables (limit différent à chaque fois)
- TTL trop court
- Cache vidé trop fréquemment

**Solutions**:
- Standardiser les paramètres côté frontend
- Augmenter les TTL
- Vérifier les logs de nettoyage

## Best Practices

1. **Monitorer la RAM**: Surveiller l'utilisation mémoire en production
2. **Ajuster les TTL**: Selon les patterns d'usage réels
3. **Logs**: Activer les logs pour comprendre les patterns de cache
4. **Tests**: Tester avec et sans cache pour valider les gains
5. **Documentation**: Documenter les changements de TTL

## Migration & Rollback

### Activer le cache progressivement

```python
# Phase 1: Activer seulement autocomplete
@cache_result(ttl_seconds=600)
def search(self, ...):
    ...

# Phase 2: Activer les autres services
# Après validation en production
```

### Rollback rapide

Si problème en production:
1. Vider le cache: `POST /admin/cache/clear`
2. Désactiver les décorateurs dans le code
3. Redéployer

---

**Version**: 1.0
**Dernière mise à jour**: 2025-12-23

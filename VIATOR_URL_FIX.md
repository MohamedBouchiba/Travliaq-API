# ⚠️ CORRECTION URGENTE - URL de Base Viator

## Problème Identifié

L'URL de base de l'API Viator était **incorrecte** dans la configuration:
- ❌ **Incorrect**: `https://api.viator.com`
- ✅ **Correct**: `https://api.viator.com/partner`

## Ce Qui a Été Corrigé

### 1. app/core/config.py
```python
# Avant (INCORRECT)
viator_base_url: str = Field("https://api.viator.com", alias="VIATOR_BASE_URL")

# Après (CORRECT)
viator_base_url: str = Field("https://api.viator.com/partner", alias="VIATOR_BASE_URL")
```

### 2. .env.example
```bash
# Avant (INCORRECT)
VIATOR_BASE_URL=https://api.viator.com

# Après (CORRECT)
VIATOR_BASE_URL=https://api.viator.com/partner
```

## Action Requise IMMÉDIATEMENT

### Sur Ton Environnement Local

Modifie ton fichier `.env`:

```bash
# Ouvre e:\CrewTravliaq\Travliaq-API\.env
# Change cette ligne:
VIATOR_BASE_URL=https://api.viator.com/partner
```

### Sur Railway (Production)

Modifie la variable d'environnement Railway:

1. Va dans ton projet Railway
2. Trouve la variable `VIATOR_BASE_URL`
3. Change la valeur vers: `https://api.viator.com/partner`
4. Redémarre l'application

**OU si la variable n'existe pas**, elle utilisera la valeur par défaut qui est maintenant correcte dans `config.py`.

## Vérification

Après le déploiement, teste à nouveau:

```bash
curl -X POST "https://travliaq-api-production.up.railway.app/admin/destinations/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "cities_only": true
  }'
```

**Réponse attendue**: HTTP 200 avec les destinations synchronisées

## Source de la Correction

Selon l'OpenAPI spec de Viator (ligne 12-17):

```json
{
  "servers": [
    {
      "url": "https://api.viator.com/partner",
      "description": "Production server (uses live data)"
    },
    {
      "url": "https://api.sandbox.viator.com/partner",
      "description": "Sandbox server (uses test data)"
    }
  ]
}
```

Tous les endpoints Viator nécessitent le préfixe `/partner` dans l'URL de base.

## Impact

- **Avant**: Toutes les requêtes Viator retournaient 404
- **Après**: Les requêtes fonctionneront correctement

Cette correction est **critique** pour le bon fonctionnement de l'intégration Viator.

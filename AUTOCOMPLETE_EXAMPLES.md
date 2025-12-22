# Exemples d'utilisation de l'API Autocomplete

## Endpoint

```
GET /autocomplete?q={query}&limit={limit}&types={types}
```

## Exemples curl

### 1. Recherche basique "Paris"

```bash
curl "http://localhost:8000/autocomplete?q=par&limit=10&types=city,airport,country"
```

**Réponse:**
```json
{
  "q": "par",
  "results": [
    {
      "type": "city",
      "id": "3978405a-2f88-40fd-a9d1-1b7c896626ff",
      "label": "Paris, FR",
      "country_code": "FR",
      "slug": "paris",
      "lat": 48.8566,
      "lon": 2.3522
    },
    {
      "type": "airport",
      "id": "CDG",
      "label": "Paris Charles de Gaulle (CDG)",
      "country_code": "FR",
      "slug": "paris-charles-de-gaulle-cdg",
      "lat": 49.0097,
      "lon": 2.5479
    },
    {
      "type": "country",
      "id": "PY",
      "label": "Paraguay",
      "country_code": "PY",
      "slug": "paraguay",
      "lat": null,
      "lon": null
    }
  ]
}
```

### 2. Recherche uniquement aéroports

```bash
curl "http://localhost:8000/autocomplete?q=CDG&limit=5&types=airport"
```

**Réponse:**
```json
{
  "q": "CDG",
  "results": [
    {
      "type": "airport",
      "id": "CDG",
      "label": "Paris Charles de Gaulle (CDG)",
      "country_code": "FR",
      "slug": "paris-charles-de-gaulle-cdg",
      "lat": 49.0097,
      "lon": 2.5479
    }
  ]
}
```

### 3. Recherche uniquement villes et aéroports

```bash
curl "http://localhost:8000/autocomplete?q=New&limit=10&types=city,airport"
```

### 4. Recherche de pays uniquement

```bash
curl "http://localhost:8000/autocomplete?q=Fran&limit=10&types=country"
```

**Réponse:**
```json
{
  "q": "Fran",
  "results": [
    {
      "type": "country",
      "id": "FR",
      "label": "France",
      "country_code": "FR",
      "slug": "france",
      "lat": null,
      "lon": null
    },
    {
      "type": "country",
      "id": "PF",
      "label": "French Polynesia",
      "country_code": "PF",
      "slug": "french-polynesia",
      "lat": null,
      "lon": null
    }
  ]
}
```

### 5. Query < 3 caractères → résultats vides

```bash
curl "http://localhost:8000/autocomplete?q=Pa&limit=10&types=city,airport,country"
```

**Réponse:**
```json
{
  "q": "Pa",
  "results": []
}
```

### 6. Limite de résultats

```bash
curl "http://localhost:8000/autocomplete?q=London&limit=3&types=city,airport,country"
```

## Exemples JavaScript (Frontend)

### Fetch API

```javascript
async function searchLocations(query, limit = 10, types = 'city,airport,country') {
  const params = new URLSearchParams({
    q: query,
    limit: limit.toString(),
    types: types
  });

  const response = await fetch(`/autocomplete?${params}`);
  const data = await response.json();

  return data;
}

// Usage
const results = await searchLocations('par', 10);
console.log(results);
// { q: "par", results: [...] }
```

### Axios

```javascript
import axios from 'axios';

async function searchLocations(query, limit = 10, types = 'city,airport,country') {
  const { data } = await axios.get('/autocomplete', {
    params: { q: query, limit, types }
  });

  return data;
}

// Usage
const results = await searchLocations('par', 10);
```

### React Hook avec debounce

```typescript
import { useState, useEffect } from 'react';
import { debounce } from 'lodash';

interface Location {
  type: 'city' | 'airport' | 'country';
  id: string;
  label: string;
  country_code: string;
  slug: string;
  lat: number | null;
  lon: number | null;
}

function useLocationAutocomplete(query: string, types: string = 'city,airport,country') {
  const [results, setResults] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Skip if query < 3 chars
    if (query.length < 3) {
      setResults([]);
      return;
    }

    const searchLocations = debounce(async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          q: query,
          limit: '10',
          types
        });

        const response = await fetch(`/autocomplete?${params}`);
        const data = await response.json();
        setResults(data.results);
      } catch (error) {
        console.error('Search failed:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    searchLocations();

    return () => searchLocations.cancel();
  }, [query, types]);

  return { results, loading };
}

// Usage in component
function LocationSearch() {
  const [query, setQuery] = useState('');
  const { results, loading } = useLocationAutocomplete(query);

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Rechercher un lieu..."
      />

      {loading && <p>Chargement...</p>}

      {query.length >= 3 && (
        <ul>
          {results.map((location) => (
            <li key={`${location.type}-${location.id}`}>
              <span className={`icon-${location.type}`} />
              {location.label}
            </li>
          ))}
        </ul>
      )}

      {query.length > 0 && query.length < 3 && (
        <p className="hint">Tapez au moins 3 caractères</p>
      )}
    </div>
  );
}
```

## Paramètres détaillés

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `q` | string | ✅ Oui | - | Terme de recherche (min 1 char, résultats vides si < 3) |
| `limit` | integer | ❌ Non | 10 | Nombre max de résultats (min: 1, max: 20) |
| `types` | string | ❌ Non | "city,airport,country" | Types de lieux séparés par virgules |

## Types de lieux

- `city` - Villes
- `airport` - Aéroports
- `country` - Pays

**Exemples de combinaisons:**
- `types=city` - Uniquement villes
- `types=airport` - Uniquement aéroports
- `types=city,airport` - Villes et aéroports
- `types=city,airport,country` - Tous les types (défaut)

## Structure de réponse

```typescript
interface AutocompleteResponse {
  q: string;                    // Query originale
  results: Location[];          // Résultats (vide si q < 3 chars)
}

interface Location {
  type: 'city' | 'airport' | 'country';
  id: string;                   // ISO2 (pays), UUID (ville), IATA (aéroport)
  label: string;                // Label à afficher
  country_code: string;         // Code pays ISO2
  slug: string;                 // Slug URL-friendly
  lat: number | null;           // Latitude (null pour pays)
  lon: number | null;           // Longitude (null pour pays)
}
```

## Comportement

1. **Query < 3 caractères**: Retourne `results: []` (vide)
2. **Tri par pertinence**:
   - Priorité 1: Label commence par la requête
   - Priorité 2: Label contient la requête
   - Ensuite par rang: Pays > Aéroports > Villes (population)
3. **Insensible à la casse**: "par" = "Par" = "PAR"
4. **Trim automatique**: " par " devient "par"

## Codes d'erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 422 | Paramètres invalides (ex: types="invalid") |
| 500 | Erreur serveur |

## Performance

- **Latence typique**: 30-100ms
- **Cache**: Non (données PostgreSQL en temps réel)
- **Rate limit**: Aucune limite actuellement

## Notes pour le frontend

1. **Debounce recommandé**: 300ms pour éviter trop de requêtes
2. **Minimum 3 caractères**: Afficher un message si < 3 chars
3. **Icônes**: Utiliser le champ `type` pour afficher des icônes appropriées
4. **Coordonnées**: Disponibles pour villes et aéroports (null pour pays)
5. **Sélection**: Utiliser `id` + `type` comme clé unique

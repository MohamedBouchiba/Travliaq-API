# API Guide - Frontend Implementation

Documentation pour les endpoints de recherche et géolocalisation.

## 1. Autocomplete Search

**Endpoint:** `GET /autocomplete`

**Usage:** Suggestions de lieux pendant la saisie utilisateur (pays, villes, aéroports).

### Parameters

| Param  | Type   | Required | Default | Description |
|--------|--------|----------|---------|-------------|
| `q`    | string | ✓        | -       | Texte recherché (min 1 char, résultats vides si < 3) |
| `limit`| int    | -        | 10      | Nombre max de résultats (max: 20) |
| `types`| string | -        | "city,airport,country" | Types filtrés (ex: "city,airport") |

### Request Example

```javascript
// Recherche simple
GET /autocomplete?q=par

// Recherche avec filtres
GET /autocomplete?q=par&limit=5&types=city,airport
```

### Response Example

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
    }
  ]
}
```

### Ordre des Résultats

1. **Correspondance** : Résultats commençant par la recherche en premier
2. **Type** : Cities → Airports → Countries
3. **Importance** : Population/rang (rank_signal)

### Frontend Tips

```javascript
// Debounce recommandé (300-500ms)
const searchAutocomplete = debounce(async (query) => {
  if (query.length < 3) return []; // Pas de requête si < 3 chars

  const response = await fetch(`/autocomplete?q=${query}&limit=10`);
  const data = await response.json();
  return data.results;
}, 300);

// Affichage suggéré
results.map(item => ({
  label: item.label,
  type: item.type, // Pour afficher une icône (🏙️ 🛫 🌍)
  value: item
}));
```

---

## 2. Top Cities by Country

**Endpoint:** `GET /top-cities/{country_code}`

**Usage:** Obtenir les villes les plus importantes d'un pays (triées par population).

### Parameters

| Param  | Type   | Required | Default | Description |
|--------|--------|----------|---------|-------------|
| `country_code` | string | ✓ | - | Code ISO2 du pays (ex: "FR", "US", "GB") |
| `limit`| int    | -        | 5       | Nombre de villes à retourner (max: 20) |

### Request Example

```javascript
// Top 5 villes de France
GET /top-cities/FR

// Top 10 villes des États-Unis
GET /top-cities/US?limit=10
```

### Response Example

```json
{
  "country_code": "FR",
  "total_cities": 2847,
  "cities": [
    {
      "id": "3978405a-2f88-40fd-a9d1-1b7c896626ff",
      "name": "Paris",
      "country_code": "FR",
      "slug": "paris",
      "population": 2138551,
      "lat": 48.8566,
      "lon": 2.3522
    },
    {
      "id": "uuid-marseille",
      "name": "Marseille",
      "country_code": "FR",
      "slug": "marseille",
      "population": 869815,
      "lat": 43.2965,
      "lon": 5.3698
    },
    {
      "id": "uuid-lyon",
      "name": "Lyon",
      "country_code": "FR",
      "slug": "lyon",
      "population": 513275,
      "lat": 45.7640,
      "lon": 4.8357
    }
  ]
}
```

### Ordre des Résultats

Villes triées par:
1. **Population** (décroissant)
2. **Rank signal** (si population NULL)
3. **Nom** (alphabétique)

### Frontend Tips

```javascript
// Exemple d'appel
const getTopCities = async (countryCode, limit = 5) => {
  try {
    const response = await fetch(`/top-cities/${countryCode.toUpperCase()}?limit=${limit}`);

    if (!response.ok) {
      if (response.status === 404) {
        return { error: 'Pays non trouvé' };
      }
      throw new Error('Service unavailable');
    }

    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Error fetching top cities:', error);
    return { error: error.message };
  }
};

// Affichage suggéré
cities.map(city => ({
  label: `${city.name} (${(city.population / 1000000).toFixed(1)}M)`,
  coordinates: { lat: city.lat, lon: city.lon }
}));
```

---

## 3. Nearest Airports to City

**Endpoint:** `POST /nearest-airports`

**Usage:** Trouver les aéroports les plus proches d'une ville (avec tolérance aux fautes).

### Request Body

```json
{
  "city": "Paris",
  "limit": 3
}
```

| Field  | Type   | Required | Default | Description |
|--------|--------|----------|---------|-------------|
| `city` | string | ✓        | -       | Nom de la ville (min 2 chars, typos OK!) |
| `limit`| int    | -        | 3       | Nombre d'aéroports (max: 10) |

### Response Example

```json
{
  "city_query": "Pari",
  "matched_city": "Paris",
  "matched_city_id": "3978405a-2f88-40fd-a9d1-1b7c896626ff",
  "match_score": 95,
  "city_location": {
    "lat": 48.8566,
    "lon": 2.3522
  },
  "airports": [
    {
      "iata": "ORY",
      "name": "Paris Orly (ORY)",
      "city_name": "Paris Orly",
      "country_code": "FR",
      "lat": 48.7233,
      "lon": 2.3794,
      "distance_km": 14.3
    },
    {
      "iata": "CDG",
      "name": "Paris Charles de Gaulle (CDG)",
      "city_name": "Paris Charles de Gaulle",
      "country_code": "FR",
      "lat": 49.0097,
      "lon": 2.5479,
      "distance_km": 23.1
    },
    {
      "iata": "BVA",
      "name": "Paris Beauvais (BVA)",
      "city_name": "Paris Beauvais",
      "country_code": "FR",
      "lat": 49.4544,
      "lon": 2.1128,
      "distance_km": 69.2
    }
  ]
}
```

### Match Score

- **100.0** : Correspondance exacte
- **80.0-99.9** : Fuzzy match (fautes de frappe tolérées)
- **< 80.0** : Ville non trouvée (404)

Note: Le score est un nombre décimal entre 0 et 100.

### Error Responses

```json
// 404 - Ville non trouvée
{
  "detail": "No city match found for 'Parisx'. Please check spelling or try a different city name."
}

// 503 - PostgreSQL non configuré
{
  "detail": "Airports service unavailable - PostgreSQL not configured"
}
```

### Frontend Tips

```javascript
// Exemple d'appel
const findNearestAirports = async (cityName) => {
  try {
    const response = await fetch('/nearest-airports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: cityName, limit: 3 })
    });

    if (!response.ok) {
      if (response.status === 404) {
        return { error: 'Ville non trouvée' };
      }
      throw new Error('Service unavailable');
    }

    const data = await response.json();

    // Afficher le match score si < 100 pour informer l'utilisateur
    if (data.match_score < 100) {
      console.log(`Ville corrigée: ${data.city_query} → ${data.matched_city}`);
    }

    return data.airports;

  } catch (error) {
    console.error('Error finding airports:', error);
    return { error: error.message };
  }
};

// Affichage suggéré des aéroports
airports.map(airport => ({
  label: `${airport.name} (${airport.distance_km.toFixed(1)} km)`,
  code: airport.iata,
  distance: airport.distance_km
}));
```

---

## Workflow Recommandé

### Scénario 1: Recherche de ville + aéroports

```
1. User tape "Par" dans un input
   └─> Autocomplete (/autocomplete?q=Par&types=city)
       └─> Affiche: ["Paris, FR", "Paramaribo, SR", "Parma, IT"]

2. User sélectionne "Paris, FR"
   └─> Trouver aéroports (/nearest-airports)
       └─> Body: { city: "Paris", limit: 3 }
       └─> Affiche: ["ORY (14 km)", "CDG (23 km)", "BVA (69 km)"]
```

### Scénario 2: Explorer un pays

```
1. User sélectionne "France" dans une liste de pays
   └─> Top villes (/top-cities/FR?limit=5)
       └─> Affiche: ["Paris (2.1M)", "Marseille (870k)", "Lyon (513k)", ...]

2. User clique sur "Marseille"
   └─> Trouver aéroports (/nearest-airports)
       └─> Body: { city: "Marseille", limit: 3 }
       └─> Affiche: ["MRS (5 km)", ...]
```

---

## Notes Importantes

### Autocomplete
- ✅ Léger et rapide (GET request)
- ✅ Tolérant aux accents (Paris = paris)
- ✅ Résultats vides si < 3 caractères (économise les requêtes)
- ⚠️ Utiliser debounce côté front (300-500ms)

### Top Cities
- ✅ Très rapide (GET request)
- ✅ Code pays insensible à la casse (fr = FR)
- ✅ Retourne le nombre total de villes du pays
- ✅ Limite configurable (1-20 villes)
- ⚠️ Retourne 404 si code pays invalide

### Nearest Airports
- ✅ Tolérant aux fautes (Fuzzy matching 80%+)
- ✅ Distance réelle (PostGIS great circle)
- ✅ Retourne le nom corrigé de la ville
- ⚠️ POST request (body JSON)
- ⚠️ Peut retourner 404 si ville vraiment introuvable

### Performance
- Autocomplete: ~50-100ms (première requête) / ~5-10ms (en cache)
- Top Cities: ~30-80ms (première requête) / ~5-10ms (en cache)
- Nearest Airports: ~100-200ms (première requête) / ~5-10ms (en cache)
- Pas de limite de rate (mais restez raisonnables)

### Cache
- ✅ Cache en mémoire côté serveur pour réduire la charge DB
- ✅ Autocomplete: 10 minutes de cache
- ✅ Top Cities: 30 minutes de cache (les populations changent rarement)
- ✅ Nearest Airports: 15 minutes de cache
- ✅ Nettoyage automatique des entrées expirées toutes les heures
- ⚠️ Les réponses en cache sont quasi-instantanées

---

## Code Complet Exemple (React)

```javascript
import { useState, useCallback } from 'react';
import debounce from 'lodash/debounce';

function AirportFinder() {
  const [suggestions, setSuggestions] = useState([]);
  const [airports, setAirports] = useState([]);

  // Autocomplete avec debounce
  const searchCities = useCallback(
    debounce(async (query) => {
      if (query.length < 3) {
        setSuggestions([]);
        return;
      }

      const res = await fetch(`/autocomplete?q=${query}&types=city&limit=10`);
      const data = await res.json();
      setSuggestions(data.results);
    }, 300),
    []
  );

  // Recherche aéroports
  const findAirports = async (cityName) => {
    const res = await fetch('/nearest-airports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: cityName, limit: 3 })
    });

    if (!res.ok) {
      alert('Ville non trouvée');
      return;
    }

    const data = await res.json();
    setAirports(data.airports);
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Rechercher une ville..."
        onChange={(e) => searchCities(e.target.value)}
      />

      <ul>
        {suggestions.map(city => (
          <li key={city.id} onClick={() => findAirports(city.label.split(',')[0])}>
            {city.label}
          </li>
        ))}
      </ul>

      {airports.length > 0 && (
        <div>
          <h3>Aéroports proches</h3>
          <ul>
            {airports.map(airport => (
              <li key={airport.iata}>
                {airport.name} - {airport.distance_km.toFixed(1)} km
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## Questions Fréquentes

**Q: Faut-il gérer les accents côté front?**
R: Non, l'API est insensible aux accents. `Paris = paris = París`

**Q: Que faire si l'utilisateur tape "Pari" au lieu de "Paris"?**
R: L'endpoint `/nearest-airports` corrigera automatiquement via fuzzy matching (score 95+).

**Q: Combien de résultats autocomplete afficher?**
R: Recommandé: 5-10 résultats max pour UX optimale.

**Q: Que faire si PostgreSQL n'est pas configuré?**
R: Les endpoints retournent 503. Afficher un message "Service temporairement indisponible".

**Q: Comment obtenir les plus grandes villes d'un pays?**
R: Utilisez `/top-cities/{country_code}` avec le code ISO2 du pays (ex: `/top-cities/FR` pour la France).

**Q: Les villes retournées ont-elles toutes une population?**
R: Non, certaines villes peuvent avoir `population: null`. Dans ce cas, le tri utilise `rank_signal` comme fallback.

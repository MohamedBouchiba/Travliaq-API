# Guide d'Intégration Frontend - Travliaq API

Documentation complète pour intégrer l'API Travliaq dans votre application frontend.

**Base URL Production**: `https://travliaq-api-production.up.railway.app`

---

## Table des Matières

1. [Recherche d'Activités](#1-recherche-dactivités)
2. [Détails d'une Activité](#2-détails-dune-activité)
3. [Vérification de Disponibilité](#3-vérification-de-disponibilité)
4. [Recherche de Tags/Catégories](#4-recherche-de-tagscatégories)
5. [Gestion des Erreurs](#5-gestion-des-erreurs)
6. [Exemples d'Intégration Frontend](#6-exemples-dintégration-frontend)
7. [Bonnes Pratiques](#7-bonnes-pratiques)

---

## 1. Recherche d'Activités

### Endpoint
```
POST /api/v1/activities/search
```

### Description
Recherche d'activités selon la localisation, dates, filtres et préférences. Supporte le cache automatique (7 jours).

### Paramètres de Requête

```typescript
interface ActivitySearchRequest {
  location: {
    city: string;              // Nom de la ville (ex: "Paris", "Rome", "Algers")
    country_code: string;      // Code pays ISO 3166-1 alpha-2 (ex: "FR", "IT", "DZ")
    region?: string;           // Optionnel: région (ex: "Île-de-France")
  };

  dates: {
    start: string;             // Date de début (format: "YYYY-MM-DD")
    end?: string;              // Date de fin optionnelle (format: "YYYY-MM-DD")
  };

  filters?: {
    categories?: string[];     // Mots-clés de catégories (ex: ["museum", "food"])
    price_range?: {
      min?: number;            // Prix minimum en devise choisie
      max?: number;            // Prix maximum en devise choisie
    };
    rating_min?: number;       // Note minimum (0-5)
    duration_minutes?: number; // Durée maximale en minutes
  };

  sort?: string;               // Tri: "default", "rating", "price", "duration", "date_added"
  currency?: string;           // Devise: "EUR", "USD", "GBP", etc. (défaut: "EUR")
  language?: string;           // Langue: "en", "fr", "es", etc. (défaut: "en")

  pagination?: {
    page?: number;             // Numéro de page (défaut: 1)
    limit?: number;            // Résultats par page (défaut: 30, max: 100)
  };
}
```

### Exemple de Requête

#### JavaScript/Fetch
```javascript
const searchActivities = async (city, countryCode, startDate, filters = {}) => {
  const response = await fetch('https://travliaq-api-production.up.railway.app/api/v1/activities/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      location: {
        city: city,
        country_code: countryCode,
      },
      dates: {
        start: startDate,
      },
      filters: {
        categories: filters.categories || [],
        price_range: filters.priceRange,
        rating_min: filters.ratingMin,
      },
      currency: 'EUR',
      language: 'fr',
      pagination: {
        page: 1,
        limit: 30,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Erreur API: ${response.status}`);
  }

  return await response.json();
};

// Utilisation
try {
  const results = await searchActivities('Paris', 'FR', '2026-06-15', {
    categories: ['museum', 'food'],
    ratingMin: 4.0,
    priceRange: { min: 20, max: 150 },
  });

  console.log(`Trouvé ${results.results.total_count} activités`);
  results.results.activities.forEach(activity => {
    console.log(`- ${activity.title} (${activity.pricing.from_price}€)`);
  });
} catch (error) {
  console.error('Erreur lors de la recherche:', error);
}
```

#### TypeScript/Axios
```typescript
import axios from 'axios';

interface SearchFilters {
  categories?: string[];
  priceRange?: { min?: number; max?: number };
  ratingMin?: number;
}

const API_BASE_URL = 'https://travliaq-api-production.up.railway.app';

const searchActivities = async (
  city: string,
  countryCode: string,
  startDate: string,
  filters: SearchFilters = {}
) => {
  const { data } = await axios.post(`${API_BASE_URL}/api/v1/activities/search`, {
    location: {
      city,
      country_code: countryCode,
    },
    dates: {
      start: startDate,
    },
    filters: {
      categories: filters.categories || [],
      price_range: filters.priceRange,
      rating_min: filters.ratingMin,
    },
    currency: 'EUR',
    language: 'fr',
    pagination: {
      page: 1,
      limit: 30,
    },
  });

  return data;
};
```

### Réponse

```typescript
interface ActivitySearchResponse {
  success: boolean;
  results: {
    activities: Activity[];      // Liste des activités
    total_count: number;          // Nombre total de résultats
    page: number;                 // Page actuelle
    per_page: number;             // Résultats par page
    has_more: boolean;            // Y a-t-il plus de résultats?
  };
  location_resolution: {
    destination_id: string;       // ID Viator de la destination
    matched_city: string | null;  // Ville matchée en base
  };
  cache_info: {
    cached: boolean;              // Résultat en cache?
    cached_at: string | null;     // Date de mise en cache
    ttl_seconds: number;          // Durée de vie du cache
  };
  request_summary: {
    city: string;
    country_code: string;
    start_date: string;
    categories?: string[];
    price_range?: { min?: number; max?: number };
    rating_min?: number;
  };
}

interface Activity {
  id: string;                     // Code produit Viator
  title: string;                  // Titre de l'activité
  description: string;            // Description complète
  images: {
    url: string;
    is_cover: boolean;
    variants: {
      small?: string;             // 200px
      medium?: string;            // 600px
      large?: string;             // >600px
    };
  }[];
  pricing: {
    from_price: number;           // Prix à partir de
    currency: string;             // Devise
    original_price?: number;      // Prix avant réduction
    is_discounted: boolean;       // En promotion?
  };
  rating: {
    average: number;              // Note moyenne (0-5)
    count: number;                // Nombre d'avis
  };
  duration: {
    minutes: number;              // Durée en minutes
    formatted: string;            // Format lisible (ex: "2h 30min")
  };
  categories: string[];           // Tags de catégories
  flags: string[];                // Badges (ex: "LIKELY_TO_SELL_OUT")
  booking_url: string;            // URL de réservation
  confirmation_type: string;      // Type de confirmation
  location: {
    destination: string;          // Destination
    country: string;              // Pays
  };
  availability: string;           // Disponibilité
}
```

### Exemple de Réponse

```json
{
  "success": true,
  "results": {
    "activities": [
      {
        "id": "3731LOUVRE",
        "title": "Musée du Louvre: Billet coupe-file",
        "description": "Découvrez les chefs-d'œuvre du Louvre...",
        "images": [
          {
            "url": "https://media.viator.com/paris-louvre.jpg",
            "is_cover": true,
            "variants": {
              "small": "https://media.viator.com/paris-louvre-200.jpg",
              "medium": "https://media.viator.com/paris-louvre-600.jpg",
              "large": "https://media.viator.com/paris-louvre-1200.jpg"
            }
          }
        ],
        "pricing": {
          "from_price": 17.0,
          "currency": "EUR",
          "original_price": null,
          "is_discounted": false
        },
        "rating": {
          "average": 4.7,
          "count": 12453
        },
        "duration": {
          "minutes": 120,
          "formatted": "2h"
        },
        "categories": ["tag_21514", "tag_10847"],
        "flags": ["LIKELY_TO_SELL_OUT"],
        "booking_url": "https://www.viator.com/tours/Paris/3731LOUVRE",
        "confirmation_type": "INSTANT",
        "location": {
          "destination": "Paris",
          "country": "France"
        },
        "availability": "available"
      }
    ],
    "total_count": 234,
    "page": 1,
    "per_page": 30,
    "has_more": true
  },
  "location_resolution": {
    "destination_id": "684",
    "matched_city": "Paris"
  },
  "cache_info": {
    "cached": false,
    "cached_at": null,
    "ttl_seconds": 604800
  },
  "request_summary": {
    "city": "Paris",
    "country_code": "FR",
    "start_date": "2026-06-15",
    "categories": ["museum", "food"],
    "rating_min": 4.0
  }
}
```

---

## 2. Détails d'une Activité

### Endpoint
```
GET /api/v1/activities/{product_code}
```

### Description
Récupère les détails complets d'une activité spécifique.

### Paramètres URL
- `product_code`: Code produit Viator (ex: "3731LOUVRE")

### Query Parameters (optionnels)
- `language`: Code langue (défaut: "en")
- `currency`: Code devise (défaut: "EUR")

### Exemple de Requête

```javascript
const getActivityDetails = async (productCode, language = 'fr', currency = 'EUR') => {
  const response = await fetch(
    `https://travliaq-api-production.up.railway.app/api/v1/activities/${productCode}?language=${language}&currency=${currency}`
  );

  if (!response.ok) {
    throw new Error(`Activité non trouvée: ${response.status}`);
  }

  return await response.json();
};

// Utilisation
const details = await getActivityDetails('3731LOUVRE', 'fr', 'EUR');
console.log(details.activity.title);
```

### Réponse

```json
{
  "success": true,
  "activity": {
    "id": "3731LOUVRE",
    "title": "Musée du Louvre: Billet coupe-file",
    "description": "Description complète...",
    "images": [...],
    "pricing": {...},
    "rating": {...},
    "duration": {...},
    "categories": [...],
    "flags": [...],
    "booking_url": "https://www.viator.com/tours/Paris/3731LOUVRE",
    "confirmation_type": "INSTANT",
    "location": {...},
    "availability": "available"
  }
}
```

---

## 3. Vérification de Disponibilité

### Endpoint
```
POST /api/v1/activities/{product_code}/availability
```

### Description
Vérifie la disponibilité d'une activité pour des dates spécifiques.

### Exemple de Requête

```javascript
const checkAvailability = async (productCode, startDate, endDate = null) => {
  const response = await fetch(
    `https://travliaq-api-production.up.railway.app/api/v1/activities/${productCode}/availability`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        start_date: startDate,
        end_date: endDate,
        currency: 'EUR',
      }),
    }
  );

  return await response.json();
};

// Utilisation
const availability = await checkAvailability('3731LOUVRE', '2026-06-15', '2026-06-20');
console.log(`Disponibilités: ${availability.available_dates.length} dates`);
```

---

## 4. Recherche de Tags/Catégories

### Endpoint
```
GET /admin/tags/search
```

### Description
Recherche les tags Viator correspondant à un mot-clé. Utile pour suggérer des catégories à l'utilisateur.

### Query Parameters
- `keyword`: Mot-clé à rechercher (ex: "museum", "food")
- `language`: Langue de recherche (défaut: "en")
- `limit`: Nombre max de résultats (défaut: 20)

### Exemple de Requête

```javascript
const searchTags = async (keyword, language = 'fr') => {
  const response = await fetch(
    `https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=${keyword}&language=${language}`
  );

  return await response.json();
};

// Utilisation - Autocomplete de catégories
const handleCategoryInput = async (userInput) => {
  const tags = await searchTags(userInput, 'fr');

  // Afficher les suggestions
  const suggestions = tags.results.map(tag => ({
    id: tag.tag_id,
    label: tag.tag_name,
    value: userInput, // Garder le keyword original pour la recherche
  }));

  return suggestions;
};

// Exemple: Utilisateur tape "musée"
const suggestions = await handleCategoryInput('musée');
// Retourne: [
//   { id: 21514, label: "Musées", value: "musée" },
//   { id: 11901, label: "Billets pour musées et laissez-passer", value: "musée" },
//   ...
// ]
```

### Réponse

```json
{
  "keyword": "museum",
  "language": "en",
  "count": 5,
  "results": [
    {
      "tag_id": 21514,
      "tag_name": "Museums",
      "parent_tag_id": null,
      "all_names": {
        "en": "Museums",
        "fr": "Musées",
        "es": "Museos",
        "de": "Museen"
      }
    }
  ],
  "tag_ids": [21514, 10847, 11901, 12716, 13109]
}
```

### Liste des Root Tags

```
GET /admin/tags/root
```

Récupère toutes les catégories racines pour construire un menu de filtres.

```javascript
const getRootCategories = async () => {
  const response = await fetch(
    'https://travliaq-api-production.up.railway.app/admin/tags/root'
  );

  const data = await response.json();

  // Créer un menu de catégories
  return data.root_tags.map(tag => ({
    id: tag.tag_id,
    label: tag.all_names.fr || tag.tag_name, // Utiliser la traduction française
  }));
};
```

---

## 5. Gestion des Erreurs

### Codes d'Erreur HTTP

| Code | Signification | Action Frontend |
|------|---------------|-----------------|
| 200 | Succès | Afficher les résultats |
| 400 | Requête invalide | Vérifier les paramètres |
| 404 | Ressource non trouvée | Afficher message d'erreur |
| 500 | Erreur serveur | Réessayer ou afficher message générique |
| 503 | Service indisponible | Viator API non configurée |

### Exemple de Gestion d'Erreurs

```javascript
const searchActivitiesWithErrorHandling = async (params) => {
  try {
    const response = await fetch('https://travliaq-api-production.up.railway.app/api/v1/activities/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    // Erreur HTTP
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      switch (response.status) {
        case 400:
          throw new Error(`Paramètres invalides: ${errorData.detail || 'Vérifiez votre requête'}`);
        case 404:
          throw new Error('Destination non trouvée. Vérifiez le nom de la ville et le code pays.');
        case 503:
          throw new Error('Service temporairement indisponible. Réessayez dans quelques instants.');
        default:
          throw new Error(`Erreur serveur (${response.status})`);
      }
    }

    const data = await response.json();

    // Vérifier si la réponse indique un succès
    if (!data.success) {
      throw new Error(data.message || 'La recherche a échoué');
    }

    // Aucun résultat trouvé
    if (data.results.total_count === 0) {
      return {
        isEmpty: true,
        message: 'Aucune activité trouvée pour ces critères. Essayez d\'élargir votre recherche.',
        data,
      };
    }

    return { isEmpty: false, data };

  } catch (error) {
    // Erreur réseau
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Impossible de se connecter au serveur. Vérifiez votre connexion internet.');
    }

    throw error;
  }
};

// Utilisation dans un composant React
const handleSearch = async () => {
  setLoading(true);
  setError(null);

  try {
    const result = await searchActivitiesWithErrorHandling({
      location: { city: 'Paris', country_code: 'FR' },
      dates: { start: '2026-06-15' },
      filters: { categories: ['museum'] },
    });

    if (result.isEmpty) {
      setError(result.message);
      setActivities([]);
    } else {
      setActivities(result.data.results.activities);
    }
  } catch (error) {
    setError(error.message);
  } finally {
    setLoading(false);
  }
};
```

---

## 6. Exemples d'Intégration Frontend

### React Hook Complet

```typescript
import { useState, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = 'https://travliaq-api-production.up.railway.app';

interface SearchParams {
  city: string;
  countryCode: string;
  startDate: string;
  categories?: string[];
  priceRange?: { min?: number; max?: number };
  ratingMin?: number;
}

export const useActivitiesSearch = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const search = useCallback(async (params: SearchParams, page: number = 1) => {
    setLoading(true);
    setError(null);

    try {
      const { data } = await axios.post(`${API_BASE_URL}/api/v1/activities/search`, {
        location: {
          city: params.city,
          country_code: params.countryCode,
        },
        dates: {
          start: params.startDate,
        },
        filters: {
          categories: params.categories,
          price_range: params.priceRange,
          rating_min: params.ratingMin,
        },
        currency: 'EUR',
        language: 'fr',
        pagination: {
          page,
          limit: 30,
        },
      });

      if (!data.success) {
        throw new Error(data.message || 'Échec de la recherche');
      }

      setActivities(data.results.activities);
      setTotalCount(data.results.total_count);
      setHasMore(data.results.has_more);

      return data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Une erreur est survenue';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    activities,
    loading,
    error,
    totalCount,
    hasMore,
    search,
  };
};

// Utilisation dans un composant
const ActivitiesSearchPage = () => {
  const { activities, loading, error, totalCount, search } = useActivitiesSearch();
  const [filters, setFilters] = useState({
    city: 'Paris',
    countryCode: 'FR',
    startDate: '2026-06-15',
    categories: [],
    ratingMin: 4.0,
  });

  const handleSearch = async () => {
    await search(filters);
  };

  return (
    <div>
      {/* Formulaire de recherche */}
      <button onClick={handleSearch} disabled={loading}>
        {loading ? 'Recherche...' : 'Rechercher'}
      </button>

      {/* Affichage des erreurs */}
      {error && <div className="error">{error}</div>}

      {/* Résultats */}
      {totalCount > 0 && <p>{totalCount} activités trouvées</p>}

      <div className="activities-grid">
        {activities.map(activity => (
          <ActivityCard key={activity.id} activity={activity} />
        ))}
      </div>
    </div>
  );
};
```

### Vue.js Composable

```typescript
import { ref, computed } from 'vue';
import axios from 'axios';

const API_BASE_URL = 'https://travliaq-api-production.up.railway.app';

export const useActivities = () => {
  const activities = ref([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const totalCount = ref(0);

  const searchActivities = async (params: any) => {
    loading.value = true;
    error.value = null;

    try {
      const { data } = await axios.post(`${API_BASE_URL}/api/v1/activities/search`, {
        location: {
          city: params.city,
          country_code: params.countryCode,
        },
        dates: {
          start: params.startDate,
        },
        filters: params.filters,
        currency: 'EUR',
        language: 'fr',
      });

      activities.value = data.results.activities;
      totalCount.value = data.results.total_count;

      return data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    activities,
    loading,
    error,
    totalCount,
    searchActivities,
  };
};
```

### Vanilla JavaScript - Pagination

```javascript
class ActivitiesSearchClient {
  constructor(baseUrl = 'https://travliaq-api-production.up.railway.app') {
    this.baseUrl = baseUrl;
    this.currentPage = 1;
    this.totalPages = 1;
  }

  async search(params, page = 1) {
    const response = await fetch(`${this.baseUrl}/api/v1/activities/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...params,
        pagination: {
          page,
          limit: 30,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Erreur API: ${response.status}`);
    }

    const data = await response.json();

    this.currentPage = page;
    this.totalPages = Math.ceil(data.results.total_count / 30);

    return data;
  }

  async nextPage(params) {
    if (this.currentPage < this.totalPages) {
      return await this.search(params, this.currentPage + 1);
    }
    return null;
  }

  async previousPage(params) {
    if (this.currentPage > 1) {
      return await this.search(params, this.currentPage - 1);
    }
    return null;
  }
}

// Utilisation
const client = new ActivitiesSearchClient();

const searchParams = {
  location: { city: 'Paris', country_code: 'FR' },
  dates: { start: '2026-06-15' },
  filters: { categories: ['museum'] },
  currency: 'EUR',
  language: 'fr',
};

// Première page
const page1 = await client.search(searchParams);
console.log(`Page ${client.currentPage} / ${client.totalPages}`);

// Page suivante
const page2 = await client.nextPage(searchParams);
```

---

## 7. Bonnes Pratiques

### 7.1 Caching Côté Frontend

L'API utilise un cache Redis de 7 jours. Évitez de dupliquer le cache côté frontend pour les mêmes recherches.

```javascript
// ❌ Mauvais - Cache redondant
const cachedSearch = useMemo(() => {
  return searchResults; // L'API cache déjà
}, [searchResults]);

// ✅ Bon - Laissez l'API gérer le cache
const results = await searchActivities(params);
```

### 7.2 Debouncing pour Autocomplete

```javascript
import { debounce } from 'lodash';

const debouncedTagSearch = debounce(async (keyword) => {
  const tags = await fetch(
    `https://travliaq-api-production.up.railway.app/admin/tags/search?keyword=${keyword}&language=fr`
  ).then(r => r.json());

  setSuggestions(tags.results);
}, 300);

// Dans un input
<input
  onChange={(e) => debouncedTagSearch(e.target.value)}
  placeholder="Rechercher une catégorie..."
/>
```

### 7.3 Optimisation des Images

Utilisez les variants d'images selon le contexte:

```javascript
const ActivityCard = ({ activity }) => {
  const coverImage = activity.images.find(img => img.is_cover) || activity.images[0];

  return (
    <div className="activity-card">
      {/* Vignette - petite image */}
      <img
        src={coverImage.variants.small}
        alt={activity.title}
        loading="lazy"
      />

      {/* Page détails - grande image */}
      <img
        src={coverImage.variants.large}
        srcSet={`
          ${coverImage.variants.small} 200w,
          ${coverImage.variants.medium} 600w,
          ${coverImage.variants.large} 1200w
        `}
        sizes="(max-width: 600px) 200px, (max-width: 1200px) 600px, 1200px"
        alt={activity.title}
      />
    </div>
  );
};
```

### 7.4 Validation des Dates

```javascript
const validateSearchDates = (startDate, endDate = null) => {
  const start = new Date(startDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Date de début dans le passé
  if (start < today) {
    throw new Error('La date de début doit être dans le futur');
  }

  // Date de fin avant date de début
  if (endDate) {
    const end = new Date(endDate);
    if (end < start) {
      throw new Error('La date de fin doit être après la date de début');
    }
  }

  return true;
};
```

### 7.5 Gestion des Codes Pays

```javascript
// Utiliser un mapping pour l'UX
const COUNTRY_CODES = {
  'France': 'FR',
  'Italie': 'IT',
  'Espagne': 'ES',
  'Allemagne': 'DE',
  'Royaume-Uni': 'GB',
  'États-Unis': 'US',
  'Algérie': 'DZ',
  'Maroc': 'MA',
  'Tunisie': 'TN',
};

// Composant de sélection
const CountrySelect = ({ onChange }) => {
  return (
    <select onChange={(e) => onChange(e.target.value)}>
      {Object.entries(COUNTRY_CODES).map(([name, code]) => (
        <option key={code} value={code}>
          {name}
        </option>
      ))}
    </select>
  );
};
```

### 7.6 Affichage des Prix

```javascript
const formatPrice = (price, currency) => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency,
  }).format(price);
};

// Utilisation
const PriceDisplay = ({ activity }) => (
  <div className="price">
    {activity.pricing.is_discounted && (
      <span className="original-price">
        {formatPrice(activity.pricing.original_price, activity.pricing.currency)}
      </span>
    )}
    <span className="current-price">
      {formatPrice(activity.pricing.from_price, activity.pricing.currency)}
    </span>
  </div>
);
```

### 7.7 Filtres Réactifs

```javascript
const ActivitiesFilter = () => {
  const [filters, setFilters] = useState({
    categories: [],
    priceRange: { min: 0, max: 500 },
    ratingMin: 0,
  });

  const updateFilter = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  // Auto-search quand les filtres changent
  useEffect(() => {
    const timer = setTimeout(() => {
      search(filters);
    }, 500); // Debounce 500ms

    return () => clearTimeout(timer);
  }, [filters]);

  return (
    <div className="filters">
      {/* Catégories */}
      <CategorySelect
        value={filters.categories}
        onChange={(cats) => updateFilter('categories', cats)}
      />

      {/* Prix */}
      <PriceRangeSlider
        min={filters.priceRange.min}
        max={filters.priceRange.max}
        onChange={(range) => updateFilter('priceRange', range)}
      />

      {/* Note minimum */}
      <RatingFilter
        value={filters.ratingMin}
        onChange={(rating) => updateFilter('ratingMin', rating)}
      />
    </div>
  );
};
```

---

## 8. Exemples Complets d'Interface

### Interface de Recherche Complète (React)

```typescript
import React, { useState } from 'react';
import { useActivitiesSearch } from './hooks/useActivitiesSearch';

const ActivitySearchPage = () => {
  const { activities, loading, error, totalCount, search } = useActivitiesSearch();

  const [searchParams, setSearchParams] = useState({
    city: '',
    countryCode: 'FR',
    startDate: '',
    categories: [],
    priceRange: { min: 0, max: 500 },
    ratingMin: 0,
  });

  const handleSearch = async (e) => {
    e.preventDefault();

    // Validation
    if (!searchParams.city || !searchParams.startDate) {
      alert('Veuillez renseigner une ville et une date');
      return;
    }

    await search(searchParams);
  };

  return (
    <div className="search-page">
      {/* Formulaire de recherche */}
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          placeholder="Ville (ex: Paris, Rome, Alger)"
          value={searchParams.city}
          onChange={(e) => setSearchParams({ ...searchParams, city: e.target.value })}
        />

        <select
          value={searchParams.countryCode}
          onChange={(e) => setSearchParams({ ...searchParams, countryCode: e.target.value })}
        >
          <option value="FR">France</option>
          <option value="IT">Italie</option>
          <option value="ES">Espagne</option>
          <option value="DZ">Algérie</option>
          <option value="MA">Maroc</option>
        </select>

        <input
          type="date"
          value={searchParams.startDate}
          min={new Date().toISOString().split('T')[0]}
          onChange={(e) => setSearchParams({ ...searchParams, startDate: e.target.value })}
        />

        <CategorySelector
          selected={searchParams.categories}
          onChange={(cats) => setSearchParams({ ...searchParams, categories: cats })}
        />

        <button type="submit" disabled={loading}>
          {loading ? 'Recherche...' : 'Rechercher'}
        </button>
      </form>

      {/* Résultats */}
      {error && <div className="error-message">{error}</div>}

      {totalCount > 0 && (
        <div className="results-header">
          <h2>{totalCount} activités trouvées</h2>
        </div>
      )}

      <div className="activities-grid">
        {activities.map(activity => (
          <ActivityCard key={activity.id} activity={activity} />
        ))}
      </div>

      {totalCount === 0 && !loading && !error && (
        <div className="no-results">
          <p>Aucune activité trouvée pour ces critères.</p>
          <p>Essayez d'élargir votre recherche ou de modifier les filtres.</p>
        </div>
      )}
    </div>
  );
};

const ActivityCard = ({ activity }) => {
  const coverImage = activity.images.find(img => img.is_cover) || activity.images[0];

  return (
    <div className="activity-card">
      <img
        src={coverImage?.variants.medium || coverImage?.url}
        alt={activity.title}
        loading="lazy"
      />

      <div className="card-content">
        <h3>{activity.title}</h3>

        <div className="rating">
          {'⭐'.repeat(Math.round(activity.rating.average))}
          <span>{activity.rating.average.toFixed(1)}</span>
          <span>({activity.rating.count} avis)</span>
        </div>

        <p className="duration">{activity.duration.formatted}</p>

        <div className="price">
          {activity.pricing.is_discounted && (
            <span className="original-price">
              {activity.pricing.original_price} {activity.pricing.currency}
            </span>
          )}
          <span className="current-price">
            À partir de {activity.pricing.from_price} {activity.pricing.currency}
          </span>
        </div>

        <a
          href={activity.booking_url}
          target="_blank"
          rel="noopener noreferrer"
          className="book-button"
        >
          Réserver maintenant
        </a>
      </div>
    </div>
  );
};

export default ActivitySearchPage;
```

---

## Support

Pour toute question ou problème:

1. **Documentation API**: [RAILWAY_ADMIN_GUIDE.md](RAILWAY_ADMIN_GUIDE.md)
2. **Guide Viator**: [VIATOR_WRAPPER_README.md](VIATOR_WRAPPER_README.md)
3. **Endpoints Admin**: Utilisez les endpoints `/admin/tags/*` pour diagnostiquer les problèmes

**Base URL**: `https://travliaq-api-production.up.railway.app`

**Dernière mise à jour**: 2026-01-02

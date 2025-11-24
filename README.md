# Travliaq-API

API de normalisation et d'enrichissement des données de voyage.

## Fonctionnalités

- Récupération des données depuis Supabase PostgreSQL
- Normalisation et validation contre le schéma JSON officiel (draft-07)
- Génération de fichiers enrichis (`out/<id>/enrich.json`)

## Installation Locale

1. Créer un environnement virtuel :
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurer l'environnement :
   Copier `.env.example` vers `.env` et configurer la connexion PostgreSQL.

4. Lancer l'API :
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Déploiement (Docker / Railway)

### Docker

Construire l'image :
```bash
docker build -t travliaq-api .
```

Lancer le conteneur :
```bash
docker run -p 8000:8000 --env-file .env travliaq-api
```

### Variables d'Environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `PG_CONN` | Chaîne de connexion PostgreSQL | `postgresql://user:pass@host:port/db` |

### Documentation API

Une fois lancé, la documentation interactive est disponible sur :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

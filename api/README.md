# API GMAO - Gestion de Stock

Cette API FastAPI fournit un système complet de gestion de stock pour le système GMAO.

## Fonctionnalités

-   **Gestion des catégories** : CRUD complet pour les catégories de produits
-   **Gestion des fournisseurs** : CRUD complet pour les fournisseurs
-   **Gestion des produits** : CRUD complet avec recherche et gestion des références
-   **Gestion des mouvements de stock** : Entrées, sorties et ajustements automatiques
-   **Suivi du stock en temps réel** : Stock actuel avec historique des mouvements
-   **Alertes de stock faible** : Identification des produits en rupture

## Structure de la base de données

### Tables principales

1. **categories** : Catégories de produits
2. **fournisseurs** : Informations des fournisseurs
3. **produits** : Catalogue des produits avec références
4. **mouvements_stock** : Historique de tous les mouvements
5. **stock_actuel** : État actuel du stock (mise à jour automatique)

### Relations

-   Un produit appartient à une catégorie (optionnel)
-   Un produit a un fournisseur (optionnel)
-   Chaque mouvement de stock est lié à un produit
-   Le stock actuel est automatiquement calculé via des triggers

## Endpoints principaux

### Catégories

-   `GET /categories/` - Liste des catégories
-   `POST /categories/` - Créer une catégorie
-   `GET /categories/{id}` - Détails d'une catégorie
-   `PUT /categories/{id}` - Modifier une catégorie
-   `DELETE /categories/{id}` - Supprimer une catégorie

### Fournisseurs

-   `GET /fournisseurs/` - Liste des fournisseurs
-   `POST /fournisseurs/` - Créer un fournisseur
-   `GET /fournisseurs/{id}` - Détails d'un fournisseur
-   `PUT /fournisseurs/{id}` - Modifier un fournisseur
-   `DELETE /fournisseurs/{id}` - Supprimer un fournisseur

### Produits

-   `GET /produits/` - Liste des produits (avec recherche)
-   `POST /produits/` - Créer un produit
-   `GET /produits/{id}` - Détails d'un produit
-   `PUT /produits/{id}` - Modifier un produit
-   `DELETE /produits/{id}` - Supprimer un produit

### Mouvements de stock

-   `GET /mouvements-stock/` - Historique des mouvements
-   `POST /mouvements-stock/` - Créer un mouvement (entrée/sortie/ajustement)
-   `GET /mouvements-stock/{id}` - Détails d'un mouvement

### Stock

-   `GET /stock/` - État du stock de tous les produits
-   `GET /stock/{produit_id}` - Stock d'un produit spécifique
-   `GET /produits-avec-stock/` - Produits avec leur stock actuel

## Types de mouvements

1. **ENTREE** : Ajout de stock (réception, retour)
2. **SORTIE** : Diminution de stock (consommation, vente)
3. **AJUSTEMENT** : Correction du stock (inventaire)

## Démarrage

### Avec Docker Compose

```bash
# Démarrer tous les services
docker-compose up -d

# L'API sera disponible sur http://localhost:8000
# La documentation interactive sur http://localhost:8000/docs
```

### Variables d'environnement

-   `DATABASE_URL` : URL de connexion PostgreSQL
-   `PYTHONUNBUFFERED` : Sortie Python non bufferisée

## Documentation

-   **Swagger UI** : http://localhost:8000/docs
-   **ReDoc** : http://localhost:8000/redoc
-   **OpenAPI JSON** : http://localhost:8000/openapi.json

## Exemples d'utilisation

### Créer une catégorie

```bash
curl -X POST "http://localhost:8000/categories/" \
  -H "Content-Type: application/json" \
  -d '{"nom": "Électronique", "description": "Composants électroniques"}'
```

### Créer un produit

```bash
curl -X POST "http://localhost:8000/produits/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Résistance 10K",
    "reference": "RES-10K-001",
    "description": "Résistance 10 kOhm 1/4W",
    "categorie_id": 1,
    "prix_unitaire": 0.15,
    "stock_min": 100,
    "stock_max": 1000,
    "unite": "pièce"
  }'
```

### Ajouter du stock (entrée)

```bash
curl -X POST "http://localhost:8000/mouvements-stock/" \
  -H "Content-Type: application/json" \
  -d '{
    "produit_id": 1,
    "type_mouvement": "ENTREE",
    "quantite": 500,
    "motif": "Réception commande",
    "reference_document": "BON-001",
    "created_by": "admin"
  }'
```

### Consommer du stock (sortie)

```bash
curl -X POST "http://localhost:8000/mouvements-stock/" \
  -H "Content-Type: application/json" \
  -d '{
    "produit_id": 1,
    "type_mouvement": "SORTIE",
    "quantite": 50,
    "motif": "Maintenance équipement A",
    "created_by": "technicien"
  }'
```

## Sécurité

⚠️ **Important** : Cette version est une base de développement. Pour la production :

1. Ajouter l'authentification et l'autorisation
2. Configurer CORS avec des domaines spécifiques
3. Utiliser HTTPS
4. Ajouter la validation et la sanitisation des données
5. Implémenter la limitation de taux (rate limiting)
6. Configurer les logs et le monitoring

## Technologies utilisées

-   **FastAPI** : Framework web moderne et rapide
-   **SQLAlchemy** : ORM Python
-   **PostgreSQL** : Base de données relationnelle
-   **Pydantic** : Validation des données
-   **Uvicorn** : Serveur ASGI

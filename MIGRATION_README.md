# 🔄 Migration Excel vers API PostgreSQL - GMAO

Ce document explique la migration atomique du système GMAO depuis le stockage Excel vers une API FastAPI avec base de données PostgreSQL.

## 📋 Vue d'ensemble

La migration remplace progressivement les fonctions de stockage Excel par des appels API, tout en conservant un système de fallback pour assurer la continuité de service.

### ✨ Fonctionnalités migrées

-   ✅ **Gestion des produits (inventaire)**

    -   Chargement depuis l'API avec fallback Excel
    -   Sauvegarde via l'API avec fallback Excel
    -   Recherche et filtrage
    -   Import/export en masse

-   ✅ **Gestion des fournisseurs**

    -   CRUD complet via API
    -   Migration des données existantes
    -   Fallback Excel automatique

-   ✅ **Gestion des emplacements**

    -   CRUD complet via API
    -   Migration des données existantes
    -   Fallback Excel automatique

-   ✅ **Gestion des demandes**

    -   Création et suivi via API
    -   Migration des demandes existantes
    -   Fallback Excel automatique

-   ✅ **Historique des mouvements**
    -   Enregistrement via API
    -   Migration de l'historique existant
    -   Fallback Excel automatique

## 🚀 Démarrage rapide

### 1. Démarrer la base de données PostgreSQL

```bash
# Démarrer PostgreSQL avec Docker Compose
docker-compose up -d postgres
```

### 2. Démarrer l'API FastAPI

```bash
# Option 1: Script automatique
python start_api.py

# Option 2: Manuel
cd api
uvicorn main:app --host 0.0.0.0 --port 8010 --reload
```

### 3. Vérifier le fonctionnement

-   API: http://localhost:8010
-   Documentation: http://localhost:8010/docs
-   Interface de test: http://localhost:8010/redoc

### 4. Lancer l'application Streamlit

```bash
streamlit run app.py
```

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Base de données PostgreSQL
POSTGRES_DB=gmao_db
POSTGRES_USER=gmao_user
POSTGRES_PASSWORD=gmao_password
POSTGRES_PORT=5432

# API
API_BASE_URL=http://localhost:8010
```

### Structure de la base de données

La base de données PostgreSQL contient les tables suivantes :

-   `inventaire` - Produits en stock
-   `fournisseurs` - Informations des fournisseurs
-   `emplacements` - Emplacements de stockage
-   `demandes` - Demandes de matériel
-   `historique` - Historique des mouvements
-   `tables_atelier` - Tables d'atelier
-   `listes_inventaire` - Listes d'inventaire
-   `produits_listes_inventaire` - Produits dans les listes

## 📊 Migration des données

### Migration automatique

L'application détecte automatiquement si l'API est disponible et migre les données :

```python
from migration_utils import migrer_excel_vers_api

# Migrer toutes les données Excel vers l'API
migrer_excel_vers_api()
```

### Migration manuelle

Pour migrer des données spécifiques :

```python
from migration_utils import (
    migrer_inventaire_excel,
    migrer_fournisseurs_excel,
    migrer_emplacements_excel,
    migrer_demandes_excel,
    migrer_historique_excel
)

# Migrer l'inventaire uniquement
migrer_inventaire_excel()
```

### Import en masse

Pour importer de nouveaux produits depuis un fichier Excel :

```python
from migration_utils import importer_produits_en_masse

# Dans Streamlit
uploaded_file = st.file_uploader("Choisir un fichier Excel", type=['xlsx'])
if uploaded_file:
    importer_produits_en_masse(uploaded_file)
```

## 🔄 Système de fallback

Le système implémente un fallback automatique vers Excel si l'API n'est pas disponible :

### Fonctionnement

1. **Test de connexion** : Chaque fonction teste d'abord la connexion à l'API
2. **Utilisation API** : Si disponible, utilise l'API pour les opérations
3. **Fallback Excel** : Si l'API n'est pas disponible, utilise les fichiers Excel
4. **Messages informatifs** : L'utilisateur est informé du mode utilisé

### Exemple de fonction migrée

```python
def load_data():
    """Charge les données depuis l'API ou Excel en fallback"""
    try:
        if api_client.test_connection():
            st.info("🔗 Chargement depuis l'API")
            return api_client.get_inventaire()
    except Exception as e:
        st.warning(f"⚠️ Erreur API: {str(e)}")

    # Fallback vers Excel
    st.info("📂 Chargement depuis Excel (mode fallback)")
    return load_data_from_excel()
```

## 🛠️ Développement

### Structure des fichiers

```
GMAO/
├── app.py                 # Application Streamlit principale (migrée)
├── api_client.py          # Client pour l'API FastAPI
├── migration_utils.py     # Utilitaires de migration
├── start_api.py          # Script de démarrage de l'API
├── docker-compose.yml    # Configuration Docker
├── api/                  # API FastAPI
│   ├── main.py          # Points d'entrée API
│   ├── models.py        # Modèles SQLAlchemy
│   ├── schemas.py       # Schémas Pydantic
│   ├── crud.py          # Opérations CRUD
│   ├── database.py      # Configuration base de données
│   └── requirements.txt # Dépendances API
└── data/                # Fichiers Excel (fallback)
    ├── inventaire_avec_references.xlsx
    ├── fournisseurs.xlsx
    ├── emplacements.xlsx
    ├── demandes.xlsx
    └── historique.xlsx
```

### API Endpoints

#### Inventaire

-   `GET /inventaire/` - Liste tous les produits
-   `POST /inventaire/` - Crée un nouveau produit
-   `GET /inventaire/{id}` - Récupère un produit par ID
-   `PUT /inventaire/{id}` - Met à jour un produit
-   `DELETE /inventaire/{id}` - Supprime un produit
-   `GET /inventaire/search/?search=term` - Recherche de produits

#### Fournisseurs

-   `GET /fournisseurs/` - Liste tous les fournisseurs
-   `POST /fournisseurs/` - Crée un nouveau fournisseur
-   `GET /fournisseurs/{id}` - Récupère un fournisseur par ID
-   `PUT /fournisseurs/{id}` - Met à jour un fournisseur
-   `DELETE /fournisseurs/{id}` - Supprime un fournisseur

#### Emplacements

-   `GET /emplacements/` - Liste tous les emplacements
-   `POST /emplacements/` - Crée un nouvel emplacement
-   `GET /emplacements/{id}` - Récupère un emplacement par ID
-   `PUT /emplacements/{id}` - Met à jour un emplacement
-   `DELETE /emplacements/{id}` - Supprime un emplacement

#### Demandes

-   `GET /demandes/` - Liste toutes les demandes
-   `POST /demandes/` - Crée une nouvelle demande
-   `GET /demandes/{id}` - Récupère une demande par ID
-   `PUT /demandes/{id}` - Met à jour une demande

#### Historique

-   `GET /historique/` - Liste l'historique des mouvements
-   `POST /mouvements-stock/` - Enregistre un mouvement de stock

## 🔍 Tests et validation

### Test de l'API

```bash
# Test de santé
curl http://localhost:8010/health

# Test des produits
curl http://localhost:8010/inventaire/

# Test de recherche
curl "http://localhost:8010/inventaire/search/?search=vis"
```

### Test de l'application

1. Démarrer l'API : `python start_api.py`
2. Lancer Streamlit : `streamlit run app.py`
3. Vérifier que les données se chargent depuis l'API
4. Arrêter l'API et vérifier le fallback Excel

## 📈 Avantages de la migration

### Performance

-   ✅ Accès concurrent aux données
-   ✅ Requêtes optimisées avec index
-   ✅ Pagination pour les gros volumes

### Fiabilité

-   ✅ Transactions ACID
-   ✅ Contraintes d'intégrité
-   ✅ Sauvegarde automatique

### Évolutivité

-   ✅ API REST standard
-   ✅ Documentation automatique
-   ✅ Facilité d'intégration

### Maintenance

-   ✅ Logs centralisés
-   ✅ Monitoring des performances
-   ✅ Déploiement containerisé

## 🚨 Dépannage

### L'API ne démarre pas

1. Vérifier PostgreSQL : `docker-compose ps`
2. Vérifier les dépendances : `pip install -r api/requirements.txt`
3. Vérifier les logs : `docker-compose logs postgres`

### Erreurs de connexion

1. Vérifier l'URL de l'API dans `api_client.py`
2. Vérifier les variables d'environnement
3. Tester la connexion : `curl http://localhost:8010/health`

### Données manquantes

1. Vérifier la migration : utiliser `migration_utils.py`
2. Vérifier les fichiers Excel dans le dossier `data/`
3. Consulter les logs de l'application

## 📞 Support

Pour toute question ou problème :

1. Consulter les logs de l'API
2. Vérifier la documentation : http://localhost:8010/docs
3. Tester les endpoints individuellement
4. Utiliser le mode fallback Excel en cas de problème critique

---

**Note** : Cette migration est conçue pour être progressive et réversible. Le système peut fonctionner en mode hybride (API + Excel) pendant la période de transition.

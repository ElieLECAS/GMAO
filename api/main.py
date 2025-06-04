from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import models
import schemas
from database import SessionLocal, engine, get_db

# Créer les tables
models.Base.metadata.create_all(bind=engine)

# Initialiser FastAPI
app = FastAPI(
    title="GMAO - API de Gestion de Stock",
    description="API pour la gestion de stock dans le système GMAO",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes pour les catégories
@app.get("/categories/", response_model=List[schemas.Categorie])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les catégories"""
    categories = crud.get_categories(db, skip=skip, limit=limit)
    return categories

@app.post("/categories/", response_model=schemas.Categorie)
def create_categorie(categorie: schemas.CategorieCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle catégorie"""
    return crud.create_categorie(db=db, categorie=categorie)

@app.get("/categories/{categorie_id}", response_model=schemas.Categorie)
def read_categorie(categorie_id: int, db: Session = Depends(get_db)):
    """Récupérer une catégorie par ID"""
    db_categorie = crud.get_categorie(db, categorie_id=categorie_id)
    if db_categorie is None:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return db_categorie

@app.put("/categories/{categorie_id}", response_model=schemas.Categorie)
def update_categorie(categorie_id: int, categorie: schemas.CategorieUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une catégorie"""
    db_categorie = crud.update_categorie(db, categorie_id=categorie_id, categorie=categorie)
    if db_categorie is None:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return db_categorie

@app.delete("/categories/{categorie_id}")
def delete_categorie(categorie_id: int, db: Session = Depends(get_db)):
    """Supprimer une catégorie"""
    db_categorie = crud.delete_categorie(db, categorie_id=categorie_id)
    if db_categorie is None:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return {"message": "Catégorie supprimée avec succès"}

# Routes pour les fournisseurs
@app.get("/fournisseurs/", response_model=List[schemas.Fournisseur])
def read_fournisseurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les fournisseurs"""
    fournisseurs = crud.get_fournisseurs(db, skip=skip, limit=limit)
    return fournisseurs

@app.post("/fournisseurs/", response_model=schemas.Fournisseur)
def create_fournisseur(fournisseur: schemas.FournisseurCreate, db: Session = Depends(get_db)):
    """Créer un nouveau fournisseur"""
    return crud.create_fournisseur(db=db, fournisseur=fournisseur)

@app.get("/fournisseurs/{fournisseur_id}", response_model=schemas.Fournisseur)
def read_fournisseur(fournisseur_id: int, db: Session = Depends(get_db)):
    """Récupérer un fournisseur par ID"""
    db_fournisseur = crud.get_fournisseur(db, fournisseur_id=fournisseur_id)
    if db_fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return db_fournisseur

@app.put("/fournisseurs/{fournisseur_id}", response_model=schemas.Fournisseur)
def update_fournisseur(fournisseur_id: int, fournisseur: schemas.FournisseurUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un fournisseur"""
    db_fournisseur = crud.update_fournisseur(db, fournisseur_id=fournisseur_id, fournisseur=fournisseur)
    if db_fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return db_fournisseur

@app.delete("/fournisseurs/{fournisseur_id}")
def delete_fournisseur(fournisseur_id: int, db: Session = Depends(get_db)):
    """Supprimer un fournisseur"""
    db_fournisseur = crud.delete_fournisseur(db, fournisseur_id=fournisseur_id)
    if db_fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return {"message": "Fournisseur supprimé avec succès"}

# Routes pour les produits
@app.get("/produits/", response_model=List[schemas.Produit])
def read_produits(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = Query(None, description="Recherche par nom, référence ou description"),
    db: Session = Depends(get_db)
):
    """Récupérer tous les produits avec recherche optionnelle"""
    produits = crud.get_produits(db, skip=skip, limit=limit, search=search)
    return produits

@app.post("/produits/", response_model=schemas.Produit)
def create_produit(produit: schemas.ProduitCreate, db: Session = Depends(get_db)):
    """Créer un nouveau produit"""
    # Vérifier si la référence existe déjà
    if produit.reference:
        db_produit = crud.get_produit_by_reference(db, reference=produit.reference)
        if db_produit:
            raise HTTPException(status_code=400, detail="Un produit avec cette référence existe déjà")
    
    return crud.create_produit(db=db, produit=produit)

@app.get("/produits/{produit_id}", response_model=schemas.Produit)
def read_produit(produit_id: int, db: Session = Depends(get_db)):
    """Récupérer un produit par ID"""
    db_produit = crud.get_produit(db, produit_id=produit_id)
    if db_produit is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return db_produit

@app.put("/produits/{produit_id}", response_model=schemas.Produit)
def update_produit(produit_id: int, produit: schemas.ProduitUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un produit"""
    db_produit = crud.update_produit(db, produit_id=produit_id, produit=produit)
    if db_produit is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return db_produit

@app.delete("/produits/{produit_id}")
def delete_produit(produit_id: int, db: Session = Depends(get_db)):
    """Supprimer un produit"""
    db_produit = crud.delete_produit(db, produit_id=produit_id)
    if db_produit is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"message": "Produit supprimé avec succès"}

# Routes pour les mouvements de stock
@app.get("/mouvements-stock/", response_model=List[schemas.MouvementStock])
def read_mouvements_stock(
    skip: int = 0, 
    limit: int = 100, 
    produit_id: Optional[int] = Query(None, description="Filtrer par produit"),
    db: Session = Depends(get_db)
):
    """Récupérer tous les mouvements de stock"""
    mouvements = crud.get_mouvements_stock(db, skip=skip, limit=limit, produit_id=produit_id)
    return mouvements

@app.post("/mouvements-stock/", response_model=schemas.MouvementStock)
def create_mouvement_stock(mouvement: schemas.MouvementStockCreate, db: Session = Depends(get_db)):
    """Créer un nouveau mouvement de stock"""
    try:
        return crud.create_mouvement_stock(db=db, mouvement=mouvement)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/mouvements-stock/{mouvement_id}", response_model=schemas.MouvementStock)
def read_mouvement_stock(mouvement_id: int, db: Session = Depends(get_db)):
    """Récupérer un mouvement de stock par ID"""
    db_mouvement = crud.get_mouvement_stock(db, mouvement_id=mouvement_id)
    if db_mouvement is None:
        raise HTTPException(status_code=404, detail="Mouvement de stock non trouvé")
    return db_mouvement

# Routes pour le stock actuel
@app.get("/stock/", response_model=List[schemas.StockActuel])
def read_stocks_actuels(
    skip: int = 0, 
    limit: int = 100, 
    stock_faible: bool = Query(False, description="Afficher seulement les stocks faibles"),
    db: Session = Depends(get_db)
):
    """Récupérer tous les stocks actuels"""
    stocks = crud.get_stocks_actuels(db, skip=skip, limit=limit, stock_faible=stock_faible)
    return stocks

@app.get("/stock/{produit_id}", response_model=schemas.StockActuel)
def read_stock_actuel(produit_id: int, db: Session = Depends(get_db)):
    """Récupérer le stock actuel d'un produit"""
    db_stock = crud.get_stock_actuel(db, produit_id=produit_id)
    if db_stock is None:
        raise HTTPException(status_code=404, detail="Stock non trouvé pour ce produit")
    return db_stock

# Routes spécialisées
@app.get("/produits-avec-stock/", response_model=List[schemas.ProduitAvecStock])
def read_produits_avec_stock(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = Query(None, description="Recherche par nom, référence ou description"),
    db: Session = Depends(get_db)
):
    """Récupérer tous les produits avec leur stock actuel"""
    produits = crud.get_produits_avec_stock(db, skip=skip, limit=limit, search=search)
    
    # Transformer les données pour inclure le stock actuel
    result = []
    for produit in produits:
        produit_data = {
            "id": produit.id,
            "nom": produit.nom,
            "description": produit.description,
            "reference": produit.reference,
            "code_barre": produit.code_barre,
            "prix_unitaire": produit.prix_unitaire,
            "stock_min": produit.stock_min,
            "stock_max": produit.stock_max,
            "unite": produit.unite,
            "categorie": produit.categorie,
            "fournisseur": produit.fournisseur,
            "stock_actuel": produit.stock.quantite_disponible if produit.stock else 0,
            "derniere_entree": produit.stock.derniere_entree if produit.stock else None,
            "derniere_sortie": produit.stock.derniere_sortie if produit.stock else None
        }
        result.append(produit_data)
    
    return result

# Route de santé
@app.get("/health")
def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "OK", "message": "API GMAO - Gestion de Stock opérationnelle"}

# Route racine
@app.get("/")
def read_root():
    """Page d'accueil de l'API"""
    return {
        "message": "Bienvenue sur l'API GMAO - Gestion de Stock",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "categories": "/categories/",
            "fournisseurs": "/fournisseurs/",
            "produits": "/produits/",
            "mouvements_stock": "/mouvements-stock/",
            "stock": "/stock/",
            "produits_avec_stock": "/produits-avec-stock/"
        }
    } 
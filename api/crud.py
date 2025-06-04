from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from typing import List, Optional
import models
import schemas

# CRUD pour Catégories
def get_categorie(db: Session, categorie_id: int):
    return db.query(models.Categorie).filter(models.Categorie.id == categorie_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categorie).offset(skip).limit(limit).all()

def create_categorie(db: Session, categorie: schemas.CategorieCreate):
    db_categorie = models.Categorie(**categorie.model_dump())
    db.add(db_categorie)
    db.commit()
    db.refresh(db_categorie)
    return db_categorie

def update_categorie(db: Session, categorie_id: int, categorie: schemas.CategorieUpdate):
    db_categorie = get_categorie(db, categorie_id)
    if db_categorie:
        update_data = categorie.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_categorie, field, value)
        db.commit()
        db.refresh(db_categorie)
    return db_categorie

def delete_categorie(db: Session, categorie_id: int):
    db_categorie = get_categorie(db, categorie_id)
    if db_categorie:
        db.delete(db_categorie)
        db.commit()
    return db_categorie

# CRUD pour Fournisseurs
def get_fournisseur(db: Session, fournisseur_id: int):
    return db.query(models.Fournisseur).filter(models.Fournisseur.id == fournisseur_id).first()

def get_fournisseurs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Fournisseur).offset(skip).limit(limit).all()

def create_fournisseur(db: Session, fournisseur: schemas.FournisseurCreate):
    db_fournisseur = models.Fournisseur(**fournisseur.model_dump())
    db.add(db_fournisseur)
    db.commit()
    db.refresh(db_fournisseur)
    return db_fournisseur

def update_fournisseur(db: Session, fournisseur_id: int, fournisseur: schemas.FournisseurUpdate):
    db_fournisseur = get_fournisseur(db, fournisseur_id)
    if db_fournisseur:
        update_data = fournisseur.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_fournisseur, field, value)
        db.commit()
        db.refresh(db_fournisseur)
    return db_fournisseur

def delete_fournisseur(db: Session, fournisseur_id: int):
    db_fournisseur = get_fournisseur(db, fournisseur_id)
    if db_fournisseur:
        db.delete(db_fournisseur)
        db.commit()
    return db_fournisseur

# CRUD pour Produits
def get_produit(db: Session, produit_id: int):
    return db.query(models.Produit).options(
        joinedload(models.Produit.categorie),
        joinedload(models.Produit.fournisseur),
        joinedload(models.Produit.stock)
    ).filter(models.Produit.id == produit_id).first()

def get_produits(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(models.Produit).options(
        joinedload(models.Produit.categorie),
        joinedload(models.Produit.fournisseur),
        joinedload(models.Produit.stock)
    )
    
    if search:
        query = query.filter(
            or_(
                models.Produit.nom.ilike(f"%{search}%"),
                models.Produit.reference.ilike(f"%{search}%"),
                models.Produit.description.ilike(f"%{search}%")
            )
        )
    
    return query.offset(skip).limit(limit).all()

def get_produit_by_reference(db: Session, reference: str):
    return db.query(models.Produit).filter(models.Produit.reference == reference).first()

def create_produit(db: Session, produit: schemas.ProduitCreate):
    db_produit = models.Produit(**produit.model_dump())
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    
    # Créer l'entrée de stock initial
    db_stock = models.StockActuel(produit_id=db_produit.id, quantite_disponible=0)
    db.add(db_stock)
    db.commit()
    
    return db_produit

def update_produit(db: Session, produit_id: int, produit: schemas.ProduitUpdate):
    db_produit = get_produit(db, produit_id)
    if db_produit:
        update_data = produit.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_produit, field, value)
        db.commit()
        db.refresh(db_produit)
    return db_produit

def delete_produit(db: Session, produit_id: int):
    db_produit = get_produit(db, produit_id)
    if db_produit:
        db.delete(db_produit)
        db.commit()
    return db_produit

# CRUD pour Mouvements de Stock
def get_mouvement_stock(db: Session, mouvement_id: int):
    return db.query(models.MouvementStock).options(
        joinedload(models.MouvementStock.produit)
    ).filter(models.MouvementStock.id == mouvement_id).first()

def get_mouvements_stock(db: Session, skip: int = 0, limit: int = 100, produit_id: Optional[int] = None):
    query = db.query(models.MouvementStock).options(
        joinedload(models.MouvementStock.produit)
    ).order_by(desc(models.MouvementStock.created_at))
    
    if produit_id:
        query = query.filter(models.MouvementStock.produit_id == produit_id)
    
    return query.offset(skip).limit(limit).all()

def create_mouvement_stock(db: Session, mouvement: schemas.MouvementStockCreate):
    # Récupérer le stock actuel
    stock_actuel = db.query(models.StockActuel).filter(
        models.StockActuel.produit_id == mouvement.produit_id
    ).first()
    
    if not stock_actuel:
        # Créer le stock s'il n'existe pas
        stock_actuel = models.StockActuel(produit_id=mouvement.produit_id, quantite_disponible=0)
        db.add(stock_actuel)
        db.commit()
        db.refresh(stock_actuel)
    
    stock_avant = stock_actuel.quantite_disponible
    
    # Calculer le nouveau stock
    if mouvement.type_mouvement == "ENTREE":
        stock_apres = stock_avant + mouvement.quantite
    elif mouvement.type_mouvement == "SORTIE":
        stock_apres = stock_avant - mouvement.quantite
        if stock_apres < 0:
            raise ValueError("Stock insuffisant pour cette sortie")
    else:  # AJUSTEMENT
        stock_apres = mouvement.quantite
    
    # Créer le mouvement
    db_mouvement = models.MouvementStock(
        **mouvement.model_dump(),
        stock_avant=stock_avant,
        stock_apres=stock_apres
    )
    db.add(db_mouvement)
    db.commit()
    db.refresh(db_mouvement)
    
    return db_mouvement

# CRUD pour Stock Actuel
def get_stock_actuel(db: Session, produit_id: int):
    return db.query(models.StockActuel).options(
        joinedload(models.StockActuel.produit)
    ).filter(models.StockActuel.produit_id == produit_id).first()

def get_stocks_actuels(db: Session, skip: int = 0, limit: int = 100, stock_faible: bool = False):
    query = db.query(models.StockActuel).options(
        joinedload(models.StockActuel.produit).joinedload(models.Produit.categorie),
        joinedload(models.StockActuel.produit).joinedload(models.Produit.fournisseur)
    )
    
    if stock_faible:
        query = query.join(models.Produit).filter(
            models.StockActuel.quantite_disponible <= models.Produit.stock_min
        )
    
    return query.offset(skip).limit(limit).all()

def get_produits_avec_stock(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    """Récupère les produits avec leur stock actuel"""
    query = db.query(models.Produit).options(
        joinedload(models.Produit.categorie),
        joinedload(models.Produit.fournisseur),
        joinedload(models.Produit.stock)
    )
    
    if search:
        query = query.filter(
            or_(
                models.Produit.nom.ilike(f"%{search}%"),
                models.Produit.reference.ilike(f"%{search}%"),
                models.Produit.description.ilike(f"%{search}%")
            )
        )
    
    return query.offset(skip).limit(limit).all() 
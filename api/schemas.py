from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class TypeMouvement(str, Enum):
    ENTREE = "ENTREE"
    SORTIE = "SORTIE"
    AJUSTEMENT = "AJUSTEMENT"

# Schémas pour Categorie
class CategorieBase(BaseModel):
    nom: str
    description: Optional[str] = None

class CategorieCreate(CategorieBase):
    pass

class CategorieUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None

class Categorie(CategorieBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime

# Schémas pour Fournisseur
class FournisseurBase(BaseModel):
    nom: str
    contact: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None

class FournisseurCreate(FournisseurBase):
    pass

class FournisseurUpdate(BaseModel):
    nom: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None

class Fournisseur(FournisseurBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime

# Schémas pour Produit
class ProduitBase(BaseModel):
    nom: str
    description: Optional[str] = None
    reference: Optional[str] = None
    code_barre: Optional[str] = None
    categorie_id: Optional[int] = None
    fournisseur_id: Optional[int] = None
    prix_unitaire: Optional[Decimal] = None
    stock_min: int = 0
    stock_max: int = 1000
    unite: str = "pièce"

class ProduitCreate(ProduitBase):
    pass

class ProduitUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    code_barre: Optional[str] = None
    categorie_id: Optional[int] = None
    fournisseur_id: Optional[int] = None
    prix_unitaire: Optional[Decimal] = None
    stock_min: Optional[int] = None
    stock_max: Optional[int] = None
    unite: Optional[str] = None

class Produit(ProduitBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    categorie: Optional[Categorie] = None
    fournisseur: Optional[Fournisseur] = None

# Schémas pour MouvementStock
class MouvementStockBase(BaseModel):
    produit_id: int
    type_mouvement: TypeMouvement
    quantite: int
    motif: Optional[str] = None
    reference_document: Optional[str] = None
    created_by: Optional[str] = None

class MouvementStockCreate(MouvementStockBase):
    pass

class MouvementStock(MouvementStockBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    stock_avant: int
    stock_apres: int
    created_at: datetime
    produit: Optional[Produit] = None

# Schémas pour StockActuel
class StockActuel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    produit_id: int
    quantite_disponible: int
    derniere_entree: Optional[datetime] = None
    derniere_sortie: Optional[datetime] = None
    updated_at: datetime
    produit: Optional[Produit] = None

# Schémas pour les réponses avec pagination
class PaginatedResponse(BaseModel):
    items: List[BaseModel]
    total: int
    page: int
    size: int
    pages: int

# Schémas spécialisés pour les vues avec stock
class ProduitAvecStock(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nom: str
    description: Optional[str] = None
    reference: Optional[str] = None
    code_barre: Optional[str] = None
    prix_unitaire: Optional[Decimal] = None
    stock_min: int
    stock_max: int
    unite: str
    categorie: Optional[Categorie] = None
    fournisseur: Optional[Fournisseur] = None
    stock_actuel: Optional[int] = None
    derniere_entree: Optional[datetime] = None
    derniere_sortie: Optional[datetime] = None 
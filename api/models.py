from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Categorie(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    produits = relationship("Produit", back_populates="categorie")

class Fournisseur(Base):
    __tablename__ = "fournisseurs"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    contact = Column(String(100))
    email = Column(String(100))
    telephone = Column(String(20))
    adresse = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    produits = relationship("Produit", back_populates="fournisseur")

class Produit(Base):
    __tablename__ = "produits"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    description = Column(Text)
    reference = Column(String(50), unique=True, index=True)
    code_barre = Column(String(50))
    categorie_id = Column(Integer, ForeignKey("categories.id"))
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"))
    prix_unitaire = Column(DECIMAL(10, 2))
    stock_min = Column(Integer, default=0)
    stock_max = Column(Integer, default=1000)
    unite = Column(String(20), default="pièce")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    categorie = relationship("Categorie", back_populates="produits")
    fournisseur = relationship("Fournisseur", back_populates="produits")
    mouvements = relationship("MouvementStock", back_populates="produit")
    stock = relationship("StockActuel", back_populates="produit", uselist=False)

class MouvementStock(Base):
    __tablename__ = "mouvements_stock"
    
    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)
    type_mouvement = Column(String(20), nullable=False)
    quantite = Column(Integer, nullable=False)
    stock_avant = Column(Integer, nullable=False)
    stock_apres = Column(Integer, nullable=False)
    motif = Column(String(200))
    reference_document = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    created_by = Column(String(100))
    
    # Contrainte pour type_mouvement
    __table_args__ = (
        CheckConstraint("type_mouvement IN ('ENTREE', 'SORTIE', 'AJUSTEMENT')", name="check_type_mouvement"),
    )
    
    # Relations
    produit = relationship("Produit", back_populates="mouvements")

class StockActuel(Base):
    __tablename__ = "stock_actuel"
    
    produit_id = Column(Integer, ForeignKey("produits.id"), primary_key=True)
    quantite_disponible = Column(Integer, nullable=False, default=0)
    derniere_entree = Column(TIMESTAMP)
    derniere_sortie = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    produit = relationship("Produit", back_populates="stock") 
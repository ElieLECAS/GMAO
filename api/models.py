from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Inventaire(Base):
    """Table principale des produits en stock"""
    __tablename__ = "inventaire"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False)
    reference_fournisseur = Column(String(100))
    produits = Column(String(500), nullable=False)
    unite_stockage = Column(String(20))
    unite_commande = Column(String(50))
    stock_min = Column(Integer, default=0)
    stock_max = Column(Integer, default=100)
    site = Column(String(100))
    lieu = Column(String(100))
    emplacement = Column(String(100))
    fournisseur = Column(String(200))
    prix_unitaire = Column(DECIMAL(10, 2), default=0)
    categorie = Column(String(100))
    secteur = Column(String(100))
    reference = Column(String(20), unique=True, nullable=False, index=True)  # Référence QR unique
    quantite = Column(Integer, default=0)
    date_entree = Column(Date, server_default=func.current_date())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Fournisseur(Base):
    """Table des fournisseurs"""
    __tablename__ = "fournisseurs"
    
    id = Column(Integer, primary_key=True, index=True)
    id_fournisseur = Column(String(20), unique=True, nullable=False, index=True)
    nom_fournisseur = Column(String(200), nullable=False, index=True)
    contact_principal = Column(String(200))
    email = Column(String(200))
    telephone = Column(String(50))
    adresse = Column(Text)
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    nb_produits = Column(Integer, default=0)
    valeur_stock_total = Column(DECIMAL(12, 2), default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Emplacement(Base):
    """Table des emplacements de stockage"""
    __tablename__ = "emplacements"
    
    id = Column(Integer, primary_key=True, index=True)
    id_emplacement = Column(String(20), unique=True, nullable=False, index=True)
    nom_emplacement = Column(String(200), nullable=False, index=True)
    type_zone = Column(String(100))
    batiment = Column(String(100))
    niveau = Column(String(50))
    responsable = Column(String(200))
    capacite_max = Column(Integer, default=100)
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    nb_produits = Column(Integer, default=0)
    taux_occupation = Column(DECIMAL(5, 2), default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Demande(Base):
    """Table des demandes de matériel"""
    __tablename__ = "demandes"
    
    id = Column(Integer, primary_key=True, index=True)
    id_demande = Column(String(50), unique=True, nullable=False, index=True)
    date_demande = Column(TIMESTAMP, nullable=False, index=True)
    demandeur = Column(String(200), nullable=False, index=True)
    produits_demandes = Column(Text, nullable=False)  # JSON stocké comme texte
    motif = Column(Text)
    statut = Column(String(50), default='En attente', index=True)
    date_traitement = Column(TIMESTAMP)
    traite_par = Column(String(200))
    commentaires = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Historique(Base):
    """Table de l'historique des mouvements de stock"""
    __tablename__ = "historique"
    
    id = Column(Integer, primary_key=True, index=True)
    date_mouvement = Column(TIMESTAMP, nullable=False, index=True)
    reference = Column(String(20), index=True)  # Référence du produit
    produit = Column(String(500), nullable=False)
    nature = Column(String(50), nullable=False, index=True)  # Entrée, Sortie, Ajustement
    quantite_mouvement = Column(Integer, nullable=False)
    quantite_avant = Column(Integer, nullable=False)
    quantite_apres = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class TableAtelier(Base):
    """Table des tables d'atelier"""
    __tablename__ = "tables_atelier"
    
    id = Column(Integer, primary_key=True, index=True)
    id_table = Column(String(20), unique=True, nullable=False, index=True)
    nom_table = Column(String(200), nullable=False)
    type_atelier = Column(String(100), nullable=False, index=True)
    emplacement = Column(String(200), nullable=False)
    responsable = Column(String(200), nullable=False, index=True)
    statut = Column(String(20), default='Actif')
    date_creation = Column(Date, server_default=func.current_date())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class ListeInventaire(Base):
    """Table des listes d'inventaire"""
    __tablename__ = "listes_inventaire"
    
    id = Column(Integer, primary_key=True, index=True)
    id_liste = Column(String(20), unique=True, nullable=False, index=True)
    nom_liste = Column(String(300), nullable=False)
    date_creation = Column(TIMESTAMP, nullable=False)
    statut = Column(String(50), default='En préparation', index=True)
    nb_produits = Column(Integer, default=0)
    cree_par = Column(String(200), default='Utilisateur')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    produits = relationship("ProduitListeInventaire", back_populates="liste", cascade="all, delete-orphan")

class ProduitListeInventaire(Base):
    """Table des produits dans les listes d'inventaire"""
    __tablename__ = "produits_listes_inventaire"
    
    id = Column(Integer, primary_key=True, index=True)
    id_liste = Column(String(20), ForeignKey("listes_inventaire.id_liste", ondelete="CASCADE"), nullable=False)
    reference_produit = Column(String(20), nullable=False, index=True)
    nom_produit = Column(String(500), nullable=False)
    emplacement = Column(String(100))
    quantite_theorique = Column(Integer, nullable=False)
    quantite_comptee = Column(Integer)
    categorie = Column(String(100))
    fournisseur = Column(String(200))
    date_ajout = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relations
    liste = relationship("ListeInventaire", back_populates="produits") 
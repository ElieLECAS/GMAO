import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Any
import json

class APIClient:
    """Client pour interagir avec l'API FastAPI GMAO"""
    
    def __init__(self, base_url: str = "http://api:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Effectue une requête HTTP vers l'API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            st.error("❌ Impossible de se connecter à l'API. Vérifiez que le serveur API est démarré.")
            return None
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                return None
            st.error(f"❌ Erreur API ({response.status_code}): {response.text}")
            return None
        except Exception as e:
            st.error(f"❌ Erreur lors de la requête API: {str(e)}")
            return None

    # =====================================================
    # GESTION DES PRODUITS (INVENTAIRE)
    # =====================================================
    
    def get_inventaire(self, skip: int = 0, limit: int = 1000) -> pd.DataFrame:
        """Récupère tous les produits de l'inventaire et les retourne sous forme de DataFrame"""
        data = self._make_request("GET", "/inventaire/", params={"skip": skip, "limit": limit})
        
        if data is None:
            return pd.DataFrame()
        
        # Convertir en DataFrame avec les colonnes attendues par l'application
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Mapper les colonnes de l'API vers les colonnes attendues par l'app
            column_mapping = {
                'code': 'Code',
                'reference_fournisseur': 'Reference_Fournisseur',
                'produits': 'Produits',
                'unite_stockage': 'Unite_Stockage',
                'unite_commande': 'Unite_Commande',
                'stock_min': 'Stock_Min',
                'stock_max': 'Stock_Max',
                'site': 'Site',
                'lieu': 'Lieu',
                'emplacement': 'Emplacement',
                'fournisseur': 'Fournisseur',
                'prix_unitaire': 'Prix_Unitaire',
                'categorie': 'Categorie',
                'secteur': 'Secteur',
                'reference': 'Reference',
                'quantite': 'Quantite',
                'date_entree': 'Date_Entree'
            }
            
            df = df.rename(columns=column_mapping)
            
            # S'assurer que les colonnes numériques sont bien typées
            numeric_columns = ['Stock_Min', 'Stock_Max', 'Prix_Unitaire', 'Quantite']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    def create_produit(self, produit_data: dict) -> dict:
        """Crée un nouveau produit dans l'inventaire"""
        # Mapper les colonnes de l'app vers les colonnes de l'API
        api_data = {
            'code': produit_data.get('Code', ''),
            'reference_fournisseur': produit_data.get('Reference_Fournisseur', ''),
            'produits': produit_data.get('Produits', ''),
            'unite_stockage': produit_data.get('Unite_Stockage', ''),
            'unite_commande': produit_data.get('Unite_Commande', ''),
            'stock_min': int(produit_data.get('Stock_Min', 0)),
            'stock_max': int(produit_data.get('Stock_Max', 100)),
            'site': produit_data.get('Site', ''),
            'lieu': produit_data.get('Lieu', ''),
            'emplacement': produit_data.get('Emplacement', ''),
            'fournisseur': produit_data.get('Fournisseur', ''),
            'prix_unitaire': float(produit_data.get('Prix_Unitaire', 0)),
            'categorie': produit_data.get('Categorie', ''),
            'secteur': produit_data.get('Secteur', ''),
            'reference': produit_data.get('Reference', ''),
            'quantite': int(produit_data.get('Quantite', 0))
        }
        
        return self._make_request("POST", "/inventaire/", data=api_data)
    
    def update_produit(self, produit_id: int, produit_data: dict) -> dict:
        """Met à jour un produit existant"""
        # Mapper les colonnes de l'app vers les colonnes de l'API
        api_data = {
            'code': produit_data.get('Code'),
            'reference_fournisseur': produit_data.get('Reference_Fournisseur'),
            'produits': produit_data.get('Produits'),
            'unite_stockage': produit_data.get('Unite_Stockage'),
            'unite_commande': produit_data.get('Unite_Commande'),
            'stock_min': int(produit_data.get('Stock_Min', 0)) if produit_data.get('Stock_Min') is not None else None,
            'stock_max': int(produit_data.get('Stock_Max', 100)) if produit_data.get('Stock_Max') is not None else None,
            'site': produit_data.get('Site'),
            'lieu': produit_data.get('Lieu'),
            'emplacement': produit_data.get('Emplacement'),
            'fournisseur': produit_data.get('Fournisseur'),
            'prix_unitaire': float(produit_data.get('Prix_Unitaire', 0)) if produit_data.get('Prix_Unitaire') is not None else None,
            'categorie': produit_data.get('Categorie'),
            'secteur': produit_data.get('Secteur'),
            'quantite': int(produit_data.get('Quantite', 0)) if produit_data.get('Quantite') is not None else None
        }
        
        # Supprimer les valeurs None pour éviter de les envoyer à l'API
        api_data = {k: v for k, v in api_data.items() if v is not None}
        
        return self._make_request("PUT", f"/inventaire/{produit_id}", data=api_data)
    
    def get_produit_by_reference(self, reference: str) -> dict:
        """Récupère un produit par sa référence QR"""
        return self._make_request("GET", f"/inventaire/reference/{reference}")
    
    def get_produit_by_code(self, code: str) -> dict:
        """Récupère un produit par son code"""
        return self._make_request("GET", f"/inventaire/code/{code}")
    
    def search_produits(self, search_term: str) -> List[dict]:
        """Recherche des produits par terme de recherche"""
        data = self._make_request("GET", "/inventaire/search/", params={"search": search_term})
        return data if data else []
    
    def delete_produit(self, produit_id: int) -> bool:
        """Supprime un produit"""
        result = self._make_request("DELETE", f"/inventaire/{produit_id}")
        return result is not None
    
    def get_stock_faible(self) -> pd.DataFrame:
        """Récupère les produits avec un stock faible"""
        data = self._make_request("GET", "/inventaire/stock-faible/")
        
        if data is None:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if not df.empty:
            # Mapper les colonnes comme dans get_inventaire
            column_mapping = {
                'code': 'Code',
                'reference_fournisseur': 'Reference_Fournisseur',
                'produits': 'Produits',
                'unite_stockage': 'Unite_Stockage',
                'unite_commande': 'Unite_Commande',
                'stock_min': 'Stock_Min',
                'stock_max': 'Stock_Max',
                'site': 'Site',
                'lieu': 'Lieu',
                'emplacement': 'Emplacement',
                'fournisseur': 'Fournisseur',
                'prix_unitaire': 'Prix_Unitaire',
                'categorie': 'Categorie',
                'secteur': 'Secteur',
                'reference': 'Reference',
                'quantite': 'Quantite',
                'date_entree': 'Date_Entree'
            }
            df = df.rename(columns=column_mapping)
        
        return df
    
    def effectuer_mouvement_stock(self, reference: str, nature: str, quantite_mouvement: int, 
                                 quantite_avant: int, quantite_apres: int, produit: str) -> dict:
        """Effectue un mouvement de stock et l'enregistre dans l'historique"""
        mouvement_data = {
            'reference': reference,
            'produit': produit,
            'nature': nature,
            'quantite_mouvement': quantite_mouvement,
            'quantite_avant': quantite_avant,
            'quantite_apres': quantite_apres
        }
        
        return self._make_request("POST", "/mouvements-stock/", data=mouvement_data)
    
    # =====================================================
    # GESTION DES FOURNISSEURS
    # =====================================================
    
    def get_fournisseurs(self) -> pd.DataFrame:
        """Récupère tous les fournisseurs"""
        data = self._make_request("GET", "/fournisseurs/", params={"limit": 1000})
        
        if data is None:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if not df.empty:
            # Mapper les colonnes pour compatibilité avec l'app existante
            column_mapping = {
                'id_fournisseur': 'ID_Fournisseur',
                'nom_fournisseur': 'Nom_Fournisseur',
                'contact_principal': 'Contact_Principal',
                'email': 'Email',
                'telephone': 'Telephone',
                'adresse': 'Adresse',
                'statut': 'Statut',
                'nb_produits': 'Nb_Produits',
                'valeur_stock_total': 'Valeur_Stock_Total'
            }
            df = df.rename(columns=column_mapping)
            
            # Add Date_Creation column if it doesn't exist (for compatibility with app.py)
            if 'Date_Creation' not in df.columns:
                df['Date_Creation'] = 'Non disponible'
        
        return df
    
    def create_fournisseur(self, fournisseur_data: dict) -> dict:
        """Crée un nouveau fournisseur"""
        api_data = {
            'id_fournisseur': fournisseur_data.get('ID_Fournisseur', ''),
            'nom_fournisseur': fournisseur_data.get('Nom_Fournisseur', ''),
            'contact_principal': fournisseur_data.get('Contact_Principal', ''),
            'email': fournisseur_data.get('Email', ''),
            'telephone': fournisseur_data.get('Telephone', ''),
            'adresse': fournisseur_data.get('Adresse', '')
        }
        
        return self._make_request("POST", "/fournisseurs/", data=api_data)
    
    # =====================================================
    # GESTION DES EMPLACEMENTS
    # =====================================================
    
    def get_emplacements(self) -> pd.DataFrame:
        """Récupère tous les emplacements"""
        data = self._make_request("GET", "/emplacements/", params={"limit": 1000})
        
        if data is None:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if not df.empty:
            column_mapping = {
                'id_emplacement': 'ID_Emplacement',
                'nom_emplacement': 'Nom_Emplacement',
                'type_zone': 'Type_Zone',
                'batiment': 'Batiment',
                'niveau': 'Niveau',
                'responsable': 'Responsable',
                'capacite_max': 'Capacite_Max',
                'statut': 'Statut',
                'nb_produits': 'Nb_Produits',
                'taux_occupation': 'Taux_Occupation'
            }
            df = df.rename(columns=column_mapping)
            
            # Add Date_Creation column if it doesn't exist (for compatibility with app.py)
            if 'Date_Creation' not in df.columns:
                df['Date_Creation'] = 'Non disponible'
        
        return df
    
    def create_emplacement(self, emplacement_data: dict) -> dict:
        """Crée un nouvel emplacement"""
        api_data = {
            'id_emplacement': emplacement_data.get('ID_Emplacement', ''),
            'nom_emplacement': emplacement_data.get('Nom_Emplacement', ''),
            'type_zone': emplacement_data.get('Type_Zone', ''),
            'batiment': emplacement_data.get('Batiment', ''),
            'niveau': emplacement_data.get('Niveau', ''),
            'responsable': emplacement_data.get('Responsable', ''),
            'capacite_max': int(emplacement_data.get('Capacite_Max', 100))
        }
        
        return self._make_request("POST", "/emplacements/", data=api_data)
    
    # =====================================================
    # GESTION DES TABLES D'ATELIER
    # =====================================================
    
    def get_tables_atelier(self) -> pd.DataFrame:
        """Récupère toutes les tables d'atelier"""
        data = self._make_request("GET", "/tables-atelier/", params={"limit": 1000})
        
        if data is None:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if not df.empty:
            column_mapping = {
                'id_table': 'ID_Table',
                'nom_table': 'Nom_Table',
                'type_atelier': 'Type_Atelier',
                'emplacement': 'Emplacement',
                'responsable': 'Responsable',
                'statut': 'Statut',
                'date_creation': 'Date_Creation'
            }
            df = df.rename(columns=column_mapping)
            
            # Convert date_creation to string format if it exists
            if 'Date_Creation' in df.columns:
                df['Date_Creation'] = pd.to_datetime(df['Date_Creation'], errors='coerce').dt.strftime('%Y-%m-%d')
            else:
                df['Date_Creation'] = 'Non disponible'
        
        return df
    
    def create_table_atelier(self, table_data: dict) -> dict:
        """Crée une nouvelle table d'atelier"""
        api_data = {
            'id_table': table_data.get('ID_Table', ''),
            'nom_table': table_data.get('Nom_Table', ''),
            'type_atelier': table_data.get('Type_Atelier', ''),
            'emplacement': table_data.get('Emplacement', ''),
            'responsable': table_data.get('Responsable', ''),
            'statut': table_data.get('Statut', 'Actif')
        }
        
        return self._make_request("POST", "/tables-atelier/", data=api_data)
    
    def update_table_atelier(self, table_id: int, table_data: dict) -> dict:
        """Met à jour une table d'atelier existante"""
        api_data = {
            'nom_table': table_data.get('Nom_Table'),
            'type_atelier': table_data.get('Type_Atelier'),
            'emplacement': table_data.get('Emplacement'),
            'responsable': table_data.get('Responsable'),
            'statut': table_data.get('Statut')
        }
        
        # Supprimer les valeurs None
        api_data = {k: v for k, v in api_data.items() if v is not None}
        
        return self._make_request("PUT", f"/tables-atelier/{table_id}", data=api_data)
    
    def get_table_atelier_by_id_table(self, id_table: str) -> dict:
        """Récupère une table d'atelier par son ID table"""
        return self._make_request("GET", f"/tables-atelier/id/{id_table}")
    
    # =====================================================
    # GESTION DES DEMANDES
    # =====================================================
    
    def get_demandes(self) -> pd.DataFrame:
        """Récupère toutes les demandes"""
        data = self._make_request("GET", "/demandes/", params={"limit": 1000})
        
        if data is None:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if not df.empty:
            column_mapping = {
                'id_demande': 'ID_Demande',
                'date_demande': 'Date_Demande',
                'demandeur': 'Demandeur',
                'produits_demandes': 'Produits_Demandes',
                'motif': 'Motif',
                'statut': 'Statut',
                'date_traitement': 'Date_Traitement',
                'traite_par': 'Traite_Par',
                'commentaires': 'Commentaires'
            }
            df = df.rename(columns=column_mapping)
        
        return df
    
    def create_demande(self, demande_data: dict) -> dict:
        """Crée une nouvelle demande"""
        # Générer un ID unique pour la demande
        demande_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        api_data = {
            'id_demande': demande_id,
            'date_demande': datetime.now().isoformat(),
            'demandeur': demande_data.get('demandeur', ''),
            'produits_demandes': json.dumps(demande_data.get('produits_demandes', {})),
            'motif': demande_data.get('motif', ''),
            'statut': 'En attente'
        }
        
        return self._make_request("POST", "/demandes/", data=api_data)
    
    def update_demande(self, demande_id: int, demande_data: dict) -> dict:
        """Met à jour une demande existante"""
        api_data = {
            'statut': demande_data.get('statut'),
            'traite_par': demande_data.get('traite_par'),
            'commentaires': demande_data.get('commentaires', ''),
            'date_traitement': datetime.now().isoformat() if demande_data.get('statut') != 'En attente' else None
        }
        
        # Supprimer les valeurs None
        api_data = {k: v for k, v in api_data.items() if v is not None}
        
        return self._make_request("PUT", f"/demandes/{demande_id}", data=api_data)
    
    # =====================================================
    # GESTION DE L'HISTORIQUE
    # =====================================================
    
    def get_historique(self) -> pd.DataFrame:
        """Récupère l'historique des mouvements"""
        data = self._make_request("GET", "/historique/", params={"limit": 1000})
        
        if data is None:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if not df.empty:
            column_mapping = {
                'date_mouvement': 'Date',
                'reference': 'Reference',
                'produit': 'Produit',
                'nature': 'Nature',
                'quantite_mouvement': 'Quantite_Mouvement',
                'quantite_avant': 'Quantite_Avant',
                'quantite_apres': 'Quantite_Apres'
            }
            df = df.rename(columns=column_mapping)
        
        return df
    
    # =====================================================
    # UTILITAIRES
    # =====================================================
    
    def test_connection(self) -> bool:
        """Test la connexion à l'API"""
        try:
            response = self._make_request("GET", "/health")
            return response is not None
        except:
            return False

# Instance globale du client API
api_client = APIClient() 
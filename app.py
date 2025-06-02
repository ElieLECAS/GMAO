import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import openpyxl
import qrcode
from io import BytesIO
from PIL import Image

# Configuration de la page
st.set_page_config(
    page_title="GMAO - Gestion de Stock",
    initial_sidebar_state="expanded",
    layout="wide"
)

# CSS pour optimiser l'interface mobile
st.markdown("""
<style>
    /* Optimisation mobile générale */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Gros boutons pour mobile */
        .stButton > button {
            height: 3rem;
            font-size: 1.2rem;
            font-weight: bold;
            border-radius: 10px;
        }
        
        /* Boutons + et - plus gros */
        .quantity-btn {
            height: 4rem !important;
            width: 4rem !important;
            font-size: 2rem !important;
            font-weight: bold !important;
            border-radius: 50% !important;
            margin: 0.5rem !important;
        }
        
        /* Input de quantité plus gros */
        .stNumberInput > div > div > input {
            height: 3rem;
            font-size: 1.5rem;
            text-align: center;
            font-weight: bold;
        }
        
        /* Texte plus gros pour mobile */
        .mobile-text {
            font-size: 1.2rem;
        }
        
        /* Métriques plus compactes */
        .metric-container {
            background: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
    }
    
    /* Boutons de quantité personnalisés */
    .quantity-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .quantity-display {
        font-size: 2rem;
        font-weight: bold;
        background: #f0f2f6;
        padding: 1rem 2rem;
        border-radius: 10px;
        min-width: 100px;
        text-align: center;
    }
    
    /* Styles pour le panier */
    .cart-item {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    
    /* Bouton ajouter au panier */
    .stButton > button[kind="primary"] {
        background: linear-gradient(45deg, #1f77b4, #17a2b8) !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(45deg, #1565c0, #138496) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    
    /* Boutons + et - dans le panier */
    .cart-quantity-btn {
        background: #e3f2fd !important;
        border: 2px solid #1f77b4 !important;
        color: #1f77b4 !important;
        font-weight: bold !important;
    }
    
    .cart-quantity-btn:hover {
        background: #1f77b4 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Titre de l'application optimisé mobile
st.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <h1 style="color: #1f77b4; margin-bottom: 0.5rem;">📦 GMAO</h1>
    <p style="color: #666; font-size: 1.2rem; margin: 0;">Gestion de Stock</p>
</div>
""", unsafe_allow_html=True)

# Fonction pour générer une référence unique pour les QR codes
def generer_reference_qr(code, designation):
    """Génère une référence unique de 10 chiffres basée sur le code et la désignation"""
    import hashlib
    import random
    
    # Créer un hash unique basé sur le code et la désignation
    text = f"{code}_{designation}"
    hash_obj = hashlib.md5(text.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convertir en nombre et prendre les 10 premiers chiffres
    hash_int = int(hash_hex, 16)
    reference_numerique = str(hash_int)[:10]
    
    # S'assurer qu'on a exactement 10 chiffres
    if len(reference_numerique) < 10:
        # Compléter avec des chiffres aléatoires si nécessaire
        reference_numerique = reference_numerique + ''.join([str(random.randint(0, 9)) for _ in range(10 - len(reference_numerique))])
    
    return reference_numerique[:10]

# Chargement des données
def load_data():
    # Créer le dossier data s'il n'existe pas
    os.makedirs("data", exist_ok=True)
    
    # Vérifier d'abord si le fichier enrichi existe
    fichier_enrichi = "data/inventaire_avec_references.xlsx"
    fichier_original = "data/exemple  Boschat Faille et SFS pour essai ACCESS.xlsx"
    
    # Utiliser le fichier enrichi s'il existe, sinon le fichier original
    if os.path.exists(fichier_enrichi):
        file_path = fichier_enrichi
        # st.info("📂 Utilisation du fichier d'inventaire enrichi existant")
    else:
        file_path = fichier_original
        # st.info("📂 Première utilisation - enrichissement du fichier d'inventaire en cours...")
    
    try:
        # Lire le fichier Excel existant avec gestion d'erreur robuste
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as excel_error:
            st.warning(f"⚠️ Erreur avec openpyxl: {str(excel_error)}")
            # Essayer avec xlrd comme alternative
            try:
                df = pd.read_excel(file_path, engine='xlrd')
                st.info("✅ Lecture réussie avec xlrd")
            except Exception as xlrd_error:
                st.error(f"❌ Erreur avec xlrd: {str(xlrd_error)}")
                # Si les deux échouent, essayer de recréer depuis le fichier original
                if file_path == fichier_enrichi:
                    st.info("🔄 Tentative de lecture du fichier original...")
                    df = pd.read_excel(fichier_original, engine='openpyxl')
                    st.success("✅ Lecture du fichier original réussie")
                else:
                    raise excel_error
        
        # Renommer les colonnes pour correspondre à l'application
        column_mapping = {
            'Code': 'Code',
            'Référence fournisseur': 'Reference_Fournisseur', 
            'Désignation': 'Produits',
            'Unité de stockage': 'Unite_Stockage',
            'Unite Commande': 'Unite_Commande',
            'Min': 'Stock_Min',
            'Max': 'Stock_Max',
            'Site': 'Site',
            'Lieu': 'Lieu',
            'Emplacement': 'Emplacement',
            'Fournisseur Standard': 'Fournisseur',
            'Prix': 'Prix_Unitaire',
            'Catégorie': 'Categorie',
            'Secteur': 'Secteur'
        }
        
        # Renommer les colonnes
        df = df.rename(columns=column_mapping)
        
        # Variable pour savoir si on doit sauvegarder les modifications
        modifications_apportees = False
        
        # Ajouter une colonne Reference pour les QR codes si elle n'existe pas
        if 'Reference' not in df.columns:
            df['Reference'] = df.apply(lambda row: generer_reference_qr(row['Code'], row['Produits']), axis=1)
            modifications_apportees = True
        
        # S'assurer que la colonne Reference est de type string
        df['Reference'] = df['Reference'].astype(str)
        
        # S'assurer que les colonnes Min et Max sont numériques
        df['Stock_Min'] = pd.to_numeric(df['Stock_Min'], errors='coerce').fillna(0)
        df['Stock_Max'] = pd.to_numeric(df['Stock_Max'], errors='coerce').fillna(100)
        df['Prix_Unitaire'] = pd.to_numeric(df['Prix_Unitaire'], errors='coerce').fillna(0)
        
        # Ajouter une colonne Quantite avec la valeur 0 par défaut si elle n'existe pas
        if 'Quantite' not in df.columns:
            # Initialiser toutes les quantités à 0
            df['Quantite'] = 0
            modifications_apportees = True
        else:
            df['Quantite'] = pd.to_numeric(df['Quantite'], errors='coerce').fillna(0)
            
        # Ajouter une colonne Date_Entree si elle n'existe pas
        if 'Date_Entree' not in df.columns:
            df['Date_Entree'] = datetime.now().strftime("%Y-%m-%d")
            modifications_apportees = True
        
        # Sauvegarder le fichier avec les nouvelles colonnes si des modifications ont été apportées
        if modifications_apportees:
            try:
                # Créer un nouveau fichier avec les données enrichies
                nouveau_fichier = "data/inventaire_avec_references.xlsx"
                df.to_excel(nouveau_fichier, index=False, engine='openpyxl')
                st.success(f"✅ Fichier enrichi sauvegardé : {nouveau_fichier}")
            except Exception as e:
                st.warning(f"⚠️ Impossible de sauvegarder le fichier enrichi : {str(e)}")
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier Excel: {str(e)}")
        # En cas d'erreur, créer un DataFrame vide avec les colonnes nécessaires
        df = pd.DataFrame(columns=['Code', 'Reference_Fournisseur', 'Produits', 'Unite_Stockage', 
                                 'Unite_Commande', 'Stock_Min', 'Stock_Max', 'Site', 'Lieu', 
                                 'Emplacement', 'Fournisseur', 'Prix_Unitaire', 'Categorie', 
                                 'Secteur', 'Reference', 'Quantite', 'Date_Entree'])
        return df

# Fonction pour sauvegarder les données
def save_data(df):
    try:
        # S'assurer que la colonne Reference est de type string avant la sauvegarde
        if 'Reference' in df.columns:
            # Traitement spécial pour éviter les .0 sur les nombres entiers
            df['Reference'] = df['Reference'].apply(lambda x: 
                str(int(float(x))) if pd.notna(x) and str(x).replace('.', '').replace('-', '').isdigit() and float(x) == int(float(x))
                else str(x) if pd.notna(x) and str(x) not in ['nan', 'None', ''] 
                else ''
            )
        
        # Sauvegarder dans le fichier enrichi pour maintenir la persistance
        fichier_enrichi = "data/inventaire_avec_references.xlsx"
        df.to_excel(fichier_enrichi, index=False, engine='openpyxl')
        
        # Aussi sauvegarder une copie de sauvegarde
        df.to_excel("data/inventaire_sauvegarde.xlsx", index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du fichier Excel: {str(e)}")

def log_mouvement(produit, nature, quantite_mouvement, quantite_apres, quantite_avant, reference=None):
    os.makedirs("data", exist_ok=True)
    file_path = "data/historique.xlsx"
    new_row = {
        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Reference': str(reference) if reference else "",
        'Produit': produit,
        'Nature': nature,
        'Quantite_Mouvement': quantite_mouvement,
        'Quantite_Avant': quantite_avant,
        'Quantite_Apres': quantite_apres
    }
    if os.path.exists(file_path):
        df_hist = pd.read_excel(file_path, engine='openpyxl')
        # S'assurer que la colonne Reference existe et est de type string
        if 'Reference' not in df_hist.columns:
            df_hist['Reference'] = ""
        # Traitement spécial pour éviter les .0 sur les nombres entiers
        df_hist['Reference'] = df_hist['Reference'].apply(lambda x: 
            str(int(float(x))) if pd.notna(x) and str(x).replace('.', '').replace('-', '').isdigit() and float(x) == int(float(x))
            else str(x) if pd.notna(x) and str(x) not in ['nan', 'None', ''] 
            else ''
        )
        df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df_hist = pd.DataFrame([new_row])
    
    # S'assurer que la colonne Reference est de type string avant la sauvegarde
    # Traitement spécial pour éviter les .0 sur les nombres entiers
    df_hist['Reference'] = df_hist['Reference'].apply(lambda x: 
        str(int(float(x))) if pd.notna(x) and str(x).replace('.', '').replace('-', '').isdigit() and float(x) == int(float(x))
        else str(x) if pd.notna(x) and str(x) not in ['nan', 'None', ''] 
        else ''
    )
    df_hist.to_excel(file_path, index=False, engine='openpyxl')

def sauvegarder_demande(demandeur, produits_demandes, motif):
    """Sauvegarde une nouvelle demande de matériel"""
    os.makedirs("data", exist_ok=True)
    file_path = "data/demandes.xlsx"
    
    # Créer un ID unique pour la demande
    demande_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    new_row = {
        'ID_Demande': demande_id,
        'Date_Demande': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Demandeur': demandeur,
        'Produits_Demandes': str(produits_demandes),  # Convertir le dict en string
        'Motif': motif,
        'Statut': 'En attente',
        'Date_Traitement': '',
        'Traite_Par': '',
        'Commentaires': ''
    }
    
    if os.path.exists(file_path):
        df_demandes = pd.read_excel(file_path, engine='openpyxl')
        df_demandes = pd.concat([df_demandes, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df_demandes = pd.DataFrame([new_row])
    
    df_demandes.to_excel(file_path, index=False, engine='openpyxl')
    return demande_id

def charger_demandes():
    """Charge toutes les demandes depuis le fichier Excel"""
    file_path = "data/demandes.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            st.error(f"Erreur lors du chargement des demandes: {str(e)}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def mettre_a_jour_demande(demande_id, nouveau_statut, traite_par, commentaires=""):
    """Met à jour le statut d'une demande"""
    file_path = "data/demandes.xlsx"
    if os.path.exists(file_path):
        df_demandes = pd.read_excel(file_path, engine='openpyxl')
        mask = df_demandes['ID_Demande'] == demande_id
        df_demandes.loc[mask, 'Statut'] = nouveau_statut
        df_demandes.loc[mask, 'Date_Traitement'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_demandes.loc[mask, 'Traite_Par'] = traite_par
        df_demandes.loc[mask, 'Commentaires'] = commentaires
        df_demandes.to_excel(file_path, index=False, engine='openpyxl')
        return True
    return False

def charger_tables_atelier():
    """Charge toutes les tables d'atelier depuis le fichier Excel"""
    file_path = "data/tables_atelier.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            st.error(f"Erreur lors du chargement des tables d'atelier: {str(e)}")
            return pd.DataFrame()
    else:
        # Créer le fichier avec des données initiales
        tables_initiales = {
            'ID_Table': ['ALU01', 'ALU02', 'PVC03', 'PVC04', 'BOIS05', 'BOIS06', 'METAL07', 'METAL08'],
            'Nom_Table': ['Table Aluminium 01', 'Table Aluminium 02', 'Table PVC 03', 'Table PVC 04', 
                         'Table Bois 05', 'Table Bois 06', 'Table Métal 07', 'Table Métal 08'],
            'Type_Atelier': ['Aluminium', 'Aluminium', 'PVC', 'PVC', 'Bois', 'Bois', 'Métallerie', 'Métallerie'],
            'Emplacement': ['Atelier A - Zone 1', 'Atelier A - Zone 2', 'Atelier B - Zone 1', 'Atelier B - Zone 2',
                           'Atelier C - Zone 1', 'Atelier C - Zone 2', 'Atelier D - Zone 1', 'Atelier D - Zone 2'],
            'Responsable': ['Jean Dupont', 'Marie Martin', 'Pierre Durand', 'Sophie Leroy',
                           'Michel Bernard', 'Claire Moreau', 'Antoine Petit', 'Isabelle Roux'],
            'Statut': ['Actif', 'Actif', 'Actif', 'Actif', 'Actif', 'Actif', 'Actif', 'Actif'],
            'Date_Creation': ['2024-01-15', '2024-01-15', '2024-01-20', '2024-01-20',
                             '2024-02-01', '2024-02-01', '2024-02-10', '2024-02-10']
        }
        df_tables = pd.DataFrame(tables_initiales)
        os.makedirs("data", exist_ok=True)
        df_tables.to_excel(file_path, index=False, engine='openpyxl')
        return df_tables

def sauvegarder_tables_atelier(df_tables):
    """Sauvegarde les tables d'atelier dans le fichier Excel"""
    try:
        df_tables.to_excel("data/tables_atelier.xlsx", index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des tables d'atelier: {str(e)}")
        return False

def ajouter_table_atelier(id_table, nom_table, type_atelier, emplacement, responsable):
    """Ajoute une nouvelle table d'atelier"""
    df_tables = charger_tables_atelier()
    
    # Vérifier si l'ID existe déjà
    if id_table in df_tables['ID_Table'].values:
        return False, "Cette ID de table existe déjà"
    
    nouvelle_table = {
        'ID_Table': id_table,
        'Nom_Table': nom_table,
        'Type_Atelier': type_atelier,
        'Emplacement': emplacement,
        'Responsable': responsable,
        'Statut': 'Actif',
        'Date_Creation': datetime.now().strftime("%Y-%m-%d")
    }
    
    df_tables = pd.concat([df_tables, pd.DataFrame([nouvelle_table])], ignore_index=True)
    
    if sauvegarder_tables_atelier(df_tables):
        return True, "Table d'atelier ajoutée avec succès"
    else:
        return False, "Erreur lors de la sauvegarde"

def charger_fournisseurs():
    """Charge tous les fournisseurs depuis le fichier Excel"""
    file_path = "data/fournisseurs.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            st.error(f"Erreur lors du chargement des fournisseurs: {str(e)}")
            return pd.DataFrame()
    else:
        # Créer le fichier avec les fournisseurs extraits de l'inventaire
        return creer_fichier_fournisseurs_initial()

def creer_fichier_fournisseurs_initial():
    """Crée le fichier initial des fournisseurs basé sur l'inventaire existant"""
    global df
    
    if df.empty or 'Fournisseur' not in df.columns:
        # Créer des fournisseurs par défaut
        fournisseurs_initiaux = {
            'ID_Fournisseur': ['FOUR001', 'FOUR002', 'FOUR003'],
            'Nom_Fournisseur': ['Fournisseur A', 'Fournisseur B', 'Fournisseur C'],
            'Contact_Principal': ['Jean Martin', 'Marie Dubois', 'Pierre Leroy'],
            'Email': ['contact@fournisseur-a.fr', 'info@fournisseur-b.fr', 'commandes@fournisseur-c.fr'],
            'Telephone': ['01 23 45 67 89', '01 98 76 54 32', '01 11 22 33 44'],
            'Adresse': ['123 Rue de la Paix, 75001 Paris', '456 Avenue des Champs, 69000 Lyon', '789 Boulevard Central, 13000 Marseille'],
            'Statut': ['Actif', 'Actif', 'Actif'],
            'Date_Creation': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'Nb_Produits': [0, 0, 0],
            'Valeur_Stock_Total': [0.0, 0.0, 0.0]
        }
    else:
        # Extraire les fournisseurs uniques de l'inventaire
        fournisseurs_uniques = df['Fournisseur'].dropna().unique()
        
        fournisseurs_initiaux = {
            'ID_Fournisseur': [f"FOUR{str(i+1).zfill(3)}" for i in range(len(fournisseurs_uniques))],
            'Nom_Fournisseur': fournisseurs_uniques.tolist(),
            'Contact_Principal': ['À définir'] * len(fournisseurs_uniques),
            'Email': [''] * len(fournisseurs_uniques),
            'Telephone': [''] * len(fournisseurs_uniques),
            'Adresse': [''] * len(fournisseurs_uniques),
            'Statut': ['Actif'] * len(fournisseurs_uniques),
            'Date_Creation': [datetime.now().strftime("%Y-%m-%d")] * len(fournisseurs_uniques),
            'Nb_Produits': [0] * len(fournisseurs_uniques),
            'Valeur_Stock_Total': [0.0] * len(fournisseurs_uniques)
        }
        
        # Calculer le nombre de produits et la valeur du stock pour chaque fournisseur
        for i, fournisseur in enumerate(fournisseurs_uniques):
            produits_fournisseur = df[df['Fournisseur'] == fournisseur]
            fournisseurs_initiaux['Nb_Produits'][i] = len(produits_fournisseur)
            fournisseurs_initiaux['Valeur_Stock_Total'][i] = (produits_fournisseur['Quantite'] * produits_fournisseur['Prix_Unitaire']).sum()
    
    df_fournisseurs = pd.DataFrame(fournisseurs_initiaux)
    os.makedirs("data", exist_ok=True)
    df_fournisseurs.to_excel("data/fournisseurs.xlsx", index=False, engine='openpyxl')
    return df_fournisseurs

def sauvegarder_fournisseurs(df_fournisseurs):
    """Sauvegarde les fournisseurs dans le fichier Excel"""
    try:
        df_fournisseurs.to_excel("data/fournisseurs.xlsx", index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des fournisseurs: {str(e)}")
        return False

def ajouter_fournisseur(nom_fournisseur, contact_principal, email, telephone, adresse):
    """Ajoute un nouveau fournisseur"""
    df_fournisseurs = charger_fournisseurs()
    
    # Vérifier si le nom existe déjà
    if nom_fournisseur in df_fournisseurs['Nom_Fournisseur'].values:
        return False, "Ce nom de fournisseur existe déjà"
    
    # Générer un nouvel ID
    if not df_fournisseurs.empty:
        dernier_id = df_fournisseurs['ID_Fournisseur'].str.extract(r'(\d+)').astype(int).max().iloc[0]
        nouvel_id = f"FOUR{str(dernier_id + 1).zfill(3)}"
    else:
        nouvel_id = "FOUR001"
    
    nouveau_fournisseur = {
        'ID_Fournisseur': nouvel_id,
        'Nom_Fournisseur': nom_fournisseur,
        'Contact_Principal': contact_principal,
        'Email': email,
        'Telephone': telephone,
        'Adresse': adresse,
        'Statut': 'Actif',
        'Date_Creation': datetime.now().strftime("%Y-%m-%d"),
        'Nb_Produits': 0,
        'Valeur_Stock_Total': 0.0
    }
    
    df_fournisseurs = pd.concat([df_fournisseurs, pd.DataFrame([nouveau_fournisseur])], ignore_index=True)
    
    if sauvegarder_fournisseurs(df_fournisseurs):
        return True, "Fournisseur ajouté avec succès"
    else:
        return False, "Erreur lors de la sauvegarde"

def ajouter_fournisseur_automatique(nom_fournisseur):
    """Ajoute automatiquement un fournisseur s'il n'existe pas déjà dans le fichier fournisseurs.xlsx"""
    df_fournisseurs = charger_fournisseurs()
    
    # Vérifier si le fournisseur existe déjà
    if nom_fournisseur in df_fournisseurs['Nom_Fournisseur'].values:
        return True  # Le fournisseur existe déjà, pas besoin de l'ajouter
    
    # Générer un nouvel ID
    if not df_fournisseurs.empty:
        dernier_id = df_fournisseurs['ID_Fournisseur'].str.extract(r'(\d+)').astype(int).max().iloc[0]
        nouvel_id = f"FOUR{str(dernier_id + 1).zfill(3)}"
    else:
        nouvel_id = "FOUR001"
    
    # Créer le nouveau fournisseur avec des valeurs par défaut
    nouveau_fournisseur = {
        'ID_Fournisseur': nouvel_id,
        'Nom_Fournisseur': nom_fournisseur,
        'Contact_Principal': 'À définir',
        'Email': '',
        'Telephone': '',
        'Adresse': 'À définir',
        'Statut': 'Actif',
        'Date_Creation': datetime.now().strftime("%Y-%m-%d"),
        'Nb_Produits': 1,  # Il aura au moins 1 produit (celui qu'on est en train d'ajouter)
        'Valeur_Stock_Total': 0.0
    }
    
    df_fournisseurs = pd.concat([df_fournisseurs, pd.DataFrame([nouveau_fournisseur])], ignore_index=True)
    
    return sauvegarder_fournisseurs(df_fournisseurs)

def mettre_a_jour_statistiques_fournisseurs():
    """Met à jour les statistiques des fournisseurs basées sur l'inventaire actuel"""
    global df
    df_fournisseurs = charger_fournisseurs()
    
    if df.empty or df_fournisseurs.empty:
        return df_fournisseurs
    
    # Réinitialiser les statistiques
    df_fournisseurs['Nb_Produits'] = 0
    df_fournisseurs['Valeur_Stock_Total'] = 0.0
    
    # Calculer les nouvelles statistiques
    for idx, fournisseur_row in df_fournisseurs.iterrows():
        nom_fournisseur = fournisseur_row['Nom_Fournisseur']
        
        # Trouver les produits de ce fournisseur
        produits_fournisseur = df[df['Fournisseur'] == nom_fournisseur]
        
        if not produits_fournisseur.empty:
            nb_produits = len(produits_fournisseur)
            valeur_stock = (produits_fournisseur['Quantite'] * produits_fournisseur['Prix_Unitaire']).sum()
            
            df_fournisseurs.loc[idx, 'Nb_Produits'] = nb_produits
            df_fournisseurs.loc[idx, 'Valeur_Stock_Total'] = valeur_stock
    
    # Sauvegarder les statistiques mises à jour
    sauvegarder_fournisseurs(df_fournisseurs)
    return df_fournisseurs

def charger_emplacements():
    """Charge tous les emplacements depuis le fichier Excel"""
    file_path = "data/emplacements.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            st.error(f"Erreur lors du chargement des emplacements: {str(e)}")
            return pd.DataFrame()
    else:
        # Créer le fichier avec les emplacements extraits de l'inventaire
        return creer_fichier_emplacements_initial()

def creer_fichier_emplacements_initial():
    """Crée le fichier initial des emplacements basé sur l'inventaire existant"""
    global df
    
    if df.empty or 'Emplacement' not in df.columns:
        # Créer des emplacements par défaut
        emplacements_initiaux = {
            'ID_Emplacement': ['EMP001', 'EMP002', 'EMP003', 'EMP004', 'EMP005'],
            'Nom_Emplacement': ['Atelier A', 'Atelier B', 'Stockage', 'Magasin', 'Zone de réception'],
            'Type_Zone': ['Atelier', 'Atelier', 'Stockage', 'Magasin', 'Réception'],
            'Batiment': ['Bâtiment 1', 'Bâtiment 1', 'Bâtiment 2', 'Bâtiment 1', 'Bâtiment 2'],
            'Niveau': ['RDC', 'RDC', 'RDC', '1er étage', 'RDC'],
            'Responsable': ['Jean Martin', 'Marie Dubois', 'Pierre Leroy', 'Sophie Bernard', 'Luc Moreau'],
            'Capacite_Max': [100, 150, 500, 200, 80],
            'Statut': ['Actif', 'Actif', 'Actif', 'Actif', 'Actif'],
            'Date_Creation': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01'],
            'Nb_Produits': [0, 0, 0, 0, 0],
            'Taux_Occupation': [0.0, 0.0, 0.0, 0.0, 0.0]
        }
    else:
        # Extraire les emplacements uniques de l'inventaire
        emplacements_uniques = df['Emplacement'].dropna().unique()
        
        emplacements_initiaux = {
            'ID_Emplacement': [f"EMP{str(i+1).zfill(3)}" for i in range(len(emplacements_uniques))],
            'Nom_Emplacement': emplacements_uniques.tolist(),
            'Type_Zone': ['À définir'] * len(emplacements_uniques),
            'Batiment': ['À définir'] * len(emplacements_uniques),
            'Niveau': ['À définir'] * len(emplacements_uniques),
            'Responsable': ['À définir'] * len(emplacements_uniques),
            'Capacite_Max': [100] * len(emplacements_uniques),
            'Statut': ['Actif'] * len(emplacements_uniques),
            'Date_Creation': [datetime.now().strftime("%Y-%m-%d")] * len(emplacements_uniques),
            'Nb_Produits': [0] * len(emplacements_uniques),
            'Taux_Occupation': [0.0] * len(emplacements_uniques)
        }
        
        # Calculer le nombre de produits pour chaque emplacement
        for i, emplacement in enumerate(emplacements_uniques):
            produits_emplacement = df[df['Emplacement'] == emplacement]
            emplacements_initiaux['Nb_Produits'][i] = len(produits_emplacement)
            # Calculer le taux d'occupation (nombre de produits / capacité max * 100)
            taux = (len(produits_emplacement) / emplacements_initiaux['Capacite_Max'][i]) * 100
            emplacements_initiaux['Taux_Occupation'][i] = min(taux, 100.0)  # Limiter à 100%
    
    df_emplacements = pd.DataFrame(emplacements_initiaux)
    os.makedirs("data", exist_ok=True)
    df_emplacements.to_excel("data/emplacements.xlsx", index=False, engine='openpyxl')
    return df_emplacements

def sauvegarder_emplacements(df_emplacements):
    """Sauvegarde les emplacements dans le fichier Excel"""
    try:
        df_emplacements.to_excel("data/emplacements.xlsx", index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des emplacements: {str(e)}")
        return False

def ajouter_emplacement(nom_emplacement, type_zone, batiment, niveau, responsable, capacite_max):
    """Ajoute un nouvel emplacement"""
    df_emplacements = charger_emplacements()
    
    # Vérifier si l'emplacement existe déjà
    if nom_emplacement in df_emplacements['Nom_Emplacement'].values:
        return False, "Cet emplacement existe déjà"
    
    # Générer un ID unique
    if df_emplacements.empty:
        nouvel_id = "EMP001"
    else:
        # Trouver le prochain ID disponible
        ids_existants = df_emplacements['ID_Emplacement'].tolist()
        numero_max = max([int(id_emp[3:]) for id_emp in ids_existants if id_emp.startswith('EMP')])
        nouvel_id = f"EMP{str(numero_max + 1).zfill(3)}"
    
    nouvel_emplacement = {
        'ID_Emplacement': nouvel_id,
        'Nom_Emplacement': nom_emplacement,
        'Type_Zone': type_zone,
        'Batiment': batiment,
        'Niveau': niveau,
        'Responsable': responsable,
        'Capacite_Max': capacite_max,
        'Statut': 'Actif',
        'Date_Creation': datetime.now().strftime("%Y-%m-%d"),
        'Nb_Produits': 0,
        'Taux_Occupation': 0.0
    }
    
    df_emplacements = pd.concat([df_emplacements, pd.DataFrame([nouvel_emplacement])], ignore_index=True)
    
    if sauvegarder_emplacements(df_emplacements):
        return True, "Emplacement ajouté avec succès"
    else:
        return False, "Erreur lors de la sauvegarde"

def mettre_a_jour_statistiques_emplacements():
    """Met à jour les statistiques des emplacements basées sur l'inventaire actuel"""
    global df
    df_emplacements = charger_emplacements()
    
    if df_emplacements.empty:
        return df_emplacements
    
    # Réinitialiser les compteurs
    df_emplacements['Nb_Produits'] = 0
    df_emplacements['Taux_Occupation'] = 0.0
    
    # Calculer les statistiques pour chaque emplacement
    for idx, emplacement_row in df_emplacements.iterrows():
        nom_emplacement = emplacement_row['Nom_Emplacement']
        capacite_max = emplacement_row['Capacite_Max']
        
        # Compter les produits dans cet emplacement
        if not df.empty and 'Emplacement' in df.columns:
            produits_emplacement = df[df['Emplacement'] == nom_emplacement]
            nb_produits = len(produits_emplacement)
            
            # Calculer le taux d'occupation
            taux_occupation = (nb_produits / capacite_max * 100) if capacite_max > 0 else 0
            taux_occupation = min(taux_occupation, 100.0)  # Limiter à 100%
            
            # Mettre à jour les valeurs
            df_emplacements.loc[idx, 'Nb_Produits'] = nb_produits
            df_emplacements.loc[idx, 'Taux_Occupation'] = round(taux_occupation, 1)
    
    # Sauvegarder les statistiques mises à jour
    sauvegarder_emplacements(df_emplacements)
    return df_emplacements

def charger_listes_inventaire():
    """Charge toutes les listes d'inventaire depuis le fichier Excel"""
    file_path = "data/listes_inventaire.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            st.error(f"Erreur lors du chargement des listes d'inventaire: {str(e)}")
            return pd.DataFrame()
    else:
        # Créer le fichier avec une structure vide
        return creer_fichier_listes_inventaire_initial()

def creer_fichier_listes_inventaire_initial():
    """Crée le fichier initial des listes d'inventaire"""
    listes_initiales = {
        'ID_Liste': [],
        'Nom_Liste': [],
        'Date_Creation': [],
        'Statut': [],
        'Nb_Produits': [],
        'Cree_Par': []
    }
    
    df_listes = pd.DataFrame(listes_initiales)
    os.makedirs("data", exist_ok=True)
    df_listes.to_excel("data/listes_inventaire.xlsx", index=False, engine='openpyxl')
    return df_listes

def sauvegarder_listes_inventaire(df_listes):
    """Sauvegarde les listes d'inventaire dans le fichier Excel"""
    try:
        df_listes.to_excel("data/listes_inventaire.xlsx", index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des listes d'inventaire: {str(e)}")
        return False

def charger_produits_liste_inventaire():
    """Charge tous les produits des listes d'inventaire depuis le fichier Excel"""
    file_path = "data/produits_listes_inventaire.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            st.error(f"Erreur lors du chargement des produits des listes d'inventaire: {str(e)}")
            return pd.DataFrame()
    else:
        # Créer le fichier avec une structure vide
        return creer_fichier_produits_listes_inventaire_initial()

def creer_fichier_produits_listes_inventaire_initial():
    """Crée le fichier initial des produits des listes d'inventaire"""
    produits_listes_initiaux = {
        'ID_Liste': [],
        'Reference_Produit': [],
        'Nom_Produit': [],
        'Emplacement': [],
        'Quantite_Theorique': [],
        'Categorie': [],
        'Fournisseur': [],
        'Date_Ajout': []
    }
    
    df_produits_listes = pd.DataFrame(produits_listes_initiaux)
    os.makedirs("data", exist_ok=True)
    df_produits_listes.to_excel("data/produits_listes_inventaire.xlsx", index=False, engine='openpyxl')
    return df_produits_listes

def sauvegarder_produits_listes_inventaire(df_produits_listes):
    """Sauvegarde les produits des listes d'inventaire dans le fichier Excel"""
    try:
        df_produits_listes.to_excel("data/produits_listes_inventaire.xlsx", index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des produits des listes d'inventaire: {str(e)}")
        return False

def ajouter_liste_inventaire(nom_liste, produits_dict, cree_par="Utilisateur"):
    """Ajoute une nouvelle liste d'inventaire avec ses produits"""
    df_listes = charger_listes_inventaire()
    df_produits_listes = charger_produits_liste_inventaire()
    
    # Vérifier si la liste existe déjà
    if nom_liste in df_listes['Nom_Liste'].values:
        return False, "Cette liste d'inventaire existe déjà"
    
    # Générer un ID unique pour la liste
    if df_listes.empty:
        nouvel_id_liste = "INV001"
    else:
        # Trouver le prochain ID disponible
        ids_existants = df_listes['ID_Liste'].tolist()
        if ids_existants:
            numero_max = max([int(id_liste[3:]) for id_liste in ids_existants if id_liste.startswith('INV')])
            nouvel_id_liste = f"INV{str(numero_max + 1).zfill(3)}"
        else:
            nouvel_id_liste = "INV001"
    
    # Ajouter la nouvelle liste
    nouvelle_liste = {
        'ID_Liste': nouvel_id_liste,
        'Nom_Liste': nom_liste,
        'Date_Creation': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Statut': 'En préparation',
        'Nb_Produits': len(produits_dict),
        'Cree_Par': cree_par
    }
    
    df_listes = pd.concat([df_listes, pd.DataFrame([nouvelle_liste])], ignore_index=True)
    
    # Ajouter les produits de la liste
    nouveaux_produits = []
    for ref, item_data in produits_dict.items():
        nouveau_produit = {
            'ID_Liste': nouvel_id_liste,
            'Reference_Produit': ref,
            'Nom_Produit': item_data['produit'],
            'Emplacement': item_data['emplacement'],
            'Quantite_Theorique': item_data['quantite_theorique'],
            'Categorie': item_data.get('categorie', 'N/A'),
            'Fournisseur': item_data.get('fournisseur', 'N/A'),
            'Date_Ajout': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        nouveaux_produits.append(nouveau_produit)
    
    if nouveaux_produits:
        df_nouveaux_produits = pd.DataFrame(nouveaux_produits)
        df_produits_listes = pd.concat([df_produits_listes, df_nouveaux_produits], ignore_index=True)
    
    # Sauvegarder les deux fichiers
    if sauvegarder_listes_inventaire(df_listes) and sauvegarder_produits_listes_inventaire(df_produits_listes):
        return True, f"Liste d'inventaire '{nom_liste}' sauvegardée avec succès"
    else:
        return False, "Erreur lors de la sauvegarde"

def obtenir_listes_inventaire_avec_produits():
    """Récupère toutes les listes d'inventaire avec leurs produits"""
    df_listes = charger_listes_inventaire()
    df_produits_listes = charger_produits_liste_inventaire()
    
    listes_avec_produits = {}
    
    for _, liste_row in df_listes.iterrows():
        id_liste = liste_row['ID_Liste']
        nom_liste = liste_row['Nom_Liste']
        
        # Récupérer les produits de cette liste
        produits_liste = df_produits_listes[df_produits_listes['ID_Liste'] == id_liste]
        
        # Convertir en format dict pour compatibilité avec l'existant
        produits_dict = {}
        for _, produit_row in produits_liste.iterrows():
            produits_dict[produit_row['Reference_Produit']] = {
                'produit': produit_row['Nom_Produit'],
                'reference': produit_row['Reference_Produit'],
                'emplacement': produit_row['Emplacement'],
                'quantite_theorique': produit_row['Quantite_Theorique'],
                'categorie': produit_row['Categorie'],
                'fournisseur': produit_row['Fournisseur']
            }
        
        listes_avec_produits[nom_liste] = {
            'id_liste': id_liste,
            'produits': produits_dict,
            'date_creation': liste_row['Date_Creation'],
            'statut': liste_row['Statut'],
            'nb_produits': liste_row['Nb_Produits'],
            'cree_par': liste_row['Cree_Par']
        }
    
    return listes_avec_produits

# Sélecteur de quantité mobile
def mobile_quantity_selector(label, min_value=1, max_value=100, default_value=1, key_prefix="qty"):
    """
    Sélecteur de quantité optimisé pour mobile avec gros boutons + et -
    """
    # Vérifier et corriger les valeurs pour éviter les erreurs
    if max_value <= 0:
        st.warning(f"⚠️ Stock insuffisant pour {label.lower()}")
        return 0
    
    # Ajuster la valeur par défaut si elle dépasse le maximum
    if default_value > max_value:
        default_value = max_value
        st.info(f"ℹ️ Quantité ajustée au maximum disponible ({max_value})")
    
    # Ajuster la valeur par défaut si elle est en dessous du minimum
    if default_value < min_value:
        default_value = min_value
    
    # Initialiser la quantité dans la session si elle n'existe pas
    session_key = f"{key_prefix}_quantity"
    if session_key not in st.session_state:
        st.session_state[session_key] = default_value
    
    # Vérifier que la valeur en session est dans les limites
    if st.session_state[session_key] > max_value:
        st.session_state[session_key] = max_value
        st.info(f"ℹ️ Quantité ajustée au stock disponible ({max_value})")
    elif st.session_state[session_key] < min_value:
        st.session_state[session_key] = min_value
    
    st.markdown(f"**{label}**")
    
    # Container pour les boutons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Bouton -
        if st.button("➖", key=f"{key_prefix}_minus", help="Diminuer", use_container_width=True):
            if st.session_state[session_key] > min_value:
                st.session_state[session_key] -= 1
                st.experimental_rerun()
    
    with col2:
        # Affichage de la quantité
        st.markdown(f"""
        <div class="quantity-display">
            {st.session_state[session_key]}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Bouton +
        if st.button("➕", key=f"{key_prefix}_plus", help="Augmenter", use_container_width=True):
            if st.session_state[session_key] < max_value:
                st.session_state[session_key] += 1
                st.experimental_rerun()
            else:
                st.warning(f"⚠️ Maximum atteint ({max_value})")
    
    # Input numérique de secours (plus petit) - seulement si max_value > min_value
    if max_value > min_value:
        with st.expander("✏️ Saisie manuelle"):
            try:
                manual_qty = st.number_input(
                    "Quantité exacte", 
                    min_value=min_value, 
                    max_value=max_value, 
                    value=min(st.session_state[session_key], max_value),
                    key=f"{key_prefix}_manual"
                )
                if manual_qty != st.session_state[session_key]:
                    st.session_state[session_key] = manual_qty
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Erreur de saisie : {str(e)}")
    else:
        st.info(f"ℹ️ Quantité fixe : {max_value}")
    
    return st.session_state[session_key]

# Fonction réutilisable pour la recherche de produits
def rechercher_produit(df, mode="selection"):
    """
    Fonction réutilisable pour rechercher un produit
    Args:
        df: DataFrame contenant les produits
        mode: "selection" pour retourner le produit sélectionné, "affichage" pour afficher les résultats
    Returns:
        produit trouvé (Series) ou None si aucun produit trouvé
    """
    search_type = st.radio("Type de recherche", ["Par référence", "Par nom"])
    
    produit_trouve = None
       
    
    if search_type == "Par référence":
        reference = st.text_input("Entrez la référence du produit")
        if reference:
            result = df[df['Reference'].astype(str) == reference]
            if not result.empty:
                produit_trouve = result.iloc[0]
                if mode == "affichage":
                    st.dataframe(result)
                # else:
                #     st.success(f"Produit trouvé : {produit_trouve['Produits']}")
            else:
                st.warning("Aucun produit trouvé avec cette référence.")
    
    else:  # Par nom
        # Créer une liste des noms de produits uniques pour la liste déroulante
        noms_produits = [""] + sorted(df['Produits'].unique().tolist())
        nom_selectionne = st.selectbox("Sélectionnez le nom du produit", noms_produits)
        
        if nom_selectionne:
            result = df[df['Produits'] == nom_selectionne]
            if not result.empty:
                if mode == "affichage":
                    st.dataframe(result)
                    return None  # Pour la recherche d'affichage, on ne retourne pas de produit spécifique
                elif len(result) == 1:
                    produit_trouve = result.iloc[0]
                    # st.success(f"Produit trouvé : {produit_trouve['Produits']}")
                else:
                    st.info(f"{len(result)} produits trouvés:")
                    st.dataframe(result[['Produits', 'Reference', 'Quantite']])
                    reference_choisie = st.selectbox("Choisissez la référence:", result['Reference'].astype(str).tolist())
                    if reference_choisie:
                        produit_trouve = result[result['Reference'].astype(str) == reference_choisie].iloc[0]
            else:
                st.warning("Aucun produit trouvé avec ce nom.")
    
    return produit_trouve

# Fonction pour vérifier les alertes de stock
def afficher_alertes_stock(df):
    """Affiche les alertes de stock pour les produits en dessous du minimum"""
    if df.empty:
        return
    
    # Produits en dessous du stock minimum (critique)
    alertes_min = df[df['Quantite'] < df['Stock_Min']]
    
    # Produits au-dessus du stock maximum (surstock)
    alertes_max = df[df['Quantite'] > df['Stock_Max']]
    
    # Produits bientôt en rupture (entre min et 30% de la plage min-max)
    seuil_alerte = df['Stock_Min'] + (df['Stock_Max'] - df['Stock_Min']) * 0.3
    alertes_bientot = df[(df['Quantite'] >= df['Stock_Min']) & (df['Quantite'] <= seuil_alerte)]
    
    if not alertes_min.empty or not alertes_max.empty or not alertes_bientot.empty:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚠️ Alertes de Stock")
        
        # Expander pour stock critique (insuffisant)
        if not alertes_min.empty:
            with st.sidebar.expander(f"🔴 Stock critique ({len(alertes_min)})", expanded=False):
                st.markdown("**Réapprovisionnement urgent requis :**")
                for _, produit in alertes_min.iterrows():
                    manquant = produit['Stock_Min'] - produit['Quantite']
                    st.error(f"**{produit['Produits']}**  \n{produit['Quantite']} < {produit['Stock_Min']} (manque {manquant})")
        
        # Expander pour stock faible (bientôt critique)
        if not alertes_bientot.empty:
            with st.sidebar.expander(f"🟠 Stock faible ({len(alertes_bientot)})", expanded=False):
                st.markdown("**Réapprovisionnement recommandé :**")
                for _, produit in alertes_bientot.iterrows():
                    seuil = seuil_alerte.loc[produit.name]
                    st.warning(f"**{produit['Produits']}**  \n{produit['Quantite']} ≤ {seuil:.0f} (seuil d'alerte)")
        
        # Expander pour surstock
        if not alertes_max.empty:
            with st.sidebar.expander(f"🟡 Surstock ({len(alertes_max)})", expanded=False):
                st.markdown("**Stock excessif :**")
                for _, produit in alertes_max.iterrows():
                    excedent = produit['Quantite'] - produit['Stock_Max']
                    st.info(f"**{produit['Produits']}**  \n{produit['Quantite']} > {produit['Stock_Max']} (+{excedent})")

# Chargement initial des données
df = load_data()

# Affichage des alertes de stock dans la sidebar
afficher_alertes_stock(df)

# Section d'aide pour les scanners
st.sidebar.markdown("---")

# Sidebar pour les actions
st.sidebar.title("📱 Navigation")

# Initialiser l'action dans la session si elle n'existe pas
if 'action' not in st.session_state:
    st.session_state.action = "Magasin"

# CSS pour les boutons de navigation mobile
st.sidebar.markdown("""
<style>
    .sidebar .stButton > button {
        height: 3.5rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Section principale - Actions fréquentes
st.sidebar.markdown("### 🎯 **Actions principales**")

if st.sidebar.button("🏪 Magasin", use_container_width=True, help="Vue d'ensemble du stock"):
    st.session_state.action = "Magasin"

if st.sidebar.button("📈 Mouvements", use_container_width=True, help="Historique des mouvements"):
    st.session_state.action = "Historique des mouvements"

if st.sidebar.button("🚨 Alertes stock", use_container_width=True):
    st.session_state.action = "Alertes de stock"

# Section mouvements - Actions courantes
st.sidebar.markdown("---")
st.sidebar.markdown("### 📦 **Demandes**")

if st.sidebar.button("📋 Demande de matériel", use_container_width=True, help="Demander du matériel"):
    st.session_state.action = "Demande de matériel"

if st.sidebar.button("⚙️ Gestion des demandes", use_container_width=True, help="Traiter les demandes"):
    st.session_state.action = "Gestion des demandes"

# Section mouvements - Actions courantes
st.sidebar.markdown("---")
st.sidebar.markdown("### 📦 **Mouvements**")

if st.sidebar.button("📥 Entrée", use_container_width=True, help="Entrée de stock"):
    st.session_state.action = "Entrée de stock"

if st.sidebar.button("📤 Sortie", use_container_width=True, help="Sortie de stock"):
    st.session_state.action = "Sortie de stock"

if st.sidebar.button("📊 Régule", use_container_width=True, help="Ajustement d'inventaire"):
    st.session_state.action = "Régule"
        
if st.sidebar.button("📝 Préparer l'inventaire", use_container_width=True, help="Créer une liste de produits à inventorier"):
    st.session_state.action = "Préparer l'inventaire"

# Section QR Codes - Outils mobiles
# st.sidebar.markdown("---")
# st.sidebar.markdown("### 📱 **QR Codes**")

# if st.sidebar.button("🏭 QR Tables", use_container_width=True, help="QR codes des tables d'atelier"):
#     st.session_state.action = "QR Code tables d'atelier"

# Section administration - Moins fréquent
with st.sidebar.expander("⚙️ **Administration**"):
    if st.button("📦 Gestion Produits", use_container_width=True):
        st.session_state.action = "Gestion des produits"
    
    if st.button("📋 Gestion Tables", use_container_width=True):
        st.session_state.action = "Gérer les tables"
    
    if st.button("🏪 Gestion Fournisseurs", use_container_width=True):
        st.session_state.action = "Fournisseurs"
    
    if st.button("📍 Gestion Emplacements", use_container_width=True):
        st.session_state.action = "Gestion des emplacements"


# Récupérer l'action actuelle
action = st.session_state.action

def get_statut_icon(statut):
    """Retourne l'icône appropriée selon le statut de la demande"""
    if statut == 'En attente':
        return '⏳'
    elif statut == 'Approuvée':
        return '✅'
    elif statut == 'Refusée':
        return '❌'
    else:
        return '📋'  # Icône par défaut

if action == "Magasin":
    st.header("Stock actuel")
    if not df.empty:
        # Ajouter une colonne de statut de stock avec la même logique que les alertes
        df_display = df.copy()
        
        # Calcul du seuil d'alerte (même logique que dans les alertes)
        seuil_alerte = df['Stock_Min'] + (df['Stock_Max'] - df['Stock_Min']) * 0.3
        
        # Calcul de la valeur du stock
        df_display['Valeur_Stock'] = df_display['Quantite'] * df_display['Prix_Unitaire']
        
        df_display['Statut_Stock'] = df_display.apply(
            lambda row: "🔴 Critique" if row['Quantite'] < row['Stock_Min'] 
            else "🟡 Surstock" if row['Quantite'] > row['Stock_Max']
            else "🟠 Bientôt rupture" if row['Quantite'] <= seuil_alerte.loc[row.name]
            else "🟢 Normal", axis=1
        )
        
        # Statistiques rapides
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            alertes_min = len(df[df['Quantite'] < df['Stock_Min']])
            st.metric("Produits en stock critique", alertes_min)
        with col2:
            alertes_bientot = len(df[(df['Quantite'] >= df['Stock_Min']) & (df['Quantite'] <= seuil_alerte)])
            st.metric("Bientôt en rupture", alertes_bientot)
        with col3:
            alertes_max = len(df[df['Quantite'] > df['Stock_Max']])
            st.metric("Produits en surstock", alertes_max)
        with col4:
            stock_normal = len(df[(df['Quantite'] >= df['Stock_Min']) & (df['Quantite'] <= df['Stock_Max']) & (df['Quantite'] > seuil_alerte)])
            st.metric("Produits en stock normal", stock_normal)
        with col5:
            valeur_totale = df_display['Valeur_Stock'].sum()
            st.metric("💰 Valeur totale du stock", f"{valeur_totale:,.2f} €")
            
        # Réorganiser les colonnes pour l'affichage
        colonnes_affichage = ['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Stock_Max', 'Prix_Unitaire', 'Valeur_Stock', 'Statut_Stock', 'Emplacement', 'Fournisseur', 'Date_Entree']
        st.dataframe(df_display[colonnes_affichage].round(2))

        # Graphique de la répartition des stocks
        fig = px.bar(df, x='Produits', y='Quantite', title='Répartition des stocks par produit')
        st.plotly_chart(fig)

    else:
        st.warning("Aucune donnée disponible dans l'inventaire.")

elif action == "Demande de matériel":
    st.header("📋 Demande de Matériel")
    
    if not df.empty:
        # ═══════════════════════════════════════════════════════════════
        # 👤 SECTION 1: IDENTIFICATION DU POSTE DE TRAVAIL
        # ═══════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("🏭 Identification du poste de travail")
        
        # Charger les tables d'atelier
        df_tables = charger_tables_atelier()
        
        # Initialiser les variables de session pour l'identification
        if 'table_identifiee' not in st.session_state:
            st.session_state.table_identifiee = None
        if 'demandeur_auto' not in st.session_state:
            st.session_state.demandeur_auto = ""
        if 'chantier_auto' not in st.session_state:
            st.session_state.chantier_auto = ""
        
        # Mode d'identification
        mode_identification = st.radio(
            "Mode d'identification", 
            ["🔍 Scanner la table d'atelier", "✏️ Saisie manuelle"],
            horizontal=True
        )
        
        if mode_identification == "🔍 Scanner la table d'atelier":
            # st.info("📱 **Scannez le QR code de votre table d'atelier pour vous identifier automatiquement**")
            
            # Scanner pour table d'atelier
            code_table_scanne = st.text_input(
                "🏭 Code de la table d'atelier", 
                placeholder="Scannez le QR code de votre table...",
                help="Le scanner tapera automatiquement le code de votre table",
                key="scanner_table_atelier"
            )
            
            if code_table_scanne:
                code_table_scanne = code_table_scanne.strip().upper()
                
                # Rechercher la table dans la base
                table_trouvee = df_tables[df_tables['ID_Table'] == code_table_scanne]
                
                if not table_trouvee.empty:
                    table_info = table_trouvee.iloc[0]
                    st.session_state.table_identifiee = table_info
                    st.session_state.demandeur_auto = table_info['Responsable']
                    st.session_state.chantier_auto = f"{table_info['Type_Atelier']} - {table_info['Nom_Table']}"
                    
                    # Affichage des informations de la table
                    st.success(f"✅ **Table identifiée : {table_info['Nom_Table']}**")
                    
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.info(f"👤 **Responsable :** {table_info['Responsable']}")
                        st.info(f"🏭 **Type d'atelier :** {table_info['Type_Atelier']}")
                    with col_info2:
                        st.info(f"📍 **Emplacement :** {table_info['Emplacement']}")
                        st.info(f"📅 **Statut :** {table_info['Statut']}")
                    
                    # Variables automatiquement remplies
                    demandeur = st.session_state.demandeur_auto
                    chantier = st.session_state.chantier_auto
                    
                else:
                    st.error(f"❌ Table non trouvée : '{code_table_scanne}'")
                    st.info("💡 Vérifiez que :")
                    st.write("- Le code de la table est correct")
                    st.write("- La table est enregistrée dans le système")
                    st.write("- Le scanner fonctionne correctement")
                    
                    # Fallback vers saisie manuelle
                    demandeur = ""
                    chantier = ""
            else:
                demandeur = ""
                chantier = ""
        
        else:  # Saisie manuelle
            st.session_state.table_identifiee = None
            col1, col2 = st.columns(2)
            with col1:
                demandeur = st.text_input("Nom du demandeur *", placeholder="Prénom NOM")
            with col2:
                chantier = st.text_input("Chantier/Atelier *", placeholder="Nom du chantier ou atelier")
        
        # Initialiser le panier dans la session
        if 'panier_demande' not in st.session_state:
            st.session_state.panier_demande = {}
        
        # Initialiser le compteur pour les clés uniques
        if 'add_counter' not in st.session_state:
            st.session_state.add_counter = 0
        
        # ═══════════════════════════════════════════════════════════════
        # 🛠️ SECTION 2: AJOUT DE PRODUITS
        # ═══════════════════════════════════════════════════════════════
        st.markdown("---")
        st.subheader("🛠️ Ajout de produits")
        
        # Afficher les produits disponibles en stock
        df_disponible = df[df['Quantite'] > 0].copy()
        
        if df_disponible.empty:
            st.warning("Aucun produit en stock actuellement.")
        else:
            # Interface simplifiée de recherche et ajout
            col_search, col_qty, col_add = st.columns([3, 1, 1])
            
            with col_search:
                # Recherche en temps réel
                search_term = st.text_input(
                    "🔍 Rechercher un produit", 
                    placeholder="Tapez le nom ou la référence du produit...",
                    key=f"search_input_{st.session_state.add_counter}"
                )
            
            # Filtrer les produits en fonction de la recherche
            if search_term:
                search_results = df_disponible[
                    df_disponible['Produits'].str.contains(search_term, case=False, na=False) |
                    df_disponible['Reference'].astype(str).str.contains(search_term, case=False, na=False)
                ]
            else:
                search_results = df_disponible
            
            # Afficher les résultats de recherche de manière compacte
            if not search_results.empty and search_term:
                st.write("**Résultats de recherche :**")
                
                # Limiter l'affichage aux 5 premiers résultats pour éviter l'encombrement
                for idx, produit in search_results.head(5).iterrows():
                    # Statut de stock avec couleur
                    if produit['Quantite'] < produit['Stock_Min']:
                        statut_icon = "🔴"
                        statut_text = "Stock critique"
                    elif produit['Quantite'] <= produit['Stock_Min'] + (produit['Stock_Max'] - produit['Stock_Min']) * 0.3:
                        statut_icon = "🟠"
                        statut_text = "Stock faible"
                    else:
                        statut_icon = "🟢"
                        statut_text = "Disponible"
                    
                    # Affichage compact du produit
                    col_prod, col_stock, col_qty_prod, col_add_prod = st.columns([2, 1, 1, 1])
                    
                    with col_prod:
                        st.write(f"**{produit['Produits']}**")
                        st.caption(f"Réf: {produit['Reference']} | {produit['Emplacement']}")
                    
                    with col_stock:
                        st.write(f"{statut_icon} {produit['Quantite']}")
                        st.caption(statut_text)
                    
                    with col_qty_prod:
                        # Interface mobile optimisée pour la quantité
                        qty_key = f"qty_{produit['Reference']}_{st.session_state.add_counter}"
                        
                        # Initialiser la quantité dans la session
                        if qty_key not in st.session_state:
                            st.session_state[qty_key] = 1
                        
                        # Boutons + et - pour mobile
                        col_minus, col_display, col_plus = st.columns([1, 2, 1])
                        
                        with col_minus:
                            if st.button("➖", key=f"{qty_key}_minus", help="Diminuer", use_container_width=True):
                                if st.session_state[qty_key] > 1:
                                    st.session_state[qty_key] -= 1
                                    st.experimental_rerun()
                        
                        with col_display:
                            st.markdown(f"""
                            <div style="text-align: center; font-size: 1.5rem; font-weight: bold; 
                                        background: #f0f2f6; padding: 0.5rem; border-radius: 5px;">
                                {st.session_state[qty_key]}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_plus:
                            if st.button("➕", key=f"{qty_key}_plus", help="Augmenter", use_container_width=True):
                                if st.session_state[qty_key] < int(produit['Quantite']):
                                    st.session_state[qty_key] += 1
                                    st.experimental_rerun()
                        
                        quantite_prod = st.session_state[qty_key]
                    
                    with col_add_prod:
                        add_key = f"add_{produit['Reference']}_{st.session_state.add_counter}"
                        # Bouton différencié pour ajouter au panier
                        if st.button("🛒 Ajouter au panier", key=add_key, help=f"Ajouter {produit['Produits']} au panier", use_container_width=True, type="primary"):
                            st.session_state.panier_demande[produit['Reference']] = {
                                'produit': produit['Produits'],
                                'quantite': quantite_prod,
                                'emplacement': produit['Emplacement']
                            }
                            st.success(f"✅ {quantite_prod} x {produit['Produits']} ajouté(s) au panier")
                            # Incrémenter le compteur pour reset les inputs
                            st.session_state.add_counter += 1
                            st.experimental_rerun()
                    
                    st.divider()
                
                if len(search_results) > 5:
                    st.info(f"+ {len(search_results) - 5} autres produits trouvés. Affinez votre recherche pour plus de précision.")
            
            elif search_term and search_results.empty:
                st.warning(f"Aucun produit trouvé pour '{search_term}'")
            
            # ═══════════════════════════════════════════════════════════════
            # 🛒 SECTION 3: PANIER
            # ═══════════════════════════════════════════════════════════════
            st.markdown("---")
            st.subheader("🛒 Votre panier")
            if st.session_state.panier_demande:
                total_articles = 0
                                               
                # Créer une copie pour éviter les modifications pendant l'itération
                panier_items = list(st.session_state.panier_demande.items())
                
                for ref, item in panier_items:
                    col_item, col_qty, col_location, col_remove = st.columns([2.5, 2, 1, 1])
                    
                    with col_item:
                        st.write(f"**{item['produit']}**")
                        st.caption(f"Réf: {ref}")
                    
                    with col_qty:
                        # Interface mobile pour modifier la quantité dans le panier
                        qty_panier_key = f"panier_qty_{ref}"
                        
                        # Initialiser la quantité si elle n'existe pas
                        if qty_panier_key not in st.session_state:
                            st.session_state[qty_panier_key] = item['quantite']
                        
                        # Vérifier le stock disponible
                        produit_stock = df[df['Reference'] == ref]
                        stock_max_dispo = int(produit_stock.iloc[0]['Quantite']) if not produit_stock.empty else 999
                        
                        # Boutons + et - pour modifier la quantité
                        col_minus_p, col_display_p, col_plus_p = st.columns([1, 2, 1])
                        
                        with col_minus_p:
                            if st.button("➖", key=f"panier_minus_{ref}", help="Diminuer", use_container_width=True):
                                if st.session_state[qty_panier_key] > 1:
                                    st.session_state[qty_panier_key] -= 1
                                    # Mettre à jour le panier
                                    st.session_state.panier_demande[ref]['quantite'] = st.session_state[qty_panier_key]
                                    st.experimental_rerun()
                        
                        with col_display_p:
                            st.markdown(f"""
                            <div style="text-align: center; font-size: 1.2rem; font-weight: bold; 
                                        background: #e8f4fd; padding: 0.3rem; border-radius: 5px; border: 2px solid #1f77b4;">
                                {st.session_state[qty_panier_key]}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_plus_p:
                            if st.button("➕", key=f"panier_plus_{ref}", help="Augmenter", use_container_width=True):
                                if st.session_state[qty_panier_key] < stock_max_dispo:
                                    st.session_state[qty_panier_key] += 1
                                    # Mettre à jour le panier
                                    st.session_state.panier_demande[ref]['quantite'] = st.session_state[qty_panier_key]
                                    st.experimental_rerun()
                                else:
                                    st.warning(f"Stock maximum atteint ({stock_max_dispo})")
                    
                    with col_location:
                        st.write(f"{item['emplacement']}")
                    
                    with col_remove:
                        if st.button(f"🗑️", key=f"remove_{ref}", help="Retirer du panier", use_container_width=True):
                            del st.session_state.panier_demande[ref]
                            # Nettoyer aussi la session de quantité
                            if qty_panier_key in st.session_state:
                                del st.session_state[qty_panier_key]
                            st.experimental_rerun()
                    
                    total_articles += st.session_state[qty_panier_key]
                    
                    st.divider()
                
                # Résumé du panier amélioré
                st.markdown("### 📊 Résumé du panier")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📦 Articles", total_articles)
                with col2:
                    nb_produits = len(st.session_state.panier_demande)
                    st.metric("🛍️ Produits", nb_produits)
                with col3:
                    if st.button("🗑️ Vider", use_container_width=True, help="Vider tout le panier"):
                        # Nettoyer toutes les sessions de quantité du panier
                        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("panier_qty_")]
                        for key in keys_to_remove:
                            del st.session_state[key]
                        st.session_state.panier_demande = {}
                        st.experimental_rerun()
                
                # Affichage compact des produits dans le panier
                if total_articles > 0:
                    st.markdown("**📋 Contenu du panier :**")
                    panier_summary = []
                    for ref, item in st.session_state.panier_demande.items():
                        qty_key = f"panier_qty_{ref}"
                        qty = st.session_state.get(qty_key, item['quantite'])
                        panier_summary.append(f"• {qty}x {item['produit']}")
                    
                    st.markdown("\n".join(panier_summary[:3]))  # Afficher max 3 produits
                    if len(panier_summary) > 3:
                        st.caption(f"... et {len(panier_summary) - 3} autre(s) produit(s)")
            else:
                st.info("Votre panier est vide. Recherchez et ajoutez des produits ci-dessus.")
        
        # ═══════════════════════════════════════════════════════════════
        # 📝 SECTION 4: FINALISATION DE LA DEMANDE
        # ═══════════════════════════════════════════════════════════════
        if st.session_state.panier_demande:
            st.markdown("---")
            st.subheader("📝 Finalisation de la demande")
            
            col1, col2 = st.columns(2)
            with col1:
                urgence = st.radio("Niveau d'urgence", ["Normal", "Urgent", "Très urgent"], index=0)
            with col2:
                date_souhaitee = st.date_input("Date souhaitée", datetime.now().date())
            
            motif = st.text_area(
                "Commentaire (facultatif)", 
                placeholder="Demande de matériel pour le chantier...",
                help="Expliquez pourquoi vous avez besoin de ce matériel"
            )
            
            # Vérifications avant soumission
            if st.button("📤 Soumettre la demande", type="primary", use_container_width=True):
                if not demandeur:
                    st.error("❌ Veuillez saisir votre nom")
                elif not chantier:
                    st.error("❌ Veuillez indiquer le chantier/atelier")
                else:
                    # Préparer les données de la demande
                    demande_data = {
                        'chantier': chantier,
                        'urgence': urgence,
                        'date_souhaitee': date_souhaitee.strftime("%Y-%m-%d"),
                        'produits': st.session_state.panier_demande
                    }
                    
                    # Sauvegarder la demande
                    demande_id = sauvegarder_demande(demandeur, demande_data, motif)
                    
                    # Confirmation
                    st.success(f"✅ Demande soumise avec succès !")
                    st.info(f"**Numéro de demande :** {demande_id}")
                    st.info("Le magasinier traitera votre demande dans les plus brefs délais.")
                    
                    # Vider le panier et reset les compteurs
                    st.session_state.panier_demande = {}
                    st.session_state.add_counter = 0
                    
                    # Afficher un récapitulatif
                    with st.expander("📄 Récapitulatif de votre demande"):
                        st.write(f"**Demandeur :** {demandeur}")
                        st.write(f"**Chantier :** {chantier}")
                        st.write(f"**Urgence :** {urgence}")
                        st.write(f"**Date souhaitée :** {date_souhaitee}")
                        st.write(f"**Motif :** {motif}")
                        st.write("**Produits demandés :**")
                        for ref, item in demande_data['produits'].items():
                            st.write(f"- {item['quantite']} x {item['produit']}")
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Gestion des demandes":
    st.header("📋 Gestion des Demandes de Matériel")
    
    # Charger les demandes
    df_demandes = charger_demandes()
    
    if not df_demandes.empty:
        # Statistiques rapides
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            en_attente = len(df_demandes[df_demandes['Statut'] == 'En attente'])
            st.metric("🕐 En attente", en_attente)
        with col2:
            approuvees = len(df_demandes[df_demandes['Statut'] == 'Approuvée'])
            st.metric("✅ Approuvées", approuvees)
        with col3:
            refusees = len(df_demandes[df_demandes['Statut'] == 'Refusée'])
            st.metric("❌ Refusées", refusees)
        with col4:
            totales = len(df_demandes)
            st.metric("📊 Total", totales)
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            statuts = ["Tous"] + sorted(df_demandes['Statut'].unique().tolist())
            filtre_statut = st.selectbox("Filtrer par statut", statuts, key="filtre_statut_demandes")
        with col2:
            demandeurs = ["Tous"] + sorted(df_demandes['Demandeur'].unique().tolist())
            filtre_demandeur = st.selectbox("Filtrer par demandeur", demandeurs)
        
        # Application des filtres
        df_filtre = df_demandes.copy()
        if filtre_statut != "Tous":
            df_filtre = df_filtre[df_filtre['Statut'] == filtre_statut]
        if filtre_demandeur != "Tous":
            df_filtre = df_filtre[df_filtre['Demandeur'] == filtre_demandeur]
        
        # Tri par date de demande (plus récent en premier)
        df_filtre = df_filtre.sort_values('Date_Demande', ascending=False)
        
        # Affichage des demandes
        for idx, demande in df_filtre.iterrows():
            statut_icon = get_statut_icon(demande['Statut'])
            with st.expander(f"{statut_icon} Demande {demande['ID_Demande']} - {demande['Demandeur']} - {demande['Statut']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**📅 Date de demande :** {demande['Date_Demande']}")
                    st.write(f"**👤 Demandeur :** {demande['Demandeur']}")
                    
                    # Affichage du statut avec icône et couleur
                    if demande['Statut'] == 'En attente':
                        st.warning(f"**{statut_icon} Statut :** {demande['Statut']}")
                    elif demande['Statut'] == 'Approuvée':
                        st.success(f"**{statut_icon} Statut :** {demande['Statut']}")
                    elif demande['Statut'] == 'Refusée':
                        st.error(f"**{statut_icon} Statut :** {demande['Statut']}")
                    else:
                        st.info(f"**{statut_icon} Statut :** {demande['Statut']}")
                    
                    # Vérifier si Date_Traitement n'est pas nan/null
                    if pd.notna(demande['Date_Traitement']) and str(demande['Date_Traitement']).lower() != 'nan':
                        st.write(f"**⏰ Traité le :** {demande['Date_Traitement']}")
                        # Vérifier si Traite_Par n'est pas nan/null
                        if pd.notna(demande['Traite_Par']) and str(demande['Traite_Par']).lower() != 'nan':
                            st.write(f"**👨‍💼 Traité par :** {demande['Traite_Par']}")
                
                with col2:
                    # Vérifier si Motif n'est pas nan/null
                    if pd.notna(demande['Motif']) and str(demande['Motif']).lower() != 'nan':
                        st.write(f"**📝 Motif :** {demande['Motif']}")
                    # Vérifier si Commentaires n'est pas nan/null
                    if pd.notna(demande['Commentaires']) and str(demande['Commentaires']).lower() != 'nan':
                        st.write(f"**💬 Commentaires :** {demande['Commentaires']}")
                
                # Détail des produits demandés
                st.write("**🛠️ Produits demandés :**")
                try:
                    import ast
                    produits_data = ast.literal_eval(demande['Produits_Demandes'])
                    
                    # Affichage des informations additionnelles si disponibles
                    if isinstance(produits_data, dict):
                        if 'chantier' in produits_data and produits_data['chantier'] and str(produits_data['chantier']).lower() != 'nan':
                            st.write(f"**🏗️ Chantier :** {produits_data['chantier']}")
                        if 'urgence' in produits_data and produits_data['urgence'] and str(produits_data['urgence']).lower() != 'nan':
                            st.write(f"**⚡ Urgence :** {produits_data['urgence']}")
                        if 'date_souhaitee' in produits_data and produits_data['date_souhaitee'] and str(produits_data['date_souhaitee']).lower() != 'nan':
                            st.write(f"**📅 Date souhaitée :** {produits_data['date_souhaitee']}")
                        
                        # Affichage des produits
                        if 'produits' in produits_data:
                            produits_list = []
                            for ref, item in produits_data['produits'].items():
                                produits_list.append({
                                    'Référence': ref,
                                    'Produit': item['produit'],
                                    'Quantité': item['quantite'],
                                    'Emplacement': item['emplacement']
                                })
                            
                            df_produits = pd.DataFrame(produits_list)
                            st.dataframe(df_produits)
                            
                            # Vérification de la disponibilité
                            st.write("**📦 Vérification de disponibilité :**")
                            for ref, item in produits_data['produits'].items():
                                produit_stock = df[df['Reference'] == ref]
                                if not produit_stock.empty:
                                    stock_actuel = int(produit_stock.iloc[0]['Quantite'])
                                    stock_min = int(produit_stock.iloc[0]['Stock_Min'])
                                    stock_max = int(produit_stock.iloc[0]['Stock_Max'])
                                    quantite_demandee = item['quantite']
                                    
                                    # Calcul de l'état du stock actuel
                                    if stock_actuel < stock_min:
                                        statut_actuel = "🔴 Stock critique"
                                        couleur_statut = "error"
                                    elif stock_actuel > stock_max:
                                        statut_actuel = "🟡 Surstock"
                                        couleur_statut = "warning"
                                    elif stock_actuel <= stock_min + (stock_max - stock_min) * 0.3:
                                        statut_actuel = "🟠 Stock faible"
                                        couleur_statut = "warning"
                                    else:
                                        statut_actuel = "🟢 Stock normal"
                                        couleur_statut = "success"
                                    
                                    # Calcul de l'état après la demande
                                    stock_apres_demande = stock_actuel - quantite_demandee
                                    if stock_apres_demande < 0:
                                        statut_apres = "❌ Stock insuffisant"
                                        couleur_apres = "error"
                                    elif stock_apres_demande < stock_min:
                                        statut_apres = "🟠 Deviendra critique"
                                        couleur_apres = "error"
                                    elif stock_apres_demande <= stock_min + (stock_max - stock_min) * 0.3:
                                        statut_apres = "🟠 Deviendra faible"
                                        couleur_apres = "warning"
                                    else:
                                        statut_apres = "🟢 Restera normal"
                                        couleur_apres = "success"
                                    
                                    # Affichage avec informations détaillées
                                    with st.container():
                                        st.write(f"**{item['produit']}** (Réf: {ref})")
                                        
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if couleur_statut == "error":
                                                st.error(f"État actuel : {statut_actuel} ({stock_actuel}/{stock_min}-{stock_max})")
                                            elif couleur_statut == "warning":
                                                st.warning(f"État actuel : {statut_actuel} ({stock_actuel}/{stock_min}-{stock_max})")
                                            else:
                                                st.success(f"État actuel : {statut_actuel} ({stock_actuel}/{stock_min}-{stock_max})")
                                        
                                        with col2:
                                            if stock_actuel >= quantite_demandee:
                                                if couleur_apres == "error":
                                                    st.error(f"Après demande : {statut_apres} ({stock_apres_demande})")
                                                elif couleur_apres == "warning":
                                                    st.warning(f"Après demande : {statut_apres} ({stock_apres_demande})")
                                                else:
                                                    st.success(f"Après demande : {statut_apres} ({stock_apres_demande})")
                                            else:
                                                st.error(f"❌ IMPOSSIBLE : {quantite_demandee} demandés mais seulement {stock_actuel} disponible(s)")
                                        
                                        # Recommandations pour le magasinier
                                        if stock_actuel < quantite_demandee:
                                            st.info(f"💡 **Recommandation :** Refuser la demande ou proposer {stock_actuel} unité(s) maximum")
                                        elif stock_apres_demande < stock_min:
                                            st.info(f"💡 **Attention :** Approbation possible mais le stock deviendra critique. Prévoir un réapprovisionnement urgent.")
                                        elif stock_actuel < stock_min:
                                            st.info(f"💡 **Attention :** Stock déjà critique. Approbation déconseillée sans réapprovisionnement.")
                                        
                                        st.divider()
                                else:
                                    st.error(f"⚠️ {item['produit']} : Produit non trouvé dans le stock")
                
                except Exception as e:
                    st.write(demande['Produits_Demandes'])
                
                # Actions pour traiter la demande
                if demande['Statut'] == 'En attente':
                    st.write("**⚙️ Actions :**")
                    
                    # Boutons d'action côte à côte
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("✅ Approuver", key=f"btn_approve_{demande['ID_Demande']}", use_container_width=True):
                            st.session_state[f"action_{demande['ID_Demande']}"] = "approve"
                    
                    with col2:
                        if st.button("❌ Refuser", key=f"btn_refuse_{demande['ID_Demande']}", use_container_width=True):
                            st.session_state[f"action_{demande['ID_Demande']}"] = "refuse"
                    
                    with col3:
                        if st.button("⏸️ Mettre en attente", key=f"btn_hold_{demande['ID_Demande']}", use_container_width=True):
                            st.session_state[f"action_{demande['ID_Demande']}"] = "hold"
                    
                    # Affichage conditionnel des formulaires selon l'action sélectionnée
                    action_key = f"action_{demande['ID_Demande']}"
                    
                    if action_key in st.session_state:
                        st.write("---")
                        
                        if st.session_state[action_key] == "approve":
                            # Formulaire d'approbation
                            with st.form(key=f"form_approve_{demande['ID_Demande']}"):
                                st.write("**✅ Approuver la demande**")
                                magasinier_approve = st.text_input("Votre nom (magasinier)", key=f"mag_approve_{demande['ID_Demande']}")
                                
                                col_submit, col_cancel = st.columns([1, 1])
                                with col_submit:
                                    approve_submitted = st.form_submit_button("✅ Confirmer l'approbation", use_container_width=True)
                                with col_cancel:
                                    if st.form_submit_button("❌ Annuler", use_container_width=True):
                                        del st.session_state[action_key]
                                        st.experimental_rerun()
                                
                                if approve_submitted and magasinier_approve:
                                    # Mettre à jour les stocks
                                    try:
                                        import ast
                                        produits_data = ast.literal_eval(demande['Produits_Demandes'])
                                        if 'produits' in produits_data:
                                            for ref, item in produits_data['produits'].items():
                                                produit_stock = df[df['Reference'] == ref]
                                                if not produit_stock.empty:
                                                    stock_actuel = int(produit_stock.iloc[0]['Quantite'])
                                                    quantite_demandee = item['quantite']
                                                    
                                                    if stock_actuel >= quantite_demandee:
                                                        nouvelle_quantite = stock_actuel - quantite_demandee
                                                        df.loc[df['Reference'] == ref, 'Quantite'] = nouvelle_quantite
                                                        
                                                        # Log du mouvement
                                                        log_mouvement(
                                                            item['produit'],
                                                            f"Sortie - Demande {demande['ID_Demande']}",
                                                            quantite_demandee,
                                                            nouvelle_quantite,
                                                            stock_actuel,
                                                            ref
                                                        )
                                        
                                        # Sauvegarder les stocks mis à jour
                                        save_data(df)
                                        
                                        # Mettre à jour le statut de la demande
                                        mettre_a_jour_demande(demande['ID_Demande'], 'Approuvée', magasinier_approve, "Demande approuvée et stock mis à jour")
                                        
                                        # Nettoyer la session
                                        del st.session_state[action_key]
                                        
                                        st.success("✅ Demande approuvée et stock mis à jour")
                                        st.experimental_rerun()
                                        
                                    except Exception as e:
                                        st.error(f"Erreur lors du traitement : {str(e)}")
                                elif approve_submitted and not magasinier_approve:
                                    st.error("Veuillez saisir votre nom")
                        
                        elif st.session_state[action_key] == "refuse":
                            # Formulaire de refus
                            with st.form(key=f"form_refuse_{demande['ID_Demande']}"):
                                st.write("**❌ Refuser la demande**")
                                magasinier_refuse = st.text_input("Votre nom (magasinier)", key=f"mag_refuse_{demande['ID_Demande']}")
                                motif_refus = st.text_area("Motif du refus", key=f"motif_{demande['ID_Demande']}", placeholder="Expliquez pourquoi cette demande est refusée...")
                                
                                col_submit, col_cancel = st.columns([1, 1])
                                with col_submit:
                                    refuse_submitted = st.form_submit_button("❌ Confirmer le refus", use_container_width=True)
                                with col_cancel:
                                    if st.form_submit_button("❌ Annuler", use_container_width=True):
                                        del st.session_state[action_key]
                                        st.experimental_rerun()
                                
                                if refuse_submitted and magasinier_refuse and motif_refus:
                                    mettre_a_jour_demande(demande['ID_Demande'], 'Refusée', magasinier_refuse, motif_refus)
                                    
                                    # Nettoyer la session
                                    del st.session_state[action_key]
                                    
                                    st.success("❌ Demande refusée")
                                    st.experimental_rerun()
                                elif refuse_submitted:
                                    if not magasinier_refuse:
                                        st.error("Veuillez saisir votre nom")
                                    if not motif_refus:
                                        st.error("Veuillez indiquer le motif du refus")
                        
                        elif st.session_state[action_key] == "hold":
                            # Formulaire de mise en attente
                            with st.form(key=f"form_hold_{demande['ID_Demande']}"):
                                st.write("**⏸️ Mettre en attente**")
                                magasinier_hold = st.text_input("Votre nom (magasinier)", key=f"mag_hold_{demande['ID_Demande']}")
                                commentaire = st.text_area("Commentaire (optionnel)", key=f"comment_{demande['ID_Demande']}", placeholder="Ajoutez un commentaire sur cette mise en attente...")
                                
                                col_submit, col_cancel = st.columns([1, 1])
                                with col_submit:
                                    hold_submitted = st.form_submit_button("⏸️ Confirmer la mise en attente", use_container_width=True)
                                with col_cancel:
                                    if st.form_submit_button("❌ Annuler", use_container_width=True):
                                        del st.session_state[action_key]
                                        st.experimental_rerun()
                                
                                if hold_submitted and magasinier_hold:
                                    mettre_a_jour_demande(demande['ID_Demande'], 'En attente', magasinier_hold, commentaire)
                                    
                                    # Nettoyer la session
                                    del st.session_state[action_key]
                                    
                                    st.success("⏸️ Demande mise à jour")
                                    st.experimental_rerun()
                                elif hold_submitted and not magasinier_hold:
                                    st.error("Veuillez saisir votre nom")
    
    else:
        st.info("Aucune demande de matériel pour le moment.")

elif action == "Gestion des produits":
    st.header("📦 Gestion des Produits")
    
    # Onglets pour différentes actions
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Rechercher", "➕ Ajouter", "✏️ Modifier", "📱 QR Codes"])
    
    with tab1:
        st.subheader("🔍 Rechercher un produit")
        
        produit_trouve = rechercher_produit(df, mode="selection")
        
        # Si un produit est trouvé, afficher les informations détaillées
        if produit_trouve is not None:
            st.markdown("---")
            
            # En-tête avec le nom du produit
            st.subheader(f"📦 {produit_trouve['Produits']}")
            
            # Informations de base en colonnes
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🆔 Référence", produit_trouve['Reference'])
            with col2:
                st.metric("📍 Emplacement", produit_trouve['Emplacement'])
            with col3:
                st.metric("🏪 Fournisseur", produit_trouve['Fournisseur'])
            
            # ═══════════════════════════════════════════════════════════════
            # 📊 SECTION 1: ÉTAT DU STOCK VISUEL
            # ═══════════════════════════════════════════════════════════════
            st.markdown("---")
            st.subheader("📊 État du stock")
            
            quantite_actuelle = int(produit_trouve['Quantite'])
            stock_min = int(produit_trouve['Stock_Min'])
            stock_max = int(produit_trouve['Stock_Max'])
            prix_unitaire = float(produit_trouve['Prix_Unitaire'])
            valeur_stock = quantite_actuelle * prix_unitaire
            
            # Métriques principales
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("📦 Stock actuel", quantite_actuelle)
            with col2:
                st.metric("🔻 Stock minimum", stock_min)
            with col3:
                st.metric("🔺 Stock maximum", stock_max)
            with col4:
                st.metric("💰 Prix unitaire", f"{prix_unitaire:.2f} €")
            with col5:
                st.metric("💎 Valeur stock", f"{valeur_stock:.2f} €")
            
            # Indicateur visuel de l'état du stock
            pourcentage_stock = (quantite_actuelle / stock_max) * 100 if stock_max > 0 else 0
            
            # Déterminer la couleur et le statut
            if quantite_actuelle < stock_min:
                couleur_statut = "#ff4444"  # Rouge
                statut_text = "🔴 STOCK CRITIQUE"
                statut_description = f"Il manque {stock_min - quantite_actuelle} unités pour atteindre le minimum"
            elif quantite_actuelle > stock_max:
                couleur_statut = "#ffaa00"  # Orange
                statut_text = "🟡 SURSTOCK"
                statut_description = f"Excédent de {quantite_actuelle - stock_max} unités au-dessus du maximum"
            elif quantite_actuelle <= stock_min + (stock_max - stock_min) * 0.3:
                couleur_statut = "#ff8800"  # Orange foncé
                statut_text = "🟠 STOCK FAIBLE"
                statut_description = "Réapprovisionnement recommandé prochainement"
            else:
                couleur_statut = "#00aa44"  # Vert
                statut_text = "🟢 STOCK NORMAL"
                statut_description = "Stock dans les limites optimales"
            
            # Affichage du statut avec barre de progression
            st.markdown(f"""
            <div style="background: {couleur_statut}; color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
                <h3 style="margin: 0; color: white;">{statut_text}</h3>
                <p style="margin: 0.5rem 0 0 0; color: white;">{statut_description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Barre de progression visuelle avec repère du stock minimum
            if stock_max > 0:
                progress_value = max(0, min(100, pourcentage_stock))
                min_position = (stock_min / stock_max) * 100
                
                # Barre de progression personnalisée avec repère du minimum
                progress_html = f"""
                <div style="position: relative; width: 100%; height: 15px; background-color: #f0f0f0; border-radius: 15px; margin: 10px 0;">
                    <div style="width: {progress_value}%; height: 100%; background: #2196f3; border-radius: 15px;"></div>
                    <div style="position: absolute; left: {min_position}%; top: -5px; width: 3px; height: 25px; background-color: #333;"></div>
                    <div style="position: absolute; left: {max(0, min_position - 2)}%; top: -25px; font-size: 12px; color: #333; font-weight: bold;">MIN</div>
                    <div style="position: absolute; left: 0; top: 35px; font-size: 11px; color: #666;">0</div>
                    <div style="position: absolute; right: 0; top: 35px; font-size: 11px; color: #666;">{stock_max}</div> 
                    <div style="position: absolute; left: {max(0, min_position - 1)}%; top: 35px; font-size: 11px; color: #333; font-weight: bold;">{stock_min}</div>
                </div>
                """
                st.markdown(progress_html, unsafe_allow_html=True)
                
                st.caption(f"Position dans la plage de stock : {progress_value:.1f}% • Stock actuel : {quantite_actuelle}/{stock_max}")
            
            # ═══════════════════════════════════════════════════════════════
            # 📈 SECTION 2: HISTORIQUE DES MOUVEMENTS
            # ═══════════════════════════════════════════════════════════════
            st.markdown("---")
            st.subheader("📈 Historique des mouvements")
            
            # Charger l'historique pour ce produit
            file_path_hist = "data/historique.xlsx"
            if os.path.exists(file_path_hist):
                try:
                    df_hist = pd.read_excel(file_path_hist, engine='openpyxl')
                    # S'assurer que la colonne Reference existe (pour la compatibilité avec les anciens fichiers)
                    if 'Reference' not in df_hist.columns:
                        df_hist['Reference'] = ""
                    
                    # Convertir la colonne Reference en string pour éviter les séparateurs
                    # Traitement spécial pour éviter les .0 sur les nombres entiers
                    df_hist['Reference'] = df_hist['Reference'].apply(lambda x: 
                        str(int(float(x))) if pd.notna(x) and str(x).replace('.', '').replace('-', '').isdigit() and float(x) == int(float(x))
                        else str(x) if pd.notna(x) and str(x) not in ['nan', 'None', ''] 
                        else ''
                    )
                    
                    # Filtrer pour le produit actuel (par référence si disponible, sinon par nom)
                    if produit_trouve['Reference'] and produit_trouve['Reference'] != "":
                        df_hist_produit = df_hist[df_hist['Reference'] == produit_trouve['Reference']].copy()
                    else:
                        df_hist_produit = df_hist[df_hist['Produit'] == produit_trouve['Produits']].copy()
                    
                    if not df_hist_produit.empty:
                        # Trier par date (plus récent en premier)
                        df_hist_produit = df_hist_produit.sort_values('Date', ascending=False)
                        
                        # Statistiques des mouvements
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            total_mouvements = len(df_hist_produit)
                            st.metric("📊 Total mouvements", total_mouvements)
                        with col2:
                            entrees = len(df_hist_produit[df_hist_produit['Nature'].str.contains('Entrée', na=False)])
                            st.metric("📥 Entrées", entrees)
                        with col3:
                            sorties = len(df_hist_produit[df_hist_produit['Nature'].str.contains('Sortie', na=False)])
                            st.metric("📤 Sorties", sorties)
                        with col4:
                            inventaires = len(df_hist_produit[df_hist_produit['Nature'].str.contains('Inventaire', na=False)])
                            st.metric("📋 Inventaires", inventaires)
                        
                        # Affichage des derniers mouvements
                        st.markdown("**🕒 Derniers mouvements :**")
                        
                        # Limiter à 10 derniers mouvements pour l'affichage
                        df_hist_recent = df_hist_produit.head(10)
                        
                        for idx, mouvement in df_hist_recent.iterrows():
                            # Déterminer l'icône et la couleur selon le type de mouvement
                            if 'Entrée' in mouvement['Nature']:
                                icone = "📥"
                                couleur = "#e8f5e8"
                                couleur_bordure = "#4caf50"
                            elif 'Sortie' in mouvement['Nature']:
                                icone = "📤"
                                couleur = "#fff3e0"
                                couleur_bordure = "#ff9800"
                            elif 'Inventaire' in mouvement['Nature']:
                                icone = "📋"
                                couleur = "#e3f2fd"
                                couleur_bordure = "#2196f3"
                            else:
                                icone = "📊"
                                couleur = "#f5f5f5"
                                couleur_bordure = "#9e9e9e"
                            
                            # Formatage de la date
                            try:
                                date_formatee = pd.to_datetime(mouvement['Date']).strftime("%d/%m/%Y %H:%M")
                            except:
                                date_formatee = str(mouvement['Date'])
                            
                            # Récupérer la référence si disponible
                            reference_mouvement = mouvement.get('Reference', '') if 'Reference' in mouvement else ''
                            reference_text = f"🆔 {reference_mouvement}" if reference_mouvement else ""
                            
                            # Affichage du mouvement
                            st.markdown(f"""
                            <div style="background: {couleur}; border-left: 4px solid {couleur_bordure}; 
                                        padding: 1rem; margin: 0.5rem 0; border-radius: 5px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong>{icone} {mouvement['Nature']}</strong><br>
                                        <span style="color: #666;">📅 {date_formatee}</span>
                                        {f'<br><span style="color: #666; font-size: 0.9em;">{reference_text}</span>' if reference_text else ''}
                                    </div>
                                    <div style="text-align: right;">
                                        <strong>Quantité: {mouvement['Quantite_Mouvement']}</strong><br>
                                        <span style="color: #666;">{mouvement['Quantite_Avant']} → {mouvement['Quantite_Apres']}</span>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Bouton pour voir tout l'historique
                        if len(df_hist_produit) > 10:
                            with st.expander(f"📜 Voir tous les mouvements ({len(df_hist_produit)} au total)"):
                                st.dataframe(df_hist_produit, use_container_width=True)
                        
                        # Graphique des mouvements dans le temps
                        if len(df_hist_produit) > 1:
                            st.markdown("**📈 Évolution du stock :**")
                            
                            # Préparer les données pour le graphique
                            df_graph = df_hist_produit.copy()
                            df_graph['Date'] = pd.to_datetime(df_graph['Date'])
                            df_graph = df_graph.sort_values('Date')
                            
                            # Créer le graphique
                            import plotly.express as px
                            import plotly.graph_objects as go
                            
                            fig = go.Figure()
                            
                            # Ligne du stock
                            fig.add_trace(go.Scatter(
                                x=df_graph['Date'],
                                y=df_graph['Quantite_Apres'],
                                mode='lines+markers',
                                name='Stock',
                                line=dict(color='#1f77b4', width=3),
                                marker=dict(size=8)
                            ))
                            
                            # Lignes de référence
                            fig.add_hline(y=stock_min, line_dash="dash", line_color="red", 
                                         annotation_text="Stock minimum")
                            fig.add_hline(y=stock_max, line_dash="dash", line_color="green", 
                                         annotation_text="Stock maximum")
                            
                            fig.update_layout(
                                title=f"Évolution du stock - {produit_trouve['Produits']}",
                                xaxis_title="Date",
                                yaxis_title="Quantité",
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    else:
                        st.info("📭 Aucun mouvement enregistré pour ce produit")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement de l'historique : {str(e)}")
            else:
                st.info("📭 Aucun historique de mouvements disponible")
            
            # ═══════════════════════════════════════════════════════════════
            # 📱 SECTION 3: QR CODE DU PRODUIT
            # ═══════════════════════════════════════════════════════════════
            st.markdown("---")
            st.subheader("📱 QR Code du produit")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**🔍 Informations d'identification :**")
                st.write(f"**📛 Nom :** {produit_trouve['Produits']}")
                st.write(f"**🆔 Référence :** {produit_trouve['Reference']}")
                st.write(f"**📅 Date d'entrée :** {produit_trouve['Date_Entree']}")
                
                # Bouton pour imprimer/télécharger
                qr = qrcode.QRCode(box_size=8, border=4)
                qr.add_data(produit_trouve['Reference'])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                
                st.download_button(
                    label="💾 Télécharger le QR Code",
                    data=buf.getvalue(),
                    file_name=f"QR_Produit_{produit_trouve['Reference']}.png",
                    mime="image/png",
                    key=f"download_qr_detail_{produit_trouve['Reference']}",
                    use_container_width=True
                )
            
            with col2:
                st.markdown("**📱 QR Code à scanner :**")
                
                # Afficher le QR code
                st.image(buf.getvalue(), caption=f"QR Code - {produit_trouve['Produits']}")
                
    
    with tab2:
        st.subheader("➕ Ajouter des produits")
        
        # Onglets pour différentes méthodes d'ajout
        sub_tab1, sub_tab2 = st.tabs(["➕ Ajout individuel", "📁 Import en masse"])
        
        with sub_tab1:
            st.subheader("➕ Ajouter un produit individuellement")
            
            with st.form("ajout_produit"):
                col1, col2 = st.columns(2)
                
                with col1:
                    produit = st.text_input("Nom du produit *")
                    reference = st.text_input("Référence (code-barres)")
                    quantite = st.number_input("Quantité", min_value=0, value=0)
                    stock_min = st.number_input("Stock minimum", min_value=0, value=10)
                    stock_max = st.number_input("Stock maximum", min_value=1, value=100)
                
                with col2:
                    # Récupérer les emplacements et fournisseurs existants
                    emplacements_existants = df['Emplacement'].dropna().unique().tolist() if not df.empty else []
                    emplacements_defaut = ["Atelier A", "Atelier B", "Stockage", "Magasin", "Zone de réception"]
                    emplacements_tous = list(set(emplacements_existants + emplacements_defaut))
                    
                    fournisseurs_existants = df['Fournisseur'].dropna().unique().tolist() if not df.empty else []
                    fournisseurs_defaut = ["Fournisseur A", "Fournisseur B", "Fournisseur C"]
                    fournisseurs_tous = list(set(fournisseurs_existants + fournisseurs_defaut))
                    
                    emplacement = st.selectbox("Emplacement", emplacements_tous)
                    
                    # Option pour choisir un fournisseur existant ou en créer un nouveau
                    choix_fournisseur = st.radio(
                        "Fournisseur",
                        ["Choisir dans la liste", "Nouveau fournisseur"],
                        horizontal=True
                    )
                    
                    if choix_fournisseur == "Choisir dans la liste":
                        fournisseur = st.selectbox("Sélectionner un fournisseur", fournisseurs_tous)
                    else:
                        fournisseur = st.text_input("Nom du nouveau fournisseur", placeholder="Ex: FournX")
                    
                    prix = st.number_input("Prix unitaire (€)", min_value=0.0, value=0.0, step=0.01)
                    
                    # Champs optionnels
                    reference_fournisseur = st.text_input("Référence fournisseur")
                    unite_stockage = st.text_input("Unité de stockage", value="Unité")
                
                submitted = st.form_submit_button("➕ Ajouter le produit", use_container_width=True)
                
                if submitted:
                    if not produit:
                        st.error("❌ Le nom du produit est obligatoire")
                    elif stock_min >= stock_max:
                        st.error("❌ Le stock minimum doit être inférieur au stock maximum")
                    elif choix_fournisseur == "Nouveau fournisseur" and not fournisseur.strip():
                        st.error("❌ Veuillez saisir le nom du nouveau fournisseur")
                    else:
                        # Générer une référence automatique si non fournie
                        if not reference:
                            reference = generer_reference_qr(produit, produit)
                        
                        # Ajouter automatiquement le fournisseur s'il n'existe pas dans le fichier fournisseurs.xlsx
                        if not ajouter_fournisseur_automatique(fournisseur):
                            st.warning(f"⚠️ Impossible d'ajouter automatiquement le fournisseur '{fournisseur}' au fichier fournisseurs.xlsx")
                        
                        new_row = pd.DataFrame({
                            'Code': [reference],
                            'Reference_Fournisseur': [reference_fournisseur],
                            'Produits': [produit],
                            'Unite_Stockage': [unite_stockage],
                            'Unite_Commande': [unite_stockage],
                            'Stock_Min': [stock_min],
                            'Stock_Max': [stock_max],
                            'Site': ['Site principal'],
                            'Lieu': [emplacement],
                            'Emplacement': [emplacement],
                            'Fournisseur': [fournisseur],
                            'Prix_Unitaire': [prix],
                            'Categorie': ['Général'],
                            'Secteur': ['Général'],
                            'Reference': [reference],
                            'Quantite': [quantite],
                            'Date_Entree': [datetime.now().strftime("%Y-%m-%d")]
                        })
                        
                        df = pd.concat([df, new_row], ignore_index=True)
                        save_data(df)
                        log_mouvement(produit, "Ajout produit", quantite, quantite, 0, reference)
                        
                        # Mettre à jour les statistiques des fournisseurs après l'ajout du produit
                        mettre_a_jour_statistiques_fournisseurs()
                        
                        st.success(f"✅ Produit '{produit}' ajouté avec succès!")
                        if fournisseur not in df['Fournisseur'].dropna().unique().tolist()[:-1]:  # Si c'est un nouveau fournisseur
                            st.info(f"ℹ️ Le fournisseur '{fournisseur}' a été automatiquement ajouté au fichier fournisseurs.xlsx")
                        st.experimental_rerun()
        
        with sub_tab2:
            st.subheader("📁 Import en masse de produits")
            
            # Instructions et modèle
            st.markdown("### 📋 Instructions")
            st.info("""
            **Format de fichier accepté :** CSV ou Excel (.xlsx)
            
            **Colonnes requises :**
            - `Désignation` : Nom du produit (obligatoire)
            
            **Colonnes recommandées :**
            - `Code` : Code du produit
            - `Référence fournisseur` : Référence chez le fournisseur
            - `Unité de stockage` : Unité de stockage (ex: Unité, Kg, Mètre)
            - `Unite Commande` : Unité de commande
            - `Min` : Stock minimum
            - `Max` : Stock maximum
            - `Site` : Site de stockage
            - `Lieu` : Lieu de stockage
            - `Emplacement` : Emplacement précis
            - `Fournisseur Standard` : Nom du fournisseur
            - `Prix` : Prix unitaire en euros
            - `Catégorie` : Catégorie du produit
            - `Secteur` : Secteur d'activité
            
                     **Colonnes optionnelles :**
             - `Quantite` : Quantité en stock (défaut: 0 si vide)
            
            💡 **Note :** Les noms de colonnes correspondent exactement au fichier Excel original
            """)
            
            # Télécharger le modèle
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📥 Télécharger le modèle")
                
                # Créer un fichier modèle basé sur les vraies colonnes du fichier Excel
                modele_data = {
                    'Code': ['VIS001', 'JOINT002', 'ALU003'],
                    'Référence fournisseur': ['VP-4040', 'EP-JOINT01', 'AE-PROF2M'],
                    'Désignation': ['Vis inox 4x40', 'Joint étanchéité', 'Profilé aluminium 2m'],
                    'Unité de stockage': ['Unité', 'Unité', 'Mètre'],
                    'Unite Commande': ['Boîte de 100', 'Unité', 'Barre de 6m'],
                    'Min': [20, 10, 5],
                    'Max': [200, 100, 50],
                    'Site': ['Site principal', 'Site principal', 'Site principal'],
                    'Lieu': ['Atelier A', 'Magasin', 'Stockage'],
                    'Emplacement': ['Étagère A1', 'Armoire B2', 'Rack C3'],
                    'Fournisseur Standard': ['Visserie Pro', 'Étanchéité Plus', 'Alu Expert'],
                    'Prix': [0.15, 2.50, 45.00],
                    'Catégorie': ['Visserie', 'Étanchéité', 'Profilés'],
                    'Secteur': ['Fixation', 'Étanchéité', 'Structure'],
                    'Quantite': [100, 50, 25]
                }
                
                df_modele = pd.DataFrame(modele_data)
                
                # Boutons de téléchargement du modèle
                csv_modele = df_modele.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📄 Télécharger modèle CSV",
                    data=csv_modele,
                    file_name="modele_import_produits.csv",
                    mime="text/csv",
                    key="download_modele_csv",
                    use_container_width=True
                )
                
                # Créer un fichier Excel pour le modèle
                from io import BytesIO
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_modele.to_excel(writer, index=False, sheet_name='Produits')
                
                st.download_button(
                    label="📊 Télécharger modèle Excel",
                    data=excel_buffer.getvalue(),
                    file_name="modele_import_produits.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_modele_excel",
                    use_container_width=True
                )
            
            with col2:
                st.markdown("### 📤 Importer votre fichier")
                
                # Upload du fichier
                uploaded_file = st.file_uploader(
                    "Choisissez votre fichier",
                    type=['csv', 'xlsx'],
                    help="Formats acceptés : CSV, Excel (.xlsx)"
                )
                
                if uploaded_file is not None:
                    try:
                        # Lire le fichier selon son type
                        if uploaded_file.name.endswith('.csv'):
                            df_import = pd.read_csv(uploaded_file, encoding='utf-8')
                        else:
                            df_import = pd.read_excel(uploaded_file, engine='openpyxl')
                        
                        st.success(f"✅ Fichier lu avec succès : {len(df_import)} ligne(s)")
                        
                        # Vérification des colonnes obligatoires (basées sur le fichier Excel original)
                        colonnes_obligatoires = ['Désignation']
                        colonnes_manquantes = [col for col in colonnes_obligatoires if col not in df_import.columns]
                        
                        if colonnes_manquantes:
                            st.error(f"❌ Colonnes manquantes : {', '.join(colonnes_manquantes)}")
                        else:
                            # Prévisualisation des données
                            st.markdown("### 👀 Prévisualisation des données")
                            st.dataframe(df_import.head(10), use_container_width=True)
                            
                            if len(df_import) > 10:
                                st.caption(f"Affichage des 10 premières lignes sur {len(df_import)} au total")
                            
                            # Validation des données
                            st.markdown("### ✅ Validation des données")
                            
                            erreurs = []
                            avertissements = []
                            
                            # Vérifier les désignations vides
                            designations_vides = df_import['Désignation'].isna().sum()
                            if designations_vides > 0:
                                erreurs.append(f"❌ {designations_vides} ligne(s) avec désignation vide")
                            
                            # Vérifier les doublons de désignations
                            doublons = df_import['Désignation'].duplicated().sum()
                            if doublons > 0:
                                avertissements.append(f"⚠️ {doublons} désignation(s) en doublon dans le fichier")
                            
                            # Vérifier les stocks min/max (colonnes du fichier Excel original)
                            if 'Min' in df_import.columns and 'Max' in df_import.columns:
                                stocks_invalides = (df_import['Min'] >= df_import['Max']).sum()
                                if stocks_invalides > 0:
                                    erreurs.append(f"❌ {stocks_invalides} ligne(s) avec stock minimum >= stock maximum")
                            
                            # Vérifier les quantités négatives
                            if 'Quantite' in df_import.columns:
                                quantites_negatives = (df_import['Quantite'] < 0).sum()
                                if quantites_negatives > 0:
                                    erreurs.append(f"❌ {quantites_negatives} ligne(s) avec quantité négative")
                            
                            # Vérifier les prix négatifs (colonne Prix du fichier Excel original)
                            if 'Prix' in df_import.columns:
                                prix_negatifs = (df_import['Prix'] < 0).sum()
                                if prix_negatifs > 0:
                                    erreurs.append(f"❌ {prix_negatifs} ligne(s) avec prix négatif")
                            
                            # Afficher les erreurs et avertissements
                            if erreurs:
                                for erreur in erreurs:
                                    st.error(erreur)
                            
                            if avertissements:
                                for avertissement in avertissements:
                                    st.warning(avertissement)
                            
                            if not erreurs:
                                st.success("✅ Toutes les validations sont passées")
                                
                                # Options d'import
                                st.markdown("### ⚙️ Options d'import")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    mode_import = st.radio(
                                        "Mode d'import",
                                        ["Ajouter uniquement", "Mettre à jour si existe"],
                                        help="Ajouter uniquement : ignore les produits existants\nMettre à jour : met à jour les produits existants"
                                    )
                                
                                with col2:
                                    generer_references = st.checkbox(
                                        "Générer automatiquement les références manquantes",
                                        value=True,
                                        help="Génère des références uniques pour les produits qui n'en ont pas"
                                    )
                                
                                # Bouton d'import
                                if st.button("📥 Importer les produits", type="primary", use_container_width=True):
                                    try:
                                        # Préparer les données pour l'import
                                        df_import_clean = df_import.copy()
                                        
                                        # Appliquer le mapping des colonnes du fichier Excel vers les colonnes internes
                                        column_mapping = {
                                            'Code': 'Code',
                                            'Référence fournisseur': 'Reference_Fournisseur', 
                                            'Désignation': 'Produits',
                                            'Unité de stockage': 'Unite_Stockage',
                                            'Unite Commande': 'Unite_Commande',
                                            'Min': 'Stock_Min',
                                            'Max': 'Stock_Max',
                                            'Site': 'Site',
                                            'Lieu': 'Lieu',
                                            'Emplacement': 'Emplacement',
                                            'Fournisseur Standard': 'Fournisseur',
                                            'Prix': 'Prix_Unitaire',
                                            'Catégorie': 'Categorie',
                                            'Secteur': 'Secteur'
                                        }
                                        
                                        # Renommer les colonnes selon le mapping
                                        df_import_clean = df_import_clean.rename(columns=column_mapping)
                                        
                                        # Remplir les colonnes manquantes avec des valeurs par défaut
                                        colonnes_defaut = {
                                            'Code': '',
                                            'Reference_Fournisseur': '',
                                            'Produits': '',
                                            'Unite_Stockage': 'Unité',
                                            'Unite_Commande': 'Unité',
                                            'Stock_Min': 10,
                                            'Stock_Max': 100,
                                            'Site': 'Site principal',
                                            'Lieu': 'Magasin',
                                            'Emplacement': 'Magasin',
                                            'Fournisseur': 'À définir',
                                            'Prix_Unitaire': 0.0,
                                            'Categorie': 'Général',
                                            'Secteur': 'Général',
                                            'Quantite': 0
                                        }
                                        
                                        for col, valeur_defaut in colonnes_defaut.items():
                                            if col not in df_import_clean.columns:
                                                df_import_clean[col] = valeur_defaut
                                            else:
                                                df_import_clean[col] = df_import_clean[col].fillna(valeur_defaut)
                                        
                                        # Générer les codes et références si nécessaire
                                        for idx, row in df_import_clean.iterrows():
                                            # Si pas de code, utiliser la désignation pour en générer un
                                            if pd.isna(row['Code']) or row['Code'] == '':
                                                df_import_clean.loc[idx, 'Code'] = row['Produits'][:10].upper().replace(' ', '')
                                        
                                        # Générer les références pour les QR codes
                                        if 'Reference' not in df_import_clean.columns or generer_references:
                                            if 'Reference' not in df_import_clean.columns:
                                                df_import_clean['Reference'] = ''
                                            
                                            for idx, row in df_import_clean.iterrows():
                                                if pd.isna(row['Reference']) or row['Reference'] == '':
                                                    df_import_clean.loc[idx, 'Reference'] = generer_reference_qr(row['Code'], row['Produits'])
                                        
                                        # Ajouter les colonnes système
                                        df_import_clean['Date_Entree'] = datetime.now().strftime("%Y-%m-%d")
                                        
                                        # S'assurer que Lieu est défini
                                        if 'Lieu' not in df_import_clean.columns or df_import_clean['Lieu'].isna().all():
                                            df_import_clean['Lieu'] = df_import_clean['Emplacement']
                                        
                                        # Statistiques d'import
                                        produits_ajoutes = 0
                                        produits_mis_a_jour = 0
                                        produits_ignores = 0
                                        
                                        # Ajouter automatiquement tous les nouveaux fournisseurs avant l'import
                                        fournisseurs_uniques = df_import_clean['Fournisseur'].dropna().unique()
                                        nouveaux_fournisseurs = []
                                        for fournisseur in fournisseurs_uniques:
                                            if fournisseur and fournisseur.strip() and fournisseur != 'À définir':
                                                if ajouter_fournisseur_automatique(fournisseur):
                                                    # Vérifier si c'était vraiment un nouveau fournisseur
                                                    df_fournisseurs_temp = charger_fournisseurs()
                                                    if fournisseur in df_fournisseurs_temp['Nom_Fournisseur'].values:
                                                        # Compter seulement si ce n'était pas déjà dans la liste
                                                        if fournisseur not in [f for f in df['Fournisseur'].dropna().unique() if f]:
                                                            nouveaux_fournisseurs.append(fournisseur)
                                        
                                        # Barre de progression
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        
                                        for idx, row in df_import_clean.iterrows():
                                            # Mise à jour de la progression
                                            progress = (idx + 1) / len(df_import_clean)
                                            progress_bar.progress(progress)
                                            status_text.text(f"Traitement en cours... {idx + 1}/{len(df_import_clean)}")
                                            
                                            # Vérifier si le produit existe déjà
                                            produit_existant = df[df['Produits'] == row['Produits']]
                                            
                                            if not produit_existant.empty and mode_import == "Mettre à jour si existe":
                                                # Mettre à jour le produit existant
                                                for col in df_import_clean.columns:
                                                    if col in df.columns:
                                                        df.loc[df['Produits'] == row['Produits'], col] = row[col]
                                                produits_mis_a_jour += 1
                                                
                                                # Log du mouvement si la quantité a changé
                                                ancienne_quantite = produit_existant.iloc[0]['Quantite']
                                                nouvelle_quantite = row['Quantite']
                                                if ancienne_quantite != nouvelle_quantite:
                                                    log_mouvement(
                                                        row['Produits'],
                                                        "Import - Mise à jour",
                                                        abs(nouvelle_quantite - ancienne_quantite),
                                                        nouvelle_quantite,
                                                        ancienne_quantite,
                                                        row['Reference']
                                                    )
                                            
                                            elif produit_existant.empty:
                                                # Ajouter le nouveau produit
                                                new_row = pd.DataFrame([row])
                                                df = pd.concat([df, new_row], ignore_index=True)
                                                produits_ajoutes += 1
                                                
                                                # Log du mouvement
                                                if row['Quantite'] > 0:
                                                    log_mouvement(
                                                        row['Produits'],
                                                        "Import - Nouveau produit",
                                                        row['Quantite'],
                                                        row['Quantite'],
                                                        0,
                                                        row['Reference']
                                                    )
                                            else:
                                                # Produit existant mais mode "Ajouter uniquement"
                                                produits_ignores += 1
                                        
                                        # Sauvegarder les données
                                        save_data(df)
                                        
                                        # Mettre à jour les statistiques des fournisseurs après l'import
                                        mettre_a_jour_statistiques_fournisseurs()
                                        
                                        # Finalisation
                                        progress_bar.progress(1.0)
                                        status_text.text("✅ Import terminé !")
                                        
                                        # Afficher le résumé
                                        st.success("🎉 Import terminé avec succès !")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("➕ Produits ajoutés", produits_ajoutes)
                                        with col2:
                                            st.metric("🔄 Produits mis à jour", produits_mis_a_jour)
                                        with col3:
                                            st.metric("⏭️ Produits ignorés", produits_ignores)
                                        
                                        # Afficher les nouveaux fournisseurs ajoutés
                                        if nouveaux_fournisseurs:
                                            st.info(f"🏪 {len(nouveaux_fournisseurs)} nouveau(x) fournisseur(s) ajouté(s) automatiquement : {', '.join(nouveaux_fournisseurs)}")
                                        
                                        st.experimental_rerun()
                                        
                                    except Exception as e:
                                        st.error(f"❌ Erreur lors de l'import : {str(e)}")
                            else:
                                st.error("❌ Veuillez corriger les erreurs avant de procéder à l'import")
                    
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la lecture du fichier : {str(e)}")
                        st.info("💡 Vérifiez que votre fichier respecte le format attendu")
    
    with tab3:
        st.subheader("✏️ Modifier un produit")
        
        if not df.empty:
            produit_to_edit = st.selectbox("Sélectionner le produit à modifier", df['Produits'].unique())
            produit_data = df[df['Produits'] == produit_to_edit].iloc[0]
            
            # Affichage des informations actuelles du produit
            st.markdown("### 📋 Informations actuelles")
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.info(f"**📦 Quantité actuelle :** {produit_data['Quantite']}")
                st.info(f"**📍 Emplacement :** {produit_data['Emplacement']}")
            with col_info2:
                st.info(f"**🔻 Stock min :** {produit_data['Stock_Min']}")
                st.info(f"**🔺 Stock max :** {produit_data['Stock_Max']}")
            with col_info3:
                st.info(f"**🏪 Fournisseur :** {produit_data['Fournisseur']}")
                st.info(f"**💰 Prix :** {produit_data['Prix_Unitaire']} €")
            
            st.markdown("---")
            
            with st.form("modifier_produit"):
                st.markdown("### ✏️ Modifications")
                
                # Première ligne : Quantité et Prix
                col1, col2 = st.columns(2)
                with col1:
                    quantite = st.number_input("Nouvelle quantité", value=int(produit_data['Quantite']), min_value=0)
                with col2:
                    prix_unitaire = st.number_input("Prix unitaire (€)", value=float(produit_data['Prix_Unitaire']), min_value=0.0, step=0.01)
                
                # Deuxième ligne : Stock min et max
                col1, col2 = st.columns(2)
                with col1:
                    stock_min = st.number_input("Stock minimum", min_value=0, value=int(produit_data['Stock_Min']))
                with col2:
                    stock_max = st.number_input("Stock maximum", min_value=1, value=int(produit_data['Stock_Max']))
                
                # Troisième ligne : Emplacement et Fournisseur
                col1, col2 = st.columns(2)
                with col1:
                    # Liste des emplacements existants
                    emplacements_existants = sorted(df['Emplacement'].dropna().unique().tolist())
                    try:
                        emplacement_index = emplacements_existants.index(produit_data['Emplacement'])
                    except ValueError:
                        emplacement_index = 0
                    
                    emplacement = st.selectbox(
                        "Nouvel emplacement", 
                        emplacements_existants, 
                        index=emplacement_index
                    )
                
                with col2:
                    # Liste des fournisseurs existants
                    fournisseurs_existants = sorted(df['Fournisseur'].dropna().unique().tolist())
                    try:
                        fournisseur_index = fournisseurs_existants.index(produit_data['Fournisseur'])
                    except ValueError:
                        fournisseur_index = 0
                    
                    fournisseur = st.selectbox(
                        "Nouveau fournisseur", 
                        fournisseurs_existants, 
                        index=fournisseur_index,
                        help="Sélectionnez un fournisseur existant dans la liste"
                    )
                
                # Champs optionnels supplémentaires
                with st.expander("🔧 Paramètres avancés (optionnel)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        reference_fournisseur = st.text_input(
                            "Référence fournisseur", 
                            value=produit_data.get('Reference_Fournisseur', ''),
                            help="Référence du produit chez le fournisseur"
                        )
                        unite_stockage = st.text_input(
                            "Unité de stockage", 
                            value=produit_data.get('Unite_Stockage', 'Unité')
                        )
                    with col2:
                        categorie = st.text_input(
                            "Catégorie", 
                            value=produit_data.get('Categorie', 'Général')
                        )
                        secteur = st.text_input(
                            "Secteur", 
                            value=produit_data.get('Secteur', 'Général')
                        )
                
                submitted = st.form_submit_button("✅ Mettre à jour le produit", type="primary", use_container_width=True)
                
                if submitted:
                    if stock_min >= stock_max:
                        st.error("❌ Le stock minimum doit être inférieur au stock maximum")
                    else:
                        # Ajouter automatiquement le fournisseur s'il n'existe pas dans le fichier fournisseurs.xlsx
                        if not ajouter_fournisseur_automatique(fournisseur):
                            st.warning(f"⚠️ Impossible d'ajouter automatiquement le fournisseur '{fournisseur}' au fichier fournisseurs.xlsx")
                        
                        # Mettre à jour toutes les informations
                        df.loc[df['Produits'] == produit_to_edit, 'Quantite'] = quantite
                        df.loc[df['Produits'] == produit_to_edit, 'Stock_Min'] = stock_min
                        df.loc[df['Produits'] == produit_to_edit, 'Stock_Max'] = stock_max
                        df.loc[df['Produits'] == produit_to_edit, 'Emplacement'] = emplacement
                        df.loc[df['Produits'] == produit_to_edit, 'Fournisseur'] = fournisseur
                        df.loc[df['Produits'] == produit_to_edit, 'Prix_Unitaire'] = prix_unitaire
                        
                        # Mettre à jour les champs optionnels s'ils existent
                        if 'Reference_Fournisseur' in df.columns:
                            df.loc[df['Produits'] == produit_to_edit, 'Reference_Fournisseur'] = reference_fournisseur
                        if 'Unite_Stockage' in df.columns:
                            df.loc[df['Produits'] == produit_to_edit, 'Unite_Stockage'] = unite_stockage
                        if 'Categorie' in df.columns:
                            df.loc[df['Produits'] == produit_to_edit, 'Categorie'] = categorie
                        if 'Secteur' in df.columns:
                            df.loc[df['Produits'] == produit_to_edit, 'Secteur'] = secteur
                        
                        # Enregistrer les modifications et logger si la quantité a changé
                        ancienne_quantite = int(produit_data['Quantite'])
                        if quantite != ancienne_quantite:
                            log_mouvement(
                                produit_to_edit,
                                "Modification - Ajustement quantité",
                                abs(quantite - ancienne_quantite),
                                quantite,
                                ancienne_quantite,
                                produit_data['Reference']
                            )
                        
                        save_data(df)
                        
                        # Mettre à jour les statistiques des fournisseurs après la modification
                        mettre_a_jour_statistiques_fournisseurs()
                        
                        st.success("✅ Produit mis à jour avec succès!")
                        
                        # Afficher un résumé des modifications
                        with st.expander("📄 Résumé des modifications"):
                            modifications = []
                            if quantite != ancienne_quantite:
                                modifications.append(f"📦 Quantité : {ancienne_quantite} → {quantite}")
                            if stock_min != int(produit_data['Stock_Min']):
                                modifications.append(f"🔻 Stock min : {produit_data['Stock_Min']} → {stock_min}")
                            if stock_max != int(produit_data['Stock_Max']):
                                modifications.append(f"🔺 Stock max : {produit_data['Stock_Max']} → {stock_max}")
                            if emplacement != produit_data['Emplacement']:
                                modifications.append(f"📍 Emplacement : {produit_data['Emplacement']} → {emplacement}")
                            if fournisseur != produit_data['Fournisseur']:
                                modifications.append(f"🏪 Fournisseur : {produit_data['Fournisseur']} → {fournisseur}")
                            if prix_unitaire != float(produit_data['Prix_Unitaire']):
                                modifications.append(f"💰 Prix : {produit_data['Prix_Unitaire']} € → {prix_unitaire} €")
                            
                            if modifications:
                                for modif in modifications:
                                    st.write(f"• {modif}")
                            else:
                                st.info("Aucune modification détectée")
                        
                        st.experimental_rerun()
        else:
            st.warning("Aucun produit disponible pour modification.")
    
    with tab4:
        st.subheader("📱 QR Code des Produits")
        
        if not df.empty:
            # Onglets pour différentes options
            sub_tab1, sub_tab2 = st.tabs(["🔍 QR Code individuel", "📦 Tous les QR codes"])
            
            with sub_tab1:
                
                produit_select = st.selectbox("Sélectionnez un produit", df['Produits'].unique(), key="qr_individual")
                produit_info = df[df['Produits'] == produit_select].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 Informations du produit")
                    st.write(f"**📛 Nom :** {produit_info['Produits']}")
                    st.write(f"**🆔 Référence :** {produit_info['Reference']}")
                    st.write(f"**📦 Quantité :** {produit_info['Quantite']}")
                    st.write(f"**📍 Emplacement :** {produit_info['Emplacement']}")
                    st.write(f"**🏪 Fournisseur :** {produit_info['Fournisseur']}")
                    st.write(f"**💰 Prix unitaire :** {produit_info['Prix_Unitaire']} €")
                
                with col2:
                    st.subheader("📱 QR Code")
                    
                    # Génération du QR code
                    qr = qrcode.QRCode(box_size=8, border=4)
                    qr.add_data(produit_info['Reference'])
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    
                    # Afficher le QR code
                    st.image(buf.getvalue(), caption=f"QR Code pour {produit_info['Produits']}")
                    
                    # Bouton de téléchargement
                    st.download_button(
                        label="💾 Télécharger le QR Code",
                        data=buf.getvalue(),
                        file_name=f"QR_Produit_{produit_info['Reference']}.png",
                        mime="image/png",
                        key=f"download_qr_individual_{produit_info['Reference']}",
                        use_container_width=True
                    )
            
            with sub_tab2:
                st.subheader("📦 Génération de tous les QR codes")
                
                # Filtres pour sélectionner les produits
                col1, col2, col3 = st.columns(3)
                with col1:
                    emplacements = ["Tous"] + sorted(df['Emplacement'].unique().tolist())
                    filtre_emplacement = st.selectbox("Filtrer par emplacement", emplacements)
                with col2:
                    fournisseurs = ["Tous"] + sorted(df['Fournisseur'].unique().tolist())
                    filtre_fournisseur = st.selectbox("Filtrer par fournisseur", fournisseurs)
                with col3:
                    # Filtre par stock (produits en stock uniquement)
                    stock_uniquement = st.checkbox("Produits en stock uniquement", value=False)
                
                # Application des filtres
                df_filtre = df.copy()
                if filtre_emplacement != "Tous":
                    df_filtre = df_filtre[df_filtre['Emplacement'] == filtre_emplacement]
                if filtre_fournisseur != "Tous":
                    df_filtre = df_filtre[df_filtre['Fournisseur'] == filtre_fournisseur]
                if stock_uniquement:
                    df_filtre = df_filtre[df_filtre['Quantite'] > 0]
                
                # Affichage du nombre de produits sélectionnés
                st.info(f"📊 **{len(df_filtre)} produit(s) sélectionné(s)** pour la génération de QR codes")
                
                if len(df_filtre) > 0:
                    # Options d'affichage
                    col1, col2 = st.columns(2)
                    with col1:
                        taille_qr = st.selectbox("Taille des QR codes", ["Petit (4)", "Moyen (6)", "Grand (8)"], index=1, key="taille_qr_produits")
                        box_size = {"Petit (4)": 4, "Moyen (6)": 6, "Grand (8)": 8}[taille_qr]
                    with col2:
                        colonnes_par_ligne = st.selectbox("QR codes par ligne", [2, 3, 4, 5], index=1, key="colonnes_qr_produits")
                    
                    # Bouton pour générer tous les QR codes
                    if st.button("📱 Générer tous les QR codes", use_container_width=True, type="primary"):
                        st.subheader("📱 QR codes de tous les produits sélectionnés")
                        
                        # Barre de progression
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Créer une grille pour afficher tous les QR codes
                        for i in range(0, len(df_filtre), colonnes_par_ligne):
                            cols = st.columns(colonnes_par_ligne)
                            
                            for j in range(colonnes_par_ligne):
                                if i + j < len(df_filtre):
                                    produit_row = df_filtre.iloc[i + j]
                                    
                                    # Mise à jour de la barre de progression
                                    progress = (i + j + 1) / len(df_filtre)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Génération en cours... {i + j + 1}/{len(df_filtre)}")
                                    
                                    with cols[j]:
                                        # Générer le QR code
                                        qr = qrcode.QRCode(box_size=box_size, border=2)
                                        qr.add_data(produit_row['Reference'])
                                        qr.make(fit=True)
                                        img = qr.make_image(fill_color="black", back_color="white")
                                        buf = BytesIO()
                                        img.save(buf, format="PNG")
                                        
                                        # Afficher avec informations
                                        st.image(buf.getvalue(), caption=f"{produit_row['Produits']}\nRéf: {produit_row['Reference']}")
                                        
                                        # Bouton de téléchargement individuel
                                        st.download_button(
                                            label=f"💾 {produit_row['Reference']}",
                                            data=buf.getvalue(),
                                            file_name=f"QR_Produit_{produit_row['Reference']}.png",
                                            mime="image/png",
                                            key=f"download_produit_{produit_row['Reference']}",
                                            use_container_width=True
                                        )
                        
                        # Finalisation
                        progress_bar.progress(1.0)
                        status_text.text("✅ Génération terminée !")
                        st.success(f"🎉 **{len(df_filtre)} QR codes générés avec succès !**")
                        
        else:
            st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Entrée de stock":
    st.header("Entrée de stock")
    if not df.empty:
        produit_trouve = rechercher_produit(df)
        
        # Affichage du formulaire d'entrée si un produit est trouvé
        if produit_trouve is not None:
            st.divider()
            st.subheader(f"Entrée de stock - {produit_trouve['Produits']}")
            st.write(f"**Référence :** {produit_trouve['Reference']}")
            st.write(f"**Emplacement :** {produit_trouve['Emplacement']}")
            quantite_actuelle = int(produit_trouve['Quantite'])
            stock_min = int(produit_trouve['Stock_Min'])
            stock_max = int(produit_trouve['Stock_Max'])
            
            # Affichage du statut de stock avec couleurs
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quantité actuelle", quantite_actuelle)
            with col2:
                st.metric("Stock minimum", stock_min)
            with col3:
                st.metric("Stock maximum", stock_max)
            
            # Indicateur de statut
            if quantite_actuelle < stock_min:
                st.error(f"⚠️ Stock critique ! Il manque {stock_min - quantite_actuelle} unités pour atteindre le minimum.")
                quantite_recommandee = stock_max - quantite_actuelle
                st.info(f"💡 Recommandation : ajouter {quantite_recommandee} unités pour atteindre le stock maximum.")
            elif quantite_actuelle > stock_max:
                st.warning(f"🟡 Surstock ! {quantite_actuelle - stock_max} unités au-dessus du maximum.")
            else:
                st.success("✅ Stock dans les limites normales.")
            
            # Interface mobile optimisée pour la quantité
            st.markdown("### 📦 Quantité à ajouter")
            quantite_ajout = mobile_quantity_selector(
                "Quantité à ajouter au stock", 
                min_value=1, 
                max_value=1000, 
                default_value=1, 
                key_prefix="entree_stock"
            )
            
            # Prévisualisation du nouveau stock
            nouveau_stock = quantite_actuelle + quantite_ajout
            
            # Affichage mobile-friendly de la prévisualisation
            st.markdown("### 📊 Prévisualisation")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Stock actuel", quantite_actuelle)
            with col2:
                st.metric("Ajout", f"+{quantite_ajout}", delta=quantite_ajout)
            with col3:
                st.metric("Nouveau stock", nouveau_stock, delta=quantite_ajout)
            
            if nouveau_stock > stock_max:
                st.warning(f"⚠️ Attention : après cette entrée, le stock sera de {nouveau_stock} (au-dessus du maximum de {stock_max})")
            
            st.markdown("---")
            if st.button("✅ Valider l'entrée", type="primary", use_container_width=True):
                nouvelle_quantite = quantite_actuelle + quantite_ajout
                df.loc[df['Reference'] == produit_trouve['Reference'], 'Quantite'] = nouvelle_quantite
                save_data(df)
                log_mouvement(produit_trouve['Produits'], "Entrée", quantite_ajout, nouvelle_quantite, quantite_actuelle, produit_trouve['Reference'])
                st.success(f"Entrée de {quantite_ajout} unités pour {produit_trouve['Produits']} effectuée.")
                st.experimental_rerun()
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Sortie de stock":
    st.header("Sortie de stock")
    if not df.empty:
        produit_trouve = rechercher_produit(df)
        
        # Affichage du formulaire de sortie si un produit est trouvé
        if produit_trouve is not None:
            st.divider()
            st.subheader(f"Sortie de stock - {produit_trouve['Produits']}")
            st.write(f"**Référence :** {produit_trouve['Reference']}")
            st.write(f"**Emplacement :** {produit_trouve['Emplacement']}")
            quantite_actuelle = int(produit_trouve['Quantite'])
            stock_min = int(produit_trouve['Stock_Min'])
            stock_max = int(produit_trouve['Stock_Max'])
            
            # Affichage du statut de stock avec couleurs
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quantité actuelle", quantite_actuelle)
            with col2:
                st.metric("Stock minimum", stock_min)
            with col3:
                st.metric("Stock maximum", stock_max)
            
            # Indicateur de statut
            if quantite_actuelle < stock_min:
                st.error(f"⚠️ Stock critique ! Il manque {stock_min - quantite_actuelle} unités pour atteindre le minimum.")
            elif quantite_actuelle > stock_max:
                st.warning(f"🟡 Surstock ! {quantite_actuelle - stock_max} unités au-dessus du maximum.")
            else:
                st.success("✅ Stock dans les limites normales.")
            
            # Interface mobile optimisée pour la quantité
            st.markdown("### 📦 Quantité à retirer")
            quantite_retrait = mobile_quantity_selector(
                "Quantité à retirer du stock", 
                min_value=1, 
                max_value=quantite_actuelle, 
                default_value=1, 
                key_prefix="sortie_stock"
            )
            
            # Prévisualisation du nouveau stock
            nouveau_stock = quantite_actuelle - quantite_retrait
            
            # Affichage mobile-friendly de la prévisualisation
            st.markdown("### 📊 Prévisualisation")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Stock actuel", quantite_actuelle)
            with col2:
                st.metric("Retrait", f"-{quantite_retrait}", delta=-quantite_retrait)
            with col3:
                st.metric("Nouveau stock", nouveau_stock, delta=-quantite_retrait)
            
            # Alertes avec couleurs
            if nouveau_stock < 0:
                st.error(f"❌ Impossible : stock insuffisant (quantité actuelle : {quantite_actuelle})")
            elif nouveau_stock < stock_min:
                st.warning(f"⚠️ Attention : après cette sortie, le stock sera de {nouveau_stock} (en dessous du minimum de {stock_min})")
            else:
                st.success("✅ Sortie possible")
            
            st.markdown("---")
            if st.button("✅ Valider la sortie", type="primary", use_container_width=True):
                if quantite_actuelle >= quantite_retrait:
                    nouvelle_quantite = quantite_actuelle - quantite_retrait
                    df.loc[df['Reference'] == produit_trouve['Reference'], 'Quantite'] = nouvelle_quantite
                    save_data(df)
                    log_mouvement(produit_trouve['Produits'], "Sortie", quantite_retrait, nouvelle_quantite, quantite_actuelle, produit_trouve['Reference'])
                    st.success(f"Sortie de {quantite_retrait} unités pour {produit_trouve['Produits']} effectuée.")
                    st.experimental_rerun()
                else:
                    st.error("Stock insuffisant pour effectuer la sortie.")
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Régule":
    st.header("Ajustement d'inventaire")
    if not df.empty:
        produit_trouve = rechercher_produit(df)
        
        # Affichage du formulaire d'inventaire si un produit est trouvé
        if produit_trouve is not None:
            st.divider()
            st.subheader(f"Ajustement d'inventaire - {produit_trouve['Produits']}")
            st.write(f"**Référence :** {produit_trouve['Reference']}")
            st.write(f"**Emplacement :** {produit_trouve['Emplacement']}")
            quantite_actuelle = int(produit_trouve['Quantite'])
            stock_min = int(produit_trouve['Stock_Min'])
            stock_max = int(produit_trouve['Stock_Max'])
            
            # Affichage du statut de stock avec couleurs
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quantité actuelle", quantite_actuelle)
            with col2:
                st.metric("Stock minimum", stock_min)
            with col3:
                st.metric("Stock maximum", stock_max)
            
            # Indicateur de statut
            if quantite_actuelle < stock_min:
                st.error(f"⚠️ Stock critique ! Il manque {stock_min - quantite_actuelle} unités pour atteindre le minimum.")
                st.info(f"💡 Recommandation : ajuster à {stock_max} unités pour un stock optimal.")
            elif quantite_actuelle > stock_max:
                st.warning(f"🟡 Surstock ! {quantite_actuelle - stock_max} unités au-dessus du maximum.")
            else:
                st.success("✅ Stock dans les limites normales.")
            
            # Interface mobile optimisée pour la quantité
            st.markdown("### 📦 Nouvelle quantité après inventaire")
            nouvelle_quantite = mobile_quantity_selector(
                "Quantité réelle comptée", 
                min_value=0, 
                max_value=9999, 
                default_value=quantite_actuelle, 
                key_prefix="inventaire_ajust"
            )
            
            # Prévisualisation du statut après ajustement
            st.markdown("### 📊 Impact de l'ajustement")
            
            if nouvelle_quantite != quantite_actuelle:
                # Calcul de la différence
                difference = nouvelle_quantite - quantite_actuelle
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Stock actuel", quantite_actuelle)
                with col2:
                    st.metric("Stock réel", nouvelle_quantite, delta=difference)
                with col3:
                    if difference > 0:
                        st.metric("Écart", f"+{difference}", delta=difference)
                    else:
                        st.metric("Écart", f"{difference}", delta=difference)
                
                # Statut après ajustement
                if nouvelle_quantite < stock_min:
                    st.warning(f"⚠️ Après ajustement : stock critique ({nouvelle_quantite} < {stock_min})")
                elif nouvelle_quantite > stock_max:
                    st.warning(f"⚠️ Après ajustement : surstock ({nouvelle_quantite} > {stock_max})")
                else:
                    st.success(f"✅ Après ajustement : stock normal ({stock_min} ≤ {nouvelle_quantite} ≤ {stock_max})")
            else:
                st.info("ℹ️ Aucun ajustement nécessaire - la quantité est identique")
            
            st.markdown("---")
            if st.button("✅ Valider l'ajustement", type="primary", use_container_width=True):
                if nouvelle_quantite != quantite_actuelle:
                    df.loc[df['Reference'] == produit_trouve['Reference'], 'Quantite'] = nouvelle_quantite
                    save_data(df)
                    log_mouvement(
                        produit_trouve['Produits'],
                        "Régule",
                        abs(nouvelle_quantite - quantite_actuelle),
                        nouvelle_quantite,
                        quantite_actuelle,
                        produit_trouve['Reference']
                    )
                    st.success(f"Inventaire ajusté pour {produit_trouve['Produits']} : {quantite_actuelle} → {nouvelle_quantite}")
                    st.experimental_rerun()
                else:
                    st.info("La quantité saisie est identique à la quantité actuelle.")
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Préparer l'inventaire":
    st.header("📊 Gestion des Inventaires")

    # Initialiser les états de session nécessaires pour la gestion des inventaires
    if 'inventaires_sauvegardes' not in st.session_state:
        st.session_state.inventaires_sauvegardes = {}  # ex: {"Nom Inventaire 1": {produits...}, ...}
    if 'page_inventaire_active' not in st.session_state:
        st.session_state.page_inventaire_active = "liste_globale" # ou "creer_liste"
    if 'liste_inventaire_en_creation' not in st.session_state:
        st.session_state.liste_inventaire_en_creation = {}
    if 'nom_inventaire_en_creation' not in st.session_state:
        st.session_state.nom_inventaire_en_creation = ""
    if 'add_inv_counter' not in st.session_state: # Compteur pour clés uniques
        st.session_state.add_inv_counter = 0

    # Navigation dans la section inventaire
    cols_nav_inv = st.columns(2)
    with cols_nav_inv[0]:
        if st.button("📜 Voir les listes d'inventaire", use_container_width=True, type=("primary" if st.session_state.page_inventaire_active == "liste_globale" else "secondary")):
            st.session_state.page_inventaire_active = "liste_globale"
            st.experimental_rerun()
    with cols_nav_inv[1]:
        if st.button("➕ Créer une nouvelle liste", use_container_width=True, type=("primary" if st.session_state.page_inventaire_active == "creer_liste" else "secondary")):
            st.session_state.page_inventaire_active = "creer_liste"
            # Réinitialiser la liste en création quand on change de page
            st.session_state.liste_inventaire_en_creation = {}
            st.session_state.nom_inventaire_en_creation = f"Inventaire du {datetime.now().strftime('%Y-%m-%d_%H%M')}"
            st.session_state.add_inv_counter +=1 # Pour reset les inputs de recherche
            st.experimental_rerun()
    
    st.markdown("---")

    if st.session_state.page_inventaire_active == "liste_globale":
        st.subheader("📜 Listes d'inventaire sauvegardées")
        
        # Charger les listes depuis Excel
        listes_avec_produits = obtenir_listes_inventaire_avec_produits()
        
        if listes_avec_produits:
            for nom_inv, data_inv in listes_avec_produits.items():
                with st.expander(f"**{nom_inv}** ({data_inv.get('nb_produits', 0)} produits) - {data_inv.get('statut', 'N/A')}"):
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.write(f"*ID : {data_inv.get('id_liste', 'N/A')}*")
                        st.write(f"*Date de création : {data_inv.get('date_creation', 'N/A')}*")
                    with col_info2:
                        st.write(f"*Créé par : {data_inv.get('cree_par', 'N/A')}*")
                        st.write(f"*Statut : {data_inv.get('statut', 'N/A')}*")
                    
                    if data_inv.get('produits'):
                        df_inv_saved = pd.DataFrame(list(data_inv['produits'].values()))
                        # S'assurer que 'quantite_theorique' n'est pas dans les colonnes à afficher
                        colonnes_a_afficher = ['produit', 'reference', 'emplacement', 'categorie']
                        # Filtrer pour ne garder que les colonnes existantes dans le DataFrame
                        colonnes_existantes = [col for col in colonnes_a_afficher if col in df_inv_saved.columns]
                        st.dataframe(df_inv_saved[colonnes_existantes], use_container_width=True)
                    else:
                        st.write("Aucun produit dans cette liste.")
                    # TODO: Ajouter des boutons pour voir/modifier/supprimer la liste sauvegardée
        else:
            st.info("Aucune liste d'inventaire n'a été sauvegardée pour le moment. Cliquez sur 'Créer une nouvelle liste' pour commencer.")

    elif st.session_state.page_inventaire_active == "creer_liste":
        st.subheader("➕ Créer une nouvelle liste d'inventaire")

        st.session_state.nom_inventaire_en_creation = st.text_input(
            "Nom de la liste d'inventaire *", 
            value=st.session_state.nom_inventaire_en_creation,
            key=f"nom_inv_creation_{st.session_state.add_inv_counter}"
        )
        
        st.markdown("#### 🛒 Ajouter des produits à la liste")
        
        # Nouvel affichage : liste complète des produits avec boutons d'ajout
        if not df.empty:
            st.write(f"**Tous les produits disponibles ({len(df)}):**")
            
            # Pagination pour éviter de surcharger l'affichage
            produits_par_page = 10
            if 'page_produits_inv' not in st.session_state:
                st.session_state.page_produits_inv = 0
            
            total_pages = (len(df) - 1) // produits_par_page + 1
            
            # Navigation de pagination
            col_prev, col_page, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.button("⬅️ Précédent", disabled=(st.session_state.page_produits_inv == 0)):
                    st.session_state.page_produits_inv = max(0, st.session_state.page_produits_inv - 1)
                    st.experimental_rerun()
            with col_page:
                st.write(f"Page {st.session_state.page_produits_inv + 1} sur {total_pages}")
            with col_next:
                if st.button("➡️ Suivant", disabled=(st.session_state.page_produits_inv >= total_pages - 1)):
                    st.session_state.page_produits_inv = min(total_pages - 1, st.session_state.page_produits_inv + 1)
                    st.experimental_rerun()
            
            # Calculer les indices pour la page actuelle
            debut = st.session_state.page_produits_inv * produits_par_page
            fin = min(debut + produits_par_page, len(df))
            
            # Afficher les produits de la page actuelle
            for idx in range(debut, fin):
                produit = df.iloc[idx]
                col_prod, col_add_btn = st.columns([4, 1])
                with col_prod:
                    st.write(f"**{produit['Produits']}**")
                    st.caption(f"Réf: {produit['Reference']} | Empl: {produit['Emplacement']} | Cat: {produit.get('Categorie', 'N/A')}")
                with col_add_btn:
                    add_key = f"add_inv_complet_{produit['Reference']}_{st.session_state.add_inv_counter}"
                    if produit['Reference'] in st.session_state.liste_inventaire_en_creation:
                        st.button("✔️ Ajouté", key=add_key, disabled=True, use_container_width=True)
                    else:
                        if st.button("➕ Ajouter à la liste à inventorier", key=add_key, use_container_width=True, type="secondary"):
                            st.session_state.liste_inventaire_en_creation[produit['Reference']] = {
                                'produit': produit['Produits'],
                                'reference': produit['Reference'],
                                'emplacement': produit['Emplacement'],
                                'quantite_theorique': int(produit['Quantite']),
                                'categorie': produit.get('Categorie', 'N/A'),
                                'fournisseur': produit.get('Fournisseur', 'N/A')
                            }
                            st.experimental_rerun()
                st.divider()
        else:
            st.warning("Aucun produit disponible dans l'inventaire.")

        st.markdown("--- ")
        st.markdown(f"#### 📜 Produits dans la liste : *{st.session_state.nom_inventaire_en_creation or 'Nouvelle Liste'}*")

        if st.session_state.liste_inventaire_en_creation:
            items_a_supprimer_creation = []
            
            # Ajustement des colonnes d'en-tête (5 colonnes visibles + action)
            c1, c2, c3, c4, c5 = st.columns([2.5, 1.5, 2, 1.5, 0.5]) 
            c1.markdown("**Produit**")
            c2.markdown("**Référence**")
            c3.markdown("**Emplacement**")
            c4.markdown("**Catégorie**")
            # c5 est pour le bouton supprimer, pas d'en-tête explicite

            for ref, item_data in st.session_state.liste_inventaire_en_creation.items():
                # Ajustement des colonnes pour chaque ligne de produit (5 colonnes visibles + action)
                col1, col2, col3, col4, col_action = st.columns([2.5, 1.5, 2, 1.5, 0.5])
                with col1:
                    st.write(item_data['produit'])
                    st.caption(f"Fourn: {item_data.get('fournisseur', 'N/A')}")
                with col2:
                    st.write(item_data['reference'])
                with col3:
                    st.write(item_data['emplacement'])
                with col4: # Anciennement pour Qté Théo, maintenant pour Catégorie
                    st.write(item_data.get('categorie', 'N/A'))
                # La quantité théorique (item_data['quantite_theorique']) n'est plus affichée ici
                with col_action:
                    if st.button("🗑️", key=f"remove_inv_creation_{ref}_{st.session_state.add_inv_counter}", help="Retirer"):
                        items_a_supprimer_creation.append(ref)
                # st.divider() # Peut-être trop de séparateurs ici

            if items_a_supprimer_creation:
                for ref_to_remove in items_a_supprimer_creation:
                    if ref_to_remove in st.session_state.liste_inventaire_en_creation:
                        del st.session_state.liste_inventaire_en_creation[ref_to_remove]
                st.experimental_rerun()
            
            total_produits_creation = len(st.session_state.liste_inventaire_en_creation)
 
            
            st.markdown("---")
            col_stats_c1 = st.columns(1)
            with col_stats_c1:
                st.metric("Produits dans cette liste", total_produits_creation)
 

            col_act_c1, col_act_c2 = st.columns([2,2])
            with col_act_c1:
                 if st.button("🗑️ Vider la liste en cours", use_container_width=True):
                    st.session_state.liste_inventaire_en_creation = {}
                    st.experimental_rerun()
            with col_act_c2:
                if st.button("💾 Sauvegarder cette liste d'inventaire", use_container_width=True, type="primary"):
                    nom_inv = st.session_state.nom_inventaire_en_creation.strip()
                    if not nom_inv:
                        st.error("❌ Veuillez donner un nom à votre liste d'inventaire.")
                    elif not st.session_state.liste_inventaire_en_creation:
                        st.warning("⚠️ La liste est vide. Ajoutez des produits avant de sauvegarder.")
                    else:
                        # Utiliser la nouvelle fonction de sauvegarde Excel
                        success, message = ajouter_liste_inventaire(
                            nom_inv, 
                            st.session_state.liste_inventaire_en_creation
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            # Réinitialiser pour une nouvelle liste et revenir à la vue globale
                            st.session_state.liste_inventaire_en_creation = {}
                            st.session_state.nom_inventaire_en_creation = ""
                            st.session_state.add_inv_counter += 1
                            st.session_state.page_inventaire_active = "liste_globale"
                            st.experimental_rerun()
                        else:
                            st.error(f"❌ {message}")
        else:
            st.info("Aucun produit ajouté à cette liste pour le moment.")

elif action == "Alertes de stock":
    st.header("🚨 Alertes de Stock")
    
    if not df.empty:
        # Produits en stock critique (en dessous du minimum)
        alertes_min = df[df['Quantite'] < df['Stock_Min']]
        
        # Produits en surstock (au-dessus du maximum)
        alertes_max = df[df['Quantite'] > df['Stock_Max']]
        
        # Produits bientôt en rupture (entre min et 50% de la plage min-max)
        seuil_alerte = df['Stock_Min'] + (df['Stock_Max'] - df['Stock_Min']) * 0.3
        alertes_bientot = df[(df['Quantite'] >= df['Stock_Min']) & (df['Quantite'] <= seuil_alerte)]
        
        # Métriques en colonnes
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔴 Stock critique", len(alertes_min))
        with col2:
            st.metric("🟠 Bientôt en rupture", len(alertes_bientot))
        with col3:
            st.metric("🟡 Surstock", len(alertes_max))
        
        # Affichage des alertes critiques
        if not alertes_min.empty:
            st.subheader("🔴 Produits en stock critique")
            st.error("Ces produits nécessitent un réapprovisionnement urgent !")
            
            alertes_min_display = alertes_min.copy()
            alertes_min_display['Manquant'] = alertes_min_display['Stock_Min'] - alertes_min_display['Quantite']
            alertes_min_display['Recommandation'] = alertes_min_display['Stock_Max'] - alertes_min_display['Quantite']
            
            colonnes_critique = ['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Manquant', 'Recommandation', 'Fournisseur']
            st.dataframe(alertes_min_display[colonnes_critique])
        
        # Affichage des alertes de bientôt en rupture
        if not alertes_bientot.empty:
            st.subheader("🟠 Produits bientôt en rupture")
            st.warning("Ces produits devraient être commandés prochainement")
            
            alertes_bientot_display = alertes_bientot.copy()
            alertes_bientot_display['Seuil_Alerte'] = seuil_alerte[alertes_bientot.index].round(1)
            alertes_bientot_display['Recommandation'] = alertes_bientot_display['Stock_Max'] - alertes_bientot_display['Quantite']
            
            colonnes_bientot = ['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Seuil_Alerte', 'Stock_Max', 'Recommandation', 'Fournisseur']
            st.dataframe(alertes_bientot_display[colonnes_bientot])
        
        # Affichage des surstocks
        if not alertes_max.empty:
            st.subheader("🟡 Produits en surstock")
            st.info("Ces produits ont un stock excessif")
            
            alertes_max_display = alertes_max.copy()
            alertes_max_display['Excédent'] = alertes_max_display['Quantite'] - alertes_max_display['Stock_Max']
            
            colonnes_surstock = ['Produits', 'Reference', 'Quantite', 'Stock_Max', 'Excédent', 'Emplacement']
            st.dataframe(alertes_max_display[colonnes_surstock])
        
        # Si tout va bien
        if alertes_min.empty and alertes_bientot.empty and alertes_max.empty:
            st.success("🎉 Aucune alerte ! Tous les stocks sont dans les limites normales.")
            
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Historique des mouvements":
    st.header("📈 Historique des mouvements de stock")
    import pandas as pd
    import os
    file_path = "data/historique.xlsx"
    if os.path.exists(file_path):
        df_hist = pd.read_excel(file_path, engine='openpyxl')
        if not df_hist.empty:
            # S'assurer que la colonne Reference existe (pour la compatibilité avec les anciens fichiers)
            if 'Reference' not in df_hist.columns:
                df_hist['Reference'] = ""
            
            # Convertir la colonne Reference en string pour éviter les séparateurs
            # Traitement spécial pour éviter les .0 sur les nombres entiers
            df_hist['Reference'] = df_hist['Reference'].apply(lambda x: 
                str(int(float(x))) if pd.notna(x) and str(x).replace('.', '').replace('-', '').isdigit() and float(x) == int(float(x))
                else str(x) if pd.notna(x) and str(x) not in ['nan', 'None', ''] 
                else ''
            )
            
            df_hist = df_hist.sort_values(by="Date", ascending=False)
            
            # Statistiques générales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total mouvements", len(df_hist))
            with col2:
                entrees = len(df_hist[df_hist['Nature'].str.contains('Entrée', na=False)])
                st.metric("📥 Entrées", entrees)
            with col3:
                sorties = len(df_hist[df_hist['Nature'].str.contains('Sortie', na=False)])
                st.metric("📤 Sorties", sorties)
            with col4:
                inventaires = len(df_hist[df_hist['Nature'].str.contains('Inventaire', na=False)])
                st.metric("📋 Inventaires", inventaires)
            
            st.markdown("---")
            
            # Filtres améliorés
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                types = ["Tous"] + sorted(df_hist['Nature'].dropna().unique().tolist())
                type_filtre = st.selectbox("🔄 Type de mouvement", types)
            with col2:
                produits = ["Tous"] + sorted(df_hist['Produit'].dropna().unique().tolist())
                produit_filtre = st.selectbox("📦 Produit", produits)
            with col3:
                # Filtre par référence
                references = ["Toutes"] + sorted([ref for ref in df_hist['Reference'].dropna().unique().tolist() if ref != ""])
                reference_filtre = st.selectbox("🆔 Référence", references)
            with col4:
                min_date = pd.to_datetime(df_hist['Date']).min().date()
                max_date = pd.to_datetime(df_hist['Date']).max().date()
                date_range = st.date_input("📅 Plage de dates", (min_date, max_date))
            
            # Application des filtres
            df_filtre = df_hist.copy()
            if type_filtre != "Tous":
                df_filtre = df_filtre[df_filtre['Nature'] == type_filtre]
            if produit_filtre != "Tous":
                df_filtre = df_filtre[df_filtre['Produit'] == produit_filtre]
            if reference_filtre != "Toutes":
                df_filtre = df_filtre[df_filtre['Reference'] == reference_filtre]
            if date_range:
                df_filtre = df_filtre[(pd.to_datetime(df_filtre['Date']).dt.date >= date_range[0]) & (pd.to_datetime(df_filtre['Date']).dt.date <= date_range[1])]
            
            if not df_filtre.empty:
                # Réorganiser les colonnes pour mettre la référence en évidence
                colonnes_ordre = ['Date', 'Reference', 'Produit', 'Nature', 'Quantite_Mouvement', 'Quantite_Avant', 'Quantite_Apres']
                df_affichage = df_filtre[colonnes_ordre].copy()
                
                # Renommer les colonnes pour un affichage plus clair
                df_affichage.columns = ['📅 Date', '🆔 Référence', '📦 Produit', '🔄 Nature', '📊 Quantité', '📉 Avant', '📈 Après']
                
                # Affichage du tableau avec mise en forme
                st.dataframe(
                    df_affichage, 
                    use_container_width=True,
                    hide_index=True
                )
                
                # Bouton d'export
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    # Export CSV
                    csv_data = df_filtre.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📄 Exporter en CSV",
                        data=csv_data,
                        file_name=f"historique_mouvements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="export_csv_historique",
                        use_container_width=True
                    )
                
                with col2:
                    # Export Excel
                    from io import BytesIO
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df_filtre.to_excel(writer, index=False, sheet_name='Historique_Mouvements')
                    
                    st.download_button(
                        label="📊 Exporter en Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"historique_mouvements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="export_excel_historique",
                        use_container_width=True
                    )
            else:
                st.warning("🔍 Aucun mouvement ne correspond aux filtres sélectionnés")
        else:
            st.info("📭 Aucun mouvement enregistré pour le moment.")
    else:
        st.info("📭 Aucun mouvement enregistré pour le moment.")

elif action == "Gérer les tables":
    st.header("📋 Gestion des Tables d'Atelier")
    
    # Charger les tables d'atelier
    df_tables = charger_tables_atelier()
    
    # Onglets pour différentes actions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Liste des tables", "➕ Ajouter une table", "✏️ Modifier une table", "📊 Statistiques détaillées", "📱 QR Codes"])
    
    with tab1:
        st.subheader("📋 Liste des tables d'atelier")
        
        if not df_tables.empty:
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                types_atelier = ["Tous"] + sorted(df_tables['Type_Atelier'].unique().tolist())
                filtre_type = st.selectbox("Filtrer par type", types_atelier, key="filtre_type_liste_tables")
            with col2:
                statuts = ["Tous"] + sorted(df_tables['Statut'].unique().tolist())
                filtre_statut = st.selectbox("Filtrer par statut", statuts, key="filtre_statut_liste_tables")
            with col3:
                responsables = ["Tous"] + sorted(df_tables['Responsable'].unique().tolist())
                filtre_responsable = st.selectbox("Filtrer par responsable", responsables)
            
            # Application des filtres
            df_filtre = df_tables.copy()
            if filtre_type != "Tous":
                df_filtre = df_filtre[df_filtre['Type_Atelier'] == filtre_type]
            if filtre_statut != "Tous":
                df_filtre = df_filtre[df_filtre['Statut'] == filtre_statut]
            if filtre_responsable != "Tous":
                df_filtre = df_filtre[df_filtre['Responsable'] == filtre_responsable]
            
            # Affichage du tableau
            st.dataframe(df_filtre, use_container_width=True)
            
            # Statistiques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total tables", len(df_filtre))
            with col2:
                actives = len(df_filtre[df_filtre['Statut'] == 'Actif'])
                st.metric("✅ Tables actives", actives)
            with col3:
                types_uniques = df_filtre['Type_Atelier'].nunique()
                st.metric("🏭 Types d'ateliers", types_uniques)
            with col4:
                responsables_uniques = df_filtre['Responsable'].nunique()
                st.metric("👥 Responsables", responsables_uniques)
        else:
            st.warning("Aucune table d'atelier enregistrée.")
    
    with tab2:
        st.subheader("➕ Ajouter une nouvelle table d'atelier")
        
        with st.form("ajouter_table"):
            col1, col2 = st.columns(2)
            
            with col1:
                id_table = st.text_input(
                    "ID de la table *", 
                    placeholder="Ex: ALU01, PVC03, BOIS05",
                    help="Identifiant unique de la table (sera utilisé pour le QR code)"
                ).upper()
                
                nom_table = st.text_input(
                    "Nom de la table *", 
                    placeholder="Ex: Table Aluminium 01"
                )
                
                type_atelier = st.selectbox(
                    "Type d'atelier *", 
                    ["Aluminium", "PVC", "Bois", "Métallerie", "Assemblage", "Finition", "Autre"]
                )
            
            with col2:
                emplacement = st.text_input(
                    "Emplacement *", 
                    placeholder="Ex: Atelier A - Zone 1"
                )
                
                responsable = st.text_input(
                    "Responsable *", 
                    placeholder="Ex: Jean Dupont"
                )
            
            submitted = st.form_submit_button("➕ Ajouter la table", use_container_width=True)
            
            if submitted:
                if not all([id_table, nom_table, type_atelier, emplacement, responsable]):
                    st.error("❌ Veuillez remplir tous les champs obligatoires")
                else:
                    success, message = ajouter_table_atelier(id_table, nom_table, type_atelier, emplacement, responsable)
                    if success:
                        st.success(f"✅ {message}")
                        st.experimental_rerun()
                    else:
                        st.error(f"❌ {message}")
    
    with tab3:
        st.subheader("✏️ Modifier une table d'atelier")
        
        if not df_tables.empty:
            table_a_modifier = st.selectbox(
                "Sélectionnez la table à modifier", 
                df_tables['ID_Table'].unique(),
                format_func=lambda x: f"{x} - {df_tables[df_tables['ID_Table'] == x]['Nom_Table'].iloc[0]}"
            )
            
            table_data = df_tables[df_tables['ID_Table'] == table_a_modifier].iloc[0]
            
            with st.form("modifier_table"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nouveau_nom = st.text_input("Nom de la table", value=table_data['Nom_Table'])
                    nouveau_type = st.selectbox(
                        "Type d'atelier", 
                        ["Aluminium", "PVC", "Bois", "Métallerie", "Assemblage", "Finition", "Autre"],
                        index=["Aluminium", "PVC", "Bois", "Métallerie", "Assemblage", "Finition", "Autre"].index(table_data['Type_Atelier']) if table_data['Type_Atelier'] in ["Aluminium", "PVC", "Bois", "Métallerie", "Assemblage", "Finition", "Autre"] else 0
                    )
                
                with col2:
                    nouvel_emplacement = st.text_input("Emplacement", value=table_data['Emplacement'])
                    nouveau_responsable = st.text_input("Responsable", value=table_data['Responsable'])
                    nouveau_statut = st.selectbox(
                        "Statut", 
                        ["Actif", "Inactif", "Maintenance"],
                        index=["Actif", "Inactif", "Maintenance"].index(table_data['Statut']) if table_data['Statut'] in ["Actif", "Inactif", "Maintenance"] else 0
                    )
                
                submitted_modif = st.form_submit_button("✏️ Mettre à jour", use_container_width=True)
                
                if submitted_modif:
                    # Mettre à jour les données
                    df_tables.loc[df_tables['ID_Table'] == table_a_modifier, 'Nom_Table'] = nouveau_nom
                    df_tables.loc[df_tables['ID_Table'] == table_a_modifier, 'Type_Atelier'] = nouveau_type
                    df_tables.loc[df_tables['ID_Table'] == table_a_modifier, 'Emplacement'] = nouvel_emplacement
                    df_tables.loc[df_tables['ID_Table'] == table_a_modifier, 'Responsable'] = nouveau_responsable
                    df_tables.loc[df_tables['ID_Table'] == table_a_modifier, 'Statut'] = nouveau_statut
                    
                    if sauvegarder_tables_atelier(df_tables):
                        st.success("✅ Table mise à jour avec succès!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
        else:
            st.warning("Aucune table d'atelier à modifier.")
    
    with tab4:
        st.subheader("📊 Statistiques détaillées par table d'atelier")
        
        if not df_tables.empty:
            # Charger les demandes pour analyser l'activité des tables
            df_demandes = charger_demandes()
            
            # Sélection de la table pour les détails
            table_selectionnee = st.selectbox(
                "Sélectionnez une table d'atelier pour voir les statistiques", 
                df_tables['ID_Table'].unique(),
                key="select_table_stats",
                format_func=lambda x: f"{x} - {df_tables[df_tables['ID_Table'] == x]['Nom_Table'].iloc[0]}"
            )
            
            # Informations de la table sélectionnée
            table_info = df_tables[df_tables['ID_Table'] == table_selectionnee].iloc[0]
            
            # Affichage des informations générales
            st.markdown("---")
            st.subheader(f"📋 Informations - {table_info['Nom_Table']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**🆔 ID Table :** {table_info['ID_Table']}")
                st.info(f"**🏭 Type :** {table_info['Type_Atelier']}")
            with col2:
                st.info(f"**👤 Responsable :** {table_info['Responsable']}")
                st.info(f"**📊 Statut :** {table_info['Statut']}")
            with col3:
                st.info(f"**📍 Emplacement :** {table_info['Emplacement']}")
                st.info(f"**📅 Créée le :** {table_info['Date_Creation']}")
            
            # Analyse des demandes de matériel
            st.markdown("---")
            st.subheader("📦 Activité de demandes de matériel")
            
            if not df_demandes.empty:
                # Filtrer les demandes liées à cette table
                # On cherche dans les données de demande si le chantier/atelier correspond à la table
                demandes_table = []
                
                for idx, demande in df_demandes.iterrows():
                    try:
                        import ast
                        produits_data = ast.literal_eval(demande['Produits_Demandes'])
                        
                        # Vérifier si c'est une demande structurée avec chantier
                        if isinstance(produits_data, dict) and 'chantier' in produits_data:
                            chantier = produits_data['chantier']
                            # Vérifier si le chantier contient exactement l'ID de la table ou le nom de la table
                            # Utiliser des correspondances exactes pour éviter les faux positifs
                            chantier_lower = chantier.lower()
                            id_table_lower = table_info['ID_Table'].lower()
                            nom_table_lower = table_info['Nom_Table'].lower()
                            type_atelier_lower = table_info['Type_Atelier'].lower()
                            
                            # Vérification exacte de l'ID de table (avec délimiteurs)
                            import re
                            id_pattern = r'\b' + re.escape(id_table_lower) + r'\b'
                            nom_pattern = r'\b' + re.escape(nom_table_lower) + r'\b'
                            
                            if (re.search(id_pattern, chantier_lower) or 
                                re.search(nom_pattern, chantier_lower) or
                                (type_atelier_lower in chantier_lower and len(type_atelier_lower) > 3)):
                                demandes_table.append(demande)
                        
                        # Aussi vérifier dans le demandeur si c'est le responsable de la table
                        elif demande['Demandeur'] == table_info['Responsable']:
                            demandes_table.append(demande)
                            
                    except Exception:
                        # Si erreur de parsing, vérifier juste le demandeur
                        if demande['Demandeur'] == table_info['Responsable']:
                            demandes_table.append(demande)
                
                if demandes_table:
                    df_demandes_table = pd.DataFrame(demandes_table)
                    
                    # Statistiques générales
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        total_demandes = len(df_demandes_table)
                        st.metric("📋 Total demandes", total_demandes)
                    with col2:
                        demandes_approuvees = len(df_demandes_table[df_demandes_table['Statut'] == 'Approuvée'])
                        st.metric("✅ Approuvées", demandes_approuvees)
                    with col3:
                        demandes_en_attente = len(df_demandes_table[df_demandes_table['Statut'] == 'En attente'])
                        st.metric("⏳ En attente", demandes_en_attente)
                    with col4:
                        demandes_refusees = len(df_demandes_table[df_demandes_table['Statut'] == 'Refusée'])
                        st.metric("❌ Refusées", demandes_refusees)
                    
                    # Analyse temporelle
                    st.markdown("### 📈 Évolution des demandes")
                    
                    # Convertir les dates et créer un graphique temporel
                    df_demandes_table['Date_Demande'] = pd.to_datetime(df_demandes_table['Date_Demande'])
                    df_demandes_table['Mois'] = df_demandes_table['Date_Demande'].dt.to_period('M')
                    
                    # Compter les demandes par mois
                    demandes_par_mois = df_demandes_table.groupby('Mois').size().reset_index(name='Nombre_Demandes')
                    demandes_par_mois['Mois_Str'] = demandes_par_mois['Mois'].astype(str)
                    
                    if len(demandes_par_mois) > 0:
                        import plotly.express as px
                        fig_evolution = px.line(
                            demandes_par_mois, 
                            x='Mois_Str', 
                            y='Nombre_Demandes',
                            title=f'Évolution des demandes - {table_info["Nom_Table"]}',
                            labels={'Mois_Str': 'Mois', 'Nombre_Demandes': 'Nombre de demandes'}
                        )
                        fig_evolution.update_layout(xaxis_tickangle=45)
                        st.plotly_chart(fig_evolution, use_container_width=True)
                    
                    # Analyse des produits les plus demandés
                    st.markdown("### 🛠️ Produits les plus demandés")
                    
                    produits_demandes = {}
                    for idx, demande in df_demandes_table.iterrows():
                        try:
                            import ast
                            produits_data = ast.literal_eval(demande['Produits_Demandes'])
                            
                            if isinstance(produits_data, dict) and 'produits' in produits_data:
                                for ref, item in produits_data['produits'].items():
                                    produit_nom = item['produit']
                                    quantite = item['quantite']
                                    
                                    if produit_nom in produits_demandes:
                                        produits_demandes[produit_nom] += quantite
                                    else:
                                        produits_demandes[produit_nom] = quantite
                        except Exception:
                            continue
                    
                    if produits_demandes:
                        # Créer un DataFrame des produits demandés
                        df_produits_stats = pd.DataFrame(
                            list(produits_demandes.items()), 
                            columns=['Produit', 'Quantité_Totale']
                        ).sort_values('Quantité_Totale', ascending=False)
                        
                        # Afficher le top 10
                        st.dataframe(df_produits_stats.head(10), use_container_width=True)
                        
                        # Graphique des produits les plus demandés
                        if len(df_produits_stats) > 0:
                            fig_produits = px.bar(
                                df_produits_stats.head(10), 
                                x='Produit', 
                                y='Quantité_Totale',
                                title=f'Top 10 des produits demandés - {table_info["Nom_Table"]}',
                                labels={'Quantité_Totale': 'Quantité totale demandée', 'Produit': 'Produits'}
                            )
                            fig_produits.update_layout(xaxis_tickangle=45)
                            st.plotly_chart(fig_produits, use_container_width=True)
                    else:
                        st.info("Aucun détail de produit trouvé dans les demandes")
                    
                    # Liste détaillée des demandes
                    st.markdown("### 📋 Historique détaillé des demandes")
                    
                    # Trier par date (plus récent en premier)
                    df_demandes_table_sorted = df_demandes_table.sort_values('Date_Demande', ascending=False)
                    
                    for idx, demande in df_demandes_table_sorted.iterrows():
                        statut_icon = get_statut_icon(demande['Statut'])
                        
                        with st.expander(f"{statut_icon} {demande['ID_Demande']} - {str(demande['Date_Demande'])[:10]} - {demande['Statut']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**📅 Date :** {demande['Date_Demande']}")
                                st.write(f"**👤 Demandeur :** {demande['Demandeur']}")
                                st.write(f"**📝 Motif :** {demande['Motif']}")
                            
                            with col2:
                                if demande['Statut'] == 'En attente':
                                    st.warning(f"**{statut_icon} Statut :** {demande['Statut']}")
                                elif demande['Statut'] == 'Approuvée':
                                    st.success(f"**{statut_icon} Statut :** {demande['Statut']}")
                                elif demande['Statut'] == 'Refusée':
                                    st.error(f"**{statut_icon} Statut :** {demande['Statut']}")
                                
                                if demande['Date_Traitement']:
                                    st.write(f"**⏰ Traité le :** {demande['Date_Traitement']}")
                                    st.write(f"**👨‍💼 Traité par :** {demande['Traite_Par']}")
                            
                            # Détail des produits demandés
                            try:
                                import ast
                                produits_data = ast.literal_eval(demande['Produits_Demandes'])
                                
                                if isinstance(produits_data, dict):
                                    if 'urgence' in produits_data:
                                        st.write(f"**⚡ Urgence :** {produits_data['urgence']}")
                                    if 'date_souhaitee' in produits_data:
                                        st.write(f"**📅 Date souhaitée :** {produits_data['date_souhaitee']}")
                                    
                                    if 'produits' in produits_data:
                                        st.write("**🛠️ Produits demandés :**")
                                        produits_list = []
                                        for ref, item in produits_data['produits'].items():
                                            produits_list.append({
                                                'Référence': ref,
                                                'Produit': item['produit'],
                                                'Quantité': item['quantite'],
                                                'Emplacement': item['emplacement']
                                            })
                                        
                                        df_produits_demande = pd.DataFrame(produits_list)
                                        st.dataframe(df_produits_demande, use_container_width=True)
                            except Exception:
                                st.write(f"**📦 Détails :** {demande['Produits_Demandes']}")
                
                else:
                    st.info(f"Aucune demande de matériel trouvée pour la table {table_info['Nom_Table']}")
                    st.write("💡 **Comment associer des demandes à cette table :**")
                    st.write("- Le demandeur doit être le responsable de la table")
                    st.write("- Ou le chantier/atelier doit contenir l'ID ou le nom de la table")
            
            else:
                st.info("Aucune demande de matériel enregistrée dans le système")
                
        else:
            st.warning("Aucune table d'atelier disponible pour afficher les statistiques.")
    
    with tab5:
        st.subheader("📱 QR Code des Tables d'Atelier")
        
        if not df_tables.empty:
            # Onglets pour différentes options
            sub_tab1, sub_tab2 = st.tabs(["🔍 QR Code individuel", "🏭 Toutes les tables"])
            
            with sub_tab1:
                
                # Sélection de la table
                table_select = st.selectbox(
                    "Sélectionnez une table d'atelier", 
                    df_tables['ID_Table'].unique(), 
                    key="qr_table_individual",
                    format_func=lambda x: f"{x} - {df_tables[df_tables['ID_Table'] == x]['Nom_Table'].iloc[0]}"
                )
                
                # Informations de la table sélectionnée
                table_info = df_tables[df_tables['ID_Table'] == table_select].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 Informations de la table")
                    st.write(f"**🆔 ID Table :** {table_info['ID_Table']}")
                    st.write(f"**📛 Nom :** {table_info['Nom_Table']}")
                    st.write(f"**🏭 Type d'atelier :** {table_info['Type_Atelier']}")
                    st.write(f"**📍 Emplacement :** {table_info['Emplacement']}")
                    st.write(f"**👤 Responsable :** {table_info['Responsable']}")
                    st.write(f"**📊 Statut :** {table_info['Statut']}")
                    st.write(f"**📅 Date création :** {table_info['Date_Creation']}")
                
                with col2:
                    st.subheader("📱 QR Code")
                    
                    # Génération du QR code avec l'ID de la table
                    qr = qrcode.QRCode(box_size=8, border=4)
                    qr.add_data(table_info['ID_Table'])
                    qr.make(fit=True)
                    
                    # Créer l'image du QR code
                    img = qr.make_image(fill_color="black", back_color="white")
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    
                    # Afficher le QR code
                    st.image(buf.getvalue(), caption=f"QR Code pour {table_info['Nom_Table']}")
                    
                    # Bouton de téléchargement
                    st.download_button(
                        label="💾 Télécharger le QR Code",
                        data=buf.getvalue(),
                        file_name=f"QR_Table_{table_info['ID_Table']}.png",
                        mime="image/png",
                        key=f"download_qr_table_individual_{table_info['ID_Table']}",
                        use_container_width=True
                    )
            
            with sub_tab2:
                st.subheader("🏭 Génération de tous les QR codes")
                
                # Filtres pour sélectionner les tables
                col1, col2, col3 = st.columns(3)
                with col1:
                    types_atelier = ["Tous"] + sorted(df_tables['Type_Atelier'].unique().tolist())
                    filtre_type = st.selectbox("Filtrer par type d'atelier", types_atelier, key="filtre_type_qr_tables")
                with col2:
                    statuts = ["Tous"] + sorted(df_tables['Statut'].unique().tolist())
                    filtre_statut = st.selectbox("Filtrer par statut", statuts, key="filtre_statut_qr_tables")
                with col3:
                    # Filtre par tables actives uniquement
                    actives_uniquement = st.checkbox("Tables actives uniquement", value=True)
                
                # Application des filtres
                df_filtre = df_tables.copy()
                if filtre_type != "Tous":
                    df_filtre = df_filtre[df_filtre['Type_Atelier'] == filtre_type]
                if filtre_statut != "Tous":
                    df_filtre = df_filtre[df_filtre['Statut'] == filtre_statut]
                if actives_uniquement:
                    df_filtre = df_filtre[df_filtre['Statut'] == 'Actif']
                
                # Affichage du nombre de tables sélectionnées
                st.info(f"🏭 **{len(df_filtre)} table(s) sélectionnée(s)** pour la génération de QR codes")
                
                if len(df_filtre) > 0:
                    # Options d'affichage
                    col1, col2 = st.columns(2)
                    with col1:
                        taille_qr = st.selectbox("Taille des QR codes", ["Petit (4)", "Moyen (6)", "Grand (8)"], index=1, key="taille_table")
                        box_size = {"Petit (4)": 4, "Moyen (6)": 6, "Grand (8)": 8}[taille_qr]
                    with col2:
                        colonnes_par_ligne = st.selectbox("QR codes par ligne", [2, 3, 4], index=1, key="colonnes_table")
                    
                    # Bouton pour générer tous les QR codes
                    if st.button("🏭 Générer tous les QR codes", use_container_width=True, type="primary"):
                        st.subheader("🏭 QR codes de toutes les tables sélectionnées")
                        
                        # Barre de progression
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Créer une grille pour afficher tous les QR codes
                        for i in range(0, len(df_filtre), colonnes_par_ligne):
                            cols = st.columns(colonnes_par_ligne)
                            
                            for j in range(colonnes_par_ligne):
                                if i + j < len(df_filtre):
                                    table_row = df_filtre.iloc[i + j]
                                    
                                    # Mise à jour de la barre de progression
                                    progress = (i + j + 1) / len(df_filtre)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Génération en cours... {i + j + 1}/{len(df_filtre)}")
                                    
                                    with cols[j]:
                                        # Générer le QR code
                                        qr = qrcode.QRCode(box_size=box_size, border=2)
                                        qr.add_data(table_row['ID_Table'])
                                        qr.make(fit=True)
                                        img = qr.make_image(fill_color="black", back_color="white")
                                        buf = BytesIO()
                                        img.save(buf, format="PNG")
                                        
                                        # Afficher avec informations
                                        st.image(buf.getvalue(), caption=f"**{table_row['ID_Table']}**\n{table_row['Nom_Table']}\n{table_row['Type_Atelier']}\n👤 {table_row['Responsable']}")
                                        
                                        # Bouton de téléchargement individuel
                                        st.download_button(
                                            label=f"💾 {table_row['ID_Table']}",
                                            data=buf.getvalue(),
                                            file_name=f"QR_Table_{table_row['ID_Table']}.png",
                                            mime="image/png",
                                            key=f"download_table_{table_row['ID_Table']}",
                                            use_container_width=True
                                        )
                        
                        # Finalisation
                        progress_bar.progress(1.0)
                        status_text.text("✅ Génération terminée !")
                        st.success(f"🎉 **{len(df_filtre)} QR codes générés avec succès !**")
                        
                else:
                    st.warning("Aucune table ne correspond aux filtres sélectionnés.")
            
        else:
            st.warning("Aucune table d'atelier disponible. Veuillez d'abord créer des tables.")

elif action == "Fournisseurs":
    st.header("🏪 Gestion des Fournisseurs")
    
    # Charger et mettre à jour les fournisseurs
    df_fournisseurs = mettre_a_jour_statistiques_fournisseurs()
    
    # Onglets pour différentes actions
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Liste des fournisseurs", "➕ Ajouter un fournisseur", "✏️ Modifier un fournisseur", "📊 Statistiques détaillées"])
    
    with tab1:
        st.subheader("📋 Liste des fournisseurs")
        
        if not df_fournisseurs.empty:
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                statuts = ["Tous"] + sorted(df_fournisseurs['Statut'].unique().tolist())
                filtre_statut = st.selectbox("Filtrer par statut", statuts, key="filtre_statut_fournisseur")
            with col2:
                # Filtre par nombre de produits
                min_produits = st.number_input("Nombre minimum de produits", min_value=0, value=0, key="min_produits")
            with col3:
                # Bouton pour actualiser les statistiques
                if st.button("🔄 Actualiser les statistiques", use_container_width=True):
                    df_fournisseurs = mettre_a_jour_statistiques_fournisseurs()
                    st.success("✅ Statistiques mises à jour")
                    st.experimental_rerun()
            
            # Application des filtres
            df_filtre = df_fournisseurs.copy()
            if filtre_statut != "Tous":
                df_filtre = df_filtre[df_filtre['Statut'] == filtre_statut]
            if min_produits > 0:
                df_filtre = df_filtre[df_filtre['Nb_Produits'] >= min_produits]
            
            # Affichage du tableau avec formatage
            df_display = df_filtre.copy()
            df_display['Valeur_Stock_Total'] = df_display['Valeur_Stock_Total'].apply(lambda x: f"{x:,.2f} €")
            
            st.dataframe(df_display, use_container_width=True)
            
            # Statistiques globales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total fournisseurs", len(df_filtre))
            with col2:
                actifs = len(df_filtre[df_filtre['Statut'] == 'Actif'])
                st.metric("✅ Fournisseurs actifs", actifs)
            with col3:
                total_produits = df_filtre['Nb_Produits'].sum()
                st.metric("📦 Total produits", total_produits)
            with col4:
                valeur_totale = df_filtre['Valeur_Stock_Total'].sum()
                st.metric("💰 Valeur totale", f"{valeur_totale:,.2f} €")
            
            # Graphiques de répartition
            if len(df_filtre) > 0:
                st.markdown("---")
                st.subheader("📊 Répartition par fournisseur")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Graphique nombre de produits par fournisseur
                    fig_produits = px.bar(
                        df_filtre, 
                        x='Nom_Fournisseur', 
                        y='Nb_Produits',
                        title='Nombre de produits par fournisseur',
                        labels={'Nb_Produits': 'Nombre de produits', 'Nom_Fournisseur': 'Fournisseur'}
                    )
                    fig_produits.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig_produits, use_container_width=True)
                
                with col2:
                    # Graphique valeur du stock par fournisseur
                    fig_valeur = px.bar(
                        df_filtre, 
                        x='Nom_Fournisseur', 
                        y='Valeur_Stock_Total',
                        title='Valeur du stock par fournisseur',
                        labels={'Valeur_Stock_Total': 'Valeur du stock (€)', 'Nom_Fournisseur': 'Fournisseur'}
                    )
                    fig_valeur.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig_valeur, use_container_width=True)
        else:
            st.warning("Aucun fournisseur enregistré.")
    
    with tab2:
        st.subheader("➕ Ajouter un nouveau fournisseur")
        
        with st.form("ajouter_fournisseur"):
            col1, col2 = st.columns(2)
            
            with col1:
                nom_fournisseur = st.text_input(
                    "Nom du fournisseur *", 
                    placeholder="Ex: Entreprise ABC"
                )
                
                contact_principal = st.text_input(
                    "Contact principal *", 
                    placeholder="Ex: Jean Dupont"
                )
                
                email = st.text_input(
                    "Email", 
                    placeholder="Ex: contact@entreprise-abc.fr"
                )
            
            with col2:
                telephone = st.text_input(
                    "Téléphone", 
                    placeholder="Ex: 01 23 45 67 89"
                )
                
                adresse = st.text_area(
                    "Adresse", 
                    placeholder="Ex: 123 Rue de la Paix, 75001 Paris"
                )
            
            submitted = st.form_submit_button("➕ Ajouter le fournisseur", use_container_width=True)
            
            if submitted:
                if not all([nom_fournisseur, contact_principal]):
                    st.error("❌ Veuillez remplir au minimum le nom du fournisseur et le contact principal")
                else:
                    success, message = ajouter_fournisseur(nom_fournisseur, contact_principal, email, telephone, adresse)
                    if success:
                        st.success(f"✅ {message}")
                        st.experimental_rerun()
                    else:
                        st.error(f"❌ {message}")
    
    with tab3:
        st.subheader("✏️ Modifier un fournisseur")
        
        if not df_fournisseurs.empty:
            fournisseur_a_modifier = st.selectbox(
                "Sélectionnez le fournisseur à modifier", 
                df_fournisseurs['Nom_Fournisseur'].unique(),
                key="select_fournisseur_modifier"
            )
            
            fournisseur_data = df_fournisseurs[df_fournisseurs['Nom_Fournisseur'] == fournisseur_a_modifier].iloc[0]
            
            with st.form("modifier_fournisseur"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nouveau_nom = st.text_input("Nom du fournisseur", value=fournisseur_data['Nom_Fournisseur'])
                    nouveau_contact = st.text_input("Contact principal", value=fournisseur_data['Contact_Principal'])
                    nouvel_email = st.text_input("Email", value=fournisseur_data['Email'])
                
                with col2:
                    nouveau_telephone = st.text_input("Téléphone", value=fournisseur_data['Telephone'])
                    nouvelle_adresse = st.text_area("Adresse", value=fournisseur_data['Adresse'])
                    nouveau_statut = st.selectbox(
                        "Statut", 
                        ["Actif", "Inactif", "Suspendu"],
                        index=["Actif", "Inactif", "Suspendu"].index(fournisseur_data['Statut']) if fournisseur_data['Statut'] in ["Actif", "Inactif", "Suspendu"] else 0
                    )
                
                submitted_modif = st.form_submit_button("✏️ Mettre à jour", use_container_width=True)
                
                if submitted_modif:
                    # Mettre à jour les données
                    df_fournisseurs.loc[df_fournisseurs['Nom_Fournisseur'] == fournisseur_a_modifier, 'Nom_Fournisseur'] = nouveau_nom
                    df_fournisseurs.loc[df_fournisseurs['Nom_Fournisseur'] == fournisseur_a_modifier, 'Contact_Principal'] = nouveau_contact
                    df_fournisseurs.loc[df_fournisseurs['Nom_Fournisseur'] == fournisseur_a_modifier, 'Email'] = nouvel_email
                    df_fournisseurs.loc[df_fournisseurs['Nom_Fournisseur'] == fournisseur_a_modifier, 'Telephone'] = nouveau_telephone
                    df_fournisseurs.loc[df_fournisseurs['Nom_Fournisseur'] == fournisseur_a_modifier, 'Adresse'] = nouvelle_adresse
                    df_fournisseurs.loc[df_fournisseurs['Nom_Fournisseur'] == fournisseur_a_modifier, 'Statut'] = nouveau_statut
                    
                    if sauvegarder_fournisseurs(df_fournisseurs):
                        st.success("✅ Fournisseur mis à jour avec succès!")
                        
                        # Si le nom a changé, mettre à jour aussi l'inventaire
                        if nouveau_nom != fournisseur_a_modifier:
                            df.loc[df['Fournisseur'] == fournisseur_a_modifier, 'Fournisseur'] = nouveau_nom
                            save_data(df)
                            st.info("📦 Inventaire mis à jour avec le nouveau nom du fournisseur")
                        
                        st.experimental_rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
        else:
            st.warning("Aucun fournisseur à modifier.")
    
    with tab4:
        st.subheader("📊 Statistiques détaillées par fournisseur")
        
        if not df_fournisseurs.empty and not df.empty:
            # Sélection du fournisseur pour les détails
            fournisseur_selectionne = st.selectbox(
                "Sélectionnez un fournisseur pour voir les détails", 
                df_fournisseurs['Nom_Fournisseur'].unique(),
                key="select_fournisseur_stats"
            )
            
            # Informations du fournisseur sélectionné
            fournisseur_info = df_fournisseurs[df_fournisseurs['Nom_Fournisseur'] == fournisseur_selectionne].iloc[0]
            
            # Affichage des informations générales
            st.markdown("---")
            st.subheader(f"📋 Informations - {fournisseur_selectionne}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**👤 Contact :** {fournisseur_info['Contact_Principal']}")
                st.info(f"**📧 Email :** {fournisseur_info['Email']}")
            with col2:
                st.info(f"**📞 Téléphone :** {fournisseur_info['Telephone']}")
                st.info(f"**📅 Depuis :** {fournisseur_info['Date_Creation']}")
            with col3:
                st.info(f"**📊 Statut :** {fournisseur_info['Statut']}")
                st.info(f"**🆔 ID :** {fournisseur_info['ID_Fournisseur']}")
            
            if fournisseur_info['Adresse']:
                st.info(f"**📍 Adresse :** {fournisseur_info['Adresse']}")
            
            # Statistiques détaillées
            st.markdown("---")
            st.subheader("📊 Statistiques")
            
            # Produits de ce fournisseur
            produits_fournisseur = df[df['Fournisseur'] == fournisseur_selectionne]
            
            if not produits_fournisseur.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📦 Nombre de produits", len(produits_fournisseur))
                with col2:
                    stock_total = produits_fournisseur['Quantite'].sum()
                    st.metric("📊 Stock total", stock_total)
                with col3:
                    valeur_stock = (produits_fournisseur['Quantite'] * produits_fournisseur['Prix_Unitaire']).sum()
                    st.metric("💰 Valeur du stock", f"{valeur_stock:,.2f} €")
                with col4:
                    prix_moyen = produits_fournisseur['Prix_Unitaire'].mean()
                    st.metric("💵 Prix moyen", f"{prix_moyen:.2f} €")
                
                # Liste des produits
                st.markdown("---")
                st.subheader("📦 Produits de ce fournisseur")
                
                # Ajouter des colonnes calculées pour l'affichage
                produits_display = produits_fournisseur.copy()
                produits_display['Valeur_Stock'] = produits_display['Quantite'] * produits_fournisseur['Prix_Unitaire']
                
                # Statut de stock
                produits_display['Statut_Stock'] = produits_display.apply(
                    lambda row: "🔴 Critique" if row['Quantite'] < row['Stock_Min'] 
                    else "🟡 Surstock" if row['Quantite'] > row['Stock_Max']
                    else "🟠 Faible" if row['Quantite'] <= row['Stock_Min'] + (row['Stock_Max'] - row['Stock_Min']) * 0.3
                    else "🟢 Normal", axis=1
                )
                
                # Colonnes à afficher
                colonnes_produits = ['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Stock_Max', 'Prix_Unitaire', 'Valeur_Stock', 'Statut_Stock', 'Emplacement']
                st.dataframe(produits_display[colonnes_produits].round(2), use_container_width=True)
                
                # Alertes pour ce fournisseur
                alertes_critique = produits_fournisseur[produits_fournisseur['Quantite'] < produits_fournisseur['Stock_Min']]
                alertes_surstock = produits_fournisseur[produits_fournisseur['Quantite'] > produits_fournisseur['Stock_Max']]
                
                # Produits bientôt en rupture (entre min et 30% de la plage min-max)
                seuil_alerte_fournisseur = produits_fournisseur['Stock_Min'] + (produits_fournisseur['Stock_Max'] - produits_fournisseur['Stock_Min']) * 0.3
                alertes_bientot = produits_fournisseur[(produits_fournisseur['Quantite'] >= produits_fournisseur['Stock_Min']) & (produits_fournisseur['Quantite'] <= seuil_alerte_fournisseur)]
                
                if not alertes_critique.empty or not alertes_bientot.empty or not alertes_surstock.empty:
                    st.markdown("---")
                    st.subheader("⚠️ Alertes de stock")
                    
                    if not alertes_critique.empty:
                        st.error(f"🔴 **{len(alertes_critique)} produit(s) en stock critique** nécessitent un réapprovisionnement urgent")
                        alertes_critique_display = alertes_critique.copy()
                        alertes_critique_display['Recommandation'] = alertes_critique_display['Stock_Max'] - alertes_critique_display['Quantite']
                        st.dataframe(alertes_critique_display[['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Stock_Max', 'Recommandation']], use_container_width=True)
                    
                    if not alertes_bientot.empty:
                        st.warning(f"🟠 **{len(alertes_bientot)} produit(s) bientôt en rupture** - réapprovisionnement recommandé")
                        alertes_bientot_display = alertes_bientot.copy()
                        alertes_bientot_display['Seuil_Alerte'] = seuil_alerte_fournisseur[alertes_bientot.index].round(1)
                        alertes_bientot_display['Recommandation'] = alertes_bientot_display['Stock_Max'] - alertes_bientot_display['Quantite']
                        st.dataframe(alertes_bientot_display[['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Seuil_Alerte', 'Stock_Max', 'Recommandation']], use_container_width=True)
                    
                    if not alertes_surstock.empty:
                        st.warning(f"🟡 **{len(alertes_surstock)} produit(s) en surstock**")
                        st.dataframe(alertes_surstock[['Produits', 'Reference', 'Quantite', 'Stock_Max']], use_container_width=True)
                
                # Graphique de répartition des stocks pour ce fournisseur
                if len(produits_fournisseur) > 1:
                    st.markdown("---")
                    st.subheader("📈 Répartition des stocks")
                    
                    fig_stock = px.bar(
                        produits_fournisseur, 
                        x='Produits', 
                        y='Quantite',
                        title=f'Stock par produit - {fournisseur_selectionne}',
                        labels={'Quantite': 'Quantité en stock', 'Produits': 'Produits'}
                    )
                    fig_stock.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig_stock, use_container_width=True)
            else:
                st.warning(f"Aucun produit trouvé pour le fournisseur {fournisseur_selectionne}")
        else:
            st.warning("Aucune donnée disponible pour afficher les statistiques.")

elif action == "Gestion des emplacements":
    st.header("🏪 Gestion des Emplacements")
    
    # Charger et mettre à jour les emplacements
    df_emplacements = mettre_a_jour_statistiques_emplacements()
    
    # Onglets pour différentes actions
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Liste des emplacements", "➕ Ajouter un emplacement", "✏️ Modifier un emplacement", "📊 Statistiques détaillées"])
    
    with tab1:
        st.subheader("📋 Liste des emplacements")
        
        if not df_emplacements.empty:
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                types_emplacement = ["Tous"] + sorted(df_emplacements['Type_Zone'].unique().tolist())
                filtre_type = st.selectbox("Filtrer par type", types_emplacement, key="filtre_type_liste_emplacements")
            with col2:
                statuts = ["Tous"] + sorted(df_emplacements['Statut'].unique().tolist())
                filtre_statut = st.selectbox("Filtrer par statut", statuts, key="filtre_statut_liste_emplacements")
            with col3:
                responsables = ["Tous"] + sorted(df_emplacements['Responsable'].unique().tolist())
                filtre_responsable = st.selectbox("Filtrer par responsable", responsables)
            
            # Application des filtres
            df_filtre = df_emplacements.copy()
            if filtre_type != "Tous":
                df_filtre = df_filtre[df_filtre['Type_Zone'] == filtre_type]
            if filtre_statut != "Tous":
                df_filtre = df_filtre[df_filtre['Statut'] == filtre_statut]
            if filtre_responsable != "Tous":
                df_filtre = df_filtre[df_filtre['Responsable'] == filtre_responsable]
            
            # Affichage du tableau
            st.dataframe(df_filtre, use_container_width=True)
            
            # Statistiques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total emplacements", len(df_filtre))
            with col2:
                actifs = len(df_filtre[df_filtre['Statut'] == 'Actif'])
                st.metric("✅ Emplacements actifs", actifs)
            with col3:
                types_uniques = df_filtre['Type_Zone'].nunique()
                st.metric("🏪 Types d'emplacements", types_uniques)
            with col4:
                responsables_uniques = df_filtre['Responsable'].nunique()
                st.metric("👥 Responsables", responsables_uniques)
        else:
            st.warning("Aucun emplacement enregistré.")
    
    with tab2:
        st.subheader("➕ Ajouter un nouvel emplacement")
        
        with st.form("ajouter_emplacement"):
            col1, col2 = st.columns(2)
            
            with col1:
                nom_emplacement = st.text_input(
                    "Nom de l'emplacement *", 
                    placeholder="Ex: Atelier A - Zone 1"
                )
                
                type_zone = st.selectbox(
                    "Type de zone *", 
                    ["Atelier", "Stockage", "Magasin", "Réception"]
                )
                
                responsable = st.text_input(
                    "Responsable *", 
                    placeholder="Ex: Jean Dupont"
                )
            
            with col2:
                batiment = st.text_input(
                    "Batiment *", 
                    placeholder="Ex: Bâtiment 1"
                )
                
                niveau = st.text_input(
                    "Niveau *", 
                    placeholder="Ex: RDC"
                )
                
                capacite_max = st.number_input("Capacité maximale", min_value=1, value=100, step=1)
            
            
            submitted = st.form_submit_button("➕ Ajouter l'emplacement", use_container_width=True)
            
            if submitted:
                if not all([nom_emplacement, type_zone, batiment, niveau, responsable, capacite_max]):
                    st.error("❌ Veuillez remplir tous les champs obligatoires")
                else:
                    success, message = ajouter_emplacement(nom_emplacement, type_zone, batiment, niveau, responsable, capacite_max)
                    if success:
                        st.success(f"✅ {message}")
                        st.experimental_rerun()
                    else:
                        st.error(f"❌ {message}")
    
    with tab3:
        st.subheader("✏️ Modifier un emplacement")
        
        if not df_emplacements.empty:
            emplacement_a_modifier = st.selectbox(
                "Sélectionnez l'emplacement à modifier", 
                df_emplacements['Nom_Emplacement'].unique(),
                key="select_emplacement_modifier"
            )
            
            emplacement_data = df_emplacements[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier].iloc[0]
            
            with st.form("modifier_emplacement"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nouveau_nom = st.text_input("Nom de l'emplacement", value=emplacement_data['Nom_Emplacement'])
                    nouveau_type = st.selectbox(
                        "Type de zone", 
                        ["Atelier", "Stockage", "Magasin", "Réception"],
                        index=["Atelier", "Stockage", "Magasin", "Réception"].index(emplacement_data['Type_Zone']) if emplacement_data['Type_Zone'] in ["Atelier", "Stockage", "Magasin", "Réception"] else 0
                    )
                
                with col2:
                    nouveau_batiment = st.text_input("Batiment", value=emplacement_data['Batiment'])
                    nouveau_niveau = st.text_input("Niveau", value=emplacement_data['Niveau'])
                    nouveau_responsable = st.text_input("Responsable", value=emplacement_data['Responsable'])
                    nouvelle_capacite = st.number_input("Capacité maximale", min_value=1, value=int(emplacement_data['Capacite_Max']), step=1)
                
                submitted_modif = st.form_submit_button("✏️ Mettre à jour", use_container_width=True)
                
                if submitted_modif:
                    # Mettre à jour les données
                    df_emplacements.loc[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier, 'Nom_Emplacement'] = nouveau_nom
                    df_emplacements.loc[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier, 'Type_Zone'] = nouveau_type
                    df_emplacements.loc[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier, 'Batiment'] = nouveau_batiment
                    df_emplacements.loc[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier, 'Niveau'] = nouveau_niveau
                    df_emplacements.loc[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier, 'Responsable'] = nouveau_responsable
                    df_emplacements.loc[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier, 'Capacite_Max'] = nouvelle_capacite
                    df_emplacements.loc[df_emplacements['Nom_Emplacement'] == emplacement_a_modifier, 'Statut'] = 'Actif'
                    
                    if sauvegarder_emplacements(df_emplacements):
                        st.success("✅ Emplacement mis à jour avec succès!")
                        
                        # Si le nom a changé, mettre à jour aussi l'inventaire
                        if nouveau_nom != emplacement_a_modifier:
                            df.loc[df['Emplacement'] == emplacement_a_modifier, 'Emplacement'] = nouveau_nom
                            save_data(df)
                            st.info("📦 Inventaire mis à jour avec le nouveau nom de l'emplacement")
                        
                        st.experimental_rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
        else:
            st.warning("Aucun emplacement à modifier.")
    
    with tab4:
        st.subheader("📊 Statistiques détaillées par emplacement")
        
        if not df_emplacements.empty:
            # Charger les demandes pour analyser l'activité des emplacements
            df_demandes = charger_demandes()
            
            # Sélection de l'emplacement pour les détails
            emplacement_selectionne = st.selectbox(
                "Sélectionnez un emplacement pour voir les statistiques", 
                df_emplacements['Nom_Emplacement'].unique(),
                key="select_emplacement_stats"
            )
            
            # Informations de l'emplacement sélectionné
            emplacement_info = df_emplacements[df_emplacements['Nom_Emplacement'] == emplacement_selectionne].iloc[0]
            
            # Affichage des informations générales
            st.markdown("---")
            st.subheader(f"📋 Informations - {emplacement_info['Nom_Emplacement']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**🏪 Capacité maximale :** {emplacement_info['Capacite_Max']}")
                st.info(f"**👤 Responsable :** {emplacement_info['Responsable']}")
            with col2:
                st.info(f"**📍 Type de zone :** {emplacement_info['Type_Zone']}")
                st.info(f"**🏢 Batiment :** {emplacement_info['Batiment']}")
            with col3:
                st.info(f"**🏢 Niveau :** {emplacement_info['Niveau']}")
                st.info(f"**📅 Date création :** {emplacement_info['Date_Creation']}")
            
            if emplacement_info['Taux_Occupation']:
                st.info(f"**🏢 Taux d'occupation :** {emplacement_info['Taux_Occupation']}%")
            
            # Statistiques détaillées
            st.markdown("---")
            st.subheader("📊 Statistiques")
            
            # Produits de cet emplacement
            produits_emplacement = df[df['Emplacement'] == emplacement_selectionne]
            
            if not produits_emplacement.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📦 Nombre de produits", len(produits_emplacement))
                with col2:
                    stock_total = produits_emplacement['Quantite'].sum()
                    st.metric("📊 Stock total", stock_total)
                with col3:
                    valeur_stock = (produits_emplacement['Quantite'] * produits_emplacement['Prix_Unitaire']).sum()
                    st.metric("💰 Valeur du stock", f"{valeur_stock:,.2f} €")
                with col4:
                    prix_moyen = produits_emplacement['Prix_Unitaire'].mean()
                    st.metric("💵 Prix moyen", f"{prix_moyen:.2f} €")
                
                # Liste des produits
                st.markdown("---")
                st.subheader("📦 Produits de cet emplacement")
                
                # Ajouter des colonnes calculées pour l'affichage
                produits_display = produits_emplacement.copy()
                produits_display['Valeur_Stock'] = produits_display['Quantite'] * produits_emplacement['Prix_Unitaire']
                
                # Statut de stock
                produits_display['Statut_Stock'] = produits_display.apply(
                    lambda row: "🔴 Critique" if row['Quantite'] < row['Stock_Min'] 
                    else "🟡 Surstock" if row['Quantite'] > row['Stock_Max']
                    else "🟠 Faible" if row['Quantite'] <= row['Stock_Min'] + (row['Stock_Max'] - row['Stock_Min']) * 0.3
                    else "🟢 Normal", axis=1
                )
                
                # Colonnes à afficher
                colonnes_produits = ['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Stock_Max', 'Prix_Unitaire', 'Valeur_Stock', 'Statut_Stock', 'Emplacement']
                st.dataframe(produits_display[colonnes_produits].round(2), use_container_width=True)
                
                # Alertes pour cet emplacement
                alertes_critique = produits_emplacement[produits_emplacement['Quantite'] < produits_emplacement['Stock_Min']]
                alertes_surstock = produits_emplacement[produits_emplacement['Quantite'] > produits_emplacement['Stock_Max']]
                
                # Produits bientôt en rupture (entre min et 30% de la plage min-max)
                seuil_alerte_emplacement = produits_emplacement['Stock_Min'] + (produits_emplacement['Stock_Max'] - produits_emplacement['Stock_Min']) * 0.3
                alertes_bientot = produits_emplacement[(produits_emplacement['Quantite'] >= produits_emplacement['Stock_Min']) & (produits_emplacement['Quantite'] <= seuil_alerte_emplacement)]
                
                if not alertes_critique.empty or not alertes_bientot.empty or not alertes_surstock.empty:
                    st.markdown("---")
                    st.subheader("⚠️ Alertes de stock")
                    
                    if not alertes_critique.empty:
                        st.error(f"🔴 **{len(alertes_critique)} produit(s) en stock critique** nécessitent un réapprovisionnement urgent")
                        alertes_critique_display = alertes_critique.copy()
                        alertes_critique_display['Recommandation'] = alertes_critique_display['Stock_Max'] - alertes_critique_display['Quantite']
                        st.dataframe(alertes_critique_display[['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Stock_Max', 'Recommandation']], use_container_width=True)
                    
                    if not alertes_bientot.empty:
                        st.warning(f"🟠 **{len(alertes_bientot)} produit(s) bientôt en rupture** - réapprovisionnement recommandé")
                        alertes_bientot_display = alertes_bientot.copy()
                        alertes_bientot_display['Seuil_Alerte'] = seuil_alerte_emplacement[alertes_bientot.index].round(1)
                        alertes_bientot_display['Recommandation'] = alertes_bientot_display['Stock_Max'] - alertes_bientot_display['Quantite']
                        st.dataframe(alertes_bientot_display[['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Seuil_Alerte', 'Stock_Max', 'Recommandation']], use_container_width=True)
                    
                    if not alertes_surstock.empty:
                        st.warning(f"🟡 **{len(alertes_surstock)} produit(s) en surstock**")
                        st.dataframe(alertes_surstock[['Produits', 'Reference', 'Quantite', 'Stock_Max']], use_container_width=True)
                
                # Graphique de répartition des stocks pour cet emplacement
                if len(produits_emplacement) > 1:
                    st.markdown("---")
                    st.subheader("📈 Répartition des stocks")
                    
                    fig_stock = px.bar(
                        produits_emplacement, 
                        x='Produits', 
                        y='Quantite',
                        title=f'Stock par produit - {emplacement_info["Nom_Emplacement"]}',
                        labels={'Quantite': 'Quantité en stock', 'Produits': 'Produits'}
                    )
                    fig_stock.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig_stock, use_container_width=True)
            else:
                st.warning(f"Aucun produit trouvé pour l'emplacement {emplacement_info['Nom_Emplacement']}")
        else:
            st.warning("Aucune donnée disponible pour afficher les statistiques.")


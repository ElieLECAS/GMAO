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
    initial_sidebar_state="expanded"
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
        
        # Ajouter une colonne Quantite avec des valeurs aléatoires si elle n'existe pas
        if 'Quantite' not in df.columns:
            import random
            # Générer des quantités aléatoires basées sur les stocks min/max pour simuler un état vivant
            df['Quantite'] = df.apply(lambda row: random.randint(
                max(0, int(row['Stock_Min']) - 5),  # Peut être en dessous du minimum
                int(row['Stock_Max']) + random.randint(0, 20)  # Peut dépasser le maximum
            ), axis=1)
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
        # Sauvegarder dans le fichier enrichi pour maintenir la persistance
        fichier_enrichi = "data/inventaire_avec_references.xlsx"
        df.to_excel(fichier_enrichi, index=False, engine='openpyxl')
        
        # Aussi sauvegarder une copie de sauvegarde
        df.to_excel("data/inventaire_sauvegarde.xlsx", index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du fichier Excel: {str(e)}")

def log_mouvement(produit, nature, quantite_mouvement, quantite_apres, quantite_avant):
    os.makedirs("data", exist_ok=True)
    file_path = "data/historique.xlsx"
    new_row = {
        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Produit': produit,
        'Nature': nature,
        'Quantite_Mouvement': quantite_mouvement,
        'Quantite_Avant': quantite_avant,
        'Quantite_Apres': quantite_apres
    }
    if os.path.exists(file_path):
        df_hist = pd.read_excel(file_path, engine='openpyxl')
        df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df_hist = pd.DataFrame([new_row])
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
        nom = st.text_input("Entrez le nom du produit")
        if nom:
            result = df[df['Produits'].str.contains(nom, case=False)]
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
    
    # Produits en dessous du stock minimum
    alertes_min = df[df['Quantite'] < df['Stock_Min']]
    
    # Produits au-dessus du stock maximum
    alertes_max = df[df['Quantite'] > df['Stock_Max']]
    
    if not alertes_min.empty or not alertes_max.empty:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚠️ Alertes de Stock")
        
        if not alertes_min.empty:
            st.sidebar.markdown("**🔴 Stock insuffisant :**")
            for _, produit in alertes_min.iterrows():
                st.sidebar.error(f"**{produit['Produits']}** : {produit['Quantite']} < {produit['Stock_Min']}")
        
        if not alertes_max.empty:
            st.sidebar.markdown("**🟡 Surstock :**")
            for _, produit in alertes_max.iterrows():
                st.sidebar.warning(f"**{produit['Produits']}** : {produit['Quantite']} > {produit['Stock_Max']}")

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

if st.sidebar.button("📊 Inventaire", use_container_width=True, help="Ajustement d'inventaire"):
    st.session_state.action = "Inventaire"

if st.sidebar.button("🔍 Rechercher", use_container_width=True):
    st.session_state.action = "Rechercher un produit"

# Section QR Codes - Outils mobiles
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 **QR Codes**")

if st.sidebar.button("📦 QR Produits", use_container_width=True, help="QR codes des produits"):
    st.session_state.action = "QR Code produit"

if st.sidebar.button("🏭 QR Tables", use_container_width=True, help="QR codes des tables d'atelier"):
    st.session_state.action = "QR Code tables d'atelier"

# Section administration - Moins fréquent
with st.sidebar.expander("⚙️ **Administration**"):
    if st.button("➕ Ajouter produit", use_container_width=True):
        st.session_state.action = "Ajouter un produit"
    
    if st.button("✏️ Modifier produit", use_container_width=True):
        st.session_state.action = "Modifier un produit"
    
    if st.button("📋 Gérer tables", use_container_width=True):
        st.session_state.action = "Gérer les tables"
    
    if st.button("🏪 Fournisseurs", use_container_width=True):
        st.session_state.action = "Fournisseurs"

# Section rapports - Moins fréquent
with st.sidebar.expander("📊 **Rapports**"):
    if st.button("🚨 Alertes stock", use_container_width=True):
        st.session_state.action = "Alertes de stock"
    
    if st.button("📈 Historique", use_container_width=True):
        st.session_state.action = "Historique des mouvements"

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
            filtre_statut = st.selectbox("Filtrer par statut", statuts)
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
                    
                    if demande['Date_Traitement']:
                        st.write(f"**⏰ Traité le :** {demande['Date_Traitement']}")
                        st.write(f"**👨‍💼 Traité par :** {demande['Traite_Par']}")
                
                with col2:
                    st.write(f"**📝 Motif :** {demande['Motif']}")
                    if demande['Commentaires']:
                        st.write(f"**💬 Commentaires :** {demande['Commentaires']}")
                
                # Détail des produits demandés
                st.write("**🛠️ Produits demandés :**")
                try:
                    import ast
                    produits_data = ast.literal_eval(demande['Produits_Demandes'])
                    
                    # Affichage des informations additionnelles si disponibles
                    if isinstance(produits_data, dict):
                        if 'chantier' in produits_data:
                            st.write(f"**🏗️ Chantier :** {produits_data['chantier']}")
                        if 'urgence' in produits_data:
                            st.write(f"**⚡ Urgence :** {produits_data['urgence']}")
                        if 'date_souhaitee' in produits_data:
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
                                                            stock_actuel
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

elif action == "Ajouter un produit":
    st.header("Ajouter un nouveau produit")
    
    with st.form("ajout_produit"):
        produit = st.text_input("Nom du produit")
        reference = st.text_input("Référence (code-barres)")
        quantite = st.number_input("Quantité", min_value=0)
        
        col1, col2 = st.columns(2)
        with col1:
            stock_min = st.number_input("Stock minimum", min_value=0, value=10)
        with col2:
            stock_max = st.number_input("Stock maximum", min_value=1, value=100)
        
        emplacement = st.selectbox("Emplacement", ["Atelier A", "Atelier B", "Stockage"])
        fournisseur = st.selectbox("Fournisseur", ["Fournisseur A", "Fournisseur B", "Fournisseur C"])
        prix = st.number_input("Prix unitaire", min_value=0.0)
        
        submitted = st.form_submit_button("Ajouter")
        
        if submitted:
            if stock_min >= stock_max:
                st.error("Le stock minimum doit être inférieur au stock maximum")
            else:
                new_row = pd.DataFrame({
                    'Produits': [produit],
                    'Reference': [reference],
                    'Quantite': [quantite],
                    'Stock_Min': [stock_min],
                    'Stock_Max': [stock_max],
                    'Emplacement': [emplacement],
                    'Fournisseur': [fournisseur],
                    'Date_Entree': [datetime.now().strftime("%Y-%m-%d")],
                    'Prix_Unitaire': [prix]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("Produit ajouté avec succès!")
                st.experimental_rerun()

elif action == "Modifier un produit":
    st.header("Modifier un produit")
    
    if not df.empty:
        produit_to_edit = st.selectbox("Sélectionner le produit à modifier", df['Produits'].unique())
        produit_data = df[df['Produits'] == produit_to_edit].iloc[0]
        
        with st.form("modifier_produit"):
            quantite = st.number_input("Nouvelle quantité", value=int(produit_data['Quantite']))
            
            col1, col2 = st.columns(2)
            with col1:
                stock_min = st.number_input("Stock minimum", min_value=0, value=int(produit_data['Stock_Min']))
            with col2:
                stock_max = st.number_input("Stock maximum", min_value=1, value=int(produit_data['Stock_Max']))
            
            emplacement = st.selectbox("Nouvel emplacement", df['Emplacement'].unique(), 
                                     index=list(df['Emplacement'].unique()).index(produit_data['Emplacement']))
            
            submitted = st.form_submit_button("Mettre à jour")
            
            if submitted:
                if stock_min >= stock_max:
                    st.error("Le stock minimum doit être inférieur au stock maximum")
                else:
                    df.loc[df['Produits'] == produit_to_edit, 'Quantite'] = quantite
                    df.loc[df['Produits'] == produit_to_edit, 'Stock_Min'] = stock_min
                    df.loc[df['Produits'] == produit_to_edit, 'Stock_Max'] = stock_max
                    df.loc[df['Produits'] == produit_to_edit, 'Emplacement'] = emplacement
                    save_data(df)
                    st.success("Produit mis à jour avec succès!")
                    st.experimental_rerun()

elif action == "Rechercher un produit":
    st.header("🔍 Rechercher un produit")
    
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
        pourcentage_stock = (quantite_actuelle - stock_min) / (stock_max - stock_min) * 100 if stock_max > stock_min else 50
        
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
        
        # Barre de progression visuelle
        if stock_max > stock_min:
            progress_value = max(0, min(100, pourcentage_stock))
            st.progress(progress_value / 100)
            st.caption(f"Position dans la plage de stock : {progress_value:.1f}%")
        
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
                # Filtrer pour le produit actuel
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
                        
                        # Affichage du mouvement
                        st.markdown(f"""
                        <div style="background: {couleur}; border-left: 4px solid {couleur_bordure}; 
                                    padding: 1rem; margin: 0.5rem 0; border-radius: 5px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>{icone} {mouvement['Nature']}</strong><br>
                                    <span style="color: #666;">📅 {date_formatee}</span>
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
                use_container_width=True
            )
        
        with col2:
            st.markdown("**📱 QR Code à scanner :**")
            
            # Afficher le QR code
            st.image(buf.getvalue(), caption=f"QR Code - {produit_trouve['Produits']}")
            
            st.caption("💡 Scannez ce code avec votre smartphone ou scanner pour identifier rapidement ce produit")
    

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
                log_mouvement(produit_trouve['Produits'], "Entrée", quantite_ajout, nouvelle_quantite, quantite_actuelle)
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
                    log_mouvement(produit_trouve['Produits'], "Sortie", quantite_retrait, nouvelle_quantite, quantite_actuelle)
                    st.success(f"Sortie de {quantite_retrait} unités pour {produit_trouve['Produits']} effectuée.")
                    st.experimental_rerun()
                else:
                    st.error("Stock insuffisant pour effectuer la sortie.")
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Inventaire":
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
                        "Inventaire",
                        abs(nouvelle_quantite - quantite_actuelle),
                        nouvelle_quantite,
                        quantite_actuelle
                    )
                    st.success(f"Inventaire ajusté pour {produit_trouve['Produits']} : {quantite_actuelle} → {nouvelle_quantite}")
                    st.experimental_rerun()
                else:
                    st.info("La quantité saisie est identique à la quantité actuelle.")
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

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
            
            colonnes_bientot = ['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Seuil_Alerte', 'Stock_Max', 'Fournisseur']
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
    st.header("Historique des mouvements de stock")
    import pandas as pd
    import os
    file_path = "data/historique.xlsx"
    if os.path.exists(file_path):
        df_hist = pd.read_excel(file_path, engine='openpyxl')
        if not df_hist.empty:
            df_hist = df_hist.sort_values(by="Date", ascending=False)
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                types = ["Tous"] + sorted(df_hist['Nature'].dropna().unique().tolist())
                type_filtre = st.selectbox("Type de mouvement", types)
            with col2:
                produits = ["Tous"] + sorted(df_hist['Produit'].dropna().unique().tolist())
                produit_filtre = st.selectbox("Produit", produits)
            with col3:
                min_date = pd.to_datetime(df_hist['Date']).min().date()
                max_date = pd.to_datetime(df_hist['Date']).max().date()
                date_range = st.date_input("Plage de dates", (min_date, max_date))
            # Application des filtres
            df_filtre = df_hist.copy()
            if type_filtre != "Tous":
                df_filtre = df_filtre[df_filtre['Nature'] == type_filtre]
            if produit_filtre != "Tous":
                df_filtre = df_filtre[df_filtre['Produit'] == produit_filtre]
            if date_range:
                df_filtre = df_filtre[(pd.to_datetime(df_filtre['Date']).dt.date >= date_range[0]) & (pd.to_datetime(df_filtre['Date']).dt.date <= date_range[1])]
            st.dataframe(df_filtre)
        else:
            st.info("Aucun mouvement enregistré pour le moment.")
    else:
        st.info("Aucun mouvement enregistré pour le moment.")

elif action == "QR Code produit":
    st.header("📱 QR Code des Produits")
    
    if not df.empty:
        # Onglets pour différentes options
        tab1, tab2 = st.tabs(["🔍 QR Code individuel", "📦 Tous les QR codes"])
        
        with tab1:
            st.subheader("🔍 Génération d'un QR code individuel")
            
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
                    use_container_width=True
                )
        
        with tab2:
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
                stock_uniquement = st.checkbox("Produits en stock uniquement", value=True)
            
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
                    taille_qr = st.selectbox("Taille des QR codes", ["Petit (4)", "Moyen (6)", "Grand (8)"], index=1)
                    box_size = {"Petit (4)": 4, "Moyen (6)": 6, "Grand (8)": 8}[taille_qr]
                with col2:
                    colonnes_par_ligne = st.selectbox("QR codes par ligne", [2, 3, 4, 5], index=1)
                
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
                                    st.image(buf.getvalue(), caption=f"**{produit_row['Produits']}**\nRéf: {produit_row['Reference']}\nStock: {produit_row['Quantite']}")
                                    
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

elif action == "QR Code tables d'atelier":
    st.header("🏭 QR Code des Tables d'Atelier")
    
    # Charger les tables d'atelier
    df_tables = charger_tables_atelier()
    
    if not df_tables.empty:
        # Onglets pour différentes options
        tab1, tab2 = st.tabs(["🔍 QR Code individuel", "🏭 Toutes les tables"])
        
        with tab1:
            st.subheader("🔍 Génération d'un QR code individuel")
            
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
                    use_container_width=True
                )
        
        with tab2:
            st.subheader("🏭 Génération de tous les QR codes")
            
            # Filtres pour sélectionner les tables
            col1, col2, col3 = st.columns(3)
            with col1:
                types_atelier = ["Tous"] + sorted(df_tables['Type_Atelier'].unique().tolist())
                filtre_type = st.selectbox("Filtrer par type d'atelier", types_atelier)
            with col2:
                statuts = ["Tous"] + sorted(df_tables['Statut'].unique().tolist())
                filtre_statut = st.selectbox("Filtrer par statut", statuts)
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
                    
                st.warning("Aucune table ne correspond aux filtres sélectionnés.")
        
    else:
        st.warning("Aucune table d'atelier disponible. Veuillez d'abord créer des tables.")

elif action == "Gérer les tables":
    st.header("📋 Gestion des Tables d'Atelier")
    st.info("💡 Gérez les tables d'atelier et leurs informations")
    
    # Charger les tables d'atelier
    df_tables = charger_tables_atelier()
    
    # Onglets pour différentes actions
    tab1, tab2, tab3 = st.tabs(["📋 Liste des tables", "➕ Ajouter une table", "✏️ Modifier une table"])
    
    with tab1:
        st.subheader("📋 Liste des tables d'atelier")
        
        if not df_tables.empty:
            # Filtres
            col1, col2, col3 = st.columns(3)
            with col1:
                types_atelier = ["Tous"] + sorted(df_tables['Type_Atelier'].unique().tolist())
                filtre_type = st.selectbox("Filtrer par type", types_atelier)
            with col2:
                statuts = ["Tous"] + sorted(df_tables['Statut'].unique().tolist())
                filtre_statut = st.selectbox("Filtrer par statut", statuts)
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

elif action == "Fournisseurs":
    st.header("🏪 Gestion des Fournisseurs")
    st.info("💡 Gérez vos fournisseurs et consultez leurs statistiques")
    
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
                produits_display['Valeur_Stock'] = produits_display['Quantite'] * produits_display['Prix_Unitaire']
                
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
                
                if not alertes_critique.empty or not alertes_surstock.empty:
                    st.markdown("---")
                    st.subheader("⚠️ Alertes de stock")
                    
                    if not alertes_critique.empty:
                        st.error(f"🔴 **{len(alertes_critique)} produit(s) en stock critique** nécessitent un réapprovisionnement urgent")
                        st.dataframe(alertes_critique[['Produits', 'Reference', 'Quantite', 'Stock_Min']], use_container_width=True)
                    
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


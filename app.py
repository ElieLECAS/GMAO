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
st.set_page_config(page_title="GMAO - Gestion de Stock", layout="wide")

# Titre de l'application
st.title("📦 Système de Gestion de Stock")

# Données initiales
INITIAL_DATA = {
    'Produits': ['Tournevis cruciforme', 'Marteau 500g', 'Perceuse sans fil', 'Vis 6x50mm', 'Clé à molette'],
    'Reference': ['TS001', 'MH001', 'PS001', 'V001', 'CM001'],
    'Quantite': [50, 30, 15, 1000, 25],
    'Stock_Min': [10, 5, 2, 100, 5],
    'Stock_Max': [100, 50, 20, 2000, 50],
    'Emplacement': ['Atelier A', 'Atelier B', 'Atelier A', 'Stockage', 'Atelier B'],
    'Fournisseur': ['Fournisseur A', 'Fournisseur B', 'Fournisseur C', 'Fournisseur A', 'Fournisseur B'],
    'Date_Entree': ['2024-03-15', '2024-03-14', '2024-03-13', '2024-03-12', '2024-03-11'],
    'Prix_Unitaire': [15.99, 25.50, 89.99, 0.15, 12.75]
}

# Chargement des données
def load_data():
    # Créer le dossier data s'il n'existe pas
    os.makedirs("data", exist_ok=True)
    
    file_path = "data/inventaire.xlsx"
    
    # Si le fichier n'existe pas, créer un nouveau fichier avec les données initiales
    if not os.path.exists(file_path):
        df = pd.DataFrame(INITIAL_DATA)
        df.to_excel(file_path, index=False, engine='openpyxl')
        return df
    
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Migration : ajouter les colonnes Stock_Min et Stock_Max si elles n'existent pas
        if 'Stock_Min' not in df.columns:
            df['Stock_Min'] = 10  # Valeur par défaut
        if 'Stock_Max' not in df.columns:
            df['Stock_Max'] = 100  # Valeur par défaut
            
        # Sauvegarder le fichier mis à jour
        df.to_excel(file_path, index=False, engine='openpyxl')
        return df
        
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier Excel: {str(e)}")
        # En cas d'erreur, créer un nouveau fichier avec les données initiales
        df = pd.DataFrame(INITIAL_DATA)
        df.to_excel(file_path, index=False, engine='openpyxl')
        return df

# Fonction pour sauvegarder les données
def save_data(df):
    try:
        df.to_excel("data/inventaire.xlsx", index=False, engine='openpyxl')
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
    search_type = st.radio("Type de recherche", ["Par référence", "Par nom", "Scanner externe"])
    
    produit_trouve = None
    
    if search_type == "Scanner externe":
        st.info("🔍 **Scanner externe connecté**")
        st.write("💡 Utilisez votre scanner USB/Bluetooth pour scanner le code-barres ou QR code")
        st.write("📋 Types de scanners recommandés :")
        st.write("- 🔲 **Scanner 2D** (pour QR codes et codes-barres)")
        st.write("- 🔍 **Douchette 2D USB** (branchement plug-and-play)")
        st.write("- 📱 **Scanner Bluetooth** (connexion sans fil)")
        
        # Champ d'input qui recevra automatiquement les données du scanner
        code_scanne = st.text_input(
            "📄 Code scanné", 
            placeholder="Positionnez le curseur ici et scannez votre code...",
            help="Le scanner USB tapera automatiquement le code dans ce champ",
            key="scanner_input"
        )
        
        if code_scanne:
            # Nettoyer le code (supprimer les espaces, retours à la ligne, etc.)
            code_scanne = code_scanne.strip()
            
            if len(code_scanne) > 0:
                # Rechercher d'abord par référence exacte
                result = df[df['Reference'] == code_scanne]
                
                if not result.empty:
                    produit_trouve = result.iloc[0]
                    if mode == "affichage":
                        st.success(f"✅ Produit trouvé par référence : **{produit_trouve['Produits']}**")
                        st.dataframe(result)
                    else:
                        st.success(f"✅ Produit trouvé : **{produit_trouve['Produits']}**")
                else:
                    # Si pas trouvé par référence, essayer par code-barres (si différent)
                    # ou recherche dans le nom du produit
                    result_nom = df[df['Produits'].str.contains(code_scanne, case=False, na=False)]
                    
                    if not result_nom.empty:
                        if mode == "affichage":
                            st.info(f"🔍 Produit(s) trouvé(s) par nom contenant '{code_scanne}':")
                            st.dataframe(result_nom)
                        elif len(result_nom) == 1:
                            produit_trouve = result_nom.iloc[0]
                            st.success(f"✅ Produit trouvé par nom : **{produit_trouve['Produits']}**")
                        else:
                            st.info(f"🔍 {len(result_nom)} produits trouvés par nom:")
                            st.dataframe(result_nom[['Produits', 'Reference', 'Quantite']])
                            reference_choisie = st.selectbox("Choisissez la référence:", result_nom['Reference'].tolist())
                            if reference_choisie:
                                produit_trouve = result_nom[result_nom['Reference'] == reference_choisie].iloc[0]
                    else:
                        st.warning(f"❌ Aucun produit trouvé avec le code : '{code_scanne}'")
                        st.info("💡 Vérifiez que :")
                        st.write("- Le produit existe dans votre inventaire")
                        st.write("- La référence est correcte")
                        st.write("- Le scanner fonctionne correctement")
    
    elif search_type == "Par référence":
        reference = st.text_input("Entrez la référence du produit")
        if reference:
            result = df[df['Reference'] == reference]
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
                    reference_choisie = st.selectbox("Choisissez la référence:", result['Reference'].tolist())
                    if reference_choisie:
                        produit_trouve = result[result['Reference'] == reference_choisie].iloc[0]
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
with st.sidebar.expander("🔍 Guide Scanners", expanded=False):
    st.markdown("### Scanners recommandés")
    st.write("**📱 Pour QR codes + codes-barres :**")
    st.write("- Scanner 2D USB (HID)")
    st.write("- Douchette 2D Bluetooth")
    st.write("- Scanner portable 2D")
    
    st.write("**⚠️ Non compatible :**")
    st.write("- Scanner laser classique")
    st.write("- Scanner 1D uniquement")
    
    st.markdown("### Installation")
    st.write("1. 🔌 Branchez le scanner USB")
    st.write("2. 📱 Ou appairez en Bluetooth") 
    st.write("3. ✅ Prêt à l'emploi !")
    
    st.markdown("### Utilisation")
    st.write("1. 📍 Cliquez dans le champ")
    st.write("2. 🔍 Scannez le code")
    st.write("3. ⚡ Le code apparaît automatiquement")

# Sidebar pour les actions
st.sidebar.title("Actions")
action = st.sidebar.selectbox(
    "Choisir une action",
    [
        "Magasin",
        "Demande de matériel",
        "Gestion des demandes",
        "Ajouter un produit",
        "Modifier un produit",
        "Rechercher un produit",
        "Entrée de stock",
        "Sortie de stock",
        "Inventaire",
        "Alertes de stock",
        "Historique des mouvements",
        "QR Code produit"
    ]
)

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
    st.info("💡 Remplissez ce formulaire pour demander du matériel au magasinier")
    
    if not df.empty:
        # Informations du demandeur
        with st.expander("👤 Informations du demandeur", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                demandeur = st.text_input("Nom du demandeur *", placeholder="Prénom NOM")
            with col2:
                chantier = st.selectbox("Chantier/Atelier *", ["Atelier A", "Atelier B", "Chantier 1", "Chantier 2", "Maintenance"])
        
        # Sélection des produits
        st.subheader("🛠️ Sélection des produits")
        
        # Afficher les produits disponibles en stock
        df_disponible = df[df['Quantite'] > 0].copy()
        
        if df_disponible.empty:
            st.warning("Aucun produit en stock actuellement.")
        else:
            # Initialiser le panier dans la session
            if 'panier_demande' not in st.session_state:
                st.session_state.panier_demande = {}
            
            # Section de recherche rapide
            with st.expander("🔍 Recherche rapide de produits", expanded=False):
                st.info("💡 Recherchez un produit spécifique pour l'ajouter rapidement à votre demande")
                
                produit_trouve = rechercher_produit(df_disponible, mode="selection")
                
                if produit_trouve is not None:
                    # Affichage du produit trouvé avec option d'ajout
                    # st.success(f"**Produit trouvé :** {produit_trouve['Produits']}")
                    
                    # Informations du produit
                    col_info, col_action = st.columns([2, 1])
                    
                    with col_info:
                        # Statut de stock avec couleur
                        if produit_trouve['Quantite'] < produit_trouve['Stock_Min']:
                            statut = "🔴 Stock critique"
                        elif produit_trouve['Quantite'] <= produit_trouve['Stock_Min'] + (produit_trouve['Stock_Max'] - produit_trouve['Stock_Min']) * 0.3:
                            statut = "🟠 Stock faible"
                        else:
                            statut = "🟢 Disponible"
                        
                        st.write(f"**{produit_trouve['Produits']}**")
                        st.write(f"**Référence :** {produit_trouve['Reference']}")
                        st.write(f"**Stock :** {produit_trouve['Quantite']} - {statut}")
                        st.write(f"**Emplacement :** {produit_trouve['Emplacement']}")
                    
                    with col_action:
                        # Formulaire d'ajout au panier
                        with st.container():
                            quantite_recherche = st.number_input(
                                "Quantité", 
                                min_value=1, 
                                max_value=int(produit_trouve['Quantite']), 
                                value=1,
                                step=1,
                                key=f"qty_search_{produit_trouve['Reference']}"
                            )
                            
                            if st.button("➕ Ajouter au panier", key=f"add_search_{produit_trouve['Reference']}", use_container_width=True):
                                st.session_state.panier_demande[produit_trouve['Reference']] = {
                                    'produit': produit_trouve['Produits'],
                                    'quantite': quantite_recherche,
                                    'emplacement': produit_trouve['Emplacement']
                                }
                                st.success(f"✅ {quantite_recherche} x {produit_trouve['Produits']} ajouté(s) au panier")
                                st.experimental_rerun()
            
            st.divider()
            
            # Affichage du panier
            st.subheader("🛒 Votre panier")
            if st.session_state.panier_demande:
                total_articles = 0
                for ref, item in st.session_state.panier_demande.items():
                    col_item, col_qty, col_remove = st.columns([3, 1, 1])
                    
                    with col_item:
                        st.write(f"**{item['produit']}**")
                        st.write(f"Réf: {ref} - Emplacement: {item['emplacement']}")
                    
                    with col_qty:
                        st.write(f"**Quantité: {item['quantite']}**")
                    
                    with col_remove:
                        if st.button(f"❌ Retirer", key=f"remove_{ref}", use_container_width=True):
                            del st.session_state.panier_demande[ref]
                            st.experimental_rerun()
                    
                    st.divider()
                    total_articles += item['quantite']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total articles", total_articles)
                with col2:
                    if st.button("🗑️ Vider le panier", use_container_width=True):
                        st.session_state.panier_demande = {}
                        st.experimental_rerun()
            else:
                st.info("Votre panier est vide. Utilisez la recherche ci-dessus pour ajouter des produits.")
        
        # Finalisation de la demande
        if st.session_state.panier_demande:
            st.subheader("📝 Finalisation de la demande")
            
            col1, col2 = st.columns(2)
            with col1:
                urgence = st.selectbox("Niveau d'urgence", ["Normal", "Urgent", "Très urgent"])
            with col2:
                date_souhaitee = st.date_input("Date souhaitée", datetime.now().date())
            
            motif = st.text_area(
                "Motif de la demande *", 
                placeholder="Décrivez l'utilisation prévue du matériel...",
                help="Expliquez pourquoi vous avez besoin de ce matériel"
            )
            
            # Vérifications avant soumission
            if st.button("📤 Soumettre la demande", type="primary"):
                if not demandeur:
                    st.error("❌ Veuillez saisir votre nom")
                elif not motif:
                    st.error("❌ Veuillez indiquer le motif de votre demande")
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
                    
                    # Vider le panier
                    st.session_state.panier_demande = {}
                    
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
    st.info("👥 Interface magasinier pour traiter les demandes")
    
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
    st.header("Rechercher un produit")
    
    produit_trouve = rechercher_produit(df, mode="affichage")

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
            
            quantite_ajout = st.number_input("Quantité à ajouter", min_value=1, step=1, key="ajout_entree")
            
            # Prévisualisation du nouveau stock
            nouveau_stock = quantite_actuelle + quantite_ajout
            if nouveau_stock > stock_max:
                st.warning(f"⚠️ Attention : après cette entrée, le stock sera de {nouveau_stock} (au-dessus du maximum de {stock_max})")
            
            if st.button("Valider l'entrée", type="primary"):
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
            
            quantite_retrait = st.number_input("Quantité à retirer", min_value=1, step=1, key="retrait_sortie")
            
            # Prévisualisation du nouveau stock
            nouveau_stock = quantite_actuelle - quantite_retrait
            if nouveau_stock < 0:
                st.error(f"❌ Impossible : stock insuffisant (quantité actuelle : {quantite_actuelle})")
            elif nouveau_stock < stock_min:
                st.warning(f"⚠️ Attention : après cette sortie, le stock sera de {nouveau_stock} (en dessous du minimum de {stock_min})")
            
            if st.button("Valider la sortie", type="primary"):
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
            
            nouvelle_quantite = st.number_input("Nouvelle quantité (après inventaire)", min_value=0, value=quantite_actuelle, step=1, key="nv_inventaire")
            
            # Prévisualisation du statut après ajustement
            if nouvelle_quantite != quantite_actuelle:
                if nouvelle_quantite < stock_min:
                    st.warning(f"⚠️ Après ajustement : stock critique ({nouvelle_quantite} < {stock_min})")
                elif nouvelle_quantite > stock_max:
                    st.warning(f"⚠️ Après ajustement : surstock ({nouvelle_quantite} > {stock_max})")
                else:
                    st.success(f"✅ Après ajustement : stock normal ({stock_min} ≤ {nouvelle_quantite} ≤ {stock_max})")
            
            if st.button("Valider l'ajustement", type="primary"):
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
    st.header("QR Code d'un produit")
    if not df.empty:
        produit_select = st.selectbox("Sélectionnez un produit", df['Produits'].unique(), key="qr")
        reference = df[df['Produits'] == produit_select]['Reference'].iloc[0]
        st.write(f"**Référence (code-barres) :** {reference}")
        # Génération du QR code
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(reference)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"QR Code pour {produit_select}")
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")
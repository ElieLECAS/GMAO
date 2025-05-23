import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import openpyxl
import qrcode
from io import BytesIO
from PIL import Image
import cv2
from pyzbar.pyzbar import decode
import numpy as np

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
    search_type = st.radio("Type de recherche", ["Par référence", "Par nom", "Scanner QR Code"])
    
    produit_trouve = None
    
    if search_type == "Scanner QR Code":
        st.write("Présentez le QR code devant la caméra")
        if st.button("Démarrer le scan"):
            code = scan_qr_code()
            if code:
                result = df[df['Reference'] == code]
                if not result.empty:
                    produit_trouve = result.iloc[0]
                    if mode == "affichage":
                        st.dataframe(result)
                    else:
                        st.success(f"Produit trouvé : {produit_trouve['Produits']}")
                else:
                    st.warning("Aucun produit trouvé avec cette référence.")
    
    elif search_type == "Par référence":
        reference = st.text_input("Entrez la référence du produit")
        if reference:
            result = df[df['Reference'] == reference]
            if not result.empty:
                produit_trouve = result.iloc[0]
                if mode == "affichage":
                    st.dataframe(result)
                else:
                    st.success(f"Produit trouvé : {produit_trouve['Produits']}")
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
                    st.success(f"Produit trouvé : {produit_trouve['Produits']}")
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

# Sidebar pour les actions
st.sidebar.title("Actions")
action = st.sidebar.selectbox(
    "Choisir une action",
    [
        "Voir l'inventaire",
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

# Fonction pour scanner le QR code
def scan_qr_code():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Impossible d'accéder à la caméra")
        return None
    
    stframe = st.empty()
    stop_button = st.button("Arrêter le scan")
    
    while not stop_button:
        ret, frame = cap.read()
        if not ret:
            st.error("Erreur lors de la lecture de la caméra")
            break
            
        # Détection des QR codes
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            # Dessiner un rectangle autour du QR code
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                cv2.polylines(frame, [hull], True, (0, 255, 0), 2)
            else:
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], True, (0, 255, 0), 2)
            
            # Afficher le code
            code = obj.data.decode('utf-8')
            cv2.putText(frame, code, (points[0][0], points[0][1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Convertir l'image pour Streamlit
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            stframe.image(frame_rgb)
            
            # Libérer la caméra et retourner le code
            cap.release()
            return code
        
        # Convertir l'image pour Streamlit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        stframe.image(frame_rgb)
    
    cap.release()
    return None

if action == "Voir l'inventaire":
    st.header("Inventaire actuel")
    if not df.empty:
        # Ajouter une colonne de statut de stock avec la même logique que les alertes
        df_display = df.copy()
        
        # Calcul du seuil d'alerte (même logique que dans les alertes)
        seuil_alerte = df['Stock_Min'] + (df['Stock_Max'] - df['Stock_Min']) * 0.3
        
        df_display['Statut_Stock'] = df_display.apply(
            lambda row: "🔴 Critique" if row['Quantite'] < row['Stock_Min'] 
            else "🟡 Surstock" if row['Quantite'] > row['Stock_Max']
            else "🟠 Bientôt rupture" if row['Quantite'] <= seuil_alerte.loc[row.name]
            else "🟢 Normal", axis=1
        )
        

        

        
        # Statistiques rapides
        col1, col2, col3, col4 = st.columns(4)
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
            
        # Réorganiser les colonnes pour l'affichage
        colonnes_affichage = ['Produits', 'Reference', 'Quantite', 'Stock_Min', 'Stock_Max', 'Statut_Stock', 'Emplacement', 'Fournisseur', 'Date_Entree', 'Prix_Unitaire']
        st.dataframe(df_display[colonnes_affichage])

        # Graphique de la répartition des stocks
        fig = px.bar(df, x='Produits', y='Quantite', title='Répartition des stocks par produit')
        st.plotly_chart(fig)

    else:
        st.warning("Aucune donnée disponible dans l'inventaire.")

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
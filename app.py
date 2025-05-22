import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import openpyxl
import qrcode
from io import BytesIO
from PIL import Image
import platform
import sys

# Vérifier si nous sommes sur Streamlit Cloud
IS_STREAMLIT_CLOUD = os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false').lower() == 'true'

# Importer les modules de caméra seulement si nous ne sommes pas sur Streamlit Cloud
if not IS_STREAMLIT_CLOUD:
    try:
        import cv2
        from pyzbar.pyzbar import decode
        import numpy as np
        CAMERA_AVAILABLE = True
    except ImportError:
        CAMERA_AVAILABLE = False
else:
    CAMERA_AVAILABLE = False

# Configuration de la page
st.set_page_config(page_title="GMAO - Gestion de Stock", layout="wide")

# Titre de l'application
st.title("📦 Système de Gestion de Stock")

# Données initiales
INITIAL_DATA = {
    'Produits': ['Tournevis cruciforme', 'Marteau 500g', 'Perceuse sans fil', 'Vis 6x50mm', 'Clé à molette'],
    'Reference': ['TS001', 'MH001', 'PS001', 'V001', 'CM001'],
    'Quantite': [50, 30, 15, 1000, 25],
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
        return pd.read_excel(file_path, engine='openpyxl')
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

# Chargement initial des données
df = load_data()

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
        "Historique des mouvements",
        "QR Code produit"
    ]
)

# Fonction pour scanner le QR code
def scan_qr_code():
    if not CAMERA_AVAILABLE:
        st.warning("La caméra n'est pas disponible dans cet environnement.")
        return None
        
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
        st.dataframe(df)
        
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
        emplacement = st.selectbox("Emplacement", ["Atelier A", "Atelier B", "Stockage"])
        fournisseur = st.selectbox("Fournisseur", ["Fournisseur A", "Fournisseur B", "Fournisseur C"])
        prix = st.number_input("Prix unitaire", min_value=0.0)
        
        submitted = st.form_submit_button("Ajouter")
        
        if submitted:
            new_row = pd.DataFrame({
                'Produits': [produit],
                'Reference': [reference],
                'Quantite': [quantite],
                'Emplacement': [emplacement],
                'Fournisseur': [fournisseur],
                'Date_Entree': [datetime.now().strftime("%Y-%m-%d")],
                'Prix_Unitaire': [prix]
            })
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("Produit ajouté avec succès!")

elif action == "Modifier un produit":
    st.header("Modifier un produit")
    
    if not df.empty:
        produit_to_edit = st.selectbox("Sélectionner le produit à modifier", df['Produits'].unique())
        produit_data = df[df['Produits'] == produit_to_edit].iloc[0]
        
        with st.form("modifier_produit"):
            quantite = st.number_input("Nouvelle quantité", value=int(produit_data['Quantite']))
            emplacement = st.selectbox("Nouvel emplacement", df['Emplacement'].unique(), 
                                     index=list(df['Emplacement'].unique()).index(produit_data['Emplacement']))
            
            submitted = st.form_submit_button("Mettre à jour")
            
            if submitted:
                df.loc[df['Produits'] == produit_to_edit, 'Quantite'] = quantite
                df.loc[df['Produits'] == produit_to_edit, 'Emplacement'] = emplacement
                save_data(df)
                st.success("Produit mis à jour avec succès!")

elif action == "Rechercher un produit":
    st.header("Rechercher un produit")
    
    if CAMERA_AVAILABLE:
        search_type = st.radio("Type de recherche", ["Par référence", "Par nom", "Scanner QR Code"])
    else:
        search_type = st.radio("Type de recherche", ["Par référence", "Par nom"])
    
    if search_type == "Scanner QR Code" and CAMERA_AVAILABLE:
        st.write("Présentez le QR code devant la caméra")
        if st.button("Démarrer le scan"):
            code = scan_qr_code()
            if code:
                result = df[df['Reference'] == code]
                if not result.empty:
                    st.success(f"Produit trouvé : {result['Produits'].iloc[0]}")
                    st.dataframe(result)
                else:
                    st.warning("Aucun produit trouvé avec cette référence.")
    elif search_type == "Par référence":
        reference = st.text_input("Entrez la référence du produit")
        if reference:
            result = df[df['Reference'] == reference]
            if not result.empty:
                st.dataframe(result)
            else:
                st.warning("Aucun produit trouvé avec cette référence.")
    else:
        nom = st.text_input("Entrez le nom du produit")
        if nom:
            result = df[df['Produits'].str.contains(nom, case=False)]
            if not result.empty:
                st.dataframe(result)
            else:
                st.warning("Aucun produit trouvé avec ce nom.")

elif action == "Entrée de stock":
    st.header("Entrée de stock")
    if not df.empty:
        if CAMERA_AVAILABLE:
            search_type = st.radio("Méthode de sélection", ["Liste déroulante", "Scanner QR Code"])
        else:
            search_type = "Liste déroulante"
        
        if search_type == "Scanner QR Code" and CAMERA_AVAILABLE:
            st.write("Présentez le QR code devant la caméra")
            if st.button("Démarrer le scan"):
                code = scan_qr_code()
                if code:
                    produit_select = df[df['Reference'] == code]['Produits'].iloc[0]
                    st.session_state['produit_entree'] = produit_select
                    st.experimental_rerun()
        
        produit_select = st.selectbox("Sélectionnez un produit", df['Produits'].unique(), 
                                    key="entree", 
                                    index=df['Produits'].tolist().index(st.session_state.get('produit_entree', df['Produits'].iloc[0])) if st.session_state.get('produit_entree') in df['Produits'].tolist() else 0)
        quantite_actuelle = int(df[df['Produits'] == produit_select]['Quantite'].iloc[0])
        st.write(f"Quantité actuelle : **{quantite_actuelle}**")
        quantite_ajout = st.number_input("Quantité à ajouter", min_value=1, step=1, key="ajout")
        if st.button("Valider l'entrée"):
            nouvelle_quantite = quantite_actuelle + quantite_ajout
            df.loc[df['Produits'] == produit_select, 'Quantite'] = nouvelle_quantite
            save_data(df)
            log_mouvement(produit_select, "Entrée", quantite_ajout, nouvelle_quantite, quantite_actuelle)
            st.success(f"Entrée de {quantite_ajout} unités pour {produit_select} effectuée.")
            st.experimental_rerun()
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Sortie de stock":
    st.header("Sortie de stock")
    if not df.empty:
        if CAMERA_AVAILABLE:
            search_type = st.radio("Méthode de sélection", ["Liste déroulante", "Scanner QR Code"])
        else:
            search_type = "Liste déroulante"
        
        if search_type == "Scanner QR Code" and CAMERA_AVAILABLE:
            st.write("Présentez le QR code devant la caméra")
            if st.button("Démarrer le scan"):
                code = scan_qr_code()
                if code:
                    produit_select = df[df['Reference'] == code]['Produits'].iloc[0]
                    st.session_state['produit_sortie'] = produit_select
                    st.experimental_rerun()
        
        produit_select = st.selectbox("Sélectionnez un produit", df['Produits'].unique(), 
                                    key="sortie",
                                    index=df['Produits'].tolist().index(st.session_state.get('produit_sortie', df['Produits'].iloc[0])) if st.session_state.get('produit_sortie') in df['Produits'].tolist() else 0)
        quantite_actuelle = int(df[df['Produits'] == produit_select]['Quantite'].iloc[0])
        st.write(f"Quantité actuelle : **{quantite_actuelle}**")
        quantite_retrait = st.number_input("Quantité à retirer", min_value=1, step=1, key="retrait")
        if st.button("Valider la sortie"):
            if quantite_actuelle >= quantite_retrait:
                nouvelle_quantite = quantite_actuelle - quantite_retrait
                df.loc[df['Produits'] == produit_select, 'Quantite'] = nouvelle_quantite
                save_data(df)
                log_mouvement(produit_select, "Sortie", quantite_retrait, nouvelle_quantite, quantite_actuelle)
                st.success(f"Sortie de {quantite_retrait} unités pour {produit_select} effectuée.")
                st.experimental_rerun()
            else:
                st.error("Stock insuffisant pour effectuer la sortie.")
    else:
        st.warning("Aucun produit disponible dans l'inventaire.")

elif action == "Inventaire":
    st.header("Ajustement d'inventaire")
    if not df.empty:
        if CAMERA_AVAILABLE:
            search_type = st.radio("Méthode de sélection", ["Liste déroulante", "Scanner QR Code"])
        else:
            search_type = "Liste déroulante"
        
        if search_type == "Scanner QR Code" and CAMERA_AVAILABLE:
            st.write("Présentez le QR code devant la caméra")
            if st.button("Démarrer le scan"):
                code = scan_qr_code()
                if code:
                    produit_select = df[df['Reference'] == code]['Produits'].iloc[0]
                    st.session_state['produit_inventaire'] = produit_select
                    st.experimental_rerun()
        
        produit_select = st.selectbox("Sélectionnez un produit", df['Produits'].unique(), 
                                    key="inventaire",
                                    index=df['Produits'].tolist().index(st.session_state.get('produit_inventaire', df['Produits'].iloc[0])) if st.session_state.get('produit_inventaire') in df['Produits'].tolist() else 0)
        quantite_actuelle = int(df[df['Produits'] == produit_select]['Quantite'].iloc[0])
        st.write(f"Quantité actuelle : **{quantite_actuelle}**")
        nouvelle_quantite = st.number_input("Nouvelle quantité (après inventaire)", min_value=0, value=quantite_actuelle, step=1, key="nv_inventaire")
        if st.button("Valider l'ajustement"):
            if nouvelle_quantite != quantite_actuelle:
                df.loc[df['Produits'] == produit_select, 'Quantite'] = nouvelle_quantite
                save_data(df)
                log_mouvement(
                    produit_select,
                    "Inventaire",
                    abs(nouvelle_quantite - quantite_actuelle),
                    nouvelle_quantite,
                    quantite_actuelle
                )
                st.success(f"Inventaire ajusté pour {produit_select} : {quantite_actuelle} → {nouvelle_quantite}")
                st.experimental_rerun()
            else:
                st.info("La quantité saisie est identique à la quantité actuelle.")
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
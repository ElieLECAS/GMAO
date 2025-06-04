import pandas as pd
import streamlit as st
from datetime import datetime
import os
from api_client import api_client
from app import generer_reference_qr

def migrer_excel_vers_api():
    """
    Migre toutes les données Excel existantes vers l'API
    """
    st.header("🔄 Migration des données Excel vers l'API")
    
    if not api_client.test_connection():
        st.error("❌ Impossible de se connecter à l'API. Vérifiez que le serveur est démarré.")
        return
    
    # Migration de l'inventaire
    st.subheader("📦 Migration de l'inventaire")
    migrer_inventaire_excel()
    
    # Migration des fournisseurs
    st.subheader("🏢 Migration des fournisseurs")
    migrer_fournisseurs_excel()
    
    # Migration des emplacements
    st.subheader("📍 Migration des emplacements")
    migrer_emplacements_excel()
    
    # Migration des demandes
    st.subheader("📋 Migration des demandes")
    migrer_demandes_excel()
    
    # Migration de l'historique
    st.subheader("📊 Migration de l'historique")
    migrer_historique_excel()

def migrer_inventaire_excel():
    """Migre l'inventaire depuis Excel vers l'API"""
    fichier_excel = "data/inventaire_avec_references.xlsx"
    
    if not os.path.exists(fichier_excel):
        st.warning("⚠️ Aucun fichier d'inventaire Excel trouvé")
        return
    
    try:
        df = pd.read_excel(fichier_excel, engine='openpyxl')
        
        if df.empty:
            st.warning("⚠️ Le fichier d'inventaire est vide")
            return
        
        # Renommer les colonnes si nécessaire
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
        
        df = df.rename(columns=column_mapping)
        
        # Générer les références QR si elles n'existent pas
        if 'Reference' not in df.columns:
            df['Reference'] = df.apply(lambda row: generer_reference_qr(row['Code'], row['Produits']), axis=1)
        
        # Ajouter les colonnes manquantes
        if 'Quantite' not in df.columns:
            df['Quantite'] = 0
        if 'Date_Entree' not in df.columns:
            df['Date_Entree'] = datetime.now().strftime("%Y-%m-%d")
        
        # Nettoyer les données
        df['Stock_Min'] = pd.to_numeric(df['Stock_Min'], errors='coerce').fillna(0)
        df['Stock_Max'] = pd.to_numeric(df['Stock_Max'], errors='coerce').fillna(100)
        df['Prix_Unitaire'] = pd.to_numeric(df['Prix_Unitaire'], errors='coerce').fillna(0)
        df['Quantite'] = pd.to_numeric(df['Quantite'], errors='coerce').fillna(0)
        df['Reference'] = df['Reference'].astype(str)
        
        # Migrer chaque produit
        success_count = 0
        error_count = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for index, row in df.iterrows():
            try:
                produit_data = row.to_dict()
                
                # Vérifier si le produit existe déjà
                existing_produit = api_client.get_produit_by_reference(str(row['Reference']))
                
                if existing_produit:
                    # Mettre à jour
                    result = api_client.update_produit(existing_produit['id'], produit_data)
                else:
                    # Créer
                    result = api_client.create_produit(produit_data)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur pour le produit {row.get('Code', 'N/A')}: {str(e)}")
                error_count += 1
            
            # Mettre à jour la barre de progression
            progress = (index + 1) / len(df)
            progress_bar.progress(progress)
            status_text.text(f"Migration en cours... {index + 1}/{len(df)} produits traités")
        
        st.success(f"✅ Migration terminée: {success_count} produits migrés, {error_count} erreurs")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la migration de l'inventaire: {str(e)}")

def migrer_fournisseurs_excel():
    """Migre les fournisseurs depuis Excel vers l'API"""
    fichier_excel = "data/fournisseurs.xlsx"
    
    if not os.path.exists(fichier_excel):
        st.warning("⚠️ Aucun fichier de fournisseurs Excel trouvé")
        return
    
    try:
        df = pd.read_excel(fichier_excel, engine='openpyxl')
        
        if df.empty:
            st.warning("⚠️ Le fichier des fournisseurs est vide")
            return
        
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                fournisseur_data = {
                    'ID_Fournisseur': str(row.get('ID_Fournisseur', '')),
                    'Nom_Fournisseur': str(row.get('Nom_Fournisseur', '')),
                    'Contact_Principal': str(row.get('Contact_Principal', '')),
                    'Email': str(row.get('Email', '')),
                    'Telephone': str(row.get('Telephone', '')),
                    'Adresse': str(row.get('Adresse', ''))
                }
                
                result = api_client.create_fournisseur(fournisseur_data)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur pour le fournisseur {row.get('Nom_Fournisseur', 'N/A')}: {str(e)}")
                error_count += 1
        
        st.success(f"✅ {success_count} fournisseurs migrés, {error_count} erreurs")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la migration des fournisseurs: {str(e)}")

def migrer_emplacements_excel():
    """Migre les emplacements depuis Excel vers l'API"""
    fichier_excel = "data/emplacements.xlsx"
    
    if not os.path.exists(fichier_excel):
        st.warning("⚠️ Aucun fichier d'emplacements Excel trouvé")
        return
    
    try:
        df = pd.read_excel(fichier_excel, engine='openpyxl')
        
        if df.empty:
            st.warning("⚠️ Le fichier des emplacements est vide")
            return
        
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                emplacement_data = {
                    'ID_Emplacement': str(row.get('ID_Emplacement', '')),
                    'Nom_Emplacement': str(row.get('Nom_Emplacement', '')),
                    'Type_Zone': str(row.get('Type_Zone', '')),
                    'Batiment': str(row.get('Batiment', '')),
                    'Niveau': str(row.get('Niveau', '')),
                    'Responsable': str(row.get('Responsable', '')),
                    'Capacite_Max': int(row.get('Capacite_Max', 100))
                }
                
                result = api_client.create_emplacement(emplacement_data)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur pour l'emplacement {row.get('Nom_Emplacement', 'N/A')}: {str(e)}")
                error_count += 1
        
        st.success(f"✅ {success_count} emplacements migrés, {error_count} erreurs")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la migration des emplacements: {str(e)}")

def migrer_demandes_excel():
    """Migre les demandes depuis Excel vers l'API"""
    fichier_excel = "data/demandes.xlsx"
    
    if not os.path.exists(fichier_excel):
        st.warning("⚠️ Aucun fichier de demandes Excel trouvé")
        return
    
    try:
        df = pd.read_excel(fichier_excel, engine='openpyxl')
        
        if df.empty:
            st.warning("⚠️ Le fichier des demandes est vide")
            return
        
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Convertir les produits demandés depuis string vers dict si nécessaire
                produits_demandes = row.get('Produits_Demandes', '{}')
                if isinstance(produits_demandes, str):
                    try:
                        import ast
                        produits_demandes = ast.literal_eval(produits_demandes)
                    except:
                        produits_demandes = {}
                
                demande_data = {
                    'demandeur': str(row.get('Demandeur', '')),
                    'produits_demandes': produits_demandes,
                    'motif': str(row.get('Motif', ''))
                }
                
                result = api_client.create_demande(demande_data)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur pour la demande {row.get('ID_Demande', 'N/A')}: {str(e)}")
                error_count += 1
        
        st.success(f"✅ {success_count} demandes migrées, {error_count} erreurs")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la migration des demandes: {str(e)}")

def migrer_historique_excel():
    """Migre l'historique depuis Excel vers l'API"""
    fichier_excel = "data/historique.xlsx"
    
    if not os.path.exists(fichier_excel):
        st.warning("⚠️ Aucun fichier d'historique Excel trouvé")
        return
    
    try:
        df = pd.read_excel(fichier_excel, engine='openpyxl')
        
        if df.empty:
            st.warning("⚠️ Le fichier d'historique est vide")
            return
        
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                result = api_client.effectuer_mouvement_stock(
                    reference=str(row.get('Reference', '')),
                    nature=str(row.get('Nature', '')),
                    quantite_mouvement=int(row.get('Quantite_Mouvement', 0)),
                    quantite_avant=int(row.get('Quantite_Avant', 0)),
                    quantite_apres=int(row.get('Quantite_Apres', 0)),
                    produit=str(row.get('Produit', ''))
                )
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur pour le mouvement {index}: {str(e)}")
                error_count += 1
        
        st.success(f"✅ {success_count} mouvements d'historique migrés, {error_count} erreurs")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la migration de l'historique: {str(e)}")

def importer_produits_en_masse(uploaded_file):
    """
    Importe des produits en masse depuis un fichier Excel uploadé
    """
    if uploaded_file is None:
        st.warning("⚠️ Aucun fichier sélectionné")
        return
    
    try:
        # Lire le fichier Excel
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        if df.empty:
            st.warning("⚠️ Le fichier est vide")
            return
        
        st.info(f"📊 {len(df)} lignes détectées dans le fichier")
        
        # Afficher un aperçu des données
        st.subheader("📋 Aperçu des données")
        st.dataframe(df.head())
        
        # Mapping des colonnes
        st.subheader("🔗 Mapping des colonnes")
        
        colonnes_requises = ['Code', 'Produits', 'Reference_Fournisseur', 'Unite_Stockage', 
                           'Unite_Commande', 'Stock_Min', 'Stock_Max', 'Site', 'Lieu', 
                           'Emplacement', 'Fournisseur', 'Prix_Unitaire', 'Categorie', 'Secteur']
        
        colonnes_fichier = df.columns.tolist()
        
        # Interface de mapping
        mapping = {}
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Colonnes requises:**")
            for col_req in colonnes_requises:
                st.write(f"• {col_req}")
        
        with col2:
            st.write("**Mapping:**")
            for col_req in colonnes_requises:
                mapping[col_req] = st.selectbox(
                    f"Mapper {col_req} avec:",
                    options=[""] + colonnes_fichier,
                    key=f"mapping_{col_req}"
                )
        
        if st.button("🚀 Lancer l'importation"):
            importer_avec_mapping(df, mapping)
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier: {str(e)}")

def importer_avec_mapping(df, mapping):
    """
    Effectue l'importation avec le mapping défini
    """
    try:
        # Appliquer le mapping
        df_mapped = pd.DataFrame()
        
        for col_req, col_fichier in mapping.items():
            if col_fichier and col_fichier in df.columns:
                df_mapped[col_req] = df[col_fichier]
            else:
                # Valeurs par défaut
                if col_req in ['Stock_Min', 'Stock_Max', 'Prix_Unitaire']:
                    df_mapped[col_req] = 0
                else:
                    df_mapped[col_req] = ""
        
        # Générer les références QR
        df_mapped['Reference'] = df_mapped.apply(
            lambda row: generer_reference_qr(row['Code'], row['Produits']), axis=1
        )
        
        # Ajouter les colonnes manquantes
        df_mapped['Quantite'] = 0
        df_mapped['Date_Entree'] = datetime.now().strftime("%Y-%m-%d")
        
        # Nettoyer les données
        df_mapped['Stock_Min'] = pd.to_numeric(df_mapped['Stock_Min'], errors='coerce').fillna(0)
        df_mapped['Stock_Max'] = pd.to_numeric(df_mapped['Stock_Max'], errors='coerce').fillna(100)
        df_mapped['Prix_Unitaire'] = pd.to_numeric(df_mapped['Prix_Unitaire'], errors='coerce').fillna(0)
        df_mapped['Reference'] = df_mapped['Reference'].astype(str)
        
        # Importer via l'API
        success_count = 0
        error_count = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for index, row in df_mapped.iterrows():
            try:
                produit_data = row.to_dict()
                
                # Vérifier si le produit existe déjà
                existing_produit = api_client.get_produit_by_reference(str(row['Reference']))
                
                if existing_produit:
                    # Mettre à jour
                    result = api_client.update_produit(existing_produit['id'], produit_data)
                else:
                    # Créer
                    result = api_client.create_produit(produit_data)
                
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                st.warning(f"⚠️ Erreur pour le produit {row.get('Code', 'N/A')}: {str(e)}")
                error_count += 1
            
            # Mettre à jour la barre de progression
            progress = (index + 1) / len(df_mapped)
            progress_bar.progress(progress)
            status_text.text(f"Importation en cours... {index + 1}/{len(df_mapped)} produits traités")
        
        st.success(f"✅ Importation terminée: {success_count} produits importés, {error_count} erreurs")
        
    except Exception as e:
        st.error(f"❌ Erreur lors de l'importation: {str(e)}")

def exporter_donnees_api():
    """
    Exporte toutes les données de l'API vers des fichiers Excel
    """
    st.header("📤 Export des données de l'API")
    
    if not api_client.test_connection():
        st.error("❌ Impossible de se connecter à l'API")
        return
    
    # Export de l'inventaire
    if st.button("📦 Exporter l'inventaire"):
        df_inventaire = api_client.get_inventaire()
        if not df_inventaire.empty:
            df_inventaire.to_excel("export_inventaire.xlsx", index=False)
            st.success("✅ Inventaire exporté vers export_inventaire.xlsx")
        else:
            st.warning("⚠️ Aucun produit à exporter")
    
    # Export des fournisseurs
    if st.button("🏢 Exporter les fournisseurs"):
        df_fournisseurs = api_client.get_fournisseurs()
        if not df_fournisseurs.empty:
            df_fournisseurs.to_excel("export_fournisseurs.xlsx", index=False)
            st.success("✅ Fournisseurs exportés vers export_fournisseurs.xlsx")
        else:
            st.warning("⚠️ Aucun fournisseur à exporter")
    
    # Export des emplacements
    if st.button("📍 Exporter les emplacements"):
        df_emplacements = api_client.get_emplacements()
        if not df_emplacements.empty:
            df_emplacements.to_excel("export_emplacements.xlsx", index=False)
            st.success("✅ Emplacements exportés vers export_emplacements.xlsx")
        else:
            st.warning("⚠️ Aucun emplacement à exporter")
    
    # Export des demandes
    if st.button("📋 Exporter les demandes"):
        df_demandes = api_client.get_demandes()
        if not df_demandes.empty:
            df_demandes.to_excel("export_demandes.xlsx", index=False)
            st.success("✅ Demandes exportées vers export_demandes.xlsx")
        else:
            st.warning("⚠️ Aucune demande à exporter")
    
    # Export de l'historique
    if st.button("📊 Exporter l'historique"):
        df_historique = api_client.get_historique()
        if not df_historique.empty:
            df_historique.to_excel("export_historique.xlsx", index=False)
            st.success("✅ Historique exporté vers export_historique.xlsx")
        else:
            st.warning("⚠️ Aucun historique à exporter") 
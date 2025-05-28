#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier l'ajout automatique de fournisseurs
"""

import pandas as pd
import os
from datetime import datetime

def charger_fournisseurs():
    """Charge tous les fournisseurs depuis le fichier Excel"""
    file_path = "data/fournisseurs.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            print(f"Erreur lors du chargement des fournisseurs: {str(e)}")
            return pd.DataFrame()
    else:
        print("Fichier fournisseurs.xlsx non trouvé")
        return pd.DataFrame()

def sauvegarder_fournisseurs(df_fournisseurs):
    """Sauvegarde les fournisseurs dans le fichier Excel"""
    try:
        os.makedirs("data", exist_ok=True)
        df_fournisseurs.to_excel("data/fournisseurs.xlsx", index=False, engine='openpyxl')
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des fournisseurs: {str(e)}")
        return False

def ajouter_fournisseur_automatique(nom_fournisseur):
    """Ajoute automatiquement un fournisseur s'il n'existe pas déjà dans le fichier fournisseurs.xlsx"""
    df_fournisseurs = charger_fournisseurs()
    
    # Vérifier si le fournisseur existe déjà
    if not df_fournisseurs.empty and nom_fournisseur in df_fournisseurs['Nom_Fournisseur'].values:
        print(f"✅ Le fournisseur '{nom_fournisseur}' existe déjà")
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
    
    if sauvegarder_fournisseurs(df_fournisseurs):
        print(f"✅ Fournisseur '{nom_fournisseur}' ajouté automatiquement avec l'ID {nouvel_id}")
        return True
    else:
        print(f"❌ Erreur lors de l'ajout du fournisseur '{nom_fournisseur}'")
        return False

def test_ajout_fournisseur():
    """Test de la fonction d'ajout automatique de fournisseur"""
    print("🧪 Test de l'ajout automatique de fournisseur")
    print("=" * 50)
    
    # Afficher l'état initial
    df_fournisseurs = charger_fournisseurs()
    print(f"📊 Nombre de fournisseurs avant test: {len(df_fournisseurs)}")
    if not df_fournisseurs.empty:
        print("📋 Fournisseurs existants:")
        for nom in df_fournisseurs['Nom_Fournisseur'].values:
            print(f"  - {nom}")
    
    print("\n🔄 Test d'ajout du fournisseur 'FournX'...")
    
    # Tester l'ajout d'un nouveau fournisseur
    resultat = ajouter_fournisseur_automatique("FournX")
    
    # Vérifier le résultat
    df_fournisseurs_apres = charger_fournisseurs()
    print(f"📊 Nombre de fournisseurs après test: {len(df_fournisseurs_apres)}")
    
    if "FournX" in df_fournisseurs_apres['Nom_Fournisseur'].values:
        print("✅ Test réussi ! Le fournisseur 'FournX' a été ajouté.")
        fournisseur_info = df_fournisseurs_apres[df_fournisseurs_apres['Nom_Fournisseur'] == 'FournX'].iloc[0]
        print(f"   ID: {fournisseur_info['ID_Fournisseur']}")
        print(f"   Contact: {fournisseur_info['Contact_Principal']}")
        print(f"   Statut: {fournisseur_info['Statut']}")
        print(f"   Date création: {fournisseur_info['Date_Creation']}")
    else:
        print("❌ Test échoué ! Le fournisseur 'FournX' n'a pas été ajouté.")
    
    print("\n🔄 Test d'ajout du même fournisseur (doit être ignoré)...")
    resultat2 = ajouter_fournisseur_automatique("FournX")
    
    df_fournisseurs_final = charger_fournisseurs()
    print(f"📊 Nombre de fournisseurs final: {len(df_fournisseurs_final)}")
    
    if len(df_fournisseurs_final) == len(df_fournisseurs_apres):
        print("✅ Test réussi ! Le fournisseur existant n'a pas été dupliqué.")
    else:
        print("❌ Test échoué ! Le fournisseur a été dupliqué.")

if __name__ == "__main__":
    test_ajout_fournisseur() 
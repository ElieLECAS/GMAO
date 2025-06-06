#!/usr/bin/env python3
"""
Script de test pour vérifier la fonctionnalité de détection des doublons
lors de l'importation de produits.
"""

import pandas as pd
import os

def create_test_excel():
    """Créer un fichier Excel de test avec des doublons"""
    
    # Données de test avec des doublons intentionnels
    data = [
        {
            'Désignation': 'Vis M6x20',
            'Référence fournisseur': 'VIS-M6-20',
            'Unité de stockage': 'Pièce',
            'Min': 10,
            'Max': 100,
            'Prix': 0.15,
            'Catégorie': 'Visserie',
            'Fournisseur Standard': 'Boulonnerie Dupont',
            'Site': 'Atelier Principal',
            'Lieu': 'Zone Stockage',
            'Emplacement': 'Étagère A1',
            'Quantité': 50
        },
        {
            'Désignation': 'Écrou M6',
            'Référence fournisseur': 'ECR-M6',
            'Unité de stockage': 'Pièce',
            'Min': 20,
            'Max': 200,
            'Prix': 0.08,
            'Catégorie': 'Visserie',
            'Fournisseur Standard': 'Boulonnerie Dupont',
            'Site': 'Atelier Principal',
            'Lieu': 'Zone Stockage',
            'Emplacement': 'Étagère A1',
            'Quantité': 150
        },
        {
            'Désignation': 'Vis M6x20 - Lot de 100',  # DOUBLON INTENTIONNEL
            'Référence fournisseur': 'VIS-M6-20',  # MÊME RÉFÉRENCE = DOUBLON
            'Unité de stockage': 'Lot',
            'Min': 15,  # Valeurs différentes pour tester la mise à jour
            'Max': 120,
            'Prix': 12.50,  # Prix différent pour le lot
            'Catégorie': 'Visserie',
            'Fournisseur Standard': 'Boulonnerie Dupont',  # Même fournisseur
            'Site': 'Atelier Principal',
            'Lieu': 'Zone Stockage',
            'Emplacement': 'Étagère A2',  # Emplacement différent
            'Quantité': 5  # 5 lots = 500 pièces
        },
        {
            'Désignation': 'Rondelle M6',
            'Référence fournisseur': 'RON-M6',
            'Unité de stockage': 'Pièce',
            'Min': 30,
            'Max': 300,
            'Prix': 0.05,
            'Catégorie': 'Visserie',
            'Fournisseur Standard': 'Boulonnerie Martin',  # Fournisseur différent
            'Site': 'Atelier Principal',
            'Lieu': 'Zone Stockage',
            'Emplacement': 'Étagère A1',
            'Quantité': 200
        },
        {
            'Désignation': 'Vis M6x20',  # AUTRE DOUBLON avec fournisseur différent
            'Référence fournisseur': 'VIS-M6-20-MARTIN',
            'Unité de stockage': 'Pièce',
            'Min': 12,
            'Max': 80,
            'Prix': 0.16,
            'Catégorie': 'Visserie',
            'Fournisseur Standard': 'Boulonnerie Martin',  # Fournisseur différent
            'Site': 'Atelier Secondaire',
            'Lieu': 'Stockage B',
            'Emplacement': 'Étagère B1',
            'Quantité': 40
        }
    ]
    
    # Créer le DataFrame
    df = pd.DataFrame(data)
    
    # Sauvegarder en Excel
    filename = 'test_import_doublons.xlsx'
    df.to_excel(filename, index=False)
    
    print(f"Fichier de test créé : {filename}")
    print(f"Contenu du fichier :")
    print(df.to_string(index=False))
    print(f"\nDoublons détectés :")
    print(f"- Référence 'VIS-M6-20' apparaît 2 fois :")
    print(f"  * Ligne 1 : Référence 'VIS-M6-20' + Fournisseur 'Boulonnerie Dupont' (Vis à l'unité)")
    print(f"  * Ligne 3 : Référence 'VIS-M6-20' + Fournisseur 'Boulonnerie Dupont' (DOUBLON - Vis en lot)")
    print(f"  * Ligne 5 : Référence 'VIS-M6-20-MARTIN' + Fournisseur 'Boulonnerie Martin' (pas un doublon car référence et fournisseur différents)")
    print(f"- 1 doublon réel détecté : même référence fournisseur chez le même fournisseur")
    
    return filename

def test_duplicate_detection():
    """Tester la fonction de détection des doublons"""
    
    # Simuler la fonction de détection des doublons
    def produit_existe_par_designation_test(designation, fournisseur=None):
        """Version de test de la fonction de détection"""
        produits_existants = [
            {'produits': 'Vis M6x20', 'fournisseur': 'Boulonnerie Dupont'},
            {'produits': 'Écrou M6', 'fournisseur': 'Boulonnerie Dupont'},
            {'produits': 'Rondelle M8', 'fournisseur': 'Boulonnerie Martin'}
        ]
        
        for produit in produits_existants:
            produit_designation = produit.get('produits', '').strip().lower()
            
            if produit_designation == designation.strip().lower():
                if fournisseur:
                    produit_fournisseur = produit.get('fournisseur', '').strip().lower()
                    if produit_fournisseur == fournisseur.strip().lower():
                        return produit
                else:
                    return produit
        
        return None
    
    # Tests
    print("\n=== Tests de détection des doublons ===")
    
    # Test 1 : Produit existant avec même fournisseur
    result = produit_existe_par_designation_test('Vis M6x20', 'Boulonnerie Dupont')
    print(f"Test 1 - Vis M6x20 + Boulonnerie Dupont : {'DOUBLON DÉTECTÉ' if result else 'NOUVEAU PRODUIT'}")
    
    # Test 2 : Produit existant avec fournisseur différent
    result = produit_existe_par_designation_test('Vis M6x20', 'Boulonnerie Martin')
    print(f"Test 2 - Vis M6x20 + Boulonnerie Martin : {'DOUBLON DÉTECTÉ' if result else 'NOUVEAU PRODUIT'}")
    
    # Test 3 : Produit existant sans spécifier le fournisseur
    result = produit_existe_par_designation_test('Vis M6x20')
    print(f"Test 3 - Vis M6x20 (sans fournisseur) : {'DOUBLON DÉTECTÉ' if result else 'NOUVEAU PRODUIT'}")
    
    # Test 4 : Nouveau produit
    result = produit_existe_par_designation_test('Vis M8x25', 'Boulonnerie Dupont')
    print(f"Test 4 - Vis M8x25 + Boulonnerie Dupont : {'DOUBLON DÉTECTÉ' if result else 'NOUVEAU PRODUIT'}")

if __name__ == "__main__":
    print("=== Test de la fonctionnalité de gestion des doublons ===\n")
    
    # Créer le fichier Excel de test
    excel_file = create_test_excel()
    
    # Tester la détection des doublons
    test_duplicate_detection()
    
    print(f"\n=== Instructions pour tester ===")
    print(f"1. Démarrez l'application Flask")
    print(f"2. Allez sur la page 'Gestion des Produits'")
    print(f"3. Cliquez sur 'Importer Excel'")
    print(f"4. Sélectionnez le fichier '{excel_file}'")
    print(f"5. Testez les deux options :")
    print(f"   - 'Ignorer' : Les doublons seront ignorés")
    print(f"   - 'Mettre à jour' : Les doublons seront mis à jour")
    print(f"6. Vérifiez les statistiques d'importation")
    
    print(f"\n=== Résultats attendus ===")
    print(f"Mode 'Ignorer' :")
    print(f"- 3 produits créés (Vis M6x20, Écrou M6, Rondelle M6, Vis M6x20 avec fournisseur différent)")
    print(f"- 1 produit ignoré (Vis M6x20 doublon avec même fournisseur)")
    print(f"")
    print(f"Mode 'Mettre à jour' :")
    print(f"- 3 produits créés")
    print(f"- 1 produit mis à jour (Vis M6x20 avec Boulonnerie Dupont)") 
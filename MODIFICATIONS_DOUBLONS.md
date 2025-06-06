# Modifications pour la Gestion des Doublons lors de l'Importation

## Problème identifié

Lors de l'importation de fichiers Excel, si le même fichier était importé plusieurs fois, les produits étaient créés en double sans vérification d'unicité basée sur la désignation.

## Solution implémentée

### 1. Fonction de vérification d'unicité

**Fichier**: `UI/app.py`
**Fonction**: `produit_existe_par_designation(designation, fournisseur=None)`

-   Vérifie si un produit existe déjà par désignation
-   Optionnellement vérifie aussi le fournisseur pour permettre le même produit chez différents fournisseurs
-   Gère les descriptions composées (ex: "Vis M6x20 - Description")
-   Comparaison insensible à la casse

### 2. Modification de la création manuelle de produits

**Route**: `/api/produits` (POST)

-   Ajout de la vérification d'unicité avant création
-   Message d'erreur explicite en cas de doublon détecté
-   Prise en compte du fournisseur dans la vérification

### 3. Amélioration de l'importation Excel

**Route**: `/api/import-produits` (POST)

#### Nouvelles fonctionnalités :

-   **Option de gestion des doublons** :
    -   `ignorer` : Les produits existants sont ignorés (comportement par défaut)
    -   `mettre_a_jour` : Les produits existants sont mis à jour avec les nouvelles données

#### Statistiques enrichies :

-   `produits_crees` : Nouveaux produits créés
-   `produits_ignores` : Produits existants ignorés
-   `produits_mis_a_jour` : Produits existants mis à jour

#### Logique de mise à jour :

-   Seuls les champs non vides du fichier Excel sont mis à jour
-   La quantité n'est PAS mise à jour pour préserver le stock actuel
-   Mise à jour des informations produit, fournisseur, emplacement, prix, etc.

### 4. Interface utilisateur améliorée

**Fichier**: `UI/templates/gestion_produits.html`

#### Modal d'importation enrichie :

-   Ajout d'options radio pour choisir la gestion des doublons
-   Explication claire des deux modes
-   Information sur les critères d'unicité (désignation + fournisseur)

#### JavaScript mis à jour :

-   Transmission de l'option de gestion des doublons au serveur
-   Affichage des statistiques détaillées après importation

## Critères d'unicité

Un produit est considéré comme un doublon si :

1. **Même désignation** (insensible à la casse)
2. **ET même fournisseur** (si spécifié)

Cela permet d'avoir le même produit chez différents fournisseurs.

## Exemples d'utilisation

### Cas 1 : Importation avec doublons - Mode "Ignorer"

```
Fichier Excel contient :
- Vis M6x20 (Fournisseur A) ← Nouveau
- Écrou M6 (Fournisseur A) ← Nouveau
- Vis M6x20 (Fournisseur A) ← Doublon ignoré
- Vis M6x20 (Fournisseur B) ← Nouveau (fournisseur différent)

Résultat :
- 3 produits créés
- 1 produit ignoré
```

### Cas 2 : Importation avec doublons - Mode "Mettre à jour"

```
Même fichier Excel :

Résultat :
- 3 produits créés
- 1 produit mis à jour (Vis M6x20 Fournisseur A)
```

## Fichiers modifiés

1. **UI/app.py**

    - Ajout fonction `produit_existe_par_designation()`
    - Modification `creer_produit()`
    - Modification `import_produits()`

2. **UI/templates/gestion_produits.html**

    - Ajout options de gestion des doublons
    - Modification JavaScript `startImport()`

3. **test_import_doublons.py** (nouveau)
    - Script de test avec fichier Excel d'exemple
    - Tests unitaires de la détection des doublons

## Tests recommandés

1. Créer quelques produits manuellement
2. Exporter/créer un fichier Excel avec ces mêmes produits
3. Tester l'importation en mode "Ignorer"
4. Tester l'importation en mode "Mettre à jour"
5. Vérifier les statistiques d'importation
6. Vérifier que les données sont correctement mises à jour

## Sécurité et performance

-   La vérification se fait côté serveur
-   Pas de modification de la quantité en stock lors des mises à jour
-   Gestion des erreurs avec messages explicites
-   Performance : Une seule requête API pour récupérer tous les produits existants

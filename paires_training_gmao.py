# Paires Question-SQL pour l'entraînement de Vanna - Système GMAO
# À copier dans votre notebook train.ipynb

# =====================================================
# QUESTIONS SUR LES FOURNISSEURS
# =====================================================

# Question simple - Liste des fournisseurs
vn.train(
    question="Liste-moi tous les fournisseurs",
    sql="SELECT nom_fournisseur, statut FROM fournisseurs ORDER BY nom_fournisseur;"
)

vn.train(
    question="Quels sont les fournisseurs actifs ?",
    sql="SELECT id_fournisseur, nom_fournisseur, contact1_email FROM fournisseurs WHERE statut = 'Actif';"
)

vn.train(
    question="Montre-moi les coordonnées du fournisseur X",
    sql="SELECT nom_fournisseur, adresse, contact1_nom, contact1_email, contact1_tel_mobile FROM fournisseurs WHERE nom_fournisseur ILIKE '%X%';"
)

vn.train(
    question="Combien de fournisseurs avons-nous ?",
    sql="SELECT COUNT(*) as nombre_fournisseurs FROM fournisseurs WHERE statut = 'Actif';"
)

# =====================================================
# QUESTIONS SUR L'INVENTAIRE/STOCK
# =====================================================

vn.train(
    question="Montre-moi tous les produits en stock",
    sql="SELECT reference, produits, quantite, emplacement, fournisseur FROM inventaire WHERE quantite > 0 ORDER BY produits;"
)

vn.train(
    question="Quels produits ont un stock faible ?",
    sql="SELECT reference, produits, quantite, stock_min, emplacement FROM inventaire WHERE quantite <= stock_min ORDER BY quantite;"
)

vn.train(
    question="Liste des produits par fournisseur",
    sql="SELECT fournisseur, COUNT(*) as nb_produits, SUM(quantite) as stock_total FROM inventaire GROUP BY fournisseur ORDER BY nb_produits DESC;"
)

vn.train(
    question="Quel est le stock total par catégorie ?",
    sql="SELECT categorie, COUNT(*) as nb_produits, SUM(quantite) as quantite_totale FROM inventaire GROUP BY categorie ORDER BY quantite_totale DESC;"
)

vn.train(
    question="Recherche un produit par référence",
    sql="SELECT * FROM inventaire WHERE reference = 'REF123';"
)

vn.train(
    question="Produits stockés dans l'emplacement X",
    sql="SELECT reference, produits, quantite, prix_unitaire FROM inventaire WHERE emplacement ILIKE '%X%';"
)

vn.train(
    question="Valeur totale du stock",
    sql="SELECT SUM(quantite * prix_unitaire) as valeur_totale_stock FROM inventaire;"
)

# =====================================================
# QUESTIONS SUR LA HIÉRARCHIE (SITES/LIEUX/EMPLACEMENTS)
# =====================================================

vn.train(
    question="Liste tous les sites",
    sql="SELECT code_site, nom_site, ville, responsable FROM sites WHERE statut = 'Actif';"
)

vn.train(
    question="Quels sont les lieux du site X ?",
    sql="SELECT l.code_lieu, l.nom_lieu, l.type_lieu, s.nom_site FROM lieux l JOIN sites s ON l.site_id = s.id WHERE s.nom_site ILIKE '%X%';"
)

vn.train(
    question="Montre-moi les emplacements du lieu Y",
    sql="SELECT e.code_emplacement, e.nom_emplacement, e.type_emplacement, e.nb_produits FROM emplacements e JOIN lieux l ON e.lieu_id = l.id WHERE l.nom_lieu ILIKE '%Y%';"
)

vn.train(
    question="Hiérarchie complète des emplacements",
    sql="SELECT s.nom_site, l.nom_lieu, e.nom_emplacement, e.nb_produits FROM sites s JOIN lieux l ON s.id = l.site_id JOIN emplacements e ON l.id = e.lieu_id ORDER BY s.nom_site, l.nom_lieu, e.nom_emplacement;"
)

# =====================================================
# QUESTIONS SUR LES DEMANDES
# =====================================================

vn.train(
    question="Liste des demandes en attente",
    sql="SELECT id_demande, date_demande, demandeur, statut FROM demandes WHERE statut = 'En attente' ORDER BY date_demande;"
)

vn.train(
    question="Demandes par demandeur",
    sql="SELECT demandeur, COUNT(*) as nb_demandes, MAX(date_demande) as derniere_demande FROM demandes GROUP BY demandeur ORDER BY nb_demandes DESC;"
)

vn.train(
    question="Demandes traitées ce mois",
    sql="SELECT COUNT(*) as demandes_traitees FROM demandes WHERE statut = 'Traitée' AND DATE_TRUNC('month', date_traitement) = DATE_TRUNC('month', CURRENT_DATE);"
)

# =====================================================
# QUESTIONS SUR L'HISTORIQUE
# =====================================================

vn.train(
    question="Historique des mouvements du produit X",
    sql="SELECT date_mouvement, nature, quantite_mouvement, quantite_avant, quantite_apres FROM historique WHERE produit ILIKE '%X%' ORDER BY date_mouvement DESC;"
)

vn.train(
    question="Mouvements d'entrée cette semaine",
    sql="SELECT reference, produit, quantite_mouvement, date_mouvement FROM historique WHERE nature = 'Entrée' AND date_mouvement >= DATE_TRUNC('week', CURRENT_DATE);"
)

vn.train(
    question="Mouvements de sortie par jour",
    sql="SELECT DATE(date_mouvement) as jour, COUNT(*) as nb_sorties, SUM(quantite_mouvement) as quantite_totale FROM historique WHERE nature = 'Sortie' GROUP BY DATE(date_mouvement) ORDER BY jour DESC;"
)

# =====================================================
# QUESTIONS SUR LES TABLES D'ATELIER
# =====================================================

vn.train(
    question="Liste des tables d'atelier",
    sql="SELECT id_table, nom_table, type_atelier, responsable FROM tables_atelier WHERE statut = 'Actif';"
)

vn.train(
    question="Tables d'atelier par responsable",
    sql="SELECT responsable, COUNT(*) as nb_tables FROM tables_atelier WHERE statut = 'Actif' GROUP BY responsable;"
)

# =====================================================
# QUESTIONS SUR LES LISTES D'INVENTAIRE
# =====================================================

vn.train(
    question="Listes d'inventaire en cours",
    sql="SELECT id_liste, nom_liste, statut, nb_produits, date_creation FROM listes_inventaire WHERE statut IN ('En préparation', 'En cours');"
)

vn.train(
    question="Produits dans la liste d'inventaire X",
    sql="SELECT reference_produit, nom_produit, quantite_theorique, quantite_comptee, emplacement FROM produits_listes_inventaire WHERE id_liste = 'X';"
)

# =====================================================
# QUESTIONS COMPLEXES AVEC JOINTURES
# =====================================================

vn.train(
    question="Produits et leurs fournisseurs avec contacts",
    sql="SELECT i.reference, i.produits, i.quantite, f.nom_fournisseur, f.contact1_email FROM inventaire i LEFT JOIN fournisseurs f ON i.fournisseur = f.nom_fournisseur WHERE i.quantite > 0;"
)

vn.train(
    question="Stock par site avec détails",
    sql="SELECT s.nom_site, l.nom_lieu, e.nom_emplacement, COUNT(i.id) as nb_produits, SUM(i.quantite) as stock_total FROM sites s JOIN lieux l ON s.id = l.site_id JOIN emplacements e ON l.id = e.lieu_id LEFT JOIN inventaire i ON CONCAT(s.nom_site, ' - ', l.nom_lieu, ' - ', e.nom_emplacement) = i.emplacement GROUP BY s.nom_site, l.nom_lieu, e.nom_emplacement ORDER BY stock_total DESC;"
)

vn.train(
    question="Analyse des ruptures de stock",
    sql="SELECT i.reference, i.produits, i.quantite, i.stock_min, f.nom_fournisseur, f.contact1_email FROM inventaire i LEFT JOIN fournisseurs f ON i.fournisseur = f.nom_fournisseur WHERE i.quantite <= i.stock_min ORDER BY (i.stock_min - i.quantite) DESC;"
)

# =====================================================
# QUESTIONS STATISTIQUES ET ANALYTIQUES
# =====================================================

vn.train(
    question="Top 10 des produits les plus stockés",
    sql="SELECT reference, produits, quantite, prix_unitaire, (quantite * prix_unitaire) as valeur FROM inventaire WHERE quantite > 0 ORDER BY quantite DESC LIMIT 10;"
)

vn.train(
    question="Répartition du stock par secteur",
    sql="SELECT secteur, COUNT(*) as nb_produits, SUM(quantite) as stock_total, AVG(prix_unitaire) as prix_moyen FROM inventaire WHERE secteur IS NOT NULL GROUP BY secteur ORDER BY stock_total DESC;"
)

vn.train(
    question="Évolution des entrées/sorties par mois",
    sql="SELECT DATE_TRUNC('month', date_mouvement) as mois, nature, COUNT(*) as nb_mouvements, SUM(quantite_mouvement) as quantite_totale FROM historique GROUP BY DATE_TRUNC('month', date_mouvement), nature ORDER BY mois DESC, nature;"
)

vn.train(
    question="Taux d'occupation des emplacements",
    sql="SELECT nom_emplacement, nb_produits, capacite_max, taux_occupation, (nb_produits::float / capacite_max * 100) as pourcentage_reel FROM emplacements WHERE capacite_max > 0 ORDER BY taux_occupation DESC;"
)

# =====================================================
# QUESTIONS DE RECHERCHE ET FILTRES
# =====================================================

vn.train(
    question="Recherche produit contenant 'vis'",
    sql="SELECT reference, produits, quantite, emplacement FROM inventaire WHERE produits ILIKE '%vis%' ORDER BY produits;"
)

vn.train(
    question="Produits ajoutés cette semaine",
    sql="SELECT reference, produits, quantite, date_entree FROM inventaire WHERE date_entree >= DATE_TRUNC('week', CURRENT_DATE) ORDER BY date_entree DESC;"
)

vn.train(
    question="Fournisseurs sans produits en stock",
    sql="SELECT f.nom_fournisseur, f.contact1_email FROM fournisseurs f LEFT JOIN inventaire i ON f.nom_fournisseur = i.fournisseur WHERE i.fournisseur IS NULL AND f.statut = 'Actif';"
)

print("Toutes les paires question-SQL ont été définies !")
print("Copiez ces instructions vn.train() dans votre notebook train.ipynb") 
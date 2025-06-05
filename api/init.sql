-- Script d'initialisation de la base de données GMAO
-- Schéma basé sur les fichiers Excel de l'application Streamlit

-- =====================================================
-- TABLE PRINCIPALE: INVENTAIRE (PRODUITS)
-- =====================================================
CREATE TABLE IF NOT EXISTS inventaire (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    reference_fournisseur VARCHAR(100),
    produits VARCHAR(500) NOT NULL,
    unite_stockage VARCHAR(20),
    unite_commande VARCHAR(50),
    stock_min INTEGER DEFAULT 0,
    stock_max INTEGER DEFAULT 100,
    site VARCHAR(100),
    lieu VARCHAR(100),
    emplacement VARCHAR(100),
    fournisseur VARCHAR(200),
    prix_unitaire DECIMAL(10,2) DEFAULT 0,
    categorie VARCHAR(100),
    secteur VARCHAR(100),
    reference VARCHAR(20) UNIQUE NOT NULL, -- Référence QR unique de 10 chiffres
    quantite INTEGER DEFAULT 0,
    date_entree DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: FOURNISSEURS
-- =====================================================
CREATE TABLE IF NOT EXISTS fournisseurs (
    id SERIAL PRIMARY KEY,
    id_fournisseur VARCHAR(20) UNIQUE NOT NULL,
    nom_fournisseur VARCHAR(200) NOT NULL,
    adresse TEXT,
    
    -- Contact 1
    contact1_nom VARCHAR(100),
    contact1_prenom VARCHAR(100),
    contact1_fonction VARCHAR(100),
    contact1_tel_fixe VARCHAR(20),
    contact1_tel_mobile VARCHAR(20),
    contact1_email VARCHAR(200),
    
    -- Contact 2
    contact2_nom VARCHAR(100),
    contact2_prenom VARCHAR(100),
    contact2_fonction VARCHAR(100),
    contact2_tel_fixe VARCHAR(20),
    contact2_tel_mobile VARCHAR(20),
    contact2_email VARCHAR(200),
    
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    nb_produits INTEGER DEFAULT 0,
    valeur_stock_total DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- STRUCTURE HIÉRARCHIQUE: SITES > LIEUX > EMPLACEMENTS
-- =====================================================

-- TABLE: SITES (Niveau 1)
CREATE TABLE IF NOT EXISTS sites (
    id SERIAL PRIMARY KEY,
    code_site VARCHAR(20) UNIQUE NOT NULL,
    nom_site VARCHAR(200) NOT NULL,
    adresse TEXT,
    ville VARCHAR(100),
    code_postal VARCHAR(10),
    pays VARCHAR(100) DEFAULT 'France',
    responsable VARCHAR(200),
    telephone VARCHAR(50),
    email VARCHAR(200),
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: LIEUX (Niveau 2)
CREATE TABLE IF NOT EXISTS lieux (
    id SERIAL PRIMARY KEY,
    code_lieu VARCHAR(20) UNIQUE NOT NULL,
    nom_lieu VARCHAR(200) NOT NULL,
    site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    type_lieu VARCHAR(100),
    niveau VARCHAR(50),
    surface DECIMAL(10,2),
    responsable VARCHAR(200),
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: EMPLACEMENTS (Niveau 3)
CREATE TABLE IF NOT EXISTS emplacements (
    id SERIAL PRIMARY KEY,
    code_emplacement VARCHAR(20) UNIQUE NOT NULL,
    nom_emplacement VARCHAR(200) NOT NULL,
    lieu_id INTEGER NOT NULL REFERENCES lieux(id) ON DELETE CASCADE,
    type_emplacement VARCHAR(100),
    position VARCHAR(100),
    capacite_max INTEGER DEFAULT 100,
    temperature_min DECIMAL(5,2),
    temperature_max DECIMAL(5,2),
    humidite_max DECIMAL(5,2),
    conditions_speciales TEXT,
    responsable VARCHAR(200),
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    nb_produits INTEGER DEFAULT 0,
    taux_occupation DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: DEMANDES DE MATERIEL
-- =====================================================
CREATE TABLE IF NOT EXISTS demandes (
    id SERIAL PRIMARY KEY,
    id_demande VARCHAR(50) UNIQUE NOT NULL,
    date_demande TIMESTAMP NOT NULL,
    demandeur VARCHAR(200) NOT NULL,
    produits_demandes TEXT NOT NULL, -- JSON stocké comme texte
    motif TEXT,
    statut VARCHAR(50) DEFAULT 'En attente',
    date_traitement TIMESTAMP,
    traite_par VARCHAR(200),
    commentaires TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: HISTORIQUE DES MOUVEMENTS
-- =====================================================
CREATE TABLE IF NOT EXISTS historique (
    id SERIAL PRIMARY KEY,
    date_mouvement TIMESTAMP NOT NULL,
    reference VARCHAR(20), -- Référence du produit
    produit VARCHAR(500) NOT NULL,
    nature VARCHAR(50) NOT NULL, -- Entrée, Sortie, Ajustement
    quantite_mouvement INTEGER NOT NULL,
    quantite_avant INTEGER NOT NULL,
    quantite_apres INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: TABLES D'ATELIER
-- =====================================================
CREATE TABLE IF NOT EXISTS tables_atelier (
    id SERIAL PRIMARY KEY,
    id_table VARCHAR(20) UNIQUE NOT NULL,
    nom_table VARCHAR(200) NOT NULL,
    type_atelier VARCHAR(100) NOT NULL,
    emplacement VARCHAR(200) NOT NULL,
    responsable VARCHAR(200) NOT NULL,
    statut VARCHAR(20) DEFAULT 'Actif',
    date_creation DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: LISTES D'INVENTAIRE
-- =====================================================
CREATE TABLE IF NOT EXISTS listes_inventaire (
    id SERIAL PRIMARY KEY,
    id_liste VARCHAR(20) UNIQUE NOT NULL,
    nom_liste VARCHAR(300) NOT NULL,
    date_creation TIMESTAMP NOT NULL,
    statut VARCHAR(50) DEFAULT 'En préparation',
    nb_produits INTEGER DEFAULT 0,
    cree_par VARCHAR(200) DEFAULT 'Utilisateur',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE: PRODUITS DES LISTES D'INVENTAIRE
-- =====================================================
CREATE TABLE IF NOT EXISTS produits_listes_inventaire (
    id SERIAL PRIMARY KEY,
    id_liste VARCHAR(20) NOT NULL,
    reference_produit VARCHAR(20) NOT NULL,
    nom_produit VARCHAR(500) NOT NULL,
    emplacement VARCHAR(100),
    quantite_theorique INTEGER NOT NULL,
    quantite_comptee INTEGER,
    categorie VARCHAR(100),
    fournisseur VARCHAR(200),
    date_ajout TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_liste) REFERENCES listes_inventaire(id_liste) ON DELETE CASCADE
);

-- =====================================================
-- INDEX POUR AMÉLIORER LES PERFORMANCES
-- =====================================================

-- Index sur la table inventaire
CREATE INDEX IF NOT EXISTS idx_inventaire_code ON inventaire(code);
CREATE INDEX IF NOT EXISTS idx_inventaire_reference ON inventaire(reference);
CREATE INDEX IF NOT EXISTS idx_inventaire_fournisseur ON inventaire(fournisseur);
CREATE INDEX IF NOT EXISTS idx_inventaire_emplacement ON inventaire(emplacement);
CREATE INDEX IF NOT EXISTS idx_inventaire_categorie ON inventaire(categorie);

-- Index sur les fournisseurs
CREATE INDEX IF NOT EXISTS idx_fournisseurs_nom ON fournisseurs(nom_fournisseur);
CREATE INDEX IF NOT EXISTS idx_fournisseurs_id ON fournisseurs(id_fournisseur);

-- Index sur les sites
CREATE INDEX IF NOT EXISTS idx_sites_code ON sites(code_site);
CREATE INDEX IF NOT EXISTS idx_sites_nom ON sites(nom_site);

-- Index sur les lieux
CREATE INDEX IF NOT EXISTS idx_lieux_code ON lieux(code_lieu);
CREATE INDEX IF NOT EXISTS idx_lieux_nom ON lieux(nom_lieu);
CREATE INDEX IF NOT EXISTS idx_lieux_site ON lieux(site_id);

-- Index sur les emplacements
CREATE INDEX IF NOT EXISTS idx_emplacements_code ON emplacements(code_emplacement);
CREATE INDEX IF NOT EXISTS idx_emplacements_nom ON emplacements(nom_emplacement);
CREATE INDEX IF NOT EXISTS idx_emplacements_lieu ON emplacements(lieu_id);

-- Index sur les demandes
CREATE INDEX IF NOT EXISTS idx_demandes_statut ON demandes(statut);
CREATE INDEX IF NOT EXISTS idx_demandes_demandeur ON demandes(demandeur);
CREATE INDEX IF NOT EXISTS idx_demandes_date ON demandes(date_demande);

-- Index sur l'historique
CREATE INDEX IF NOT EXISTS idx_historique_reference ON historique(reference);
CREATE INDEX IF NOT EXISTS idx_historique_date ON historique(date_mouvement);
CREATE INDEX IF NOT EXISTS idx_historique_nature ON historique(nature);

-- Index sur les tables d'atelier
CREATE INDEX IF NOT EXISTS idx_tables_atelier_type ON tables_atelier(type_atelier);
CREATE INDEX IF NOT EXISTS idx_tables_atelier_responsable ON tables_atelier(responsable);

-- Index sur les listes d'inventaire
CREATE INDEX IF NOT EXISTS idx_listes_inventaire_statut ON listes_inventaire(statut);
CREATE INDEX IF NOT EXISTS idx_produits_listes_reference ON produits_listes_inventaire(reference_produit);

-- =====================================================
-- FONCTIONS ET TRIGGERS
-- =====================================================

-- Fonction pour mettre à jour les statistiques des fournisseurs
CREATE OR REPLACE FUNCTION update_fournisseur_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour le nombre de produits et la valeur totale du stock pour le fournisseur
    UPDATE fournisseurs 
    SET 
        nb_produits = (
            SELECT COUNT(*) 
            FROM inventaire 
            WHERE fournisseur = fournisseurs.nom_fournisseur
        ),
        valeur_stock_total = (
            SELECT COALESCE(SUM(quantite * prix_unitaire), 0)
            FROM inventaire 
            WHERE fournisseur = fournisseurs.nom_fournisseur
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE nom_fournisseur = COALESCE(NEW.fournisseur, OLD.fournisseur);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour les stats des fournisseurs
CREATE TRIGGER trigger_update_fournisseur_stats
    AFTER INSERT OR UPDATE OR DELETE ON inventaire
    FOR EACH ROW
    EXECUTE FUNCTION update_fournisseur_stats();

-- Fonction pour mettre à jour les statistiques des emplacements
CREATE OR REPLACE FUNCTION update_emplacement_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour le nombre de produits et le taux d'occupation pour l'emplacement
    UPDATE emplacements 
    SET 
        nb_produits = (
            SELECT COUNT(*) 
            FROM inventaire 
            WHERE emplacement = emplacements.nom_emplacement
        ),
        taux_occupation = (
            SELECT CASE 
                WHEN emplacements.capacite_max > 0 THEN 
                    ROUND((COUNT(*)::DECIMAL / emplacements.capacite_max * 100), 2)
                ELSE 0 
            END
            FROM inventaire 
            WHERE emplacement = emplacements.nom_emplacement
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE nom_emplacement = COALESCE(NEW.emplacement, OLD.emplacement);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour les stats des emplacements
CREATE TRIGGER trigger_update_emplacement_stats
    AFTER INSERT OR UPDATE OR DELETE ON inventaire
    FOR EACH ROW
    EXECUTE FUNCTION update_emplacement_stats();

-- Fonction pour mettre à jour le nombre de produits dans les listes d'inventaire
CREATE OR REPLACE FUNCTION update_liste_inventaire_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour le nombre de produits dans la liste
    UPDATE listes_inventaire 
    SET 
        nb_produits = (
            SELECT COUNT(*) 
            FROM produits_listes_inventaire 
            WHERE id_liste = listes_inventaire.id_liste
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id_liste = COALESCE(NEW.id_liste, OLD.id_liste);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour les stats des listes d'inventaire
CREATE TRIGGER trigger_update_liste_inventaire_stats
    AFTER INSERT OR UPDATE OR DELETE ON produits_listes_inventaire
    FOR EACH ROW
    EXECUTE FUNCTION update_liste_inventaire_stats();

-- =====================================================
-- TRIGGERS POUR LA HIÉRARCHIE
-- =====================================================

-- Fonction pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour updated_at
CREATE TRIGGER update_sites_updated_at BEFORE UPDATE ON sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lieux_updated_at BEFORE UPDATE ON lieux
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_emplacements_updated_at BEFORE UPDATE ON emplacements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

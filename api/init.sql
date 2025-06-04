-- Script d'initialisation de la base de données GMAO
-- Tables pour la gestion de stock

-- Table des catégories de produits
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des fournisseurs
CREATE TABLE IF NOT EXISTS fournisseurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    contact VARCHAR(100),
    email VARCHAR(100),
    telephone VARCHAR(20),
    adresse TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des produits/articles
CREATE TABLE IF NOT EXISTS produits (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    description TEXT,
    reference VARCHAR(50) UNIQUE,
    code_barre VARCHAR(50),
    categorie_id INTEGER REFERENCES categories(id),
    fournisseur_id INTEGER REFERENCES fournisseurs(id),
    prix_unitaire DECIMAL(10,2),
    stock_min INTEGER DEFAULT 0,
    stock_max INTEGER DEFAULT 1000,
    unite VARCHAR(20) DEFAULT 'pièce',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des mouvements de stock
CREATE TABLE IF NOT EXISTS mouvements_stock (
    id SERIAL PRIMARY KEY,
    produit_id INTEGER NOT NULL REFERENCES produits(id),
    type_mouvement VARCHAR(20) NOT NULL CHECK (type_mouvement IN ('ENTREE', 'SORTIE', 'AJUSTEMENT')),
    quantite INTEGER NOT NULL,
    stock_avant INTEGER NOT NULL,
    stock_apres INTEGER NOT NULL,
    motif VARCHAR(200),
    reference_document VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Table du stock actuel (vue matérialisée pour performance)
CREATE TABLE IF NOT EXISTS stock_actuel (
    produit_id INTEGER PRIMARY KEY REFERENCES produits(id),
    quantite_disponible INTEGER NOT NULL DEFAULT 0,
    derniere_entree TIMESTAMP,
    derniere_sortie TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_produits_reference ON produits(reference);
CREATE INDEX IF NOT EXISTS idx_produits_categorie ON produits(categorie_id);
CREATE INDEX IF NOT EXISTS idx_mouvements_produit ON mouvements_stock(produit_id);
CREATE INDEX IF NOT EXISTS idx_mouvements_date ON mouvements_stock(created_at);

-- Fonction pour mettre à jour le stock automatiquement
CREATE OR REPLACE FUNCTION update_stock_actuel()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour ou insérer dans stock_actuel
    INSERT INTO stock_actuel (produit_id, quantite_disponible, updated_at)
    VALUES (NEW.produit_id, NEW.stock_apres, CURRENT_TIMESTAMP)
    ON CONFLICT (produit_id) 
    DO UPDATE SET 
        quantite_disponible = NEW.stock_apres,
        updated_at = CURRENT_TIMESTAMP,
        derniere_entree = CASE WHEN NEW.type_mouvement = 'ENTREE' THEN CURRENT_TIMESTAMP ELSE stock_actuel.derniere_entree END,
        derniere_sortie = CASE WHEN NEW.type_mouvement = 'SORTIE' THEN CURRENT_TIMESTAMP ELSE stock_actuel.derniere_sortie END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour automatiquement le stock
CREATE TRIGGER trigger_update_stock
    AFTER INSERT ON mouvements_stock
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_actuel();

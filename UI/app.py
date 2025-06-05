from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import requests
import os
from datetime import datetime
import qrcode
import io
import base64
from PIL import Image
import json

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration de l'API
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8010')

class APIClient:
    """Client pour communiquer avec l'API FastAPI"""
    
    def __init__(self, base_url):
        self.base_url = base_url
    
    def get(self, endpoint, params=None):
        """Effectuer une requête GET"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API GET {endpoint}: {e}")
            return None
    
    def post(self, endpoint, data=None):
        """Effectuer une requête POST"""
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data)
            if response.status_code == 422:
                print(f"Erreur 422 pour POST {endpoint}")
                print(f"Données envoyées: {data}")
                print(f"Réponse d'erreur: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API POST {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Détails de l'erreur: {e.response.text}")
            return None
    
    def put(self, endpoint, data=None):
        """Effectuer une requête PUT"""
        try:
            response = requests.put(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API PUT {endpoint}: {e}")
            return None
    
    def delete(self, endpoint):
        """Effectuer une requête DELETE"""
        try:
            response = requests.delete(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API DELETE {endpoint}: {e}")
            return None

# Instance du client API
api_client = APIClient(API_BASE_URL)

# =====================================================
# ROUTES PRINCIPALES - MÊME STRUCTURE QUE STREAMLIT
# =====================================================

@app.route('/')
def index():
    """Page d'accueil avec menu principal - équivalent à la sidebar Streamlit"""
    return render_template('index.html')

# =====================================================
# ACTIONS PRINCIPALES
# =====================================================

@app.route('/magasin')
def magasin():
    """Page Magasin - Vue d'ensemble du stock"""
    produits = api_client.get('/inventaire/')
    
    if produits is None:
        produits = []
        flash('Erreur lors du chargement de l\'inventaire', 'error')
    
    # Calculer les statistiques comme dans Streamlit
    stats = {
        'total_produits': len(produits),
        'stock_critique': 0,
        'stock_faible': 0,
        'surstock': 0,
        'stock_normal': 0,
        'valeur_totale': 0
    }
    
    if produits:
        for produit in produits:
            # Conversion sécurisée des valeurs numériques
            try:
                quantite = int(produit.get('quantite', 0))
            except (ValueError, TypeError):
                quantite = 0
                
            try:
                stock_min = int(produit.get('seuil_alerte', 0))
            except (ValueError, TypeError):
                stock_min = 0
                
            try:
                stock_max = int(produit.get('stock_max', 100))
            except (ValueError, TypeError):
                stock_max = 100
                
            try:
                prix = float(produit.get('prix_unitaire', 0))
            except (ValueError, TypeError):
                prix = 0
            
            # Calcul du seuil d'alerte (30% entre min et max)
            if stock_max > stock_min:
                seuil_alerte = stock_min + (stock_max - stock_min) * 0.3
            else:
                seuil_alerte = stock_min
            
            # Classification du stock
            if quantite < stock_min:
                stats['stock_critique'] += 1
            elif quantite > stock_max:
                stats['surstock'] += 1
            elif quantite <= seuil_alerte:
                stats['stock_faible'] += 1
            else:
                stats['stock_normal'] += 1
            
            # Valeur du stock
            stats['valeur_totale'] += quantite * prix
    
    return render_template('magasin.html', produits=produits, stats=stats)

@app.route('/historique-mouvements')
def historique_mouvements():
    """Page Historique des mouvements"""
    historique = api_client.get('/historique/')
    
    if historique is None:
        historique = []
        flash('Erreur lors du chargement de l\'historique', 'error')
    
    # Traiter les données pour l'affichage
    for mouvement in historique:
        # S'assurer que les champs nécessaires existent
        if 'date_mouvement' in mouvement:
            mouvement['date'] = mouvement['date_mouvement']
        elif 'date' not in mouvement:
            mouvement['date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Normaliser la nature pour l'affichage
        if 'nature' not in mouvement:
            mouvement['nature'] = 'Mouvement'
            mouvement['nature_normalized'] = 'inventaire'
            mouvement['nature_display'] = 'Mouvement'
        else:
            # Conserver la nature originale et ajouter une version normalisée
            mouvement['nature_originale'] = mouvement['nature']
            nature_lower = mouvement['nature'].lower()
            if 'entrée' in nature_lower or 'entree' in nature_lower:
                mouvement['nature_normalized'] = 'entree'
                mouvement['nature_display'] = 'Entrée'
            elif 'sortie' in nature_lower:
                mouvement['nature_normalized'] = 'sortie'
                mouvement['nature_display'] = 'Sortie'
            elif 'ajustement' in nature_lower or 'régule' in nature_lower or 'regule' in nature_lower:
                mouvement['nature_normalized'] = 'ajustement'
                mouvement['nature_display'] = 'Ajustement'
            else:
                mouvement['nature_normalized'] = 'inventaire'
                mouvement['nature_display'] = mouvement['nature']
            
        if 'quantite_mouvement' not in mouvement:
            mouvement['quantite_mouvement'] = mouvement.get('quantite', 0)
        if 'quantite_avant' not in mouvement:
            mouvement['quantite_avant'] = 0
        if 'quantite_apres' not in mouvement:
            mouvement['quantite_apres'] = mouvement.get('quantite', 0)
        if 'commentaires' not in mouvement:
            mouvement['commentaires'] = ''
    
    return render_template('historique_mouvements.html', historique=historique)

@app.route('/alertes-stock')
def alertes_stock():
    """Page Alertes de stock"""
    produits = api_client.get('/inventaire/')
    
    if produits is None:
        produits = []
        flash('Erreur lors du chargement de l\'inventaire', 'error')
    
    # Calculer les alertes comme dans Streamlit
    produits_avec_alertes = []
    
    for produit in produits:
        # Conversion sécurisée des valeurs numériques
        try:
            quantite = int(produit.get('quantite', 0))
        except (ValueError, TypeError):
            quantite = 0
            
        try:
            stock_min = int(produit.get('seuil_alerte', 0))
        except (ValueError, TypeError):
            stock_min = 0
            
        try:
            stock_max = int(produit.get('stock_max', 100))
        except (ValueError, TypeError):
            stock_max = 100
        
        # Calcul du seuil d'alerte (30% entre min et max)
        if stock_max > stock_min:
            seuil_alerte = stock_min + (stock_max - stock_min) * 0.3
        else:
            seuil_alerte = stock_min
        
        # Déterminer le statut
        statut = None
        if quantite < stock_min:
            statut = 'critique'
        elif quantite > stock_max:
            statut = 'surstock'
        elif quantite <= seuil_alerte:
            statut = 'faible'
        
        # Ajouter seulement les produits avec des alertes
        if statut:
            produit_alerte = produit.copy()
            produit_alerte['statut'] = statut
            produit_alerte['seuil_alerte'] = int(seuil_alerte)
            produits_avec_alertes.append(produit_alerte)
    
    return render_template('alertes_stock.html', produits=produits_avec_alertes)

# =====================================================
# DEMANDES
# =====================================================

@app.route('/demande-materiel')
def demande_materiel():
    """Page Demande de matériel - équivalent Streamlit"""
    # Charger les tables d'atelier pour l'identification
    tables = api_client.get('/tables-atelier/') or []
    produits = api_client.get('/inventaire/') or []
    
    return render_template('demande_materiel.html', tables=tables, produits=produits)

@app.route('/gestion-demandes')
def gestion_demandes():
    """Page Gestion des demandes"""
    demandes_list = api_client.get('/demandes/')
    
    if demandes_list is None:
        demandes_list = []
        flash('Erreur lors du chargement des demandes', 'error')
    
    return render_template('gestion_demandes.html', demandes=demandes_list)

# =====================================================
# MOUVEMENTS
# =====================================================

@app.route('/entree-stock', methods=['GET', 'POST'])
def entree_stock():
    """Page Entrée de stock"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Construire le motif avec utilisateur et commentaires
        motif_parts = []
        if data.get('utilisateur'):
            motif_parts.append(f"Utilisateur: {data['utilisateur']}")
        if data.get('commentaires'):
            motif_parts.append(f"Commentaires: {data['commentaires']}")
        motif = " | ".join(motif_parts) if motif_parts else None
        
        mouvement_data = {
            'reference_produit': data['reference'],
            'nature': 'Entrée',
            'quantite': int(data['quantite']),
            'motif': motif
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify({'success': True, 'message': 'Entrée enregistrée avec succès'})
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
    
    return render_template('entree_stock.html')

@app.route('/sortie-stock', methods=['GET', 'POST'])
def sortie_stock():
    """Page Sortie de stock"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Construire le motif avec utilisateur et commentaires
        motif_parts = []
        if data.get('utilisateur'):
            motif_parts.append(f"Utilisateur: {data['utilisateur']}")
        if data.get('commentaires'):
            motif_parts.append(f"Commentaires: {data['commentaires']}")
        motif = " | ".join(motif_parts) if motif_parts else None
        
        mouvement_data = {
            'reference_produit': data['reference'],
            'nature': 'Sortie',
            'quantite': int(data['quantite']),
            'motif': motif
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify({'success': True, 'message': 'Sortie enregistrée avec succès'})
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
    
    return render_template('sortie_stock.html')

@app.route('/regule-stock', methods=['GET', 'POST'])
def regule_stock():
    """Page Régule - Ajustement d'inventaire"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Construire le motif avec utilisateur et commentaires
        motif_parts = []
        if data.get('utilisateur'):
            motif_parts.append(f"Utilisateur: {data['utilisateur']}")
        if data.get('commentaires'):
            motif_parts.append(f"Commentaires: {data['commentaires']}")
        motif = " | ".join(motif_parts) if motif_parts else None
        
        mouvement_data = {
            'reference_produit': data['reference'],
            'nature': 'Ajustement',
            'quantite': int(data['quantite']),  # Pour ajustement, c'est la nouvelle quantité totale
            'motif': motif
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify({'success': True, 'message': 'Ajustement enregistré avec succès'})
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
    
    return render_template('regule_stock.html')

@app.route('/preparer-inventaire')
def preparer_inventaire():
    """Page Préparer l'inventaire"""
    listes = api_client.get('/listes-inventaire/') or []
    produits = api_client.get('/inventaire/') or []
    
    return render_template('preparer_inventaire.html', listes=listes, produits=produits)

# =====================================================
# ADMINISTRATION
# =====================================================

@app.route('/gestion-produits')
def gestion_produits():
    """Page Gestion des produits"""
    produits_raw = api_client.get('/inventaire/') or []
    # Normaliser les données des produits
    produits = [normalize_produit(p.copy()) for p in produits_raw]
    
    fournisseurs = api_client.get('/fournisseurs/') or []
    emplacements = api_client.get('/emplacements/') or []
    
    return render_template('gestion_produits.html', produits=produits, 
                         fournisseurs=fournisseurs, emplacements=emplacements)

@app.route('/api/produits', methods=['POST'])
def creer_produit():
    """Créer un nouveau produit"""
    try:
        data = request.get_json()
        print(f"Données reçues: {data}")  # Debug
        
        # Validation des champs requis
        if not data.get('designation'):
            return jsonify({'success': False, 'message': 'La désignation est requise'})
        
        # Générer un code QR automatique à 10 chiffres
        import random
        import string
        qr_code = ''.join(random.choices(string.digits, k=10))
        
        # Préparer les données pour l'API selon le nouveau schéma
        produit_data = {
            'code': qr_code,  # Code QR généré automatiquement
            'reference': qr_code,  # Référence QR unique
            'reference_fournisseur': data.get('reference_fournisseur', '') or None,
            'produits': data.get('designation', ''),  # Utiliser désignation
            'unite_stockage': data.get('unite_stockage', '') or None,
            'unite_commande': data.get('unite_commande', '') or None,
            'stock_min': int(data.get('seuil_alerte', 0)) if data.get('seuil_alerte') else 0,
            'stock_max': int(data.get('stock_max', 100)) if data.get('stock_max') else 100,
            'site': data.get('site', '') or None,
            'lieu': data.get('lieu', '') or None,
            'emplacement': data.get('emplacement', '') or None,
            'fournisseur': data.get('fournisseur', '') or None,
            'prix_unitaire': float(data.get('prix_unitaire', 0)) if data.get('prix_unitaire') else 0.0,
            'categorie': data.get('categorie', '') or None,
            'secteur': data.get('secteur', '') or None,
            'quantite': int(data.get('quantite', 0)) if data.get('quantite') else 0
        }
        
        # Ajouter la description si fournie
        if data.get('description'):
            produit_data['produits'] = f"{data.get('designation')} - {data.get('description')}"
        
        print(f"Données envoyées à l'API: {produit_data}")  # Debug
        
        result = api_client.post('/inventaire/', produit_data)
        print(f"Résultat API: {result}")  # Debug
        
        if result:
            return jsonify({'success': True, 'message': 'Produit créé avec succès', 'produit': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du produit'})
            
    except Exception as e:
        print(f"Erreur dans creer_produit: {str(e)}")  # Debug
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/produits/<int:produit_id>', methods=['PUT'])
def modifier_produit(produit_id):
    """Modifier un produit existant"""
    try:
        data = request.get_json()
        
        # Préparer les données pour l'API (seulement les champs modifiés)
        produit_data = {}
        
        # Note: La référence QR ne peut pas être modifiée
        
        if data.get('reference_fournisseur') is not None:
            produit_data['reference_fournisseur'] = data.get('reference_fournisseur')
            
        if data.get('designation'):
            if data.get('description'):
                produit_data['produits'] = f"{data.get('designation')} - {data.get('description')}"
            else:
                produit_data['produits'] = data.get('designation')
                
        if data.get('unite_stockage') is not None:
            produit_data['unite_stockage'] = data.get('unite_stockage')
            
        if data.get('unite_commande') is not None:
            produit_data['unite_commande'] = data.get('unite_commande')
                
        if data.get('seuil_alerte') is not None:
            produit_data['stock_min'] = int(data.get('seuil_alerte'))
            
        if data.get('stock_max') is not None:
            produit_data['stock_max'] = int(data.get('stock_max'))
            
        if data.get('site') is not None:
            produit_data['site'] = data.get('site')
            
        if data.get('lieu') is not None:
            produit_data['lieu'] = data.get('lieu')
            
        if data.get('emplacement') is not None:
            produit_data['emplacement'] = data.get('emplacement')
            
        if data.get('fournisseur') is not None:
            produit_data['fournisseur'] = data.get('fournisseur')
            
        if data.get('prix_unitaire') is not None:
            produit_data['prix_unitaire'] = float(data.get('prix_unitaire')) if data.get('prix_unitaire') else 0
            
        if data.get('categorie') is not None:
            produit_data['categorie'] = data.get('categorie')
            
        if data.get('secteur') is not None:
            produit_data['secteur'] = data.get('secteur')
        
        result = api_client.put(f'/inventaire/{produit_id}', produit_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Produit modifié avec succès', 'produit': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du produit'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/produits/<int:produit_id>', methods=['DELETE'])
def supprimer_produit(produit_id):
    """Supprimer un produit"""
    try:
        result = api_client.delete(f'/inventaire/{produit_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Produit supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du produit'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/produits/<reference>')
def get_produit_by_reference(reference):
    """Récupérer un produit par sa référence pour modification"""
    try:
        produit = api_client.get(f'/inventaire/reference/{reference}')
        
        if produit:
            return jsonify({'success': True, 'produit': produit})
        else:
            return jsonify({'success': False, 'message': 'Produit non trouvé'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/historique/reference/<reference>')
def historique_by_reference(reference):
    """Récupérer l'historique des mouvements d'un produit par référence"""
    try:
        historique = api_client.get(f'/historique/reference/{reference}')
        
        if historique:
            return jsonify(historique)
        else:
            return jsonify([])
            
    except Exception as e:
        return jsonify([])

@app.route('/mouvement-stock', methods=['POST'])
def mouvement_stock_api():
    """Effectuer un mouvement de stock depuis la page de détail"""
    try:
        data = request.get_json()
        
        # Mapper les natures pour l'API
        nature_mapping = {
            'entree': 'Entrée',
            'sortie': 'Sortie', 
            'inventaire': 'Ajustement'
        }
        
        mouvement_data = {
            'reference_produit': data.get('reference'),
            'nature': nature_mapping.get(data.get('nature'), data.get('nature')),
            'quantite': int(data.get('quantite')),
            'motif': f"Utilisateur: {data.get('utilisateur')}" + (f" | {data.get('commentaires')}" if data.get('commentaires') else "")
        }
        
        result = api_client.post('/mouvements-stock/', mouvement_data)
        
        if result and result.get('success'):
            return jsonify(result)
        else:
            error_message = result.get('message', 'Erreur lors de l\'enregistrement') if result else 'Erreur lors de l\'enregistrement'
            return jsonify({'success': False, 'message': error_message})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/gestion-tables')
def gestion_tables():
    """Page Gestion des tables d'atelier"""
    tables = api_client.get('/tables-atelier/') or []
    
    return render_template('gestion_tables.html', tables=tables)

@app.route('/gestion-fournisseurs')
def gestion_fournisseurs():
    """Page Gestion des fournisseurs"""
    fournisseurs = api_client.get('/fournisseurs/') or []
    print(f"Fournisseurs récupérés: {fournisseurs}")  # Debug
    
    return render_template('gestion_fournisseurs.html', fournisseurs=fournisseurs)

@app.route('/gestion-emplacements')
def gestion_emplacements():
    """Page Gestion de la hiérarchie Site > Lieu > Emplacement"""
    sites = api_client.get('/sites/') or []
    lieux = api_client.get('/lieux/') or []
    emplacements = api_client.get('/emplacements-hierarchy/') or []
    
    return render_template('gestion_emplacements.html', 
                         sites=sites, 
                         lieux=lieux, 
                         emplacements=emplacements)

# =====================================================
# ROUTES UTILITAIRES (COMPATIBILITÉ)
# =====================================================

@app.route('/scanner')
def scanner():
    """Page de scanner QR code"""
    return render_template('scanner.html')

@app.route('/inventaire')
def inventaire():
    """Redirection vers magasin pour compatibilité"""
    return redirect(url_for('magasin'))

@app.route('/produit/<reference>')
def produit_detail(reference):
    """Page de détail d'un produit"""
    produit = api_client.get(f'/inventaire/reference/{reference}')
    
    if produit is None:
        flash('Produit non trouvé', 'error')
        return redirect(url_for('magasin'))
    
    # Générer le QR code
    qr_code_data = generate_qr_code(reference)
    
    return render_template('produit_detail.html', produit=produit, qr_code=qr_code_data)

@app.route('/api/produit/<reference>')
def api_produit(reference):
    """API endpoint pour récupérer un produit par référence (pour le scanner)"""
    produit = api_client.get(f'/inventaire/reference/{reference}')
    
    if produit:
        return jsonify(produit)
    else:
        return jsonify({'error': 'Produit non trouvé'}), 404

# Compatibilité avec les anciennes routes
@app.route('/demandes')
def demandes():
    """Redirection vers gestion des demandes"""
    return redirect(url_for('gestion_demandes'))

@app.route('/nouvelle-demande')
def nouvelle_demande():
    """Redirection vers demande de matériel"""
    return redirect(url_for('demande_materiel'))

@app.route('/stock-faible')
def stock_faible():
    """Redirection vers alertes de stock"""
    return redirect(url_for('alertes_stock'))

@app.route('/mouvement-stock')
def mouvement_stock():
    """Page de sélection du type de mouvement"""
    return render_template('mouvement_stock_menu.html')

def generate_qr_code(data):
    """Générer un QR code et le retourner en base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir en base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

# =====================================================
# FONCTIONS HELPER POUR LES TEMPLATES
# =====================================================

def get_stock_status(produit):
    """Détermine le statut du stock d'un produit"""
    quantite = produit.get('quantite', 0)
    # Normaliser les noms de champs entre API et templates
    stock_min = produit.get('stock_min', produit.get('seuil_alerte', 0))
    stock_max = produit.get('stock_max', 100)
    
    # Calcul du seuil d'alerte (30% entre min et max)
    seuil_alerte = stock_min + (stock_max - stock_min) * 0.3
    
    if quantite < stock_min:
        return 'critique'
    elif quantite > stock_max:
        return 'surstock'
    elif quantite <= seuil_alerte:
        return 'faible'
    else:
        return 'normal'

def get_status_class(produit):
    """Retourne la classe CSS pour le statut du stock"""
    status = get_stock_status(produit)
    return f'status-{status}'

def get_stock_status_text(produit):
    """Retourne le texte du statut du stock"""
    status = get_stock_status(produit)
    status_texts = {
        'critique': '🔴 Critique',
        'faible': '🟠 Faible',
        'surstock': '🟡 Surstock',
        'normal': '🟢 Normal'
    }
    return status_texts.get(status, '❓ Inconnu')

def normalize_produit(produit):
    """Normalise les données d'un produit pour compatibilité entre API et templates"""
    if not produit:
        return produit
    
    # Ajouter des alias pour la compatibilité
    if 'stock_min' in produit and 'seuil_alerte' not in produit:
        produit['seuil_alerte'] = produit['stock_min']
    if 'produits' in produit and 'nom' not in produit:
        # Extraire le nom de base du champ produits
        nom_complet = produit['produits']
        if ' - ' in nom_complet:
            produit['nom'] = nom_complet.split(' - ')[0]
        else:
            produit['nom'] = nom_complet
    
    return produit

# Enregistrer les fonctions helper pour les templates
app.jinja_env.globals.update(
    get_stock_status=get_stock_status,
    get_status_class=get_status_class,
    get_stock_status_text=get_stock_status_text,
    normalize_produit=normalize_produit
)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/api/fournisseurs', methods=['POST'])
def creer_fournisseur():
    """Créer un nouveau fournisseur"""
    try:
        data = request.get_json()
        
        # Générer un ID fournisseur automatique
        import random
        import string
        from datetime import datetime
        id_fournisseur = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Préparer les données pour l'API selon le schéma FournisseurCreate
        fournisseur_data = {
            'id_fournisseur': id_fournisseur,
            'nom_fournisseur': data.get('nom', ''),  # Mapper 'nom' vers 'nom_fournisseur'
            'contact_principal': data.get('contact', ''),
            'email': data.get('email', ''),
            'telephone': data.get('telephone', ''),
            'adresse': data.get('adresse', ''),
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/fournisseurs/', fournisseur_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Fournisseur créé avec succès', 'fournisseur': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du fournisseur'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/fournisseurs/<int:fournisseur_id>', methods=['PUT'])
def modifier_fournisseur(fournisseur_id):
    """Modifier un fournisseur existant"""
    try:
        data = request.get_json()
        
        # Préparer les données pour l'API (seulement les champs modifiés)
        fournisseur_data = {}
        
        if data.get('nom'):
            fournisseur_data['nom_fournisseur'] = data.get('nom')
            
        if data.get('contact') is not None:
            fournisseur_data['contact_principal'] = data.get('contact')
            
        if data.get('email') is not None:
            fournisseur_data['email'] = data.get('email')
            
        if data.get('telephone') is not None:
            fournisseur_data['telephone'] = data.get('telephone')
            
        if data.get('adresse') is not None:
            fournisseur_data['adresse'] = data.get('adresse')
            
        if data.get('statut') is not None:
            fournisseur_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/fournisseurs/{fournisseur_id}', fournisseur_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Fournisseur modifié avec succès', 'fournisseur': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du fournisseur'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/fournisseurs/<int:fournisseur_id>', methods=['DELETE'])
def supprimer_fournisseur(fournisseur_id):
    """Supprimer un fournisseur"""
    try:
        result = api_client.delete(f'/fournisseurs/{fournisseur_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Fournisseur supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du fournisseur'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/fournisseurs/<int:fournisseur_id>')
def get_fournisseur_by_id(fournisseur_id):
    """Récupérer un fournisseur par son ID"""
    try:
        result = api_client.get(f'/fournisseurs/{fournisseur_id}')
        
        if result:
            return jsonify({'success': True, 'fournisseur': result})
        else:
            return jsonify({'success': False, 'message': 'Fournisseur non trouvé'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# =====================================================
# ROUTES API POUR LA HIÉRARCHIE SITE > LIEU > EMPLACEMENT
# =====================================================

# SITES
@app.route('/api/sites', methods=['POST'])
def creer_site():
    """Créer un nouveau site"""
    try:
        data = request.get_json()
        
        # Générer un code site automatique
        import random
        import string
        from datetime import datetime
        code_site = f"SITE{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        site_data = {
            'code_site': code_site,
            'nom_site': data.get('nom_site', ''),
            'adresse': data.get('adresse', ''),
            'ville': data.get('ville', ''),
            'code_postal': data.get('code_postal', ''),
            'pays': data.get('pays', 'France'),
            'responsable': data.get('responsable', ''),
            'telephone': data.get('telephone', ''),
            'email': data.get('email', ''),
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/sites/', site_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Site créé avec succès', 'site': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du site'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/sites/<int:site_id>', methods=['PUT'])
def modifier_site(site_id):
    """Modifier un site existant"""
    try:
        data = request.get_json()
        
        site_data = {}
        if data.get('nom_site'):
            site_data['nom_site'] = data.get('nom_site')
        if data.get('adresse') is not None:
            site_data['adresse'] = data.get('adresse')
        if data.get('ville') is not None:
            site_data['ville'] = data.get('ville')
        if data.get('code_postal') is not None:
            site_data['code_postal'] = data.get('code_postal')
        if data.get('pays') is not None:
            site_data['pays'] = data.get('pays')
        if data.get('responsable') is not None:
            site_data['responsable'] = data.get('responsable')
        if data.get('telephone') is not None:
            site_data['telephone'] = data.get('telephone')
        if data.get('email') is not None:
            site_data['email'] = data.get('email')
        if data.get('statut') is not None:
            site_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/sites/{site_id}', site_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Site modifié avec succès', 'site': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du site'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/sites/<int:site_id>', methods=['DELETE'])
def supprimer_site(site_id):
    """Supprimer un site"""
    try:
        result = api_client.delete(f'/sites/{site_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Site supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du site'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# LIEUX
@app.route('/api/lieux', methods=['POST'])
def creer_lieu():
    """Créer un nouveau lieu"""
    try:
        data = request.get_json()
        
        # Générer un code lieu automatique
        from datetime import datetime
        code_lieu = f"LIEU{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        lieu_data = {
            'code_lieu': code_lieu,
            'nom_lieu': data.get('nom_lieu', ''),
            'site_id': int(data.get('site_id')),
            'type_lieu': data.get('type_lieu', ''),
            'niveau': data.get('niveau', ''),
            'surface': float(data.get('surface', 0)) if data.get('surface') else None,
            'responsable': data.get('responsable', ''),
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/lieux/', lieu_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Lieu créé avec succès', 'lieu': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création du lieu'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/lieux/<int:lieu_id>', methods=['PUT'])
def modifier_lieu(lieu_id):
    """Modifier un lieu existant"""
    try:
        data = request.get_json()
        
        lieu_data = {}
        if data.get('nom_lieu'):
            lieu_data['nom_lieu'] = data.get('nom_lieu')
        if data.get('site_id') is not None:
            lieu_data['site_id'] = int(data.get('site_id'))
        if data.get('type_lieu') is not None:
            lieu_data['type_lieu'] = data.get('type_lieu')
        if data.get('niveau') is not None:
            lieu_data['niveau'] = data.get('niveau')
        if data.get('surface') is not None:
            lieu_data['surface'] = float(data.get('surface')) if data.get('surface') else None
        if data.get('responsable') is not None:
            lieu_data['responsable'] = data.get('responsable')
        if data.get('statut') is not None:
            lieu_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/lieux/{lieu_id}', lieu_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Lieu modifié avec succès', 'lieu': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification du lieu'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/lieux/<int:lieu_id>', methods=['DELETE'])
def supprimer_lieu(lieu_id):
    """Supprimer un lieu"""
    try:
        result = api_client.delete(f'/lieux/{lieu_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Lieu supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression du lieu'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/lieux/site/<int:site_id>')
def get_lieux_by_site(site_id):
    """Récupérer les lieux d'un site"""
    try:
        result = api_client.get(f'/lieux/site/{site_id}')
        
        if result is not None:
            return jsonify({'success': True, 'lieux': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la récupération des lieux'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# EMPLACEMENTS
@app.route('/api/emplacements', methods=['POST'])
def creer_emplacement():
    """Créer un nouvel emplacement"""
    try:
        data = request.get_json()
        
        emplacement_data = {
            'nom_emplacement': data.get('nom_emplacement', ''),
            'lieu_id': int(data.get('lieu_id')),
            'type_emplacement': data.get('type_emplacement', ''),
            'position': data.get('position', ''),
            'capacite_max': int(data.get('capacite_max', 100)),
            'temperature_min': float(data.get('temperature_min')) if data.get('temperature_min') else None,
            'temperature_max': float(data.get('temperature_max')) if data.get('temperature_max') else None,
            'humidite_max': float(data.get('humidite_max')) if data.get('humidite_max') else None,
            'conditions_speciales': data.get('conditions_speciales', ''),
            'responsable': data.get('responsable', ''),
            'statut': data.get('statut', 'Actif')
        }
        
        result = api_client.post('/emplacements/', emplacement_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Emplacement créé avec succès', 'emplacement': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la création de l\'emplacement'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/emplacements/<int:emplacement_id>', methods=['PUT'])
def modifier_emplacement(emplacement_id):
    """Modifier un emplacement existant"""
    try:
        data = request.get_json()
        
        emplacement_data = {}
        if data.get('nom_emplacement'):
            emplacement_data['nom_emplacement'] = data.get('nom_emplacement')
        if data.get('lieu_id') is not None:
            emplacement_data['lieu_id'] = int(data.get('lieu_id'))
        if data.get('type_emplacement') is not None:
            emplacement_data['type_emplacement'] = data.get('type_emplacement')
        if data.get('position') is not None:
            emplacement_data['position'] = data.get('position')
        if data.get('capacite_max') is not None:
            emplacement_data['capacite_max'] = int(data.get('capacite_max'))
        if data.get('temperature_min') is not None:
            emplacement_data['temperature_min'] = float(data.get('temperature_min')) if data.get('temperature_min') else None
        if data.get('temperature_max') is not None:
            emplacement_data['temperature_max'] = float(data.get('temperature_max')) if data.get('temperature_max') else None
        if data.get('humidite_max') is not None:
            emplacement_data['humidite_max'] = float(data.get('humidite_max')) if data.get('humidite_max') else None
        if data.get('conditions_speciales') is not None:
            emplacement_data['conditions_speciales'] = data.get('conditions_speciales')
        if data.get('responsable') is not None:
            emplacement_data['responsable'] = data.get('responsable')
        if data.get('statut') is not None:
            emplacement_data['statut'] = data.get('statut')
        
        result = api_client.put(f'/emplacements/{emplacement_id}', emplacement_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Emplacement modifié avec succès', 'emplacement': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la modification de l\'emplacement'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/emplacements/<int:emplacement_id>', methods=['DELETE'])
def supprimer_emplacement(emplacement_id):
    """Supprimer un emplacement"""
    try:
        result = api_client.delete(f'/emplacements/{emplacement_id}')
        
        if result:
            return jsonify({'success': True, 'message': 'Emplacement supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la suppression de l\'emplacement'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/emplacements/lieu/<int:lieu_id>')
def get_emplacements_by_lieu(lieu_id):
    """Récupérer les emplacements d'un lieu"""
    try:
        result = api_client.get(f'/emplacements/lieu/{lieu_id}')
        
        if result is not None:
            return jsonify({'success': True, 'emplacements': result})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la récupération des emplacements'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
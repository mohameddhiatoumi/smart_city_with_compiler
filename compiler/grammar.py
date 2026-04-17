"""
Grammar definitions and keyword mappings for NL to SQL compilation
Defines French language patterns and their SQL equivalents
"""
SENSOR_TYPE_VALUES = {
    'air': ['air', 'pm2.5', 'pm10', 'co2', 'no2'],
    'bruit': ['bruit', 'db', 'décibel', 'decibel'],
    'trafic': ['trafic', 'vehicules', 'débit', 'debit'],
}
TIME_PERIODS = {
    'this_month': ['ce mois', 'ce mois-ci', 'mois courant'],
    'this_week': ['cette semaine', 'semaine courante', 'cette semaine-ci'],
    'today': ['aujourd hui', 'aujourd\'hui', 'aujourd hui', 'ce jour'],
    'recently': ['récemment', 'recemment', 'derniers jours', 'dernier mois'],
}
# Query intent keywords
INTENT_KEYWORDS = {
    'select': ['affiche', 'montre', 'liste', 'donne', 'trouve', 'quels', 'quelles', 'combien'],
    'count': ['combien', 'nombre'],
    'aggregate': ['moyenne', 'total', 'somme', 'maximum', 'minimum', 'max', 'min'],
}

# Entity mappings (French → SQL table names)
ENTITY_MAPPINGS = {
    'zones': ['zone', 'zones', 'quartier', 'quartiers', 'secteur', 'secteurs'],
    'capteurs': ['capteur', 'capteurs', 'sensor', 'sensors'],
    'mesures': ['mesure', 'mesures', 'measurement', 'measurements', 'donnée', 'données'],
    'citoyens': ['citoyen', 'citoyens', 'habitant', 'habitants', 'personne', 'personnes'],
    'vehicules': ['véhicule', 'véhicules', 'voiture', 'voitures', 'vehicle', 'vehicles'],
    'trajets': ['trajet', 'trajets', 'voyage', 'voyages', 'itinéraire', 'itinéraires'],
    'interventions': ['intervention', 'interventions', 'maintenance', 'maintenances'],
    'techniciens': ['technicien', 'techniciens', 'tech', 'techs'],
}

# Attribute mappings (French → SQL column names)
ATTRIBUTE_MAPPINGS = {
    # Zones
    'nom': ['nom', 'name', 'appellation'],
    
    # Capteurs
    'statut': ['statut', 'status', 'état', 'etat'],
    'type_capteur': ['type'],
    'taux_erreur': ['erreur', 'taux_erreur', 'error_rate'],
    
    # Mesures
    'pollution': ['pollution', 'polluée', 'polluees', 'pollué', 'pollués'],
    'valeur': ['valeur', 'value', 'mesure'],
    'type_mesure': ['type_mesure', 'mesure'],
    
    # Citoyens
    'score_ecologique': ['score', 'score_ecologique', 'score_écologique', 'ecologique', 'écologique', 'eco'],
    
    # Trajets
    'economie_co2': ['economie', 'économie', 'co2', 'economie_co2', 'économie_co2', 'économique'],
    'distance_km': ['distance'],
    
    # Common
    'timestamp': ['date', 'heure', 'temps', 'time'],
}

# Status values
STATUS_VALUES = {
    'hors_service': ['hors_service', 'hors service', 'hs', 'cassé', 'cassés'],
    'actif': ['actif', 'actifs', 'active', 'actives', 'fonctionnel'],
    'signale': ['signalé', 'signalés', 'signale', 'alerte', 'problème'],
    'en_maintenance': ['en_maintenance', 'en maintenance', 'maintenance'],
    'inactif': ['inactif', 'inactifs', 'inactive', 'inactives'],
}

# Comparison operators
OPERATORS = {
    '>': ['>', 'supérieur', 'plus grand', 'au-dessus', 'dessus'],
    '<': ['<', 'inférieur', 'plus petit', 'en-dessous', 'dessous'],
    '=': ['=', 'égal', 'egal'],
    '>=': ['>=', 'au moins', 'minimum'],
    '<=': ['<=', 'au plus', 'maximum'],
}

# Aggregate functions
AGGREGATES = {
    'AVG': ['moyenne', 'moy'],
    'SUM': ['somme', 'total'],
    'COUNT': ['nombre', 'combien', 'count'],
    'MAX': ['maximum', 'max', 'plus grand', 'plus élevé'],
    'MIN': ['minimum', 'min', 'plus petit', 'plus bas'],
}

# Order keywords
ORDER_KEYWORDS = {
    'ASC': ['croissant', 'ascendant', 'asc'],
    'DESC': ['décroissant', 'descendant', 'desc', 'plus', 'moins'],
}

# Pollution-specific patterns
POLLUTION_PATTERNS = {
    'avg_pm25': ['pollution', 'polluée', 'pollué', 'polluées', 'pollués', 'air'],
}
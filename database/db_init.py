"""
Database initialization and schema creation for Neo-Sousse 2030
Creates all tables with proper constraints and indexes
"""

import sqlite3
from db_utils import DB_PATH, get_connection, verify_schema

# Complete SQL schema with enhancements for anomaly detection
SCHEMA_SQL = """
-- ZONES (geographic areas)
CREATE TABLE IF NOT EXISTS zones (
    zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CAPTEURS (sensors with lifecycle states and anomaly tracking)
CREATE TABLE IF NOT EXISTS capteurs (
    capteur_id VARCHAR(20) PRIMARY KEY,
    zone_id INTEGER NOT NULL,
    type_capteur VARCHAR(20) NOT NULL CHECK(type_capteur IN ('air', 'bruit', 'trafic')),
    statut VARCHAR(20) NOT NULL DEFAULT 'inactif' 
        CHECK(statut IN ('inactif', 'actif', 'signale', 'en_maintenance', 'hors_service')),
    date_installation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    derniere_maintenance TIMESTAMP,
    taux_erreur REAL DEFAULT 0.0 CHECK(taux_erreur >= 0 AND taux_erreur <= 100),
    nb_anomalies_totales INTEGER DEFAULT 0,
    seuil_alerte REAL DEFAULT 15.0,
    FOREIGN KEY (zone_id) REFERENCES zones(zone_id)
);

-- MESURES (time-series measurements with anomaly flagging)
CREATE TABLE IF NOT EXISTS mesures (
    mesure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    capteur_id VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type_mesure VARCHAR(20) NOT NULL 
        CHECK(type_mesure IN ('PM2.5', 'PM10', 'CO2', 'NO2', 'temperature', 'humidite', 'bruit_db', 'debit_vehicules')),
    valeur REAL NOT NULL,
    unite VARCHAR(10) NOT NULL,
    est_anomalie BOOLEAN DEFAULT 0,
    FOREIGN KEY (capteur_id) REFERENCES capteurs(capteur_id)
);

-- Indexes for time-series performance
CREATE INDEX IF NOT EXISTS idx_mesures_timestamp ON mesures(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mesures_capteur_time ON mesures(capteur_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mesures_type ON mesures(type_mesure);
CREATE INDEX IF NOT EXISTS idx_mesures_anomalie ON mesures(est_anomalie) WHERE est_anomalie = 1;

-- CITOYENS (citizens)
CREATE TABLE IF NOT EXISTS citoyens (
    citoyen_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    zone_id INTEGER NOT NULL,
    score_ecologique INTEGER DEFAULT 50 CHECK(score_ecologique >= 0 AND score_ecologique <= 100),
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES zones(zone_id)
);

-- TECHNICIENS (technicians for interventions)
CREATE TABLE IF NOT EXISTS techniciens (
    technicien_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(100) NOT NULL,
    specialite VARCHAR(50),
    disponible BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VEHICULES (vehicles - owned or public)
CREATE TABLE IF NOT EXISTS vehicules (
    vehicule_id VARCHAR(20) PRIMARY KEY,
    citoyen_id INTEGER,
    type_vehicule VARCHAR(20) NOT NULL 
        CHECK(type_vehicule IN ('voiture_electrique', 'voiture_thermique', 'bus', 'tramway', 'velo')),
    statut VARCHAR(20) NOT NULL DEFAULT 'stationne'
        CHECK(statut IN ('stationne', 'en_route', 'en_panne', 'arrive')),
    zone_actuelle_id INTEGER,
    derniere_position TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citoyen_id) REFERENCES citoyens(citoyen_id),
    FOREIGN KEY (zone_actuelle_id) REFERENCES zones(zone_id)
);

-- TRAJETS (vehicle journeys with CO2 data)
CREATE TABLE IF NOT EXISTS trajets (
    trajet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicule_id VARCHAR(20) NOT NULL,
    zone_depart_id INTEGER NOT NULL,
    zone_arrivee_id INTEGER NOT NULL,
    timestamp_depart TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timestamp_arrivee TIMESTAMP,
    distance_km REAL CHECK(distance_km >= 0),
    economie_co2 REAL DEFAULT 0.0,
    statut VARCHAR(20) DEFAULT 'en_cours' 
        CHECK(statut IN ('en_cours', 'termine', 'annule')),
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(vehicule_id),
    FOREIGN KEY (zone_depart_id) REFERENCES zones(zone_id),
    FOREIGN KEY (zone_arrivee_id) REFERENCES zones(zone_id)
);

-- INTERVENTIONS (maintenance workflow)
CREATE TABLE IF NOT EXISTS interventions (
    intervention_id INTEGER PRIMARY KEY AUTOINCREMENT,
    capteur_id VARCHAR(20) NOT NULL,
    statut VARCHAR(30) NOT NULL DEFAULT 'demande'
        CHECK(statut IN ('demande', 'tech1_assigne', 'tech2_valide', 'ia_valide', 'termine')),
    date_demande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_terminaison TIMESTAMP,
    technicien1_id INTEGER,
    technicien2_id INTEGER,
    validation_ia BOOLEAN DEFAULT 0,
    description TEXT,
    FOREIGN KEY (capteur_id) REFERENCES capteurs(capteur_id),
    FOREIGN KEY (technicien1_id) REFERENCES techniciens(technicien_id),
    FOREIGN KEY (technicien2_id) REFERENCES techniciens(technicien_id)
);
"""


def initialize_database():
    """
    Create database and all tables with constraints.
    Safe to run multiple times (uses IF NOT EXISTS).
    """
    print("🔧 Initializing Neo-Sousse 2030 database...")
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Execute schema creation
            cursor.executescript(SCHEMA_SQL)
            
            print("✅ Database schema created successfully")
            
        # Verify schema
        if verify_schema():
            print("✅ Schema verification passed")
            return True
        else:
            print("❌ Schema verification failed")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = initialize_database()
    if success:
        print("\n🎉 Database ready for data generation!")
        print(f"📁 Location: {DB_PATH}")
    else:
        print("\n⚠️  Please check errors above")
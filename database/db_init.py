"""
PostgreSQL Database initialization
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'neo_sousse_2030')
DB_PORT = os.getenv('DB_PORT', '5432')

SCHEMA_SQL = """
-- ZONES (geographic areas)
CREATE TABLE IF NOT EXISTS zones (
    zone_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CAPTEURS (sensors)
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
    FOREIGN KEY (zone_id) REFERENCES zones(zone_id) ON DELETE CASCADE
);

-- MESURES (time-series measurements)
CREATE TABLE IF NOT EXISTS mesures (
    mesure_id SERIAL PRIMARY KEY,
    capteur_id VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type_mesure VARCHAR(20) NOT NULL 
        CHECK(type_mesure IN ('PM2.5', 'PM10', 'CO2', 'NO2', 'temperature', 'humidite', 'bruit_db', 'debit_vehicules')),
    valeur REAL NOT NULL,
    unite VARCHAR(10) NOT NULL,
    est_anomalie BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (capteur_id) REFERENCES capteurs(capteur_id) ON DELETE CASCADE
);

-- CITOYENS (citizens)
CREATE TABLE IF NOT EXISTS citoyens (
    citoyen_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    zone_id INTEGER NOT NULL,
    score_ecologique INTEGER DEFAULT 50 CHECK(score_ecologique >= 0 AND score_ecologique <= 100),
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES zones(zone_id) ON DELETE CASCADE
);

-- TECHNICIENS (technicians)
CREATE TABLE IF NOT EXISTS techniciens (
    technicien_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    specialite VARCHAR(50),
    disponible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VEHICULES (vehicles)
CREATE TABLE IF NOT EXISTS vehicules (
    vehicule_id VARCHAR(20) PRIMARY KEY,
    citoyen_id INTEGER,
    type_vehicule VARCHAR(20) NOT NULL CHECK(type_vehicule IN ('voiture_electrique', 'voiture_thermique', 'bus', 'tramway', 'velo')),
    statut VARCHAR(20) NOT NULL DEFAULT 'stationne'
        CHECK(statut IN ('stationne', 'en_route', 'en_panne', 'arrive')),
    zone_actuelle_id INTEGER,
    derniere_position TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citoyen_id) REFERENCES citoyens(citoyen_id) ON DELETE SET NULL,
    FOREIGN KEY (zone_actuelle_id) REFERENCES zones(zone_id) ON DELETE SET NULL
);

-- TRAJETS (vehicle journeys)
CREATE TABLE IF NOT EXISTS trajets (
    trajet_id SERIAL PRIMARY KEY,
    vehicule_id VARCHAR(20) NOT NULL,
    zone_depart_id INTEGER NOT NULL,
    zone_arrivee_id INTEGER,
    timestamp_depart TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timestamp_arrivee TIMESTAMP,
    distance_km REAL CHECK(distance_km >= 0),
    economie_co2 REAL DEFAULT 0.0,
    statut VARCHAR(20) DEFAULT 'en_cours' 
        CHECK(statut IN ('en_cours', 'termine', 'annule')),
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(vehicule_id) ON DELETE CASCADE,
    FOREIGN KEY (zone_depart_id) REFERENCES zones(zone_id) ON DELETE CASCADE,
    FOREIGN KEY (zone_arrivee_id) REFERENCES zones(zone_id) ON DELETE SET NULL
);

-- INTERVENTIONS (maintenance workflow)
CREATE TABLE IF NOT EXISTS interventions (
    intervention_id SERIAL PRIMARY KEY,
    capteur_id VARCHAR(20) NOT NULL,
    statut VARCHAR(30) NOT NULL DEFAULT 'demande'
        CHECK(statut IN ('demande', 'tech1_assigne', 'tech2_valide', 'ia_valide', 'termine')),
    date_demande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_terminaison TIMESTAMP,
    technicien1_id INTEGER,
    technicien2_id INTEGER,
    validation_ia BOOLEAN DEFAULT FALSE,
    description TEXT,
    FOREIGN KEY (capteur_id) REFERENCES capteurs(capteur_id) ON DELETE CASCADE,
    FOREIGN KEY (technicien1_id) REFERENCES techniciens(technicien_id) ON DELETE SET NULL,
    FOREIGN KEY (technicien2_id) REFERENCES techniciens(technicien_id) ON DELETE SET NULL
);

-- ALERTES (alerts)
CREATE TABLE IF NOT EXISTS alertes (
    alerte_id SERIAL PRIMARY KEY,
    capteur_id VARCHAR(20) NOT NULL,
    type_alerte VARCHAR(50) NOT NULL,
    severite VARCHAR(20) NOT NULL CHECK(severite IN ('info', 'warning', 'critical')),
    description TEXT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolution_date TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (capteur_id) REFERENCES capteurs(capteur_id) ON DELETE CASCADE
);

-- INDEXES for performance
CREATE INDEX IF NOT EXISTS idx_mesures_timestamp ON mesures(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mesures_capteur_time ON mesures(capteur_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mesures_type ON mesures(type_mesure);
CREATE INDEX IF NOT EXISTS idx_mesures_anomalie ON mesures(est_anomalie) WHERE est_anomalie = TRUE;
CREATE INDEX IF NOT EXISTS idx_capteurs_zone ON capteurs(zone_id);
CREATE INDEX IF NOT EXISTS idx_capteurs_statut ON capteurs(statut);
CREATE INDEX IF NOT EXISTS idx_interventions_capteur ON interventions(capteur_id);
CREATE INDEX IF NOT EXISTS idx_interventions_statut ON interventions(statut);
CREATE INDEX IF NOT EXISTS idx_alertes_capteur ON alertes(capteur_id);
"""

def init_database():
    """Initialize PostgreSQL database"""
    conn = None
    try:
        print(f"🔌 Connecting to PostgreSQL server at {DB_HOST}:{DB_PORT}...")
        
        # ✅ CHANGE: Connect to 'postgres' database first (default system DB)
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres',  # ✅ Use 'postgres' not neo_user
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL server")
        
        # Check if database exists
        print(f"🔍 Checking if database '{DB_NAME}' exists...")
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"📝 Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✅ Database '{DB_NAME}' created")
        else:
            print(f"✅ Database '{DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        
        # ✅ CHANGE: Now connect to the new database to create schema
        print(f"\n🔌 Connecting to database '{DB_NAME}'...")
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,  # ✅ Connect to the actual database
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print(f"✅ Connected to database '{DB_NAME}'")
        
        # Execute schema SQL
        print("\n📋 Creating schema...")
        cursor.execute(SCHEMA_SQL)
        print("✅ Database schema created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        if conn:
            conn.close()
        raise

if __name__ == "__main__":
    print("🚀 Initializing PostgreSQL database...")
    print(f"   Host: {DB_HOST}")
    print(f"   Port: {DB_PORT}")
    print(f"   User: {DB_USER}")
    print(f"   Database: {DB_NAME}")
    print()
    
    init_database()
    print("\n✅ Database initialization complete!")
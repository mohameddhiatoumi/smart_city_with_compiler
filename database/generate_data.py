"""
Generate realistic sample data for Neo-Sousse 2030
Creates zones, sensors, measurements, citizens, vehicles, etc.
UPDATED: PostgreSQL version
"""

import random
import psycopg2
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv
import os

load_dotenv()

# ✅ CHANGE 1: PostgreSQL configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'neo_sousse_2030')
DB_PORT = os.getenv('DB_PORT', '5432')

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

fake = Faker('fr_FR')
random.seed(42)

# Configuration
NUM_ZONES = 10
NUM_CAPTEURS = 60
NUM_MESURES_PER_CAPTEUR = 200
NUM_CITOYENS = 150
NUM_TECHNICIENS = 8
NUM_VEHICULES = 30
NUM_TRAJETS = 100
NUM_INTERVENTIONS = 15


def generate_zones():
    """Create 10 geographic zones"""
    zones = [
        ("Centre-ville", "Zone commerciale et administrative"),
        ("Zone Industrielle Nord", "Usines et entrepôts"),
        ("Corniche", "Front de mer et promenade"),
        ("Quartier Résidentiel Sud", "Habitations et écoles"),
        ("Zone Portuaire", "Port commercial et pêche"),
        ("Technopole", "Parc technologique et startups"),
        ("Médina", "Vieille ville historique"),
        ("Zone Universitaire", "Campus et résidences étudiantes"),
        ("Quartier des Affaires", "Tours de bureaux"),
        ("Périphérie Ouest", "Zone en développement")
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # ✅ CHANGE 2: Use %s instead of ? for PostgreSQL
    for nom, desc in zones:
        cursor.execute(
            "INSERT INTO zones (nom, description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (nom, desc)
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Created {len(zones)} zones")


def generate_capteurs():
    """Create sensors distributed across zones"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT zone_id FROM zones")
    zones = [row[0] for row in cursor.fetchall()]
    
    sensor_types = ['air', 'bruit', 'trafic']
    statuts = ['inactif', 'actif', 'actif', 'actif', 'actif', 'signale', 'en_maintenance']
    
    capteurs = []
    for i in range(1, NUM_CAPTEURS + 1):
        zone_id = random.choice(zones)
        type_capteur = random.choice(sensor_types)
        statut = random.choice(statuts)
        
        days_ago = random.randint(0, 730)
        date_install = datetime.now() - timedelta(days=days_ago)
        
        derniere_maint = None
        if random.random() < 0.3:
            derniere_maint = date_install + timedelta(days=random.randint(30, days_ago))
        
        taux_erreur = random.uniform(0, 5) if statut == 'actif' else random.uniform(10, 25)
        
        capteurs.append((
            f"C-{i:03d}",
            zone_id,
            type_capteur,
            statut,
            date_install,
            derniere_maint,
            round(taux_erreur, 2),
            int(taux_erreur * 10),
            15.0
        ))
    
    # ✅ CHANGE 2: Use %s instead of ?
    for capteur in capteurs:
        cursor.execute("""
            INSERT INTO capteurs (capteur_id, zone_id, type_capteur, statut, 
                                 date_installation, derniere_maintenance, taux_erreur,
                                 nb_anomalies_totales, seuil_alerte)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, capteur)
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Created {len(capteurs)} sensors")


def generate_mesures():
    """Generate realistic time-series measurements"""
    print("⏳ Generating measurements (this may take a moment)...")
    
    measure_config = {
        'PM2.5': {'base': 25, 'unit': 'µg/m³', 'range': 15, 'anomaly_range': 100},
        'PM10': {'base': 50, 'unit': 'µg/m³', 'range': 20, 'anomaly_range': 150},
        'CO2': {'base': 400, 'unit': 'ppm', 'range': 50, 'anomaly_range': 300},
        'NO2': {'base': 40, 'unit': 'µg/m³', 'range': 15, 'anomaly_range': 80},
        'temperature': {'base': 22, 'unit': '°C', 'range': 8, 'anomaly_range': 20},
        'humidite': {'base': 60, 'unit': '%', 'range': 20, 'anomaly_range': 40},
        'bruit_db': {'base': 55, 'unit': 'dB', 'range': 15, 'anomaly_range': 40},
        'debit_vehicules': {'base': 120, 'unit': 'veh/h', 'range': 80, 'anomaly_range': 300}
    }
    
    sensor_type_map = {
        'air': ['PM2.5', 'PM10', 'CO2', 'NO2', 'temperature', 'humidite'],
        'bruit': ['bruit_db', 'temperature'],
        'trafic': ['debit_vehicules']
    }
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT capteur_id, type_capteur FROM capteurs")
    capteurs = cursor.fetchall()
    
    mesures = []
    for capteur_id, type_capteur in capteurs:
        measure_types = sensor_type_map[type_capteur]
        
        for i in range(NUM_MESURES_PER_CAPTEUR):
            minutes_ago = i * 5
            timestamp = datetime.now() - timedelta(minutes=minutes_ago)
            
            type_mesure = random.choice(measure_types)
            config = measure_config[type_mesure]
            
            is_anomaly = random.random() < 0.01
            
            if is_anomaly:
                valeur = config['base'] + random.uniform(-config['anomaly_range'], config['anomaly_range'])
            else:
                valeur = config['base'] + random.uniform(-config['range'], config['range'])
            
            valeur = max(0, valeur)
            
            # ✅ CHANGE 2: Use %s and TRUE/FALSE for PostgreSQL
            cursor.execute("""
                INSERT INTO mesures (capteur_id, timestamp, type_mesure, valeur, unite, est_anomalie)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (capteur_id, timestamp, type_mesure, round(valeur, 2), config['unit'], is_anomaly))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    total = len(capteurs) * NUM_MESURES_PER_CAPTEUR
    print(f"✅ Created {total} measurements")


def generate_citoyens():
    """Generate citizens with ecological scores"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT zone_id FROM zones")
    zones = [row[0] for row in cursor.fetchall()]
    
    for _ in range(NUM_CITOYENS):
        nom = fake.name()
        email = fake.email()
        zone_id = random.choice(zones)
        score = random.randint(20, 95)
        date_inscription = datetime.now() - timedelta(days=random.randint(0, 365))
        
        # ✅ CHANGE 2: Use %s for PostgreSQL
        cursor.execute("""
            INSERT INTO citoyens (nom, email, zone_id, score_ecologique, date_inscription)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (nom, email, zone_id, score, date_inscription))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Created {NUM_CITOYENS} citizens")


def generate_techniciens():
    """Generate technicians"""
    specialites = [
        'Capteurs Air', 'Capteurs Bruit', 'Capteurs Trafic',
        'Électronique', 'Réseaux', 'Maintenance Générale'
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for i in range(NUM_TECHNICIENS):
        nom = fake.name()
        specialite = random.choice(specialites)
        disponible = random.choice([True, True, True, False])
        
        # ✅ CHANGE 2: Use %s and TRUE/FALSE for PostgreSQL
        cursor.execute("""
            INSERT INTO techniciens (nom, specialite, disponible)
            VALUES (%s, %s, %s)
        """, (nom, specialite, disponible))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Created {NUM_TECHNICIENS} technicians")


def generate_vehicules():
    """Generate vehicles (owned and public)"""
    types = ['voiture_electrique', 'voiture_thermique', 'bus', 'tramway', 'velo']
    statuts = ['stationne', 'en_route', 'stationne', 'stationne']
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT citoyen_id FROM citoyens LIMIT 20")
    citizen_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT zone_id FROM zones")
    zones = [row[0] for row in cursor.fetchall()]
    
    for i in range(1, NUM_VEHICULES + 1):
        if i <= 20:
            citoyen_id = citizen_ids[i - 1]
            type_veh = random.choice(['voiture_electrique', 'voiture_thermique', 'velo'])
        else:
            citoyen_id = None
            type_veh = random.choice(['bus', 'tramway'])
        
        statut = random.choice(statuts)
        zone_id = random.choice(zones)
        derniere_pos = datetime.now() - timedelta(minutes=random.randint(0, 1440))
        
        # ✅ CHANGE 2: Use %s for PostgreSQL
        cursor.execute("""
            INSERT INTO vehicules (vehicule_id, citoyen_id, type_vehicule, statut, 
                                  zone_actuelle_id, derniere_position)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (f"V-{i:04d}", citoyen_id, type_veh, statut, zone_id, derniere_pos))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Created {NUM_VEHICULES} vehicles")


def generate_trajets():
    """Generate vehicle journeys with CO2 calculations"""
    co2_per_km = {
        'voiture_electrique': 0,
        'voiture_thermique': 0.12,
        'bus': 0.08,
        'tramway': 0,
        'velo': 0
    }
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT vehicule_id, type_vehicule FROM vehicules")
    vehicules = cursor.fetchall()
    
    cursor.execute("SELECT zone_id FROM zones")
    zones = [row[0] for row in cursor.fetchall()]
    
    for _ in range(NUM_TRAJETS):
        vehicule_id, type_veh = random.choice(vehicules)
        zone_depart = random.choice(zones)
        zone_arrivee = random.choice([z for z in zones if z != zone_depart])
        
        distance = random.uniform(2, 25)
        
        baseline_co2 = distance * 0.12
        actual_co2 = distance * co2_per_km[type_veh]
        economie = baseline_co2 - actual_co2
        
        hours_ago = random.randint(0, 168)
        depart = datetime.now() - timedelta(hours=hours_ago)
        
        if random.random() < 0.8:
            arrivee = depart + timedelta(minutes=int(distance * 3))
            statut = 'termine'
        else:
            arrivee = None
            statut = 'en_cours'
        
        # ✅ CHANGE 2: Use %s for PostgreSQL
        cursor.execute("""
            INSERT INTO trajets (vehicule_id, zone_depart_id, zone_arrivee_id,
                                timestamp_depart, timestamp_arrivee, distance_km,
                                economie_co2, statut)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (vehicule_id, zone_depart, zone_arrivee, depart, arrivee,
              round(distance, 2), round(economie, 3), statut))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Created {NUM_TRAJETS} journeys")


def generate_interventions():
    """Generate maintenance interventions in various states"""
    statuts = ['demande', 'tech1_assigne', 'tech2_valide', 'ia_valide', 'termine']
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT capteur_id FROM capteurs 
        WHERE statut IN ('signale', 'en_maintenance') 
        LIMIT %s
    """, (NUM_INTERVENTIONS,))
    capteur_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT technicien_id FROM techniciens LIMIT 6")
    tech_ids = [row[0] for row in cursor.fetchall()]
    
    for capteur_id in capteur_ids:
        statut = random.choice(statuts)
        days_ago = random.randint(0, 30)
        date_demande = datetime.now() - timedelta(days=days_ago)
        
        tech1 = random.choice(tech_ids) if statut != 'demande' else None
        tech2 = random.choice(tech_ids) if statut in ['tech2_valide', 'ia_valide', 'termine'] else None
        ia_valid = statut in ['ia_valide', 'termine']
        date_fin = date_demande + timedelta(hours=random.randint(24, 72)) if statut == 'termine' else None
        
        # ✅ CHANGE 2: Use %s and TRUE/FALSE for PostgreSQL
        cursor.execute("""
            INSERT INTO interventions (capteur_id, statut, date_demande, date_terminaison,
                                      technicien1_id, technicien2_id, validation_ia, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (capteur_id, statut, date_demande, date_fin, tech1, tech2, ia_valid,
              "Maintenance suite à taux d'erreur élevé"))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Created {len(capteur_ids)} interventions")


def main():
    """Generate all sample data"""
    print("\n🌆 Generating Neo-Sousse 2030 sample data...\n")
    
    generate_zones()
    generate_capteurs()
    generate_mesures()
    generate_citoyens()
    generate_techniciens()
    generate_vehicules()
    generate_trajets()
    generate_interventions()
    
    # ✅ CHANGE 3: Use the updated function
    from db_utils import get_table_stats
    
    print("\n" + "="*50)
    get_table_stats()
    print("\n🎉 Data generation complete!")


if __name__ == "__main__":
    main()
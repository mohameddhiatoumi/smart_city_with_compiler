"""
Generate realistic sample data for Neo-Sousse 2030
Creates zones, sensors, measurements, citizens, vehicles, etc.
"""

import random
import sqlite3
from datetime import datetime, timedelta
from faker import Faker
from db_utils import get_connection, get_table_stats

fake = Faker('fr_FR')  # French locale for Tunisian names
random.seed(42)  # Reproducible data

# Configuration
NUM_ZONES = 10
NUM_CAPTEURS = 60
NUM_MESURES_PER_CAPTEUR = 200  # ~200 measurements each = 12,000 total
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
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO zones (nom, description) VALUES (?, ?)",
            zones
        )
    print(f"✅ Created {len(zones)} zones")


def generate_capteurs():
    """Create sensors distributed across zones"""
    capteurs = []
    sensor_types = {
        'air': ['PM2.5', 'PM10', 'CO2', 'NO2'],
        'bruit': ['bruit_db'],
        'trafic': ['debit_vehicules']
    }
    
    statuts = ['inactif', 'actif', 'actif', 'actif', 'actif', 'signale', 'en_maintenance']
    
    for i in range(1, NUM_CAPTEURS + 1):
        zone_id = random.randint(1, NUM_ZONES)
        type_capteur = random.choice(list(sensor_types.keys()))
        statut = random.choice(statuts)
        
        # Installation dates in last 2 years
        days_ago = random.randint(0, 730)
        date_install = datetime.now() - timedelta(days=days_ago)
        
        # Some sensors recently maintained
        derniere_maint = None
        if random.random() < 0.3:  # 30% have recent maintenance
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
            int(taux_erreur * 10),  # nb_anomalies_totales
            15.0  # seuil_alerte
        ))
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO capteurs (capteur_id, zone_id, type_capteur, statut, 
                                 date_installation, derniere_maintenance, taux_erreur,
                                 nb_anomalies_totales, seuil_alerte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, capteurs)
    
    print(f"✅ Created {len(capteurs)} sensors")


def generate_mesures():
    """Generate realistic time-series measurements"""
    print("⏳ Generating measurements (this may take a moment)...")
    
    # Measurement baselines and ranges
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
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all sensors
        cursor.execute("SELECT capteur_id, type_capteur FROM capteurs")
        capteurs = cursor.fetchall()
        
        mesures = []
        for capteur_id, type_capteur in capteurs:
            # Get measurement types for this sensor
            measure_types = sensor_type_map[type_capteur]
            
            # Generate measurements over last 7 days
            for i in range(NUM_MESURES_PER_CAPTEUR):
                minutes_ago = i * 5  # Every 5 minutes
                timestamp = datetime.now() - timedelta(minutes=minutes_ago)
                
                # Pick a random measurement type for this sensor
                type_mesure = random.choice(measure_types)
                config = measure_config[type_mesure]
                
                # 1% chance of anomaly (big change)
                is_anomaly = random.random() < 0.01
                
                if is_anomaly:
                    valeur = config['base'] + random.uniform(-config['anomaly_range'], config['anomaly_range'])
                else:
                    valeur = config['base'] + random.uniform(-config['range'], config['range'])
                
                # Ensure positive values
                valeur = max(0, valeur)
                
                mesures.append((
                    capteur_id,
                    timestamp,
                    type_mesure,
                    round(valeur, 2),
                    config['unit'],
                    1 if is_anomaly else 0
                ))
        
        # Batch insert for performance
        cursor.executemany("""
            INSERT INTO mesures (capteur_id, timestamp, type_mesure, valeur, unite, est_anomalie)
            VALUES (?, ?, ?, ?, ?, ?)
        """, mesures)
    
    print(f"✅ Created {len(mesures)} measurements")


def generate_citoyens():
    """Generate citizens with ecological scores"""
    citoyens = []
    
    for _ in range(NUM_CITOYENS):
        nom = fake.name()
        email = fake.email()
        zone_id = random.randint(1, NUM_ZONES)
        score = random.randint(20, 95)
        days_ago = random.randint(0, 365)
        date_inscription = datetime.now() - timedelta(days=days_ago)
        
        citoyens.append((nom, email, zone_id, score, date_inscription))
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO citoyens (nom, email, zone_id, score_ecologique, date_inscription)
            VALUES (?, ?, ?, ?, ?)
        """, citoyens)
    
    print(f"✅ Created {len(citoyens)} citizens")


def generate_techniciens():
    """Generate technicians"""
    specialites = [
        'Capteurs Air', 'Capteurs Bruit', 'Capteurs Trafic',
        'Électronique', 'Réseaux', 'Maintenance Générale'
    ]
    
    techniciens = []
    for i in range(NUM_TECHNICIENS):
        nom = fake.name()
        specialite = random.choice(specialites)
        disponible = random.choice([1, 1, 1, 0])  # 75% available
        
        techniciens.append((nom, specialite, disponible))
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO techniciens (nom, specialite, disponible)
            VALUES (?, ?, ?)
        """, techniciens)
    
    print(f"✅ Created {len(techniciens)} technicians")


def generate_vehicules():
    """Generate vehicles (owned and public)"""
    types = ['voiture_electrique', 'voiture_thermique', 'bus', 'tramway', 'velo']
    statuts = ['stationne', 'en_route', 'stationne', 'stationne']
    
    vehicules = []
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT citoyen_id FROM citoyens LIMIT 20")
        citizen_ids = [row[0] for row in cursor.fetchall()]
        
        for i in range(1, NUM_VEHICULES + 1):
            # 70% owned by citizens, 30% public transport
            if i <= 20:
                citoyen_id = citizen_ids[i - 1]
                type_veh = random.choice(['voiture_electrique', 'voiture_thermique', 'velo'])
            else:
                citoyen_id = None
                type_veh = random.choice(['bus', 'tramway'])
            
            statut = random.choice(statuts)
            zone_id = random.randint(1, NUM_ZONES)
            
            vehicules.append((
                f"V-{i:04d}",
                citoyen_id,
                type_veh,
                statut,
                zone_id,
                datetime.now() - timedelta(minutes=random.randint(0, 1440))
            ))
        
        cursor.executemany("""
            INSERT INTO vehicules (vehicule_id, citoyen_id, type_vehicule, statut, 
                                  zone_actuelle_id, derniere_position)
            VALUES (?, ?, ?, ?, ?, ?)
        """, vehicules)
    
    print(f"✅ Created {len(vehicules)} vehicles")


def generate_trajets():
    """Generate vehicle journeys with CO2 calculations"""
    co2_per_km = {
        'voiture_electrique': 0,
        'voiture_thermique': 0.12,  # kg CO2/km
        'bus': 0.08,
        'tramway': 0,
        'velo': 0
    }
    
    trajets = []
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vehicule_id, type_vehicule FROM vehicules")
        vehicules = cursor.fetchall()
        
        for _ in range(NUM_TRAJETS):
            vehicule_id, type_veh = random.choice(vehicules)
            zone_depart = random.randint(1, NUM_ZONES)
            zone_arrivee = random.randint(1, NUM_ZONES)
            
            # Avoid same zone
            while zone_arrivee == zone_depart:
                zone_arrivee = random.randint(1, NUM_ZONES)
            
            distance = random.uniform(2, 25)  # km
            
            # CO2 saved vs. baseline thermal car
            baseline_co2 = distance * 0.12
            actual_co2 = distance * co2_per_km[type_veh]
            economie = baseline_co2 - actual_co2
            
            hours_ago = random.randint(0, 168)  # Last week
            depart = datetime.now() - timedelta(hours=hours_ago)
            
            # 80% completed
            if random.random() < 0.8:
                arrivee = depart + timedelta(minutes=int(distance * 3))
                statut = 'termine'
            else:
                arrivee = None
                statut = 'en_cours'
            
            trajets.append((
                vehicule_id, zone_depart, zone_arrivee, depart, arrivee,
                round(distance, 2), round(economie, 3), statut
            ))
        
        cursor.executemany("""
            INSERT INTO trajets (vehicule_id, zone_depart_id, zone_arrivee_id,
                                timestamp_depart, timestamp_arrivee, distance_km,
                                economie_co2, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, trajets)
    
    print(f"✅ Created {len(trajets)} journeys")


def generate_interventions():
    """Generate maintenance interventions in various states"""
    statuts = ['demande', 'tech1_assigne', 'tech2_valide', 'ia_valide', 'termine']
    
    interventions = []
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get sensors with issues
        cursor.execute("""
            SELECT capteur_id FROM capteurs 
            WHERE statut IN ('signale', 'en_maintenance') 
            LIMIT ?
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
            ia_valid = 1 if statut in ['ia_valide', 'termine'] else 0
            date_fin = date_demande + timedelta(hours=random.randint(24, 72)) if statut == 'termine' else None
            
            interventions.append((
                capteur_id, statut, date_demande, date_fin,
                tech1, tech2, ia_valid,
                f"Maintenance suite à taux d'erreur élevé"
            ))
        
        cursor.executemany("""
            INSERT INTO interventions (capteur_id, statut, date_demande, date_terminaison,
                                      technicien1_id, technicien2_id, validation_ia, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, interventions)
    
    print(f"✅ Created {len(interventions)} interventions")


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
    
    print("\n" + "="*50)
    get_table_stats()
    print("\n🎉 Data generation complete!")


if __name__ == "__main__":
    main()
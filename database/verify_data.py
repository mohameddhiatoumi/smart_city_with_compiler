"""
Verify database integrity and test sample queries
"""

from db_utils import execute_query, get_table_stats

def run_verification_queries():
    """Run test queries from the project PDF"""
    
    print("\n🔍 Running verification queries...\n")
    
    # Query 1: Top 5 most polluted zones
    print("1️⃣  Top 5 most polluted zones:")
    results = execute_query("""
        SELECT z.nom AS zone, AVG(m.valeur) AS pollution_moyenne
        FROM mesures m
        JOIN capteurs c ON m.capteur_id = c.capteur_id
        JOIN zones z ON c.zone_id = z.zone_id
        WHERE m.type_mesure = 'PM2.5'
        GROUP BY z.zone_id, z.nom
        ORDER BY pollution_moyenne DESC
        LIMIT 5
    """)
    for row in results:
        print(f"   {row['zone']:30} : {row['pollution_moyenne']:.2f} µg/m³")
    
    # Query 2: Sensors out of service
    print("\n2️⃣  Sensors out of service:")
    results = execute_query("""
        SELECT COUNT(*) as count FROM capteurs WHERE statut = 'hors_service'
    """)
    print(f"   Total: {results[0]['count']}")
    
    # Query 3: Citizens with ecological score > 80
    print("\n3️⃣  Citizens with ecological score > 80:")
    results = execute_query("""
        SELECT nom, score_ecologique 
        FROM citoyens 
        WHERE score_ecologique > 80 
        ORDER BY score_ecologique DESC
        LIMIT 10
    """)
    for row in results:
        print(f"   {row['nom']:30} : {row['score_ecologique']}")
    
    # Query 4: Most economical journey in CO2
    print("\n4️⃣  Most CO2-economical journey:")
    results = execute_query("""
        SELECT t.trajet_id, v.type_vehicule, t.economie_co2,
               zd.nom AS depart, za.nom AS arrivee
        FROM trajets t
        JOIN vehicules v ON t.vehicule_id = v.vehicule_id
        JOIN zones zd ON t.zone_depart_id = zd.zone_id
        JOIN zones za ON t.zone_arrivee_id = za.zone_id
        WHERE t.statut = 'termine'
        ORDER BY t.economie_co2 DESC
        LIMIT 1
    """)
    if results:
        row = results[0]
        print(f"   Journey #{row['trajet_id']}: {row['depart']} → {row['arrivee']}")
        print(f"   Vehicle: {row['type_vehicule']}")
        print(f"   CO2 saved: {row['economie_co2']:.3f} kg")
    
    # Additional: Anomaly detection
    print("\n5️⃣  Recent anomalies detected:")
    results = execute_query("""
        SELECT c.capteur_id, c.type_capteur, COUNT(*) as nb_anomalies,
               c.taux_erreur, c.statut
        FROM mesures m
        JOIN capteurs c ON m.capteur_id = c.capteur_id
        WHERE m.est_anomalie = 1
        GROUP BY c.capteur_id
        ORDER BY nb_anomalies DESC
        LIMIT 5
    """)
    for row in results:
        print(f"   {row['capteur_id']} ({row['type_capteur']}): {row['nb_anomalies']} anomalies, " +
              f"error rate: {row['taux_erreur']:.1f}%, status: {row['statut']}")
    
    print("\n✅ Verification complete!\n")


if __name__ == "__main__":
    get_table_stats()
    run_verification_queries()
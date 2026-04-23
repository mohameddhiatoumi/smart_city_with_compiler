"""
Generate sample trajectory data for traffic analysis
Populates the trajets table with realistic vehicle journey data
UPDATED: PostgreSQL version
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ✅ CHANGE 1: Use PostgreSQL instead of SQLite
import psycopg2
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

load_dotenv()

# ✅ CHANGE 2: PostgreSQL configuration
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

def generate_trajectories():
    """Generate sample trajectory data for the last 7 days"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🚗 GENERATING TRAJECTORY DATA")
    print("=" * 60)
    
    # Get existing vehicles
    cursor.execute("SELECT vehicule_id FROM vehicules")
    vehicles = [row[0] for row in cursor.fetchall()]
    
    # Get existing zones
    cursor.execute("SELECT zone_id FROM zones")
    zones = [row[0] for row in cursor.fetchall()]
    
    if not vehicles:
        print("❌ No vehicles found! Run db_init.py first")
        cursor.close()
        conn.close()
        return False
    
    if not zones:
        print("❌ No zones found! Run db_init.py first")
        cursor.close()
        conn.close()
        return False
    
    print(f"\n📊 Found {len(vehicles)} vehicles and {len(zones)} zones\n")
    
    # Generate trajectories for last 7 days
    base_date = datetime.now() - timedelta(days=7)
    
    print("📝 Generating trajectories for last 7 days...")
    
    count = 0
    for day in range(7):
        date = base_date + timedelta(days=day)
        
        for vehicle in vehicles:
            num_trips = random.randint(3, 4)
            
            for trip in range(num_trips):
                hour = random.randint(6, 22)
                minute = random.randint(0, 59)
                
                start_zone = random.choice(zones)
                end_zone = random.choice([z for z in zones if z != start_zone])
                
                distance = random.uniform(5, 50)
                co2_saved = distance * random.uniform(0.1, 0.3)
                
                timestamp_start = date.replace(hour=hour, minute=minute)
                trip_duration = timedelta(minutes=int(30 + distance / 25 * 30))
                timestamp_end = timestamp_start + trip_duration
                
                # ✅ CHANGE 3: Use %s instead of ? for PostgreSQL
                cursor.execute("""
                    INSERT INTO trajets 
                    (vehicule_id, zone_depart_id, zone_arrivee_id, timestamp_depart, 
                     timestamp_arrivee, distance_km, economie_co2, statut)
                    VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (vehicle, start_zone, end_zone, timestamp_start,
                      timestamp_end, round(distance, 2), round(co2_saved, 2), 'termine'))
                
                count += 1
    
    # Batch commit
    try:
        conn.commit()
        
        print(f"✅ Generated {count} trajectories")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM trajets")
        total_count = cursor.fetchone()[0]
        print(f"✅ Total trajectories in database: {total_count}")
        
        # Show sample data
        cursor.execute("""
            SELECT 
                v.vehicule_id,
                z1.nom as zone_depart,
                z2.nom as zone_arrivee,
                t.distance_km,
                t.economie_co2,
                t.timestamp_depart
            FROM trajets t
            JOIN vehicules v ON t.vehicule_id = v.vehicule_id
            JOIN zones z1 ON t.zone_depart_id = z1.zone_id
            JOIN zones z2 ON t.zone_arrivee_id = z2.zone_id
            LIMIT 5
        """)
        
        print("\n📋 Sample trajectories:")
        print("-" * 80)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} → {row[2]}")
            print(f"    Distance: {row[3]} km | CO2 saved: {row[4]} kg")
            print(f"    Date: {row[5]}")
            print()
        
        print("=" * 60)
        print("✅ Trajectory generation complete!")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inserting trajectories: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


if __name__ == "__main__":
    success = generate_trajectories()
    sys.exit(0 if success else 1)
"""
Generate sample trajectory data for traffic analysis
Populates the trajets table with realistic vehicle journey data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "neo_sousse.db"

def generate_trajectories():
    """Generate sample trajectory data for the last 7 days"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🚗 GENERATING TRAJECTORY DATA")
    print("=" * 60)
    
    # Get existing vehicles
    cursor.execute("SELECT vehicule_id FROM vehicules")
    vehicles = [row['vehicule_id'] for row in cursor.fetchall()]
    
    # Get existing zones
    cursor.execute("SELECT zone_id FROM zones")
    zones = [row['zone_id'] for row in cursor.fetchall()]
    
    if not vehicles:
        print("❌ No vehicles found! Run db_init.py first")
        conn.close()
        return False
    
    if not zones:
        print("❌ No zones found! Run db_init.py first")
        conn.close()
        return False
    
    print(f"\n📊 Found {len(vehicles)} vehicles and {len(zones)} zones\n")
    
    # Generate trajectories for last 7 days
    trajectories = []
    base_date = datetime.now() - timedelta(days=7)
    
    print("📝 Generating trajectories for last 7 days...")
    
    for day in range(7):
        date = base_date + timedelta(days=day)
        
        # Generate 3-4 trips per vehicle per day
        for vehicle in vehicles:
            num_trips = random.randint(3, 4)
            
            for trip in range(num_trips):
                # Random start time during the day
                hour = random.randint(6, 22)  # 6 AM to 10 PM
                minute = random.randint(0, 59)
                
                start_zone = random.choice(zones)
                end_zone = random.choice([z for z in zones if z != start_zone])
                
                # Generate realistic distance (5-50 km)
                distance = random.uniform(5, 50)
                
                # CO2 savings (varies by vehicle type and distance)
                co2_saved = distance * random.uniform(0.1, 0.3)
                
                timestamp_start = date.replace(hour=hour, minute=minute)
                # Trip duration: 30 min to 2 hours depending on distance
                trip_duration = timedelta(minutes=int(30 + distance / 25 * 30))
                timestamp_end = timestamp_start + trip_duration
                
                trajectories.append({
                    'vehicule_id': vehicle,
                    'zone_depart_id': start_zone,
                    'zone_arrivee_id': end_zone,
                    'timestamp_depart': timestamp_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp_arrivee': timestamp_end.strftime('%Y-%m-%d %H:%M:%S'),
                    'distance_km': round(distance, 2),
                    'economie_co2': round(co2_saved, 2),
                    'statut': 'termine'
                })
    
    # Insert trajectories
    try:
        cursor.executemany("""
            INSERT INTO trajets 
            (vehicule_id, zone_depart_id, zone_arrivee_id, timestamp_depart, 
             timestamp_arrivee, distance_km, economie_co2, statut)
            VALUES 
            (:vehicule_id, :zone_depart_id, :zone_arrivee_id, :timestamp_depart,
             :timestamp_arrivee, :distance_km, :economie_co2, :statut)
        """, trajectories)
        
        conn.commit()
        
        print(f"✅ Generated {len(trajectories)} trajectories")
        
        # Verify
        cursor.execute("SELECT COUNT(*) as count FROM trajets")
        count = cursor.fetchone()['count']
        print(f"✅ Total trajectories in database: {count}")
        
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
            print(f"  {row['vehicule_id']}: {row['zone_depart']} → {row['zone_arrivee']}")
            print(f"    Distance: {row['distance_km']} km | CO2 saved: {row['economie_co2']} kg")
            print(f"    Date: {row['timestamp_depart']}")
            print()
        
        print("=" * 60)
        print("✅ Trajectory generation complete!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error inserting trajectories: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = generate_trajectories()
    sys.exit(0 if success else 1)
"""
Real-time sensor simulator for Neo-Sousse 2030
Continuously generates realistic measurements with anomaly detection
UPDATED: PostgreSQL version
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import signal
from datetime import datetime
from threading import Thread, Event
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ✅ CHANGE 1: Use PostgreSQL config
import psycopg2
from dotenv import load_dotenv

load_dotenv()

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

from simulator_config import (
    MEASUREMENT_INTERVAL_SECONDS, SIMULATION_SPEED_MULTIPLIER,
    SENSOR_MEASUREMENTS, MEASUREMENT_UNITS, ERROR_RATE_THRESHOLD,
    AUTO_CREATE_INTERVENTIONS, LOG_LEVEL, LOG_FILE, CONSOLE_OUTPUT
)
from simulator_utils import (
    generate_next_value, get_initial_value, calculate_error_rate,
    should_trigger_intervention
)
from simulator_logger import (
    setup_logger, log_measurement, log_sensor_status_change,
    log_intervention_created, log_simulation_start, log_simulation_stop
)


class SensorSimulator:
    """Main sensor simulator class"""
    
    def __init__(self):
        self.logger = setup_logger(LOG_FILE, LOG_LEVEL, CONSOLE_OUTPUT)
        self.stop_event = Event()
        self.active_sensors = {}
        self.recovery_counters = {}
        self.stats = {
            'total_measurements': 0,
            'total_anomalies': 0,
            'interventions_created': 0
        }
        self.RECOVERY_THRESHOLD = 10
        
    def load_active_sensors(self):
        """Load all active sensors from database"""
        conn = None
        try:
            # ✅ CHANGE 2: Use PostgreSQL connection
            conn = get_connection()
            cursor = conn.cursor()
            
            # ✅ CHANGE 3: Use %s instead of ?
            cursor.execute("""
                SELECT capteur_id, type_capteur, statut
                FROM capteurs
                WHERE statut IN ('actif', 'signale')
            """)
            
            sensors = cursor.fetchall()
            
            for sensor in sensors:
                # ✅ CHANGE 4: Access by index (PostgreSQL returns tuples)
                sensor_id = sensor[0]  # capteur_id
                sensor_type = sensor[1]  # type_capteur
                
                # Initialize recovery counter
                self.recovery_counters[sensor_id] = 0
                
                # Initialize last values for each measurement type
                last_values = {}
                measure_types = SENSOR_MEASUREMENTS[sensor_type]
                
                for measure_type in measure_types:
                    # ✅ CHANGE 3: Use %s instead of ?
                    cursor.execute("""
                        SELECT valeur FROM mesures
                        WHERE capteur_id = %s AND type_mesure = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (sensor_id, measure_type))
                    
                    result = cursor.fetchone()
                    if result:
                        last_values[measure_type] = result[0]  # ✅ CHANGE 4: Access by index
                    else:
                        last_values[measure_type] = get_initial_value(measure_type)
                
                self.active_sensors[sensor_id] = {
                    'type': sensor_type,
                    'last_values': last_values
                }
            
            cursor.close()
        except Exception as e:
            self.logger.error(f"Error loading sensors: {e}")
        finally:
            if conn:
                conn.close()
        
        self.logger.info(f"Loaded {len(self.active_sensors)} active sensors")
    
    def generate_measurement(self, sensor_id):
        """Generate measurements for a single sensor"""
        sensor_data = self.active_sensors[sensor_id]
        sensor_type = sensor_data['type']
        measure_types = SENSOR_MEASUREMENTS[sensor_type]
        
        measurements = []
        
        for measure_type in measure_types:
            last_value = sensor_data['last_values'][measure_type]
            new_value, is_anomaly = generate_next_value(sensor_id, measure_type, last_value)
            
            # Update last value
            sensor_data['last_values'][measure_type] = new_value
            
            # Log measurement
            log_measurement(self.logger, sensor_id, measure_type, new_value, is_anomaly)
            
            measurements.append({
                'capteur_id': sensor_id,
                'type_mesure': measure_type,
                'valeur': new_value,
                'unite': MEASUREMENT_UNITS[measure_type],
                'est_anomalie': is_anomaly  # ✅ CHANGE 5: PostgreSQL uses TRUE/FALSE not 0/1
            })
            
            # Update stats
            self.stats['total_measurements'] += 1
            if is_anomaly:
                self.stats['total_anomalies'] += 1
        
        return measurements
    
    def save_measurements(self, measurements):
        """Batch save measurements to database"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add timestamp to each measurement
        for measurement in measurements:
            measurement['timestamp'] = current_time
        
        conn = None
        try:
            # ✅ CHANGE 2: Use PostgreSQL
            conn = get_connection()
            cursor = conn.cursor()
            
            # ✅ CHANGE 3 & 6: Use %s instead of :name and convert to tuples
            for measurement in measurements:
                cursor.execute("""
                    INSERT INTO mesures (capteur_id, timestamp, type_mesure, valeur, unite, est_anomalie)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    measurement['capteur_id'],
                    measurement['timestamp'],
                    measurement['type_mesure'],
                    measurement['valeur'],
                    measurement['unite'],
                    measurement['est_anomalie']
                ))
            
            conn.commit()
            cursor.close()
        except Exception as e:
            self.logger.error(f"Error saving measurements: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def update_sensor_statistics(self):
        """Update sensor statistics for all active sensors and check for status changes"""
        conn = None
        try:
            # ✅ CHANGE 2: Use PostgreSQL
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get all active/signaled sensors
            cursor.execute("""
                SELECT capteur_id FROM capteurs 
                WHERE statut IN ('actif', 'signale')
            """)
            
            sensor_ids = [row[0] for row in cursor.fetchall()]  # ✅ CHANGE 4: Access by index
            
            for sensor_id in sensor_ids:
                # Get measurements from last 24 hours
                # ✅ CHANGE 3: Use %s and INTERVAL for PostgreSQL
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN est_anomalie = TRUE THEN 1 ELSE 0 END) as anomalies
                    FROM mesures
                    WHERE capteur_id = %s 
                    AND timestamp >= NOW() - INTERVAL '24 hours'
                """, (sensor_id,))
                
                result = cursor.fetchone()
                total = result[0]
                anomalies = result[1] or 0
                
                error_rate = calculate_error_rate(total, anomalies)
                
                # Update sensor statistics
                # ✅ CHANGE 3: Use %s instead of ?
                cursor.execute("""
                    UPDATE capteurs
                    SET taux_erreur = %s,
                        nb_anomalies_totales = %s
                    WHERE capteur_id = %s
                """, (error_rate, anomalies, sensor_id))
                
                # Get current status
                cursor.execute("""
                    SELECT statut FROM capteurs WHERE capteur_id = %s
                """, (sensor_id,))
                
                current_status_row = cursor.fetchone()
                current_status = current_status_row[0]  # ✅ CHANGE 4: Access by index
                
                # ===== INSTANT FLAG: If error rate exceeds threshold =====
                if error_rate >= ERROR_RATE_THRESHOLD:
                    if current_status == 'actif':
                        cursor.execute("""
                            UPDATE capteurs
                            SET statut = %s
                            WHERE capteur_id = %s
                        """, ('signale', sensor_id))
                        
                        log_sensor_status_change(
                            self.logger, sensor_id, 'actif', 'signale', error_rate
                        )
                        
                        # Reset recovery counter on flagging
                        self.recovery_counters[sensor_id] = 0
                        
                        # Create intervention if enabled
                        if AUTO_CREATE_INTERVENTIONS:
                            # Check if intervention already exists
                            cursor.execute("""
                                SELECT COUNT(*) as count FROM interventions
                                WHERE capteur_id = %s AND statut != 'termine'
                            """, (sensor_id,))
                            
                            count = cursor.fetchone()[0]  # ✅ CHANGE 4: Access by index
                            if count == 0:
                                # Create new intervention
                                description = f"Auto-generated: Error rate {error_rate:.2f}% exceeds threshold"
                                cursor.execute("""
                                    INSERT INTO interventions (capteur_id, statut, description)
                                    VALUES (%s, %s, %s)
                                    RETURNING intervention_id
                                """, (sensor_id, 'demande', description))
                                
                                intervention_id = cursor.fetchone()[0]  # ✅ CHANGE 4 & 7: Use RETURNING
                                self.stats['interventions_created'] += 1
                                log_intervention_created(self.logger, sensor_id, intervention_id)
                
                # ===== RECOVERY WITH COUNTER: If error rate is good =====
                elif error_rate < 5.0:
                    if current_status == 'signale':
                        # Increment recovery counter
                        self.recovery_counters[sensor_id] += 1
                        
                        # Only recover after 10 consecutive normal cycles
                        if self.recovery_counters[sensor_id] >= self.RECOVERY_THRESHOLD:
                            cursor.execute("""
                                UPDATE capteurs
                                SET statut = %s
                                WHERE capteur_id = %s
                            """, ('actif', sensor_id))
                            
                            log_sensor_status_change(
                                self.logger, sensor_id, 'signale', 'actif', error_rate
                            )
                            
                            # Reset counter after recovery
                            self.recovery_counters[sensor_id] = 0
                        else:
                            # Log recovery progress
                            self.logger.info(
                                f"RECOVERY: {sensor_id} | Good readings: {self.recovery_counters[sensor_id]}/{self.RECOVERY_THRESHOLD} | Error: {error_rate:.2f}%"
                            )
                    else:
                        # Reset counter if sensor is actif and doing well
                        self.recovery_counters[sensor_id] = 0
                
                # ===== RESET COUNTER: If error rate is between 5-15% (ambiguous) =====
                else:
                    # In the middle zone - don't change status but reset recovery counter
                    if current_status == 'signale':
                        # If we get an ambiguous reading while in signale, reset the counter
                        self.recovery_counters[sensor_id] = 0
                        self.logger.debug(f"RESET RECOVERY: {sensor_id} | Ambiguous reading detected, recovery counter reset | Error: {error_rate:.2f}%")
            
            conn.commit()
            cursor.close()
        
        except Exception as e:
            self.logger.error(f"Error updating sensor statistics: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def simulation_cycle(self):
        """Single simulation cycle - generate measurements for all sensors"""
        all_measurements = []
        
        for sensor_id in self.active_sensors.keys():
            measurements = self.generate_measurement(sensor_id)
            all_measurements.extend(measurements)
        
        # Save all measurements in batch
        if all_measurements:
            self.save_measurements(all_measurements)
        
        # Update sensor statistics after EVERY cycle
        self.update_sensor_statistics()
    
    def run(self):
        """Main simulation loop"""
        self.load_active_sensors()
        
        if not self.active_sensors:
            self.logger.error("No active sensors found. Please check your database.")
            return
        
        log_simulation_start(
            self.logger,
            len(self.active_sensors),
            MEASUREMENT_INTERVAL_SECONDS
        )
        
        interval = MEASUREMENT_INTERVAL_SECONDS / SIMULATION_SPEED_MULTIPLIER
        
        try:
            while not self.stop_event.is_set():
                cycle_start = time.time()
                
                self.simulation_cycle()
                
                # Sleep for remaining interval time
                elapsed = time.time() - cycle_start
                sleep_time = max(0, interval - elapsed)
                
                if self.stop_event.wait(sleep_time):
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Simulator error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
    
    def stop(self):
        """Stop the simulator gracefully"""
        self.stop_event.set()
        log_simulation_stop(
            self.logger,
            self.stats['total_measurements'],
            self.stats['total_anomalies']
        )


def signal_handler(sig, frame):
    """Handle CTRL+C gracefully"""
    print("\nStopping simulator...")
    simulator.stop()
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handler for graceful shutdown
    simulator = SensorSimulator()
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n" + "="*60)
    print("NEO-SOUSSE 2030 - SENSOR SIMULATOR")
    print("="*60)
    print("Press CTRL+C to stop the simulator")
    print("="*60 + "\n")
    
    simulator.run()
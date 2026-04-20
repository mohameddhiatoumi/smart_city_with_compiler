"""
Real-time sensor simulator for Neo-Sousse 2030
Continuously generates realistic measurements with anomaly detection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import signal
from datetime import datetime
from threading import Thread, Event
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import get_connection
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
        self.active_sensors = {}  # {sensor_id: {type, last_values: {measure_type: value}}}
        self.recovery_counters = {}  # {sensor_id: consecutive_normal_readings}
        self.stats = {
            'total_measurements': 0,
            'total_anomalies': 0,
            'interventions_created': 0
        }
        self.RECOVERY_THRESHOLD = 10  # 10 consecutive normal cycles to recover
        
    def load_active_sensors(self):
        """Load all active sensors from database"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT capteur_id, type_capteur, statut
                FROM capteurs
                WHERE statut IN ('actif', 'signale')
            """)
            
            sensors = cursor.fetchall()
            
            for sensor in sensors:
                sensor_id = sensor['capteur_id']
                sensor_type = sensor['type_capteur']
                
                # Initialize recovery counter
                self.recovery_counters[sensor_id] = 0
                
                # Initialize last values for each measurement type
                last_values = {}
                measure_types = SENSOR_MEASUREMENTS[sensor_type]
                
                for measure_type in measure_types:
                    # Try to get last value from database
                    cursor.execute("""
                        SELECT valeur FROM mesures
                        WHERE capteur_id = ? AND type_mesure = ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (sensor_id, measure_type))
                    
                    result = cursor.fetchone()
                    if result:
                        last_values[measure_type] = result['valeur']
                    else:
                        last_values[measure_type] = get_initial_value(measure_type)
                
                self.active_sensors[sensor_id] = {
                    'type': sensor_type,
                    'last_values': last_values
                }
        
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
                'est_anomalie': 1 if is_anomaly else 0
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
        
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT INTO mesures (capteur_id, timestamp, type_mesure, valeur, unite, est_anomalie)
                    VALUES (:capteur_id, :timestamp, :type_mesure, :valeur, :unite, :est_anomalie)
                """, measurements)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error saving measurements: {e}")
    
    def update_sensor_statistics(self):
        """Update sensor statistics for all active sensors and check for status changes"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all active/signaled sensors
                cursor.execute("""
                    SELECT capteur_id FROM capteurs 
                    WHERE statut IN ('actif', 'signale')
                """)
                
                sensor_ids = [row['capteur_id'] for row in cursor.fetchall()]
                
                for sensor_id in sensor_ids:
                    # Get measurements from last 24 hours
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(est_anomalie) as anomalies
                        FROM mesures
                        WHERE capteur_id = ? 
                        AND timestamp >= datetime('now', '-24 hours')
                    """, (sensor_id,))
                    
                    result = cursor.fetchone()
                    total = result['total']
                    anomalies = result['anomalies'] or 0
                    
                    error_rate = calculate_error_rate(total, anomalies)
                    
                    # Update sensor statistics
                    cursor.execute("""
                        UPDATE capteurs
                        SET taux_erreur = ?,
                            nb_anomalies_totales = ?
                        WHERE capteur_id = ?
                    """, (error_rate, anomalies, sensor_id))
                    
                    # Get current status
                    cursor.execute("""
                        SELECT statut FROM capteurs WHERE capteur_id = ?
                    """, (sensor_id,))
                    current_status = cursor.fetchone()['statut']
                    
                    # ===== INSTANT FLAG: If error rate exceeds threshold =====
                    if error_rate >= ERROR_RATE_THRESHOLD:
                        if current_status == 'actif':
                            cursor.execute("""
                                UPDATE capteurs
                                SET statut = 'signale'
                                WHERE capteur_id = ?
                            """, (sensor_id,))
                            
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
                                    WHERE capteur_id = ? AND statut != 'termine'
                                """, (sensor_id,))
                                
                                if cursor.fetchone()['count'] == 0:
                                    # Create new intervention
                                    description = f"Auto-generated: Error rate {error_rate:.2f}% exceeds threshold"
                                    cursor.execute("""
                                        INSERT INTO interventions (capteur_id, statut, description)
                                        VALUES (?, 'demande', ?)
                                    """, (sensor_id, description))
                                    
                                    self.stats['interventions_created'] += 1
                                    log_intervention_created(self.logger, sensor_id, cursor.lastrowid)
                    
                    # ===== RECOVERY WITH COUNTER: If error rate is good =====
                    elif error_rate < 5.0:
                        if current_status == 'signale':
                            # Increment recovery counter
                            self.recovery_counters[sensor_id] += 1
                            
                            # Only recover after 10 consecutive normal cycles
                            if self.recovery_counters[sensor_id] >= self.RECOVERY_THRESHOLD:
                                cursor.execute("""
                                    UPDATE capteurs
                                    SET statut = 'actif'
                                    WHERE capteur_id = ?
                                """, (sensor_id,))
                                
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
        
        except Exception as e:
            self.logger.error(f"Error updating sensor statistics: {e}")
    
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
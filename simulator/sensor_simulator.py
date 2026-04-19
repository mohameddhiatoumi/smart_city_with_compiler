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
from compiler import NLQueryCompiler
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
        self.stats = {
            'total_measurements': 0,
            'total_anomalies': 0,
            'interventions_created': 0
        }
        
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
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO mesures (capteur_id, type_mesure, valeur, unite, est_anomalie)
                VALUES (:capteur_id, :type_mesure, :valeur, :unite, :est_anomalie)
            """, measurements)
    
    def update_sensor_statistics(self, sensor_id):
        """Update sensor error rate and check for status changes"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total measurements and anomalies for this sensor
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(est_anomalie) as anomalies
                FROM mesures
                WHERE capteur_id = ?
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
            
            # Check if status should change
            cursor.execute("""
                SELECT statut FROM capteurs WHERE capteur_id = ?
            """, (sensor_id,))
            current_status = cursor.fetchone()['statut']
            
            # Trigger status change if error rate exceeds threshold
            if should_trigger_intervention(error_rate, ERROR_RATE_THRESHOLD):
                if current_status == 'actif':
                    cursor.execute("""
                        UPDATE capteurs
                        SET statut = 'signale'
                        WHERE capteur_id = ?
                    """, (sensor_id,))
                    
                    log_sensor_status_change(
                        self.logger, sensor_id, 'actif', 'signale', error_rate
                    )
                    
                    # Create intervention if enabled
                    if AUTO_CREATE_INTERVENTIONS:
                        self.create_intervention(sensor_id, error_rate)
    
    def create_intervention(self, sensor_id, error_rate):
        """Automatically create intervention for faulty sensor"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if intervention already exists for this sensor
            cursor.execute("""
                SELECT COUNT(*) as count FROM interventions
                WHERE capteur_id = ? AND statut != 'termine'
            """, (sensor_id,))
            
            if cursor.fetchone()['count'] > 0:
                return  # Already has open intervention
            
            # Create new intervention
            description = f"Auto-generated: Error rate {error_rate:.2f}% exceeds threshold"
            cursor.execute("""
                INSERT INTO interventions (capteur_id, statut, description)
                VALUES (?, 'demande', ?)
            """, (sensor_id, description))
            
            intervention_id = cursor.lastrowid
            self.stats['interventions_created'] += 1
            
            log_intervention_created(self.logger, sensor_id, intervention_id)
    
    def simulation_cycle(self):
        """Single simulation cycle - generate measurements for all sensors"""
        all_measurements = []
        
        for sensor_id in self.active_sensors.keys():
            measurements = self.generate_measurement(sensor_id)
            all_measurements.extend(measurements)
        
        # Save all measurements in batch
        if all_measurements:
            self.save_measurements(all_measurements)
        
        # Update sensor statistics (check every 10 cycles to reduce DB load)
        if self.stats['total_measurements'] % 10 == 0:
            for sensor_id in self.active_sensors.keys():
                self.update_sensor_statistics(sensor_id)
    
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
            self.logger.info(" Keyboard interrupt received")
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
    print("\n Stopping simulator...")
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
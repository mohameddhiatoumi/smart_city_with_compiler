"""
Configuration settings for the sensor simulator
Adjust these values to control simulation behavior
"""

from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Simulation timing
MEASUREMENT_INTERVAL_SECONDS = 10   # How often to generate measurements (5 seconds for faster data)
SIMULATION_SPEED_MULTIPLIER = 1    # Set to 60 for 1-hour simulation in 1 minute (testing mode)

# Anomaly detection
ANOMALY_PROBABILITY = 0.03         # 3% chance of anomaly per measurement (increased from 1%)
ERROR_RATE_THRESHOLD = 15.0        # % error rate to trigger 'signale' status
AUTO_CREATE_INTERVENTIONS = True   # Automatically create interventions for faulty sensors

# Measurement variation ranges - MUCH LARGER for visible changes
NORMAL_VARIATION = {
    'PM2.5': {'min_change': -15, 'max_change': 12},        # Increased from -6 to 3
    'PM10': {'min_change': -18, 'max_change': 15},         # Increased from -7 to 5
    'CO2': {'min_change': -30, 'max_change': 25},          # Increased from -12 to 10
    'NO2': {'min_change': -18, 'max_change': 15},          # Increased from -7 to 5
    'temperature': {'min_change': -2.5, 'max_change': 2},  # Increased from -3 to 1
    'humidite': {'min_change': -8, 'max_change': 6},       # Increased from -5 to 3
    'bruit_db': {'min_change': -12, 'max_change': 10},     # Increased from -6 to 5
    'debit_vehicules': {'min_change': -50, 'max_change': 45}  # Increased from -22 to 20
}

# ANOMALY_VARIATION - Large spikes (30-50% changes)
ANOMALY_VARIATION = {
    'PM2.5': {'min_change': -50, 'max_change': 80},        # Smaller anomalies for visible spikes
    'PM10': {'min_change': -70, 'max_change': 100},
    'CO2': {'min_change': -150, 'max_change': 200},
    'NO2': {'min_change': -50, 'max_change': 80},
    'temperature': {'min_change': -15, 'max_change': 15},
    'humidite': {'min_change': -30, 'max_change': 30},
    'bruit_db': {'min_change': -25, 'max_change': 35},
    'debit_vehicules': {'min_change': -150, 'max_change': 200}
}

# Measurement baselines (reset point if value goes out of reasonable bounds)
MEASUREMENT_BASELINES = {
    'PM2.5': {'baseline': 25, 'min': 0, 'max': 200},
    'PM10': {'baseline': 50, 'min': 0, 'max': 300},
    'CO2': {'baseline': 400, 'min': 300, 'max': 1000},
    'NO2': {'baseline': 40, 'min': 0, 'max': 200},
    'temperature': {'baseline': 22, 'min': -10, 'max': 50},
    'humidite': {'baseline': 60, 'min': 0, 'max': 100},
    'bruit_db': {'baseline': 55, 'min': 20, 'max': 120},
    'debit_vehicules': {'baseline': 120, 'min': 0, 'max': 500}
}

# Units for each measurement type
MEASUREMENT_UNITS = {
    'PM2.5': 'µg/m³',
    'PM10': 'µg/m³',
    'CO2': 'ppm',
    'NO2': 'µg/m³',
    'temperature': '°C',
    'humidite': '%',
    'bruit_db': 'dB',
    'debit_vehicules': 'veh/h'
}

# Sensor type to measurement type mapping
SENSOR_MEASUREMENTS = {
    'air': ['PM2.5', 'PM10', 'CO2', 'NO2', 'temperature', 'humidite'],
    'bruit': ['bruit_db', 'temperature'],
    'trafic': ['debit_vehicules']
}

# Diurnal patterns (hour-based multipliers for realistic variation)
# Keys are hours (0-23), values are multipliers
TRAFFIC_PATTERN = {
    0: 0.2, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.2, 5: 0.5,
    6: 1.2, 7: 1.8, 8: 2.0, 9: 1.5, 10: 1.2, 11: 1.3,
    12: 1.4, 13: 1.3, 14: 1.2, 15: 1.3, 16: 1.5, 17: 2.0,
    18: 1.8, 19: 1.4, 20: 1.0, 21: 0.7, 22: 0.5, 23: 0.3
}

POLLUTION_PATTERN = {
    0: 0.7, 1: 0.6, 2: 0.5, 3: 0.5, 4: 0.6, 5: 0.8,
    6: 1.2, 7: 1.5, 8: 1.7, 9: 1.6, 10: 1.4, 11: 1.3,
    12: 1.3, 13: 1.2, 14: 1.2, 15: 1.3, 16: 1.5, 17: 1.7,
    18: 1.6, 19: 1.3, 20: 1.1, 21: 0.9, 22: 0.8, 23: 0.7
}

# Logging
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = str(PROJECT_ROOT / 'logs' / 'simulator.log')
CONSOLE_OUTPUT = True  # Print to console in addition to log file
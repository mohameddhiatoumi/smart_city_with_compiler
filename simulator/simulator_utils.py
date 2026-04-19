"""
Utility functions for realistic sensor data generation
Handles diurnal patterns, value constraints, and anomaly generation with momentum
"""

import random
from datetime import datetime
from simulator_config import (
    NORMAL_VARIATION, ANOMALY_VARIATION, MEASUREMENT_BASELINES,
    TRAFFIC_PATTERN, POLLUTION_PATTERN, ANOMALY_PROBABILITY
)

# Global momentum tracker: {sensor_id: {measure_type: {'direction': 1 or -1, 'cycles': 0}}}
MOMENTUM_TRACKER = {}


def get_diurnal_multiplier(measure_type, current_hour=None):
    """
    Get time-of-day multiplier for realistic patterns
    
    Args:
        measure_type: Type of measurement
        current_hour: Hour (0-23), defaults to current hour
    
    Returns:
        Float multiplier (0.1 to 2.0)
    """
    if current_hour is None:
        current_hour = datetime.now().hour
    
    # Apply patterns based on measurement type
    if measure_type == 'debit_vehicules':
        return TRAFFIC_PATTERN.get(current_hour, 1.0)
    elif measure_type in ['PM2.5', 'PM10', 'CO2', 'NO2']:
        return POLLUTION_PATTERN.get(current_hour, 1.0)
    else:
        return 1.0  # No pattern for temperature, humidity, noise


def update_momentum(sensor_id, measure_type, change_direction):
    """
    Track momentum for smooth trending patterns
    
    Args:
        sensor_id: ID of the sensor
        measure_type: Type of measurement
        change_direction: 1 for up, -1 for down
    """
    key = f"{sensor_id}:{measure_type}"
    
    if key not in MOMENTUM_TRACKER:
        MOMENTUM_TRACKER[key] = {'direction': change_direction, 'cycles': 1}
    else:
        momentum = MOMENTUM_TRACKER[key]
        
        if momentum['direction'] == change_direction:
            # Continue in same direction
            momentum['cycles'] += 1
            # Cap at 5 cycles to avoid infinite trends
            if momentum['cycles'] > 5:
                momentum['direction'] = -change_direction
                momentum['cycles'] = 1
        else:
            # Switch direction
            momentum['direction'] = change_direction
            momentum['cycles'] = 1


def get_momentum_factor(sensor_id, measure_type):
    """
    Get momentum multiplier for smooth trending
    
    Returns:
        Factor to apply to change (0.5 to 1.5)
    """
    key = f"{sensor_id}:{measure_type}"
    
    if key not in MOMENTUM_TRACKER:
        return 1.0
    
    momentum = MOMENTUM_TRACKER[key]
    cycles = momentum['cycles']
    
    # Increase magnitude over time: 1.0 → 1.5 over 5 cycles
    return 1.0 + (cycles / 10.0)


def generate_next_value(sensor_id, measure_type, last_value, force_anomaly=False):
    """
    Generate next measurement value based on last value with momentum tracking
    
    Args:
        sensor_id: ID of the sensor
        measure_type: Type of measurement
        last_value: Previous measurement value
        force_anomaly: Force an anomaly (for testing)
    
    Returns:
        Tuple of (new_value, is_anomaly)
    """
    config = MEASUREMENT_BASELINES[measure_type]
    baseline = config['baseline']
    
    # Determine if this is an anomaly
    is_anomaly = force_anomaly or (random.random() < ANOMALY_PROBABILITY)
    
    # Select variation range
    if is_anomaly:
        variation = ANOMALY_VARIATION[measure_type]
    else:
        variation = NORMAL_VARIATION[measure_type]
    
    # Generate change
    change = random.uniform(variation['min_change'], variation['max_change'])
    
    # Apply momentum for smooth trends (normal variations only)
    if not is_anomaly:
        momentum_factor = get_momentum_factor(sensor_id, measure_type)
        change *= momentum_factor
        
        # Track momentum direction
        change_direction = 1 if change > 0 else -1
        update_momentum(sensor_id, measure_type, change_direction)
        
        # Apply diurnal pattern
        multiplier = get_diurnal_multiplier(measure_type)
        change *= multiplier
    
    # Mean reversion: 75% trend, 25% back to baseline
    MEAN_REVERSION_WEIGHT = 0.25
    new_value = (1 - MEAN_REVERSION_WEIGHT) * (last_value + change) + \
                MEAN_REVERSION_WEIGHT * baseline
    
    # Enforce bounds
    if new_value < config['min'] or new_value > config['max']:
        new_value = baseline
        is_anomaly = True
    
    # Ensure non-negative
    if new_value < 0:
        new_value = 0
    
    return round(new_value, 2), is_anomaly


def get_initial_value(measure_type):
    """
    Get a realistic initial value for a measurement type
    
    Args:
        measure_type: Type of measurement
    
    Returns:
        Float value
    """
    config = MEASUREMENT_BASELINES[measure_type]
    
    # Start near baseline with some variation
    variation = (config['max'] - config['min']) * 0.15
    initial = config['baseline'] + random.uniform(-variation, variation)
    
    return max(config['min'], min(config['max'], initial))


def calculate_error_rate(total_measurements, total_anomalies):
    """
    Calculate error rate percentage
    
    Args:
        total_measurements: Total number of measurements
        total_anomalies: Number of anomalous measurements
    
    Returns:
        Error rate as percentage (0-100)
    """
    if total_measurements == 0:
        return 0.0
    
    return round((total_anomalies / total_measurements) * 100, 2)


def should_trigger_intervention(error_rate, threshold=15.0):
    """
    Determine if error rate warrants intervention
    
    Args:
        error_rate: Current error rate percentage
        threshold: Threshold for intervention
    
    Returns:
        Boolean
    """
    return error_rate >= threshold
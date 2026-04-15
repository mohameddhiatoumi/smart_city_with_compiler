"""
Utility functions for realistic sensor data generation
Handles diurnal patterns, value constraints, and anomaly generation
"""

import random
from datetime import datetime
from simulator_config import (
    NORMAL_VARIATION, ANOMALY_VARIATION, MEASUREMENT_BASELINES,
    TRAFFIC_PATTERN, POLLUTION_PATTERN, ANOMALY_PROBABILITY
)


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


def generate_next_value(measure_type, last_value, force_anomaly=False):
    """
    Generate next measurement value based on last value
    
    Args:
        measure_type: Type of measurement
        last_value: Previous measurement value
        force_anomaly: Force an anomaly (for testing)
    
    Returns:
        Tuple of (new_value, is_anomaly)
    """
    config = MEASUREMENT_BASELINES[measure_type]
    
    # Determine if this is an anomaly
    is_anomaly = force_anomaly or (random.random() < ANOMALY_PROBABILITY)
    
    # Select variation range
    if is_anomaly:
        variation = ANOMALY_VARIATION[measure_type]
    else:
        variation = NORMAL_VARIATION[measure_type]
    
    # Generate change
    change = random.uniform(variation['min_change'], variation['max_change'])
    
    # Apply diurnal pattern to normal variations
    if not is_anomaly:
        multiplier = get_diurnal_multiplier(measure_type)
        change *= multiplier
    
    # Calculate new value
    new_value = last_value + change
    
    # Enforce bounds (reset to baseline if out of range)
    if new_value < config['min'] or new_value > config['max']:
        new_value = config['baseline']
        is_anomaly = True  # Mark as anomaly since we had to reset
    
    # Ensure non-negative for certain types
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
    variation = (config['max'] - config['min']) * 0.2
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
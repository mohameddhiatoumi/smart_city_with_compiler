"""
Logging utilities for the sensor simulator
Provides colored console output and file logging
"""

import logging
import os
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


def setup_logger(log_file='../logs/simulator.log', level='INFO', console_output=True):
    """
    Setup logger with file and optional console output
    
    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console_output: Whether to print to console
    
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('SensorSimulator')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # File handler (no colors)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (with colors)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def log_measurement(logger, sensor_id, measure_type, value, is_anomaly=False):
    """Log a measurement event"""
    if is_anomaly:
        logger.warning(f"🚨 ANOMALY: {sensor_id} | {measure_type} = {value:.2f} (ABNORMAL)")
    else:
        logger.debug(f"📊 {sensor_id} | {measure_type} = {value:.2f}")


def log_sensor_status_change(logger, sensor_id, old_status, new_status, error_rate):
    """Log sensor status transition"""
    logger.warning(
        f"⚠️  SENSOR STATUS CHANGE: {sensor_id} | {old_status} → {new_status} | "
        f"Error rate: {error_rate:.2f}%"
    )


def log_intervention_created(logger, sensor_id, intervention_id):
    """Log automatic intervention creation"""
    logger.info(f"🔧 INTERVENTION CREATED: #{intervention_id} for sensor {sensor_id}")


def log_simulation_start(logger, num_sensors, interval):
    """Log simulation startup"""
    logger.info("="*60)
    logger.info(f"🚀 SENSOR SIMULATOR STARTED")
    logger.info(f"   Active sensors: {num_sensors}")
    logger.info(f"   Measurement interval: {interval} seconds")
    logger.info(f"   Anomaly probability: 1%")
    logger.info("="*60)


def log_simulation_stop(logger, total_measurements, total_anomalies):
    """Log simulation shutdown"""
    logger.info("="*60)
    logger.info(f"🛑 SENSOR SIMULATOR STOPPED")
    logger.info(f"   Total measurements: {total_measurements}")
    logger.info(f"   Total anomalies detected: {total_anomalies}")
    logger.info("="*60)
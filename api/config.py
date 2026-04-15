"""
API configuration settings
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "neo_sousse.db"

# API settings
API_TITLE = "Neo-Sousse 2030 Smart City API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
Smart City Platform API for Neo-Sousse 2030.

Features:
* Real-time sensor data
* Pollution monitoring
* Natural language queries
* Intervention management
"""

# CORS settings (for React frontend)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Pagination defaults
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Time ranges for queries
DEFAULT_TIME_RANGE_HOURS = 24
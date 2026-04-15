"""
Sensor-related API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.db_utils import execute_query
from api.models import SensorBase, SensorDetail, MeasurementBase
from api.config import DEFAULT_PAGE_SIZE, DEFAULT_TIME_RANGE_HOURS

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get("/", response_model=List[SensorBase])
async def list_sensors(
    type_capteur: Optional[str] = None,
    statut: Optional[str] = None,
    zone_id: Optional[int] = None
):
    """Get list of all sensors with optional filters"""
    query = "SELECT capteur_id, zone_id, type_capteur, statut FROM capteurs WHERE 1=1"
    params = []
    
    if type_capteur:
        query += " AND type_capteur = ?"
        params.append(type_capteur)
    
    if statut:
        query += " AND statut = ?"
        params.append(statut)
    
    if zone_id:
        query += " AND zone_id = ?"
        params.append(zone_id)
    
    query += " ORDER BY capteur_id"
    
    results = execute_query(query, tuple(params))
    return [dict(row) for row in results]


@router.get("/{capteur_id}", response_model=SensorDetail)
async def get_sensor(capteur_id: str):
    """Get detailed information about a specific sensor"""
    query = """
        SELECT capteur_id, zone_id, type_capteur, statut,
               date_installation, derniere_maintenance,
               taux_erreur, nb_anomalies_totales, seuil_alerte
        FROM capteurs
        WHERE capteur_id = ?
    """
    
    results = execute_query(query, (capteur_id,))
    
    if not results:
        raise HTTPException(status_code=404, detail=f"Sensor {capteur_id} not found")
    
    return dict(results[0])


@router.get("/{capteur_id}/measurements", response_model=List[MeasurementBase])
async def get_sensor_measurements(
    capteur_id: str,
    hours: int = Query(DEFAULT_TIME_RANGE_HOURS, ge=1, le=168),
    type_mesure: Optional[str] = None,
    anomalies_only: bool = False,
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=1000)
):
    """Get measurements for a specific sensor"""
    
    # Calculate time threshold
    time_threshold = datetime.now() - timedelta(hours=hours)
    
    query = """
        SELECT mesure_id, capteur_id, timestamp, type_mesure, valeur, unite, est_anomalie
        FROM mesures
        WHERE capteur_id = ? AND timestamp >= ?
    """
    params = [capteur_id, time_threshold]
    
    if type_mesure:
        query += " AND type_mesure = ?"
        params.append(type_mesure)
    
    if anomalies_only:
        query += " AND est_anomalie = 1"
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    results = execute_query(query, tuple(params))
    return [dict(row) for row in results]


@router.get("/{capteur_id}/latest")
async def get_latest_measurements(capteur_id: str):
    """Get the most recent measurement of each type for a sensor"""
    query = """
        WITH LatestPerType AS (
            SELECT type_mesure, MAX(timestamp) as latest_time
            FROM mesures
            WHERE capteur_id = ?
            GROUP BY type_mesure
        )
        SELECT m.type_mesure, m.valeur, m.unite, m.timestamp, m.est_anomalie
        FROM mesures m
        INNER JOIN LatestPerType l ON m.type_mesure = l.type_mesure AND m.timestamp = l.latest_time
        WHERE m.capteur_id = ?
        ORDER BY m.type_mesure
    """
    
    results = execute_query(query, (capteur_id, capteur_id))
    return [dict(row) for row in results]
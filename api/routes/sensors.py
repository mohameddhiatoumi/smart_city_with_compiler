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

@router.get("/measurements/recent-all")
async def get_all_recent_measurements(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get recent measurements from ALL active sensors
    This is the endpoint the frontend PollutionChart uses
    """
    try:
        # Calculate time threshold as string (SQLite stores timestamps as strings)
        time_threshold = datetime.now() - timedelta(hours=hours)
        time_threshold_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"🔍 DEBUG: Time threshold: {time_threshold_str}")
        print(f"🔍 DEBUG: Limit: {limit}")
        
        # Query for recent measurements
        query = """
            SELECT 
                mesure_id, 
                capteur_id, 
                timestamp, 
                type_mesure, 
                valeur, 
                unite, 
                est_anomalie
            FROM mesures
            WHERE timestamp >= ?
            AND capteur_id IN (
                SELECT capteur_id FROM capteurs 
                WHERE statut IN ('actif', 'signale')
            )
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        results = execute_query(query, (time_threshold_str, limit))
        
        print(f"🔍 DEBUG: Query returned {len(results) if results else 0} results")
        
        # Convert sqlite3.Row objects to dictionaries properly
        data = []
        for row in results:
            data.append({
                'mesure_id': row['mesure_id'],
                'capteur_id': row['capteur_id'],
                'timestamp': row['timestamp'],
                'type_mesure': row['type_mesure'],
                'valeur': float(row['valeur']),  # Ensure it's a float
                'unite': row['unite'],
                'est_anomalie': row['est_anomalie']
            })
        
        print(f"✅ Returning {len(data)} measurements")
        return data
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/", response_model=List[SensorBase])
async def list_sensors(
    type_capteur: Optional[str] = None,
    statut: Optional[str] = None,
    zone_id: Optional[int] = None
):
    """Get list of all sensors with optional filters"""
    query = "SELECT capteur_id, zone_id, type_capteur, statut, taux_erreur, nb_anomalies_totales FROM capteurs WHERE 1=1"
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
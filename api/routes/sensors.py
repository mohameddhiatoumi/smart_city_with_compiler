"""
Sensor-related API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

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
        time_threshold = datetime.now() - timedelta(hours=hours)
        time_threshold_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"🔍 DEBUG: Time threshold: {time_threshold_str}")
        print(f"🔍 DEBUG: Limit: {limit}")
        
        # ✅ CHANGE: Use %s instead of ? for PostgreSQL
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
            WHERE timestamp >= %s
            AND capteur_id IN (
                SELECT capteur_id FROM capteurs 
                WHERE statut IN ('actif', 'signale')
            )
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        results = execute_query(query, (time_threshold_str, limit))
        
        print(f"🔍 DEBUG: Query returned {len(results) if results else 0} results")
        
        data = []
        for row in results:
            data.append({
                'mesure_id': row['mesure_id'],
                'capteur_id': row['capteur_id'],
                'timestamp': row['timestamp'],
                'type_mesure': row['type_mesure'],
                'valeur': float(row['valeur']),
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
    # ✅ CHANGE: Use %s instead of ?
    query = "SELECT capteur_id, zone_id, type_capteur, statut, taux_erreur, nb_anomalies_totales FROM capteurs WHERE 1=1"
    params = []
    
    if type_capteur:
        query += " AND type_capteur = %s"
        params.append(type_capteur)
    
    if statut:
        query += " AND statut = %s"
        params.append(statut)
    
    if zone_id:
        query += " AND zone_id = %s"
        params.append(zone_id)
    
    query += " ORDER BY capteur_id"
    
    results = execute_query(query, tuple(params))
    return [dict(row) for row in results]


@router.get("/{capteur_id}", response_model=SensorDetail)
async def get_sensor(capteur_id: str):
    """Get detailed information about a specific sensor"""
    # ✅ CHANGE: Use %s instead of ?
    query = """
        SELECT capteur_id, zone_id, type_capteur, statut,
               date_installation, derniere_maintenance,
               taux_erreur, nb_anomalies_totales, seuil_alerte
        FROM capteurs
        WHERE capteur_id = %s
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
    
    time_threshold = datetime.now() - timedelta(hours=hours)
    
    # ✅ CHANGE: Use %s instead of ? for PostgreSQL
    query = """
        SELECT mesure_id, capteur_id, timestamp, type_mesure, valeur, unite, est_anomalie
        FROM mesures
        WHERE capteur_id = %s AND timestamp >= %s
    """
    params = [capteur_id, time_threshold]
    
    if type_mesure:
        query += " AND type_mesure = %s"
        params.append(type_mesure)
    
    if anomalies_only:
        query += " AND est_anomalie = TRUE"  # ✅ CHANGE: TRUE instead of 1
    
    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)
    
    results = execute_query(query, tuple(params))
    return [dict(row) for row in results]


@router.get("/{capteur_id}/latest")
async def get_latest_measurements(capteur_id: str):
    """Get the most recent measurement of each type for a sensor"""
    # ✅ CHANGE: Use %s instead of ?
    query = """
        WITH LatestPerType AS (
            SELECT type_mesure, MAX(timestamp) as latest_time
            FROM mesures
            WHERE capteur_id = %s
            GROUP BY type_mesure
        )
        SELECT m.type_mesure, m.valeur, m.unite, m.timestamp, m.est_anomalie
        FROM mesures m
        INNER JOIN LatestPerType l ON m.type_mesure = l.type_mesure AND m.timestamp = l.latest_time
        WHERE m.capteur_id = %s
        ORDER BY m.type_mesure
    """
    
    results = execute_query(query, (capteur_id, capteur_id))
    return [dict(row) for row in results]
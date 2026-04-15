"""
Zone-related API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from database.db_utils import execute_query
from api.models import ZoneBase, ZonePollution
from api.config import DEFAULT_TIME_RANGE_HOURS

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("/", response_model=List[ZoneBase])
async def list_zones():
    """Get list of all zones"""
    query = "SELECT zone_id, nom, description FROM zones ORDER BY zone_id"
    results = execute_query(query)
    return [dict(row) for row in results]


@router.get("/{zone_id}", response_model=ZoneBase)
async def get_zone(zone_id: int):
    """Get information about a specific zone"""
    query = "SELECT zone_id, nom, description FROM zones WHERE zone_id = ?"
    results = execute_query(query, (zone_id,))
    
    if not results:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    
    return dict(results[0])


@router.get("/{zone_id}/pollution", response_model=ZonePollution)
async def get_zone_pollution(
    zone_id: int,
    hours: int = Query(DEFAULT_TIME_RANGE_HOURS, ge=1, le=168)
):
    """Get average pollution levels for a zone"""
    
    time_threshold = datetime.now() - timedelta(hours=hours)
    
    query = """
        SELECT 
            z.zone_id,
            z.nom as zone_nom,
            AVG(CASE WHEN m.type_mesure = 'PM2.5' THEN m.valeur END) as avg_pm25,
            AVG(CASE WHEN m.type_mesure = 'PM10' THEN m.valeur END) as avg_pm10,
            AVG(CASE WHEN m.type_mesure = 'CO2' THEN m.valeur END) as avg_co2,
            AVG(CASE WHEN m.type_mesure = 'NO2' THEN m.valeur END) as avg_no2,
            COUNT(*) as measurement_count
        FROM zones z
        JOIN capteurs c ON z.zone_id = c.zone_id
        JOIN mesures m ON c.capteur_id = m.capteur_id
        WHERE z.zone_id = ? AND m.timestamp >= ?
        GROUP BY z.zone_id, z.nom
    """
    
    results = execute_query(query, (zone_id, time_threshold))
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No pollution data for zone {zone_id}")
    
    return dict(results[0])


@router.get("/pollution/ranking")
async def get_pollution_ranking(
    hours: int = Query(DEFAULT_TIME_RANGE_HOURS, ge=1, le=168),
    pollutant: str = Query("PM2.5", pattern="^(PM2.5|PM10|CO2|NO2)$")
):
    """Get zones ranked by pollution level"""
    
    time_threshold = datetime.now() - timedelta(hours=hours)
    
    query = f"""
        SELECT 
            z.zone_id,
            z.nom as zone_nom,
            AVG(m.valeur) as avg_value,
            COUNT(*) as measurement_count
        FROM zones z
        JOIN capteurs c ON z.zone_id = c.zone_id
        JOIN mesures m ON c.capteur_id = m.capteur_id
        WHERE m.type_mesure = ? AND m.timestamp >= ?
        GROUP BY z.zone_id, z.nom
        ORDER BY avg_value DESC
    """
    
    results = execute_query(query, (pollutant, time_threshold))
    return [dict(row) for row in results]
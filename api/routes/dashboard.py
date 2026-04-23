"""
Dashboard statistics and overview endpoints
"""

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from database.db_utils import execute_query
from api.models import DashboardStats, AnomalyAlert

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get overall system statistics"""
    
    # ✅ CHANGE: Use TRUE instead of 1 for PostgreSQL
    sensor_stats = execute_query("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN statut = 'actif' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN statut = 'signale' THEN 1 ELSE 0 END) as faulty,
            AVG(taux_erreur) as avg_error
        FROM capteurs
    """)[0]
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # ✅ CHANGE: Use %s instead of ?
    measurement_stats = execute_query("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN est_anomalie = TRUE THEN 1 ELSE 0 END) as anomalies
        FROM mesures
        WHERE timestamp >= %s
    """, (today,))[0]
    
    intervention_count = execute_query("""
        SELECT COUNT(*) as count
        FROM interventions
        WHERE statut != 'termine'
    """)[0]['count']
    
    return {
        'total_sensors': sensor_stats['total'],
        'active_sensors': sensor_stats['active'],
        'faulty_sensors': sensor_stats['faulty'],
        'total_measurements_today': measurement_stats['total'],
        'total_anomalies_today': measurement_stats['anomalies'] or 0,
        'avg_error_rate': round(sensor_stats['avg_error'] or 0, 2),
        'ongoing_interventions': intervention_count
    }


@router.get("/anomalies", response_model=List[AnomalyAlert])
async def get_recent_anomalies(limit: int = Query(10, ge=1, le=50)):
    """Get sensors with recent anomalies"""
    
    # ✅ CHANGE: Use %s and TRUE instead of ? and 1
    query = """
        SELECT 
            c.capteur_id,
            c.type_capteur,
            z.nom as zone_nom,
            c.taux_erreur,
            c.nb_anomalies_totales as nb_anomalies,
            MAX(m.timestamp) as last_anomaly
        FROM capteurs c
        JOIN zones z ON c.zone_id = z.zone_id
        JOIN mesures m ON c.capteur_id = m.capteur_id
        WHERE m.est_anomalie = TRUE
        GROUP BY c.capteur_id, c.type_capteur, z.nom, c.taux_erreur, c.nb_anomalies_totales
        ORDER BY last_anomaly DESC
        LIMIT %s
    """
    
    results = execute_query(query, (limit,))
    return [dict(row) for row in results]


@router.get("/live-feed")
async def get_live_feed(limit: int = Query(20, ge=1, le=100)):
    """Get most recent measurements across all sensors"""
    
    # ✅ CHANGE: Use %s instead of ?
    query = """
        SELECT 
            m.capteur_id,
            c.type_capteur,
            z.nom as zone_nom,
            m.type_mesure,
            m.valeur,
            m.unite,
            m.timestamp,
            m.est_anomalie
        FROM mesures m
        JOIN capteurs c ON m.capteur_id = c.capteur_id
        JOIN zones z ON c.zone_id = z.zone_id
        ORDER BY m.timestamp DESC
        LIMIT %s
    """
    
    results = execute_query(query, (limit,))
    return [dict(row) for row in results]
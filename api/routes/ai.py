"""
AI Generative Module Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from ai_module import AIGenerator, TemplateAIGenerator

router = APIRouter(prefix="/ai", tags=["AI"])

# Try to initialize AI generator
try:
    ai_gen = AIGenerator(db_path="neo_sousse.db", use_openrouter=True)
except Exception as e:
    print(f"⚠️  OpenRouter not available, using templates: {e}")
    ai_gen = TemplateAIGenerator(db_path="neo_sousse.db")

@router.get("/report/air-quality")
async def get_air_quality_report(zone_id: Optional[int] = None, date: Optional[str] = None):
    """
    Generate air quality report
    
    Args:
        zone_id: Optional zone ID
        date: Optional date in format YYYY-MM-DD
    """
    try:
        report = ai_gen.generate_air_quality_report(zone_id=zone_id, date_str=date)
        return {
            "type": "air_quality",
            "content": report,
            "zone_id": zone_id,
            "date": date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendation/sensor/{capteur_id}")
async def get_sensor_recommendation(capteur_id: str):
    """
    Generate maintenance recommendation for a specific sensor
    
    Args:
        capteur_id: Sensor ID (e.g., 'C-001')
    """
    try:
        recommendation = ai_gen.generate_maintenance_recommendation(capteur_id)
        return {
            "type": "maintenance",
            "capteur_id": capteur_id,
            "content": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/traffic")
async def get_traffic_analysis(zone_id: Optional[int] = None):
    """
    Generate traffic pattern analysis
    
    Args:
        zone_id: Optional zone ID
    """
    try:
        analysis = ai_gen.generate_traffic_analysis(zone_id=zone_id)
        return {
            "type": "traffic",
            "content": analysis,
            "zone_id": zone_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-transition")
async def validate_fsm_transition(
    entity_type: str,
    current_state: str,
    proposed_event: str,
    context: dict = None
):
    """
    Validate if a state transition is logically appropriate
    
    Args:
        entity_type: 'sensor', 'intervention', or 'vehicle'
        current_state: Current state of entity
        proposed_event: Event to trigger
        context: Additional context data
    """
    try:
        result = ai_gen.validate_fsm_transition(
            entity_type=entity_type,
            current_state=current_state,
            proposed_event=proposed_event,
            context=context or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
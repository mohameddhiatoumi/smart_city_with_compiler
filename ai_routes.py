"""
FastAPI routes for AI Generative Module
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(__file__))
from ai_module import AIGenerator, TemplateAIGenerator

router = APIRouter(prefix="/ai", tags=["AI Generation"])

# Global AI generator (will be initialized from main app)
ai_generator = None


def init_ai_generator(db_path: str, use_openai: bool = True, api_key: Optional[str] = None):
    """Initialize the AI generator"""
    global ai_generator
    
    if use_openai:
        try:
            ai_generator = AIGenerator(api_key=api_key, db_path=db_path)
            return True
        except ValueError:
            # Fall back to template-based
            ai_generator = TemplateAIGenerator(db_path=db_path)
            return False
    else:
        ai_generator = TemplateAIGenerator(db_path=db_path)
        return False


# Request models
class AirQualityReportRequest(BaseModel):
    zone_id: Optional[int] = None
    date: Optional[str] = None  # Format: YYYY-MM-DD


class MaintenanceRequest(BaseModel):
    capteur_id: int


class TrafficAnalysisRequest(BaseModel):
    zone_id: Optional[int] = None


class FSMValidationRequest(BaseModel):
    entity_type: str  # 'sensor', 'intervention', 'vehicle'
    current_state: str
    proposed_event: str
    context: Dict[str, Any]


class EcoScoreRequest(BaseModel):
    citoyen_id: int


# Response models
class ReportResponse(BaseModel):
    success: bool
    report: str
    generated_at: str


class ValidationResponse(BaseModel):
    is_valid: Optional[bool]
    confidence: float
    reasoning: str
    alternative: Optional[str] = None


# ============================================================================
# AI GENERATION ROUTES
# ============================================================================

@router.post("/reports/air-quality", response_model=ReportResponse)
async def generate_air_quality_report(request: AirQualityReportRequest):
    """
    Generate natural language air quality report
    
    - **zone_id**: Optional zone ID to filter (None = all zones)
    - **date**: Optional date in YYYY-MM-DD format (None = today)
    """
    if ai_generator is None:
        raise HTTPException(status_code=500, detail="AI generator not initialized")
    
    try:
        report = ai_generator.generate_air_quality_report(
            zone_id=request.zone_id,
            date_str=request.date
        )
        
        from datetime import datetime
        return ReportResponse(
            success=True,
            report=report,
            generated_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/maintenance", response_model=ReportResponse)
async def generate_maintenance_recommendation(request: MaintenanceRequest):
    """
    Generate maintenance recommendation for a sensor
    
    - **capteur_id**: Sensor ID to analyze
    """
    if ai_generator is None:
        raise HTTPException(status_code=500, detail="AI generator not initialized")
    
    try:
        report = ai_generator.generate_maintenance_recommendation(
            capteur_id=request.capteur_id
        )
        
        from datetime import datetime
        return ReportResponse(
            success=True,
            report=report,
            generated_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/traffic", response_model=ReportResponse)
async def generate_traffic_analysis(request: TrafficAnalysisRequest):
    """
    Generate traffic pattern analysis
    
    - **zone_id**: Optional zone ID to filter (None = all zones)
    """
    if ai_generator is None:
        raise HTTPException(status_code=500, detail="AI generator not initialized")
    
    try:
        # Check if method exists (only in AIGenerator, not TemplateAIGenerator)
        if not hasattr(ai_generator, 'generate_traffic_analysis'):
            raise HTTPException(
                status_code=501,
                detail="Traffic analysis requires OpenAI API. Please configure OPENAI_API_KEY."
            )
        
        report = ai_generator.generate_traffic_analysis(
            zone_id=request.zone_id
        )
        
        from datetime import datetime
        return ReportResponse(
            success=True,
            report=report,
            generated_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/eco-score", response_model=ReportResponse)
async def generate_eco_score_report(request: EcoScoreRequest):
    """
    Generate personalized eco-score report for a citizen
    
    - **citoyen_id**: Citizen ID to analyze
    """
    if ai_generator is None:
        raise HTTPException(status_code=500, detail="AI generator not initialized")
    
    try:
        # Check if method exists (only in AIGenerator)
        if not hasattr(ai_generator, 'generate_eco_score_report'):
            raise HTTPException(
                status_code=501,
                detail="Eco-score reports require OpenAI API. Please configure OPENAI_API_KEY."
            )
        
        report = ai_generator.generate_eco_score_report(
            citoyen_id=request.citoyen_id
        )
        
        from datetime import datetime
        return ReportResponse(
            success=True,
            report=report,
            generated_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/fsm-transition", response_model=ValidationResponse)
async def validate_fsm_transition(request: FSMValidationRequest):
    """
    Validate if a FSM transition is logical using AI
    
    - **entity_type**: Type of entity ('sensor', 'intervention', 'vehicle')
    - **current_state**: Current state of the entity
    - **proposed_event**: Event to trigger
    - **context**: Additional context data
    """
    if ai_generator is None:
        raise HTTPException(status_code=500, detail="AI generator not initialized")
    
    try:
        # Check if method exists (only in AIGenerator)
        if not hasattr(ai_generator, 'validate_fsm_transition'):
            raise HTTPException(
                status_code=501,
                detail="FSM validation requires OpenAI API. Please configure OPENAI_API_KEY."
            )
        
        result = ai_generator.validate_fsm_transition(
            entity_type=request.entity_type,
            current_state=request.current_state,
            proposed_event=request.proposed_event,
            context=request.context
        )
        
        return ValidationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ROUTES
# ============================================================================

@router.get("/status")
async def get_ai_status():
    """Get AI generator status and capabilities"""
    if ai_generator is None:
        return {
            "initialized": False,
            "type": None,
            "capabilities": []
        }
    
    is_openai = isinstance(ai_generator, AIGenerator)
    
    capabilities = [
        "generate_air_quality_report",
        "generate_maintenance_recommendation"
    ]
    
    if is_openai:
        capabilities.extend([
            "generate_traffic_analysis",
            "generate_eco_score_report",
            "validate_fsm_transition"
        ])
    
    return {
        "initialized": True,
        "type": "OpenAI" if is_openai else "Template",
        "capabilities": capabilities,
        "model": getattr(ai_generator, 'model', None)
    }


# ============================================================================
# QUICK GENERATION ENDPOINTS (GET methods for convenience)
# ============================================================================

@router.get("/quick/air-quality")
async def quick_air_quality_report(
    zone_id: Optional[int] = Query(None, description="Zone ID to filter"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Quick endpoint for air quality report (GET method)"""
    request = AirQualityReportRequest(zone_id=zone_id, date=date)
    return await generate_air_quality_report(request)


@router.get("/quick/maintenance/{capteur_id}")
async def quick_maintenance_recommendation(capteur_id: int):
    """Quick endpoint for maintenance recommendation (GET method)"""
    request = MaintenanceRequest(capteur_id=capteur_id)
    return await generate_maintenance_recommendation(request)


@router.get("/quick/traffic")
async def quick_traffic_analysis(
    zone_id: Optional[int] = Query(None, description="Zone ID to filter")
):
    """Quick endpoint for traffic analysis (GET method)"""
    request = TrafficAnalysisRequest(zone_id=zone_id)
    return await generate_traffic_analysis(request)


@router.get("/quick/eco-score/{citoyen_id}")
async def quick_eco_score_report(citoyen_id: int):
    """Quick endpoint for eco-score report (GET method)"""
    request = EcoScoreRequest(citoyen_id=citoyen_id)
    return await generate_eco_score_report(request)

"""
FastAPI routes for FSM operations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os

# Import FSM engine
sys.path.append(os.path.dirname(__file__))
from fsm_engine import FSMManager, InvalidTransitionError, FSMError

router = APIRouter(prefix="/fsm", tags=["FSM"])

# Global FSM manager (will be initialized with db_path from main app)
fsm_manager: Optional[FSMManager] = None


def init_fsm_manager(db_path: str):
    """Initialize the FSM manager"""
    global fsm_manager
    fsm_manager = FSMManager(db_path)


# Request models
class SensorEventRequest(BaseModel):
    event: str
    context: Optional[Dict[str, Any]] = None


class InterventionEventRequest(BaseModel):
    event: str
    context: Optional[Dict[str, Any]] = None


class VehicleEventRequest(BaseModel):
    event: str
    context: Optional[Dict[str, Any]] = None


# Response models
class FSMStateResponse(BaseModel):
    entity_id: str | int  # ✅ Changed from int to str
    entity_type: str
    current_state: str
    valid_transitions: List[str]
    history: List[Dict[str, Any]]


class TransitionResponse(BaseModel):
    success: bool
    new_state: str
    message: str


# ============================================================================
# SENSOR FSM ROUTES
# ============================================================================

@router.get("/sensors/{capteur_id}/state", response_model=FSMStateResponse)
async def get_sensor_state(capteur_id: str):  # ✅ Changed from int to str
    """Get current state and valid transitions for a sensor"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        fsm = fsm_manager.get_sensor_fsm(capteur_id)
        valid_transitions = [t.event for t in fsm.get_valid_transitions({'capteur_id': capteur_id})]
        
        return FSMStateResponse(
            entity_id=capteur_id,
            entity_type="sensor",
            current_state=fsm.current_state,
            valid_transitions=valid_transitions,
            history=fsm.history[-10:]  # Last 10 transitions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sensors/{capteur_id}/trigger", response_model=TransitionResponse)
async def trigger_sensor_event(capteur_id: str, request: SensorEventRequest):  # ✅ Changed from int to str
    """Trigger an event on a sensor FSM"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        new_state = fsm_manager.trigger_sensor_event(
            capteur_id, 
            request.event, 
            request.context
        )
        
        return TransitionResponse(
            success=True,
            new_state=new_state,
            message=f"Sensor {capteur_id} transitioned to {new_state}"
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FSMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensors/{capteur_id}/diagram")
async def get_sensor_diagram(capteur_id: str):  # ✅ Changed from int to str
    """Get textual FSM diagram for a sensor"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        fsm = fsm_manager.get_sensor_fsm(capteur_id)
        return {"diagram": fsm.get_state_diagram()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INTERVENTION FSM ROUTES
# ============================================================================

@router.get("/interventions/{intervention_id}/state", response_model=FSMStateResponse)
async def get_intervention_state(intervention_id: str):  # ✅ Changed from int to str
    """Get current state and valid transitions for an intervention"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        intervention_id = int(intervention_id)  # ✅ Convert to int for DB lookup
        fsm = fsm_manager.get_intervention_fsm(intervention_id)
        valid_transitions = [t.event for t in fsm.get_valid_transitions({'intervention_id': intervention_id})]
        
        return FSMStateResponse(
            entity_id=intervention_id,
            entity_type="intervention",
            current_state=fsm.current_state,
            valid_transitions=valid_transitions,
            history=fsm.history[-10:]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid intervention ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interventions/{intervention_id}/trigger", response_model=TransitionResponse)
async def trigger_intervention_event(intervention_id: str, request: InterventionEventRequest):  # ✅ Changed from int to str
    """Trigger an event on an intervention FSM"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        intervention_id = int(intervention_id)  # ✅ Convert to int for DB lookup
        new_state = fsm_manager.trigger_intervention_event(
            intervention_id,
            request.event,
            request.context
        )
        
        return TransitionResponse(
            success=True,
            new_state=new_state,
            message=f"Intervention {intervention_id} transitioned to {new_state}"
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid intervention ID format")
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FSMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interventions/{intervention_id}/diagram")
async def get_intervention_diagram(intervention_id: str):  # ✅ Changed from int to str
    """Get textual FSM diagram for an intervention"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        intervention_id = int(intervention_id)  # ✅ Convert to int for DB lookup
        fsm = fsm_manager.get_intervention_fsm(intervention_id)
        return {"diagram": fsm.get_state_diagram()}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid intervention ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VEHICLE FSM ROUTES
# ============================================================================

@router.get("/vehicles/{vehicule_id}/state", response_model=FSMStateResponse)
async def get_vehicle_state(vehicule_id: str):  # ✅ Changed from int to str
    """Get current state and valid transitions for a vehicle"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        vehicule_id = int(vehicule_id)  # ✅ Convert to int for DB lookup
        fsm = fsm_manager.get_vehicle_fsm(vehicule_id)
        valid_transitions = [t.event for t in fsm.get_valid_transitions({'vehicule_id': vehicule_id})]
        
        return FSMStateResponse(
            entity_id=vehicule_id,
            entity_type="vehicle",
            current_state=fsm.current_state,
            valid_transitions=valid_transitions,
            history=fsm.history[-10:]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vehicle ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vehicles/{vehicule_id}/trigger", response_model=TransitionResponse)
async def trigger_vehicle_event(vehicule_id: str, request: VehicleEventRequest):  # ✅ Keep as str
    """Trigger an event on a vehicle FSM"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        # Don't convert - keep as string if vehicles use VARCHAR IDs
        new_state = fsm_manager.trigger_vehicle_event(
            vehicule_id,  # ✅ Pass as-is
            request.event,
            request.context
        )
        
        return TransitionResponse(
            success=True,
            new_state=new_state,
            message=f"Vehicle {vehicule_id} transitioned to {new_state}"
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FSMError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vehicles/{vehicule_id}/diagram")
async def get_vehicle_diagram(vehicule_id: str):  # ✅ Changed from int to str
    """Get textual FSM diagram for a vehicle"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        vehicule_id = int(vehicule_id)  # ✅ Convert to int for DB lookup
        fsm = fsm_manager.get_vehicle_fsm(vehicule_id)
        return {"diagram": fsm.get_state_diagram()}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vehicle ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@router.get("/events/sensors")
async def get_sensor_events():
    """Get all available sensor events"""
    return {
        "events": [
            "activer",
            "detecter_anomalie",
            "commencer_reparation",
            "terminer_reparation",
            "declarer_hors_service",
            "reactiver"
        ]
    }


@router.get("/events/interventions")
async def get_intervention_events():
    """Get all available intervention events"""
    return {
        "events": [
            "assigner_tech1",
            "tech2_valider",
            "ia_valider",
            "terminer",
            "annuler"
        ]
    }


@router.get("/events/vehicles")
async def get_vehicle_events():
    """Get all available vehicle events"""
    return {
        "events": [
            "demarrer",
            "tomber_en_panne",
            "reparer",
            "arriver",
            "stationner"
        ]
    }

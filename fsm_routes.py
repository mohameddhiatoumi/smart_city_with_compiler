"""
FastAPI routes for FSM operations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os
import sqlite3
import json
import time 

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
@router.post("/interventions/create-for-sensor/{capteur_id}")
async def create_intervention_for_sensor(capteur_id: str):
    """Create a new intervention for a sensor in en_maintenance"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        conn = sqlite3.connect(fsm_manager.db_path)
        cursor = conn.cursor()
        
        # Check if sensor exists and is in en_maintenance
        cursor.execute(
            "SELECT capteur_id, statut FROM capteurs WHERE capteur_id = ?",
            (capteur_id,)
        )
        sensor = cursor.fetchone()
        
        if not sensor:
            conn.close()
            print(f"❌ Sensor {capteur_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Sensor {capteur_id} not found")
        
        sensor_id, sensor_status = sensor[0], sensor[1]
        print(f"🔍 Sensor {sensor_id} current status: '{sensor_status}'")
        
        if sensor_status != 'en_maintenance':
            conn.close()
            print(f"❌ Sensor {capteur_id} status is '{sensor_status}', expected 'en_maintenance'")
            raise HTTPException(status_code=400, detail=f"Sensor {capteur_id} is in '{sensor_status}' state, not 'en_maintenance'")
        
        # Create new intervention
        cursor.execute(
            """INSERT INTO interventions (capteur_id, statut, date_demande)
               VALUES (?, 'demande', datetime('now'))""",
            (capteur_id,)
        )
        conn.commit()
        
        intervention_id = cursor.lastrowid
        print(f"✅ Created intervention {intervention_id} for sensor {capteur_id}")
        conn.close()
        
        return {
            "success": True,
            "intervention_id": intervention_id,
            "capteur_id": capteur_id,
            "message": f"Intervention created for sensor {capteur_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating intervention: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@router.get("/interventions/pending")
async def get_pending_interventions():
    """Get all pending interventions for sensors in en_maintenance state"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        conn = sqlite3.connect(fsm_manager.db_path)
        cursor = conn.cursor()
        
        # Get all sensors that are in en_maintenance state
        cursor.execute(
            """SELECT c.capteur_id, c.type_capteur, c.zone_id
               FROM capteurs c
               WHERE c.statut = ?
               ORDER BY c.capteur_id DESC""",
            ('en_maintenance',)
        )
        
        rows = cursor.fetchall()
        sensors = []
        for row in rows:
            sensors.append({
                'capteur_id': row[0],
                'type_capteur': row[1],
                'zone_id': row[2]
            })
        
        conn.close()
        
        return {
            "pending_sensors": sensors,
            "count": len(sensors)
        }
    except Exception as e:
        print(f"Error in get_pending_interventions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def trigger_intervention_event(intervention_id: str, request: InterventionEventRequest):
    """Trigger an event on an intervention FSM"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        intervention_id = int(intervention_id)
        new_state = fsm_manager.trigger_intervention_event(
            intervention_id,
            request.event,
            request.context
        )
        
        # If intervention is completed, clear both caches so they reload from DB
        if new_state == 'termine':
            try:
                conn = sqlite3.connect(fsm_manager.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT capteur_id FROM interventions WHERE intervention_id = ?", (intervention_id,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    capteur_id = result[0]
                    # Clear caches to force reload from DB
                    fsm_manager.clear_sensor_cache(capteur_id)
                    fsm_manager.clear_intervention_cache(intervention_id)
                    print(f"✅ Cleared cache for sensor {capteur_id} - intervention {intervention_id} completed")
            except Exception as e:
                print(f"Error clearing cache: {e}")
        
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
async def get_vehicle_state(vehicule_id: str):  # ✅ Keep as str
    """Get current state and valid transitions for a vehicle"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        # Keep as string - vehicles use VARCHAR IDs
        fsm = fsm_manager.get_vehicle_fsm(vehicule_id)
        valid_transitions = [t.event for t in fsm.get_valid_transitions({'vehicule_id': vehicule_id})]
        
        return FSMStateResponse(
            entity_id=vehicule_id,
            entity_type="vehicle",
            current_state=fsm.current_state,
            valid_transitions=valid_transitions,
            history=fsm.history[-10:]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vehicles/{vehicule_id}/trigger", response_model=TransitionResponse)
async def trigger_vehicle_event(vehicule_id: str, request: VehicleEventRequest):
    """Trigger an event on a vehicle FSM"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        # Keep as string - vehicles use VARCHAR IDs
        new_state = fsm_manager.trigger_vehicle_event(
            vehicule_id,  # ✅ Pass as string
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
async def get_vehicle_diagram(vehicule_id: str):
    """Get textual FSM diagram for a vehicle"""
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        # Keep as string - vehicles use VARCHAR IDs
        fsm = fsm_manager.get_vehicle_fsm(vehicule_id)
        return {"diagram": fsm.get_state_diagram()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#
# ============================================================================
# IA VALIDATION AUTO-TRANSITION
# ============================================================================

@router.post("/interventions/{intervention_id}/ia-auto-validate")
async def ia_auto_validate(intervention_id: str):
    """
    IA automatically validates and decides:
    - If valid -> moves to TERMINÉ
    - If invalid -> moves back to DEMANDE
    Shows thinking animation for 3 seconds before deciding
    """
    if fsm_manager is None:
        raise HTTPException(status_code=500, detail="FSM manager not initialized")
    
    try:
        print(f"\n🔍 ia_auto_validate called with intervention_id: {intervention_id}")
        
        # Convert to int with better error handling
        try:
            intervention_id_int = int(intervention_id)
        except ValueError as ve:
            print(f"❌ Cannot convert intervention_id '{intervention_id}' to int: {ve}")
            raise HTTPException(status_code=400, detail=f"Invalid intervention ID format")
        
        print(f"✅ Converted to int: {intervention_id_int}")
        
        # Get the intervention FSM
        fsm = fsm_manager.get_intervention_fsm(intervention_id_int)
        print(f"📊 Current FSM state: {fsm.current_state}")
        
        # Check if we're in ia_valide state
        if fsm.current_state != 'ia_valide':
            print(f"❌ Not in ia_valide state, current: {fsm.current_state}")
            raise HTTPException(status_code=400, detail=f"Intervention is in '{fsm.current_state}' state, not 'ia_valide'")
        
        # Get validation data from intervention
        conn = sqlite3.connect(fsm_manager.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT description, capteur_id FROM interventions WHERE intervention_id = ?",
            (intervention_id_int,)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            print(f"❌ Intervention {intervention_id_int} not found")
            raise HTTPException(status_code=404, detail=f"Intervention not found")
        
        description_str = result[0]
        capteur_id = result[1]
        
        print(f"📋 Description from DB: {repr(description_str)}")
        print(f"🔧 Capteur ID: {capteur_id}")
        
        # Parse validation data or generate if missing
        if description_str:
            try:
                validation_data = json.loads(description_str)
                print(f"✅ Parsed existing validation data: {validation_data}")
            except json.JSONDecodeError as e:
                print(f"⚠️ Could not parse JSON, will generate validation")
                validation_data = None
        else:
            print(f"⚠️ Description is empty, will generate validation")
            validation_data = None
        
        # If no valid data, generate it now
        if not validation_data:
            print(f"🔄 Generating validation data on-the-fly...")
            
            # Get sensor data
            cursor.execute(
                """SELECT c.type_capteur, m.valeur, m.type_mesure
                   FROM capteurs c
                   LEFT JOIN mesures m ON c.capteur_id = m.capteur_id
                   WHERE c.capteur_id = ?
                   ORDER BY m.timestamp DESC LIMIT 1""",
                (capteur_id,)
            )
            sensor_result = cursor.fetchone()
            conn.close()
            
            if sensor_result:
                type_capteur = sensor_result[0]
                current_value = sensor_result[1] if sensor_result[1] else 0
                type_mesure = sensor_result[2] if sensor_result[2] else "unknown"
                
                print(f"📊 Sensor data: type={type_capteur}, value={current_value}, mesure={type_mesure}")
                
                # Import validation functions
                from fsm_engine import generate_corrected_sensor_value, validate_sensor_with_ai
                
                # Generate corrected value
                corrected_value = generate_corrected_sensor_value(type_capteur, current_value)
                print(f"📈 Generated corrected value: {corrected_value} (original: {current_value})")
                
                # Validate with AI
                is_valid, ai_report = validate_sensor_with_ai(
                    temp_value=corrected_value,
                    original_value=current_value,
                    type_capteur=type_capteur,
                    type_mesure=type_mesure
                )
                
                validation_data = {
                    'is_valid': is_valid,
                    'ai_report': ai_report,
                    'temp_value': corrected_value,
                    'original_value': current_value,
                    'type_capteur': type_capteur,
                    'type_mesure': type_mesure
                }
                
                print(f"✅ Generated validation data: is_valid={is_valid}")
            else:
                conn.close()
                print(f"❌ No sensor data found for capteur {capteur_id}")
                raise HTTPException(status_code=400, detail="No sensor measurement data found")
        
        # Extract validation results
        is_valid = validation_data.get('is_valid', False)
        ai_report = validation_data.get('ai_report', 'Unable to generate report')
        
        print(f"🤖 AI Decision: is_valid={is_valid}")
        print(f"📝 AI Report: {ai_report}")
        
        # Simulate AI thinking (3 seconds delay)
        print("💭 AI thinking...")
        time.sleep(3)
        print("✅ AI thinking complete")
        
        # Auto-transition based on AI decision
        context = {
            'intervention_id': intervention_id_int,
            'is_valid': is_valid,
            'ai_report': ai_report
        }
        
        if is_valid:
            # Valid -> move to TERMINÉ
            print(f"✅ Triggering auto_terminate")
            new_state = fsm.trigger('auto_terminate', context)
            print(f"✅ New state: {new_state}")
            
            # Clear sensor cache so it reloads from DB with new status
            fsm_manager.clear_sensor_cache(capteur_id)
            print(f"🧹 Cleared FSM cache for sensor {capteur_id}")
            
            return {
                "success": True,
                "decision": "ACCEPTED ✅",
                "new_state": new_state,
                "ai_report": ai_report,
                "message": "AI validation passed. Intervention completed."
            }
        else:
            # Invalid -> move back to DEMANDE
            print(f"❌ Triggering auto_reject")
            new_state = fsm.trigger('auto_reject', context)
            print(f"📍 New state: {new_state}")
            
            # Clear sensor cache so it reloads from DB
            fsm_manager.clear_sensor_cache(capteur_id)
            print(f"🧹 Cleared FSM cache for sensor {capteur_id}")
            
            return {
                "success": True,
                "decision": "REJECTED ❌",
                "new_state": new_state,
                "ai_report": ai_report,
                "message": "AI validation failed. Returning to demand."
            }
    
    except HTTPException:
        raise
    except InvalidTransitionError as e:
        print(f"❌ InvalidTransitionError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
#
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

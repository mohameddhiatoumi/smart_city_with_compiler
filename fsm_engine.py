"""
Finite State Machine Engine for Neo-Sousse 2030
Implements the correct sensor, intervention, and vehicle FSMs based on handmade diagrams
"""

from enum import Enum
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import json
import time


class FSMError(Exception):
    """Base exception for FSM-related errors"""
    pass


class InvalidTransitionError(FSMError):
    """Raised when attempting an invalid state transition"""
    pass


@dataclass
class Transition:
    """Represents a state transition"""
    from_state: str
    to_state: str
    event: str
    condition: Optional[Callable] = None
    action: Optional[Callable] = None
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if transition can be executed given the context"""
        if self.condition is None:
            return True
        return self.condition(context)
    
    def execute_action(self, context: Dict[str, Any]) -> None:
        """Execute the transition action if defined"""
        if self.action:
            self.action(context)


class StateMachine:
    """Generic Finite State Machine"""
    
    def __init__(self, name: str, initial_state: str):
        self.name = name
        self.initial_state = initial_state
        self.current_state = initial_state
        self.states: List[str] = [initial_state]
        self.transitions: List[Transition] = []
        self.history: List[Dict[str, Any]] = []
        
    def add_state(self, state: str) -> None:
        """Add a new state to the machine"""
        if state not in self.states:
            self.states.append(state)
    
    def add_transition(self, from_state: str, to_state: str, event: str,
                      condition: Optional[Callable] = None,
                      action: Optional[Callable] = None) -> None:
        """Add a transition between states"""
        self.add_state(from_state)
        self.add_state(to_state)
        
        transition = Transition(from_state, to_state, event, condition, action)
        self.transitions.append(transition)
    
    def get_valid_transitions(self, context: Dict[str, Any] = None) -> List[Transition]:
        """Get all valid transitions from current state"""
        if context is None:
            context = {}
            
        valid = []
        for trans in self.transitions:
            if trans.from_state == self.current_state:
                if trans.can_execute(context):
                    valid.append(trans)
        return valid
    
    def trigger(self, event: str, context: Dict[str, Any] = None) -> str:
        """Trigger an event and transition to new state"""
        if context is None:
            context = {}
        
        # Find matching transition
        matching_trans = None
        for trans in self.transitions:
            if trans.from_state == self.current_state and trans.event == event:
                if trans.can_execute(context):
                    matching_trans = trans
                    break
        
        if matching_trans is None:
            valid_events = [t.event for t in self.get_valid_transitions(context)]
            raise InvalidTransitionError(
                f"Cannot trigger '{event}' from state '{self.current_state}'. "
                f"Valid events: {valid_events}"
            )
        
        # Record history
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'from_state': self.current_state,
            'to_state': matching_trans.to_state,
            'event': event,
            'context': context.copy()
        })
        
        # Execute action
        matching_trans.execute_action(context)
        
        # Change state
        old_state = self.current_state
        self.current_state = matching_trans.to_state
        
        return self.current_state
    
    def get_state_diagram(self) -> str:
        """Generate a textual representation of the FSM"""
        lines = [f"\n=== {self.name} FSM ==="]
        lines.append(f"Current State: {self.current_state}")
        lines.append(f"States: {', '.join(self.states)}")
        lines.append("\nTransitions:")
        
        for trans in self.transitions:
            lines.append(f"  {trans.from_state} --[{trans.event}]--> {trans.to_state}")
        
        return "\n".join(lines)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_corrected_sensor_value(type_capteur: str, current_value: float) -> float:
    """Generate a corrected sensor value based on type"""
    import random
    
    if type_capteur == 'air':
        return round(random.uniform(25, 45), 2)
    elif type_capteur == 'bruit':
        return round(random.uniform(50, 65), 2)
    elif type_capteur == 'trafic':
        return round(random.uniform(150, 400), 2)
    else:
        return round(current_value * 0.95, 2)


def validate_sensor_with_ai(temp_value: float, original_value: float, type_capteur: str, type_mesure: str) -> tuple:
    """AI validation with human-readable report"""
    
    if temp_value is None:
        return False, "❌ Cannot validate: no corrected value available"
    
    is_valid = True
    reasons = []
    
    if type_capteur == 'air':
        if 10 <= temp_value <= 200:
            reasons.append(f"✅ Air quality value ({temp_value}) is within normal range")
        else:
            reasons.append(f"❌ Air quality value ({temp_value}) exceeds normal range")
            is_valid = False
    
    elif type_capteur == 'bruit':
        if 30 <= temp_value <= 90:
            reasons.append(f"✅ Noise level ({temp_value} dB) is acceptable")
        else:
            reasons.append(f"❌ Noise level ({temp_value} dB) is abnormal")
            is_valid = False
    
    elif type_capteur == 'trafic':
        if 0 <= temp_value <= 10000:
            reasons.append(f"✅ Traffic count ({int(temp_value)} vehicles) is reasonable")
        else:
            reasons.append(f"❌ Traffic count is unusually high")
            is_valid = False
    
    if original_value and original_value != 0:
        change_percent = abs(temp_value - original_value) / abs(original_value) * 100
        if change_percent < 300:
            reasons.append(f"✅ Correction is reasonable ({change_percent:.1f}% change)")
        else:
            reasons.append(f"⚠️ Large correction ({change_percent:.1f}% change) - but acceptable")
    
    report = "🤖 AI Validation Report:\n"
    report += f"Sensor Type: {type_capteur}\n"
    report += f"Measurement Type: {type_mesure}\n"
    report += f"Original Value: {original_value}\n"
    report += f"Corrected Value: {temp_value}\n\n"
    report += "Validation Results:\n"
    report += "\n".join(reasons)
    report += f"\n\n{'✅ VALIDATION PASSED - Sensor maintenance approved!' if is_valid else '❌ VALIDATION FAILED - Please retry'}"
    
    return is_valid, report
# ============================================================================
# SENSOR LIFECYCLE FSM - CORRECTED FROM HANDMADE DIAGRAM
# ============================================================================

def create_sensor_fsm(db_path: str, capteur_id: str) -> StateMachine:
    """Create a sensor lifecycle FSM with correct transitions"""
    
    def update_capteur_status(context: Dict[str, Any]) -> None:
        """Update sensor status in database"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE capteurs SET statut = ? WHERE capteur_id = ?",
                (context['new_status'], context['capteur_id'])
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating capteur status: {e}")
    
    fsm = StateMachine(name=f"Capteur_{capteur_id}", initial_state="inactif")
    
    # Add all states
    states = ["inactif", "actif", "signale", "en_maintenance", "hors_service"]
    for state in states:
        fsm.add_state(state)
    
    # INACTIF transitions
    fsm.add_transition("inactif", "actif", "installation",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'actif'}))
    fsm.add_transition("inactif", "hors_service", "panne_critique",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'hors_service'}))
    
    # ACTIF transitions
    fsm.add_transition("actif", "signale", "détection_anomalie",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'signale'}))
    fsm.add_transition("actif", "hors_service", "panne_critique",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'hors_service'}))
    
    # SIGNALÉ transitions
    fsm.add_transition("signale", "hors_service", "panne_critique",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'hors_service'}))
    fsm.add_transition("signale", "en_maintenance", "panne_reparable",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'en_maintenance'}))
    fsm.add_transition("signale", "actif", "réparation",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'actif'}))
    
    # EN_MAINTENANCE transitions
    fsm.add_transition("en_maintenance", "hors_service", "panne_critique",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'hors_service'}))
    fsm.add_transition("en_maintenance", "actif", "réparation",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'actif'}))
    
    # HORS_SERVICE transitions
    fsm.add_transition("hors_service", "inactif", "installation",
                      action=lambda ctx: update_capteur_status({**ctx, 'new_status': 'inactif'}))
    
    return fsm


# ============================================================================
# INTERVENTION WORKFLOW FSM - CORRECTED FROM HANDMADE DIAGRAM
# ============================================================================

def create_intervention_fsm(db_path: str, intervention_id: int) -> StateMachine:
    """Create an intervention workflow FSM with correct transitions"""
    
    def update_intervention_status(context: Dict[str, Any]) -> None:
        """Update intervention status in database"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            updates = ["statut = ?"]
            params = [context['new_status']]
            
            if 'technicien1_id' in context:
                updates.append("technicien1_id = ?")
                params.append(context['technicien1_id'])
            
            if 'technicien2_id' in context:
                updates.append("technicien2_id = ?")
                params.append(context['technicien2_id'])
            
            if 'validation_ia' in context:
                updates.append("validation_ia = ?")
                params.append(context['validation_ia'])
            
            if 'ai_report' in context:
                updates.append("description = ?")
                params.append(context['ai_report'])
            
            if context['new_status'] == 'termine':
                updates.append("date_terminaison = datetime('now')")
            
            params.append(context['intervention_id'])
            
            query = f"UPDATE interventions SET {', '.join(updates)} WHERE intervention_id = ?"
            cursor.execute(query, params)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating intervention status: {e}")
    
    def generate_temp_value(context: Dict[str, Any]) -> None:
        """Generate corrected sensor value and store temporarily"""
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            print(f"\n🔍 generate_temp_value called for intervention {context['intervention_id']}")
            
            # Get sensor info
            cursor.execute(
                """SELECT c.capteur_id, c.type_capteur, m.valeur, m.type_mesure, m.mesure_id
                FROM interventions i
                JOIN capteurs c ON i.capteur_id = c.capteur_id
                LEFT JOIN mesures m ON c.capteur_id = m.capteur_id
                WHERE i.intervention_id = ?
                ORDER BY m.timestamp DESC LIMIT 1""",
                (context['intervention_id'],)
            )
            result = cursor.fetchone()
            
            if result:
                capteur_id = result[0]
                type_capteur = result[1]
                current_value = result[2] if result[2] else 0
                type_mesure = result[3] if result[3] else "unknown"
                
                # Generate corrected value
                corrected_value = generate_corrected_sensor_value(type_capteur, current_value)
                
                print(f"📊 Generated corrected value: {corrected_value} (was {current_value})")
                
                # Store in intervention description as JSON
                temp_data = {
                    'temp_value': corrected_value,
                    'original_value': current_value,
                    'type_capteur': type_capteur,
                    'type_mesure': type_mesure,
                    'generated_at': datetime.now().isoformat()
                }
                
                temp_json = json.dumps(temp_data)
                print(f"💾 Storing temp data: {temp_json}")
                
                cursor.execute(
                    "UPDATE interventions SET description = ? WHERE intervention_id = ?",
                    (temp_json, context['intervention_id'])
                )
                conn.commit()
                print(f"✅ Temp value stored")
                
                context['temp_value'] = corrected_value
            else:
                print(f"⚠️ No sensor data found for intervention {context['intervention_id']}")
            
            conn.close()
        except Exception as e:
            print(f"❌ Error generating temp value: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def ai_validate_sensor(context: Dict[str, Any]) -> None:
        """AI validates the temp value and generates report"""
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            print(f"\n🔍 ai_validate_sensor called for intervention {context['intervention_id']}")
            
            # Get temp data from intervention
            cursor.execute(
                "SELECT capteur_id, description FROM interventions WHERE intervention_id = ?",
                (context['intervention_id'],)
            )
            result = cursor.fetchone()
            
            if not result:
                print(f"❌ Intervention {context['intervention_id']} not found")
                return
            
            capteur_id = result[0]
            description_json = result[1]
            
            print(f"📋 Current description: {description_json}")
            
            # Parse temp data
            temp_data = {}
            if description_json:
                try:
                    temp_data = json.loads(description_json)
                    print(f"✅ Parsed temp data: {temp_data}")
                except json.JSONDecodeError:
                    print(f"⚠️ Could not parse existing description as JSON, creating new")
                    temp_data = {}
            
            temp_value = temp_data.get('temp_value')
            original_value = temp_data.get('original_value')
            type_capteur = temp_data.get('type_capteur')
            type_mesure = temp_data.get('type_mesure')
            
            print(f"📊 Values: temp={temp_value}, original={original_value}, type={type_capteur}")
            
            # AI Validation
            is_valid, ai_report = validate_sensor_with_ai(
                temp_value=temp_value,
                original_value=original_value,
                type_capteur=type_capteur,
                type_mesure=type_mesure
            )
            
            print(f"🤖 AI Decision: is_valid={is_valid}")
            
            # Store AI report
            validation_data = {
                'is_valid': is_valid,
                'ai_report': ai_report,
                'temp_value': temp_value,
                'original_value': original_value,
                'validated_at': datetime.now().isoformat()
            }
            
            validation_json = json.dumps(validation_data)
            print(f"💾 Storing validation data: {validation_json}")
            
            # Update intervention with AI report
            cursor.execute(
                "UPDATE interventions SET description = ?, validation_ia = ? WHERE intervention_id = ?",
                (validation_json, 1 if is_valid else 0, context['intervention_id'])
            )
            
            # If valid, update sensor value using subquery
            if is_valid:
                cursor.execute(
                    """UPDATE mesures SET valeur = ? 
                    WHERE mesure_id = (
                        SELECT mesure_id FROM mesures 
                        WHERE capteur_id = ? 
                        ORDER BY timestamp DESC LIMIT 1
                    )""",
                    (temp_value, capteur_id)
                )
                print(f"✅ Updated sensor measurement to {temp_value}")
            
            conn.commit()
            print(f"✅ Intervention updated with validation data")
            
            # Store in context for later use
            context['ai_report'] = ai_report
            context['is_valid'] = is_valid
            context['validation_ia'] = 1 if is_valid else 0
            
        except Exception as e:
            print(f"❌ Error in AI validation: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def update_sensor_to_actif(context: Dict[str, Any]) -> None:
        """Update sensor from en_maintenance to actif"""
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Get capteur_id from intervention
            cursor.execute(
                "SELECT capteur_id FROM interventions WHERE intervention_id = ?",
                (context['intervention_id'],)
            )
            result = cursor.fetchone()
            
            if result:
                capteur_id = result[0]
                print(f"🔄 Updating sensor {capteur_id} from en_maintenance to actif")
                
                # Update sensor status to actif
                cursor.execute(
                    "UPDATE capteurs SET statut = 'actif' WHERE capteur_id = ?",
                    (capteur_id,)
                )
                conn.commit()
                print(f"✅ Sensor {capteur_id} updated to actif")
            
        except Exception as e:
            print(f"Error updating sensor status: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    fsm = StateMachine(name=f"Intervention_{intervention_id}", initial_state="demande")
    
    states = ["demande", "tech1_assigne", "tech2_valide", "ia_valide", "termine"]
    for state in states:
        fsm.add_state(state)
    
    # DEMANDE → TECH1_ASSIGNÉ
    fsm.add_transition("demande", "tech1_assigne", "assigner_tech1",
                      action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'tech1_assigne'}))
    
    # TECH1_ASSIGNÉ → TECH2_VALIDE (generates temp value in background)
    fsm.add_transition("tech1_assigne", "tech2_valide", "valide_tech2",
                      action=lambda ctx: [
                          generate_temp_value(ctx),
                          update_intervention_status({**ctx, 'new_status': 'tech2_valide'})
                      ])
    fsm.add_transition("tech1_assigne", "demande", "rejeter",
                      action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'demande'}))
    
    # TECH2_VALIDE → IA_VALIDE (AI validates in background)
    fsm.add_transition("tech2_valide", "ia_valide", "valide_ia",
                      action=lambda ctx: [
                          ai_validate_sensor(ctx),
                          update_intervention_status({**ctx, 'new_status': 'ia_valide'})
                      ])
    fsm.add_transition("tech2_valide", "demande", "rejeter",
                      action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'demande'}))
    
    # IA_VALIDE → TERMINÉ (updates sensor to actif)
        # IA_VALIDE → TERMINÉ or DEMANDE (auto-decided by AI)
    # If valid -> terminate
    fsm.add_transition("ia_valide", "termine", "auto_terminate",
                      condition=lambda ctx: ctx.get('is_valid', False),
                      action=lambda ctx: [
                          update_sensor_to_actif(ctx),
                          update_intervention_status({**ctx, 'new_status': 'termine', 'validation_ia': 1})
                      ])
    
    # If invalid -> back to demand
    fsm.add_transition("ia_valide", "demande", "auto_reject",
                      condition=lambda ctx: not ctx.get('is_valid', False),
                      action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'demande'}))
    
    return fsm

# ============================================================================
# VEHICLE JOURNEY FSM - CORRECTED FROM HANDMADE DIAGRAM
# ============================================================================
def create_vehicle_fsm(db_path: str, vehicule_id: str) -> StateMachine:
    """Create a vehicle journey FSM with correct transitions"""
    
    def update_vehicule_status(context: Dict[str, Any]) -> None:
        """Update vehicle status in database"""
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE vehicules SET statut = ? WHERE vehicule_id = ?",
                (context['new_status'], context['vehicule_id'])
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating vehicule status: {e}")
    
    def create_trajet(context: Dict[str, Any]) -> None:
        """Create journey record when vehicle starts"""
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Get current zone from vehicle
            cursor.execute(
                "SELECT zone_actuelle_id FROM vehicules WHERE vehicule_id = ?",
                (context['vehicule_id'],)
            )
            result = cursor.fetchone()
            zone_depart_id = result[0] if result else None
            
            if zone_depart_id:
                cursor.execute(
                    """INSERT INTO trajets (vehicule_id, zone_depart_id, timestamp_depart, statut)
                    VALUES (?, ?, datetime('now'), 'en_cours')""",
                    (context['vehicule_id'], zone_depart_id)
                )
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Error creating trajet: {e}")
    
    def complete_trajet(context: Dict[str, Any]) -> None:
        """Complete journey record when vehicle arrives"""
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Get current zone as arrival zone
            cursor.execute(
                "SELECT zone_actuelle_id FROM vehicules WHERE vehicule_id = ?",
                (context['vehicule_id'],)
            )
            result = cursor.fetchone()
            zone_arrivee_id = result[0] if result else None
            
            if zone_arrivee_id:
                cursor.execute(
                    """UPDATE trajets 
                    SET zone_arrivee_id = ?,
                        timestamp_arrivee = datetime('now'),
                        statut = 'termine'
                    WHERE vehicule_id = ? 
                    AND timestamp_arrivee IS NULL
                    ORDER BY timestamp_depart DESC
                    LIMIT 1""",
                    (zone_arrivee_id, context['vehicule_id'])
                )
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Error completing trajet: {e}")
    
    fsm = StateMachine(name=f"Vehicule_{vehicule_id}", initial_state="stationne")
    
    # Add all states
    states = ["stationne", "en_route", "en_panne", "arrive"]
    for state in states:
        fsm.add_state(state)
    
    # STATIONNE transitions
    fsm.add_transition("stationne", "en_route", "démarrer",
                      action=lambda ctx: [
                          update_vehicule_status({**ctx, 'new_status': 'en_route'}),
                          create_trajet(ctx)
                      ])
    
    # EN_ROUTE transitions
    fsm.add_transition("en_route", "arrive", "arrivée",
                      action=lambda ctx: [
                          update_vehicule_status({**ctx, 'new_status': 'arrive'}),
                          complete_trajet(ctx)
                      ])
    fsm.add_transition("en_route", "en_panne", "panne",
                      action=lambda ctx: update_vehicule_status({**ctx, 'new_status': 'en_panne'}))
    
    # EN_PANNE transitions
    fsm.add_transition("en_panne", "stationne", "réparé",
                      action=lambda ctx: update_vehicule_status({**ctx, 'new_status': 'stationne'}))
    
    return fsm



# ============================================================================
# FSM MANAGER
# ============================================================================

class FSMManager:
    """Manages all FSM instances for the application"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.sensor_fsms: Dict[str, StateMachine] = {}
        self.intervention_fsms: Dict[int, StateMachine] = {}
        self.vehicle_fsms: Dict[str, StateMachine] = {}
    def clear_sensor_cache(self, capteur_id: str) -> None:
        """Clear cached FSM for a sensor to force reload from DB"""
        if capteur_id in self.sensor_fsms:
            del self.sensor_fsms[capteur_id]
            print(f"🧹 Cleared FSM cache for sensor {capteur_id}")
    
    def clear_intervention_cache(self, intervention_id: int) -> None:
        """Clear cached FSM for an intervention to force reload from DB"""
        if intervention_id in self.intervention_fsms:
            del self.intervention_fsms[intervention_id]
            print(f"🧹 Cleared FSM cache for intervention {intervention_id}")
    
    def get_sensor_fsm(self, capteur_id: str, current_status: str = None) -> StateMachine:
        """Get or create FSM for a sensor"""
        if capteur_id not in self.sensor_fsms:
            fsm = create_sensor_fsm(self.db_path, capteur_id)
            
            if current_status:
                fsm.current_state = current_status
            else:
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT statut FROM capteurs WHERE capteur_id = ?", (capteur_id,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        fsm.current_state = result['statut']
                except Exception as e:
                    print(f"Error fetching capteur status: {e}")
            
            self.sensor_fsms[capteur_id] = fsm
        
        return self.sensor_fsms[capteur_id]
    
    def get_intervention_fsm(self, intervention_id: int, current_status: str = None) -> StateMachine:
        """Get or create FSM for an intervention"""
        if intervention_id not in self.intervention_fsms:
            fsm = create_intervention_fsm(self.db_path, intervention_id)
            
            if current_status:
                fsm.current_state = current_status
            else:
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT statut FROM interventions WHERE intervention_id = ?", (intervention_id,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        fsm.current_state = result['statut']
                except Exception as e:
                    print(f"Error fetching intervention status: {e}")
            
            self.intervention_fsms[intervention_id] = fsm
        
        return self.intervention_fsms[intervention_id]
    
    def get_vehicle_fsm(self, vehicule_id: str, current_status: str = None) -> StateMachine:
        """Get or create FSM for a vehicle"""
        if vehicule_id not in self.vehicle_fsms:
            fsm = create_vehicle_fsm(self.db_path, vehicule_id)
            
            if current_status:
                fsm.current_state = current_status
            else:
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT statut FROM vehicules WHERE vehicule_id = ?", (vehicule_id,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        fsm.current_state = result['statut']
                except Exception as e:
                    print(f"Error fetching vehicule status: {e}")
            
            self.vehicle_fsms[vehicule_id] = fsm
        
        return self.vehicle_fsms[vehicule_id]
    
    def trigger_sensor_event(self, capteur_id: str, event: str, context: Dict[str, Any] = None) -> str:
        """Trigger event on sensor FSM"""
        if context is None:
            context = {}
        context['capteur_id'] = capteur_id
        
        fsm = self.get_sensor_fsm(capteur_id)
        return fsm.trigger(event, context)
    
    def trigger_intervention_event(self, intervention_id: int, event: str, context: Dict[str, Any] = None) -> str:
        """Trigger event on intervention FSM"""
        if context is None:
            context = {}
        context['intervention_id'] = intervention_id
        
        fsm = self.get_intervention_fsm(intervention_id)
        return fsm.trigger(event, context)
    
    def trigger_vehicle_event(self, vehicule_id: str, event: str, context: Dict[str, Any] = None) -> str:
        """Trigger event on vehicle FSM"""
        if context is None:
            context = {}
        context['vehicule_id'] = vehicule_id
        
        fsm = self.get_vehicle_fsm(vehicule_id)
        return fsm.trigger(event, context)
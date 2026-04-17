"""
Finite State Machine Engine for Neo-Sousse 2030
Implements sensor lifecycle, intervention workflow, and vehicle journey FSMs
"""

from enum import Enum
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import json


class FSMError(Exception):
    """Base exception for FSM-related errors"""
    pass


class InvalidTransitionError(FSMError):
    """Raised when attempting an invalid state transition"""
    pass


class InvalidStateError(FSMError):
    """Raised when current state is invalid"""
    pass


@dataclass
class Transition:
    """Represents a state transition"""
    from_state: str
    to_state: str
    event: str
    condition: Optional[Callable] = None  # Optional guard condition
    action: Optional[Callable] = None     # Optional action to execute
    
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
        # Ensure states exist
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
    
    def can_transition(self, event: str, context: Dict[str, Any] = None) -> bool:
        """Check if a transition is possible for given event"""
        if context is None:
            context = {}
            
        for trans in self.get_valid_transitions(context):
            if trans.event == event:
                return True
        return False
    
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
    
    def reset(self) -> None:
        """Reset to initial state"""
        self.current_state = self.initial_state
        self.history.clear()
    
    def get_state_diagram(self) -> str:
        """Generate a textual representation of the FSM"""
        lines = [f"=== {self.name} FSM ==="]
        lines.append(f"Current State: {self.current_state}")
        lines.append(f"States: {', '.join(self.states)}")
        lines.append("\nTransitions:")
        
        for trans in self.transitions:
            guard = " [guarded]" if trans.condition else ""
            action = " (with action)" if trans.action else ""
            lines.append(f"  {trans.from_state} --[{trans.event}]--> {trans.to_state}{guard}{action}")
        
        return "\n".join(lines)


# ============================================================================
# SENSOR LIFECYCLE FSM
# ============================================================================

class SensorState(str, Enum):
    INACTIF = "inactif"
    ACTIF = "actif"
    SIGNALE = "signale"
    EN_MAINTENANCE = "en_maintenance"
    HORS_SERVICE = "hors_service"


class SensorEvent(str, Enum):
    INSTALLER = "installer"
    ACTIVER = "activer"
    DETECTER_ANOMALIE = "detecter_anomalie"
    COMMENCER_REPARATION = "commencer_reparation"
    TERMINER_REPARATION = "terminer_reparation"
    DECLARER_HORS_SERVICE = "declarer_hors_service"
    REACTIVER = "reactiver"


def create_sensor_fsm(db_path: str, capteur_id: int) -> StateMachine:
    """Create a sensor lifecycle FSM"""
    
    def update_sensor_status(context: Dict[str, Any]) -> None:
        """Update sensor status in database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE capteurs SET statut = ? WHERE capteur_id = ?",
            (context['new_status'], context['capteur_id'])
        )
        conn.commit()
        conn.close()
    
    def create_intervention(context: Dict[str, Any]) -> None:
        """Create intervention request when sensor is flagged"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO interventions (capteur_id, statut, date_demande)
               VALUES (?, 'demande', datetime('now'))""",
            (context['capteur_id'],)
        )
        conn.commit()
        conn.close()
    
    def check_error_threshold(context: Dict[str, Any]) -> bool:
        """Check if error rate exceeds threshold"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT taux_erreur FROM capteurs WHERE capteur_id = ?",
            (context['capteur_id'],)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0] > 15.0  # 15% threshold
        return False
    
    # Create FSM
    fsm = StateMachine(name=f"Sensor_{capteur_id}", initial_state=SensorState.INACTIF)
    
    # Add all states
    for state in SensorState:
        fsm.add_state(state.value)
    
    # Define transitions
    # INACTIF -> ACTIF (installation and activation)
    fsm.add_transition(
        SensorState.INACTIF, SensorState.ACTIF, SensorEvent.ACTIVER,
        action=lambda ctx: update_sensor_status({**ctx, 'new_status': 'actif'})
    )
    
    # ACTIF -> SIGNALE (anomaly detected)
    fsm.add_transition(
        SensorState.ACTIF, SensorState.SIGNALE, SensorEvent.DETECTER_ANOMALIE,
        condition=check_error_threshold,
        action=lambda ctx: [
            update_sensor_status({**ctx, 'new_status': 'signale'}),
            create_intervention(ctx)
        ]
    )
    
    # SIGNALE -> EN_MAINTENANCE (repair started)
    fsm.add_transition(
        SensorState.SIGNALE, SensorState.EN_MAINTENANCE, SensorEvent.COMMENCER_REPARATION,
        action=lambda ctx: update_sensor_status({**ctx, 'new_status': 'en_maintenance'})
    )
    
    # EN_MAINTENANCE -> ACTIF (repair successful)
    fsm.add_transition(
        SensorState.EN_MAINTENANCE, SensorState.ACTIF, SensorEvent.TERMINER_REPARATION,
        action=lambda ctx: update_sensor_status({**ctx, 'new_status': 'actif'})
    )
    
    # EN_MAINTENANCE -> HORS_SERVICE (irreparable)
    fsm.add_transition(
        SensorState.EN_MAINTENANCE, SensorState.HORS_SERVICE, SensorEvent.DECLARER_HORS_SERVICE,
        action=lambda ctx: update_sensor_status({**ctx, 'new_status': 'hors_service'})
    )
    
    # SIGNALE -> ACTIF (false alarm, reactivate)
    fsm.add_transition(
        SensorState.SIGNALE, SensorState.ACTIF, SensorEvent.REACTIVER,
        action=lambda ctx: update_sensor_status({**ctx, 'new_status': 'actif'})
    )
    
    # ACTIF -> HORS_SERVICE (critical failure)
    fsm.add_transition(
        SensorState.ACTIF, SensorState.HORS_SERVICE, SensorEvent.DECLARER_HORS_SERVICE,
        action=lambda ctx: update_sensor_status({**ctx, 'new_status': 'hors_service'})
    )
    
    return fsm


# ============================================================================
# INTERVENTION WORKFLOW FSM
# ============================================================================

class InterventionState(str, Enum):
    DEMANDE = "demande"
    TECH1_ASSIGNE = "tech1_assigne"
    TECH2_VALIDE = "tech2_valide"
    IA_VALIDE = "ia_valide"
    TERMINE = "termine"
    ANNULE = "annule"


class InterventionEvent(str, Enum):
    ASSIGNER_TECH1 = "assigner_tech1"
    TECH2_VALIDER = "tech2_valider"
    IA_VALIDER = "ia_valider"
    TERMINER = "terminer"
    ANNULER = "annuler"


def create_intervention_fsm(db_path: str, intervention_id: int) -> StateMachine:
    """Create an intervention workflow FSM"""
    
    def update_intervention_status(context: Dict[str, Any]) -> None:
        """Update intervention status in database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        updates = ["statut = ?"]
        params = [context['new_status']]
        
        if 'tech1_id' in context:
            updates.append("technicien1_id = ?")
            params.append(context['tech1_id'])
        
        if 'tech2_id' in context:
            updates.append("technicien2_id = ?")
            params.append(context['tech2_id'])
        
        if 'validation_ia' in context:
            updates.append("validation_ia = ?")
            params.append(context['validation_ia'])
        
        if context['new_status'] == 'termine':
            updates.append("date_terminaison = datetime('now')")
        
        params.append(context['intervention_id'])
        
        query = f"UPDATE interventions SET {', '.join(updates)} WHERE intervention_id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
    
    def check_technician_available(context: Dict[str, Any]) -> bool:
        """Check if assigned technician is available"""
        if 'tech1_id' not in context and 'tech2_id' not in context:
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        tech_id = context.get('tech1_id') or context.get('tech2_id')
        cursor.execute(
            "SELECT disponible FROM techniciens WHERE technicien_id = ?",
            (tech_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return result[0] == 1 if result else False
    
    # Create FSM
    fsm = StateMachine(name=f"Intervention_{intervention_id}", initial_state=InterventionState.DEMANDE)
    
    # Add all states
    for state in InterventionState:
        fsm.add_state(state.value)
    
    # Define transitions
    # DEMANDE -> TECH1_ASSIGNE
    fsm.add_transition(
        InterventionState.DEMANDE, InterventionState.TECH1_ASSIGNE, 
        InterventionEvent.ASSIGNER_TECH1,
        condition=check_technician_available,
        action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'tech1_assigne'})
    )
    
    # TECH1_ASSIGNE -> TECH2_VALIDE
    fsm.add_transition(
        InterventionState.TECH1_ASSIGNE, InterventionState.TECH2_VALIDE,
        InterventionEvent.TECH2_VALIDER,
        action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'tech2_valide'})
    )
    
    # TECH2_VALIDE -> IA_VALIDE
    fsm.add_transition(
        InterventionState.TECH2_VALIDE, InterventionState.IA_VALIDE,
        InterventionEvent.IA_VALIDER,
        action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'ia_valide'})
    )
    
    # IA_VALIDE -> TERMINE
    fsm.add_transition(
        InterventionState.IA_VALIDE, InterventionState.TERMINE,
        InterventionEvent.TERMINER,
        action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'termine'})
    )
    
    # Any state -> ANNULE (except TERMINE)
    for state in [InterventionState.DEMANDE, InterventionState.TECH1_ASSIGNE, 
                  InterventionState.TECH2_VALIDE, InterventionState.IA_VALIDE]:
        fsm.add_transition(
            state, InterventionState.ANNULE, InterventionEvent.ANNULER,
            action=lambda ctx: update_intervention_status({**ctx, 'new_status': 'annule'})
        )
    
    return fsm


# ============================================================================
# VEHICLE JOURNEY FSM
# ============================================================================

class VehicleState(str, Enum):
    STATIONNE = "stationne"
    EN_ROUTE = "en_route"
    EN_PANNE = "en_panne"
    ARRIVE = "arrive"


class VehicleEvent(str, Enum):
    DEMARRER = "demarrer"
    TOMBER_EN_PANNE = "tomber_en_panne"
    REPARER = "reparer"
    ARRIVER = "arriver"
    STATIONNER = "stationner"


def create_vehicle_fsm(db_path: str, vehicule_id: int) -> StateMachine:
    """Create a vehicle journey FSM"""
    
    def update_vehicle_status(context: Dict[str, Any]) -> None:
        """Update vehicle status in database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE vehicules SET statut = ? WHERE vehicule_id = ?",
            (context['new_status'], context['vehicule_id'])
        )
        conn.commit()
        conn.close()
    
    def create_trajet(context: Dict[str, Any]) -> None:
        """Create journey record when vehicle starts"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO trajets (vehicule_id, zone_depart_id, timestamp_depart)
               VALUES (?, ?, datetime('now'))""",
            (context['vehicule_id'], context.get('zone_depart_id'))
        )
        conn.commit()
        conn.close()
    
    def complete_trajet(context: Dict[str, Any]) -> None:
        """Complete journey record when vehicle arrives"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the latest incomplete journey
        cursor.execute(
            """UPDATE trajets 
               SET zone_arrivee_id = ?, 
                   timestamp_arrivee = datetime('now'),
                   distance_km = ?,
                   economie_co2 = ?
               WHERE vehicule_id = ? 
               AND timestamp_arrivee IS NULL
               ORDER BY timestamp_depart DESC
               LIMIT 1""",
            (context.get('zone_arrivee_id'), context.get('distance_km', 0),
             context.get('economie_co2', 0), context['vehicule_id'])
        )
        conn.commit()
        conn.close()
    
    # Create FSM
    fsm = StateMachine(name=f"Vehicle_{vehicule_id}", initial_state=VehicleState.STATIONNE)
    
    # Add all states
    for state in VehicleState:
        fsm.add_state(state.value)
    
    # Define transitions
    # STATIONNE -> EN_ROUTE
    fsm.add_transition(
        VehicleState.STATIONNE, VehicleState.EN_ROUTE, VehicleEvent.DEMARRER,
        action=lambda ctx: [
            update_vehicle_status({**ctx, 'new_status': 'en_route'}),
            create_trajet(ctx)
        ]
    )
    
    # EN_ROUTE -> EN_PANNE
    fsm.add_transition(
        VehicleState.EN_ROUTE, VehicleState.EN_PANNE, VehicleEvent.TOMBER_EN_PANNE,
        action=lambda ctx: update_vehicle_status({**ctx, 'new_status': 'en_panne'})
    )
    
    # EN_PANNE -> EN_ROUTE
    fsm.add_transition(
        VehicleState.EN_PANNE, VehicleState.EN_ROUTE, VehicleEvent.REPARER,
        action=lambda ctx: update_vehicle_status({**ctx, 'new_status': 'en_route'})
    )
    
    # EN_ROUTE -> ARRIVE
    fsm.add_transition(
        VehicleState.EN_ROUTE, VehicleState.ARRIVE, VehicleEvent.ARRIVER,
        action=lambda ctx: [
            update_vehicle_status({**ctx, 'new_status': 'arrive'}),
            complete_trajet(ctx)
        ]
    )
    
    # ARRIVE -> STATIONNE
    fsm.add_transition(
        VehicleState.ARRIVE, VehicleState.STATIONNE, VehicleEvent.STATIONNER,
        action=lambda ctx: update_vehicle_status({**ctx, 'new_status': 'stationne'})
    )
    
    return fsm


# ============================================================================
# FSM MANAGER
# ============================================================================

class FSMManager:
    """Manages all FSM instances for the application"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.sensor_fsms: Dict[int, StateMachine] = {}
        self.intervention_fsms: Dict[int, StateMachine] = {}
        self.vehicle_fsms: Dict[int, StateMachine] = {}
    
    def get_sensor_fsm(self, capteur_id: int, current_status: str = None) -> StateMachine:
        """Get or create FSM for a sensor"""
        if capteur_id not in self.sensor_fsms:
            fsm = create_sensor_fsm(self.db_path, capteur_id)
            
            # Set current state from database if provided
            if current_status:
                fsm.current_state = current_status
            else:
                # Fetch from database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT statut FROM capteurs WHERE capteur_id = ?", (capteur_id,))
                result = cursor.fetchone()
                conn.close()
                if result:
                    fsm.current_state = result[0]
            
            self.sensor_fsms[capteur_id] = fsm
        
        return self.sensor_fsms[capteur_id]
    
    def get_intervention_fsm(self, intervention_id: int, current_status: str = None) -> StateMachine:
        """Get or create FSM for an intervention"""
        if intervention_id not in self.intervention_fsms:
            fsm = create_intervention_fsm(self.db_path, intervention_id)
            
            if current_status:
                fsm.current_state = current_status
            else:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT statut FROM interventions WHERE intervention_id = ?", (intervention_id,))
                result = cursor.fetchone()
                conn.close()
                if result:
                    fsm.current_state = result[0]
            
            self.intervention_fsms[intervention_id] = fsm
        
        return self.intervention_fsms[intervention_id]
    
    def get_vehicle_fsm(self, vehicule_id: int, current_status: str = None) -> StateMachine:
        """Get or create FSM for a vehicle"""
        if vehicule_id not in self.vehicle_fsms:
            fsm = create_vehicle_fsm(self.db_path, vehicule_id)
            
            if current_status:
                fsm.current_state = current_status
            else:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT statut FROM vehicules WHERE vehicule_id = ?", (vehicule_id,))
                result = cursor.fetchone()
                conn.close()
                if result:
                    fsm.current_state = result[0]
            
            self.vehicle_fsms[vehicule_id] = fsm
        
        return self.vehicle_fsms[vehicule_id]
    
    def trigger_sensor_event(self, capteur_id: int, event: str, context: Dict[str, Any] = None) -> str:
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
    
    def trigger_vehicle_event(self, vehicule_id: int, event: str, context: Dict[str, Any] = None) -> str:
        """Trigger event on vehicle FSM"""
        if context is None:
            context = {}
        context['vehicule_id'] = vehicule_id
        
        fsm = self.get_vehicle_fsm(vehicule_id)
        return fsm.trigger(event, context)


if __name__ == "__main__":
    # Demo usage
    print("=== FSM Engine Demo ===\n")
    
    # Create a sensor FSM
    fsm = StateMachine("Demo_Sensor", "inactif")
    fsm.add_transition("inactif", "actif", "activer")
    fsm.add_transition("actif", "signale", "detecter_anomalie")
    fsm.add_transition("signale", "en_maintenance", "reparer")
    
    print(fsm.get_state_diagram())
    print(f"\nCurrent state: {fsm.current_state}")
    
    print("\n--- Triggering events ---")
    print(f"After 'activer': {fsm.trigger('activer')}")
    print(f"After 'detecter_anomalie': {fsm.trigger('detecter_anomalie')}")
    print(f"After 'reparer': {fsm.trigger('reparer')}")
    
    print("\n--- FSM History ---")
    for entry in fsm.history:
        print(f"{entry['timestamp']}: {entry['from_state']} --[{entry['event']}]--> {entry['to_state']}")

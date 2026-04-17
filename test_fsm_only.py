"""
FSM Module Test Suite (no external dependencies)
"""

import sys
from datetime import datetime

# Import FSM modules only
from fsm_engine import (
    FSMManager, StateMachine, 
    SensorState, SensorEvent,
    InterventionState, InterventionEvent,
    VehicleState, VehicleEvent,
    InvalidTransitionError
)


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_fsm_basic():
    """Test basic FSM functionality"""
    print_section("TEST 1: Basic FSM Operations")
    
    # Create simple FSM
    fsm = StateMachine("Test", "state_A")
    fsm.add_transition("state_A", "state_B", "event_1")
    fsm.add_transition("state_B", "state_C", "event_2")
    
    print("Initial state:", fsm.current_state)
    assert fsm.current_state == "state_A", "Initial state should be state_A"
    
    # Test transition
    new_state = fsm.trigger("event_1")
    print(f"After 'event_1': {new_state}")
    assert new_state == "state_B", "Should transition to state_B"
    
    # Test history
    print(f"History entries: {len(fsm.history)}")
    assert len(fsm.history) == 1, "Should have 1 history entry"
    
    print("✓ Basic FSM operations work correctly\n")


def test_fsm_invalid_transition():
    """Test invalid transition handling"""
    print_section("TEST 2: Invalid Transition Handling")
    
    fsm = StateMachine("Test", "state_A")
    fsm.add_transition("state_A", "state_B", "valid_event")
    
    print("Current state:", fsm.current_state)
    
    try:
        fsm.trigger("invalid_event")
        print("✗ Should have raised InvalidTransitionError")
        assert False
    except InvalidTransitionError as e:
        print(f"✓ Correctly caught invalid transition: {e}\n")


def test_sensor_fsm():
    """Test sensor lifecycle FSM"""
    print_section("TEST 3: Sensor Lifecycle FSM")
    
    fsm = StateMachine("Sensor_Test", SensorState.INACTIF)
    
    # Add transitions
    fsm.add_transition(SensorState.INACTIF, SensorState.ACTIF, SensorEvent.ACTIVER)
    fsm.add_transition(SensorState.ACTIF, SensorState.SIGNALE, SensorEvent.DETECTER_ANOMALIE)
    fsm.add_transition(SensorState.SIGNALE, SensorState.EN_MAINTENANCE, SensorEvent.COMMENCER_REPARATION)
    fsm.add_transition(SensorState.EN_MAINTENANCE, SensorState.ACTIF, SensorEvent.TERMINER_REPARATION)
    fsm.add_transition(SensorState.EN_MAINTENANCE, SensorState.HORS_SERVICE, SensorEvent.DECLARER_HORS_SERVICE)
    
    print("Sensor FSM Diagram:")
    print(fsm.get_state_diagram())
    
    # Test lifecycle
    print("\n--- Testing sensor lifecycle ---")
    print(f"Initial: {fsm.current_state}")
    
    fsm.trigger(SensorEvent.ACTIVER)
    print(f"After activation: {fsm.current_state}")
    assert fsm.current_state == SensorState.ACTIF
    
    fsm.trigger(SensorEvent.DETECTER_ANOMALIE)
    print(f"After anomaly detected: {fsm.current_state}")
    assert fsm.current_state == SensorState.SIGNALE
    
    fsm.trigger(SensorEvent.COMMENCER_REPARATION)
    print(f"After repair started: {fsm.current_state}")
    assert fsm.current_state == SensorState.EN_MAINTENANCE
    
    fsm.trigger(SensorEvent.TERMINER_REPARATION)
    print(f"After repair completed: {fsm.current_state}")
    assert fsm.current_state == SensorState.ACTIF
    
    print("\n✓ Sensor FSM lifecycle works correctly\n")


def test_intervention_fsm():
    """Test intervention workflow FSM"""
    print_section("TEST 4: Intervention Workflow FSM")
    
    fsm = StateMachine("Intervention_Test", InterventionState.DEMANDE)
    
    # Add transitions
    fsm.add_transition(InterventionState.DEMANDE, InterventionState.TECH1_ASSIGNE, 
                      InterventionEvent.ASSIGNER_TECH1)
    fsm.add_transition(InterventionState.TECH1_ASSIGNE, InterventionState.TECH2_VALIDE,
                      InterventionEvent.TECH2_VALIDER)
    fsm.add_transition(InterventionState.TECH2_VALIDE, InterventionState.IA_VALIDE,
                      InterventionEvent.IA_VALIDER)
    fsm.add_transition(InterventionState.IA_VALIDE, InterventionState.TERMINE,
                      InterventionEvent.TERMINER)
    
    print("Intervention FSM Diagram:")
    print(fsm.get_state_diagram())
    
    # Test workflow
    print("\n--- Testing intervention workflow ---")
    states = [
        (InterventionEvent.ASSIGNER_TECH1, InterventionState.TECH1_ASSIGNE),
        (InterventionEvent.TECH2_VALIDER, InterventionState.TECH2_VALIDE),
        (InterventionEvent.IA_VALIDER, InterventionState.IA_VALIDE),
        (InterventionEvent.TERMINER, InterventionState.TERMINE)
    ]
    
    for event, expected_state in states:
        fsm.trigger(event)
        print(f"After '{event}': {fsm.current_state}")
        assert fsm.current_state == expected_state
    
    print("\n✓ Intervention FSM workflow works correctly\n")


def test_vehicle_fsm():
    """Test vehicle journey FSM"""
    print_section("TEST 5: Vehicle Journey FSM")
    
    fsm = StateMachine("Vehicle_Test", VehicleState.STATIONNE)
    
    # Add transitions
    fsm.add_transition(VehicleState.STATIONNE, VehicleState.EN_ROUTE, VehicleEvent.DEMARRER)
    fsm.add_transition(VehicleState.EN_ROUTE, VehicleState.EN_PANNE, VehicleEvent.TOMBER_EN_PANNE)
    fsm.add_transition(VehicleState.EN_PANNE, VehicleState.EN_ROUTE, VehicleEvent.REPARER)
    fsm.add_transition(VehicleState.EN_ROUTE, VehicleState.ARRIVE, VehicleEvent.ARRIVER)
    fsm.add_transition(VehicleState.ARRIVE, VehicleState.STATIONNE, VehicleEvent.STATIONNER)
    
    print("Vehicle FSM Diagram:")
    print(fsm.get_state_diagram())
    
    # Test journey with breakdown
    print("\n--- Testing vehicle journey (with breakdown) ---")
    fsm.trigger(VehicleEvent.DEMARRER)
    print(f"Started journey: {fsm.current_state}")
    assert fsm.current_state == VehicleState.EN_ROUTE
    
    fsm.trigger(VehicleEvent.TOMBER_EN_PANNE)
    print(f"Breakdown occurred: {fsm.current_state}")
    assert fsm.current_state == VehicleState.EN_PANNE
    
    fsm.trigger(VehicleEvent.REPARER)
    print(f"Repaired: {fsm.current_state}")
    assert fsm.current_state == VehicleState.EN_ROUTE
    
    fsm.trigger(VehicleEvent.ARRIVER)
    print(f"Arrived: {fsm.current_state}")
    assert fsm.current_state == VehicleState.ARRIVE
    
    fsm.trigger(VehicleEvent.STATIONNER)
    print(f"Parked: {fsm.current_state}")
    assert fsm.current_state == VehicleState.STATIONNE
    
    print("\n✓ Vehicle FSM journey works correctly\n")


def test_fsm_conditions():
    """Test FSM with guard conditions"""
    print_section("TEST 6: FSM Guard Conditions")
    
    fsm = StateMachine("Conditional", "idle")
    
    # Add transition with condition
    def check_temperature(context):
        return context.get('temperature', 0) > 30
    
    fsm.add_transition("idle", "overheated", "check_temp", condition=check_temperature)
    
    # Test with temperature too low
    print("Testing with temperature = 20°C")
    try:
        fsm.trigger("check_temp", {"temperature": 20})
        print("✗ Should not have transitioned")
        assert False
    except InvalidTransitionError:
        print("✓ Correctly blocked transition (temperature too low)")
    
    # Test with temperature high enough
    print("\nTesting with temperature = 35°C")
    fsm.trigger("check_temp", {"temperature": 35})
    print(f"Transitioned to: {fsm.current_state}")
    assert fsm.current_state == "overheated"
    
    print("\n✓ Guard conditions work correctly\n")


def test_fsm_history():
    """Test FSM history tracking"""
    print_section("TEST 7: FSM History Tracking")
    
    fsm = StateMachine("History_Test", "A")
    fsm.add_transition("A", "B", "go_to_B")
    fsm.add_transition("B", "C", "go_to_C")
    fsm.add_transition("C", "A", "go_to_A")
    
    # Make several transitions
    fsm.trigger("go_to_B", {"user": "test"})
    fsm.trigger("go_to_C", {"user": "test"})
    fsm.trigger("go_to_A", {"user": "test"})
    
    print(f"Total history entries: {len(fsm.history)}")
    assert len(fsm.history) == 3
    
    print("\nHistory log:")
    for i, entry in enumerate(fsm.history, 1):
        print(f"  {i}. {entry['from_state']} --[{entry['event']}]--> {entry['to_state']}")
        print(f"     Time: {entry['timestamp']}")
        print(f"     Context: {entry['context']}")
    
    print("\n✓ History tracking works correctly\n")


def test_fsm_actions():
    """Test FSM transition actions"""
    print_section("TEST 8: FSM Transition Actions")
    
    action_log = []
    
    def log_action(context):
        action_log.append(f"Action executed: {context}")
    
    fsm = StateMachine("Action_Test", "idle")
    fsm.add_transition("idle", "active", "activate", action=log_action)
    
    print("Triggering transition with action...")
    fsm.trigger("activate", {"param": "value"})
    
    print(f"Action log entries: {len(action_log)}")
    assert len(action_log) == 1
    print(f"Action logged: {action_log[0]}")
    
    print("\n✓ Transition actions work correctly\n")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  NEO-SOUSSE 2030 - FSM MODULE TEST SUITE")
    print("="*60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tests = [
        test_fsm_basic,
        test_fsm_invalid_transition,
        test_sensor_fsm,
        test_intervention_fsm,
        test_vehicle_fsm,
        test_fsm_conditions,
        test_fsm_history,
        test_fsm_actions
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ TEST FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ TEST ERROR: {e}\n")
            failed += 1
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
    else:
        print(f"\n⚠️  {failed} test(s) failed\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

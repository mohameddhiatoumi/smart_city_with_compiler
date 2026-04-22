import { useState, useEffect } from 'react';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import EntitySelector from './EntitySelector';
import FSMVisualizer from './FSMVisualizer';
import EventTrigger from './EventTrigger';
import StateTimeline from './StateTimeline';
import {
  getSensorFSMState,
  triggerSensorEvent,
  getSensorEvents,
  getInterventionFSMState,
  triggerInterventionEvent,
  getInterventionEvents,
  getVehicleFSMState,
  triggerVehicleEvent,
  getVehicleEvents,
} from '../../services/fsm-service';

const FSMDashboard = ({ onClose }) => {
  const [entityType, setEntityType] = useState('sensor');
  const [entityId, setEntityId] = useState(null);
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [availableEvents, setAvailableEvents] = useState([]);

  // Fetch FSM state
  const fetchFSMState = async (type, id) => {
    if (!id) return;

    setLoading(true);
    setError('');

    try {
      let stateData, eventsData;

      if (type === 'sensor') {
        stateData = await getSensorFSMState(id);
        eventsData = await getSensorEvents();
      } else if (type === 'intervention') {
        stateData = await getInterventionFSMState(id);
        eventsData = await getInterventionEvents();
      } else if (type === 'vehicle') {
        stateData = await getVehicleFSMState(id);
        eventsData = await getVehicleEvents();
      }

      setState(stateData);
      setAvailableEvents(eventsData?.events || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch FSM state');
      console.error('Error fetching FSM state:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle entity selection change

    
  const handleEntityChange = (type, id) => {
    setEntityType(type);
    setEntityId(id);
    // Force immediate refresh when switching entity
    setTimeout(() => {
      fetchFSMState(type, id);
    }, 50);
  };

  // Trigger event*
  // In FSMDashboard.jsx, update the handleTriggerEvent function:

    const handleTriggerEvent = async (event, context = {}) => {
    if (!entityId) return;

    setLoading(true);
    try {
        if (entityType === 'sensor') {
        await triggerSensorEvent(entityId, event, context);
        } else if (entityType === 'intervention') {
        await triggerInterventionEvent(entityId, event, context);
        } else if (entityType === 'vehicle') {
        await triggerVehicleEvent(entityId, event, context);
        }

        // Refresh state after event
        await fetchFSMState(entityType, entityId);
    } catch (err) {
        setError(err.message || 'Failed to trigger event');
        throw err;
    } finally {
        setLoading(false);
    }
    };
  

  // Initial fetch and auto-refresh
  useEffect(() => {
    if (entityId) {
      // Fetch immediately with current entityType and entityId
      fetchFSMState(entityType, entityId);
      
      // Auto-refresh every 3 seconds
      const interval = setInterval(() => {
        fetchFSMState(entityType, entityId);
      }, 3000);
      
      return () => clearInterval(interval);
    }
  }, [entityType, entityId]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="text-3xl font-bold text-gray-900">
              🤖 FSM Dashboard - State Machine Visualizer
            </h1>
          </div>
          <button
            onClick={() => fetchFSMState(entityType, entityId)}
            disabled={loading || !entityId}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 text-gray-700 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Entity Selector */}
        <EntitySelector onEntityChange={handleEntityChange} />

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            ❌ {error}
          </div>
        )}

        {/* FSM Content */}
        {state && entityId ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-2">
              <FSMVisualizer
                entityType={entityType}
                currentState={state.current_state}
                validTransitions={state.valid_transitions}
              />

              <EventTrigger
                entityType={entityType}
                entityId={entityId}
                availableEvents={state.valid_transitions}
                onEventTriggered={handleTriggerEvent}
              />
            </div>

            {/* Right Column - History */}
            <div>
              <StateTimeline history={state.history} />
            </div>
          </div>
        ) : (
          <div className="text-center py-16">
            {loading ? (
              <div>
                <div className="inline-block">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
                </div>
                <p className="mt-4 text-gray-600">Loading FSM state...</p>
              </div>
            ) : (
              <p className="text-gray-500">Select an entity to view its FSM state</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default FSMDashboard;
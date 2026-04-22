import { useState, useEffect } from 'react';
import { ZapOff, Loader, CheckCircle, XCircle } from 'lucide-react';
import { getAllZones } from '../../services/api';

const EventTrigger = ({ entityType, entityId, availableEvents, onEventTriggered }) => {
  const [selectedEvent, setSelectedEvent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState('');
  
  // AI Validation states
  const [loadingMessage, setLoadingMessage] = useState('');
  const [aiReport, setAIReport] = useState(null);
  const [showAIReport, setShowAIReport] = useState(false);
  const [currentState, setCurrentState] = useState('');

  // Fetch zones for vehicle events
  useEffect(() => {
    if (entityType === 'vehicle') {
      const fetchZones = async () => {
        try {
          const data = await getAllZones();
          setZones(data);
          if (data.length > 0) {
            setSelectedZone(data[0].zone_id.toString());
          }
        } catch (err) {
          console.error('Failed to fetch zones:', err);
        }
      };
      fetchZones();
    }
  }, [entityType]);

  // Get current state from availableEvents (passed from parent)
  useEffect(() => {
    if (availableEvents && entityType === 'intervention') {
      // We need to track current state - this will be passed from parent
      // For now, we can infer it from valid transitions
      console.log('Available events:', availableEvents);
    }
  }, [availableEvents, entityType]);

  const handleTriggerEvent = async () => {
    if (!selectedEvent) {
      setError('Please select an event');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const context = {};
      
      // Add zone context for vehicle events
      if (entityType === 'vehicle' && selectedEvent === 'demarrer') {
        if (!selectedZone) {
          setError('Please select a departure zone');
          setLoading(false);
          return;
        }
        context.zone_depart_id = parseInt(selectedZone);
      }
      
      if (entityType === 'vehicle' && selectedEvent === 'arriver') {
        if (!selectedZone) {
          setError('Please select an arrival zone');
          setLoading(false);
          return;
        }
        context.zone_arrivee_id = parseInt(selectedZone);
        context.distance_km = 10; // Default distance
        context.economie_co2 = 2.5; // Default CO2 savings
      }

      await onEventTriggered(selectedEvent, context);
      setSuccess(`Event "${selectedEvent}" triggered successfully!`);
      setSelectedEvent('');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      console.error('Full error:', err);
      
      if (err.response?.status === 400) {
        setError(err.response.data?.detail || 'Invalid transition');
      } else if (err.response?.status === 500) {
        setError(err.response.data?.detail || 'Server error');
      } else if (err.message === 'Network Error') {
        setError('Network error - check if server is running on http://localhost:8000');
      } else {
        setError(err.message || 'Failed to trigger event');
      }
    } finally {
      setLoading(false);
    }
  };

  // Handle IA Validation Auto-transition
  const handleIAValidation = async () => {
  if (!entityId) return;
  
  setLoading(true);
  setLoadingMessage('🤖 IA is thinking...');
  setAIReport(null);
  setError('');
  
  try {
    console.log(`🔍 Starting IA validation for intervention ${entityId}`);
    
    // First, get the current state to verify we're in ia_valide
    const stateResponse = await fetch(
      `http://localhost:8000/fsm/interventions/${entityId}/state`
    );
    const stateData = await stateResponse.json();
    console.log('📊 Current intervention state:', stateData.current_state);
    
    if (stateData.current_state !== 'ia_valide') {
      setError(`Cannot validate - intervention is in "${stateData.current_state}" state, not "ia_valide"`);
      setLoading(false);
      return;
    }
    
    // Call the auto-validate endpoint
    const response = await fetch(
      `http://localhost:8000/fsm/interventions/${entityId}/ia-auto-validate`,
      { method: 'POST' }
    );
    
    const data = await response.json();
    console.log('📋 IA Validation response:', data);
    
    if (data.success) {
      // Show AI decision with report
      setAIReport({
        decision: data.decision,
        report: data.ai_report,
        newState: data.new_state,
        message: data.message
      });
      setShowAIReport(true);
      
      // Wait 2 seconds then refresh
      setTimeout(() => {
  // Trigger a refresh by calling parent's refresh function
  // Don't pass null, just fetch fresh data
  window.location.reload(); // Or call parent's fetch function
}, 2000);
    } else {
      setError(data.detail || 'AI validation failed');
      console.error('❌ API error:', data.detail);
    }
  } catch (error) {
    console.error('❌ Error in IA validation:', error);
    setError('IA validation error: ' + error.message);
  } finally {
    setLoading(false);
    setLoadingMessage('');
  }
};

  const getEventColor = (event) => {
    if (event === 'annuler' || event === 'declarer_hors_service' || event === 'tomber_en_panne') 
      return 'bg-red-500 hover:bg-red-600';
    if (event.includes('terminer') || event.includes('arriver') || event === 'reparer') 
      return 'bg-green-500 hover:bg-green-600';
    if (event.includes('reparation') || event === 'demarrer' || event === 'stationner') 
      return 'bg-blue-500 hover:bg-blue-600';
    return 'bg-indigo-500 hover:bg-indigo-600';
  };

  const needsZoneSelection = entityType === 'vehicle' && 
    (selectedEvent === 'demarrer' || selectedEvent === 'arriver');

  // Check if we should show IA validation button
  const isInIAValidationMode = entityType === 'intervention' && 
  availableEvents &&  
  availableEvents.some(e => e === 'auto_terminate' || e === 'auto_reject');

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Trigger Event</h2>

      {/* Special case: IA Validation Mode */}
      {isInIAValidationMode && !showAIReport && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-300 rounded-lg p-4 mb-4">
          <h3 className="text-lg font-bold text-blue-900 mb-3 flex items-center gap-2">
            🤖 AI Validation Mode
          </h3>
          <p className="text-sm text-gray-700 mb-3">Let the AI automatically decide if this sensor maintenance is valid</p>
          <button
            onClick={handleIAValidation}
            disabled={loading}
            className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                {loadingMessage}
              </>
            ) : (
              '▶ Start AI Validation'
            )}
          </button>
        </div>
      )}

      {/* AI Report Display */}
      {aiReport && showAIReport && (
        <div className={`border-2 rounded-lg p-4 mb-4 ${
          aiReport.decision.includes('ACCEPTED') 
            ? 'bg-green-50 border-green-300' 
            : 'bg-red-50 border-red-300'
        }`}>
          <div className="flex items-center gap-3 mb-3">
            {aiReport.decision.includes('ACCEPTED') ? (
              <>
                <CheckCircle className="w-8 h-8 text-green-600" />
                <h3 className="text-2xl font-bold text-green-900">Validation Passed ✅</h3>
              </>
            ) : (
              <>
                <XCircle className="w-8 h-8 text-red-600" />
                <h3 className="text-2xl font-bold text-red-900">Validation Failed ❌</h3>
              </>
            )}
          </div>
          
          <div className="bg-white rounded p-3 mb-3 border">
            <p className="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed font-mono">
              {aiReport.report}
            </p>
          </div>
          
          <div className={`text-sm p-3 rounded ${
            aiReport.decision.includes('ACCEPTED')
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}>
            <p><span className="font-semibold">Status:</span> {aiReport.message}</p>
            <p className="mt-2"><span className="font-semibold">Transition:</span> ia_valide → <span className="font-bold">{aiReport.newState}</span></p>
          </div>
          
          <button
            onClick={() => {
              setShowAIReport(false);
              setAIReport(null);
              setSelectedEvent('');
            }}
            className="mt-3 w-full px-3 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 text-sm font-medium"
          >
            Close Report
          </button>
        </div>
      )}

      {/* Regular Event Selection - Hidden during IA validation */}
      {!(isInIAValidationMode && !showAIReport) && !showAIReport && (
        <>
          {/* Event Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Event
            </label>
            <select
              value={selectedEvent}
              onChange={(e) => setSelectedEvent(e.target.value)}
              disabled={loading || !availableEvents || availableEvents.length === 0}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
            >
              <option value="">Choose an event...</option>
              {availableEvents?.map((event) => (
                <option key={event} value={event}>
                  {event.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Zone Selection for Vehicle Events */}
          {needsZoneSelection && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {selectedEvent === 'demarrer' ? '📍 Departure Zone' : '📍 Arrival Zone'}
              </label>
              <select
                value={selectedZone}
                onChange={(e) => setSelectedZone(e.target.value)}
                disabled={loading || zones.length === 0}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a zone...</option>
                {zones.map((zone) => (
                  <option key={zone.zone_id} value={zone.zone_id}>
                    {zone.nom}
                  </option>
                ))}
              </select>
              {!selectedZone && needsZoneSelection && (
                <p className="text-xs text-blue-600 mt-2">⚠️ Zone is required for this event</p>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              ❌ {error}
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              ✅ {success}
            </div>
          )}

          {/* Trigger Button */}
          <button
            onClick={handleTriggerEvent}
            disabled={loading || !selectedEvent || !entityId || (needsZoneSelection && !selectedZone)}
            className={`w-full py-2 px-4 rounded-lg text-white font-medium flex items-center justify-center gap-2 transition-colors ${
              loading || !selectedEvent || !entityId || (needsZoneSelection && !selectedZone)
                ? 'bg-gray-400 cursor-not-allowed'
                : `${getEventColor(selectedEvent)} cursor-pointer`
            }`}
          >
            {loading ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Triggering...
              </>
            ) : (
              <>
                <ZapOff className="w-4 h-4" />
                Trigger Event
              </>
            )}
          </button>
        </>
      )}

      {/* Debug Info */}
      <div className="mt-4 p-2 bg-gray-50 rounded text-xs text-gray-600 border border-gray-200">
        <p>Entity Type: <span className="font-mono">{entityType}</span></p>
        <p>Entity ID: <span className="font-mono">{entityId}</span></p>
        <p>Selected Event: <span className="font-mono">{selectedEvent || 'None'}</span></p>
        {needsZoneSelection && (
          <p>Selected Zone: <span className="font-mono">{selectedZone || 'None'}</span></p>
        )}
      </div>
    </div>
  );
};

export default EventTrigger;
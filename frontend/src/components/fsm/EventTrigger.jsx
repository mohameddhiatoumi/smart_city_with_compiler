import { useState, useEffect } from 'react';
import { ZapOff, Loader } from 'lucide-react';
import { getAllZones } from '../../services/api';

const EventTrigger = ({ entityType, entityId, availableEvents, onEventTriggered }) => {
  const [selectedEvent, setSelectedEvent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState('');

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

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Trigger Event</h2>

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
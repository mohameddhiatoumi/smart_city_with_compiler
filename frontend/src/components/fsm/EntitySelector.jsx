import { useState, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { getAllSensors, getAllZones } from '../../services/api';

const EntitySelector = ({ onEntityChange }) => {
  const [entityType, setEntityType] = useState('sensor');
  const [entityId, setEntityId] = useState('');
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchEntities = async () => {
      setLoading(true);
      try {
        if (entityType === 'sensor') {
          const data = await getAllSensors();
          setEntities(data);
          if (data.length > 0 && !entityId) {
            setEntityId(data[0].capteur_id);
            onEntityChange(entityType, data[0].capteur_id);
          }
                   } else if (entityType === 'intervention') {
          // Fetch pending interventions (sensors in en_maintenance)
          try {
            const response = await fetch('http://localhost:8000/fsm/interventions/pending');
            const data = await response.json();
            
            // For each sensor, create or get an intervention
            const interventionOptions = [];
            for (const sensor of data.pending_sensors) {
              try {
                // Create new intervention for this sensor
                const createResponse = await fetch(
                  `http://localhost:8000/fsm/interventions/create-for-sensor/${sensor.capteur_id}`,
                  { method: 'POST' }
                );
                const interventionData = await createResponse.json();
                
                if (interventionData.success) {
                  interventionOptions.push({
                    id: interventionData.intervention_id,  // Use intervention_id (integer)
                    name: `Sensor: ${sensor.capteur_id} (${sensor.type_capteur})`
                  });
                }
              } catch (error) {
                console.error(`Failed to create intervention for ${sensor.capteur_id}:`, error);
              }
            }
            
            setEntities(interventionOptions);
            if (interventionOptions.length > 0 && !entityId) {
              setEntityId(interventionOptions[0].id);
              onEntityChange('intervention', interventionOptions[0].id);
            }
          } catch (error) {
            console.error('Failed to fetch pending interventions:', error);
            setEntities([]);
          }
        } else if (entityType === 'vehicle') {
          // Vehicles would come from API
          setEntities([
            { id: 1, name: 'Vehicle 1' },
            { id: 2, name: 'Vehicle 2' },
            { id: 3, name: 'Vehicle 3' },
          ]);
        }
      } catch (error) {
        console.error('Failed to fetch entities:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEntities();
  }, [entityType]);

  const handleEntityTypeChange = (e) => {
    const newType = e.target.value;
    setEntityType(newType);
    setEntityId('');
  };

  const handleEntityIdChange = (e) => {
    const newId = e.target.value;
    setEntityId(newId);
    onEntityChange(entityType, newId);
  };

      const getEntityIdField = () => {
    if (entityType === 'sensor' && entities.length > 0) {
      return entities.map((sensor) => (
        <option key={sensor.capteur_id} value={sensor.capteur_id}>
          Sensor {sensor.capteur_id} - {sensor.type_capteur}
        </option>
      ));
    } else if (entityType === 'intervention' && entities.length > 0) {
      return entities.map((intervention) => (
        <option key={intervention.id} value={intervention.id}>
          {intervention.name}
        </option>
      ));
    }
    
    return entities.map((entity) => (
      <option key={entity.id} value={entity.id}>
        {entity.name}
      </option>
    ));
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Select Entity</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Entity Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Entity Type
          </label>
          <div className="relative">
            <select
              value={entityType}
              onChange={handleEntityTypeChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
            >
              <option value="sensor">🔧 Sensor</option>
              <option value="intervention">👷 Intervention</option>
              <option value="vehicle">🚗 Vehicle</option>
            </select>
            <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        {/* Entity ID Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {entityType.charAt(0).toUpperCase() + entityType.slice(1)} ID
          </label>
          <div className="relative">
            <select
              value={entityId}
              onChange={handleEntityIdChange}
              disabled={loading || entities.length === 0}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white disabled:bg-gray-100 disabled:text-gray-500"
            >
              <option value="">
                {loading ? 'Loading...' : 'Select an ID'}
              </option>
              {getEntityIdField()}
            </select>
            <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EntitySelector;
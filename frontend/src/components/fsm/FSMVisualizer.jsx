import { Activity, AlertTriangle, Wrench, XCircle, Truck, CheckCircle } from 'lucide-react';

const FSMVisualizer = ({ entityType, currentState, validTransitions }) => {
  const getStateConfig = (state, type) => {
    const sensorStates = {
      inactif: { color: 'bg-gray-400', icon: XCircle, label: 'Inactive' },
      actif: { color: 'bg-green-500', icon: Activity, label: 'Active' },
      signale: { color: 'bg-yellow-500', icon: AlertTriangle, label: 'Flagged' },
      en_maintenance: { color: 'bg-blue-500', icon: Wrench, label: 'Maintenance' },
      hors_service: { color: 'bg-red-500', icon: XCircle, label: 'Out of Service' },
    };

    const interventionStates = {
      demande: { color: 'bg-gray-400', icon: CheckCircle, label: 'Requested' },
      tech1_assigne: { color: 'bg-blue-400', icon: Activity, label: 'Tech 1 Assigned' },
      tech2_valide: { color: 'bg-purple-500', icon: CheckCircle, label: 'Tech 2 Validated' },
      ia_valide: { color: 'bg-indigo-500', icon: CheckCircle, label: 'AI Validated' },
      termine: { color: 'bg-green-500', icon: CheckCircle, label: 'Completed' },
      annule: { color: 'bg-red-500', icon: XCircle, label: 'Cancelled' },
    };

    const vehicleStates = {
      stationne: { color: 'bg-gray-400', icon: Truck, label: 'Parked' },
      en_route: { color: 'bg-blue-500', icon: Truck, label: 'In Transit' },
      en_panne: { color: 'bg-red-500', icon: AlertTriangle, label: 'Broken Down' },
      arrive: { color: 'bg-green-500', icon: CheckCircle, label: 'Arrived' },
    };

    const stateMap = {
      sensor: sensorStates,
      intervention: interventionStates,
      vehicle: vehicleStates,
    };

    return stateMap[type]?.[state] || { color: 'bg-gray-400', icon: XCircle, label: state };
  };

  const stateConfig = getStateConfig(currentState, entityType);
  const StateIcon = stateConfig.icon;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">FSM State</h2>

      {/* Current State Display */}
      <div className="flex items-center justify-center mb-8 p-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-blue-200">
        <div className={`${stateConfig.color} p-4 rounded-full mr-6`}>
          <StateIcon className="w-8 h-8 text-white" />
        </div>
        <div>
          <p className="text-sm text-gray-600 mb-1">Current State</p>
          <p className="text-3xl font-bold text-gray-900">{stateConfig.label}</p>
          <p className="text-xs text-gray-500 mt-1">({currentState})</p>
        </div>
      </div>

      {/* Valid Transitions */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Valid Transitions</h3>
        {validTransitions && validTransitions.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {validTransitions.map((transition) => (
              <div
                key={transition}
                className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-center"
              >
                <p className="text-sm font-medium text-blue-900">
                  ➜ {transition}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No valid transitions available</p>
        )}
      </div>
    </div>
  );
};

export default FSMVisualizer;
import { Activity, AlertTriangle, Wrench, XCircle } from 'lucide-react';

const SensorCard = ({ sensor }) => {
  const statusConfig = {
    actif: { color: 'bg-green-500', icon: Activity, text: 'Actif' },
    signale: { color: 'bg-yellow-500', icon: AlertTriangle, text: 'Signalé' },
    en_maintenance: { color: 'bg-blue-500', icon: Wrench, text: 'Maintenance' },
    hors_service: { color: 'bg-red-500', icon: XCircle, text: 'Hors Service' },
    inactif: { color: 'bg-gray-400', icon: XCircle, text: 'Inactif' },
  };

  const config = statusConfig[sensor.statut] || statusConfig.inactif;
  const StatusIcon = config.icon;

  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-lg text-gray-900">{sensor.capteur_id}</h3>
        <div className={`${config.color} p-2 rounded-full`}>
          <StatusIcon className="w-4 h-4 text-white" />
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Type:</span>
          <span className="font-medium text-gray-900">{sensor.type_capteur}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Statut:</span>
          <span className={`font-medium ${config.color.replace('bg-', 'text-')}`}>
            {config.text}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Taux d'erreur:</span>
          <span className="font-medium text-gray-900">{sensor.taux_erreur?.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
};

export default SensorCard;
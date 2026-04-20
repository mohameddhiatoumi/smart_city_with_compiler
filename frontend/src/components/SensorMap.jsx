import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Wrench, XCircle, MapPin } from 'lucide-react';
import { getAllSensors, getAllZones, getSensorLatestMeasurements } from '../services/api';

const SensorMap = () => {
  const [sensors, setSensors] = useState([]);
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [sensorMeasurements, setSensorMeasurements] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sensorsData, zonesData] = await Promise.all([
          getAllSensors(),
          getAllZones()
        ]);
        setSensors(sensorsData);
        setZones(zonesData);
        
        // Fetch latest measurements for all sensors
        const measurements = {};
        for (const sensor of sensorsData) {
          try {
            const latestMeasurements = await getSensorLatestMeasurements(sensor.capteur_id);
            measurements[sensor.capteur_id] = latestMeasurements;
          } catch (error) {
            console.warn(`Failed to fetch measurements for ${sensor.capteur_id}`);
            measurements[sensor.capteur_id] = [];
          }
        }
        setSensorMeasurements(measurements);
      } catch (error) {
        console.error('Failed to fetch map data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Group sensors by zone
  const sensorsByZone = sensors.reduce((acc, sensor) => {
    if (!acc[sensor.zone_id]) {
      acc[sensor.zone_id] = [];
    }
    acc[sensor.zone_id].push(sensor);
    return acc;
  }, {});

  // Status configuration
  const statusConfig = {
    actif: { 
      color: '#10B981', 
      bgColor: 'bg-green-100', 
      borderColor: 'border-green-500', 
      icon: Activity, 
      label: 'Actif' 
    },
    signale: { 
      color: '#F59E0B', 
      bgColor: 'bg-yellow-100', 
      borderColor: 'border-yellow-500', 
      icon: AlertTriangle, 
      label: 'Signalé' 
    },
    en_maintenance: { 
      color: '#3B82F6', 
      bgColor: 'bg-blue-100', 
      borderColor: 'border-blue-500', 
      icon: Wrench, 
      label: 'Maintenance' 
    },
    hors_service: { 
      color: '#EF4444', 
      bgColor: 'bg-red-100', 
      borderColor: 'border-red-500', 
      icon: XCircle, 
      label: 'Hors Service' 
    },
    inactif: { 
      color: '#6B7280', 
      bgColor: 'bg-gray-100', 
      borderColor: 'border-gray-400', 
      icon: XCircle, 
      label: 'Inactif' 
    },
  };

  // Get zone statistics
  const getZoneStats = (zoneId) => {
    const zoneSensors = sensorsByZone[zoneId] || [];
    const stats = {
      total: zoneSensors.length,
      actif: zoneSensors.filter(s => s.statut === 'actif').length,
      signale: zoneSensors.filter(s => s.statut === 'signale').length,
      faulty: zoneSensors.filter(s => s.statut === 'en_maintenance' || s.statut === 'hors_service').length,
    };
    
    // Determine zone health color
    if (stats.faulty > 0 || stats.signale > stats.total * 0.3) {
      stats.healthColor = '#EF4444'; // Red
    } else if (stats.signale > 0) {
      stats.healthColor = '#F59E0B'; // Yellow
    } else {
      stats.healthColor = '#10B981'; // Green
    }
    
    return stats;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-12 text-gray-500">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          Chargement de la carte...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <MapPin className="w-6 h-6" />
          Carte des Capteurs par Zone
        </h2>
        
        {/* Legend */}
        <div className="flex gap-4 text-sm flex-wrap">
          {Object.entries(statusConfig).map(([status, config]) => {
            const Icon = config.icon;
            return (
              <div key={status} className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: config.color }}></div>
                <span className="text-gray-700">{config.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Zone Grid Map */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        {zones.map((zone) => {
          const stats = getZoneStats(zone.zone_id);
          const isSelected = selectedZone?.zone_id === zone.zone_id;

          return (
            <div
              key={zone.zone_id}
              onClick={() => setSelectedZone(isSelected ? null : zone)}
              className={`
                relative p-4 rounded-lg border-2 cursor-pointer transition-all
                ${isSelected ? 'ring-4 ring-blue-300 shadow-lg' : 'hover:shadow-md'}
              `}
              style={{ 
                borderColor: stats.healthColor,
                backgroundColor: isSelected ? '#EFF6FF' : '#FFFFFF'
              }}
            >
              {/* Zone Header */}
              <div className="mb-3">
                <h3 className="font-bold text-sm text-gray-900 mb-1 truncate" title={zone.nom}>
                  {zone.nom}
                </h3>
                <div className="flex items-center gap-1 text-xs text-gray-600">
                  <Activity className="w-3 h-3" />
                  <span>{stats.total} capteurs</span>
                </div>
              </div>

              {/* Mini Status Indicators */}
              <div className="flex gap-1 flex-wrap">
                {stats.actif > 0 && (
                  <div className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                    {stats.actif}
                  </div>
                )}
                {stats.signale > 0 && (
                  <div className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs font-medium">
                    ⚠ {stats.signale}
                  </div>
                )}
                {stats.faulty > 0 && (
                  <div className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                    ✕ {stats.faulty}
                  </div>
                )}
              </div>

              {/* Health Indicator */}
              <div 
                className="absolute top-2 right-2 w-3 h-3 rounded-full"
                style={{ backgroundColor: stats.healthColor }}
                title="Santé de la zone"
              ></div>
            </div>
          );
        })}
      </div>

      {/* Selected Zone Details */}
      {selectedZone && (
        <div className="border-t pt-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Détails: {selectedZone.nom}
          </h3>
          
          {sensorsByZone[selectedZone.zone_id]?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {sensorsByZone[selectedZone.zone_id].map((sensor) => {
                const config = statusConfig[sensor.statut] || statusConfig.inactif;
                const Icon = config.icon;
                const measurements = sensorMeasurements[sensor.capteur_id] || [];

                return (
                  <div
                    key={sensor.capteur_id}
                    className={`p-4 rounded-lg border-2 ${config.borderColor} ${config.bgColor} flex flex-col`}
                  >
                    {/* Sensor Header */}
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-bold text-lg text-gray-900">{sensor.capteur_id}</span>
                      <Icon className="w-5 h-5" style={{ color: config.color }} />
                    </div>
                    
                    {/* Sensor Info */}
                    <div className="space-y-2 text-sm mb-3 pb-3 border-b border-current border-opacity-20">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Type:</span>
                        <span className="font-medium text-gray-900 capitalize">{sensor.type_capteur}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Statut:</span>
                        <span className="font-medium" style={{ color: config.color }}>
                          {config.label}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Erreur:</span>
                        <span className={`font-medium ${(sensor.taux_erreur || 0) > 15 ? 'text-red-600' : 'text-gray-900'}`}>
                          {typeof sensor.taux_erreur === 'number' ? `${sensor.taux_erreur.toFixed(1)}%` : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* Latest Measurements */}
                    {measurements && measurements.length > 0 ? (
                      <div className="flex-grow">
                        <p className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wider">Dernières valeurs:</p>
                        <div className="space-y-1.5">
                          {measurements.map((m, idx) => (
                            <div key={idx} className="flex justify-between items-start gap-2">
                              <span className="text-xs text-gray-600 truncate flex-shrink-0">{m.type_mesure}:</span>
                              <span className="text-xs font-bold text-gray-900 text-right flex-shrink-0">
                                {m.valeur !== null && m.valeur !== undefined 
                                  ? `${parseFloat(m.valeur).toFixed(1)} ${m.unite || ''}` 
                                  : 'N/A'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500 italic">
                        Aucune mesure disponible
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">
              Aucun capteur dans cette zone
            </p>
          )}
        </div>
      )}

      {/* Summary Statistics */}
      <div className="mt-8 pt-6 border-t">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-900">{zones.length}</div>
            <div className="text-sm text-gray-600 mt-1">Zones Total</div>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-600">
              {Object.values(sensorsByZone).flat().filter(s => s.statut === 'actif').length}
            </div>
            <div className="text-sm text-gray-600 mt-1">Capteurs Actifs</div>
          </div>
          <div className="p-4 bg-yellow-50 rounded-lg">
            <div className="text-3xl font-bold text-yellow-600">
              {Object.values(sensorsByZone).flat().filter(s => s.statut === 'signale').length}
            </div>
            <div className="text-sm text-gray-600 mt-1">Alertes</div>
          </div>
          <div className="p-4 bg-red-50 rounded-lg">
            <div className="text-3xl font-bold text-red-600">
              {Object.values(sensorsByZone).flat().filter(s => s.statut === 'hors_service' || s.statut === 'en_maintenance').length}
            </div>
            <div className="text-sm text-gray-600 mt-1">En Panne</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SensorMap;
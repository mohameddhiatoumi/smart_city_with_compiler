import { useEffect, useState } from 'react';
import LiveStats from './LiveStats';
import NLQueryInterface from './NLQueryInterface';
import PollutionChart from './PollutionChart';
import SensorCard from './SensorCard';
import { getAllSensors } from '../services/api';

const Dashboard = () => {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSensors = async () => {
      try {
        const data = await getAllSensors();
        setSensors(data.slice(0, 12)); // Show first 12 sensors
      } catch (error) {
        console.error('Failed to fetch sensors:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSensors();
    const interval = setInterval(fetchSensors, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            🌆 Neo-Sousse 2030 - Smart City Dashboard
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Live Statistics */}
        <LiveStats />

        {/* Natural Language Query Interface */}
        <NLQueryInterface />

        {/* Pollution Chart */}
        <PollutionChart />

        {/* Sensors Grid */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Capteurs Actifs</h2>
          {loading ? (
            <div className="text-center py-8">Chargement des capteurs...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {sensors.map((sensor) => (
                <SensorCard key={sensor.capteur_id} sensor={sensor} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
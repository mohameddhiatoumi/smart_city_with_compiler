import { useState } from 'react';
import { useEffect } from 'react';
import LiveStats from './LiveStats';
import NLQueryInterface from './NLQueryInterface';
import PollutionChart from './PollutionChart';
import SensorCard from './SensorCard';
import SensorMap from './SensorMap';
import AIReports from './AIReports';  // ← ADD THIS IMPORT
import FSMDashboard from './fsm/FSMDashboard';
import { getAllSensors } from '../services/api';

const Dashboard = () => {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFSM, setShowFSM] = useState(false);
  const [aiReportsRef, setAiReportsRef] = useState(null);

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

  const scrollToAIReports = () => {
    if (aiReportsRef) {
      aiReportsRef.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (showFSM) {
    return <FSMDashboard onClose={() => setShowFSM(false)} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">
            🌆 Neo-Sousse 2030 - Smart City Dashboard
          </h1>
          <div className="flex gap-3">
            <button
              onClick={scrollToAIReports}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              🤖 AI Reports
            </button>
            <button
              onClick={() => setShowFSM(true)}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              🤖 FSM Dashboard
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Live Statistics */}
        <LiveStats />

        {/* Natural Language Query Interface */}
        <NLQueryInterface />

        {/* Sensor Map */}
        <SensorMap />

        {/* AI Reports Section - WITH REF */}
        <div ref={setAiReportsRef} className="scroll-mt-20">
          <AIReports />
        </div>

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
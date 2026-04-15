import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getRecentMeasurements } from '../services/api';

const PollutionChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const measurements = await getRecentMeasurements(50);
        
        // Group by timestamp and aggregate
        const grouped = measurements.reduce((acc, m) => {
          const time = new Date(m.timestamp).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
          });
          
          if (!acc[time]) {
            acc[time] = { time, PM25: [], CO2: [], NO2: [] };
          }
          
          if (m.type_mesure === 'PM2.5') acc[time].PM25.push(m.valeur);
          if (m.type_mesure === 'CO2') acc[time].CO2.push(m.valeur);
          if (m.type_mesure === 'NO2') acc[time].NO2.push(m.valeur);
          
          return acc;
        }, {});

        // Calculate averages
        const chartData = Object.values(grouped).map(item => ({
          time: item.time,
          PM25: item.PM25.length > 0 ? item.PM25.reduce((a, b) => a + b, 0) / item.PM25.length : null,
          CO2: item.CO2.length > 0 ? item.CO2.reduce((a, b) => a + b, 0) / item.CO2.length : null,
          NO2: item.NO2.length > 0 ? item.NO2.reduce((a, b) => a + b, 0) / item.NO2.length : null,
        })).slice(-20); // Last 20 data points

        setData(chartData);
      } catch (error) {
        console.error('Failed to fetch measurements:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="text-center py-8">Chargement des données...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Pollution en Temps Réel</h2>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="PM25" stroke="#ef4444" name="PM2.5 (µg/m³)" />
          <Line type="monotone" dataKey="CO2" stroke="#3b82f6" name="CO2 (ppm)" />
          <Line type="monotone" dataKey="NO2" stroke="#f59e0b" name="NO2 (µg/m³)" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PollutionChart;
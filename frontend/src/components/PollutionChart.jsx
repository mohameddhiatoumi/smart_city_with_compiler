import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getRecentMeasurements } from '../services/api';

const PollutionChart = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('📊 Fetching pollution measurements...');
      const measurements = await getRecentMeasurements(500);
      
      if (!measurements || measurements.length === 0) {
        console.warn('⚠️ No measurements received from API');
        setError('Aucune donnée disponible pour le moment');
        setData([]);
        return;
      }

      console.log(`✅ Received ${measurements.length} measurements`);

      // Group by timestamp and aggregate
      const grouped = measurements.reduce((acc, m) => {
        if (!m || !m.timestamp || !m.type_mesure || m.valeur === null || m.valeur === undefined) {
          console.warn('⚠️ Skipping invalid measurement:', m);
          return acc;
        }

        // Parse timestamp correctly
        const timestamp = new Date(m.timestamp);
        if (isNaN(timestamp.getTime())) {
          console.warn('⚠️ Invalid timestamp:', m.timestamp);
          return acc;
        }

        const time = timestamp.toLocaleTimeString('fr-FR', {
          hour: '2-digit',
          minute: '2-digit'
        });

        if (!acc[time]) {
          acc[time] = { time, PM25: [], CO2: [], NO2: [] };
        }

        // Safely add measurement
        const value = parseFloat(m.valeur);
        if (!isNaN(value)) {
          if (m.type_mesure === 'PM2.5') acc[time].PM25.push(value);
          else if (m.type_mesure === 'CO2') acc[time].CO2.push(value);
          else if (m.type_mesure === 'NO2') acc[time].NO2.push(value);
        }

        return acc;
      }, {});

      // Calculate averages with null handling
      const chartData = Object.values(grouped)
        .map(item => ({
          time: item.time,
          PM25: item.PM25.length > 0 ? Math.round((item.PM25.reduce((a, b) => a + b, 0) / item.PM25.length) * 10) / 10 : null,
          CO2: item.CO2.length > 0 ? Math.round((item.CO2.reduce((a, b) => a + b, 0) / item.CO2.length) * 10) / 10 : null,
          NO2: item.NO2.length > 0 ? Math.round((item.NO2.reduce((a, b) => a + b, 0) / item.NO2.length) * 10) / 10 : null,
        }))
        .sort((a, b) => {
          // Sort by time
          const timeA = new Date(`2024-01-01 ${a.time}`).getTime();
          const timeB = new Date(`2024-01-01 ${b.time}`).getTime();
          return timeA - timeB;
        })
        .slice(-20); // Last 20 data points

      if (chartData.length === 0) {
        console.warn('⚠️ No valid chart data after processing');
        setError('Impossible de traiter les données reçues');
        setData([]);
        return;
      }

      console.log(`✅ Processed ${chartData.length} data points for chart`);
      setData(chartData);
      setRetryCount(0); // Reset retry counter on success
    } catch (error) {
      console.error('❌ Failed to fetch measurements:', error);
      setError(`Erreur lors du chargement: ${error.message || 'Erreur inconnue'}`);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    
    return () => clearInterval(interval);
  }, []);

  // Loading state
  if (loading && data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Pollution en Temps Réel</h2>
        <div className="flex items-center justify-center h-96 bg-gray-50 rounded">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Chargement des données...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state with retry button
  if (error && data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Pollution en Temps Réel</h2>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                {error}
              </h3>
              <div className="mt-4">
                <button
                  onClick={() => {
                    setRetryCount(prev => prev + 1);
                    fetchData();
                  }}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  🔄 Réessayer
                </button>
                {retryCount > 0 && (
                  <p className="text-xs text-red-600 mt-2">
                    Tentative {retryCount}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Empty data state
  if (!loading && data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Pollution en Temps Réel</h2>
        <div className="flex items-center justify-center h-96 bg-gray-50 rounded">
          <div className="text-center text-gray-500">
            <p className="mb-4">📊 Aucune donnée disponible</p>
            <button
              onClick={fetchData}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              Actualiser
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Successful chart render
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Pollution en Temps Réel</h2>
        <button
          onClick={fetchData}
          disabled={loading}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
        >
          🔄 Actualiser
        </button>
      </div>

      {data.length > 0 && (
        <div className="mb-2 text-xs text-gray-500">
          {data.length} points de données • Dernière mise à jour: {new Date().toLocaleTimeString('fr-FR')}
        </div>
      )}

      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="time"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #ccc',
              borderRadius: '4px',
              padding: '8px'
            }}
            formatter={(value) => (value !== null ? value.toFixed(2) : 'N/A')}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="PM25"
            stroke="#ef4444"
            name="PM2.5 (µg/m³)"
            connectNulls
            isAnimationActive={false}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="CO2"
            stroke="#3b82f6"
            name="CO2 (ppm)"
            connectNulls
            isAnimationActive={false}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="NO2"
            stroke="#f59e0b"
            name="NO2 (µg/m³)"
            connectNulls
            isAnimationActive={false}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PollutionChart;
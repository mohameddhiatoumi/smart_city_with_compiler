import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Thermometer, Wind } from 'lucide-react';
import { getDashboardStats } from '../services/api';

const LiveStats = () => {
  const [stats, setStats] = useState({
    total_sensors: 0,
    active_sensors: 0,
    faulty_sensors: 0,
    avg_pollution: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const statCards = [
    {
      title: 'Total Sensors',
      value: stats.total_sensors,
      icon: Activity,
      color: 'bg-blue-500',
    },
    {
      title: 'Active',
      value: stats.active_sensors,
      icon: Thermometer,
      color: 'bg-green-500',
    },
    {
      title: 'Faulty',
      value: stats.faulty_sensors,
      icon: AlertTriangle,
      color: 'bg-red-500',
    },
    {
      title: 'Avg Pollution',
      value: `${stats.avg_pollution?.toFixed(1) || 0} µg/m³`,
      icon: Wind,
      color: 'bg-orange-500',
    },
  ];

  if (loading) {
    return <div className="text-gray-500">Loading statistics...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {statCards.map((stat, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">{stat.title}</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
            </div>
            <div className={`${stat.color} p-3 rounded-full`}>
              <stat.icon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default LiveStats;
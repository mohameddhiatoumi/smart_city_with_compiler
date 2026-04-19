import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Natural Language Query
export const executeNLQuery = async (query) => {
  const response = await api.post(`/query?query=${encodeURIComponent(query)}`);
  return response.data;
};

// Dashboard Stats
export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

// Sensors
export const getAllSensors = async () => {
  const response = await api.get('/sensors');
  return response.data;
};

export const getSensorById = async (sensorId) => {
  const response = await api.get(`/sensors/${sensorId}`);
  return response.data;
};

// Zones
export const getAllZones = async () => {
  const response = await api.get('/zones');
  return response.data;
};

export const getZonePollution = async (zoneId, pollutant = 'PM2.5') => {
  const response = await api.get(`/zones/${zoneId}/pollution`, {
    params: { pollutant }
  });
  return response.data;
};


// Recent Measurements - FIXED
export const getRecentMeasurements = async (limit = 100) => {
  try {
    console.log('📡 Fetching recent measurements from all sensors...');
    const response = await api.get('/sensors/measurements/recent-all', {
      params: { 
        hours: 24,    // 
        limit: 500   // ← INCREASE limit to get more points
      }
    });
    console.log(`✅ Received ${response.data?.length || 0} measurements`);
    return response.data || [];
  } catch (error) {
    console.error('❌ Error fetching recent measurements:', error);
    return [];
  }
};

export default api;
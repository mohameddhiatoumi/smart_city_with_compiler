import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================
// NATURAL LANGUAGE QUERY
// ============================================================
export const executeNLQuery = async (query) => {
  const response = await api.post(`/query?query=${encodeURIComponent(query)}`);
  return response.data;
};

// ============================================================
// DASHBOARD STATS
// ============================================================
export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

// ============================================================
// SENSORS
// ============================================================
export const getAllSensors = async () => {
  const response = await api.get('/sensors');
  return response.data;
};

export const getSensorById = async (sensorId) => {
  const response = await api.get(`/sensors/${sensorId}`);
  return response.data;
};

export const getSensorLatestMeasurements = async (sensorId) => {
  try {
    const response = await api.get(`/sensors/${sensorId}/latest`);
    return response.data || [];
  } catch (error) {
    console.warn(`Failed to fetch latest measurements for ${sensorId}`);
    return [];
  }
};

// ============================================================
// ZONES
// ============================================================
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

// ============================================================
// MEASUREMENTS
// ============================================================
export const getRecentMeasurements = async (limit = 100) => {
  try {
    console.log('📡 Fetching recent measurements from all sensors...');
    const response = await api.get('/sensors/measurements/recent-all', {
      params: { 
        hours: 1,
        limit: 500
      }
    });
    console.log(`✅ Received ${response.data?.length || 0} measurements`);
    return response.data || [];
  } catch (error) {
    console.error('❌ Error fetching recent measurements:', error);
    return [];
  }
};

// ============================================================
// AI REPORTS - NEW FUNCTIONS
// ============================================================
export const getAirQualityReport = async (zoneId = null, date = null) => {
  try {
    const params = new URLSearchParams();
    if (zoneId) params.append('zone_id', zoneId);
    if (date) params.append('date', date);
    
    const response = await api.get(`/ai/report/air-quality?${params}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching air quality report:', error);
    throw error;
  }
};

export const getSensorRecommendation = async (sensorId) => {
  try {
    const response = await api.get(`/ai/recommendation/sensor/${sensorId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching sensor recommendation:', error);
    throw error;
  }
};

export const getTrafficAnalysis = async (zoneId = null) => {
  try {
    const params = new URLSearchParams();
    if (zoneId) params.append('zone_id', zoneId);
    
    const response = await api.get(`/ai/analysis/traffic?${params}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching traffic analysis:', error);
    throw error;
  }
};

export const validateFSMTransition = async (entityType, currentState, proposedEvent, context = {}) => {
  try {
    const response = await api.post('/ai/validate-transition', {
      entity_type: entityType,
      current_state: currentState,
      proposed_event: proposedEvent,
      context: context
    });
    return response.data;
  } catch (error) {
    console.error('Error validating FSM transition:', error);
    throw error;
  }
};

export default api;
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// SENSOR FSM
// ============================================================================

// SENSOR FSM - UPDATED

export const getSensorFSMState = async (sensorId) => {
  const id = parseInt(sensorId) || sensorId;  // Try to convert to int, fallback to original
  const response = await api.get(`/fsm/sensors/${id}/state`);
  return response.data;
};

export const triggerSensorEvent = async (sensorId, event, context = {}) => {
  const id = parseInt(sensorId) || sensorId;  // Try to convert to int, fallback to original
  const response = await api.post(`/fsm/sensors/${id}/trigger`, {
    event,
    context,
  });
  return response.data;
};

export const getSensorFSMDiagram = async (sensorId) => {
  const id = parseInt(sensorId) || sensorId;  // Try to convert to int, fallback to original
  const response = await api.get(`/fsm/sensors/${id}/diagram`);
  return response.data;
};

export const getSensorEvents = async () => {
  const response = await api.get('/fsm/events/sensors');
  return response.data;
};

// ============================================================================
// INTERVENTION FSM
// ============================================================================

export const getInterventionFSMState = async (interventionId) => {
  const response = await api.get(`/fsm/interventions/${interventionId}/state`);
  return response.data;
};

export const triggerInterventionEvent = async (interventionId, event, context = {}) => {
  const response = await api.post(`/fsm/interventions/${interventionId}/trigger`, {
    event,
    context,
  });
  return response.data;
};

export const getInterventionFSMDiagram = async (interventionId) => {
  const response = await api.get(`/fsm/interventions/${interventionId}/diagram`);
  return response.data;
};

export const getInterventionEvents = async () => {
  const response = await api.get('/fsm/events/interventions');
  return response.data;
};

// ============================================================================
// VEHICLE FSM
// ============================================================================

export const getVehicleFSMState = async (vehicleId) => {
  const response = await api.get(`/fsm/vehicles/${vehicleId}/state`);
  return response.data;
};

export const triggerVehicleEvent = async (vehicleId, event, context = {}) => {
  const response = await api.post(`/fsm/vehicles/${vehicleId}/trigger`, {
    event,
    context,
  });
  return response.data;
};

export const getVehicleFSMDiagram = async (vehicleId) => {
  const response = await api.get(`/fsm/vehicles/${vehicleId}/diagram`);
  return response.data;
};

export const getVehicleEvents = async () => {
  const response = await api.get('/fsm/events/vehicles');
  return response.data;
};

export default api;
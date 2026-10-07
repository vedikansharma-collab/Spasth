import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const uploadPolicy = async (file, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/policies/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress,
  });
  return response.data;
};

export const getPolicies = async () => {
  const response = await api.get('/policies');
  return response.data;
};

export const getPolicyDetail = async (policyId) => {
  const response = await api.get(`/policies/${policyId}`);
  return response.data;
};

export const getPolicyPage = async (policyId, pageNumber) => {
  const response = await api.get(`/policies/${policyId}/pages/${pageNumber}`);
  return response.data;
};

export const getTreatments = async () => {
  const response = await api.get('/treatments');
  return response.data;
};

export const calculateEstimate = async (payload) => {
  const response = await api.post('/estimate', payload);
  return response.data;
};

export const calculateTreatment = async (payload) => {
  const response = await api.post('/calculate', payload);
  return response.data;
};

export default api;

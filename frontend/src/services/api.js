import axios from 'axios';

const API_BASE_URL = '/api';
const TOKEN_KEY = 'spasth_auth_token';

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY);
export const setStoredToken = (token) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
};
export const clearStoredToken = () => localStorage.removeItem(TOKEN_KEY);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach Bearer token to all outgoing API requests
api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor: handle 401 Unauthorized token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      clearStoredToken();
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// AUTHENTICATION APIS
// ============================================================================

export const registerUser = async (email, password) => {
  const response = await api.post('/auth/register', { email, password });
  if (response.data?.access_token) {
    setStoredToken(response.data.access_token);
  }
  return response.data;
};

export const loginUser = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  if (response.data?.access_token) {
    setStoredToken(response.data.access_token);
  }
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

export const logoutUser = () => {
  clearStoredToken();
};

// ============================================================================
// CORE SERVICE APIS
// ============================================================================

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

export const calculateClaim = async (payload) => {
  const response = await api.post('/estimate/calculate-claim', payload);
  return response.data;
};

export const askPolicy = async (policyId, query) => {
  const response = await api.post(`/policies/${policyId}/ask`, { query });
  return response.data;
};

export default api;

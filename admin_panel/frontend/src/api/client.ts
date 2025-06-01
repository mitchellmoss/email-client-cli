import axios from 'axios';

// API URL configuration - can be set via environment variable
// In production, this should be set to your API server URL (e.g., https://api.your-domain.com)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Log API URL in development only
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL);
}

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
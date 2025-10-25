// src/api.ts
import axios from 'axios';
export const API_BASE = __DEV__ ? 'http://localhost:8000' : 'https://<api-host>';
const api = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });

// Add request/response interceptors for debugging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.log('API Request Error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.log('API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

export default api;

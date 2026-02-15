import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { ApiError, ApiErrorResponse } from '@/types/api.types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  withCredentials: true,  
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - NO TOKEN EXTRACTION NEEDED
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle 401 Unauthorized - Try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        
        await api.post(`/auth/refresh`);
        return api(originalRequest);
      } catch (refreshError) {
        
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Transform error to ApiError
    const apiError: ApiError = {
      message: error.response?.data?.message || error.message || 'An error occurred',
      status: error.response?.status || 500,
      errors: error.response?.data?.errors,
    };

    return Promise.reject(apiError);
  }
);

export default api;
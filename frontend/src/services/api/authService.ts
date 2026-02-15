import api from '../axios/axiosConfig';
import {
  LoginCredentials,
  RegisterData,
  AuthResponse,
} from '@/types/auth.types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    console.log('authService.login called with:', { email: credentials.email });

    const loginData = {
      email: credentials.email,
      password: credentials.password,
      user_agent: credentials.user_agent || navigator.userAgent,
      ip_address: credentials.ip_address || null,
      device_fingerprint: credentials.device_fingerprint,
    };

    console.log('Login request data:', loginData);

    try {
      const response = await api.post('/auth/login', loginData);
      console.log('Login response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Login API error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw error;
    }
  },

  async register(data: RegisterData): Promise<any> {
    console.log('authService.register called with:', data);
    console.log('Request URL:', '/auth/register');
    console.log('Request body:', JSON.stringify(data, null, 2));

    try {
      const response = await api.post('/auth/register', data);
      console.log('Response received:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Registration API error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw error;
    }
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.warn('Logout request failed:', error);
    }
  },

  async refreshToken(): Promise<void> {
    try {
      await api.post('/auth/refresh');
      console.log('Token refreshed successfully');
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  },

  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/auth/forgot-password', { email });
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  },

  async verifyEmail(token: string): Promise<void> {
    await api.post('/auth/verify-email', { token });
  },
};
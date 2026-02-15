import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthState } from '@/types/auth.types';
import { authService } from '@/services/api/authService';
import { generateDeviceId } from '@/utils/helpers';

interface LocationData {
  city?: string;
  region?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
}

interface LoginPayload {
  email: string;
  password: string;
  ip_address: string;
  user_agent?: string;
  device_fingerprint?: string;
  device_id?: string;
  location?: string;
  location_latitude?: number;
  location_longitude?: number;
  location_city?: string;
  location_region?: string;
  location_country?: string;
  typing_speed?: number;
  key_interval?: number;
  key_hold?: number;
}

interface AuthContextType extends Omit<AuthState, 'accessToken' | 'refreshToken'> {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<any>;
  register: (email: string, password: string, confirmPassword: string) => Promise<any>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

async function getLocationFromIP(ip: string): Promise<LocationData> {
  try {
    if (
      !ip ||
      ip === '0.0.0.0' ||
      ip === '127.0.0.1' ||
      ip.startsWith('192.168.') ||
      ip.startsWith('10.')
    ) {
      return {};
    }

    const response = await fetch(`https://ipinfo.io/${ip}/json`);
    if (!response.ok) return {};

    const data = await response.json();
    const [lat, lng] = (data.loc || '0,0').split(',').map(Number);

    return {
      city: data.city || undefined,
      region: data.region || undefined,
      country: data.country || undefined,
      latitude: lat || undefined,
      longitude: lng || undefined,
    };
  } catch (error) {
    console.warn('Failed to fetch location from IP:', error);
    return {};
  }
}

function formatLocation(locationData: LocationData): string {
  if (!locationData) return 'Unknown';
  const parts = [locationData.city, locationData.region, locationData.country].filter(Boolean);
  return parts.length > 0 ? parts.join(', ') : 'Unknown';
}

function getOrCreateDeviceFingerprint(): string {
  try {
    let stored = sessionStorage.getItem('device_fp_session');

    if (stored && stored.trim() !== '') {
      return stored;
    }

    const newId = generateDeviceId();
    sessionStorage.setItem('device_fp_session', newId);

    return newId;
  } catch (error) {
    console.warn('sessionStorage not available, generating fresh fingerprint');
    return generateDeviceId();
  }
}

function clearDeviceFingerprint(): void {
  try {
    sessionStorage.removeItem('device_fp_session');
  } catch (error) {
    console.warn('Failed to clear device fingerprint:', error);
  }
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<{
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
  }>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        getOrCreateDeviceFingerprint();
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    };

    initializeAuth();
  }, []);

  const login = async (payload: LoginPayload): Promise<any> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const deviceFingerprint =
        payload.device_fingerprint && payload.device_fingerprint.trim() !== ''
          ? payload.device_fingerprint
          : getOrCreateDeviceFingerprint();

      const locationData = await getLocationFromIP(payload.ip_address);
      const formattedLocation = formatLocation(locationData);

      const enhancedPayload: LoginPayload = {
        ...payload,
        device_fingerprint: deviceFingerprint,
        device_id: deviceFingerprint,
        location: formattedLocation || payload.location,
        location_latitude: locationData.latitude ?? payload.location_latitude,
        location_longitude: locationData.longitude ?? payload.location_longitude,
        location_city: locationData.city ?? payload.location_city,
        location_region: locationData.region ?? payload.location_region,
        location_country: locationData.country ?? payload.location_country,
        user_agent: payload.user_agent || navigator.userAgent,
        typing_speed: payload.typing_speed ?? 0.0,
        key_interval: payload.key_interval ?? 0.0,
        key_hold: payload.key_hold ?? 0.0,
      };

      const response = await authService.login(enhancedPayload);

      if (response.mfa_required) {
        setState(prev => ({ ...prev, isLoading: false }));
        return response;
      }

      setState({
        user: response.user || null,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return response;
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.detail || error.message || 'Login failed';

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMsg,
      }));

      throw error;
    }
  };

  const register = async (
    email: string,
    password: string,
    confirmPassword: string
  ): Promise<any> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await authService.register({
        email,
        password,
        password_confirm: confirmPassword,
      });

      setState(prev => ({ ...prev, isLoading: false }));

      return response;
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.detail || error.message || 'Registration failed';

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMsg,
      }));

      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      clearDeviceFingerprint();

      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  };

  const updateUser = (user: User): void => {
    setState(prev => ({
      ...prev,
      user: user || null,
    }));
  };

  const refreshAuth = async (): Promise<void> => {
    try {
      logout();
    } catch (error) {
      console.warn('Auth refresh failed, logging out');
      await logout();
    }
  };

  const value: AuthContextType = {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    login,
    register,
    logout,
    updateUser,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
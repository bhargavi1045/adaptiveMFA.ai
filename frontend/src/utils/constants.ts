export const APP_NAME = 'Adaptive MFA';

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  MFA_VERIFICATION: '/mfa-verify',
  MFA_SETUP: '/mfa-setup',
  SETTINGS: '/settings',
  SECURITY: '/settings/security',
  SESSIONS: '/settings/sessions',
  PROFILE: '/settings/profile',
  PASSWORD_RESET: '/password-reset',
  VERIFY_EMAIL: '/verify-email',
} as const;

export const MFA_METHOD_LABELS = {
  totp: 'Authenticator App',
  sms: 'SMS',
  email: 'Email',
  biometric: 'Biometric',
} as const;

export const RISK_LEVEL_COLORS = {
  low: 'text-green-600 bg-green-50',
  medium: 'text-yellow-600 bg-yellow-50',
  high: 'text-orange-600 bg-orange-50',
  critical: 'text-red-600 bg-red-50',
} as const;

export const RISK_LEVEL_LABELS = {
  low: 'Low Risk',
  medium: 'Medium Risk',
  high: 'High Risk',
  critical: 'Critical Risk',
} as const;

export const API_TIMEOUT = 30000;
export const TOKEN_REFRESH_INTERVAL = 14 * 60 * 1000; 
export const SESSION_CHECK_INTERVAL = 60 * 1000;
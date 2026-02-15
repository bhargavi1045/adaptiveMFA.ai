export interface User {
  id: string;
  email: string;
  name?: string;
  is_active: boolean;
  created_at: string;
  mfa_enabled: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  user_agent?: string;
  ip_address?: string;
  device_fingerprint?: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
}

export interface AuthResponse {
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  user?: User;
  mfa_required?: boolean;
  mfa_token?: string;
  message?: string;
}

export interface RegisterResponse {
  message: string;
  user: User;
  qr_code_uri: string;
  backup_codes: string[];
  setup_token: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface TokenPayload {
  sub: string;
  exp: number;
  iat: number;
}
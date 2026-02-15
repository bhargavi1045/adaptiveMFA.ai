export interface DeviceInfo {
  device_type: string;
  browser: string;
  os: string;
  device_id?: string;
}

export interface Location {
  ip_address: string;
  city?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
}

export interface Session {
  session_id: string;
  user_id: string;
  device_info: DeviceInfo;
  location?: Location;
  created_at: string;
  last_activity: string;
  is_current: boolean;
  expires_at?: string;
}

export interface RiskAssessment {
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  factors: RiskFactor[];
  timestamp: string;
}

export interface RiskFactor {
  type: string;
  description: string;
  weight: number;
}

export interface LoginEvent {
  id: string;
  user_id: string;
  timestamp: string;
  success: boolean;
  ip_address: string;
  device_info: DeviceInfo;
  location?: Location;
  risk_assessment?: RiskAssessment;
  mfa_used?: boolean;
}
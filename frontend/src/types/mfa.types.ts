export enum MFAMethod {
  TOTP = 'totp',
  SMS = 'sms',
  EMAIL = 'email',
  BIOMETRIC = 'biometric',
}

export interface MFAChallenge {
  challenge_id: string;
  method: MFAMethod;
  expires_at: string;
  masked_destination?: string; 
}

export interface MFAVerification {
  challenge_id: string;
  code: string;
}

export interface MFASetupRequest {
  method: MFAMethod;
}

export interface MFASetupResponse {
  method: MFAMethod;
  secret?: string; 
  qr_code?: string;
  backup_codes?: string[];
}

export interface MFAStatus {
  enabled: boolean;
  methods: MFAMethod[];
  primary_method?: MFAMethod;
}

export interface MFAVerificationResponse {
  success: boolean;
  access_token?: string;
  refresh_token?: string;
  message?: string;
}
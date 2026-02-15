import api from '../axios/axiosConfig';
import { Session, LoginEvent, RiskAssessment } from '@/types/session.types';
import { ApiResponse } from '@/types/api.types';


function formatDevice(fingerprint?: string): string {
  return fingerprint ? `${fingerprint.substring(0, 16)}...` : 'Unknown Device';
}

export const sessionService = {

  async getSessions(): Promise<Session[]> {
    const response = await api.get<ApiResponse<Session[]>>('/sessions/active');
    return response.data.data!;
  },

  async getFullDashboard(): Promise<any> {
    const response = await api.get('/sessions/dashboard/full');
    const dashboardData = response.data;

    // Enrich sessions with device display
    if (dashboardData.sessions && Array.isArray(dashboardData.sessions)) {
      dashboardData.sessions = dashboardData.sessions.map((session: any) => ({
        ...session,
        device_display: formatDevice(session.device_fingerprint),
      }));
    }

    // Enrich login history with device display
    if (dashboardData.login_history && Array.isArray(dashboardData.login_history)) {
      dashboardData.login_history = dashboardData.login_history.map((event: any) => ({
        ...event,
        device_display: formatDevice(event.device_fingerprint),
      }));
    }

    // Enrich risk assessment with device display
    if (dashboardData.risk_assessment) {
      dashboardData.risk_assessment = {
        ...dashboardData.risk_assessment,
        device_status: dashboardData.risk_assessment.device_known 
          ? `Known ✓ (${formatDevice(dashboardData.risk_assessment.device_fingerprint)})`
          : 'New Device',
      };
    }

    return dashboardData;
  },

  async getDashboardOverview(): Promise<any> {
    const response = await api.get('/sessions/dashboard/overview');
    return response.data;
  },

  async getSession(sessionId: string): Promise<Session> {
    const response = await api.get<ApiResponse<Session>>(`/sessions/${sessionId}`);
    return response.data.data!;
  },

  async terminateSession(sessionId: string): Promise<void> {
    await api.delete(`/sessions/${sessionId}`);
  },

  async terminateAllOtherSessions(): Promise<void> {
    await api.delete('/sessions/revoke-all');
  },

  async getCurrentSession(): Promise<Session> {
    const sessions = await this.getSessions();
    return sessions[0];
  },


  async getLoginHistory(
    limit: number = 50,
    offset: number = 0,
    riskLevel?: string,
    days: number = 30
  ): Promise<LoginEvent[]> {
    const params: any = { limit, offset, days };
    if (riskLevel) params.risk_level = riskLevel;

    const response = await api.get<LoginEvent[]>('/sessions/history', { params });
    const events = response.data;

    return events.map((event: any) => ({
      ...event,
      device_display: formatDevice(event.device_fingerprint),
    }));
  },

  async getRiskAssessmentDetail(eventId: string): Promise<any> {
    const response = await api.get(`/sessions/risk-assessment/${eventId}`);
    const detail = response.data;

    // Add device display/status
    if (detail.device_analysis) {
      detail.device_analysis.device_display = formatDevice(detail.device_analysis.device_fingerprint);
      detail.device_analysis.device_status = detail.device_analysis.device_known 
        ? `Known ✓ (${formatDevice(detail.device_analysis.device_fingerprint)})`
        : 'New Device';
    }

    return detail;
  },

  async getCurrentRiskAssessment(): Promise<RiskAssessment> {
    const dashboard = await this.getDashboardOverview();
    return {
      risk_level: dashboard.current_risk_level,
      risk_score: dashboard.stats.average_risk_score,
      factors: [],
      timestamp: new Date().toISOString(),
    };
  },

  async trustDevice(deviceId: string): Promise<void> {
    await api.post('/sessions/trust-device', { device_id: deviceId });
  },

  async removeTrustedDevice(deviceId: string): Promise<void> {
    await api.delete(`/sessions/trust-device/${deviceId}`);
  },

  async getTrustedDevices(): Promise<
    Array<{
      device_fingerprint: string;
      last_seen: string;
      login_count: number;
      locations: string[];
      device_display?: string;
    }>
  > {
    const response = await api.get('/user/trusted-devices');
    const devices = response.data;

    return devices.map((device: any) => ({
      ...device,
      device_display: formatDevice(device.device_fingerprint),
      locations: device.locations?.slice(0, 3) || ['Multiple Locations'],
    }));
  },
};
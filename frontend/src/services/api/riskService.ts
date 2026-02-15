import axios from '@/services/axios/axiosConfig';

export interface RiskAssessment {
  riskLevel: 'low' | 'medium' | 'high';
  lastLoginRiskScore: number;
  unusualActivity: boolean;
  message?: string;
}

export const riskService = {
  getRiskAssessment: async (): Promise<RiskAssessment> => {
    const { data } = await axios.get<RiskAssessment>(
      '/risk/assessment'
    );
    return data;
  },

  acknowledgeRisk: async (riskId: string) => {
    await axios.post(`/risk/${riskId}/acknowledge`);
  },
};
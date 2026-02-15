import axios from '@/services/axios/axiosConfig';

export interface UserProfile {
  id: string;
  fullName: string;
  email: string;
  mfaEnabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export const userService = {
  getProfile: async (): Promise<UserProfile> => {
    const { data } = await axios.get<UserProfile>('/user/profile');
    return data;
  },

  updateProfile: async (updates: Partial<UserProfile>) => {
    const { data } = await axios.put<UserProfile>(
      '/user/profile',
      updates
    );
    return data;
  },

  changePassword: async (currentPassword: string, newPassword: string) => {
    await axios.post('/user/change-password', {
      currentPassword,
      newPassword,
    });
  },

  enableMFA: async () => {
    const { data } = await axios.post<{ secret: string }>('/user/mfa/enable');
    return data;
  },

  disableMFA: async () => {
    await axios.post('/user/mfa/disable');
  },
};
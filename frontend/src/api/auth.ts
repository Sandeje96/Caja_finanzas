import { apiClient } from './client';

export const requestOtp = async (phone: string) => {
  const res = await apiClient.post('/auth/login', { phone });
  return res.data;
};

export const verifyOtp = async (phone: string, otp_code: string) => {
  const res = await apiClient.post('/auth/verify', { phone, otp_code });
  return res.data; // { access_token, user }
};

export const getMe = async () => {
  const res = await apiClient.get('/auth/me');
  return res.data;
};

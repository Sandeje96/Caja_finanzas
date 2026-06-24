import { apiClient } from './client';

export const getDashboardSummary = async () => {
  const res = await apiClient.get('/dashboard/summary');
  return res.data; // { balance, income, expense }
};

export const getDashboardStats = async () => {
  const res = await apiClient.get('/dashboard/stats');
  return res.data; // { categories: [], monthly: {} }
};

import { apiClient } from './client';

export const getTransactions = async (page = 1, perPage = 50) => {
  const res = await apiClient.get(`/transactions?page=${page}&per_page=${perPage}`);
  return res.data;
};

export const updateTransaction = async (id: string, data: any) => {
  const res = await apiClient.patch(`/transactions/${id}`, data);
  return res.data;
};

export const deleteTransaction = async (id: string) => {
  const res = await apiClient.delete(`/transactions/${id}`);
  return res.data;
};

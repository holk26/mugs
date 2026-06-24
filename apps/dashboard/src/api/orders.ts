import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface Order {
  id: string;
  status: string;
  customer_email: string;
  customer_name: string;
  total: number;
  created_at: string;
}

export async function listOrders(params?: Record<string, unknown>): Promise<PaginatedResponse<Order>> {
  const response = await apiClient.get<PaginatedResponse<Order>>('/api/v1/admin/orders/', { params });
  return response.data;
}

export async function getOrder(id: string) {
  const response = await apiClient.get(`/api/v1/admin/orders/${id}/`);
  return response.data;
}

export async function updateOrderStatus(id: string, status: string) {
  const response = await apiClient.patch(`/api/v1/admin/orders/${id}/status/`, { status });
  return response.data;
}

import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface OrderLine {
  product_name: string;
  variant_name: string;
  quantity: number;
  unit_price: string;
  total_price: string;
}

export interface UploadFile {
  file: string;
  name?: string;
}

export interface ShippingAddress {
  name: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface Order {
  id: string;
  status: string;
  customer_email: string;
  customer_name: string;
  total: number | string;
  created_at: string;
  shipping_address?: ShippingAddress | null;
  raw_upload?: UploadFile | null;
  processed_upload?: UploadFile | null;
  lines?: OrderLine[];
  printful_order_id?: string;
  printful_status?: string;
}

export async function listOrders(params?: Record<string, unknown>): Promise<PaginatedResponse<Order>> {
  const response = await apiClient.get<PaginatedResponse<Order>>('/api/v1/admin/orders/', { params });
  return response.data;
}

export async function getOrder(id: string): Promise<Order> {
  const response = await apiClient.get<Order>(`/api/v1/admin/orders/${id}/`);
  return response.data;
}

export async function updateOrderStatus(id: string, status: string) {
  const response = await apiClient.patch(`/api/v1/admin/orders/${id}/status/`, { status });
  return response.data;
}

export async function pushOrderToPrintful(id: string) {
  const response = await apiClient.post(`/api/v1/admin/orders/${id}/printful/push/`);
  return response.data;
}

export async function confirmPrintfulOrder(id: string) {
  const response = await apiClient.post(`/api/v1/admin/orders/${id}/printful/confirm/`);
  return response.data;
}

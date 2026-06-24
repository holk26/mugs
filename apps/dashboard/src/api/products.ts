import apiClient from './client';
import type { ProductInput } from '@/lib/schemas';

export interface Product {
  id: string;
  handle: string;
  title: string;
  price: number;
  status: 'draft' | 'active' | 'archived';
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function listProducts(params?: Record<string, unknown>): Promise<PaginatedResponse<Product>> {
  const response = await apiClient.get<PaginatedResponse<Product>>('/api/v1/admin/products/', { params });
  return response.data;
}

export async function getProduct(id: string) {
  const response = await apiClient.get(`/api/v1/admin/products/${id}/`);
  return response.data;
}

export async function createProduct(data: ProductInput) {
  const response = await apiClient.post('/api/v1/admin/products/', data);
  return response.data;
}

export async function updateProduct(id: string, data: ProductInput) {
  const response = await apiClient.patch(`/api/v1/admin/products/${id}/`, data);
  return response.data;
}

export async function deleteProduct(id: string) {
  await apiClient.delete(`/api/v1/admin/products/${id}/`);
}

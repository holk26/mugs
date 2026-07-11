import apiClient from './client';
import type { PaginatedResponse } from './products';

export type DiscountType = 'percentage' | 'fixed_amount';
export type AppliesTo = 'all' | 'products' | 'collections';

export interface DiscountCode {
  id: string;
  code: string;
  description: string;
  discount_type: DiscountType;
  value: number | string;
  currency: string;
  min_order_amount: number | string | null;
  max_discount_amount: number | string | null;
  usage_limit_total: number | null;
  usage_limit_per_user: number | null;
  starts_at: string | null;
  expires_at: string | null;
  applies_to: AppliesTo;
  product_ids: string[];
  collection_ids: string[];
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface DiscountCodeInput {
  code: string;
  description: string;
  discount_type: DiscountType;
  value: number | string;
  currency: string;
  min_order_amount: number | string | null;
  max_discount_amount: number | string | null;
  usage_limit_total: number | null;
  usage_limit_per_user: number | null;
  starts_at: string | null;
  expires_at: string | null;
  applies_to: AppliesTo;
  product_ids: string[];
  collection_ids: string[];
  is_active: boolean;
}

export async function listDiscounts(params?: Record<string, unknown>): Promise<PaginatedResponse<DiscountCode>> {
  const response = await apiClient.get<PaginatedResponse<DiscountCode>>('/api/v1/admin/discounts/', { params });
  return response.data;
}

export async function getDiscount(id: string): Promise<DiscountCode> {
  const response = await apiClient.get<DiscountCode>(`/api/v1/admin/discounts/${id}/`);
  return response.data;
}

export async function createDiscount(data: DiscountCodeInput): Promise<DiscountCode> {
  const response = await apiClient.post<DiscountCode>('/api/v1/admin/discounts/', data);
  return response.data;
}

export async function updateDiscount(id: string, data: Partial<DiscountCodeInput>): Promise<DiscountCode> {
  const response = await apiClient.patch<DiscountCode>(`/api/v1/admin/discounts/${id}/`, data);
  return response.data;
}

export async function deleteDiscount(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/admin/discounts/${id}/`);
}

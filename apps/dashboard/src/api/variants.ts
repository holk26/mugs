import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface ProductVariant {
  id: string;
  title: string;
  sku: string;
  price: number;
  compare_at_price: number | null;
  stock: number;
  options: Record<string, unknown>;
  active: boolean;
  printful_sync_variant_id: number;
  printful_variant_id: number;
  created_at: string;
  updated_at: string;
}

export interface VariantInput {
  title: string;
  sku: string;
  price: number;
  compare_at_price?: number | null;
  stock: number;
  active: boolean;
}

export async function listVariants(productId: string): Promise<PaginatedResponse<ProductVariant>> {
  const response = await apiClient.get<PaginatedResponse<ProductVariant>>(`/api/v1/admin/products/${productId}/variants/`);
  return response.data;
}

export async function updateVariant(productId: string, variantId: string, data: VariantInput) {
  const response = await apiClient.patch(`/api/v1/admin/products/${productId}/variants/${variantId}/`, data);
  return response.data;
}

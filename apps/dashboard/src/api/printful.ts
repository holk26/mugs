import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface PrintfulSyncLog {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: string;
  products_created: number;
  products_updated: number;
  errors: unknown[];
}

export interface SyncPrintfulResult {
  log_id: string;
  status: string;
  created: number;
  updated: number;
  errors: unknown[];
}

export interface PrintfulStoreProduct {
  id: number;
  name: string;
  thumbnail_url?: string;
  synced?: number;
}

export interface PrintfulStoreProductsResponse {
  items: PrintfulStoreProduct[];
  total: number;
  limit: number;
  offset: number;
}

export interface ImportPrintfulResult {
  id: string;
  handle: string;
  title: string;
  created: boolean;
}

export async function syncPrintful(): Promise<SyncPrintfulResult> {
  const response = await apiClient.post('/api/v1/admin/printful/sync/');
  return response.data;
}

export async function listPrintfulStoreProducts(
  params?: { search?: string; limit?: number; offset?: number }
): Promise<PrintfulStoreProductsResponse> {
  const response = await apiClient.get<PrintfulStoreProductsResponse>('/api/v1/admin/printful/store-products/', { params });
  return response.data;
}

export async function importPrintfulProduct(printfulProductId: number): Promise<ImportPrintfulResult> {
  const response = await apiClient.post<ImportPrintfulResult>('/api/v1/admin/printful/store-products/import/', {
    printful_product_id: printfulProductId,
  });
  return response.data;
}

export async function listPrintfulLogs(): Promise<PaginatedResponse<PrintfulSyncLog>> {
  const response = await apiClient.get<PaginatedResponse<PrintfulSyncLog>>('/api/v1/admin/printful/logs/');
  return response.data;
}

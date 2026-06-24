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

export async function syncPrintful(): Promise<SyncPrintfulResult> {
  const response = await apiClient.post('/api/v1/admin/printful/sync/');
  return response.data;
}

export async function listPrintfulLogs(): Promise<PaginatedResponse<PrintfulSyncLog>> {
  const response = await apiClient.get<PaginatedResponse<PrintfulSyncLog>>('/api/v1/admin/printful/logs/');
  return response.data;
}

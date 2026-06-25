import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface PrintfulWebhookEvent {
  id: string;
  event_type: string;
  payload: Record<string, unknown>;
  processed: boolean;
  created_at: string;
}

export async function listPrintfulWebhookEvents(): Promise<PaginatedResponse<PrintfulWebhookEvent>> {
  const response = await apiClient.get<PaginatedResponse<PrintfulWebhookEvent>>('/api/v1/admin/printful/webhooks/');
  return response.data;
}

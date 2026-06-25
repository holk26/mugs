import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface Collection {
  id: string;
  handle: string;
  title: string;
}

export async function listCollections(): Promise<PaginatedResponse<Collection>> {
  const response = await apiClient.get<PaginatedResponse<Collection>>('/api/v1/admin/collections/');
  return response.data;
}

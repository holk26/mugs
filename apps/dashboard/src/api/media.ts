import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface ProductMedia {
  id: string;
  type: 'image' | 'video';
  url: string;
  alt: string;
  order: number;
}

export interface MediaInput {
  file: File;
  alt?: string;
  order?: number;
}

export async function listMedia(productId: string): Promise<PaginatedResponse<ProductMedia>> {
  const response = await apiClient.get<PaginatedResponse<ProductMedia>>(`/api/v1/admin/products/${productId}/media/`);
  return response.data;
}

export async function uploadMedia(productId: string, data: MediaInput) {
  const formData = new FormData();
  formData.append('file', data.file);
  if (data.alt) formData.append('alt', data.alt);
  if (data.order !== undefined) formData.append('order', String(data.order));
  const response = await apiClient.post(`/api/v1/admin/products/${productId}/media/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function updateMedia(productId: string, mediaId: string, data: { alt?: string; order?: number }) {
  const response = await apiClient.patch(`/api/v1/admin/products/${productId}/media/${mediaId}/`, data);
  return response.data;
}

export async function deleteMedia(productId: string, mediaId: string) {
  await apiClient.delete(`/api/v1/admin/products/${productId}/media/${mediaId}/`);
}

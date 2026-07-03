import apiClient from './client';

export interface DashboardStats {
  orders_today: number;
  active_products: number;
  last_sync_at: string | null;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>('/api/v1/admin/stats/dashboard/');
  return response.data;
}

import apiClient from './client';
import axios from 'axios';
import type { User } from '@/stores/authStore';

export interface SignInInput {
  email: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export async function signIn(data: SignInInput): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/api/v1/auth/signin/', data);
  return response.data;
}

export async function refreshToken(refresh: string): Promise<{ access: string }> {
  // Use plain axios to avoid interceptor recursion during refresh
  const response = await axios.post<{ access: string }>(`${apiClient.defaults.baseURL}/api/v1/auth/refresh/`, { refresh });
  return response.data;
}

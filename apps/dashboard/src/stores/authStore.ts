import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
}

interface AuthState {
  accessToken: string | null;
  user: User | null;
  setAuth: (accessToken: string, refreshToken: string, user: User) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      setAuth: (accessToken, refreshToken, user) => {
        localStorage.setItem('refresh_token', refreshToken);
        set({ accessToken, user });
      },
      setAccessToken: (accessToken) => set({ accessToken }),
      setUser: (user) => set({ user }),
      logout: () => {
        localStorage.removeItem('refresh_token');
        set({ accessToken: null, user: null });
      },
    }),
    { name: 'auth-storage', partialize: (state) => ({ user: state.user }) }
  )
);

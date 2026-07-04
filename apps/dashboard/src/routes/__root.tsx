import { createRootRoute, Outlet, redirect } from '@tanstack/react-router';
import { useAuthStore } from '@/stores/authStore';
import { refreshToken } from '@/api/auth';
import { AppLayout } from '@/components/layout/AppLayout';

export const Route = createRootRoute({
  component: () => {
    const isAuthenticated = !!useAuthStore((s) => s.accessToken);
    if (!isAuthenticated) return <Outlet />;
    return <AppLayout />;
  },
  beforeLoad: async ({ location }) => {
    const publicRoutes = ['/login'];
    const isPublic = publicRoutes.includes(location.pathname);
    const store = useAuthStore.getState();

    if (!store.accessToken || !store.user) {
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { access } = await refreshToken(refresh);
          store.setAccessToken(access);
        } catch {
          store.logout();
          if (!isPublic) throw redirect({ to: '/login' });
        }
      } else if (!isPublic) {
        throw redirect({ to: '/login' });
      }
    }

    if (store.user && !store.user.is_staff && !isPublic) {
      throw redirect({ to: '/login' });
    }
  },
});
